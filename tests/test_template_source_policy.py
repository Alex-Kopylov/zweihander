"""Authoring policy for template sources under `plugins/`.

Templates take callable names from the action map or the wrapper filter,
never as hardcoded harness-specific literals, and never select names inside
harness conditionals. No output path may have both a plain and a template
source.
"""

import json
import re
from pathlib import Path

from plugin_maintenance.render import MATRIX_PATH, TEMPLATE_SUFFIX


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"

HARNESS_CONDITIONAL_BLOCK = re.compile(
    r"\{%-?\s*if\s+harness[\s\S]*?\{%-?\s*endif\s*-?%\}"
)
DOLLAR_INVOCATION = re.compile(r"\$[a-z0-9][a-z0-9-]*(:[a-z0-9_-]+)?")


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


def test_no_plain_and_template_source_collisions():
    collisions = [
        str(path.relative_to(REPO_ROOT))
        for path in template_sources()
        if path.with_name(path.name[: -len(TEMPLATE_SUFFIX)]).exists()
    ]

    assert not collisions, "\n".join(collisions)
