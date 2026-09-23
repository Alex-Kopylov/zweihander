"""Both runtime manifests of a plugin declare the same version.

A rendered tree carries only its own harness's metadata directory, so the two
manifests can be compared in one place only: the authored tree, which the
build layer is the one reader of.
"""

import json

from plugin_maintenance import REPO_ROOT


PLUGINS_ROOT = REPO_ROOT / "plugins"
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


def test_both_runtime_manifests_agree_on_version() -> None:
    disagreements = []

    for plugin in sorted(path for path in PLUGINS_ROOT.iterdir() if path.is_dir()):
        versions = {
            manifest: json.loads((plugin / manifest).read_text(encoding="utf-8"))[
                "version"
            ]
            for manifest in MANIFESTS
            if (plugin / manifest).is_file()
        }
        if len(set(versions.values())) > 1:
            disagreements.append(f"{plugin.name}: {versions}")

    assert not disagreements, (
        "a plugin ships one version to every runtime:\n" + "\n".join(disagreements)
    )
