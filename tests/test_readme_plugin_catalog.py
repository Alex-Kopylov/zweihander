import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
EXPECTED_CATALOG_HEADINGS = [
    "General User Productivity",
    "General AI User Productivity",
    "Programming",
    "AI Engineer",
]


def readme_mermaid_blocks() -> list[str]:
    readme = README.read_text(encoding="utf-8")
    return re.findall(r"```mermaid\n(.*?)\n```", readme, flags=re.DOTALL)


def top_level_kanban_sections(block: str) -> list[str]:
    lines = block.splitlines()
    if not lines or lines[0] != "kanban":
        return []

    return [
        line.strip()
        for line in lines[1:]
        if line.startswith("  ") and not line.startswith("    ") and line.strip()
    ]


def section_label(section: str) -> str:
    match = re.fullmatch(r"[A-Za-z0-9_]+\[(.+)\]", section)
    assert match, f"unexpected kanban section syntax: {section}"
    return match.group(1)


def catalog_kanban_blocks() -> list[str]:
    return [block for block in readme_mermaid_blocks() if block.startswith("kanban")]


def test_readme_kanban_blocks_stay_within_mermaid_styled_sections() -> None:
    kanban_sections = [
        top_level_kanban_sections(block) for block in catalog_kanban_blocks()
    ]

    assert kanban_sections
    assert all(len(sections) <= 10 for sections in kanban_sections)


def test_readme_catalog_uses_requested_kanban_categories() -> None:
    readme = README.read_text(encoding="utf-8")

    headings = re.findall(r"^### (.+)$", readme, flags=re.MULTILINE)

    assert headings[: len(EXPECTED_CATALOG_HEADINGS)] == EXPECTED_CATALOG_HEADINGS
    assert len(catalog_kanban_blocks()) == len(EXPECTED_CATALOG_HEADINGS)


def test_readme_catalog_kanban_lists_every_plugin_once() -> None:
    expected_plugins = sorted(
        path.parent.parent.name
        for path in (REPO_ROOT / "plugins").glob("*/.codex-plugin/plugin.json")
    )
    actual_plugins = sorted(
        section_label(section)
        for block in catalog_kanban_blocks()
        for section in top_level_kanban_sections(block)
    )

    assert actual_plugins == expected_plugins
