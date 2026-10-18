"""Copy upstream Mermaid docs into the plugin; run by the weekly sync workflow, not the build."""

from __future__ import annotations

import os
import re
import shutil

# Reading HEAD without git would mean reimplementing ref resolution (symbolic refs,
# packed-refs, worktree gitdir files); running git itself is the robust way.
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from dataclasses import dataclass
from pathlib import Path

from plugin_maintenance.generators.mermaid_diagrams.generated_docs import (
    PLUGIN_ROOT,
    js_iso_timestamp,
    load_navigation_metadata_from_path,
    update_generated_docs,
    write_bundled_navigation_metadata,
)

REFERENCES_DIR = PLUGIN_ROOT / "skills/mermaid/references"
README_PATH = PLUGIN_ROOT / "README.md"
CONFIG_FILES = [
    "configuration.md",
    "directives.md",
    "layouts.md",
    "math.md",
    "theming.md",
    "tidy-tree.md",
]


class GitNotFoundError(RuntimeError):
    """The sync cannot record the checkout's commit because git is not installed."""

    def __str__(self) -> str:
        """Say what is missing and why the sync needs it."""
        return "git is not on PATH; the Mermaid sync needs it to record the source checkout's commit"


@dataclass(frozen=True)
class ExistingSyncMetadata:
    """Commit and date recorded by the previous sync."""

    commit: str
    date: str


def plugin_relative_path(path: str | Path) -> Path:
    """Resolve `path` against the plugin root unless it is already absolute."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PLUGIN_ROOT / candidate


def git_commit(directory: Path) -> str:
    """Return the HEAD commit of `directory`, or `unknown` when it is not a git checkout."""
    git = shutil.which("git")
    if git is None:
        raise GitNotFoundError
    try:
        # The argv is fixed apart from the checkout path, and no shell parses it.
        result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [git, "-C", str(directory), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return "unknown"
    return result.stdout.strip()


class MissingSyncSourceError(FileNotFoundError):
    """The Mermaid checkout lacks a directory or file the sync copies."""

    def __init__(self, description: str, path: Path) -> None:
        """Name what is missing and where it was expected."""
        super().__init__(f"Missing Mermaid {description}: {path}")


def require_path(path: Path, description: str) -> None:
    """Raise MissingSyncSourceError naming `description` when `path` is missing."""
    if not path.exists():
        raise MissingSyncSourceError(description, path)


def preflight_sync_source(source_dir: Path) -> None:
    """Check the Mermaid checkout has every directory and file the sync copies."""
    syntax_dir = source_dir / "docs/syntax"
    config_dir = source_dir / "docs/config"
    docs_navigation_path = source_dir / "packages/mermaid/src/docs/.vitepress/config.ts"
    require_path(syntax_dir, "syntax directory")
    require_path(config_dir, "config directory")
    require_path(docs_navigation_path, "docs navigation file")
    for file in CONFIG_FILES:
        require_path(config_dir / file, f"config doc {file}")


def read_existing_sync_metadata() -> ExistingSyncMetadata | None:
    """Return the commit and date recorded in the plugin README, or None."""
    if not README_PATH.exists():
        return None
    match = re.search(
        r"Last synced from Mermaid: [^@]+ @ ([0-9a-f]+|unknown) on ([^\n]+)",
        README_PATH.read_text(encoding="utf-8"),
    )
    return ExistingSyncMetadata(match.group(1), match.group(2).strip()) if match else None


def copy_docs(source_dir: Path) -> None:
    """Replace the bundled references with the checkout's syntax and config docs."""
    syntax_dir = source_dir / "docs/syntax"
    config_dir = source_dir / "docs/config"

    shutil.rmtree(REFERENCES_DIR, ignore_errors=True)
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    for source_path in sorted(syntax_dir.iterdir(), key=lambda path: path.name):
        if source_path.suffix == ".md":
            shutil.copyfile(source_path, REFERENCES_DIR / source_path.name)

    for file in CONFIG_FILES:
        shutil.copyfile(config_dir / file, REFERENCES_DIR / f"config-{file}")


def sync_mermaid_docs(source: str | Path = "mermaid-source") -> None:
    """Sync references from a Mermaid checkout and regenerate the plugin docs."""
    source_dir = plugin_relative_path(source)
    docs_navigation_path = source_dir / "packages/mermaid/src/docs/.vitepress/config.ts"
    source_commit = git_commit(source_dir)
    existing_sync_metadata = read_existing_sync_metadata()

    os.environ["MERMAID_SYNC_SOURCE"] = "mermaid-js/mermaid"
    os.environ["MERMAID_SOURCE_COMMIT"] = source_commit
    os.environ["MERMAID_SYNC_DATE"] = (
        existing_sync_metadata.date
        if existing_sync_metadata and existing_sync_metadata.commit == source_commit
        else js_iso_timestamp()
    )
    os.environ["MERMAID_DOCS_NAVIGATION"] = os.path.relpath(
        docs_navigation_path,
        PLUGIN_ROOT,
    )

    preflight_sync_source(source_dir)
    write_bundled_navigation_metadata(load_navigation_metadata_from_path(docs_navigation_path))
    copy_docs(source_dir)
    update_generated_docs()


def main(argv: list[str] | None = None) -> int:
    """Sync from the checkout named in `argv`; return the process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    source = argv[0] if argv else "mermaid-source"
    sync_mermaid_docs(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
