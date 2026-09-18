"""The build's own guarantees about the trees it publishes.

Three checks carry the harness-format guarantee between them: a rendered tree
for one harness carries no other harness's callable names, a file rendered
from a template carries no leftover Jinja marker outside its raw blocks, and
consecutive builds are byte-identical. The first two live here rather than
among the rendered-content tests because each needs the template a file was
rendered from, which only the build layer may open; the tree they scan is a
fresh render like everyone else's. Only the freshness check and the
byte-identical rebuild answer for the committed trees, which is what they are
for.
"""

import json
import re
from pathlib import Path

from plugin_maintenance import HARNESSES, REPO_ROOT
from plugin_maintenance.build import stale_paths
from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import (
    DIST_DIRS,
    MATRIX_PATH,
    TEMPLATE_SUFFIX,
    leftover_jinja_markers,
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
        *(callable_names(other) for other in HARNESSES if other != harness)
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


def test_rendered_files_carry_no_leftover_jinja_markers(rendered: Path):
    violations = []

    for path in rendered_files(rendered):
        source = template_source(rendered, path)
        if not source.is_file():
            continue
        template_text = source.read_text(encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        for marker in leftover_jinja_markers(template_text, text):
            violations.append(f"{path}: contains {marker} outside any raw block")

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
