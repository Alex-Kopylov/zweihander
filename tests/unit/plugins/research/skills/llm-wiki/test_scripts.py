"""The llm-wiki helper scripts, run from the tree a user installs."""

import hashlib
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

SCRIPTS = Path("research", "skills", "llm-wiki", "scripts")


def run(script: Path, *args: str) -> str:
    return subprocess.run([str(script), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def scripts(rendered: Path) -> Path:
    return rendered / SCRIPTS


def test_scripts_are_executable(scripts: Path) -> None:
    for name in ("body_sha256.sh", "freshness.sh"):
        assert scripts.joinpath(name).stat().st_mode & stat.S_IXUSR


def test_body_hash_skips_frontmatter(scripts: Path, tmp_path: Path) -> None:
    body = "# Title\n\nbody text\n"
    bare = tmp_path / "bare.md"
    bare.write_text(body, encoding="utf-8")
    fronted = tmp_path / "fronted.md"
    fronted.write_text("---\ntitle: x\n---\n" + body, encoding="utf-8")
    expected = hashlib.sha256(body.encode()).hexdigest()
    assert run(scripts / "body_sha256.sh", str(bare)) == expected
    assert run(scripts / "body_sha256.sh", str(fronted)) == expected


def test_freshness_follows_todays_year(scripts: Path) -> None:
    year = datetime.now(tz=UTC).astimezone().year
    assert run(scripts / "freshness.sh", f"{year}-09-18") == "fresh"
    assert run(scripts / "freshness.sh", f"{year - 1}-01-01") == "fresh"
    assert run(scripts / "freshness.sh", str(year - 2)) == "recent"
    assert run(scripts / "freshness.sh", f"{year - 3}-12-31") == "historical"


def test_freshness_rejects_a_non_date(scripts: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run(scripts / "freshness.sh", "yesterday")
