"""Command-line behavior for the marketplace build tools."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import tree_snapshot


def command_repo(tmp_path: Path) -> Path:
    """Copy only the source a build command needs into a disposable repo."""
    repo = tmp_path / "repo"
    for path in (
        "plugin_maintenance",
        "plugins",
        ".agents",
        ".claude-plugin",
        ".gitignore",
    ):
        source = REPO_ROOT / path
        destination = repo / path
        if source.is_dir():
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return repo


def run_module(repo: Path, module: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


@pytest.mark.parametrize("argument", ["--no-such-flag", "--help"])
def test_build_rejects_or_describes_arguments_without_writing(tmp_path: Path, argument: str) -> None:
    repo = command_repo(tmp_path)
    before = tree_snapshot(repo)

    result = run_module(repo, "plugin_maintenance.build", argument)

    assert result.returncode == (2 if argument == "--no-such-flag" else 0)
    if argument == "--no-such-flag":
        assert "unrecognized arguments: --no-such-flag" in result.stderr
    else:
        assert "usage:" in result.stdout
    assert tree_snapshot(repo) == before


def test_render_module_startup_has_no_runtime_warning(tmp_path: Path) -> None:
    repo = command_repo(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::RuntimeWarning",
            "-m",
            "plugin_maintenance.render",
            "--help",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )

    assert result.returncode == 0, result.stderr
    assert "RuntimeWarning" not in result.stderr
