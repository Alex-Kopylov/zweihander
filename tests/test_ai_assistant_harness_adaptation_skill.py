import json
import re
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
HARNESS_ROOT = SKILL_ROOT / "references" / "ai-assistant-harnesses"


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
        "Claude Code",
        "Codex",
    ]:
        assert phrase in description

    metadata = frontmatter["metadata"]
    assert isinstance(metadata, dict)
    assert (
        metadata["ai-assistant-harness-adaptation.claude-code"]
        == "references/ai-assistant-harnesses/claude-code.md"
    )
    assert (
        metadata["ai-assistant-harness-adaptation.codex"]
        == "references/ai-assistant-harnesses/codex.md"
    )


def test_metadata_links_are_file_only_harness_references() -> None:
    metadata = parse_frontmatter(SKILL_FILE)["metadata"]
    assert isinstance(metadata, dict)

    for key, value in metadata.items():
        assert key.startswith("ai-assistant-harness-adaptation.")
        assert value.endswith(".md")
        assert "\n" not in value
        assert " " not in value
        resolved = (SKILL_ROOT / value).resolve()
        assert resolved.is_file()
        assert HARNESS_ROOT.resolve() in resolved.parents


def test_skill_instructs_single_matching_harness_reference_only() -> None:
    body = skill_body()

    assert re.search(
        r"load exactly one matching metadata-linked harness reference",
        body,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"skip the other harness files",
        body,
        flags=re.IGNORECASE,
    )


def test_skill_has_no_shared_cross_harness_instruction_table() -> None:
    body = skill_body()
    tables = re.findall(r"(?:^\|.*\|\n){2,}", body, flags=re.MULTILINE)

    assert not any(
        "Claude Code" in table and "Codex" in table
        for table in tables
    )


def test_harness_references_and_live_lab_protocol_exist() -> None:
    assert (HARNESS_ROOT / "claude-code.md").is_file()
    assert (HARNESS_ROOT / "codex.md").is_file()
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
    assert "Claude Code" in combined
    assert "Codex" in combined
    assert "codex.md" in combined
    assert "claude-code.md" in combined
    assert "only" in combined
