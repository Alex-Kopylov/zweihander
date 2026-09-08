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
    assert claude["version"] == codex["version"] == "0.7.0"


def test_browser_render_script_is_gone() -> None:
    # Behaviour of the replacement lives in tests/test_typst_export_script.py.
    assert not (PLUGIN / "skills/export-pdf/scripts/html-to-pdf.sh").exists()
    assert (PLUGIN / "skills/export-pdf/scripts/typst-to-pdf.sh").exists()


def test_typst_is_the_only_external_dependency() -> None:
    # Metadata is set in the Typst source rather than stripped from the output,
    # so no PDF post-processing tool is needed and the scrub skill is gone.
    assert not (PLUGIN / "skills/scrub-pdf-metadata").exists()

    for path in PLUGIN.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for tool in ("qpdf", "mutool"):
            assert tool not in text, f"{path.relative_to(PLUGIN)} still needs {tool}"


def test_export_path_fixes_metadata_at_the_source() -> None:
    export = (PLUGIN / "skills/export-pdf/SKILL.md").read_text(encoding="utf-8")
    assert "#set document(" in export
    assert "Fix metadata at the source" in export


def test_no_browser_pipeline_remains() -> None:
    # Narrow to the old toolchain's own names: a bare "html" would trip on any
    # future URL or MIME-type mention.
    banned = ("chromium", "wkhtmltopdf", "weasyprint", "--print-to-pdf", "_CV.html")
    allowed = {
        PLUGIN / "skills/export-pdf/SKILL.md",
        PLUGIN / "skills/export-pdf/scripts/typst-to-pdf.sh",
    }

    offenders = []
    for path in PLUGIN.rglob("*"):
        if not path.is_file() or path in allowed:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        offenders += [
            f"{path.relative_to(PLUGIN)}: {term}" for term in banned if term in text
        ]
    assert not offenders, offenders
