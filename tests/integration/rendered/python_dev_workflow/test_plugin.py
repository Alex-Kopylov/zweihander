"""Contract for the python-dev-workflow plugin as a user receives it."""

import json
import re
from pathlib import Path

import pytest

REMOVED_AGENTS = (
    "test-runner",
    "unit-test-writer",
    "integration-test-writer",
    "test-unit-reviewer",
)
UPSTREAM_TOKENS = ("vitest", "crabbox", "check-changed", "autoreview", "telegram", "extensions/")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r"`[^`\n]*`")


@pytest.fixture
def plugin_root(rendered: Path) -> Path:
    return rendered / "python-dev-workflow"


@pytest.fixture
def tests_manager_root(plugin_root: Path) -> Path:
    return plugin_root / "skills" / "tests-manager"


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


def preloaded_skills(path: Path) -> list[str]:
    skills: list[str] = []
    in_skills = False

    for line in frontmatter(path).splitlines():
        if line == "skills:":
            in_skills = True
            continue
        if in_skills and line.startswith("  - "):
            skills.append(line[4:].strip())
        elif in_skills:
            break

    return skills


def heading_slugs(markdown: str) -> set[str]:
    """GitHub-style anchors, with the `-N` suffix for repeated headings."""
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    for line in FENCE.sub("", markdown).splitlines():
        match = re.match(r"#{1,6} (.+)", line)
        if not match:
            continue
        slug = re.sub(r"[^\w\- ]", "", match[1].strip().lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        slugs.add(slug if count == 0 else f"{slug}-{count}")
    return slugs


def section(markdown: str, heading: str) -> str:
    """The body of a `##` section, up to the next `##` heading."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", markdown, re.M | re.S)
    assert match, f"missing section: ## {heading}"
    return match[1]


def text_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def test_metadata_paths_resolve_from_declaring_file(
    plugin_root: Path, tests_manager_root: Path
) -> None:
    """A metadata key names a runtime path, so it resolves in the shipped tree."""
    metadata_files = [
        tests_manager_root / "SKILL.md",
        plugin_root / "agents" / "test-writer.md",
        plugin_root / "agents" / "test-assessor.md",
    ]

    missing_paths = []
    for metadata_file in metadata_files:
        keys = metadata_path_keys(metadata_file)
        assert keys, f"{metadata_file.name} declares no references"
        for key in keys:
            if not (metadata_file.parent / key).resolve().is_file():
                missing_paths.append(f"{metadata_file.relative_to(plugin_root)} -> {key}")

    assert missing_paths == []


def test_relative_markdown_links_and_anchors_resolve(plugin_root: Path) -> None:
    broken = []

    for path in plugin_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        prose = CODE_SPAN.sub("", FENCE.sub("", text))
        for target in LINK.findall(prose):
            if re.match(r"[a-z]+:", target):
                continue
            file_part, _, anchor = target.partition("#")
            linked = (path.parent / file_part).resolve() if file_part else path
            where = f"{path.relative_to(plugin_root)} -> {target}"
            if not linked.exists():
                broken.append(f"{where}: missing file")
            elif anchor and anchor not in heading_slugs(linked.read_text(encoding="utf-8")):
                broken.append(f"{where}: missing anchor")

    assert broken == []


def test_ledger_junk_enum_matches_junk_pattern_headings(tests_manager_root: Path) -> None:
    references = tests_manager_root / "references"
    ledger = json.loads((references / "schemas" / "ledger.schema.json").read_text(encoding="utf-8"))
    junk_patterns = section(
        (references / "rules" / "test-value.md").read_text(encoding="utf-8"), "Junk patterns"
    )

    headings = re.findall(r"^### (.+)$", junk_patterns, re.M)

    assert headings
    assert sorted(ledger["$defs"]["junk_pattern"]["enum"]) == sorted(headings)


def test_no_agent_preloads_tests_manager(plugin_root: Path) -> None:
    preloading = [
        agent.name
        for agent in sorted((plugin_root / "agents").glob("*.md"))
        if "tests-manager" in preloaded_skills(agent)
    ]

    assert preloading == []


def test_tree_names_no_removed_agent(rendered: Path) -> None:
    mentions = [
        f"{path.relative_to(rendered)}: {name}"
        for path in text_files(rendered)
        for name in REMOVED_AGENTS
        if name in path.read_text(encoding="utf-8") or name in path.name
    ]

    assert mentions == []


def test_plugin_carries_no_upstream_repository_specifics(plugin_root: Path) -> None:
    mentions = [
        f"{path.relative_to(plugin_root)}: {token}"
        for path in text_files(plugin_root)
        for token in UPSTREAM_TOKENS
        if token in path.read_text(encoding="utf-8").lower()
    ]

    assert mentions == []


def test_celery_expert_carries_no_testing_guidance(plugin_root: Path) -> None:
    celery_skill_root = plugin_root / "skills" / "celery-expert"
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


def test_tests_manager_owns_celery_testing_assets(tests_manager_root: Path) -> None:
    domains = tests_manager_root / "references" / "domains"
    celery_examples = domains / "examples" / "celery"

    assert (domains / "celery.md").is_file()
    assert (celery_examples / "conftest_celery.py").is_file()
    assert (celery_examples / "test_tasks.py").is_file()
    assert '"references/domains/celery.md"' in frontmatter(tests_manager_root / "SKILL.md")

    # A real conftest.py here would be auto-loaded as a non-top-level conftest
    # and apply its pytest_plugins to the whole suite. The example carries a
    # neutral name so it is only ever read, never executed as config.
    assert not (celery_examples / "conftest.py").exists()


def test_celery_expert_routes_test_work_to_tests_manager(
    plugin_root: Path, tests_manager_root: Path
) -> None:
    celery_skill_path = plugin_root / "skills" / "celery-expert" / "SKILL.md"
    routing_target = "python-dev-workflow:tests-manager"

    assert (tests_manager_root / "SKILL.md").is_file()
    assert routing_target in frontmatter(celery_skill_path)
    assert routing_target in body(celery_skill_path)


def test_agent_frontmatter_excludes_examples(plugin_root: Path) -> None:
    agent_files = sorted((plugin_root / "agents").glob("*.md"))

    assert agent_files
    invalid_files = [
        agent_file.relative_to(plugin_root)
        for agent_file in agent_files
        if "<example>" in frontmatter(agent_file)
    ]

    assert invalid_files == []


def test_e2e_level_stops_and_asks_when_resources_are_unclear(
    tests_manager_root: Path,
) -> None:
    e2e = (tests_manager_root / "references" / "levels" / "e2e.md").read_text(encoding="utf-8")

    assert "stop immediately" in e2e
    assert "Do not write or run E2E tests" in e2e
    assert "ask the user with " in e2e


def test_write_workflow_orders_levels_outside_in(tests_manager_root: Path) -> None:
    write = (tests_manager_root / "references" / "workflows" / "write.md").read_text(
        encoding="utf-8"
    )

    assert "E2E → Integration → Unit" in write


def test_scenario_planner_does_not_choose_levels(plugin_root: Path) -> None:
    planner = body(plugin_root / "agents" / "test-scenario-planner.md")

    assert "Do not choose test levels" in planner
    assert "scenarios.schema.json" in planner
