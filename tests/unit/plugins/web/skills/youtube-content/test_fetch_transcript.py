"""The youtube-content transcript helper, loaded from the tree a user installs."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path("web", "skills", "youtube-content", "scripts", "fetch_transcript.py")


def load_script(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def transcript_script(rendered: Path) -> ModuleType:
    return load_script(rendered / SCRIPT)


@pytest.mark.parametrize(
    ("url_or_id", "expected"),
    [
        pytest.param("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", id="watch"),
        pytest.param("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ", id="short"),
        pytest.param("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ", id="shorts"),
        pytest.param("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42", "dQw4w9WgXcQ", id="watch-extra-params"),
        pytest.param("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ", id="embed"),
        pytest.param("https://www.youtube.com/live/dQw4w9WgXcQ?si=abc", "dQw4w9WgXcQ", id="live"),
        pytest.param("dQw4w9WgXcQ", "dQw4w9WgXcQ", id="bare-id"),
        pytest.param("https://example.com/watch", "https://example.com/watch", id="unrecognized-passthrough"),
    ],
)
def test_youtube_url_or_id_extracts_video_id(transcript_script: ModuleType, url_or_id: str, expected: str) -> None:
    assert transcript_script.extract_video_id(url_or_id) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        pytest.param(0, "0:00", id="zero"),
        pytest.param(90, "1:30", id="seconds"),
        pytest.param(600, "10:00", id="minutes"),
        pytest.param(3661, "1:01:01", id="hours"),
    ],
)
def test_seconds_format_as_clock_timestamp(transcript_script: ModuleType, seconds: float, expected: str) -> None:
    assert transcript_script.format_timestamp(seconds) == expected


def test_missing_dependency_exits_with_uv_run_hint(
    transcript_script: ModuleType,
    rendered: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", None)

    with pytest.raises(SystemExit) as exited:
        transcript_script.fetch_transcript("dQw4w9WgXcQ")

    assert exited.value.code == 1
    assert f"`uv run {(rendered / SCRIPT).resolve()} URL`" in capsys.readouterr().err
