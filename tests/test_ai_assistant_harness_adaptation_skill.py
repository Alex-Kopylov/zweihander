import json
import re
import subprocess
import sys
from pathlib import Path


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


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    frontmatter = text.split("---\n", 2)[1]
    data: dict[str, object] = {}
    current_map: dict[str, str] | None = None

    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_map is not None:
            key, value = line.strip().split(":", 1)
            current_map[key.strip()] = value.strip().strip('"')
            continue
        key, value = line.split(":", 1)
        if value.strip():
            data[key.strip()] = value.strip().strip('"')
            current_map = None
        else:
            current_map = {}
            data[key.strip()] = current_map

    return data


def skill_body() -> str:
    return SKILL_FILE.read_text(encoding="utf-8").split("---\n", 2)[2]


def test_skill_exists_with_expected_metadata() -> None:
    assert SKILL_FILE.is_file()

    frontmatter = parse_frontmatter(SKILL_FILE)

    assert frontmatter["name"] == "adapt-skill-for-ai-harness"
    description = str(frontmatter["description"])
    for phrase in [
        "adapting skills",
        "AI Assistant Harness Adaptation",
        "assistant harness action matrix",
    ]:
        assert phrase in description

    metadata = frontmatter["metadata"]
    assert isinstance(metadata, dict)
    assert (
        metadata["ai-assistant-harness-adaptation.action-matrix"]
        == "references/harness-action-matrix.json"
    )
    assert not any(key.endswith(".codex") for key in metadata)
    assert not any(key.endswith(".claude-code") for key in metadata)


def test_metadata_links_to_scriptable_action_matrix() -> None:
    metadata = parse_frontmatter(SKILL_FILE)["metadata"]
    assert isinstance(metadata, dict)

    value = metadata["ai-assistant-harness-adaptation.action-matrix"]
    assert value.endswith(".json")
    assert "\n" not in value
    assert " " not in value
    assert (SKILL_ROOT / value).resolve() == MATRIX_FILE.resolve()
    assert MATRIX_FILE.is_file()


def test_action_matrix_supports_action_then_assistant_lookup() -> None:
    matrix = json.loads(MATRIX_FILE.read_text(encoding="utf-8"))

    assert matrix["schema_version"] == 1
    assert matrix["lookup_order"] == ["action", "assistant"]
    assert set(matrix["assistants"]) >= {"ClaudeCode", "Codex"}

    kinds = {action["kind"] for action in matrix["actions"].values()}
    assert {"workflow", "skill", "tool", "command"}.issubset(kinds)

    create_agent = matrix["actions"]["CreateAgent"]
    assert create_agent["kind"] == "workflow"
    assert set(create_agent) >= {"ClaudeCode", "Codex"}
    assert "Agent" in create_agent["ClaudeCode"]["terms"]
    assert "spawn_agent" in create_agent["Codex"]["terms"]
    assert "tool_search" in create_agent["Codex"]["discovery"]
    assert "guidance" not in json.dumps(matrix)


def test_lookup_script_returns_action_assistant_entry() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(LOOKUP_SCRIPT),
            "--matrix",
            str(MATRIX_FILE),
            "--action",
            "CreateAgent",
            "--assistant",
            "Codex",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    entry = json.loads(result.stdout)
    assert entry["action"] == "CreateAgent"
    assert entry["assistant"] == "Codex"
    assert entry["kind"] == "workflow"
    assert "spawn_agent" in entry["terms"]
    assert "tool_search" in entry["discovery"]


def test_skill_instructs_single_matching_harness_reference_only() -> None:
    body = skill_body()

    assert re.search(
        r'matrix\["actions"\]\[action_key\]\[assistant_key\]',
        body,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"CreateAgent.*Codex",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )


def test_skill_has_no_shared_cross_harness_instruction_table() -> None:
    body = skill_body()
    tables = re.findall(r"(?:^\|.*\|\n){2,}", body, flags=re.MULTILINE)

    assert not any(
        "Claude Code" in table and "Codex" in table
        for table in tables
    )


def test_skill_does_not_ship_its_own_per_harness_references() -> None:
    harness_root = SKILL_ROOT / "references" / "ai-assistant-harnesses"
    assert not (harness_root / "claude-code.md").exists()
    assert not (harness_root / "codex.md").exists()


def test_live_lab_protocol_and_skill_readme_exist() -> None:
    assert (SKILL_ROOT / "references" / "live-lab-protocol.md").is_file()
    assert (SKILL_ROOT / "README.md").is_file()


def test_evals_cover_adaptation_and_harness_read_scope() -> None:
    evals_file = SKILL_ROOT / "evals" / "evals.json"
    assert evals_file.is_file()

    evals = json.loads(evals_file.read_text(encoding="utf-8"))

    assert evals["skill_name"] == "adapt-skill-for-ai-harness"
    cases = evals.get("cases", evals.get("evals"))
    assert isinstance(cases, list)
    assert len(cases) >= 3

    combined = json.dumps(cases, sort_keys=True)
    assert "explicitly named skill" in combined
    assert "action matrix" in combined
    assert "CreateAgent" in combined
    assert "matrix" in combined
    assert "action_key" in combined
    assert "assistant_key" in combined
    assert "target skill" in combined
