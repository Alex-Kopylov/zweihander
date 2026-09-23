"""What a freshly rendered harness tree does and does not carry.

Every assertion reads the tree a user installs: no templates, no legacy
dispatch artifacts, no foreign runtime metadata, no development files, and
frontmatter that stays inside the harness's portability boundary.
"""

import json
import re
from pathlib import Path

import pytest

from plugin_maintenance.render import (
    DEV_FILE_NAMES,
    FOREIGN_METADATA_DIRS,
    FRONTMATTER_MATRIX_NAME,
    MATRIX_PATH,
    TEMPLATE_SUFFIX,
    VERBATIM_FORM,
    Harness,
    frontmatter_lines,
)


DISPATCH_SENTENCE = "Depending on who you are as an AI agent"
LEGACY_METADATA_LINKS = (
    "ai-assistant-harness-adaptation.claude-code",
    "ai-assistant-harness-adaptation.codex",
)
# The matrices ship with the adaptation skill, so their location inside a tree
# is the renderer's own path with the authored root dropped.
MATRIX_IN_TREE = Path(*MATRIX_PATH.parts[1:])
TASK_MANAGEMENT_PATTERNS = Path(
    "work-session-tools/skills/task-management/references/orchestration-patterns.md"
)


def tree_files(rendered: Path) -> list[Path]:
    return sorted(path for path in rendered.rglob("*") if path.is_file())


def test_tree_carries_no_templates(rendered: Path) -> None:
    assert not [
        path for path in tree_files(rendered) if path.name.endswith(TEMPLATE_SUFFIX)
    ]


def test_tree_carries_no_legacy_dispatch_artifacts(rendered: Path) -> None:
    violations = []

    for path in tree_files(rendered):
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


def test_tree_strips_foreign_runtime_metadata(rendered: Path, harness: str) -> None:
    foreign_metadata = FOREIGN_METADATA_DIRS[harness]

    assert not [
        path for path in tree_files(rendered) if foreign_metadata in path.parts
    ]


def test_tree_carries_no_dev_files(rendered: Path) -> None:
    assert not [path for path in tree_files(rendered) if path.name in DEV_FILE_NAMES]


def tree_frontmatter_files(rendered: Path) -> list[tuple[str, list[str]]]:
    """Every published file that opens with frontmatter, with its lines."""
    published = []
    for path in tree_files(rendered):
        if path.suffix != ".md":
            continue
        lines = frontmatter_lines(path.read_text(encoding="utf-8"))
        if lines is not None:
            published.append((path.relative_to(rendered).as_posix(), lines))
    return published


def metadata_placed_keys(rendered: Path, harness: str) -> set[str]:
    """Keys the matrix keeps out of this harness's top-level frontmatter."""
    matrix = json.loads(
        (rendered / MATRIX_IN_TREE)
        .with_name(FRONTMATTER_MATRIX_NAME)
        .read_text(encoding="utf-8")
    )
    return {
        key
        for key, entry in matrix["keys"].items()
        if entry["form"] != VERBATIM_FORM and entry[harness]["placement"] == "metadata"
    }


def test_tree_carries_no_top_level_key_the_harness_does_not_read(
    rendered: Path, harness: str
) -> None:
    """A key placed under `metadata` never reaches the top level.

    `metadata` is the free-form map every harness accepts, so a key a harness
    does not read travels there instead of sitting at the top level.
    """
    keys = metadata_placed_keys(rendered, harness)
    violations = [
        f"{name}: {key}"
        for name, lines in tree_frontmatter_files(rendered)
        for line in lines
        for key in keys
        if line.startswith(f"{key}:")
    ]

    assert not violations, "\n".join(violations)


@pytest.fixture
def orchestration_patterns(rendered: Path) -> str:
    return (rendered / TASK_MANAGEMENT_PATTERNS).read_text(encoding="utf-8")


@pytest.mark.harness(Harness.CODEX)
def test_codex_orchestration_patterns_use_plan_arrays(
    orchestration_patterns: str,
) -> None:
    """Plan items quote their keys, the way Codex sends them on the wire.

    `plan` stays an unquoted named argument, matching how every call example
    in this document names its arguments. The objects inside the list are
    object literals, so their keys carry quotes — the same convention the
    Claude Code branch uses for a nested `metadata` object.
    """
    plan_examples = re.findall(
        r"update_plan\(plan: \[(.*?)\]\)", orchestration_patterns, re.DOTALL
    )

    assert plan_examples
    for example in plan_examples:
        assert set(re.findall(r'"([a-z_]+)":', example)) == {"step", "status"}
        assert not re.search(r"(?<![\"\w])(step|status):", example)
        assert example.count('"status": "in_progress"') <= 1
        assert set(re.findall(r'"status": "([^"]+)"', example)) <= {
            "pending",
            "in_progress",
            "completed",
        }
    for foreign_field in ("taskId", "blockedBy", "metadata"):
        assert foreign_field not in orchestration_patterns


@pytest.mark.harness(Harness.CODEX)
def test_codex_orchestration_patterns_use_current_spawn_fields(
    orchestration_patterns: str,
) -> None:
    assert "spawn_agent(" in orchestration_patterns
    assert "task_name:" in orchestration_patterns
    assert "message:" in orchestration_patterns
    for foreign_marker in (
        "description:",
        "prompt:",
        "run_in_background",
        '"Explore"',
        '"haiku"',
    ):
        assert foreign_marker not in orchestration_patterns
