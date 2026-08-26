"""Layout whitelist for authored plugin and skill folders.

The renderer copies `plugins/` wholesale, so every directory an author adds
there ships to users. Its only per-name filter is `DEV_FILE_NAMES`, and
`.gitignore` cannot hide a folder the repository has to keep. A whitelist is
the one place a development-only folder gets caught, and it catches it in the
source tree instead of after publication.

Tests live in the repository's root `tests/`, never inside a skill: a
`tests/` folder under `plugins/` both ships as dead weight and escapes
`uv run pytest tests`.
"""

import functools
from collections.abc import Callable
from pathlib import Path

import pytest

from plugin_maintenance.render import ignored_path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"

# Union of what each harness's plugin spec allows at a plugin root, so a
# layout either runtime accepts never fails here.
#
# Codex contributes `assets/`, `hooks/`, `scripts/`, `skills/`, `.app.json`,
# `.mcp.json`, and `hooks.json`, per the plugin-creator skill shipped in
# `openai/codex` at `codex-rs/skills/src/assets/samples/plugin-creator/`:
# `scripts/create_basic_plugin.py` creates those four directories behind
# `--with-*` flags and writes the two dot-files, and
# `references/plugin-json-spec.md` maps the manifest's `hooks`, `mcpServers`,
# and `apps` fields onto `./hooks.json`, `./.mcp.json`, and `./.app.json`.
#
# Claude Code contributes `bin/`, `commands/`, `monitors/`, `output-styles/`,
# `themes/`, `workflows/`, `.lsp.json`, and `settings.json`.
#
# `references/` is this repository's own convention for shared runtime
# context; `AGENTS.md` and its `CLAUDE.md` sibling are its authoring-time
# instruction pair, which the renderer skips rather than ships.
PLUGIN_DIRS = {
    ".claude-plugin",
    ".codex-plugin",
    "agents",
    "assets",
    "bin",
    "commands",
    "hooks",
    "monitors",
    "output-styles",
    "references",
    "scripts",
    "skills",
    "themes",
    "workflows",
}
PLUGIN_FILES = {
    ".app.json",
    ".lsp.json",
    ".mcp.json",
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    "hooks.json",
    "THIRD_PARTY_NOTICES.md",
    "settings.json",
}

SKILL_DIRS = {
    "agents",
    "assets",
    "docs",
    "evals",
    "examples",
    "references",
    "scripts",
    "templates",
}
SKILL_FILES = {"SKILL.md", "SKILL.md.j2"}

TESTS_HINT = (
    "a skill's tests belong in the repository's root tests/ and load the "
    "script by path with importlib.util.spec_from_file_location"
)


@functools.cache
def is_ignored() -> Callable[[Path], bool]:
    return ignored_path(REPO_ROOT)


def plugin_dirs() -> list[Path]:
    return sorted(path for path in PLUGINS_ROOT.iterdir() if path.is_dir())


def skill_dirs() -> list[Path]:
    return sorted(
        skill
        for plugin in plugin_dirs()
        for skill in (plugin / "skills").glob("*")
        if skill.is_dir()
    )


def entries(parent: Path) -> list[Path]:
    ignored = is_ignored()
    return sorted(path for path in parent.iterdir() if not ignored(path))


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def unexpected(parent: Path, allowed_dirs: set[str], allowed_files: set[str]) -> list[str]:
    return [
        relative(path)
        for path in entries(parent)
        if path.name not in (allowed_dirs if path.is_dir() else allowed_files)
    ]


@pytest.mark.parametrize("plugin", plugin_dirs(), ids=relative)
def test_plugin_holds_only_whitelisted_entries(plugin: Path) -> None:
    strays = unexpected(plugin, PLUGIN_DIRS, PLUGIN_FILES)

    assert not strays, (
        f"{relative(plugin)} carries entries outside the plugin whitelist: "
        f"{strays}. Allowed directories: {sorted(PLUGIN_DIRS)}. "
        f"Allowed files: {sorted(PLUGIN_FILES)}. If this is a test folder, {TESTS_HINT}."
    )


@pytest.mark.parametrize("skill", skill_dirs(), ids=relative)
def test_skill_holds_only_whitelisted_directories(skill: Path) -> None:
    strays = [
        relative(path) for path in entries(skill) if path.is_dir() and path.name not in SKILL_DIRS
    ]

    assert not strays, (
        f"{relative(skill)} carries directories outside the skill whitelist: "
        f"{strays}. Allowed: {sorted(SKILL_DIRS)}. If this is a test folder, {TESTS_HINT}."
    )


@pytest.mark.parametrize("skill", skill_dirs(), ids=relative)
def test_skill_declares_exactly_one_skill_file(skill: Path) -> None:
    found = sorted(path.name for path in entries(skill) if path.name in SKILL_FILES)

    assert len(found) == 1, (
        f"{relative(skill)} must hold exactly one of {sorted(SKILL_FILES)}; found {found}"
    )
