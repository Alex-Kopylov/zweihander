"""The job-hunt workspace layout as it reaches a user's installed tree."""

import json
from pathlib import Path

import pytest


SLUG_RE = "^[a-z0-9]+(?:_[a-z0-9]+)*$"
# The reference docs express the same rule as a bash `[[ =~ ]]` test, and bash
# ERE has no non-capturing group.
SLUG_RE_ERE = "^[a-z0-9]+(_[a-z0-9]+)*$"


@pytest.fixture(scope="session")
def plugin(rendered: Path) -> Path:
    return rendered / "job-hunt-toolkit"


@pytest.fixture(scope="session")
def export_pdf_skill(plugin: Path) -> Path:
    return plugin / "skills/export-pdf/SKILL.md"


def test_canonical_layout_is_jobs_company(plugin: Path) -> None:
    layout = (plugin / "references/workspace-layout.md").read_text(encoding="utf-8")
    assert "jobs/<company>/" in layout
    assert "references/naming-rules.md" in layout
    assert "no fallback" in layout


def test_new_application_enforces_slug_regex_and_jobs_prefix(plugin: Path) -> None:
    skill = (plugin / "skills/new-application/SKILL.md").read_text(encoding="utf-8")
    assert SLUG_RE in skill
    assert "mkdir -p <workspace>/jobs/<slug>" in skill
    assert "deny-list" not in skill.lower()


def test_naming_rules_forbid_hyphenated_slugs(plugin: Path) -> None:
    naming = (plugin / "references/naming-rules.md").read_text(encoding="utf-8")
    assert SLUG_RE_ERE in naming
    assert "acme-robotics" not in naming
    assert "jobs/acme_robotics/" in naming


def test_plugin_manifest_pins_the_published_version(plugin: Path) -> None:
    """Each harness tree carries its own manifest, so both pin the same version."""
    manifest = json.loads(
        next(plugin.glob("*/plugin.json")).read_text(encoding="utf-8")
    )
    assert manifest["version"] == "0.7.0"


def test_browser_render_script_is_gone(plugin: Path) -> None:
    # Behaviour of the replacement is covered by the unit tests mirroring
    # the export-pdf skill's own path.
    assert not (plugin / "skills/export-pdf/scripts/html-to-pdf.sh").exists()
    assert (plugin / "skills/export-pdf/scripts/typst-to-pdf.sh").exists()


def test_typst_is_the_only_external_dependency(plugin: Path) -> None:
    # Metadata is set in the Typst source rather than stripped from the output,
    # so no PDF post-processing tool is needed and the scrub skill is gone.
    assert not (plugin / "skills/scrub-pdf-metadata").exists()

    for path in plugin.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for tool in ("qpdf", "mutool"):
            assert tool not in text, f"{path.relative_to(plugin)} still needs {tool}"


def test_export_path_fixes_metadata_at_the_source(export_pdf_skill: Path) -> None:
    export = export_pdf_skill.read_text(encoding="utf-8")
    assert "#set document(" in export
    assert "Fix metadata at the source" in export


def test_no_browser_pipeline_remains(plugin: Path, export_pdf_skill: Path) -> None:
    # Narrow to the old toolchain's own names: a bare "html" would trip on any
    # future URL or MIME-type mention.
    banned = ("chromium", "wkhtmltopdf", "weasyprint", "--print-to-pdf", "_CV.html")
    allowed = {
        export_pdf_skill,
        plugin / "skills/export-pdf/scripts/typst-to-pdf.sh",
    }

    offenders = []
    for path in plugin.rglob("*"):
        if not path.is_file() or path in allowed:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        offenders += [
            f"{path.relative_to(plugin)}: {term}" for term in banned if term in text
        ]
    assert not offenders, offenders
