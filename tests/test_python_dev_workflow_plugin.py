from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "python-dev-workflow"


def frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    return text.split("---\n", 2)[1]


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    return text.split("---\n", 2)[2]


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


def test_celery_expert_carries_no_testing_guidance() -> None:
    celery_skill_root = PLUGIN_ROOT / "skills" / "celery-expert"
    celery_skill = (celery_skill_root / "SKILL.md").read_text(encoding="utf-8")

    testing_tokens = (
        "## TDD Workflow",
        "task_always_eager",
        "pytest-celery",
        "conftest_celery.py",
    )
    leftover_tokens = [token for token in testing_tokens if token in celery_skill]

    assert leftover_tokens == []
    assert not (celery_skill_root / "examples" / "conftest_celery.py").exists()


def test_tests_manager_owns_celery_testing_assets() -> None:
    tests_manager_root = PLUGIN_ROOT / "skills" / "tests-manager"
    celery_examples = tests_manager_root / "examples" / "celery"

    assert (tests_manager_root / "references" / "celery-testing.md").is_file()
    assert (celery_examples / "conftest_celery.py").is_file()
    assert (celery_examples / "test_tasks.py").is_file()
    assert '"references/celery-testing.md"' in frontmatter(
        tests_manager_root / "SKILL.md"
    )

    # A real conftest.py here would be auto-loaded as a non-top-level conftest
    # and apply its pytest_plugins to the whole suite. The example carries a
    # neutral name so it is only ever read, never executed as config.
    assert not (celery_examples / "conftest.py").exists()


def test_celery_expert_routes_test_work_to_tests_manager() -> None:
    celery_skill_path = PLUGIN_ROOT / "skills" / "celery-expert" / "SKILL.md"
    routing_target = "python-dev-workflow:tests-manager"

    assert (PLUGIN_ROOT / "skills" / "tests-manager" / "SKILL.md").is_file()
    assert routing_target in frontmatter(celery_skill_path)
    assert routing_target in body(celery_skill_path)


def test_python_dev_workflow_agent_frontmatter_excludes_examples() -> None:
    agent_files = sorted((PLUGIN_ROOT / "agents").glob("*.md"))

    assert agent_files
    invalid_files = [
        agent_file.relative_to(REPO_ROOT)
        for agent_file in agent_files
        if "<example>" in frontmatter(agent_file)
    ]

    assert invalid_files == []


def test_tests_manager_e2e_contract() -> None:
    skill_path = PLUGIN_ROOT / "skills" / "tests-manager" / "SKILL.md"
    manager_body = body(skill_path)
    manager_frontmatter = frontmatter(skill_path)
    metadata_keys = set(metadata_path_keys(skill_path))
    references = skill_path.parent / "references"
    e2e_reference = (references / "e2e-testing.md").read_text(encoding="utf-8")

    assert {
        "references/e2e-testing.md",
        "../../agents/test-scenario-planner.md",
    } <= metadata_keys
    assert (
        "ai-assistant-harness-adaptation.claude-code: "
        "references/ai-assistant-harnesses/claude-code.md"
    ) in manager_frontmatter
    assert (
        "ai-assistant-harness-adaptation.codex: "
        "references/ai-assistant-harnesses/codex.md"
    ) in manager_frontmatter
    assert "E2E → Integration → Unit" in manager_body
    assert "not by test count or code\ncoverage percentage" in manager_body
    assert "mock" in manager_body and "observable behavior" in manager_body
    assert "stop immediately" in e2e_reference
    assert "Do not\nwrite or run E2E tests" in e2e_reference
    assert "AskUserQuestion" in (
        references / "ai-assistant-harnesses" / "claude-code.md"
    ).read_text(encoding="utf-8")
    assert "request_user_input" in (
        references / "ai-assistant-harnesses" / "codex.md"
    ).read_text(encoding="utf-8")
    assert "one happy path per endpoint" not in (
        references / "integration-testing.md"
    ).read_text(encoding="utf-8")
    assert "normally write both unit and\nintegration coverage" not in manager_body

    planner = body(PLUGIN_ROOT / "agents" / "test-scenario-planner.md")
    assert all(
        expected in planner
        for expected in (
            "task description",
            "specifications",
            "business requirements",
            "corner cases",
            "Do not choose test levels",
        )
    )
