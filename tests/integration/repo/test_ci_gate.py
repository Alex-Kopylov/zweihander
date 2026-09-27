"""Regression for the CI "committed tree is current" gate.

`git diff --exit-code` alone is blind to untracked files: a build that adds a
new file to `dist/` without the author staging it would pass the gate. The
gate script now stages everything first, so new files are caught too.
"""

import re
import subprocess
from pathlib import Path

from plugin_maintenance import REPO_ROOT


def gate_script() -> str:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"Check the committed tree is current\n\s*run: \|\n((?:^ {10}.*\n?)+)",
        workflow,
        re.MULTILINE,
    )
    assert match, "could not find the gate step in ci.yml"
    return "\n".join(line[10:] for line in match.group(1).splitlines())


def run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def init_repo(path: Path) -> None:
    run_git(["init"], path)
    run_git(["config", "user.email", "test@example.com"], path)
    run_git(["config", "user.name", "Test"], path)
    (path / "tracked.txt").write_text("original\n", encoding="utf-8")
    run_git(["add", "."], path)
    run_git(["commit", "-m", "initial"], path)


def test_gate_fails_on_untracked_file(tmp_path):
    init_repo(tmp_path)
    (tmp_path / "dist" / "new-plugin").mkdir(parents=True)
    (tmp_path / "dist" / "new-plugin" / "SKILL.md").write_text(
        "# New\n", encoding="utf-8"
    )

    result = subprocess.run(
        ["bash", "-c", gate_script()], cwd=tmp_path, capture_output=True
    )

    assert result.returncode != 0


def test_gate_passes_on_clean_tree(tmp_path):
    init_repo(tmp_path)

    result = subprocess.run(
        ["bash", "-c", gate_script()], cwd=tmp_path, capture_output=True
    )

    assert result.returncode == 0
