"""Freshness check: build a copy of the tree and compare it back.

Covers what git feeds the copy, what the copy preserves, and the three ways a
tree and a fresh build of it disagree: a file the build produces that the tree
lacks, a file the tree carries that the build does not produce, and a file
whose content or executable bit drifted.
"""

import os
import subprocess
from pathlib import Path

import pytest

from plugin_maintenance import REPO_ROOT, verify as verify_module
from plugin_maintenance.verify import (
    FIX_COMMAND,
    copy_sources,
    main,
    source_paths,
    stale_paths,
)


def git(path: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=path, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repository with a tracked file, a symlink, and a shell script."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("shared\n", encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")
    script = root / "run.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    script.chmod(0o755)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "initial")
    return root


@pytest.fixture
def scratch(repo: Path, tmp_path: Path) -> Path:
    """The copy, as it stands before a build changes anything."""
    target = tmp_path / "scratch"
    copy_sources(repo, target)
    return target


class TestSourcePaths:
    def test_lists_tracked_and_newly_added_files(self, repo):
        (repo / "new.md").write_text("new\n", encoding="utf-8")

        paths = source_paths(repo)

        assert "AGENTS.md" in paths
        assert "new.md" in paths

    def test_skips_files_gitignore_excludes(self, repo):
        (repo / "__pycache__").mkdir()
        (repo / "__pycache__" / "render.pyc").write_bytes(b"")

        assert not [
            path for path in source_paths(repo) if path.startswith("__pycache__")
        ]

    def test_skips_a_tracked_file_deleted_from_disk(self, repo):
        (repo / "run.sh").unlink()

        assert "run.sh" not in source_paths(repo)


class TestCopySources:
    def test_preserves_symlinks(self, repo, scratch):
        assert (scratch / "CLAUDE.md").is_symlink()
        assert os.readlink(scratch / "CLAUDE.md") == "AGENTS.md"

    def test_preserves_the_executable_bit(self, repo, scratch):
        assert (scratch / "run.sh").stat().st_mode & 0o111


class TestStalePaths:
    def test_an_untouched_copy_reports_nothing(self, repo, scratch):
        assert stale_paths(repo, scratch) == []

    def test_reports_content_drift(self, repo, scratch):
        (scratch / "AGENTS.md").write_text("rebuilt\n", encoding="utf-8")

        assert stale_paths(repo, scratch) == ["differs from the build: AGENTS.md"]

    def test_reports_a_dropped_executable_bit(self, repo, scratch):
        (scratch / "run.sh").chmod(0o644)

        assert stale_paths(repo, scratch) == ["differs from the build: run.sh"]

    def test_reports_a_file_the_build_does_not_produce(self, repo, scratch):
        (scratch / "run.sh").unlink()

        assert stale_paths(repo, scratch) == [
            "the tree carries it, the build does not produce it: run.sh"
        ]

    def test_reports_a_file_missing_from_the_tree(self, repo, scratch):
        (scratch / "dist").mkdir()
        (scratch / "dist" / "SKILL.md").write_text("rendered\n", encoding="utf-8")

        assert stale_paths(repo, scratch) == [
            "the build produces it, the tree lacks it: dist/SKILL.md"
        ]

    def test_ignores_build_leftovers_gitignore_excludes(self, repo, scratch):
        (scratch / "__pycache__").mkdir()
        (scratch / "__pycache__" / "render.pyc").write_bytes(b"")

        assert stale_paths(repo, scratch) == []


class TestCommandLine:
    def test_a_stale_tree_fails_and_names_the_fix(self, monkeypatch):
        monkeypatch.setattr(
            verify_module,
            "verify",
            lambda repo_root: ["differs from the build: dist/codex/x/SKILL.md"],
        )

        with pytest.raises(SystemExit) as failure:
            main()

        assert "dist/codex/x/SKILL.md" in str(failure.value)
        assert FIX_COMMAND in str(failure.value)

    def test_a_current_tree_succeeds(self, monkeypatch):
        monkeypatch.setattr(verify_module, "verify", lambda repo_root: [])

        main()


def test_ci_runs_the_same_command():
    """CI and a developer run one check, not two implementations of one."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "uv run python -m plugin_maintenance.verify" in workflow
