"""Contract for the adapt-skill-for-ai-harness skill as a user receives it.

The skill instructs harness-parametric template authoring against the action
matrix: templates resolve callable names through the action map and the
wrapper filter, harness conditionals cover only genuinely divergent narrative,
and no file in the skill instructs any per-harness reference-file pattern.

Template vocabulary is this skill's subject matter, so the assertions below
quote it as skill content. The template suffix comes from the renderer rather
than being spelled here, which keeps every test outside the build layer free
of it.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from plugin_maintenance.render import TEMPLATE_SUFFIX


@pytest.fixture(scope="session")
def skill_root(rendered: Path) -> Path:
    return rendered / "ai-assistant-ops" / "skills" / "adapt-skill-for-ai-harness"

LEGACY_MARKERS = (
    "Depending on who you are as an AI agent",
    "ai-assistant-harnesses",
    "ai-assistant-harness-adaptation.claude-code",
    "ai-assistant-harness-adaptation.codex",
    "metadata-linked reference",
)


@pytest.fixture(scope="session")
def skill_text(skill_root: Path) -> str:
    return (skill_root / "SKILL.md").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def skill_body(skill_text: str) -> str:
    return skill_text.split("---\n", 2)[2]


@pytest.fixture(scope="session")
def frontmatter_matrix_file(skill_root: Path) -> Path:
    return skill_root / "references" / "harness-frontmatter-matrix.json"


def test_skill_exists_with_expected_frontmatter(skill_text: str) -> None:
    text = skill_text

    assert text.startswith("---\n")
    frontmatter = text.split("---\n", 2)[1]
    assert "name: adapt-skill-for-ai-harness" in frontmatter
    for phrase in [
        "adapting skills",
        "AI Assistant Harness Adaptation",
        "assistant harness action matrix",
    ]:
        assert phrase in frontmatter


def test_skill_instructs_template_authoring(skill_body: str) -> None:
    body = skill_body

    assert TEMPLATE_SUFFIX in body
    assert "{{ actions.AskUser | call }}" in body
    assert '{{ "plugin-name:skill-name" | call }}' in body
    assert '{% if harness == "Codex" %}' in body
    assert '{% elif harness == "ClaudeCode" %}' in body
    assert "{% raw %}" in body
    assert "byte-for-byte" in body
    assert "explicitly named" in body


def test_skill_documents_frontmatter_portability_boundary(skill_body: str) -> None:
    body = skill_body

    assert "Frontmatter Portability Boundary" in body
    assert "harness-frontmatter-matrix.json" in body
    assert '{{ allowed_tools("Bash(git:*) Read") }}' in body
    assert '{{ argument_hint("[issue] to work through") }}' in body
    assert '{{ arguments("issue") }}' in body
    assert "the global named after it" in body
    assert "folds every frontmatter `metadata:`" in body
    for namespace in ("references", "agents", "skills", "origin", "config"):
        assert f"`{namespace}`" in body


def test_skill_documents_every_value_form(
    skill_body: str, frontmatter_matrix_file: Path
) -> None:
    body = skill_body
    forms = json.loads(frontmatter_matrix_file.read_text(encoding="utf-8"))["forms"]

    for form in forms:
        assert f"`{form}`" in body, form
    assert "would otherwise parse as a YAML list" in body
    assert "spell a placeholder inside a harness conditional" in body


def test_skill_documents_the_frontmatter_matrix_contract(skill_body: str) -> None:
    body = skill_body

    assert '`lookup_order: ["key", "assistant"]`' in body
    assert "hyphens turned into underscores" in body
    assert "metadata_namespaces" in body
    assert "specification" in body


def test_skill_names_every_portable_specification_field(
    skill_body: str, frontmatter_matrix_file: Path
) -> None:
    body = skill_body
    matrix = json.loads(frontmatter_matrix_file.read_text(encoding="utf-8"))

    for key in matrix["specification"]["portable_keys"]:
        assert f"`{key}`" in body, key


def test_skill_links_the_vendored_specification(
    skill_body: str, skill_root: Path
) -> None:
    body = skill_body
    document = skill_root / "references" / "agent-skills-specification.md"

    assert "references/agent-skills-specification.md" in body
    assert document.is_file()


def test_skill_sends_codex_product_settings_to_the_agent_file(
    skill_body: str,
) -> None:
    """Codex UI, invocation policy and tool dependencies are not frontmatter."""
    body = skill_body

    assert "agents/openai.yaml" in body
    assert "allow_implicit_invocation" in body
    assert "metadata.short-description" in body


def test_skill_documents_matrix_contract(skill_body: str) -> None:
    body = skill_body

    assert 'matrix["actions"]["CreateAgent"]["Codex"]["name"]' in body
    assert "TitleCase" in body
    assert "invocation_wrapper" in body
    assert "one callable name per" in body
    assert "`callable`" in body
    assert '`lookup_order: ["action", "assistant"]`' in body
    assert "`ClaudeCode`" in body and "`Codex`" in body


def test_skill_directory_carries_no_legacy_pattern(skill_root: Path) -> None:
    violations = []

    for path in sorted(skill_root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in LEGACY_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(skill_root)}: {marker}")

    assert not violations, "\n".join(violations)


def run_lookup(skill_root: Path, action: str, assistant: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(skill_root / "scripts" / "lookup_harness_action.py"),
            "--matrix",
            str(skill_root / "references" / "harness-action-matrix.json"),
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


def test_lookup_script_resolves_callable_name_and_invocation(skill_root: Path) -> None:
    entry = run_lookup(skill_root, "CreateAgent", "Codex")

    assert entry["action"] == "CreateAgent"
    assert entry["assistant"] == "Codex"
    assert entry["callable"] is True
    assert entry["name"] == "spawn_agent"
    assert entry["invocation"] == "$spawn_agent"


def test_lookup_script_returns_reference_material_for_non_callable(
    skill_root: Path,
) -> None:
    entry = run_lookup(skill_root, "PluginManifest", "ClaudeCode")

    assert entry["callable"] is False
    assert ".claude-plugin/plugin.json" in entry["files"]
    assert "invocation" not in entry


def test_lookup_script_fails_on_unknown_action(skill_root: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_lookup(skill_root, "NoSuchAction", "Codex")


def run_frontmatter_lookup(skill_root: Path, key: str, assistant: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(skill_root / "scripts" / "lookup_harness_frontmatter.py"),
            "--matrix",
            str(skill_root / "references" / "harness-frontmatter-matrix.json"),
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


def test_frontmatter_lookup_resolves_placement_and_declaration(
    skill_root: Path,
) -> None:
    entry = run_frontmatter_lookup(skill_root, "argument-hint", "Codex")

    assert entry["key"] == "argument-hint"
    assert entry["assistant"] == "Codex"
    assert entry["placement"] == "metadata"
    assert entry["form"] == "quoted-scalar"
    assert entry["declaration"] == "{{ argument_hint(...) }}"
    assert entry["note"]


def test_frontmatter_lookup_marks_a_portable_key_as_hand_written(
    skill_root: Path,
) -> None:
    entry = run_frontmatter_lookup(skill_root, "name", "ClaudeCode")

    assert entry["placement"] == "top-level"
    assert entry["form"] == "verbatim"
    assert entry["declaration"] == "write `name:` literally in frontmatter"


def test_frontmatter_lookup_fails_on_unknown_key(skill_root: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_frontmatter_lookup(skill_root, "no-such-key", "Codex")


def test_evals_cover_template_authoring(skill_root: Path) -> None:
    evals_file = skill_root / "evals" / "evals.json"
    evals = json.loads(evals_file.read_text(encoding="utf-8"))

    assert evals["skill_name"] == "adapt-skill-for-ai-harness"
    cases = evals["evals"]
    assert len(cases) >= 3

    combined = json.dumps(cases, sort_keys=True)
    assert "explicitly named" in combined
    assert "action matrix" in combined
    assert TEMPLATE_SUFFIX in combined
    assert "| call" in combined
    assert "CreateAgent" in combined
