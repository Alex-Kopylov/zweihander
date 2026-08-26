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
FRONTMATTER_MATRIX_FILE = (
    SKILL_ROOT / "references" / "harness-frontmatter-matrix.json"
)
LOOKUP_SCRIPT = SKILL_ROOT / "scripts" / "lookup_harness_action.py"
FRONTMATTER_LOOKUP_SCRIPT = (
    SKILL_ROOT / "scripts" / "lookup_harness_frontmatter.py"
)

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
    assert "harness-frontmatter-matrix.json" in body
    assert '{{ allowed_tools("Bash(git:*) Read") }}' in body
    assert '{{ argument_hint("[issue] to work through") }}' in body
    assert '{{ arguments("issue") }}' in body
    assert "one global named after it" in body
    assert "folds every frontmatter `metadata:`" in body
    for namespace in ("references", "agents", "skills", "origin", "config"):
        assert f"`{namespace}`" in body


def test_skill_documents_every_value_form() -> None:
    body = skill_body()
    forms = json.loads(FRONTMATTER_MATRIX_FILE.read_text(encoding="utf-8"))["forms"]

    for form in forms:
        assert f"`{form}`" in body, form
    assert "would otherwise parse as a YAML list" in body
    assert "spell a placeholder inside a harness conditional" in body


def test_skill_documents_the_frontmatter_matrix_contract() -> None:
    body = skill_body()

    assert '`lookup_order: ["key", "assistant"]`' in body
    assert "hyphens turned into underscores" in body
    assert "`top-level` where the harness" in body
    assert "metadata_namespaces" in body


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


def run_frontmatter_lookup(key: str, assistant: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(FRONTMATTER_LOOKUP_SCRIPT),
            "--matrix",
            str(FRONTMATTER_MATRIX_FILE),
            "--key",
            key,
            "--assistant",
            assistant,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_frontmatter_lookup_resolves_placement_and_declaration() -> None:
    entry = run_frontmatter_lookup("argument-hint", "Codex")

    assert entry["key"] == "argument-hint"
    assert entry["assistant"] == "Codex"
    assert entry["placement"] == "metadata"
    assert entry["form"] == "quoted-scalar"
    assert entry["declaration"] == "{{ argument_hint(...) }}"
    assert entry["note"]


def test_frontmatter_lookup_marks_a_portable_key_as_hand_written() -> None:
    entry = run_frontmatter_lookup("name", "ClaudeCode")

    assert entry["placement"] == "top-level"
    assert entry["form"] == "verbatim"
    assert entry["declaration"] == "write `name:` literally in frontmatter"


def test_frontmatter_lookup_fails_on_unknown_key() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_frontmatter_lookup("no-such-key", "Codex")


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
