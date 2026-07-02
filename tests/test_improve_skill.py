import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "ai-assistant-ops"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "improve-skill"
SKILL_FILE = SKILL_ROOT / "SKILL.md"


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


def skill_body() -> str:
    return SKILL_FILE.read_text(encoding="utf-8").split("---\n", 2)[2]


def test_skill_exists_with_trigger_only_frontmatter() -> None:
    assert SKILL_FILE.is_file()

    frontmatter = parse_frontmatter(SKILL_FILE)

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


def test_skill_body_preserves_improvement_loop_concepts() -> None:
    body = skill_body()
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


def test_bloat_hunter_is_post_rewrite_pre_evaluation_step() -> None:
    body = skill_body()

    assert "ai-assistant-ops:md-bloat-hunter" in body
    assert re.search(
        r"after rewriting[\s\S]*ai-assistant-ops:md-bloat-hunter[\s\S]*before (evaluation|rerun)",
        body,
        flags=re.IGNORECASE,
    )


def test_skill_avoids_anthropic_specific_commands_and_viewers() -> None:
    combined = "\n".join(
        [
            SKILL_FILE.read_text(encoding="utf-8"),
            (SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"),
            (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"),
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


def test_evals_cover_required_improvement_scenarios() -> None:
    evals_file = SKILL_ROOT / "evals" / "evals.json"
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


def test_openai_agent_prompt_exists() -> None:
    agent_file = SKILL_ROOT / "agents" / "openai.yaml"
    assert agent_file.is_file()

    agent = agent_file.read_text(encoding="utf-8")

    assert 'display_name: "Improve Skill"' in agent
    assert "short_description:" in agent
    assert "default_prompt:" in agent
    assert "Improve this skill" in agent


def test_ai_assistant_ops_docs_and_manifests_include_improve_skill() -> None:
    plugin_readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    codex_manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    claude_manifest = json.loads(
        (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert "`improve-skill`" in plugin_readme
    assert "`improve-skill`" in root_readme
    assert "skill improvement" in json.dumps(codex_manifest).lower()
    assert codex_manifest["version"] == claude_manifest["version"]
    assert codex_manifest["version"].count(".") == 2
