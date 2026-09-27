"""The interview skill points at the decision log it ships."""

import re
from pathlib import Path


def skill_text(rendered: Path) -> str:
    return (
        rendered / "work-session-tools" / "skills" / "interview" / "SKILL.md"
    ).read_text(encoding="utf-8")


def test_skill_invokes_the_script_it_ships(rendered: Path) -> None:
    assert "scripts/decision_log.sh" in skill_text(rendered)


def test_skill_declares_a_default_decision_log_directory(rendered: Path) -> None:
    """The script's fallback is checked against this value beside the script."""
    declared = re.search(
        r"decision-log-dir: \"(?P<dir>[^\"]+)\"", skill_text(rendered)
    )

    assert declared, "SKILL.md must declare metadata.config.decision-log-dir"
