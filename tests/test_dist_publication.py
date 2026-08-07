"""Marketplace manifests publish from the committed dist trees.

Every manifest entry sources its plugin from the manifest's own `dist/` tree
and resolves to an existing directory; the two catalogs may list different
plugin sets.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def claude_entries() -> list[dict]:
    manifest = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    return manifest["plugins"]


def codex_entries() -> list[dict]:
    manifest = json.loads(
        (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )
    return manifest["plugins"]


def test_claude_manifest_sources_resolve_into_its_dist_tree():
    for entry in claude_entries():
        source = entry["source"]

        assert source == f"./dist/claude-code/{entry['name']}", entry["name"]
        assert (REPO_ROOT / source).is_dir(), entry["name"]


def test_codex_manifest_sources_resolve_into_its_dist_tree():
    for entry in codex_entries():
        path = entry["source"]["path"]

        assert path == f"./dist/codex/{entry['name']}", entry["name"]
        assert (REPO_ROOT / path).is_dir(), entry["name"]


def test_no_manifest_entry_points_into_plugins():
    sources = [entry["source"] for entry in claude_entries()] + [
        entry["source"]["path"] for entry in codex_entries()
    ]

    assert not [source for source in sources if "plugins/" in source]


def test_codex_only_plugin_is_a_valid_catalog_divergence():
    claude_names = {entry["name"] for entry in claude_entries()}
    codex_names = {entry["name"] for entry in codex_entries()}

    assert "run-and-verify-app" in codex_names
    assert "run-and-verify-app" not in claude_names
    assert (REPO_ROOT / "dist" / "codex" / "run-and-verify-app").is_dir()
    assert not (REPO_ROOT / "dist" / "claude-code" / "run-and-verify-app").exists()
