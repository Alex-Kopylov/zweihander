"""Behavioural tests for the export-pdf render script.

These compile real documents, so they need the `typst` binary and skip
without it. They replace substring assertions about the script's text,
which passed just as happily on a script that did nothing.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    shutil.which("typst") is None, reason="typst not installed"
)


@pytest.fixture
def script(rendered: Path) -> Path:
    return (
        rendered
        / "job-hunt-toolkit"
        / "skills"
        / "export-pdf"
        / "scripts"
        / "typst-to-pdf.sh"
    )

CV = """\
#set document(title: "CV", author: "Jane Doe")
= Jane Doe
Senior ML Engineer. Shipped ranking models in production.
"""


def run(
    script: Path, typ: Path, pdf: Path, **env_overrides: str
) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        ["bash", str(script), str(typ), str(pdf)],
        capture_output=True,
        text=True,
        env=env,
    )


def test_compiles_a_cv_to_a_real_pdf(script: Path, tmp_path: Path) -> None:
    typ = tmp_path / "Jane_Doe_ML_Engineer_CV.typ"
    typ.write_text(CV, encoding="utf-8")
    pdf = tmp_path / "Jane_Doe_ML_Engineer_CV.pdf"

    result = run(script, typ, pdf)

    assert result.returncode == 0, result.stderr
    assert pdf.read_bytes().startswith(b"%PDF")


def test_document_metadata_comes_from_the_source(script: Path, tmp_path: Path) -> None:
    # The export path relies on this: clean metadata is a property of the
    # .typ, which is why nothing scrubs the output afterwards.
    typ = tmp_path / "cv.typ"
    typ.write_text(CV, encoding="utf-8")
    pdf = tmp_path / "cv.pdf"

    assert run(script, typ, pdf).returncode == 0

    raw = pdf.read_bytes()
    assert re.search(rb"/Title\s*\(CV\)", raw)
    assert b"Keywords" not in raw


def test_timestamp_is_pinned_to_utc(script: Path, tmp_path: Path) -> None:
    # Typst otherwise stamps the machine's local offset, leaking the
    # applicant's timezone band.
    typ = tmp_path / "cv.typ"
    typ.write_text(CV, encoding="utf-8")
    pdf = tmp_path / "cv.pdf"

    assert run(script, typ, pdf, TZ="Europe/Moscow").returncode == 0

    dates = re.findall(rb"/CreationDate\s*\(D:([^)]*)\)", pdf.read_bytes())
    assert dates, "no /CreationDate in output"
    for date in dates:
        assert date.endswith(b"Z"), f"local offset leaked: {date!r}"


def test_compile_error_exits_6_and_writes_no_pdf(script: Path, tmp_path: Path) -> None:
    typ = tmp_path / "broken.typ"
    typ.write_text("#let x = \n", encoding="utf-8")
    pdf = tmp_path / "broken.pdf"

    result = run(script, typ, pdf)

    assert result.returncode == 6
    assert not pdf.exists()


def test_warning_exits_7(script: Path, tmp_path: Path) -> None:
    # typst exits 0 on a font fallback, but the PDF no longer matches the
    # master, so the script must not report success.
    typ = tmp_path / "cv.typ"
    typ.write_text(
        '#set text(font: "No Such Font XYZ")\n= Jane Doe\nSome body text.\n',
        encoding="utf-8",
    )
    pdf = tmp_path / "cv.pdf"

    result = run(script, typ, pdf)

    assert result.returncode == 7
    assert "warning" in result.stderr.lower()


def test_typst_root_is_honoured_not_shadowed(script: Path, tmp_path: Path) -> None:
    # The script passes no --root, so Typst's own TYPST_ROOT still works for a
    # shared template. An earlier version overrode it and broke this.
    (tmp_path / "template.typ").write_text("#let cv(body) = body\n", encoding="utf-8")
    company = tmp_path / "jobs" / "acme"
    company.mkdir(parents=True)
    typ = company / "cv.typ"
    typ.write_text(
        '#import "/template.typ": cv\n#show: cv\n= Jane Doe\nBody text.\n',
        encoding="utf-8",
    )
    pdf = company / "cv.pdf"

    # Without the wider root the import is outside the sandbox and must fail.
    assert run(script, typ, pdf).returncode == 6
    assert run(script, typ, pdf, TYPST_ROOT=str(tmp_path)).returncode == 0


def test_relative_paths_are_rejected(script: Path, tmp_path: Path) -> None:
    typ = tmp_path / "cv.typ"
    typ.write_text(CV, encoding="utf-8")

    assert run(script, typ, Path("relative.pdf")).returncode == 2
