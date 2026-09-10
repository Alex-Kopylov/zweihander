"""Freshness check: build a copy of the tree, compare it back.

Usage: `uv run python -m plugin_maintenance.verify`

Building in place and running `git diff` only answers the question in a clean
checkout. Locally the tree is dirty by definition, and by the time the diff
runs the build has already overwritten whatever was stale, so the answer is
always "clean" — the check repairs the very drift it is meant to report. This
builds a copy of the tree instead and compares the copy against the tree it
came from, which needs no clean checkout and writes to neither the working
tree nor the index. One command is therefore correct both in CI and mid-edit.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.render import BuildError, ignored_path


FIX_COMMAND = "uv run python -m plugin_maintenance.build"


def source_paths(repo_root: Path) -> list[str]:
    """Every path git would carry into a commit, tracked or newly added.

    Asking git rather than walking keeps one declaration of what counts as
    content: `.gitignore` already decides, and the renderer reads the same
    file. A tracked path deleted from disk still lists, so it is dropped here.
    """
    listings = (["-z"], ["-z", "--others", "--exclude-standard"])
    paths: set[str] = set()
    for listing in listings:
        completed = subprocess.run(
            ["git", "ls-files", *listing],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        paths.update(entry for entry in completed.stdout.split("\0") if entry)
    return sorted(
        relative
        for relative in paths
        if (repo_root / relative).is_symlink() or (repo_root / relative).exists()
    )


def copy_sources(repo_root: Path, scratch: Path) -> None:
    """Copy the tree's content into the scratch directory, modes and all."""
    for relative in source_paths(repo_root):
        target = scratch / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_root / relative, target, follow_symlinks=False)


def run_build(scratch: Path) -> None:
    """Run the copy's own build, so nothing writes into the real tree.

    `python -m` puts the working directory first on `sys.path`, so the copy
    imports its own `plugin_maintenance` and every path the build derives from
    `__file__` lands inside the copy.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "plugin_maintenance.build"],
        cwd=scratch,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        # The copy's build already fails loud in this shape; carrying its own
        # prefix through would print `error: error:`.
        message = (completed.stderr or completed.stdout).strip()
        raise BuildError(message.removeprefix("error: "))


def built_paths(scratch: Path) -> set[str]:
    """Content of the copy after the build, minus what `.gitignore` excludes."""
    is_ignored = ignored_path(scratch)
    return {
        path.relative_to(scratch).as_posix()
        for path in scratch.rglob("*")
        if (path.is_file() or path.is_symlink()) and not is_ignored(path)
    }


def state(root: Path, relative: str) -> object:
    """What must match for a path to count as current.

    Content plus the executable bit — git's own granularity, so the check
    reports exactly the drift a commit would carry.
    """
    path = root / relative
    if path.is_symlink():
        return os.readlink(path)
    return path.read_bytes(), bool(path.stat().st_mode & 0o111)


def stale_paths(repo_root: Path, scratch: Path) -> list[str]:
    """Where the tree and a fresh build of it disagree, one line each."""
    built = built_paths(scratch)
    present = set(source_paths(repo_root))
    differences = []
    for relative in sorted(built | present):
        if relative not in present:
            differences.append(f"the build produces it, the tree lacks it: {relative}")
        elif relative not in built:
            differences.append(
                f"the tree carries it, the build does not produce it: {relative}"
            )
        elif state(repo_root, relative) != state(scratch, relative):
            differences.append(f"differs from the build: {relative}")
    return differences


def verify(repo_root: Path) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="verify-tree-") as temporary:
        scratch = Path(temporary) / "repo"
        scratch.mkdir()
        copy_sources(repo_root, scratch)
        run_build(scratch)
        return stale_paths(repo_root, scratch)


def main() -> None:
    try:
        differences = verify(REPO_ROOT)
    except BuildError as error:
        raise SystemExit(f"error: {error}") from error
    if differences:
        raise SystemExit(
            "the tree is not current:\n  "
            + "\n  ".join(differences)
            + f"\n\nrun `{FIX_COMMAND}` and commit the result"
        )
    print("tree is current")


if __name__ == "__main__":
    main()
