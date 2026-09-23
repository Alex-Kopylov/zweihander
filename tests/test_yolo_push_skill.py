import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = REPO_ROOT / "plugins" / "dev-workflow" / "skills" / "yolo-push" / "SKILL.md"

FAKE_GH = """#!/usr/bin/env bash
case "$1 $2" in
  "pr view") printf '7\\tfeat\\t%s\\tMERGED\\n' "$PR_HEAD" ;;
  "repo view") echo main ;;
  "api "*) echo false ;;
esac
"""


def cleanup_script() -> str:
    text = SKILL_FILE.read_text(encoding="utf-8")
    section = text.split("## Post-Merge Cleanup", 1)[1].split("\n## ", 1)[0]
    return "\n".join(re.findall(r"```bash\n(.*?)```", section, re.DOTALL))


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.mark.parametrize("unsafe", [False, True], ids=["clean", "unmerged-work"])
def test_cleanup_deletes_only_what_the_merged_pr_contains(tmp_path: Path, unsafe: bool) -> None:
    remote, main, wt, other = (tmp_path / n for n in ("remote.git", "main", "wt", "other"))
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(main)], check=True, capture_output=True)
    git(main, "commit", "-q", "--allow-empty", "-m", "init")
    git(main, "push", "-q", "origin", "HEAD:main")
    git(main, "worktree", "add", "-q", str(wt), "-b", "feat")
    git(wt, "commit", "-q", "--allow-empty", "-m", "feature")
    git(wt, "push", "-q", "origin", "feat")
    pr_head = git(wt, "rev-parse", "HEAD")
    git(remote, "update-ref", "refs/pull/7/head", pr_head)

    if unsafe:
        git(wt, "commit", "-q", "--allow-empty", "-m", "local only")
        subprocess.run(["git", "clone", "-q", "-b", "feat", str(remote), str(other)], check=True, capture_output=True)
        git(other, "commit", "-q", "--allow-empty", "-m", "pushed after merge")
        git(other, "push", "-q", "origin", "feat")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH)
    (bin_dir / "gh").chmod(0o755)

    subprocess.run(
        ["bash", "-c", "PR=7\n" + cleanup_script()],
        cwd=wt,
        env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path), "PR_HEAD": pr_head},
        capture_output=True,
        text=True,
    )

    assert not wt.exists()
    assert bool(git(main, "branch", "--list", "feat")) is unsafe
    assert bool(git(main, "ls-remote", "--heads", "origin", "feat")) is unsafe
