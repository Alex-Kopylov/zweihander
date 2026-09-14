import re
import shutil
import subprocess
from pathlib import Path

import pytest
from pydantic import EmailStr, TypeAdapter, ValidationError


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/job-hunt-toolkit"
SYNC_SCRIPT = PLUGIN / "skills/init-workspace/scripts/sync-application-statuses.sh"
PROVIDER_AGENTS = sorted((PLUGIN / "agents").glob("*-agent.md"))
PROVIDER_AGENT = PROVIDER_AGENTS[0]
TRACKING_SKILL = PLUGIN / "skills/track-hiring-emails/SKILL.md"
EMAIL_ADAPTER = TypeAdapter(EmailStr)


def install_sync_script(workspace: Path) -> Path:
    target = workspace / "sync-application-statuses.sh"
    shutil.copy2(SYNC_SCRIPT, target)
    shutil.copy2(SYNC_SCRIPT.with_name("application_records.py"), workspace / "application_records.py")
    target.chmod(0o755)
    return target


def write_record(workspace: Path, folder: str, frontmatter: str) -> Path:
    company_dir = workspace / "jobs" / folder
    company_dir.mkdir(parents=True)
    record = company_dir / "company.md"
    record.write_text(f"{frontmatter}\n\n# Application\n", encoding="utf-8")
    return record


def run_sync(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(script)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_sync_generates_deterministic_table_from_valid_records(tmp_path: Path) -> None:
    script = install_sync_script(tmp_path)
    write_record(
        tmp_path,
        "beta_labs",
        """---
company: beta Labs
role: ML Engineer
applied: null
status: screening
---""",
    )
    write_record(
        tmp_path,
        "alpha_co",
        """---
company: "Alpha Co"
role: "Platform | Data"
applied: 2026-09-01
status: interview
---""",
    )

    first = run_sync(script)
    assert first.returncode == 0, first.stderr
    expected = """# Applications

| Company | Role | Status | Applied |
|---|---|---|---|
| Alpha Co | Platform \\| Data | interview | 2026-09-01 |
| beta Labs | ML Engineer | screening | null |
"""
    assert (tmp_path / "APPLICATIONS.md").read_text(encoding="utf-8") == expected

    second = run_sync(script)
    assert second.returncode == 0, second.stderr
    assert (tmp_path / "APPLICATIONS.md").read_text(encoding="utf-8") == expected


@pytest.mark.parametrize(
    "frontmatter",
    [
        "company: Missing delimiters\nrole: Engineer\napplied: null\nstatus: applied",
        "---\ncompany: Missing Role\napplied: null\nstatus: applied\n---",
        "---\ncompany: Bad Status\nrole: Engineer\napplied: null\nstatus: waiting\n---",
        "---\ncompany: ~\nrole: Engineer\napplied: null\nstatus: applied\n---",
        "---\ncompany: Null\nrole: Engineer\napplied: null\nstatus: applied\n---",
        "---\ncompany: # missing\nrole: Engineer\napplied: null\nstatus: applied\n---",
        "---\ncompany: Example\nrole: NULL\napplied: null\nstatus: applied\n---",
    ],
)
def test_sync_rejects_invalid_records_without_replacing_output(
    tmp_path: Path, frontmatter: str
) -> None:
    script = install_sync_script(tmp_path)
    invalid = write_record(tmp_path, "invalid_company", frontmatter)
    previous = "# Existing applications\n"
    output = tmp_path / "APPLICATIONS.md"
    output.write_text(previous, encoding="utf-8")

    result = run_sync(script)

    assert result.returncode != 0
    assert str(invalid) in result.stderr
    assert output.read_text(encoding="utf-8") == previous


def test_sync_accepts_quoted_yaml_status_with_comment(tmp_path: Path) -> None:
    script = install_sync_script(tmp_path)
    write_record(
        tmp_path, "acme",
        '---\ncompany: "Acme #1" # name\nrole: Engineer\napplied: null\nstatus: "applied" # confirmed\n---',
    )
    result = run_sync(script)
    assert result.returncode == 0, result.stderr
    assert "| Acme #1 | Engineer | applied | null |" in (tmp_path / "APPLICATIONS.md").read_text()


def valid_email_tokens(text: str) -> list[str]:
    addresses = []
    for token in text.split():
        candidate = token.strip("`'\"()[]{}<>,.;:")
        try:
            addresses.append(str(EMAIL_ADAPTER.validate_python(candidate)))
        except ValidationError:
            continue
    return addresses


def test_email_entrypoints_load_shared_runtime_contract() -> None:
    import yaml
    agent = PROVIDER_AGENT.read_text(encoding="utf-8")
    skill = TRACKING_SKILL.read_text(encoding="utf-8")
    assert "model" not in yaml.safe_load(agent.split("---", 2)[1])
    assert "hiring-email-rules.md" in agent
    assert "hiring-email-orchestration.md" in skill
    assert "gmail_apply_labels" not in agent
    for document in (PROVIDER_AGENT, TRACKING_SKILL):
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            assert (document.parent / target).is_file(), target
    assert valid_email_tokens(agent) == []
    assert valid_email_tokens(skill) == []
