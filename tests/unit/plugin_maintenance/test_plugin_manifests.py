"""Both runtime manifests of a plugin declare the same version.

A rendered tree carries only its own harness's metadata directory, so the two
manifests can be compared in one place only: the authored tree, which the
build layer is the one reader of.
"""

import json

from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import PLUGIN_METADATA_DIRS

PLUGINS_ROOT = REPO_ROOT / "plugins"


def test_both_runtime_manifests_agree_on_version() -> None:
    disagreements = []

    for plugin in sorted(path for path in PLUGINS_ROOT.iterdir() if path.is_dir()):
        versions = {
            directory: json.loads((plugin / directory / "plugin.json").read_text(encoding="utf-8"))["version"]
            for directory in sorted(PLUGIN_METADATA_DIRS)
            if (plugin / directory / "plugin.json").is_file()
        }
        if len(set(versions.values())) > 1:
            disagreements.append(f"{plugin.name}: {versions}")

    assert not disagreements, "a plugin ships one version to every runtime:\n" + "\n".join(disagreements)
