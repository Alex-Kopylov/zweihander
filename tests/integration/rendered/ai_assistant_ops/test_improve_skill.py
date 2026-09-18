"""Contract for the improve-skill skill as a user receives it."""

import json
import re
from pathlib import Path

import pytest

from plugin_maintenance import REPO_ROOT


@pytest.fixture(scope="session")
def skill_root(rendered: Path) -> Path:
    return rendered / "ai-assistant-ops" / "skills" / "improve-skill"


@pytest.fixture(scope="session")
def skill_file(skill_root: Path) -> Path:
    return skill_root / "SKILL.md"


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    frontmatter = text.split("---\n", 2)[1]
    data = {}

    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')

    return data


def body_of(path: Path) -> str:
    return path.read_text(encoding="utf-8").split("---\n", 2)[2]


def test_skill_exists_with_trigger_only_frontmatter(skill_file: Path) -> None:
    assert skill_file.is_file()

    frontmatter = parse_frontmatter(skill_file)

    assert frontmatter["name"] == "improve-skill"
    description = frontmatter["description"]
    assert description.startswith("Use when")

    for phrase in [
        "existing skill",
        "eval feedback",
        "trigger misses",
        "output regressions",
        "bloat",
        "overfitting",
        "repeated manual work",
    ]:
        assert phrase in description

    for workflow_phrase in [
        "snapshot",
        "same prompts",
        "baseline",
        "md-bloat-hunter",
        "rerun",
    ]:
        assert workflow_phrase not in description


def test_skill_body_preserves_improvement_loop_concepts(skill_file: Path) -> None:
    body = body_of(skill_file)
    normalized = body.lower()

    assert body.lstrip().startswith("# Improve Skill")
    assert "target skill" in normalized
    assert "current stage" in normalized
    assert re.search(r"test (prompts|cases|evals).*before editing", normalized)
    assert "snapshot" in normalized
    assert "old-skill" in normalized
    assert "baseline" in normalized
    assert "same prompts" in normalized
    assert "compare" in normalized

    for phrase in [
        "outputs",
        "transcripts",
        "qualitative feedback",
        "objective assertions",
        "timing",
        "token",
        "iteration history",
        "generalize",
        "overfit",
        "lean",
        "why",
        "scripts/",
        "resources",
        "user is satisfied",
        "feedback is empty",
        "progress stalls",
        "should-trigger",
        "should-not-trigger",
    ]:
        assert phrase in normalized


def test_bloat_hunter_is_post_rewrite_pre_evaluation_step(skill_file: Path) -> None:
    body = body_of(skill_file)

    assert "ai-assistant-ops:md-bloat-hunter" in body
    assert re.search(
        r"after rewriting[\s\S]*ai-assistant-ops:md-bloat-hunter[\s\S]*before (evaluation|rerun)",
        body,
        flags=re.IGNORECASE,
    )


def test_skill_avoids_anthropic_specific_commands_and_viewers(
    skill_root: Path, skill_file: Path
) -> None:
    combined = "\n".join(
        [
            skill_file.read_text(encoding="utf-8"),
            (skill_root / "evals" / "evals.json").read_text(encoding="utf-8"),
            (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8"),
        ]
    )

    for forbidden in [
        "claude -p",
        "claude-with-access-to-the-skill",
        "eval-viewer",
        "generate_review.py",
        "/skill-test",
    ]:
        assert forbidden not in combined


def test_evals_cover_required_improvement_scenarios(skill_root: Path) -> None:
    evals_file = skill_root / "evals" / "evals.json"
    assert evals_file.is_file()

    evals = json.loads(evals_file.read_text(encoding="utf-8"))

    assert evals["skill_name"] == "improve-skill"
    cases = evals.get("cases", evals.get("evals"))
    assert isinstance(cases, list)
    assert len(cases) >= 4

    combined = json.dumps(cases, sort_keys=True)
    for phrase in [
        "baseline snapshot",
        "same prompts",
        "feedback",
        "iteration",
        "ai-assistant-ops:md-bloat-hunter",
        "post-rewrite",
        "pre-evaluation",
        "should-trigger",
        "should-not-trigger",
    ]:
        assert phrase in combined


def test_openai_agent_prompt_exists(skill_root: Path) -> None:
    agent_file = skill_root / "agents" / "openai.yaml"
    assert agent_file.is_file()

    agent = agent_file.read_text(encoding="utf-8")

    assert 'display_name: "Improve Skill"' in agent
    assert "short_description:" in agent
    assert "default_prompt:" in agent
    assert "Improve this skill" in agent


def test_plugin_manifest_advertises_skill_improvement(rendered: Path) -> None:
    manifest = json.loads(
        next((rendered / "ai-assistant-ops").glob("*/plugin.json")).read_text(
            encoding="utf-8"
        )
    )

    assert "skill improvement" in json.dumps(manifest).lower()
    assert manifest["version"].count(".") == 2


def test_root_readme_lists_improve_skill() -> None:
    assert "`improve-skill`" in (REPO_ROOT / "README.md").read_text(encoding="utf-8")
