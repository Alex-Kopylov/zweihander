"""Authoring policy for skill, agent, and template sources under `plugins/`.

Templates take callable names from the action map or the wrapper filter,
never as hardcoded harness-specific literals, and never select names inside
harness conditionals. No output path may have both a plain and a template
source. Frontmatter stays inside the portability boundary: an `allowed-tools`
grant is declared through the renderer global, and every `metadata` entry sits
under a declared namespace.
"""

import json
import re
from pathlib import Path

from plugin_maintenance.render import MATRIX_PATH, TEMPLATE_SUFFIX, frontmatter_lines


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
METADATA_NAMESPACES = {"allowed-tools", "references", "agents", "skills", "origin"}
TASK_MANAGEMENT_PATTERNS_TEMPLATE = (
    PLUGINS_ROOT
    / "work-session-tools"
    / "skills"
    / "task-management"
    / "references"
    / "orchestration-patterns.md.j2"
)

HARNESS_CONDITIONAL_BLOCK = re.compile(
    r"\{%-?\s*if\s+harness[\s\S]*?\{%-?\s*endif\s*-?%\}"
)
DOLLAR_INVOCATION = re.compile(r"\$[a-z0-9][a-z0-9-]*(:[a-z0-9_-]+)?")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)


def template_sources() -> list[Path]:
    return sorted(PLUGINS_ROOT.rglob(f"*{TEMPLATE_SUFFIX}"))


def mapped_callable_names() -> set[str]:
    matrix = json.loads((REPO_ROOT / MATRIX_PATH).read_text(encoding="utf-8"))
    return {
        action[assistant]["name"]
        for action in matrix["actions"].values()
        if action["callable"]
        for assistant in matrix["assistants"]
    }


def test_templates_never_hardcode_matrix_mapped_callable_names():
    violations = []

    for path in template_sources():
        text = path.read_text(encoding="utf-8")
        for name in sorted(mapped_callable_names()):
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
                violations.append(f"{path.relative_to(REPO_ROOT)}: literal {name}")

    assert not violations, (
        "templates must resolve callable names through the action map:\n"
        + "\n".join(violations)
    )


def test_templates_never_select_callable_names_inside_harness_conditionals():
    violations = []

    for path in template_sources():
        text = path.read_text(encoding="utf-8")
        for block in HARNESS_CONDITIONAL_BLOCK.findall(text):
            if "Skill(" in block or "| call" in block or DOLLAR_INVOCATION.search(block):
                violations.append(str(path.relative_to(REPO_ROOT)))
                break

    assert not violations, (
        "harness conditionals are for divergent narrative only; callable "
        "references belong outside them:\n" + "\n".join(violations)
    )


def test_task_management_pattern_sections_stay_outside_harness_conditionals():
    text = TASK_MANAGEMENT_PATTERNS_TEMPLATE.read_text(encoding="utf-8")
    conditional_blocks = HARNESS_CONDITIONAL_BLOCK.findall(text)

    assert conditional_blocks
    assert not [
        block for block in conditional_blocks if MARKDOWN_HEADING.search(block)
    ], (
        "keep shared document sections outside harness conditionals; branch only "
        "the local syntax or behavior"
    )


def frontmatter_carrying_sources() -> list[Path]:
    """Every skill and agent file under `plugins/`, template or plain."""
    return sorted(
        path
        for pattern in ("**/SKILL.md", "**/agents/*.md")
        for suffix in ("", TEMPLATE_SUFFIX)
        for path in PLUGINS_ROOT.glob(f"{pattern}{suffix}")
    )


def test_sources_never_hand_write_allowed_tools():
    """`allowed-tools` is the one frontmatter key the harnesses disagree on.

    Claude Code reads it at the top level and Codex does not read it there at
    all, so the placement is the renderer's call, not the author's.
    """
    violations = [
        str(path.relative_to(REPO_ROOT))
        for path in frontmatter_carrying_sources()
        for line in frontmatter_lines(path.read_text(encoding="utf-8")) or []
        if line.startswith("allowed-tools:")
    ]

    assert not violations, (
        "declare an allowed-tools grant through the allowed_tools global so "
        "each harness gets the placement it reads:\n" + "\n".join(violations)
    )


def test_frontmatter_metadata_entries_sit_under_a_namespace():
    violations = []

    for path in frontmatter_carrying_sources():
        lines = frontmatter_lines(path.read_text(encoding="utf-8")) or []
        if "metadata:" not in lines:
            continue
        block = lines[lines.index("metadata:") + 1 :]
        for line in block:
            if line and not line.startswith(" "):
                break
            entry = line.strip()
            if not line.startswith("  ") or line.startswith("   ") or not entry:
                continue
            namespace = entry.split(":", 1)[0].strip('"')
            if namespace not in METADATA_NAMESPACES:
                violations.append(f"{path.relative_to(REPO_ROOT)}: {namespace}")

    assert not violations, (
        "group frontmatter metadata one level deep under "
        f"{', '.join(sorted(METADATA_NAMESPACES))}:\n" + "\n".join(violations)
    )


def test_no_plain_and_template_source_collisions():
    collisions = [
        str(path.relative_to(REPO_ROOT))
        for path in template_sources()
        if path.with_name(path.name[: -len(TEMPLATE_SUFFIX)]).exists()
    ]

    assert not collisions, "\n".join(collisions)
