from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/job-hunt-toolkit/skills/resume-tailoring/SKILL.md.j2"
MULTI_JOB = SKILL.parent / "references/multi-job-workflow.md"


def test_resume_tailoring_produces_required_artifacts_without_checkpoints() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    multi_job = MULTI_JOB.read_text(encoding="utf-8")

    assert "## Autonomy" not in skill
    assert "autonomously" not in skill
    assert "## Completion Check" in skill
    assert "HTML tailored to the target vacancy and role" in skill
    assert "PDF was generated from that HTML" in skill
    assert "`Before | After | Why`" in skill
    assert "_CV_Report.md" not in skill
    assert "{{ actions.AskUser | call }}" in skill

    for forbidden in ["**Checkpoint:**", "Every checkpoint", "INTERACTIVE** (default)"]:
        assert forbidden not in skill
        assert forbidden not in multi_job
