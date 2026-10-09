#!/usr/bin/env python3
"""Read RSS / Atom / JSON Feed sources and discover feeds behind a page URL.

Standard library only, so it runs in any Python 3.11+ environment without an install
step. Output is JSON (``--json``) or a compact text listing.

    python3 feed.py read https://example.com/feed.xml [--limit N] [--since 2026-09-01]
    python3 feed.py discover https://example.com/
    python3 feed.py read https://example.com/  ->  discovers, then reads the first feed
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET  # ruff: ignore[suspicious-xml-etree-import] - stdlib-only by design
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

USER_AGENT = "zweihander-rss-feeds/1.0 (+https://github.com/Alex-Kopylov/zweihander)"
TIMEOUT = 20
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "media": "http://search.yahoo.com/mrss/",
}
RSS1 = "{http://purl.org/rss/1.0/}"
FEED_TYPES = ("application/rss+xml", "application/atom+xml", "application/feed+json", "application/json")
COMMON_FEED_PATHS = (
    "/feed",
    "/feed.xml",
    "/rss",
    "/rss.xml",
    "/atom.xml",
    "/index.xml",
    "/feed.json",
    "/blog/feed",
    "/blog/rss.xml",
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def fetch(url: str) -> tuple[bytes, str]:
    """Download a URL over HTTP(S).

    Args:
        url: Absolute ``http`` or ``https`` URL.

    Returns:
        The response body and its ``Content-Type`` header, empty when absent.

    Raises:
        urllib.error.URLError: For any other scheme, so a page cannot point discovery at a local file.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    req = urllib.request.Request(url, headers=headers)  # ruff: ignore[suspicious-url-open-usage] - scheme checked next
    if req.type not in {"http", "https"}:
        msg = f"unknown url type: {req.type}"
        raise urllib.error.URLError(msg)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # ruff: ignore[suspicious-url-open-usage] - http(s) only
        return resp.read(), resp.headers.get("Content-Type", "")


def strip_html(text: str | None) -> str:
    """Drop tags, decode entities, and collapse whitespace.

    Args:
        text: HTML fragment or plain text; ``None`` is treated as empty.

    Returns:
        Single-line plain text.
    """
    if not text:
        return ""
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", text))).strip()


def parse_date(value: str | None) -> str | None:
    """Normalise RFC 822 (RSS) and ISO 8601 (Atom/JSON Feed) dates to UTC ISO.

    Args:
        value: Raw date string from the feed.

    Returns:
        UTC ISO 8601 string, the stripped input when it is in neither format, or ``None`` when empty.
    """
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def _text(el: ET.Element, *paths: str) -> str | None:
    """Return the text of the first path under ``el`` that has non-blank text."""
    for p in paths:
        found = el.find(p, NS)
        if found is not None and (found.text or "").strip():
            return found.text
    return None


def _atom_link(entry: ET.Element) -> str | None:
    """Return the entry's rel=alternate link, else the first link with an href."""
    alternate = None
    for link in entry.findall("atom:link", NS) + entry.findall("link"):
        href = link.get("href")
        if not href:
            continue
        rel = link.get("rel", "alternate")
        if rel == "alternate":
            return href
        alternate = alternate or href
    return alternate


def _atom_entry(entry: ET.Element) -> dict:
    """Normalise one Atom ``<entry>``."""
    return {
        "title": strip_html(_text(entry, "atom:title")),
        "link": _atom_link(entry),
        "published": parse_date(_text(entry, "atom:published", "atom:updated")),
        "author": strip_html(_text(entry, "atom:author/atom:name", "dc:creator")),
        "summary": strip_html(_text(entry, "atom:summary", "atom:content"))[:2000],
    }


def _rss_entry(item: ET.Element) -> dict:
    """Normalise one RSS 2.0 or RSS 1.0 ``<item>``."""
    return {
        "title": strip_html(_text(item, "title", f"{RSS1}title")),
        "link": (_text(item, "link", f"{RSS1}link") or "").strip() or None,
        "published": parse_date(_text(item, "pubDate", "dc:date")),
        "author": strip_html(_text(item, "dc:creator", "author")),
        "summary": strip_html(_text(item, "content:encoded", "description", f"{RSS1}description"))[:2000],
    }


def parse_xml(data: bytes) -> dict:
    """Parse an Atom, RSS 2.0, or RSS 1.0 (RDF) document.

    Args:
        data: Raw XML bytes.

    Returns:
        ``{"format", "title", "entries"}`` with each entry normalised.

    Raises:
        ValueError: An ``<rss>`` root has no ``<channel>``.
    """
    root = ET.fromstring(data)  # ruff: ignore[suspicious-xml-element-tree-usage] - stdlib-only; expat caps entities
    tag = root.tag.rsplit("}", 1)[-1].lower()
    if tag == "feed":  # Atom
        entries = [_atom_entry(e) for e in root.findall("atom:entry", NS)]
        return {"format": "atom", "title": strip_html(_text(root, "atom:title")), "entries": entries}
    channel = root.find("channel") if tag == "rss" else root  # RSS 2.0 vs RDF/RSS 1.0
    if channel is None:
        msg = f"unrecognised XML root <{tag}>"
        raise ValueError(msg)
    items = channel.iter("item") if tag == "rss" else root.iter(f"{RSS1}item")
    entries = [_rss_entry(item) for item in items]
    return {"format": "rss", "title": strip_html(_text(channel, "title", f"{RSS1}title")), "entries": entries}


def _json_entry(item: dict) -> dict:
    """Normalise one JSON Feed item."""
    authors = item.get("authors") or ([item["author"]] if item.get("author") else [])
    summary = item.get("summary") or item.get("content_text") or item.get("content_html")
    return {
        "title": strip_html(item.get("title")),
        "link": item.get("url") or item.get("external_url"),
        "published": parse_date(item.get("date_published") or item.get("date_modified")),
        "author": ", ".join(a.get("name", "") for a in authors if isinstance(a, dict)) or None,
        "summary": strip_html(summary)[:2000],
    }


def parse_json_feed(data: bytes) -> dict:
    """Parse a JSON Feed document.

    Args:
        data: Raw JSON bytes.

    Returns:
        ``{"format", "title", "entries"}`` with each entry normalised.
    """
    doc = json.loads(data)
    entries = [_json_entry(item) for item in doc.get("items", [])]
    return {"format": "jsonfeed", "title": strip_html(doc.get("title")), "entries": entries}


def parse_feed(data: bytes, content_type: str = "") -> dict:
    """Parse a feed as JSON Feed or XML, chosen by its first byte and content type.

    Args:
        data: Raw feed bytes.
        content_type: The response ``Content-Type`` header.

    Returns:
        ``{"format", "title", "entries"}`` with each entry normalised.
    """
    head = data.lstrip()[:1]
    if head == b"{" or "json" in content_type:
        return parse_json_feed(data)
    return parse_xml(data)


def discover(page_url: str, page_html: bytes | None = None) -> list[str]:
    """Return candidate feed URLs for a page: <link rel=alternate> first, then well-known paths.

    Args:
        page_url: The page URL; relative links resolve against it.
        page_html: The page body, fetched from ``page_url`` when omitted.

    Returns:
        The advertised feed URLs, or the well-known feed paths on the page's host when none is advertised.
    """
    if page_html is None:
        page_html, _ = fetch(page_url)
    text = page_html.decode("utf-8", "replace")
    found: list[str] = []
    for m in re.finditer(r"<link\b[^>]*>", text, re.IGNORECASE):
        tag = m.group(0)
        type_m = re.search(r"""type\s*=\s*["']([^"']+)""", tag, re.IGNORECASE)
        href_m = re.search(r"""href\s*=\s*["']([^"']+)""", tag, re.IGNORECASE)
        rel_m = re.search(r"""rel\s*=\s*["']([^"']+)""", tag, re.IGNORECASE)
        if not href_m or not type_m or type_m.group(1).lower() not in FEED_TYPES:
            continue
        if rel_m and "alternate" not in rel_m.group(1).lower():
            continue
        url = urllib.parse.urljoin(page_url, html.unescape(href_m.group(1)))
        if url not in found:
            found.append(url)
    if found:
        return found
    parsed = urllib.parse.urlsplit(page_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return [base + p for p in COMMON_FEED_PATHS]


def looks_like_feed(data: bytes) -> bool:
    """Sniff whether a response body is a feed rather than an HTML page.

    Args:
        data: Raw response bytes.

    Returns:
        True for a JSON object mentioning ``items`` or an ``<rss>``, ``<feed>``, or ``<rdf>`` document.
    """
    head = data.lstrip()[:300].lower()
    return (head.startswith(b"{") and b"items" in data[:2000]) or b"<rss" in head or b"<feed" in head or b"<rdf" in head


def read(url: str) -> dict:
    """Read the feed at ``url``, or discover and read the first feed behind a page URL.

    Args:
        url: A feed URL or an ordinary page URL.

    Returns:
        The parsed feed plus ``url``, and ``discovered_from`` when it came from discovery.

    Raises:
        SystemExit: No candidate served a feed; the message lists every failed fetch.
    """
    data, ctype = fetch(url)
    if looks_like_feed(data):
        feed = parse_feed(data, ctype)
        feed["url"] = url
        return feed
    candidates = discover(url, data)
    errors = []
    for cand in candidates:
        try:
            cdata, cctype = fetch(cand)
        except (urllib.error.URLError, OSError) as exc:
            errors.append(f"{cand}: {exc}")
            continue
        if looks_like_feed(cdata):
            feed = parse_feed(cdata, cctype)
            feed["url"] = cand
            feed["discovered_from"] = url
            return feed
    raise SystemExit(f"no feed found at {url}; tried {len(candidates)} candidates\n" + "\n".join(errors))


def filter_entries(entries: list[dict], limit: int, since: str | None) -> list[dict]:
    """Keep entries published at or after ``since``, newest first, at most ``limit``.

    Args:
        entries: Normalised entries; sorted in place when ``since`` is not given.
        limit: Maximum number of entries to return.
        since: ISO date or datetime; a bare date or naive datetime means UTC. Undated entries are dropped.

    Returns:
        The filtered, sorted, truncated entries.
    """
    if since:
        cutoff = datetime.fromisoformat(since)
        if "T" not in since or cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        entries = [e for e in entries if e["published"] and datetime.fromisoformat(e["published"]) >= cutoff]
    entries.sort(key=lambda e: e["published"] or "", reverse=True)
    return entries[:limit]


def render_text(feed: dict) -> str:
    """Render a feed as a compact text listing.

    Args:
        feed: A feed as returned by ``read``.

    Returns:
        A header line, then one block per entry.
    """
    lines = [f"{feed.get('title') or '(untitled feed)'}  [{feed['format']}]  {feed['url']}"]
    for e in feed["entries"]:
        when = (e["published"] or "")[:10]
        by = f"  — {e['author']}" if e.get("author") else ""
        lines.append(f"- {when}  {e['title'] or '(no title)'}{by}\n  {e['link'] or ''}")
        if e.get("summary"):
            lines.append(f"  {e['summary'][:300]}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``read`` / ``discover`` command-line parser."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read", help="read a feed (or discover one behind a page URL)")
    r.add_argument("url")
    r.add_argument("--limit", type=int, default=20)
    r.add_argument("--since", help="ISO date/datetime; drop older entries")
    r.add_argument("--json", action="store_true")
    d = sub.add_parser("discover", help="list feed URLs advertised by a page")
    d.add_argument("url")
    d.add_argument("--json", action="store_true")
    return ap


def _run(args: argparse.Namespace) -> None:
    """Execute the parsed command and print its result."""
    if args.cmd == "discover":
        urls = discover(args.url)
        print(json.dumps(urls, indent=2) if args.json else "\n".join(urls))
        return
    feed = read(args.url)
    feed["entries"] = filter_entries(feed["entries"], args.limit, args.since)
    print(json.dumps(feed, indent=2, ensure_ascii=False) if args.json else render_text(feed))


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface.

    Args:
        argv: Arguments without the program name; ``sys.argv[1:]`` when omitted.

    Returns:
        0 on success, 2 on a network, HTTP, or parse error.
    """
    args = _build_parser().parse_args(argv)
    try:
        _run(args)
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} for {exc.url}", file=sys.stderr)
        return 2
    except (urllib.error.URLError, ET.ParseError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
