"""Tests for the Codex PostToolUse documentation-language hook."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / ".codex" / "hooks" / "docs_language_guard.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("docs_language_guard", HOOK_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = load_hook_module()


def make_patch(*paths: str) -> str:
    body = "".join(
        f"*** Update File: {path}\n@@\n-old line\n+new line\n" for path in paths
    )
    return f"*** Begin Patch\n{body}*** End Patch\n"


@pytest.fixture(scope="module")
def sample_repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("sample-repo")
    for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md"):
        (root / name).write_text(f"# {name}\n")
    (root / "docs" / "guide").mkdir(parents=True)
    (root / "docs" / "guide" / "setup.md").write_text("# Setup\n")
    (root / "docs" / "index.md").write_text("# Index\n")
    (root / "docs" / "diagram.svg").write_text("<svg></svg>\n")
    nested = root / "plugins" / "dev-workflow"
    (nested / "skills" / "commit").mkdir(parents=True)
    (nested / "skills" / "commit" / "SKILL.md").write_text("# Skill\n")
    (nested / "docs").mkdir()
    (nested / "docs" / "notes.md").write_text("# Notes\n")
    (nested / "README.md").write_text("# Plugin\n")
    (nested / "AGENTS.md").write_text("# Agents\n")
    return root


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "CONTRIBUTING.md",
        "NOTICE.md",
        "docs/guide/setup.md",
        "docs/index.md",
        "plugins/dev-workflow/README.md",
        "plugins/dev-workflow/docs/notes.md",
        "a/b/docs/c/d.md",
    ],
)
def test_in_scope_paths(path: str) -> None:
    assert hook.in_scope(PurePosixPath(path)) is True


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "CLAUDE.md",
        "plugins/dev-workflow/AGENTS.md",
        "plugins/dev-workflow/skills/commit/SKILL.md",
        "docs/diagram.svg",
        "README.txt",
        "docsy/notes.md",
    ],
)
def test_out_of_scope_paths(path: str) -> None:
    assert hook.in_scope(PurePosixPath(path)) is False


def test_patched_paths_collects_adds_and_updates() -> None:
    patch_text = (
        "*** Begin Patch\n"
        "*** Add File: docs/new.md\n"
        "*** Update File: README.md\n"
        "*** End Patch\n"
    )
    assert hook.patched_paths(patch_text) == ["docs/new.md", "README.md"]


def test_patched_paths_skips_deletes() -> None:
    patch_text = "*** Begin Patch\n*** Delete File: README.md\n*** End Patch\n"
    assert hook.patched_paths(patch_text) == []


def make_event(patch_text: str, cwd: Path) -> dict:
    return {
        "cwd": str(cwd),
        "hook_event_name": "PostToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": patch_text},
    }


def targets(patch_text: str, root: Path) -> list[str]:
    event = make_event(patch_text, root)
    return [str(path) for path in hook.targets_from_event(event, root=root)]


def test_mixed_patch_selects_only_in_scope_files(sample_repository: Path) -> None:
    patch_text = make_patch("README.md", "AGENTS.md", "docs/guide/setup.md")
    assert targets(patch_text, sample_repository) == [
        "README.md",
        "docs/guide/setup.md",
    ]


def test_missing_file_is_not_selected(sample_repository: Path) -> None:
    assert targets(make_patch("docs/does-not-exist.md"), sample_repository) == []


def test_path_outside_the_root_is_not_selected(sample_repository: Path) -> None:
    assert targets(make_patch("/etc/README.md"), sample_repository) == []


def test_duplicate_paths_are_collapsed(sample_repository: Path) -> None:
    assert targets(make_patch("README.md", "README.md"), sample_repository) == [
        "README.md"
    ]


@pytest.mark.parametrize(
    "event",
    [
        {"tool_input": {"command": "*** Begin Patch\n*** End Patch\n"}},
        {"tool_input": "not a dict"},
        {"tool_input": {"command": 42}},
        {},
    ],
)
def test_malformed_events_select_nothing(event: dict, sample_repository: Path) -> None:
    assert hook.targets_from_event(event, root=sample_repository) == []


def test_script_exits_cleanly_on_broken_stdin() -> None:
    """One end-to-end smoke test. The payload can never reach a dispatch."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="not json at all",
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
