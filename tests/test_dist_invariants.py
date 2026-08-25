"""Purity and reproducibility invariants for the committed dist trees.

Files rendered from `.j2` sources carry no foreign harness vocabulary and no
leftover Jinja markers; neither tree carries templates, legacy dispatch
artifacts, foreign runtime metadata, or development files; published
frontmatter stays inside each harness's portability boundary; consecutive
builds are byte-identical.
"""

import json
import re
from pathlib import Path

import pytest

from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import (
    DIST_DIRS,
    FOREIGN_METADATA_DIRS,
    MATRIX_PATH,
    frontmatter_lines,
    leftover_jinja_markers,
    render_tree,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "README.md"}
DISPATCH_SENTENCE = "Depending on who you are as an AI agent"
LEGACY_METADATA_LINKS = (
    "ai-assistant-harness-adaptation.claude-code",
    "ai-assistant-harness-adaptation.codex",
)
TASK_MANAGEMENT_PATTERNS = Path(
    "work-session-tools/skills/task-management/references/orchestration-patterns.md"
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


def dist_files(harness: str) -> list[Path]:
    dist_root = REPO_ROOT / DIST_DIRS[harness]
    assert dist_root.is_dir(), f"missing committed dist tree: {dist_root}"
    return sorted(path for path in dist_root.rglob("*") if path.is_file())


def rendered_from_template(harness: str, dist_path: Path) -> bool:
    relative = dist_path.relative_to(REPO_ROOT / DIST_DIRS[harness])
    return (REPO_ROOT / "plugins" / relative.parent / f"{relative.name}.j2").is_file()


def template_source(harness: str, dist_path: Path) -> Path:
    relative = dist_path.relative_to(REPO_ROOT / DIST_DIRS[harness])
    return REPO_ROOT / "plugins" / relative.parent / f"{relative.name}.j2"


@pytest.mark.parametrize(
    ("harness", "foreign_harness"), [("ClaudeCode", "Codex"), ("Codex", "ClaudeCode")]
)
def test_rendered_files_carry_no_foreign_callable_names(harness, foreign_harness):
    foreign_names = callable_names(foreign_harness) - callable_names(harness)
    violations = []

    for path in dist_files(harness):
        if not rendered_from_template(harness, path):
            continue
        relative = path.relative_to(REPO_ROOT / DIST_DIRS[harness]).as_posix()
        if relative in FOREIGN_NAME_SCAN_EXEMPT:
            continue
        text = path.read_text(encoding="utf-8")
        for name in sorted(foreign_names):
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
                violations.append(f"{relative}: contains {name}")

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_rendered_files_carry_no_leftover_jinja_markers(harness):
    violations = []

    for path in dist_files(harness):
        if not rendered_from_template(harness, path):
            continue
        template_text = template_source(harness, path).read_text(encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        for marker in leftover_jinja_markers(template_text, text):
            violations.append(f"{path}: contains {marker} outside any raw block")

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_dist_carries_no_templates(harness):
    assert not [path for path in dist_files(harness) if path.name.endswith(".j2")]


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_dist_carries_no_legacy_dispatch_artifacts(harness):
    violations = []

    for path in dist_files(harness):
        if "ai-assistant-harnesses" in path.parts:
            violations.append(f"{path}: legacy harness reference directory")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if DISPATCH_SENTENCE in text:
            violations.append(f"{path}: dispatch sentence")
        for link in LEGACY_METADATA_LINKS:
            if link in text:
                violations.append(f"{path}: metadata link {link}")

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_dist_strips_foreign_runtime_metadata(harness):
    foreign_metadata = FOREIGN_METADATA_DIRS[harness]

    assert not [
        path for path in dist_files(harness) if foreign_metadata in path.parts
    ]


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_dist_carries_no_dev_files(harness):
    assert not [path for path in dist_files(harness) if path.name in DEV_FILE_NAMES]


def dist_frontmatter_files(harness: str) -> list[tuple[str, list[str]]]:
    """Every published file that opens with frontmatter, with its lines."""
    published = []
    for path in dist_files(harness):
        if path.suffix != ".md":
            continue
        lines = frontmatter_lines(path.read_text(encoding="utf-8"))
        if lines is not None:
            published.append(
                (path.relative_to(REPO_ROOT / DIST_DIRS[harness]).as_posix(), lines)
            )
    return published


def test_codex_tree_carries_no_top_level_allowed_tools():
    """Codex documents `name` and `description` only.

    An `allowed-tools` grant reaches the Codex tree under `metadata`, the
    free-form map, never as a top-level key Codex does not read.
    """
    violations = [
        name
        for name, lines in dist_frontmatter_files("Codex")
        for line in lines
        if line.startswith("allowed-tools:")
    ]

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
def test_published_frontmatter_holds_no_duplicate_key(harness):
    """The merge step folds `metadata:` blocks; nothing else may repeat."""
    violations = []

    for name, lines in dist_frontmatter_files(harness):
        seen = set()
        for line in lines:
            match = re.match(r"([A-Za-z_][\w.-]*):", line)
            if not match:
                continue
            if match.group(1) in seen:
                violations.append(f"{name}: duplicate {match.group(1)}")
            seen.add(match.group(1))

    assert not violations, "\n".join(violations)


def task_management_patterns(harness: str) -> str:
    return (REPO_ROOT / DIST_DIRS[harness] / TASK_MANAGEMENT_PATTERNS).read_text(
        encoding="utf-8"
    )


def test_codex_orchestration_patterns_use_plan_arrays():
    text = task_management_patterns("Codex")

    plan_examples = re.findall(r"update_plan\(plan: \[(.*?)\]\)", text, re.DOTALL)

    assert plan_examples
    for example in plan_examples:
        assert set(re.findall(r"\b([a-z_]+):", example)) == {"step", "status"}
        assert example.count('status: "in_progress"') <= 1
        assert set(re.findall(r'status: "([^"]+)"', example)) <= {
            "pending",
            "in_progress",
            "completed",
        }
    for foreign_field in ("taskId", "blockedBy", "metadata"):
        assert foreign_field not in text


def test_codex_orchestration_patterns_use_current_spawn_fields():
    text = task_management_patterns("Codex")

    assert "spawn_agent(" in text
    assert "task_name:" in text
    assert "message:" in text
    for foreign_marker in (
        "description:",
        "prompt:",
        "run_in_background",
        '"Explore"',
        '"haiku"',
    ):
        assert foreign_marker not in text


def tree_snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode & 0o777,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def test_consecutive_full_builds_are_byte_identical(tmp_path):
    snapshots = []
    for build_dir in (tmp_path / "first", tmp_path / "second"):
        run_generators()
        for harness in DIST_DIRS:
            render_tree(REPO_ROOT, harness, build_dir / harness)
        snapshots.append(tree_snapshot(build_dir))

    assert snapshots[0] == snapshots[1]
