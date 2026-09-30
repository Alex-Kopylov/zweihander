"""Marketplace manifests publish the trees the renderer produces.

Every manifest entry sources its plugin from the manifest's own published
tree, and each rendered tree carries exactly the plugins its manifest lists.
Whether the committed trees are current is the build layer's question.
"""

import json
from pathlib import Path

from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import HARNESS_MANIFESTS, Harness, manifest_plugin_names


def marketplace_entries(harness: Harness) -> list[dict]:
    manifest = json.loads((REPO_ROOT / HARNESS_MANIFESTS[harness]).read_text(encoding="utf-8"))
    return manifest["plugins"]


def test_claude_manifest_sources_resolve_into_its_dist_tree():
    for entry in marketplace_entries(Harness.CLAUDE_CODE):
        assert entry["source"] == f"./dist/claude-code/{entry['name']}", entry["name"]


def test_codex_manifest_sources_resolve_into_its_dist_tree():
    for entry in marketplace_entries(Harness.CODEX):
        assert entry["source"]["path"] == f"./dist/codex/{entry['name']}", entry["name"]


def test_rendered_tree_carries_exactly_its_manifest_plugins(rendered: Path, harness: str) -> None:
    """Membership is the manifest's call, so a tree holds that list and no more."""
    listed = manifest_plugin_names(REPO_ROOT / HARNESS_MANIFESTS[harness])

    assert sorted(path.name for path in rendered.iterdir()) == sorted(listed)


def test_codex_only_plugin_is_a_valid_catalog_divergence():
    claude_names = {entry["name"] for entry in marketplace_entries(Harness.CLAUDE_CODE)}
    codex_names = {entry["name"] for entry in marketplace_entries(Harness.CODEX)}

    assert "run-and-verify-app" in codex_names
    assert "run-and-verify-app" not in claude_names
