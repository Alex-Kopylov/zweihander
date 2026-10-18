"""blocked-page-recovery's body validation, route ladder and CLI contract, loaded from the tree a user installs."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest import mock

import pytest

TARGET = "https://blocked.example/article"
# Past the 3072-byte snapshot floor, still under the 8192-byte redirect-stub ceiling.
PADDING = b"x" * 4000
NO_COPY_HINT = "No archive copy found. Try the API-first pivot or the browser tool."


def load_script(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def recover_page(rendered: Path) -> ModuleType:
    return load_script(rendered / "web" / "skills" / "blocked-page-recovery" / "scripts" / "recover_page.py")


@pytest.mark.parametrize(
    ("body", "route", "expected"),
    [
        pytest.param(b"x" * 100, "wayback", "body_too_small:100<3072", id="under-snapshot-floor"),
        pytest.param(b"x" * 511, "jina", "body_too_small:511<512", id="under-jina-floor"),
        pytest.param(
            b"<title>Just a\n  Moment...</title>" + PADDING,
            "wayback",
            "interstitial_title:'just a moment'",
            id="interstitial-title",
        ),
        pytest.param(
            b'<meta http-equiv="refresh" content="0;url=https://blocked.example/article">' + PADDING,
            "archive_today",
            "redirect_stub_to_origin",
            id="refresh-back-to-origin",
        ),
        pytest.param(
            b'<script>window.location="https://other.example/"</script>' + PADDING,
            "wayback",
            None,
            id="redirect-to-other-host",
        ),
        pytest.param(
            b"<script>location.replace('https://blocked.example/')</script>" + b"x" * 8192,
            "wayback",
            None,
            id="origin-redirect-in-large-body",
        ),
        pytest.param(b"<title>Real article</title>" + PADDING, "wayback", None, id="genuine"),
    ],
)
def test_validate_candidate_body_returns_expected_verdict(recover_page, body, route, expected):
    assert recover_page.validate(body, route, TARGET) == expected


def test_first_route_miss_returns_second_route_hit(recover_page):
    hit = {"route": "second", "provenance": "snapshot", "body": b"page"}
    first, second = mock.Mock(return_value=None), mock.Mock(return_value=hit)
    with mock.patch.object(recover_page, "ROUTES", (first, second)):
        assert recover_page.recover(TARGET, 7) is hit
    first.assert_called_once_with(TARGET, 7)
    second.assert_called_once_with(TARGET, 7)


def test_all_snapshots_miss_without_jina_key_returns_none_and_skips_jina(recover_page, monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)
    with (
        mock.patch.object(recover_page, "_fetch", return_value=(404, b"")) as fetch,
        mock.patch.object(recover_page, "_fetch_follow", return_value=(404, b"", "")) as follow,
    ):
        assert recover_page.recover(TARGET, 5) is None
    # Wayback discovery, then its redirect fallback, then archive.today rotation - and nothing on r.jina.ai.
    assert [c.args[0] for c in fetch.call_args_list] == [
        "https://archive.org/wayback/available?url=https%3A%2F%2Fblocked.example%2Farticle",
        *(f"https://{host}/newest/{TARGET}" for host in ("archive.ph", "archive.md", "archive.li", "archive.is")),
    ]
    follow.assert_called_once_with("https://web.archive.org/web/2/" + TARGET, 5)


@pytest.mark.parametrize(
    "api_url",
    ["file:///etc/passwd", "https://evil.example/web/20260101000000/page", "ftp://web.archive.org/x"],
)
def test_wayback_api_url_outside_wayback_is_never_opened(recover_page, api_url):
    discovery = json.dumps({"archived_snapshots": {"closest": {"available": True, "url": api_url}}}).encode()
    with (
        mock.patch.object(recover_page, "_fetch", return_value=(200, discovery)),
        mock.patch.object(recover_page, "_fetch_follow", return_value=(404, b"", "")) as follow,
    ):
        assert recover_page.try_wayback(TARGET, 5) is None
    follow.assert_called_once_with("https://web.archive.org/web/2/" + TARGET, 5)


def test_all_snapshots_miss_with_jina_key_returns_live_jina_hit(recover_page, monkeypatch):
    monkeypatch.setenv("JINA_API_KEY", "secret")
    page = b"<title>Live</title>" + b"x" * 600

    def only_jina_answers(url, *_, **__):
        return (200, page) if url.startswith("https://r.jina.ai/") else (404, b"")

    with (
        mock.patch.object(recover_page, "_fetch", side_effect=only_jina_answers) as fetch,
        mock.patch.object(recover_page, "_fetch_follow", return_value=(404, b"", "")),
    ):
        result = recover_page.recover(TARGET, 5)
    assert result == {
        "route": "jina_reader",
        "provenance": "live",
        "snapshot_timestamp": None,
        "source_url": "https://r.jina.ai/" + TARGET,
        "body": page,
    }
    fetch.assert_called_with("https://r.jina.ai/" + TARGET, 5, headers={"Authorization": "Bearer secret"})


def test_cli_nothing_recovered_exits_1_with_json_hint_on_stderr(recover_page, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["recover_page.py", TARGET, "--json"])
    with mock.patch.object(recover_page, "recover", return_value=None) as recover:
        assert recover_page.main() == 1
    recover.assert_called_once_with(TARGET, 25)
    out, err = capsys.readouterr()
    assert not out
    assert err == json.dumps({"recovered": False, "url": TARGET, "hint": NO_COPY_HINT}, indent=2) + "\n"


def test_cli_recovered_snapshot_with_out_exits_0_writes_body_and_prints_json(
    recover_page, monkeypatch, capsys, tmp_path
):
    saved = tmp_path / "page.html"
    snapshot = "https://web.archive.org/web/20260101000000/" + TARGET
    hit = {
        "route": "wayback",
        "provenance": "snapshot",
        "snapshot_timestamp": "20260101000000",
        "source_url": snapshot,
        "body": b"<html>page</html>",
    }
    monkeypatch.setattr(sys, "argv", ["recover_page.py", TARGET, "--json", "--out", str(saved)])
    with mock.patch.object(recover_page, "recover", return_value=hit):
        assert recover_page.main() == 0
    out, err = capsys.readouterr()
    assert json.loads(out) == {
        "route": "wayback",
        "provenance": "snapshot",
        "snapshot_timestamp": "20260101000000",
        "source_url": snapshot,
        "recovered": True,
        "url": TARGET,
        "body_bytes": 17,
        "saved_to": str(saved),
    }
    assert saved.read_bytes() == b"<html>page</html>"
    assert "ARCHIVED SNAPSHOT" in err
