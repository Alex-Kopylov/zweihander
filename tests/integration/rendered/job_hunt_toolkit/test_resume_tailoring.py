"""The resume-tailoring skill ships artifacts, not interactive checkpoints."""

from pathlib import Path


def test_resume_tailoring_produces_required_artifacts_without_checkpoints(
    rendered: Path,
) -> None:
    skill_dir = rendered / "job-hunt-toolkit" / "skills" / "resume-tailoring"
    skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    multi_job = (skill_dir / "references" / "multi-job-workflow.md").read_text(
        encoding="utf-8"
    )

    assert "## Autonomy" not in skill
    assert "autonomously" not in skill
    assert "## Completion Check" in skill
    assert "Typst source tailored to the target vacancy and role" in skill
    assert "PDF was generated from that Typst source" in skill
    assert "`Before | After | Why`" in skill
    assert "_CV_Report.md" not in skill

    for forbidden in ["**Checkpoint:**", "Every checkpoint", "INTERACTIVE** (default)"]:
        assert forbidden not in skill
        assert forbidden not in multi_job
