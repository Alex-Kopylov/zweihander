"""Contract for the harness-overlap-audit skill as a user receives it."""

import json
import re
from pathlib import Path

import pytest

from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import Harness, frontmatter_lines

# Where each harness records what the user installed. The audit must name its
# own harness's sources and none of the other's.
PROVENANCE_SOURCES = {
    Harness.CLAUDE_CODE: "installed_plugins.json",
    Harness.CODEX: "config.toml",
}


@pytest.fixture
def skill_root(rendered: Path) -> Path:
    return rendered / "ai-assistant-ops" / "skills" / "harness-overlap-audit"


@pytest.fixture
def skill_text(skill_root: Path) -> str:
    return (skill_root / "SKILL.md").read_text(encoding="utf-8")


@pytest.fixture
def body(skill_text: str) -> str:
    return skill_text.split("---\n", 2)[2]


@pytest.mark.harness(Harness.CLAUDE_CODE)
def test_claude_code_only_runs_it_on_user_request(skill_text: str) -> None:
    assert "disable-model-invocation: true" in (frontmatter_lines(skill_text) or [])


@pytest.mark.harness(Harness.CODEX)
def test_codex_only_runs_it_on_user_request(skill_root: Path) -> None:
    agent = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert re.search(r"^\s+allow_implicit_invocation: false$", agent, re.MULTILINE)


def test_provenance_sources_match_the_harness(harness: Harness, body: str) -> None:
    own = PROVENANCE_SOURCES[harness]
    foreign = [source for other, source in PROVENANCE_SOURCES.items() if other != harness]

    assert own in body
    assert not [source for source in foreign if source in body]


def test_body_states_the_audit_rules(body: str) -> None:
    normalized = body.lower()

    for phrase in [
        "never flag a built-in",
        "user-owned",
        "port",
        "agents",
        "pipeline",
        "collision prompt",
        "venn-beta",
        "harness-overlap-audit-",
    ]:
        assert phrase in normalized, phrase


def test_diagrams_go_through_the_mermaid_skills(body: str) -> None:
    assert "mermaid-diagrams:mermaid" in body
    assert "mermaid-diagrams:mermaid-lint" in body


def test_evals_cover_every_rule(skill_root: Path) -> None:
    evals = json.loads((skill_root / "evals" / "evals.json").read_text(encoding="utf-8"))
    assertion_names = {assertion["name"] for case in evals["evals"] for assertion in case["assertions"]}

    assert evals["skill_name"] == "harness-overlap-audit"
    assert {
        "built_in_pair_not_flagged",
        "optional_provider_plugin_flagged",
        "fix_targets_user_owned_side",
        "port_beside_its_built_in_flagged",
        "port_without_built_in_not_flagged",
        "pipeline_not_flagged",
        "overlapping_skill_agents_flagged",
        "summary_line_first",
    } <= assertion_names


def test_root_readme_lists_the_skill() -> None:
    assert "`harness-overlap-audit`" in (REPO_ROOT / "README.md").read_text(encoding="utf-8")
