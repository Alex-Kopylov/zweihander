"""Harness references must follow harness adaptation policy.

Policy source: plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/SKILL.md.
Every harness reads, searches, edits, and writes files and runs shell commands
natively; naming those tools in a harness reference only pollutes context.
References exist to map differently named shared mechanisms (asking the user,
subagent delegation, skill and slash-command invocation, task tracking) and
harness-specific facts such as context-file locations.

Harness references also speak only in their own harness's vocabulary, and every
adapted SKILL.md carries the exact standard harness adaptation sentence.
"""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

BASELINE_TOOL_TERMS = [
    "`Read`",
    "`Write`",
    "`Edit`",
    "`MultiEdit`",
    "`Glob`",
    "`Grep`",
    "`Bash`",
    "`apply_patch`",
    "`exec_command`",
    "`write_stdin`",
    "`sed`",
    "`nl`",
    "`rg`",
    "`rg --files`",
]

FOREIGN_TERMS_BY_REFERENCE = {
    "codex.md": {
        "case_insensitive": ["claude"],
        "exact": [
            "`AskUserQuestion`",
            "`TaskCreate`",
            "`TaskList`",
            "`TaskUpdate`",
            "`TaskGet`",
            "`TaskOutput`",
            "`TaskStop`",
            "`TeamCreate`",
            "`SlashCommand`",
            "`allowed-tools`",
            "`Agent`",
            "`Skill`",
            "Skill(",
        ],
    },
    "claude-code.md": {
        "case_insensitive": ["codex"],
        "exact": ["`request_user_input`", "`spawn_agent`", "`update_plan`"],
    },
}

HARNESS_ADAPTATION_SENTENCE = (
    "Depending on who you are as an AI agent, load exactly one metadata-linked "
    "reference and skip every non-matching file."
)

HARNESS_METADATA_LINK_RE = re.compile(
    r"ai-assistant-harness-adaptation\.(?!action-matrix)[\w-]+:\s*(\S+)"
)


def harness_reference_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob(
            "plugins/*/skills/*/references/ai-assistant-harnesses/*.md"
        )
        if ".git" not in path.parts
    )


def skill_frontmatter(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    frontmatter_end = text.find("\n---", 4)
    return text[:frontmatter_end]


def test_harness_references_exist() -> None:
    assert harness_reference_files(), "expected at least one harness reference"


def test_harness_references_do_not_coach_baseline_tools() -> None:
    violations = []
    for path in harness_reference_files():
        text = path.read_text(encoding="utf-8")
        for term in BASELINE_TOOL_TERMS:
            if term in text:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: contains {term}"
                )

    assert not violations, (
        "harness references must not name baseline file/search/edit/shell "
        "tools (see adapt-skill-for-ai-harness policy):\n"
        + "\n".join(violations)
    )


def test_harness_references_use_only_their_own_harness_language() -> None:
    violations = []
    for path in harness_reference_files():
        foreign_terms = FOREIGN_TERMS_BY_REFERENCE.get(path.name)
        if foreign_terms is None:
            continue

        text = path.read_text(encoding="utf-8")
        lowered_text = text.lower()
        for term in foreign_terms["case_insensitive"]:
            if term.lower() in lowered_text:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: contains {term!r}"
                )
        for term in foreign_terms["exact"]:
            if term in text:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}: contains {term}"
                )

    assert not violations, (
        "harness references must not name another harness or another "
        "harness's tool vocabulary (see adapt-skill-for-ai-harness policy):\n"
        + "\n".join(violations)
    )


def test_harness_reference_metadata_links_resolve() -> None:
    problems = []

    for skill_md in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        skill_dir = skill_md.parent
        frontmatter = skill_frontmatter(skill_md)
        for match in HARNESS_METADATA_LINK_RE.finditer(frontmatter):
            target = skill_dir / match.group(1)
            if not target.is_file():
                problems.append(
                    f"{skill_md.relative_to(REPO_ROOT)}: broken link {match.group(1)}"
                )

    for ref in harness_reference_files():
        skill_dir = ref.parent.parent.parent
        skill_md = skill_dir / "SKILL.md"
        rel = ref.relative_to(skill_dir).as_posix()
        if not skill_md.is_file() or rel not in skill_md.read_text(encoding="utf-8"):
            problems.append(
                f"{ref.relative_to(REPO_ROOT)}: not linked from its SKILL.md"
            )

    assert not problems, "\n".join(problems)


def test_adapted_skills_use_standard_harness_adaptation_sentence() -> None:
    violations = []

    for skill_md in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        frontmatter = skill_frontmatter(skill_md)
        if not HARNESS_METADATA_LINK_RE.search(frontmatter):
            continue
        if HARNESS_ADAPTATION_SENTENCE not in text:
            violations.append(
                f"{skill_md.relative_to(REPO_ROOT)}: missing standard sentence"
            )

    assert not violations, (
        "adapted SKILL.md files must contain the exact standard harness "
        "adaptation sentence (see adapt-skill-for-ai-harness policy):\n"
        + "\n".join(violations)
    )
