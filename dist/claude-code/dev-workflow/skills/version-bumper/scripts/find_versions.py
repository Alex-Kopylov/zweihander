#!/usr/bin/env python3
"""Scan a project directory for files containing version strings.

Usage:
    python find_versions.py [directory]

Prints JSON with discovered version entries:
    [{
      "file": "pyproject.toml",
      "version": "0.4.0",
      "line": 5,
      "pattern": "project",
      "reference": "references/python-project-files.md"
    }]
"""

import json
import re
import sys
from pathlib import Path

PATTERNS: list[tuple[str, str, str, re.Pattern[str]]] = [
    (
        "pyproject.toml",
        "project",
        "references/python-project-files.md",
        re.compile(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', re.MULTILINE),
    ),
    (
        "setup.cfg",
        "metadata",
        "references/python-project-files.md",
        re.compile(r'^version\s*=\s*(\d+\.\d+\.\d+)', re.MULTILINE),
    ),
    (
        "package.json",
        "package",
        "references/node-packages.md",
        re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"'),
    ),
    (
        "plugin.json",
        "plugin",
        "references/generic-plugin-manifests.md",
        re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"'),
    ),
    (
        "marketplace.json",
        "marketplace",
        "references/marketplace-manifests.md",
        re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"'),
    ),
]

VERSION_JSON_RE = re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"')

GLOB_PATTERNS: list[tuple[str, str, str, re.Pattern[str]]] = [
    (
        "**/__init__.py",
        "dunder",
        "references/python-module-versions.md",
        re.compile(r'^__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']', re.MULTILINE),
    ),
    (
        "**/app.py",
        "fastapi",
        "references/fastapi-apps.md",
        re.compile(r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'),
    ),
    (
        "**/main.py",
        "fastapi",
        "references/fastapi-apps.md",
        re.compile(r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'),
    ),
    (
        "**/.claude-plugin/plugin.json",
        "claude-code-plugin-manifest",
        "references/claude-code-plugin-manifests.md",
        VERSION_JSON_RE,
    ),
    (
        "**/.codex-plugin/plugin.json",
        "codex-plugin-manifest",
        "references/codex-plugin-manifests.md",
        VERSION_JSON_RE,
    ),
    (
        "**/.claude-plugin/marketplace.json",
        "claude-code-marketplace-manifest",
        "references/claude-code-marketplace-manifests.md",
        VERSION_JSON_RE,
    ),
    (
        "**/.agents/plugins/marketplace.json",
        "codex-marketplace-manifest",
        "references/codex-marketplace-manifests.md",
        VERSION_JSON_RE,
    ),
]


def find_versions(root: Path) -> list[dict[str, str | int]]:
    results: list[dict[str, str | int]] = []

    for filename, pattern_name, reference, regex in PATTERNS:
        path = root / filename
        if path.exists():
            _search_file(path=path, regex=regex, pattern_name=pattern_name, reference=reference, results=results)

    for glob, pattern_name, reference, regex in GLOB_PATTERNS:
        for path in sorted(root.glob(glob)):
            if ".venv" in path.parts or "node_modules" in path.parts:
                continue
            _search_file(path=path, regex=regex, pattern_name=pattern_name, reference=reference, results=results)

    return results


def _search_file(
    *,
    path: Path,
    regex: re.Pattern[str],
    pattern_name: str,
    reference: str,
    results: list[dict[str, str | int]],
) -> None:
    try:
        content = path.read_text()
    except (OSError, UnicodeDecodeError):
        return
    match = regex.search(content)
    if match:
        line_num = content[: match.start()].count("\n") + 1
        results.append({
            "file": str(path),
            "version": match.group(1),
            "line": line_num,
            "pattern": pattern_name,
            "reference": reference,
        })


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    versions = find_versions(root)
    print(json.dumps(versions, indent=2))
