"""The two testing skills own disjoint material and route by skill name.

Issue #84 resolved the duplicated TDD methodology this way:

- ``dev-workflow:test-driven-development`` owns the language-neutral test-first
  process and keeps its detail in references.
- ``python-dev-workflow:tests-manager`` owns Python test craft and reduces the
  process rules to a routing summary that names the TDD skill.

The plugins install independently, so neither skill may reach across the plugin
boundary with a file path. Routing happens by skill name only.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TDD_SKILL_DIR = (
    REPO_ROOT / "plugins" / "dev-workflow" / "skills" / "test-driven-development"
)
TESTS_MANAGER_DIR = (
    REPO_ROOT / "plugins" / "python-dev-workflow" / "skills" / "tests-manager"
)

TDD_SKILL_NAME = "dev-workflow:test-driven-development"
TESTS_MANAGER_NAME = "python-dev-workflow:tests-manager"

PYTHON_ONLY_TOKENS = ("pytest", "conftest", "@pytest.mark", "tests/unit/")

MAX_ENTRYPOINT_LINES = 200


def frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    return text.split("---\n", 2)[1]


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    return text.split("---\n", 2)[2]


def context_markdown(skill_dir: Path) -> list[Path]:
    """Markdown an agent loads as context, excluding eval fixtures."""
    return [
        path
        for path in sorted(skill_dir.rglob("*.md"))
        if "evals" not in path.relative_to(skill_dir).parts
    ]


def test_each_testing_skill_declares_its_own_ownership() -> None:
    tdd_body = body(TDD_SKILL_DIR / "SKILL.md")
    manager_body = body(TESTS_MANAGER_DIR / "SKILL.md")

    assert "## Ownership" in tdd_body
    assert "## Ownership" in manager_body
    assert TESTS_MANAGER_NAME in tdd_body
    assert TDD_SKILL_NAME in manager_body


def test_tdd_skill_does_not_restate_python_test_rules() -> None:
    leaks = [
        f"{path.relative_to(REPO_ROOT)}: {token}"
        for path in context_markdown(TDD_SKILL_DIR)
        for token in PYTHON_ONLY_TOKENS
        if token in path.read_text(encoding="utf-8")
    ]

    assert leaks == [], (
        "the language-neutral TDD skill must route Python work to "
        f"{TESTS_MANAGER_NAME} instead of restating Python test rules:\n"
        + "\n".join(leaks)
    )


def test_testing_skills_route_by_name_not_by_cross_plugin_path() -> None:
    """A path out of the plugin breaks whenever the sibling plugin is absent."""
    escapes = []
    for skill_dir in (TDD_SKILL_DIR, TESTS_MANAGER_DIR):
        plugin_root = skill_dir.parent.parent
        for path in context_markdown(skill_dir):
            for line in path.read_text(encoding="utf-8").splitlines():
                for token in line.split():
                    candidate = token.strip("`\"'(),")
                    if not candidate.startswith("../"):
                        continue
                    resolved = (path.parent / candidate).resolve()
                    if plugin_root not in resolved.parents:
                        escapes.append(
                            f"{path.relative_to(REPO_ROOT)}: {candidate}"
                        )

    assert escapes == [], (
        "testing skills must not reference a path outside their own plugin:\n"
        + "\n".join(escapes)
    )


def test_tdd_skill_keeps_detail_in_metadata_routed_references() -> None:
    skill_path = TDD_SKILL_DIR / "SKILL.md"
    skill_frontmatter = frontmatter(skill_path)

    expected_references = (
        "references/testing-anti-patterns.md",
        "references/rationalizations.md",
    )
    for reference in expected_references:
        assert f'"{reference}"' in skill_frontmatter
        assert (TDD_SKILL_DIR / reference).is_file()

    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    assert line_count <= MAX_ENTRYPOINT_LINES, (
        f"the TDD entrypoint grew to {line_count} lines; move detail into "
        "references instead"
    )


def test_tests_manager_harness_references_invoke_the_tdd_skill() -> None:
    harness_dir = TESTS_MANAGER_DIR / "references" / "ai-assistant-harnesses"
    claude_code = (harness_dir / "claude-code.md").read_text(encoding="utf-8")
    codex = (harness_dir / "codex.md").read_text(encoding="utf-8")

    assert f"Skill({TDD_SKILL_NAME})" in claude_code
    assert f"${TDD_SKILL_NAME}" in codex


def test_tdd_evals_pin_the_ownership_boundary() -> None:
    evals_file = TDD_SKILL_DIR / "evals" / "evals.json"
    assert evals_file.is_file()

    evals = json.loads(evals_file.read_text(encoding="utf-8"))
    assert evals["skill_name"] == "test-driven-development"

    cases = evals.get("cases", evals.get("evals"))
    assert cases
    assertion_names = {
        assertion["name"] for case in cases for assertion in case["assertions"]
    }

    assert {
        "routes_python_work_to_tests_manager",
        "no_python_routing_for_non_python",
        "should_not_trigger_for_plain_test_request",
    } <= assertion_names


def test_tests_manager_evals_pin_the_reverse_boundary() -> None:
    evals_file = TESTS_MANAGER_DIR / "evals" / "evals.json"
    evals = json.loads(evals_file.read_text(encoding="utf-8"))

    cases = evals.get("cases", evals.get("evals"))
    assertion_names = {
        assertion["name"] for case in cases for assertion in case["assertions"]
    }

    assert {
        "routes_process_detail_to_tdd_skill",
        "standalone_without_sibling_plugin",
    } <= assertion_names
