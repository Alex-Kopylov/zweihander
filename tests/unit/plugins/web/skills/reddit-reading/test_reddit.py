"""The reddit-reading script's backend selection and throttle handling, loaded from the tree a user installs."""

import argparse
import importlib.util
import io
import urllib.error
from pathlib import Path
from types import ModuleType
from unittest import mock

import pytest


def load_script(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def reddit(rendered: Path) -> ModuleType:
    return load_script(rendered / "web" / "skills" / "reddit-reading" / "scripts" / "reddit.py")


THREAD_ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><author><name>/u/op</name></author><title>Post title</title>
  <link href="https://www.reddit.com/r/test/comments/abc123/post_title/"/><updated>2026-09-01T00:00:00+00:00</updated>
  <content type="html">&lt;div&gt;body text&lt;/div&gt; submitted by /u/op [link] [comments]</content></entry>
<entry><author><name>/u/c1</name></author><title>/u/c1 on Post title</title>
  <link href="https://www.reddit.com/r/test/comments/abc123/post_title/k1/"/><updated>2026-09-01T01:00:00+00:00</updated>
  <content type="html">&lt;p&gt;first comment&lt;/p&gt;</content></entry>
</feed>"""

THREAD_URL = "https://www.reddit.com/r/test/comments/abc123/post_title/"
API_THREAD = [{"data": {"children": [{"kind": "t3", "data": {"title": "T"}}]}}, {"data": {"children": []}}]
ATOM_THREAD_ENTRIES = [{"title": "Post title", "author": "op", "created": None, "url": THREAD_URL, "body": "b"}]
FEED_RESPONSE = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>', {})


@pytest.fixture
def oauth_env(monkeypatch):
    monkeypatch.setenv("REDDIT_CLIENT_ID", "cid")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "sec")


def _http_error(code, headers):
    return urllib.error.HTTPError("https://www.reddit.com/x", code, "msg", headers, io.BytesIO(b""))


def test_anonymous_thread_uses_atom_feed_and_waits_out_a_429_exactly_once(reddit, monkeypatch):
    """Without OAuth credentials the .rss endpoint is used and a 429 is waited out exactly once.

    The 429 sleeps for x-ratelimit-reset and retries once, and the parsed thread separates the post
    from its comments with feed noise stripped.
    """
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    assert reddit.oauth_credentials() is None

    calls = []
    sleeps = []

    class Resp(io.BytesIO):
        headers = {"x-ratelimit-remaining": "0.0"}

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        if len(calls) == 1:
            raise _http_error(429, {"x-ratelimit-reset": "7"})
        return Resp(THREAD_ATOM)

    with (
        mock.patch.object(reddit.urllib.request, "urlopen", fake_urlopen),
        mock.patch.object(reddit.time, "sleep", sleeps.append),
    ):
        post = reddit.atom_thread("test", "abc123", limit=10)

    assert calls[0].startswith("https://www.reddit.com/r/test/comments/abc123/.rss")
    assert len(calls) == 2
    assert sleeps == [8]  # reset + 1s margin, one retry only
    assert post["title"] == "Post title"
    assert post["author"] == "op"
    assert post["body"] == "body text"  # "submitted by … [link] [comments]" footer stripped
    assert [c["author"] for c in post["comments"]] == ["c1"]

    # a second 429 after the retry propagates instead of looping
    with (
        mock.patch.object(reddit.urllib.request, "urlopen", side_effect=_http_error(429, {})) as urlopen,
        mock.patch.object(reddit.time, "sleep", return_value=None),
        pytest.raises(urllib.error.HTTPError),
    ):
        reddit.atom_listing("/r/test/", 1)
    assert urlopen.call_count == 2


def test_oauth_credentials_route_to_oauth_host_and_flatten_nested_comments(reddit, monkeypatch):
    """With REDDIT_CLIENT_ID/SECRET the script talks to oauth.reddit.com with a bearer token.

    It returns nested comments flattened with depth and scores — data the anonymous path cannot provide.
    """
    monkeypatch.setenv("REDDIT_CLIENT_ID", "cid")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "sec")
    assert reddit.oauth_credentials() == ("cid", "sec")

    listing = [
        {
            "data": {
                "children": [
                    {
                        "kind": "t3",
                        "data": {
                            "title": "T",
                            "author": "op",
                            "subreddit": "test",
                            "score": 42,
                            "num_comments": 2,
                            "created_utc": 1.0,
                            "permalink": "/r/test/comments/abc123/t/",
                            "is_self": True,
                            "url": "https://www.reddit.com/r/test/comments/abc123/t/",
                            "selftext": "s",
                        },
                    }
                ]
            }
        },
        {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "author": "a",
                            "score": 5,
                            "body": "top",
                            "permalink": "/p/1",
                            "replies": {
                                "data": {
                                    "children": [
                                        {
                                            "kind": "t1",
                                            "data": {"author": "b", "score": 1, "body": "reply", "replies": ""},
                                        }
                                    ]
                                }
                            },
                        },
                    },
                    {"kind": "more", "data": {}},
                ]
            }
        },
    ]
    seen = {}

    def fake_api(path, token, **params):
        seen["path"], seen["token"] = path, token
        return listing

    with mock.patch.object(reddit, "_api", fake_api):
        post = reddit.api_thread("tok", "test", "abc123", limit=10)

    assert seen == {"path": "/r/test/comments/abc123", "token": "tok"}
    assert post["score"] == 42
    assert post["url"] == "https://www.reddit.com/r/test/comments/abc123/t/"
    assert [(c["author"], c["depth"], c["score"]) for c in post["comments"]] == [("a", 0, 5), ("b", 1, 1)]

    # the bearer header actually reaches the OAuth host
    captured = {}

    def fake_get(url, headers=None, retry_on_429=True):
        captured["url"], captured["headers"] = url, headers
        return b'{"data": {"children": []}}', {}

    with mock.patch.object(reddit, "_get", fake_get):
        reddit.api_listing("tok", "/r/test/hot", 1)
    assert captured["url"].startswith("https://oauth.reddit.com/r/test/hot?")
    assert captured["headers"]["Authorization"] == "Bearer tok"


@pytest.mark.usefixtures("oauth_env")
def test_main_with_oauth_token_reads_thread_through_api(reddit):
    with (
        mock.patch.object(reddit, "oauth_token", return_value="tok"),
        mock.patch.object(reddit, "_api", return_value=API_THREAD) as api,
        mock.patch.object(reddit, "_entries") as entries,
    ):
        assert reddit.main(["thread", THREAD_URL]) == 0

    assert api.call_args.args == ("/r/test/comments/abc123", "tok")
    entries.assert_not_called()


@pytest.mark.usefixtures("oauth_env")
def test_main_with_failing_oauth_token_falls_back_to_atom_feed(reddit, capsys):
    with (
        mock.patch.object(reddit, "oauth_token", side_effect=urllib.error.URLError("down")),
        mock.patch.object(reddit, "_api") as api,
        mock.patch.object(reddit, "_entries", return_value=ATOM_THREAD_ENTRIES) as entries,
    ):
        assert reddit.main(["thread", THREAD_URL]) == 0

    assert entries.call_args.args[0].startswith("https://www.reddit.com/r/test/comments/abc123/.rss")
    api.assert_not_called()
    err = capsys.readouterr().err
    assert "reddit: OAuth token failed" in err
    assert "falling back to anonymous feeds" in err


@pytest.mark.parametrize(
    ("token", "api_error", "expected_backend"),
    [
        pytest.param("tok", None, "oauth", id="oauth-ok"),
        pytest.param("tok", urllib.error.URLError("down"), "oauth (broken)", id="oauth-broken"),
        pytest.param(None, None, "anonymous-atom", id="anonymous-only"),
    ],
)
def test_doctor_backend_state_reports_active_backend(reddit, token, api_error, expected_backend):
    with (
        mock.patch.object(reddit, "_get", return_value=FEED_RESPONSE),
        mock.patch.object(reddit, "_api", side_effect=api_error),
    ):
        report = reddit.cmd_doctor(argparse.Namespace(), token)

    assert report["active_backend"] == expected_backend
    assert report["anonymous_feed"] == "ok"
    assert not [note for note in report["notes"] if ".env" in note]
