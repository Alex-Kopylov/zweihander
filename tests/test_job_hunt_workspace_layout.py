import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/job-hunt-toolkit"

SLUG_RE = "^[a-z0-9]+(?:_[a-z0-9]+)*$"
# The reference docs express the same rule as a bash `[[ =~ ]]` test, and bash
# ERE has no non-capturing group.
SLUG_RE_ERE = "^[a-z0-9]+(_[a-z0-9]+)*$"


def test_canonical_layout_is_jobs_company() -> None:
    layout = (PLUGIN / "references/workspace-layout.md").read_text(encoding="utf-8")
    assert "jobs/<company>/" in layout
    assert "references/naming-rules.md" in layout
    assert "no fallback" in layout


def test_new_application_enforces_slug_regex_and_jobs_prefix() -> None:
    skill = (PLUGIN / "skills/new-application/SKILL.md").read_text(encoding="utf-8")
    assert SLUG_RE in skill
    assert "mkdir -p <workspace>/jobs/<slug>" in skill
    assert "deny-list" not in skill.lower()


def test_naming_rules_forbid_hyphenated_slugs() -> None:
    naming = (PLUGIN / "references/naming-rules.md").read_text(encoding="utf-8")
    assert SLUG_RE_ERE in naming
    assert "acme-robotics" not in naming
    assert "jobs/acme_robotics/" in naming


def test_plugin_manifests_agree_on_version() -> None:
    claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert claude["version"] == codex["version"] == "0.5.0"


def test_render_script_is_typst_only() -> None:
    scripts = PLUGIN / "skills/export-pdf/scripts"
    assert not (scripts / "html-to-pdf.sh").exists()

    script = (scripts / "typst-to-pdf.sh").read_text(encoding="utf-8")
    assert "typst compile" in script
    # The browser pipeline must be gone, not merely unused as a fallback.
    assert "--print-to-pdf" not in script
    assert "--headless" not in script


def test_no_html_pipeline_references_remain() -> None:
    # Only the "never fall back to X" warnings may name the old toolchain.
    allowed = {
        PLUGIN / "skills/export-pdf/SKILL.md",
        PLUGIN / "skills/export-pdf/scripts/typst-to-pdf.sh",
    }
    banned = ("html", "chromium", "wkhtmltopdf", "weasyprint")

    offenders = []
    for path in PLUGIN.rglob("*"):
        if not path.is_file() or path in allowed:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in banned:
            if term in text:
                offenders.append(f"{path.relative_to(PLUGIN)}: {term}")
    assert not offenders, offenders
