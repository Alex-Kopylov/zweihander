import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = REPO_ROOT / "plugins" / "dev-workflow" / "skills" / "yolo-push" / "SKILL.md"
QUESTION_STEP = "Cleanup 3"
DELETE_OPTION = "Delete the merged branch locally, on the remote, and its worktree if any"
KEEP_OPTION = "Keep everything for now"

FAKE_GH = """#!/usr/bin/env bash
case "$1 $2" in
  "pr view") printf '7\\tfeat\\t%s\\tMERGED\\n' "$PR_HEAD" ;;
  "repo view") echo main ;;
  "api "*) echo false ;;
esac
"""


def cleanup_section() -> str:
    text = SKILL_FILE.read_text(encoding="utf-8")
    return text.split("## Post-Merge Cleanup", 1)[1].split("\n## ", 1)[0]


def bash_blocks(markdown: str) -> str:
    return "\n".join(re.findall(r"```bash\n(.*?)```", markdown, re.DOTALL))


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_in_sandbox(tmp_path: Path, unsafe: bool, script: str) -> tuple[Path, Path, str]:
    """Merged PR #7 from branch feat checked out in worktree wt; unsafe adds work outside the PR."""
    remote, main, wt, other = (tmp_path / n for n in ("remote.git", "main", "wt", "other"))
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(main)], check=True, capture_output=True)
    (main / ".gitignore").write_text(".env\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "-q", "-m", "init")
    git(main, "push", "-q", "origin", "HEAD:main")
    git(main, "worktree", "add", "-q", str(wt), "-b", "feat")
    git(wt, "commit", "-q", "--allow-empty", "-m", "feature")
    git(wt, "push", "-q", "origin", "feat")
    pr_head = git(wt, "rev-parse", "HEAD")
    git(remote, "update-ref", "refs/pull/7/head", pr_head)

    if unsafe:
        (wt / ".env").write_text("SECRET=1\n")
        git(wt, "commit", "-q", "--allow-empty", "-m", "local only")
        subprocess.run(
            ["git", "clone", "-q", "-b", "feat", str(remote), str(other)],
            check=True,
            capture_output=True,
        )
        git(other, "commit", "-q", "--allow-empty", "-m", "pushed after merge")
        git(other, "push", "-q", "origin", "feat")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH)
    (bin_dir / "gh").chmod(0o755)

    result = subprocess.run(
        ["bash", "-c", "PR=7\n" + script],
        cwd=wt,
        env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path), "PR_HEAD": pr_head},
        capture_output=True,
        text=True,
    )
    return main, wt, result.stdout


def test_cleanup_asks_one_question_with_delete_and_keep_options() -> None:
    question_step = cleanup_section().split(QUESTION_STEP, 1)[1]

    assert DELETE_OPTION in question_step
    assert KEEP_OPTION in question_step


@pytest.mark.parametrize("unsafe", [False, True], ids=["clean", "unmerged-work"])
def test_checks_before_the_question_report_losses_and_delete_nothing(
    tmp_path: Path, unsafe: bool
) -> None:
    checks = bash_blocks(cleanup_section().split(QUESTION_STEP, 1)[0])

    main, wt, output = run_in_sandbox(tmp_path, unsafe, checks)

    assert wt.exists()
    assert git(main, "branch", "--list", "feat")
    assert git(main, "ls-remote", "--heads", "origin", "feat")
    for finding in (".env", "local only", "pushed after merge"):
        assert (finding in output) is unsafe


@pytest.mark.parametrize("unsafe", [False, True], ids=["clean", "unmerged-work"])
def test_delete_answer_removes_only_what_the_merged_pr_contains(
    tmp_path: Path, unsafe: bool
) -> None:
    main, wt, _ = run_in_sandbox(tmp_path, unsafe, bash_blocks(cleanup_section()))

    assert not wt.exists()
    assert bool(git(main, "branch", "--list", "feat")) is unsafe
    assert bool(git(main, "ls-remote", "--heads", "origin", "feat")) is unsafe
