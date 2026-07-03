"""Harness references must not coach assistants on baseline tools.

Policy source: plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/SKILL.md.
Every harness reads, searches, edits, and writes files and runs shell commands
natively; naming those tools in a harness reference only pollutes context.
References exist to map differently named shared mechanisms (asking the user,
subagent delegation, skill and slash-command invocation, task tracking) and
harness-specific facts such as context-file locations.
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


def harness_reference_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob(
            "plugins/*/skills/*/references/ai-assistant-harnesses/*.md"
        )
        if ".git" not in path.parts
    )


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


def test_harness_reference_metadata_links_resolve() -> None:
    problems = []

    for skill_md in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        skill_dir = skill_md.parent
        frontmatter_end = skill_md.read_text(encoding="utf-8").find("\n---", 4)
        frontmatter = skill_md.read_text(encoding="utf-8")[:frontmatter_end]
        for match in re.finditer(
            r"ai-assistant-harness-adaptation\.(?!action-matrix)[\w-]+:\s*(\S+)",
            frontmatter,
        ):
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
