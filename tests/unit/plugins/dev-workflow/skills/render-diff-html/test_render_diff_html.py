"""The wrapper isolates scratch files without moving its published reports."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("override", [None, "", "custom scratch"])
def test_scratch_root_and_cleanup_preserve_report_location(
    rendered: Path, tmp_path: Path, override: str | None
) -> None:
    script = rendered / "dev-workflow/skills/render-diff-html/scripts/render_diff_html.sh"
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("before\n")
    new.write_text("after\n")
    system_tmp = tmp_path / "system-temp"
    system_tmp.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npx = bin_dir / "npx"
    npx.write_text(
        "#!/usr/bin/env bash\n"
        'while [ "$#" -gt 0 ]; do\n'
        '  case "$1" in --file) output=$2; shift ;; esac\n'
        "  input=$1\n"
        "  shift\n"
        "done\n"
        'test -s "$input" || exit 1\n'
        'printf "%s\\n" "$input" > "$SCRATCH_TRACE"\n'
        'printf "report\\n" > "$output"\n'
    )
    npx.chmod(0o755)
    trace = tmp_path / "scratch-path.txt"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "TMPDIR": str(system_tmp),
        "SCRATCH_TRACE": str(trace),
    }
    env.pop("ZWEIHANDER_TMP_DIR", None)
    if override is not None:
        env["ZWEIHANDER_TMP_DIR"] = override

    result = subprocess.run(
        ["bash", str(script), "--files", str(old), str(new)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = Path(result.stdout.strip())
    assert report.parent == system_tmp / "codex-diff2html"
    assert report.read_text() == "report\n"
    scratch = Path(trace.read_text().strip())
    if not scratch.is_absolute():
        scratch = tmp_path / scratch
    expected = tmp_path / (override or ".tmp/zweihander") / "runs/render-diff-html"
    assert scratch.parent.parent == expected
    assert not scratch.parent.exists()
