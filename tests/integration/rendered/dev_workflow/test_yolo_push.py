"""The yolo-push cleanup question as a user receives it."""

import re
from pathlib import Path


def test_cleanup_question_offers_exactly_delete_or_keep(rendered: Path) -> None:
    skill = (rendered / "dev-workflow" / "skills" / "yolo-push" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    steps = re.split(r"^- \[ \] Step \d+:", skill, flags=re.MULTILINE)
    question = next(step for step in steps if "question" in step)

    options = re.findall(r"^\s+- `([^`]+)`", question, re.MULTILINE)

    assert [option.split()[0] for option in options] == ["Delete", "Keep"]
