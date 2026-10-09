"""The rss-feeds script's parsing and discovery contracts, loaded from the tree a user installs."""

import importlib.util
import json
import urllib.error
from email.message import Message
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
def feed(rendered: Path) -> ModuleType:
    return load_script(rendered / "web" / "skills" / "rss-feeds" / "scripts" / "feed.py")


RSS = b"""<?xml version="1.0"?><rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>Blog &amp; Notes</title>
<item><title>Older</title><link>https://ex.com/a</link><pubDate>Mon, 01 Sep 2026 10:00:00 GMT</pubDate>
  <dc:creator>Ann</dc:creator><description>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;</description></item>
<item><title>Newer</title><link>https://ex.com/b</link><pubDate>Thu, 04 Sep 2026 08:30:00 +0200</pubDate></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Atom Site</title>
<entry><title>Entry</title><link rel="self" href="https://ex.com/self"/><link rel="alternate" href="https://ex.com/post"/>
<updated>2026-09-03T12:00:00Z</updated><author><name>Bob</name></author><content type="html">&lt;p&gt;Body&lt;/p&gt;</content></entry>
</feed>"""

JSONFEED = b'{"version":"https://jsonfeed.org/version/1.1","title":"JF","items":[{"id":"1","url":"https://ex.com/j","title":"J1","date_published":"2026-09-02T00:00:00Z","authors":[{"name":"Cy"}],"content_text":"txt"}]}'

RDF = b"""<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel><title>RDF Site</title></channel>
<item><title>First</title><link> https://ex.com/1 </link><dc:date>2026-09-02T10:00:00+02:00</dc:date>
  <description>&lt;i&gt;one&lt;/i&gt;</description></item>
<item><title>Second</title><link>https://ex.com/2</link></item>
</rdf:RDF>"""

PAGE = b"""<html><head><title>x</title>
<link rel="alternate" type="application/atom+xml" href="/atom/everything/">
<link rel="stylesheet" href="/s.css"></head><body></body></html>"""


def test_all_three_formats_normalise_to_the_same_entry_shape_and_utc_dates(feed):
    """RSS (RFC 822), Atom (ISO), and JSON Feed (ISO) parse to identical keys with UTC-normalised dates.

    Atom picks the rel=alternate link over rel=self.
    """
    rss, atom, jf = feed.parse_feed(RSS), feed.parse_feed(ATOM), feed.parse_feed(JSONFEED, "application/feed+json")
    keys = {"title", "link", "published", "author", "summary"}
    for f in (rss, atom, jf):
        assert f["entries"]
        assert all(set(e) == keys for e in f["entries"])
    assert rss["title"] == "Blog & Notes"
    assert rss["entries"][0]["summary"] == "Hello world"  # HTML stripped, entities decoded
    assert rss["entries"][1]["published"] == "2026-09-04T06:30:00+00:00"  # +0200 → UTC
    assert atom["entries"][0]["link"] == "https://ex.com/post"
    assert jf["entries"][0]["author"] == "Cy"
    newest = feed.filter_entries(rss["entries"], limit=1, since="2026-09-02")
    assert [e["title"] for e in newest] == ["Newer"]


def test_page_url_discovers_advertised_feed_then_reads_it(feed):
    """A non-feed page falls through to <link rel=alternate> discovery, resolved against the page URL.

    `read` returns the parsed feed tagged with where it was discovered from.
    """
    responses = {
        "https://ex.com/blog/": (PAGE, "text/html"),
        "https://ex.com/atom/everything/": (ATOM, "application/atom+xml"),
    }
    with mock.patch.object(feed, "fetch", side_effect=lambda u: responses[u]):
        assert feed.discover("https://ex.com/blog/") == ["https://ex.com/atom/everything/"]
        result = feed.read("https://ex.com/blog/")
    assert result["url"] == "https://ex.com/atom/everything/"
    assert result["discovered_from"] == "https://ex.com/blog/"
    assert result["entries"][0]["title"] == "Entry"
    # no advertised feed → well-known paths are proposed, never an empty list
    with mock.patch.object(feed, "fetch", return_value=(b"<html><body>plain</body></html>", "text/html")):
        candidates = feed.discover("https://plain.example/")
    assert candidates
    assert all(c.startswith("https://plain.example/") for c in candidates)


def test_rdf_feed_with_items_beside_channel_parses_every_item(feed):
    """RSS 1.0 keeps <item> outside <channel> in the RSS 1.0 namespace; links are trimmed, dates go to UTC."""
    result = feed.parse_feed(RDF)
    assert result["format"] == "rss"
    first, second = result["entries"]
    assert first == {
        "title": "First",
        "link": "https://ex.com/1",
        "published": "2026-09-02T08:00:00+00:00",
        "author": "",
        "summary": "one",
    }
    assert (second["title"], second["published"]) == ("Second", None)


@pytest.mark.parametrize(
    ("since", "expected_titles"),
    [
        pytest.param("2026-09-01", ["Newer", "Older"], id="bare-date-is-utc-midnight-newest-first"),
        pytest.param("2026-09-02", ["Newer"], id="bare-date-drops-older"),
        pytest.param("2026-09-04T06:30:00Z", ["Newer"], id="z-suffix-cutoff-is-inclusive"),
        pytest.param("2026-09-04T08:30:00+02:00", ["Newer"], id="offset-cutoff-compares-in-utc"),
        pytest.param("2026-09-04T06:30:01", [], id="naive-datetime-is-utc"),
    ],
)
def test_since_cutoff_keeps_dated_entries_at_or_after_it(feed, since, expected_titles):
    """`--since` keeps entries published at or after the cutoff, newest first, and drops undated entries."""
    undated = {"title": "Undated", "link": None, "published": None, "author": "", "summary": ""}
    entries = [*feed.parse_feed(RSS)["entries"], undated]
    assert [e["title"] for e in feed.filter_entries(entries, limit=20, since=since)] == expected_titles


def test_page_without_any_feed_exits_listing_every_failed_candidate(feed):
    """When neither the page nor any well-known path serves a feed, `read` exits with each fetch error listed."""

    def fetch(url):
        if url == "https://plain.example/":
            return b"<html><body>plain</body></html>", "text/html"
        if url == "https://plain.example/feed":
            return b"<html>not a feed</html>", "text/html"
        raise urllib.error.URLError("refused")

    with mock.patch.object(feed, "fetch", side_effect=fetch), pytest.raises(SystemExit) as exc_info:
        feed.read("https://plain.example/")
    message = str(exc_info.value.code)
    assert message.startswith(
        f"no feed found at https://plain.example/; tried {len(feed.COMMON_FEED_PATHS)} candidates"
    )
    assert "https://plain.example/rss.xml: <urlopen error refused>" in message
    assert "https://plain.example/feed:" not in message  # fetched fine, just not a feed


@pytest.mark.parametrize("url", ["http://ex.com/feed", "https://ex.com/feed", "HTTPS://ex.com/feed"])
def test_http_url_is_fetched_with_the_skill_user_agent(feed, url):
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = b"<rss/>"
    response.__enter__.return_value.headers = {"Content-Type": "application/rss+xml"}
    with mock.patch.object(feed.urllib.request, "urlopen", return_value=response) as urlopen:
        assert feed.fetch(url) == (b"<rss/>", "application/rss+xml")
    request = urlopen.call_args.args[0]
    assert request.get_header("User-agent") == "zweihander-rss-feeds/1.0 (+https://github.com/Alex-Kopylov/zweihander)"


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://ex.com/feed.xml", "data:text/plain,<rss/>"])
def test_non_http_url_raises_url_error_without_opening_it(feed, url):
    """A page can advertise any href as its feed; only http(s) is ever opened."""
    with (
        mock.patch.object(feed.urllib.request, "urlopen") as urlopen,
        pytest.raises(urllib.error.URLError, match="unknown url type"),
    ):
        feed.fetch(url)
    urlopen.assert_not_called()


def test_cli_read_json_applies_limit_and_since_and_exits_0(feed, capsys):
    with mock.patch.object(feed, "fetch", return_value=(RSS, "application/rss+xml")):
        code = feed.main(["read", "https://ex.com/feed", "--json", "--limit", "5", "--since", "2026-09-02"])
    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["url"] == "https://ex.com/feed"
    assert [e["title"] for e in output["entries"]] == ["Newer"]


def test_cli_http_error_prints_status_to_stderr_and_exits_2(feed, capsys):
    error = urllib.error.HTTPError("https://ex.com/feed", 404, "Not Found", Message(), None)
    with mock.patch.object(feed, "fetch", side_effect=error):
        code = feed.main(["read", "https://ex.com/feed"])
    assert code == 2
    assert capsys.readouterr().err == "HTTP 404 for https://ex.com/feed\n"
