"""Build tooling for the plugin marketplace: stage-1 generators, stage-2 renderer."""

from pathlib import Path

from plugin_maintenance.render import HARNESS_MANIFESTS

REPO_ROOT = Path(__file__).resolve().parents[1]
# Derived from the renderer's harness-to-manifest mapping: manifest membership
# is what makes a harness real, so the test suite parametrizes over this rather
# than restating the names.
HARNESSES = tuple(HARNESS_MANIFESTS)
