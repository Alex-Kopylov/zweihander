"""The build's own guarantees about the trees it publishes.

The foreign-callable-name scan needs the authored tree to identify template
outputs, so it lives in the build layer. The other checks cover reproducible
builds and freshness of committed distribution trees. Jinja handles template
syntax; literal braces in rendered content are valid output.
"""

import json
import re
from pathlib import Path

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.build import stale_paths
from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import (
    DIST_DIRS,
    MATRIX_PATH,
    TEMPLATE_SUFFIX,
    Harness,
    render_tree,
    tree_snapshot,
)


# Successor of the retired AGNOSTIC_EXEMPT: dist-tree-relative paths whose
# subject matter is another harness, skipped by the foreign-name scan.
FOREIGN_NAME_SCAN_EXEMPT = {
    "dev-workflow/skills/version-bumper/references/claude-code-marketplace-manifests.md",
    "dev-workflow/skills/version-bumper/references/claude-code-plugin-manifests.md",
    "dev-workflow/skills/version-bumper/references/codex-marketplace-manifests.md",
    "dev-workflow/skills/version-bumper/references/codex-plugin-manifests.md",
    "ai-assistant-ops/skills/adapt-skill-for-ai-harness/references/harness-action-matrix.json",
}


def matrix() -> dict:
    return json.loads((REPO_ROOT / MATRIX_PATH).read_text(encoding="utf-8"))


def callable_names(harness: str) -> set[str]:
    return {
        action[harness]["name"]
        for action in matrix()["actions"].values()
        if action["callable"]
    }


def foreign_callable_names(harness: str) -> set[str]:
    """Names that belong to some other harness and not to this one."""
    return set().union(
        *(callable_names(other) for other in Harness if other != harness)
    ) - callable_names(harness)


def rendered_files(tree: Path) -> list[Path]:
    return sorted(path for path in tree.rglob("*") if path.is_file())


def template_source(tree: Path, rendered_path: Path) -> Path:
    relative = rendered_path.relative_to(tree)
    return (
        REPO_ROOT / "plugins" / relative.parent / f"{relative.name}{TEMPLATE_SUFFIX}"
    )


def test_rendered_files_carry_no_foreign_callable_names(harness, rendered: Path):
    """A callable name only a template can introduce, so only they are scanned.

    Plain files copy byte-for-byte and say `Agent` as an ordinary English
    word; a template that writes it has bypassed the action map.
    """
    foreign_names = foreign_callable_names(harness)
    violations = []

    for path in rendered_files(rendered):
        if not template_source(rendered, path).is_file():
            continue
        relative = path.relative_to(rendered).as_posix()
        if relative in FOREIGN_NAME_SCAN_EXEMPT:
            continue
        text = path.read_text(encoding="utf-8")
        for name in sorted(foreign_names):
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
                violations.append(f"{relative}: contains {name}")

    assert not violations, "\n".join(violations)


def test_consecutive_full_builds_are_byte_identical(tmp_path):
    snapshots = []
    for build_dir in (tmp_path / "first", tmp_path / "second"):
        run_generators()
        for harness in DIST_DIRS:
            render_tree(REPO_ROOT, harness, build_dir / harness)
        snapshots.append(tree_snapshot(build_dir))

    assert snapshots[0] == snapshots[1]


def test_committed_trees_match_a_fresh_render():
    """No hand edit survives in `dist/`: every byte comes from the renderer."""
    assert stale_paths() == []
