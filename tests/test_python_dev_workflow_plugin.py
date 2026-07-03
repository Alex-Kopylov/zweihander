from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "python-dev-workflow"


def frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    return text.split("---\n", 2)[1]


def metadata_path_keys(path: Path) -> list[str]:
    keys: list[str] = []
    in_metadata = False

    for line in frontmatter(path).splitlines():
        if line == "metadata:":
            in_metadata = True
            continue
        if in_metadata and line and not line.startswith(" "):
            break
        if in_metadata and ":" in line:
            key = line.split(":", 1)[0].strip().strip('"')
            if "/" in key and key.endswith((".md", ".json")):
                keys.append(key)

    return keys


def test_tests_manager_metadata_paths_resolve_from_declaring_file() -> None:
    metadata_files = [
        PLUGIN_ROOT / "skills" / "tests-manager" / "SKILL.md",
        PLUGIN_ROOT / "agents" / "unit-test-writer.md",
        PLUGIN_ROOT / "agents" / "integration-test-writer.md",
    ]

    missing_paths = []
    for metadata_file in metadata_files:
        for key in metadata_path_keys(metadata_file):
            referenced_path = (metadata_file.parent / key).resolve()
            if not referenced_path.is_file():
                missing_paths.append(
                    f"{metadata_file.relative_to(REPO_ROOT)} -> {key}"
                )

    assert missing_paths == []


def test_python_dev_workflow_agent_frontmatter_excludes_examples() -> None:
    agent_files = sorted((PLUGIN_ROOT / "agents").glob("*.md"))

    assert agent_files
    invalid_files = [
        agent_file.relative_to(REPO_ROOT)
        for agent_file in agent_files
        if "<example>" in frontmatter(agent_file)
    ]

    assert invalid_files == []
