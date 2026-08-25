"""Contract for the adapt-skill-for-ai-harness skill.

The skill instructs harness-parametric template authoring against the action
matrix: `.j2` templates resolve callable names through the action map and the
wrapper filter, harness conditionals cover only genuinely divergent narrative,
and no file in the skill instructs any per-harness reference-file pattern.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    REPO_ROOT
    / "plugins"
    / "ai-assistant-ops"
    / "skills"
    / "adapt-skill-for-ai-harness"
)
SKILL_FILE = SKILL_ROOT / "SKILL.md"
MATRIX_FILE = SKILL_ROOT / "references" / "harness-action-matrix.json"
LOOKUP_SCRIPT = SKILL_ROOT / "scripts" / "lookup_harness_action.py"

LEGACY_MARKERS = (
    "Depending on who you are as an AI agent",
    "ai-assistant-harnesses",
    "ai-assistant-harness-adaptation.claude-code",
    "ai-assistant-harness-adaptation.codex",
    "metadata-linked reference",
)


def skill_text() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


def skill_body() -> str:
    return skill_text().split("---\n", 2)[2]


def test_skill_exists_with_expected_frontmatter() -> None:
    text = skill_text()

    assert text.startswith("---\n")
    frontmatter = text.split("---\n", 2)[1]
    assert "name: adapt-skill-for-ai-harness" in frontmatter
    for phrase in [
        "adapting skills",
        "AI Assistant Harness Adaptation",
        "assistant harness action matrix",
    ]:
        assert phrase in frontmatter


def test_skill_instructs_template_authoring() -> None:
    body = skill_body()

    assert ".j2" in body
    assert "{{ actions.AskUser | call }}" in body
    assert '{{ "plugin-name:skill-name" | call }}' in body
    assert '{% if harness == "Codex" %}' in body
    assert "{% raw %}" in body
    assert "byte-for-byte" in body
    assert "explicitly named" in body


def test_skill_documents_frontmatter_portability_boundary() -> None:
    body = skill_body()

    assert "Frontmatter Portability Boundary" in body
    assert '{{ allowed_tools("Bash(git:*) Read") }}' in body
    assert "`name` and `description` are the portable keys" in body
    assert "Claude Code renders `allowed-tools: Bash(git:*) Read` at the top" in body
    assert "Codex\nrenders it under `metadata:`" in body
    assert "folds every frontmatter `metadata:`" in body
    for namespace in ("references", "agents", "skills", "origin"):
        assert f"`{namespace}`" in body


def test_skill_documents_matrix_contract() -> None:
    body = skill_body()

    assert 'matrix["actions"]["CreateAgent"]["Codex"]["name"]' in body
    assert "TitleCase" in body
    assert "invocation_wrapper" in body
    assert "one callable name per" in body
    assert "`callable`" in body
    assert '`lookup_order: ["action", "assistant"]`' in body
    assert "`ClaudeCode`" in body and "`Codex`" in body


def test_skill_directory_carries_no_legacy_pattern() -> None:
    violations = []

    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in LEGACY_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(SKILL_ROOT)}: {marker}")

    assert not violations, "\n".join(violations)


def run_lookup(action: str, assistant: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(LOOKUP_SCRIPT),
            "--matrix",
            str(MATRIX_FILE),
            "--action",
            action,
            "--assistant",
            assistant,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_lookup_script_resolves_callable_name_and_invocation() -> None:
    entry = run_lookup("CreateAgent", "Codex")

    assert entry["action"] == "CreateAgent"
    assert entry["assistant"] == "Codex"
    assert entry["callable"] is True
    assert entry["name"] == "spawn_agent"
    assert entry["invocation"] == "$spawn_agent"


def test_lookup_script_returns_reference_material_for_non_callable() -> None:
    entry = run_lookup("PluginManifest", "ClaudeCode")

    assert entry["callable"] is False
    assert ".claude-plugin/plugin.json" in entry["files"]
    assert "invocation" not in entry


def test_lookup_script_fails_on_unknown_action() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_lookup("NoSuchAction", "Codex")


def test_evals_cover_template_authoring() -> None:
    evals_file = SKILL_ROOT / "evals" / "evals.json"
    evals = json.loads(evals_file.read_text(encoding="utf-8"))

    assert evals["skill_name"] == "adapt-skill-for-ai-harness"
    cases = evals["evals"]
    assert len(cases) >= 3

    combined = json.dumps(cases, sort_keys=True)
    assert "explicitly named" in combined
    assert "action matrix" in combined
    assert ".j2" in combined
    assert "| call" in combined
    assert "CreateAgent" in combined
