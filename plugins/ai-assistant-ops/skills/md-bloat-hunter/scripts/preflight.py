#!/usr/bin/env python3
"""Check Markdown targets are safe for md-bloat-hunter to rewrite, and record their hashes."""

import argparse
import hashlib
import json
import shutil

# Tracked/clean status and the worktree root come from git itself; reading the
# index directly would reimplement git.
import subprocess  # ruff: ignore[suspicious-subprocess-import]
from pathlib import Path
from typing import Any


class TargetError(ValueError):
    """A target that fails preflight; the message is the reported error."""

    GIT_NOT_FOUND = "git executable not found on PATH"
    NOT_MARKDOWN = "target must have a .md extension"
    SYMLINK = "target must not be a symlink"
    NOT_REGULAR_FILE = "target must be a regular file"
    OUTSIDE_WORKTREE = "outside a git worktree"
    OUTSIDE_GIT_ROOT = "target real path is outside the git root"
    UNTRACKED = "target is not tracked by git"
    GIT_STATUS_FAILED = "git status failed"
    DIRTY = "target has staged or unstaged changes"
    NOT_IN_MAP = "target was not present in the original preflight map"
    HASH_CHANGED = "target content hash changed since preflight"


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run git in `cwd` and return the completed process without raising on failure."""
    git = shutil.which("git")
    if git is None:
        raise TargetError(TargetError.GIT_NOT_FOUND)
    # The executable is resolved and no shell parses the argv.
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [git, "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def sha256(path: Path) -> str:
    """Return the file's SHA-256 hex digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_root_for(path: Path) -> Path:
    """Return the root of the git worktree containing `path`."""
    result = run_git(["rev-parse", "--show-toplevel"], path.parent)
    if result.returncode != 0:
        raise TargetError(TargetError.OUTSIDE_WORKTREE)
    return Path(result.stdout.strip()).resolve()


def validate_target(path: Path) -> dict[str, str]:
    """Return the target's identity and hash, or raise TargetError when it is unsafe to rewrite."""
    resolved = path.expanduser().resolve()
    if path.suffix.lower() != ".md":
        raise TargetError(TargetError.NOT_MARKDOWN)
    if path.is_symlink() or resolved.is_symlink():
        raise TargetError(TargetError.SYMLINK)
    if not resolved.is_file():
        raise TargetError(TargetError.NOT_REGULAR_FILE)

    repo_root = git_root_for(resolved)
    if not resolved.is_relative_to(repo_root):
        raise TargetError(TargetError.OUTSIDE_GIT_ROOT)

    relative = resolved.relative_to(repo_root)
    tracked = run_git(["ls-files", "--error-unmatch", "--", str(relative)], repo_root)
    if tracked.returncode != 0:
        raise TargetError(TargetError.UNTRACKED)

    status = run_git(["status", "--porcelain", "--", str(relative)], repo_root)
    if status.returncode != 0:
        raise TargetError(status.stderr.strip() or TargetError.GIT_STATUS_FAILED)
    if status.stdout.strip():
        raise TargetError(TargetError.DIRTY)

    return {
        "file_path": str(resolved),
        "repo_root": str(repo_root),
        "git_relative_path": str(relative),
        "sha256": sha256(resolved),
    }


def load_expected(path: Path) -> dict[str, str]:
    """Map each target's resolved path to its hash from an earlier preflight run."""
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    expected: dict[str, str] = {}
    for item in payload.get("targets", []):
        expected[str(Path(item["file_path"]).resolve())] = str(item["sha256"])
    return expected


def check_expected(target: dict[str, str], expected: dict[str, str]) -> None:
    """Raise TargetError when the target is missing from, or differs from, the earlier run."""
    expected_hash = expected.get(target["file_path"])
    if expected_hash is None:
        raise TargetError(TargetError.NOT_IN_MAP)
    if expected_hash != target["sha256"]:
        raise TargetError(TargetError.HASH_CHANGED)


def main() -> int:
    """Validate every target and print the JSON report."""
    parser = argparse.ArgumentParser(description="Preflight markdown files before md-bloat-hunter writes.")
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files to validate")
    parser.add_argument(
        "--expect-map",
        type=Path,
        help="Optional earlier preflight JSON. Current file hashes must match it.",
    )
    args = parser.parse_args()

    expected = load_expected(args.expect_map) if args.expect_map else None
    targets: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for path in args.paths:
        try:
            target = validate_target(path)
            if expected is not None:
                check_expected(target, expected)
        except (ValueError, OSError) as exc:
            errors.append({"file_path": str(path), "error": str(exc)})
        else:
            targets.append(target)

    payload = {"targets": targets, "errors": errors}
    print(json.dumps(payload, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
