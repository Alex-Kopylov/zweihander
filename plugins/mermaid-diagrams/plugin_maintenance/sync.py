from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from plugin_maintenance.generated_docs import (
    PLUGIN_ROOT,
    js_iso_timestamp,
    update_generated_docs,
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


@dataclass(frozen=True)
class ExistingSyncMetadata:
    commit: str
    date: str


def plugin_relative_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PLUGIN_ROOT / candidate


def git_commit(directory: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def require_path(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing Mermaid {description}: {path}")


def preflight_sync_source(source_dir: Path) -> None:
    syntax_dir = source_dir / "docs/syntax"
    config_dir = source_dir / "docs/config"
    docs_navigation_path = (
        source_dir / "packages/mermaid/src/docs/.vitepress/config.ts"
    )
    require_path(syntax_dir, "syntax directory")
    require_path(config_dir, "config directory")
    require_path(docs_navigation_path, "docs navigation file")
    for file in CONFIG_FILES:
        require_path(config_dir / file, f"config doc {file}")


def read_existing_sync_metadata() -> ExistingSyncMetadata | None:
    if not README_PATH.exists():
        return None
    match = re.search(
        r"Last synced from Mermaid: [^@]+ @ ([0-9a-f]+|unknown) on ([^\n]+)",
        README_PATH.read_text(encoding="utf-8"),
    )
    return (
        ExistingSyncMetadata(match.group(1), match.group(2).strip())
        if match
        else None
    )


def copy_docs(source_dir: Path) -> None:
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
    source_dir = plugin_relative_path(source)
    docs_navigation_path = (
        source_dir / "packages/mermaid/src/docs/.vitepress/config.ts"
    )
    source_commit = git_commit(source_dir)
    existing_sync_metadata = read_existing_sync_metadata()

    os.environ["MERMAID_SYNC_SOURCE"] = "mermaid-js/mermaid"
    os.environ["MERMAID_SOURCE_COMMIT"] = source_commit
    os.environ["MERMAID_SYNC_DATE"] = (
        existing_sync_metadata.date
        if existing_sync_metadata
        and existing_sync_metadata.commit == source_commit
        else js_iso_timestamp()
    )
    os.environ["MERMAID_DOCS_NAVIGATION"] = os.path.relpath(
        docs_navigation_path,
        PLUGIN_ROOT,
    )

    preflight_sync_source(source_dir)
    copy_docs(source_dir)
    update_generated_docs()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    source = argv[0] if argv else "mermaid-source"
    sync_mermaid_docs(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
