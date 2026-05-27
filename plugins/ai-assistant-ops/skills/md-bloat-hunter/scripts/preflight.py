#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_root_for(path: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], path.parent)
    if result.returncode != 0:
        raise ValueError("outside a git worktree")
    return Path(result.stdout.strip()).resolve()


def validate_target(path: Path) -> dict[str, str]:
    resolved = path.expanduser().resolve()
    if path.suffix != ".md":
        raise ValueError("target must have a .md extension")
    if path.is_symlink() or resolved.is_symlink():
        raise ValueError("target must not be a symlink")
    if not resolved.is_file():
        raise ValueError("target must be a regular file")

    repo_root = git_root_for(resolved)
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("target real path is outside the git root") from exc

    relative = resolved.relative_to(repo_root)
    tracked = run_git(["ls-files", "--error-unmatch", "--", str(relative)], repo_root)
    if tracked.returncode != 0:
        raise ValueError("target is not tracked by git")

    status = run_git(["status", "--porcelain", "--", str(relative)], repo_root)
    if status.returncode != 0:
        raise ValueError(status.stderr.strip() or "git status failed")
    if status.stdout.strip():
        raise ValueError("target has staged or unstaged changes")

    return {
        "file_path": str(resolved),
        "repo_root": str(repo_root),
        "git_relative_path": str(relative),
        "sha256": sha256(resolved),
    }


def load_expected(path: Path) -> dict[str, str]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    expected: dict[str, str] = {}
    for item in payload.get("targets", []):
        expected[str(Path(item["file_path"]).resolve())] = str(item["sha256"])
    return expected


def main() -> int:
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
                expected_hash = expected.get(target["file_path"])
                if expected_hash is None:
                    raise ValueError("target was not present in the original preflight map")
                if expected_hash != target["sha256"]:
                    raise ValueError("target content hash changed since preflight")
            targets.append(target)
        except Exception as exc:
            errors.append({"file_path": str(path), "error": str(exc)})

    payload = {"targets": targets, "errors": errors}
    print(json.dumps(payload, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
