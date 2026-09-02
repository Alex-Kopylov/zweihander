#!/usr/bin/env python3
"""Codex `PostToolUse` hook that delegates documentation language cleanup.

The script reads the hook payload from stdin, picks the written files that are
in scope for `common/docs-language-guidelines.md`, and starts one headless
`codex exec` sub-agent per file. It never rewrites a file itself, and it always
exits 0 so a hook failure cannot fail the calling session.

The sub-agent runs with the hook engine off (`-c features.hooks=false`), so its
own `apply_patch` calls cannot re-enter this hook.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

# `.codex/hooks/docs_language_guard.py` sits two directories below the root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

GUIDELINES_RELATIVE_PATH = PurePosixPath("common/docs-language-guidelines.md")

# Category 1 of the guidelines scope: governance and project documents, matched
# by file name at any depth.
ROOT_DOCUMENTS = frozenset(
    {
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "README.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "SUPPORT.md",
        "GOVERNANCE.md",
        "MAINTAINERS.md",
        "AUTHORS.md",
        "CONTRIBUTORS.md",
        "NOTICE.md",
    }
)

# Category 2 of the guidelines scope: `**/docs/**/*.md`.
DOCS_DIRECTORY = "docs"
MARKDOWN_SUFFIX = ".md"

# The model the separate agent runs on.
SUBAGENT_MODEL = "gpt-5.6-luna"

SUBAGENT_TIMEOUT_SECONDS = 240

# `*** Delete File:` is left out: a deleted file has no prose left to fix.
PATCH_PATH_PATTERN = re.compile(
    r"^\*\*\* (?:Add File|Update File): (.+)$", re.MULTILINE
)

SUBAGENT_PROMPT = """Read the repository file {guidelines}.
Apply the guidelines in that file to exactly one file: {target}.
Change no other file.
If {target} already follows the guidelines, make no change."""


def patched_paths(patch_text: str) -> list[str]:
    """Returns the paths an apply_patch envelope adds or updates."""
    return [path.strip() for path in PATCH_PATH_PATTERN.findall(patch_text) if path.strip()]


def relative_to_root(raw_path: str, session_cwd: Path, root: Path) -> PurePosixPath | None:
    """Returns the path relative to the project root, or None when outside it."""
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = session_cwd / candidate
    try:
        relative = candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return PurePosixPath(relative.as_posix())


def in_scope(relative_path: PurePosixPath) -> bool:
    """Returns True when the guidelines apply to this project-relative path.

    Both categories match at any depth. A root document name counts wherever it
    sits, and a `docs` directory counts wherever it sits.
    """
    if relative_path.name in ROOT_DOCUMENTS:
        return True
    parts = relative_path.parts
    return DOCS_DIRECTORY in parts[:-1] and relative_path.name.endswith(MARKDOWN_SUFFIX)


def targets_from_event(event: dict, root: Path = PROJECT_ROOT) -> list[PurePosixPath]:
    """Returns the in-scope files the event just wrote, sorted and deduplicated."""
    session_cwd = Path(str(event.get("cwd") or "."))
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    patch_text = tool_input.get("command")
    if not isinstance(patch_text, str):
        return []

    selected = {
        relative
        for raw_path in patched_paths(patch_text)
        if (relative := relative_to_root(raw_path, session_cwd, root)) is not None
        and in_scope(relative)
        and (root / Path(relative)).is_file()
    }
    return sorted(selected)


def revert_out_of_scope_changes(relative_path: PurePosixPath, root: Path) -> None:
    """Reverts any file the sub-agent touched other than `relative_path`.

    `--sandbox workspace-write` only keeps the sub-agent inside the repo, not
    inside its one assigned file, so this is the actual write boundary.
    """
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return
    if status.returncode != 0:
        return
    target = str(relative_path)
    stray_paths = {
        line[3:].strip()
        for line in status.stdout.splitlines()
        if line[3:].strip() and line[3:].strip() != target
    }
    for stray_path in stray_paths:
        subprocess.run(
            ["git", "checkout", "--", stray_path],
            cwd=str(root),
            capture_output=True,
            timeout=30,
            check=False,
        )
        subprocess.run(
            ["git", "clean", "-fd", "--", stray_path],
            cwd=str(root),
            capture_output=True,
            timeout=30,
            check=False,
        )


def dispatch(codex_binary: str, relative_path: PurePosixPath) -> None:
    """Starts one separate agent process for one file, with a bounded timeout."""
    command = [
        codex_binary,
        "exec",
        # Loop guard: the sub-agent runs with the whole hook engine disabled.
        "-c",
        "features.hooks=false",
        "-m",
        SUBAGENT_MODEL,
        "--sandbox",
        "workspace-write",
        "--cd",
        str(PROJECT_ROOT),
        SUBAGENT_PROMPT.format(
            guidelines=GUIDELINES_RELATIVE_PATH, target=relative_path
        ),
    ]
    try:
        subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            # Hook stdout is parsed by Codex, so the sub-agent must not write to it.
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=SUBAGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return
    revert_out_of_scope_changes(relative_path, PROJECT_ROOT)


def main() -> int:
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        return 0
    if event.get("hook_event_name") != "PostToolUse":
        return 0
    if event.get("tool_name") != "apply_patch":
        return 0

    targets = targets_from_event(event)
    if not targets:
        return 0
    if not (PROJECT_ROOT / Path(GUIDELINES_RELATIVE_PATH)).is_file():
        return 0

    codex_binary = shutil.which("codex")
    if codex_binary is None:
        return 0

    for relative_path in targets:
        dispatch(codex_binary, relative_path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never fail the calling session because of this hook.
        sys.exit(0)
