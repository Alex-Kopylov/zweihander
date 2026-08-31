#!/usr/bin/env python3
"""Codex `PostToolUse` hook that delegates documentation language cleanup.

Codex runs this script after the `apply_patch` tool writes files. The script
reads the hook payload from stdin, decides which written files are in scope for
`common/docs-language-guidelines.md`, and starts one headless `codex exec`
sub-agent for each in-scope file.

Design rules:

* The script never rewrites a file itself, and it never asks the calling
  session to do the rewrite. The work goes to a separate `codex exec` process.
* The script never blocks the write. It always exits 0, so a hook failure
  cannot fail the user's session. Exit code 2 is the Codex deny signal, so this
  script must never produce it.
* The sub-agent runs with the Codex hook engine turned off
  (`-c features.hooks=false`). Its own `apply_patch` calls therefore cannot
  re-enter this hook, so the hook cannot recurse.

Hook input fields used (post-tool-use.command.input schema):
    `hook_event_name`, `tool_name`, `tool_input.command`, `cwd`.

Set `CODEX_DOCS_LANG_HOOK_DRY_RUN=1` to print the routing decision instead of
starting a sub-agent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

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

ADD_FILE_MARKER = "*** Add File: "
UPDATE_FILE_MARKER = "*** Update File: "
MOVE_TO_MARKER = "*** Move to: "
DELETE_FILE_MARKER = "*** Delete File: "

SUBAGENT_TIMEOUT_SECONDS = 240
DRY_RUN_ENVIRONMENT_VARIABLE = "CODEX_DOCS_LANG_HOOK_DRY_RUN"

SUBAGENT_PROMPT = """Read the repository file {guidelines}.
Apply the guidelines in that file to exactly one file: {target}.
Change no other file.
If {target} already follows the guidelines, make no change.
Report what you changed."""


def read_event() -> dict | None:
    """Returns the hook payload, or None when stdin holds no usable JSON."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def patched_paths(patch_text: str) -> list[str]:
    """Returns the paths an apply_patch envelope creates or updates.

    Deleted files are left out, because there is nothing left to rewrite. A
    renamed file is reported under its new path only.
    """
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith(ADD_FILE_MARKER):
            paths.append(line[len(ADD_FILE_MARKER) :].strip())
        elif line.startswith(UPDATE_FILE_MARKER):
            paths.append(line[len(UPDATE_FILE_MARKER) :].strip())
        elif line.startswith(MOVE_TO_MARKER) and paths:
            paths[-1] = line[len(MOVE_TO_MARKER) :].strip()
        elif line.startswith(DELETE_FILE_MARKER):
            continue
    return [path for path in paths if path]


def project_root(session_cwd: Path) -> Path:
    """Returns the git top level for the session directory, or the directory."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(session_cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return session_cwd
    if completed.returncode != 0:
        return session_cwd
    top_level = completed.stdout.strip()
    return Path(top_level) if top_level else session_cwd


def relative_to_root(raw_path: str, session_cwd: Path, root: Path) -> PurePosixPath | None:
    """Returns the path relative to the project root, or None when outside it."""
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = session_cwd / candidate
    try:
        resolved = candidate.resolve()
        relative = resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return PurePosixPath(relative.as_posix())


def in_scope(relative_path: PurePosixPath) -> bool:
    """Returns True when the guidelines apply to this project-relative path.

    Both categories match at any depth. A root document name counts wherever it
    sits, and a `docs` directory counts wherever it sits.
    """
    parts = relative_path.parts
    if not parts:
        return False
    if relative_path.name in ROOT_DOCUMENTS:
        return True
    return DOCS_DIRECTORY in parts[:-1] and relative_path.name.endswith(MARKDOWN_SUFFIX)


def targets_from_event(event: dict) -> tuple[Path, list[PurePosixPath]]:
    """Returns the project root and the in-scope files the event just wrote."""
    session_cwd = Path(str(event.get("cwd") or "."))
    root = project_root(session_cwd)

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return root, []
    patch_text = tool_input.get("command")
    if not isinstance(patch_text, str):
        return root, []

    selected: list[PurePosixPath] = []
    for raw_path in patched_paths(patch_text):
        relative = relative_to_root(raw_path, session_cwd, root)
        if relative is None or not in_scope(relative):
            continue
        if not (root / Path(relative)).is_file():
            continue
        if relative not in selected:
            selected.append(relative)
    return root, sorted(selected)


def dispatch(codex_binary: str, root: Path, relative_path: PurePosixPath) -> None:
    """Starts one separate agent process for one file, with a bounded timeout."""
    prompt = SUBAGENT_PROMPT.format(
        guidelines=GUIDELINES_RELATIVE_PATH,
        target=relative_path,
    )
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
        str(root),
        prompt,
    ]
    try:
        subprocess.run(
            command,
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            # Hook stdout is parsed by Codex, so the sub-agent must not write to it.
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=SUBAGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return


def main() -> int:
    event = read_event()
    if event is None:
        return 0
    if event.get("hook_event_name") != "PostToolUse":
        return 0
    if event.get("tool_name") != "apply_patch":
        return 0

    root, relative_paths = targets_from_event(event)
    dry_run = bool(os.environ.get(DRY_RUN_ENVIRONMENT_VARIABLE))

    if not relative_paths:
        if dry_run:
            print("no-dispatch")
        return 0

    if not (root / Path(GUIDELINES_RELATIVE_PATH)).is_file():
        if dry_run:
            print("no-dispatch: guidelines file missing")
        return 0

    if dry_run:
        for relative_path in relative_paths:
            print(f"dispatch: {relative_path}")
        return 0

    codex_binary = shutil.which("codex")
    if codex_binary is None:
        return 0

    for relative_path in relative_paths:
        dispatch(codex_binary, root, relative_path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never fail the calling session because of this hook.
        sys.exit(0)
