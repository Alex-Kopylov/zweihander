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


def test_render_script_does_not_shadow_typst_root() -> None:
    # Typst's default root is already the source file's directory, and passing
    # --root would override the user's TYPST_ROOT.
    script = (PLUGIN / "skills/export-pdf/scripts/typst-to-pdf.sh").read_text(encoding="utf-8")
    invocations = [
        line for line in script.splitlines()
        if "typst compile" in line and not line.lstrip().startswith("#")
    ]
    assert invocations, "no typst compile invocation found"
    assert not any("--root" in line for line in invocations)
    assert "JOB_HUNT_TYPST_ROOT" not in script


def test_scrub_strips_with_qpdf_before_exiftool() -> None:
    # exiftool writes PDFs as an incremental update, so `-all=` is reversible:
    # the stripped values stay recoverable. qpdf rewrites the file, and running
    # it first also empties what exiftool's own update could restore.
    commands = (
        PLUGIN / "skills/scrub-pdf-metadata/references/exiftool-commands.md"
    ).read_text(encoding="utf-8")
    qpdf_at = commands.index("qpdf --remove-info --remove-metadata")
    exiftool_set_at = commands.index('exiftool -Author=')
    assert qpdf_at < exiftool_set_at
    # `exiftool -all=` may only appear as a prohibition, never as the strip step.
    strip_lines = [
        line for line in commands.splitlines()
        if "exiftool -all=" in line and not line.lstrip().startswith(("-", "Do", "So"))
    ]
    assert not strip_lines, strip_lines


def test_export_path_does_not_scrub_its_own_output() -> None:
    # Typst sets Title/Author/Keywords from the source, so exports are clean by
    # construction; scrubbing them only adds size and an "I ran a scrubber" tell.
    export = (PLUGIN / "skills/export-pdf/SKILL.md").read_text(encoding="utf-8")
    assert "#set document(" in export
    assert "scrub-pdf-metadata` skill on the produced PDF" not in export


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
