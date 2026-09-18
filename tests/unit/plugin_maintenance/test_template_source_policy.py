"""Authoring policy for the sources under `plugins/`, and for the test tree.

Templates take callable names from the action map or the wrapper filter,
never as hardcoded harness-specific literals, and never select names inside
harness conditionals. No output path may have both a plain and a template
source. Frontmatter stays inside the portability boundary: every key the
frontmatter matrix places is declared through the renderer global named after
it, and every `metadata` entry sits under a namespace the same matrix declares.

The last two checks guard the test boundary itself: every test outside this
directory validates the artifact a user installs, so naming a template or a
path into the authored tree is a policy failure rather than a convention
someone remembers.
"""

import json
import re
from pathlib import Path

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.render import (
    FRONTMATTER_MATRIX_NAME,
    MATRIX_PATH,
    RAW_BLOCK,
    TEMPLATE_SUFFIX,
    VERBATIM_FORM,
    frontmatter_lines,
    ignored_path,
)


PLUGINS_ROOT = REPO_ROOT / "plugins"
TESTS_ROOT = REPO_ROOT / "tests"
# This directory is the one carve-out from the boundary: the build layer's
# subject matter is the authored tree and the template rules, so it reads both.
BUILD_LAYER = Path(__file__).resolve().parent
SHARED_CONFTEST = TESTS_ROOT / "conftest.py"
# A path into the authored tree has two spellings here: the slash-bearing
# literal, and the quoted segment joined onto `REPO_ROOT`. The second is
# matched with its join, because the bare quoted word is also the key every
# marketplace manifest stores its plugin list under. A bare unquoted word
# stays legal too, because prose and identifiers use it constantly.
AUTHORED_TREE_SPELLINGS = (
    re.escape(TEMPLATE_SUFFIX),
    re.escape(f"{PLUGINS_ROOT.name}/"),
    rf"""REPO_ROOT\s*/\s*["']{PLUGINS_ROOT.name}["']""",
)
FRONTMATTER_MATRIX = json.loads(
    (REPO_ROOT / MATRIX_PATH)
    .with_name(FRONTMATTER_MATRIX_NAME)
    .read_text(encoding="utf-8")
)
PLACED_KEYS = {
    key
    for key, entry in FRONTMATTER_MATRIX["keys"].items()
    if entry["form"] != VERBATIM_FORM
}
# A placed key reaches Codex under `metadata`, so it names a namespace there
# just as much as the content namespaces the matrix declares for authors.
METADATA_NAMESPACES = set(FRONTMATTER_MATRIX["metadata_namespaces"]) | PLACED_KEYS
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
BRANCH_TAG = re.compile(
    r"\{%-?\s*(?P<tag>if|elif|else|endif)\b(?P<test>.*?)-?%\}", re.DOTALL
)
DOLLAR_INVOCATION = re.compile(r"\$[a-z0-9][a-z0-9-]*(:[a-z0-9_-]+)?")
DECLARED_ARGUMENTS = re.compile(r"""arguments\(\s*["']([^"']+)["']\s*\)""")
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


def selects_a_callable_inside_a_conditional(text: str) -> bool:
    """Report whether a template picks a callable name per harness by hand.

    A `$name` is a Codex invocation everywhere except one place: a name the
    same file declares through the `arguments` global is a Claude Code
    argument placeholder, and spelling it belongs inside a conditional
    because Codex documents no substitution to spell it for.
    """
    placeholders = {
        name
        for declaration in DECLARED_ARGUMENTS.findall(text)
        for name in declaration.split()
    }
    for block in HARNESS_CONDITIONAL_BLOCK.findall(text):
        invoked = {
            match.group().lstrip("$") for match in DOLLAR_INVOCATION.finditer(block)
        }
        if "Skill(" in block or "| call" in block or invoked - placeholders:
            return True
    return False


def test_templates_never_select_callable_names_inside_harness_conditionals():
    violations = [
        str(path.relative_to(REPO_ROOT))
        for path in template_sources()
        if selects_a_callable_inside_a_conditional(path.read_text(encoding="utf-8"))
    ]

    assert not violations, (
        "harness conditionals are for divergent narrative only; callable "
        "references belong outside them:\n" + "\n".join(violations)
    )


def test_declared_argument_placeholder_may_be_spelled_per_harness():
    text = (
        '{{ arguments("items") }}\n'
        '{% if harness == "ClaudeCode" %}Scope: `$items`.{% endif %}\n'
    )

    assert not selects_a_callable_inside_a_conditional(text)


def test_undeclared_dollar_name_inside_a_conditional_still_fails():
    text = '{% if harness == "Codex" %}Run $commit first.{% endif %}\n'

    assert selects_a_callable_inside_a_conditional(text)


def test_declaring_one_argument_exempts_only_that_name():
    text = (
        '{{ arguments("items") }}\n'
        '{% if harness == "Codex" %}Run $commit first.{% endif %}\n'
    )

    assert selects_a_callable_inside_a_conditional(text)


def implicit_harness_branches(text: str) -> list[int]:
    """Return the line of every harness branch that does not name its harness.

    A harness conditional selects wording for the harness it is rendered for,
    so each branch answers "which harness is this for?". `{% else %}` answers
    "every harness I did not think of", which is the same content today only
    because there happen to be two harnesses: adding a third silently hands it
    the second harness's vocabulary. Requiring `{% elif harness == "..." %}`
    keeps the answer in the template, where adding a harness surfaces every
    passage that has to choose again.

    Raw blocks are removed first: their braces are literal output, not
    branches. The scan tracks nesting, so a plain `{% else %}` under a
    non-harness `if` inside a harness conditional stays untouched.
    """
    scanned = RAW_BLOCK.sub("", text)
    open_conditionals: list[bool] = []
    lines: list[int] = []
    for match in BRANCH_TAG.finditer(scanned):
        tag = match.group("tag")
        if tag == "if":
            open_conditionals.append("harness" in match.group("test"))
            continue
        if tag == "endif":
            if open_conditionals:
                open_conditionals.pop()
            continue
        if not open_conditionals or not open_conditionals[-1]:
            continue
        if tag == "else" or "harness" not in match.group("test"):
            lines.append(scanned.count("\n", 0, match.start()) + 1)
    return lines


def test_harness_conditionals_name_the_harness_in_every_branch():
    violations = [
        f"{path.relative_to(REPO_ROOT)}:{line}"
        for path in template_sources()
        for line in implicit_harness_branches(path.read_text(encoding="utf-8"))
    ]

    assert not violations, (
        "every harness branch must name its harness, so adding a harness "
        'surfaces each passage instead of inheriting another\'s wording; use '
        '`{% elif harness == "..." %}` instead of `{% else %}`:\n'
        + "\n".join(violations)
    )


def test_implicit_branch_scan_accepts_an_explicit_chain():
    text = (
        '{% if harness == "ClaudeCode" %}A.\n'
        '{% elif harness == "Codex" %}B.\n'
        "{% endif %}\n"
    )

    assert not implicit_harness_branches(text)


def test_implicit_branch_scan_rejects_an_else_branch():
    text = '{% if harness == "Codex" %}A.{% else %}B.{% endif %}\n'

    assert implicit_harness_branches(text) == [1]


def test_implicit_branch_scan_ignores_a_nested_non_harness_else():
    text = (
        '{% if harness == "Codex" %}\n'
        "{% if items %}A.{% else %}B.{% endif %}\n"
        '{% elif harness == "ClaudeCode" %}C.\n'
        "{% endif %}\n"
    )

    assert not implicit_harness_branches(text)


def test_implicit_branch_scan_ignores_a_raw_block():
    text = (
        "{% raw %}{% if harness %}A.{% else %}B.{% endif %}{% endraw %}\n"
        '{% if harness == "Codex" %}C.{% elif harness == "ClaudeCode" %}D.{% endif %}\n'
    )

    assert not implicit_harness_branches(text)


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


def test_sources_never_hand_write_a_placed_frontmatter_key():
    """A placed key is one the harnesses disagree about.

    One harness reads it at the top level and another does not read it there
    at all, so the placement is the renderer's call, not the author's.
    """
    violations = [
        f"{path.relative_to(REPO_ROOT)}: {key}"
        for path in frontmatter_carrying_sources()
        for line in frontmatter_lines(path.read_text(encoding="utf-8")) or []
        for key in PLACED_KEYS
        if line.startswith(f"{key}:")
    ]

    assert not violations, (
        "declare each of these through the global named after the key, so "
        "every harness gets the placement it reads:\n" + "\n".join(violations)
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


def boundary_scanned_files() -> list[Path]:
    """Every test file the boundary rule applies to."""
    is_ignored = ignored_path(REPO_ROOT)
    return sorted(
        path
        for path in TESTS_ROOT.rglob("*")
        if path.is_file()
        and not is_ignored(path)
        and path != SHARED_CONFTEST
        and BUILD_LAYER not in path.parents
    )


def test_tests_outside_the_build_layer_never_name_the_authored_tree():
    violations = [
        f"{path.relative_to(REPO_ROOT)}: {found.group()}"
        for path in boundary_scanned_files()
        for spelling in AUTHORED_TREE_SPELLINGS
        for found in [re.search(spelling, path.read_text(encoding="utf-8"))]
        if found
    ]

    assert not violations, (
        "a test outside the build layer validates the artifact a user "
        "installs, so it reaches plugin content through the `rendered` "
        "fixture and names neither a template nor the authored tree:\n"
        + "\n".join(violations)
    )


def test_no_test_directory_under_the_authored_tree():
    """Every test lives in the root tree, so CI runs it and no user gets it."""
    directories = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(PLUGINS_ROOT.rglob("tests"))
        if path.is_dir()
    ]

    assert not directories, (
        "move these into the root `tests/` tree: a test here is never run by "
        "CI and is copied into every published tree:\n" + "\n".join(directories)
    )
