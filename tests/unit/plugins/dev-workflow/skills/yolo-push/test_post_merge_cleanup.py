"""The post-merge cleanup commands yolo-push ships, run against real git."""

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest


FAKE_GH = """#!/usr/bin/env bash
case "$1 $2" in
  "pr view") printf '7\\tfeat\\t%s\\tMERGED\\n' "$PR_HEAD" ;;
  "repo view") echo main ;;
  "pr list") printf '%s' "$BASED_PRS" ;;
esac
"""
BASED_PR = "https://github.com/owner/repo/pull/8"
EVERYTHING = {"worktree", "local branch", "remote branch"}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@dataclass
class MergedPr:
    """PR #7 from branch `feat`, merged, with `feat` checked out in `worktree`."""

    root: Path
    remote: Path
    main: Path
    worktree: Path
    head: str
    based_prs: str = ""

    def run(self, script: str) -> str:
        return subprocess.run(
            ["bash", "-c", "PR=7\n" + script],
            cwd=self.worktree if self.worktree.exists() else self.main,
            env={
                "PATH": f"{self.root / 'bin'}:/usr/bin:/bin",
                "HOME": str(self.root),
                "PR_HEAD": self.head,
                "BASED_PRS": self.based_prs,
            },
            capture_output=True,
            text=True,
        ).stdout

    def surviving(self) -> set[str]:
        kept = set()
        if self.worktree.exists():
            kept.add("worktree")
        if git(self.main, "branch", "--list", "feat"):
            kept.add("local branch")
        if git(self.main, "ls-remote", "--heads", "origin", "feat"):
            kept.add("remote branch")
        return kept


@pytest.fixture
def cleanup(rendered: Path) -> tuple[str, str]:
    """The read-only cleanup blocks, and every cleanup block through deletion."""
    skill = rendered / "dev-workflow" / "skills" / "yolo-push" / "SKILL.md"
    blocks = re.findall(r"```bash\n(.*?)```", skill.read_text(encoding="utf-8"), re.DOTALL)
    start = next(i for i, block in enumerate(blocks) if "gh pr view" in block)
    deletion = next(i for i, block in enumerate(blocks) if "git worktree remove" in block)
    return "\n".join(blocks[start:deletion]), "\n".join(blocks[start : deletion + 1])


@pytest.fixture
def merged_pr(tmp_path: Path) -> MergedPr:
    remote, main, worktree = (tmp_path / name for name in ("remote.git", "main", "wt"))
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(main)], check=True, capture_output=True)
    (main / ".gitignore").write_text(".env\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "-q", "-m", "init")
    git(main, "push", "-q", "origin", "HEAD:main")
    git(main, "worktree", "add", "-q", str(worktree), "-b", "feat")
    git(worktree, "commit", "-q", "--allow-empty", "-m", "feature")
    git(worktree, "push", "-q", "origin", "feat")
    head = git(worktree, "rev-parse", "HEAD")
    git(remote, "update-ref", "refs/pull/7/head", head)

    gh = tmp_path / "bin" / "gh"
    gh.parent.mkdir()
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)
    return MergedPr(tmp_path, remote, main, worktree, head)


def ignored_file(pr: MergedPr) -> None:
    (pr.worktree / ".env").write_text("SECRET=1\n")


def untracked_file(pr: MergedPr) -> None:
    (pr.worktree / "notes.txt").write_text("draft\n")


def local_commit(pr: MergedPr) -> None:
    git(pr.worktree, "commit", "-q", "--allow-empty", "-m", "local only")


def remote_commit(pr: MergedPr) -> None:
    other = pr.root / "other"
    subprocess.run(
        ["git", "clone", "-q", "-b", "feat", str(pr.remote), str(other)],
        check=True,
        capture_output=True,
    )
    git(other, "commit", "-q", "--allow-empty", "-m", "pushed after merge")
    git(other, "push", "-q", "origin", "feat")


def open_based_pr(pr: MergedPr) -> None:
    pr.based_prs = BASED_PR + "\n"


LOSSES = [
    pytest.param(ignored_file, ".env", id="ignored-file"),
    pytest.param(untracked_file, "notes.txt", id="untracked-file"),
    pytest.param(local_commit, "local only", id="local-commit"),
    pytest.param(remote_commit, "pushed after merge", id="remote-commit"),
    pytest.param(open_based_pr, BASED_PR, id="open-based-pr"),
]


class TestLossChecks:
    @pytest.mark.parametrize(("setup", "finding"), LOSSES)
    def test_leftover_work_is_reported(
        self, merged_pr: MergedPr, cleanup: tuple[str, str], setup: Callable, finding: str
    ) -> None:
        setup(merged_pr)

        assert finding in merged_pr.run(cleanup[0])

    def test_clean_merge_reports_only_headings(
        self, merged_pr: MergedPr, cleanup: tuple[str, str]
    ) -> None:
        output = merged_pr.run(cleanup[0])

        assert output
        assert all(line.endswith(":") for line in output.splitlines())

    @pytest.mark.parametrize(("setup", "finding"), LOSSES)
    def test_checks_delete_nothing(
        self, merged_pr: MergedPr, cleanup: tuple[str, str], setup: Callable, finding: str
    ) -> None:
        setup(merged_pr)

        merged_pr.run(cleanup[0])

        assert merged_pr.surviving() == EVERYTHING


class TestGuardedDeletion:
    @pytest.mark.parametrize(
        ("setup", "kept"),
        [
            pytest.param(lambda pr: None, set(), id="clean"),
            pytest.param(ignored_file, set(), id="ignored-file-is-lost"),
            pytest.param(untracked_file, {"worktree", "local branch"}, id="untracked-file"),
            pytest.param(local_commit, {"local branch"}, id="local-commit"),
            pytest.param(remote_commit, {"remote branch"}, id="remote-commit"),
            pytest.param(open_based_pr, {"remote branch"}, id="open-based-pr"),
        ],
    )
    def test_deletion_keeps_only_what_holds_unmerged_work(
        self, merged_pr: MergedPr, cleanup: tuple[str, str], setup: Callable, kept: set[str]
    ) -> None:
        setup(merged_pr)

        merged_pr.run(cleanup[1])

        assert merged_pr.surviving() == kept

    def test_branch_in_main_worktree_is_switched_away_then_deleted(
        self, merged_pr: MergedPr, cleanup: tuple[str, str]
    ) -> None:
        git(merged_pr.main, "worktree", "remove", str(merged_pr.worktree))
        git(merged_pr.main, "switch", "-q", "feat")

        merged_pr.run(cleanup[1])

        assert git(merged_pr.main, "branch", "--show-current") == "main"
        assert merged_pr.surviving() == set()
