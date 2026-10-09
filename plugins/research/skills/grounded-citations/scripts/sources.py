#!/usr/bin/env python3
"""Citation ledger for grounded answers and documents.

Owns the ``url -> [n]`` mapping used by the ``grounded-citations`` skill.
Ids are assigned at retrieval time and never change, so a draft's ``[3]``
always resolves to the same page.  The model only ever emits integers the
ledger handed it, which is what makes the citations verifiable.

Subcommands
-----------
  reset                            start a clean ledger
  add URL [URL ...]                register source(s), print their ids
  ingest FILE|-                    register every url found in JSON tool output
  quote ID --text T --from FILE|-  attach verbatim supporting evidence to a source
  list                             show the ledger
  render                           render a Sources block
  verify DRAFT                     check a draft's citations against the ledger

Fact-checking is evidence-backed citation: ``quote`` only accepts text that
literally appears in the fetched page text you point it at, ``verify
--evidence`` requires every cited source to carry at least one such quote, and
``render --style evidence`` prints the quotes under each source so the reader
can check the chain themselves.  Claims from model knowledge are declared with
an ``[unverified]`` marker rather than silently blended in.

Ledger path resolution (first wins):
  --ledger PATH
  $CITATION_LEDGER
  ${ZWEIHANDER_TMP_DIR:-./.tmp/zweihander}/runs/grounded-citations/ledger.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

SCHEMA_VERSION = 1

# A shorter quote is too generic to pin a claim to one page.
_MIN_QUOTE_WORDS = 3
# Shorter fragments (labels, list stubs) are not counted as prose sentences.
_MIN_SENTENCE_WORDS = 4
# A sentence leaning on more sources than this is flagged as over-cited.
_MAX_SENTENCE_CITATIONS = 3

# A citation marker in prose: [12].  Markdown links ([text](url)) and
# reference-style labels are excluded by requiring digits only and no
# following "(" or ":".
_CITE_RE = re.compile(r"\[(\d{1,4})\](?![(:])")
_SOURCES_HEADER_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?sources:?(?:\*\*)?\s*$", re.IGNORECASE)
# The separator after "[n]" may be a hyphen, an en dash (U+2013) or a colon.
_SOURCE_LINE_RE = re.compile(r"^\s*\[(\d{1,4})\]\s*[-\u2013:]?\s*(\S+)")
_URL_IN_TEXT_RE = re.compile(r"https?://[^\s\"'<>)\]}]+")
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
# Explicit declaration that a claim comes from model knowledge, not a source.
_UNVERIFIED_RE = re.compile(r"\[unverified\]", re.IGNORECASE)


class LedgerError(SystemExit):
    """A ledger or evidence failure; exits non-zero with the message on stderr."""

    UNREADABLE = "error: ledger at {path} is unreadable ({exc}); run `reset` to start over"
    BAD_SHAPE = "error: ledger at {path} has an unexpected shape; run `reset`"
    QUOTE_TOO_SHORT = f"error: quote too short — use at least {_MIN_QUOTE_WORDS} words of verbatim text"
    QUOTE_NOT_VERBATIM = (
        "error: quote not found verbatim in the evidence text — "
        "copy the exact wording from the fetched page, do not paraphrase"
    )
    UNKNOWN_SOURCE = "error: no source [{source_id}] in the ledger"

    def __init__(self, template: str, **fields: object) -> None:
        """Format ``template`` with ``fields`` into the exit message."""
        super().__init__(template.format(**fields))


# ---------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------


def resolve_ledger_path(explicit: str | None = None) -> Path:
    """Resolve the ledger file from the flag, the environment, or the default.

    Args:
        explicit: The ``--ledger`` value; wins when non-empty.

    Returns:
        ``explicit``, else ``$CITATION_LEDGER``, else
        ``${ZWEIHANDER_TMP_DIR:-./.tmp/zweihander}/runs/grounded-citations/ledger.json``.
        Blank environment values count as unset.
    """
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("CITATION_LEDGER", "").strip()
    if env:
        return Path(env).expanduser()
    tmp_root = os.environ.get("ZWEIHANDER_TMP_DIR", "").strip() or "./.tmp/zweihander"
    return Path(tmp_root).expanduser() / "runs" / "grounded-citations" / "ledger.json"


def normalize_url(url: str) -> str:
    """Canonicalize a URL for ledger identity.

    Strips the fragment and a trailing slash so ``/page``, ``/page/`` and
    ``/page#section`` are one source.  Query strings are significant and are
    kept — they usually select different content.
    """
    u = (url or "").strip()
    if "#" in u:
        u = u.split("#", 1)[0]
    stripped = u.rstrip("/")
    return stripped or u


def load_ledger(path: Path) -> dict[str, Any]:
    """Read the ledger at ``path``, or return an empty one when the file is absent.

    Raises:
        LedgerError: The file is not readable JSON or has no ``sources`` list.
    """
    if not path.exists():
        return {"version": SCHEMA_VERSION, "sources": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise LedgerError(LedgerError.UNREADABLE, path=path, exc=exc) from exc
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise LedgerError(LedgerError.BAD_SHAPE, path=path)
    return data


def save_ledger(path: Path, data: dict[str, Any]) -> None:
    """Write ``data`` to ``path`` atomically through a pid-suffixed temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


class _LedgerLock:
    """Best-effort cross-process lock (O_EXCL lockfile, stdlib only).

    Parallel subagents can share one ledger via --ledger; without a lock two
    concurrent ``add`` calls can assign the same id.  Falls through after the
    timeout rather than blocking a task forever — a stale lock must never
    wedge the ledger.
    """

    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self) -> _LedgerLock:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    # Assume a stale lock from a crashed run.
                    try:
                        self.lock_path.unlink()
                    except OSError:
                        return self
                    continue
                time.sleep(0.05)
            else:
                return self

    def __exit__(self, *_exc: object) -> None:
        if self.fd is not None:
            with contextlib.suppress(OSError):
                os.close(self.fd)
        with contextlib.suppress(OSError):
            self.lock_path.unlink()


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def _by_url(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {s["url"]: s for s in sources}


def add_sources(
    path: Path,
    urls: Iterable[str],
    title: str | None = None,
    accessed: str | None = None,
) -> list[dict[str, Any]]:
    """Register urls, returning their ledger entries (existing or new)."""
    urls = [u for u in (str(u).strip() for u in urls) if u]
    if not urls:
        return []
    with _LedgerLock(path):
        data = load_ledger(path)
        sources = data["sources"]
        index = _by_url(sources)
        out: list[dict[str, Any]] = []
        changed = False
        for raw in urls:
            key = normalize_url(raw)
            existing = index.get(key)
            if existing is not None:
                if title and not existing.get("title"):
                    existing["title"] = title
                    changed = True
                out.append(existing)
                continue
            entry = {
                "id": len(sources) + 1,
                "url": key,
                "title": (title or "").strip(),
                "accessed": accessed or time.strftime("%Y-%m-%d"),
            }
            sources.append(entry)
            index[key] = entry
            out.append(entry)
            changed = True
        if changed:
            save_ledger(path, data)
    return out


def urls_from_json(payload: Any) -> list[tuple[str, str]]:
    """Walk arbitrary JSON tool output collecting (url, title) pairs.

    Handles web_search (``data.web[]``), web_extract (``results[]``) and any
    other nesting, in document order, deduped.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            url = node.get("url") or node.get("link") or node.get("source_url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                key = normalize_url(url)
                if key not in seen:
                    seen.add(key)
                    raw_title = node.get("title") or node.get("name") or ""
                    found.append((url, raw_title if isinstance(raw_title, str) else ""))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


# ---------------------------------------------------------------------------
# Evidence quotes (fact-checking)
# ---------------------------------------------------------------------------


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace runs to single spaces for verbatim matching."""
    return " ".join((text or "").split())


# Markdown artifacts that retrieval tools inject into otherwise-identical prose.
# ``web_extract`` returns markdown, so the most citation-worthy sentences are
# exactly the ones carrying inline links and emphasis around terms: a gene list
# arrives as _[ERAP1](https://…/erap1/)_ yet reads identically to the page a
# human sees.  Matching has to see through that markup, or the skill pushes the
# agent toward weaker evidence fragments.
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((?:[^()\s]|\([^()]*\))*\)")
_MD_NOISE_RE = re.compile(r"[*_`~]|\\(?=[^\w\s])")


def _match_key(text: str) -> str:
    """Canonicalize text for verbatim comparison.

    Whitespace-, case-, and markdown-insensitive: inline links collapse to
    their label, emphasis/code markers and backslash escapes are dropped.  The
    stored quote keeps whatever the caller passed, so the rendered evidence
    block shows clean prose rather than extractor artifacts.
    """
    collapsed = _MD_LINK_RE.sub(r"\1", text or "")
    return _normalize_ws(_MD_NOISE_RE.sub("", collapsed)).casefold()


def quote_in_evidence(quote: str, evidence: str) -> bool:
    """Return whether ``quote`` appears verbatim in the fetched ``evidence`` text.

    Whitespace, case, and markdown markup are ignored on either side.
    """
    q = _match_key(quote)
    return bool(q) and q in _match_key(evidence)


def attach_quote(path: Path, source_id: int, quote: str, evidence: str) -> dict[str, Any]:
    """Attach a verbatim quote to a ledger entry after checking it against the evidence.

    A quote the page does not contain is exactly the fabrication this guards
    against, so it is rejected before the ledger is touched.

    Args:
        path: Ledger file.
        source_id: Ledger id of the source the quote supports.
        quote: The exact wording, copied from the page.
        evidence: The fetched page text the quote must appear in.

    Returns:
        The ledger entry, carrying the quote.

    Raises:
        LedgerError: The quote is too short or not verbatim, or ``source_id`` is unknown.
    """
    quote = (quote or "").strip()
    if len(_normalize_ws(quote).split()) < _MIN_QUOTE_WORDS:
        raise LedgerError(LedgerError.QUOTE_TOO_SHORT)
    if not quote_in_evidence(quote, evidence):
        raise LedgerError(LedgerError.QUOTE_NOT_VERBATIM)
    with _LedgerLock(path):
        data = load_ledger(path)
        entry = next((s for s in data["sources"] if s["id"] == source_id), None)
        if entry is None:
            raise LedgerError(LedgerError.UNKNOWN_SOURCE, source_id=source_id)
        quotes = entry.setdefault("quotes", [])
        norm = _match_key(quote)
        if not any(_match_key(q.get("text", "")) == norm for q in quotes):
            quotes.append({"text": quote, "added": time.strftime("%Y-%m-%d")})
            save_ledger(path, data)
    return entry


def render_sources(
    sources: list[dict[str, Any]],
    style: str = "markdown",
    only: set[int] | None = None,
) -> str:
    """Render a Sources block for ledger entries.

    Args:
        sources: Ledger entries.
        style: One of ``markdown``, ``plain``, ``footnotes``, ``bibtex`` or ``evidence``.
        only: Ids to include; ``None`` includes every entry.

    Returns:
        The block ordered by id, or ``""`` when nothing is selected.
    """
    picked = [s for s in sources if only is None or s["id"] in only]
    picked.sort(key=itemgetter("id"))
    if not picked:
        return ""
    lines: list[str] = []
    if style == "bibtex":
        for s in picked:
            title = s.get("title") or s["url"]
            lines.append(
                f"@misc{{source{s['id']},\n"
                f"  title = {{{title}}},\n"
                f"  howpublished = {{\\url{{{s['url']}}}}},\n"
                f"  note = {{Accessed {s.get('accessed', '')}}}\n"
                "}"
            )
        return "\n".join(lines)
    if style == "footnotes":
        for s in picked:
            title = s.get("title")
            suffix = f" — {title}" if title else ""
            lines.append(f"[^{s['id']}]: {s['url']}{suffix}")
        return "\n".join(lines)
    header = "Sources:" if style == "plain" else "## Sources"
    lines.append(header)
    if style != "plain":
        lines.append("")
    for s in picked:
        title = s.get("title")
        suffix = f" — {title}" if title else ""
        lines.append(f"[{s['id']}] {s['url']}{suffix}")
        if style == "evidence":
            lines.extend(f'    > "{q.get("text", "")}"' for q in s.get("quotes", []))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def _split_draft(text: str) -> tuple[str, dict[int, str]]:
    """Split a draft into (prose, sources_block_map).

    The sources block is everything after the last ``Sources`` header; its
    ``[n] url`` lines are parsed out so they aren't counted as prose citations.
    Fenced code blocks are dropped from prose.
    """
    lines = text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if _SOURCES_HEADER_RE.match(line):
            header_idx = i
    listed: dict[int, str] = {}
    if header_idx >= 0:
        for line in lines[header_idx + 1 :]:
            m = _SOURCE_LINE_RE.match(line)
            if m:
                url_match = _URL_IN_TEXT_RE.search(line)
                listed[int(m.group(1))] = url_match.group(0) if url_match else m.group(2)
        body_lines = lines[:header_idx]
    else:
        body_lines = lines
    prose: list[str] = []
    in_fence = False
    for line in body_lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            prose.append(line)
    return "\n".join(prose), listed


def _strip_sources_block(text: str) -> str:
    """Return the draft with its trailing Sources block removed.

    Everything from the last Sources header onward goes; a draft with no such
    header is returned unchanged.  This is what makes ``render --replace-in``
    idempotent instead of stacking duplicate blocks.
    """
    lines = text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if _SOURCES_HEADER_RE.match(line):
            header_idx = i
    if header_idx < 0:
        return text
    return "\n".join(lines[:header_idx])


def _sentences(prose: str) -> list[str]:
    """Rough sentence split over prose lines, skipping headings and tables."""
    out: list[str] = []
    for line in prose.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|")):
            continue
        if stripped.startswith(">"):
            stripped = stripped.lstrip("> ").strip()
        for part in re.split(r"(?<=[.!?])\s+", stripped):
            sentence = part.strip()
            if len(sentence.split()) >= _MIN_SENTENCE_WORDS:
                out.append(sentence)
    return out


def _cited_ids(prose: str) -> set[int]:
    return {int(m) for m in _CITE_RE.findall(prose)}


def _id_list(ids: Iterable[int]) -> str:
    return ", ".join(f"[{i}]" for i in ids)


def _citation_errors(cited: set[int], listed: dict[int, str], by_id: dict[int, dict[str, Any]]) -> list[str]:
    """Return the errors from inline citations and the Sources block disagreeing with the ledger."""
    errors: list[str] = []
    unknown = sorted(i for i in cited if i not in by_id)
    if unknown:
        errors.append("citations not in the ledger (hallucinated or renumbered): " + _id_list(unknown))
    if cited and not listed:
        errors.append("draft cites sources but has no `Sources:` block — run `render --cited-in`")
    missing_from_block = sorted(cited - set(listed)) if listed else []
    if missing_from_block:
        errors.append("cited but absent from the Sources block: " + _id_list(missing_from_block))
    for sid, url in sorted(listed.items()):
        entry = by_id.get(sid)
        if entry is None:
            errors.append(f"Sources block lists [{sid}], which is not in the ledger")
            continue
        if normalize_url(url) != entry["url"]:
            errors.append(
                f"Sources block URL for [{sid}] does not match the ledger "
                f"(block: {url} / ledger: {entry['url']}) — re-run `render`"
            )
    return errors


def _citation_warnings(cited: set[int], listed: dict[int, str], by_id: dict[int, dict[str, Any]]) -> list[str]:
    """Return the warnings for sources that are listed or registered but never cited."""
    warnings: list[str] = []
    extra_in_block = sorted(set(listed) - cited)
    if extra_in_block:
        warnings.append("listed in Sources but never cited inline: " + _id_list(extra_in_block))
    registered_uncited = sorted(set(by_id) - cited)
    if registered_uncited:
        warnings.append("registered in the ledger but not cited in this draft: " + _id_list(registered_uncited))
    return warnings


def _stats_line(sentences: list[str], covered: list[str], cited: set[int], sources: list[dict[str, Any]]) -> str:
    """Summarize provenance coverage of the draft and evidence held by the ledger."""
    cited_sentences = [s for s in sentences if _CITE_RE.search(s)]
    unverified_sentences = [s for s in sentences if _UNVERIFIED_RE.search(s)]
    coverage = (len(covered) / len(sentences)) if sentences else 0.0
    quoted = sum(1 for s in sources if s.get("quotes"))
    ledger_size = len({s["id"] for s in sources})
    return (
        f"stats: {len(sentences)} prose sentence(s), {len(covered)} with declared provenance "
        f"({coverage:.0%}) — {len(cited_sentences)} cited, "
        f"{len(unverified_sentences)} marked [unverified] (a sentence may be both); "
        f"{len(cited)} distinct source(s) cited, "
        f"{ledger_size} in ledger ({quoted} with evidence quotes)"
    )


def verify_draft(
    draft_path: Path,
    sources: list[dict[str, Any]],
    strict: bool = False,
    min_coverage: float | None = None,
    require_evidence: bool = False,
) -> tuple[int, list[str], list[str]]:
    """Check a draft's citations against the ledger.

    Args:
        draft_path: Draft file to check.
        sources: Ledger entries.
        strict: Fail on warnings too.
        min_coverage: Required share of prose sentences that are cited or marked ``[unverified]``.
        require_evidence: Require every cited source to carry a verbatim evidence quote.

    Returns:
        ``(exit_code, errors, warnings)``; the first warning is always the ``stats:`` line.
    """
    prose, listed = _split_draft(draft_path.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in sources}
    cited = _cited_ids(prose)
    errors = _citation_errors(cited, listed, by_id)
    warnings = _citation_warnings(cited, listed, by_id)

    sentences = _sentences(prose)
    covered = [s for s in sentences if _CITE_RE.search(s) or _UNVERIFIED_RE.search(s)]
    coverage = (len(covered) / len(sentences)) if sentences else 0.0
    if min_coverage is not None and sentences and coverage < min_coverage:
        errors.append(
            f"citation coverage {coverage:.0%} is below the required {min_coverage:.0%} "
            f"({len(covered)}/{len(sentences)} sentences cited or marked [unverified])"
        )

    if require_evidence:
        unevidenced = sorted(i for i in cited if i in by_id and not by_id[i].get("quotes"))
        if unevidenced:
            errors.append(
                "cited sources carry no verbatim evidence quote (run `quote` with the "
                "fetched page text): " + _id_list(unevidenced)
            )

    over_cited = [s for s in sentences if len(_CITE_RE.findall(s)) > _MAX_SENTENCE_CITATIONS]
    if over_cited:
        warnings.append(f"{len(over_cited)} sentence(s) carry more than {_MAX_SENTENCE_CITATIONS} citations")

    code = 1 if errors else (1 if (strict and warnings) else 0)
    warnings.insert(0, _stats_line(sentences, covered, cited, sources))
    return code, errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_only(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for chunk in spec.replace(" ", "").split(","):
        if not chunk:
            continue
        if "-" in chunk:
            lo, _, hi = chunk.partition("-")
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(chunk))
    return out


def _read_input(spec: str) -> str:
    """Read a file, or stdin when ``spec`` is ``-``."""
    return sys.stdin.read() if spec == "-" else Path(spec).read_text(encoding="utf-8")


def _sorted_sources(path: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = load_ledger(path)["sources"]
    return sorted(sources, key=itemgetter("id"))


def _cmd_reset(_args: argparse.Namespace, path: Path) -> int:
    with _LedgerLock(path):
        save_ledger(path, {"version": SCHEMA_VERSION, "sources": []})
    print(f"ledger reset: {path}")
    return 0


def _cmd_add(args: argparse.Namespace, path: Path) -> int:
    title = args.title if len(args.urls) == 1 else None
    entries = add_sources(path, args.urls, title=title, accessed=args.accessed)
    if args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=False))
    else:
        for e in entries:
            print(f"[{e['id']}] {e['url']}")
    return 0


def _cmd_ingest(args: argparse.Namespace, path: Path) -> int:
    raw = _read_input(args.file)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: input is not valid JSON ({exc})", file=sys.stderr)
        return 2
    pairs = urls_from_json(payload)
    if not pairs:
        print("no urls found in input", file=sys.stderr)
        return 1
    for url, title in pairs:
        entry = add_sources(path, [url], title=title or None)[0]
        print(f"[{entry['id']}] {entry['url']}")
    return 0


def _cmd_quote(args: argparse.Namespace, path: Path) -> int:
    entry = attach_quote(path, args.id, args.text, _read_input(args.evidence))
    print(f"[{entry['id']}] evidence attached ({len(entry.get('quotes', []))} quote(s))")
    return 0


def _cmd_list(args: argparse.Namespace, path: Path) -> int:
    sources = _sorted_sources(path)
    if args.json:
        print(json.dumps(sources, indent=2, ensure_ascii=False))
    elif not sources:
        print(f"ledger is empty: {path}")
    else:
        for s in sources:
            title = f"  {s['title']}" if s.get("title") else ""
            nq = len(s.get("quotes", []))
            mark = f"  ({nq} quote{'s' if nq != 1 else ''})" if nq else ""
            print(f"[{s['id']}] {s['url']}{title}{mark}")
    return 0


def _cmd_render(args: argparse.Namespace, path: Path) -> int:
    sources = _sorted_sources(path)
    only = _parse_only(args.only)
    draft_for_ids = args.replace_in or args.cited_in
    if draft_for_ids:
        prose, _ = _split_draft(Path(draft_for_ids).read_text(encoding="utf-8"))
        cited = _cited_ids(prose)
        only = cited if only is None else (only & cited)
    block = render_sources(sources, style=args.style, only=only)
    if not block:
        print("no sources to render", file=sys.stderr)
        return 1
    if args.replace_in:
        target = Path(args.replace_in)
        body = _strip_sources_block(target.read_text(encoding="utf-8"))
        target.write_text(body.rstrip("\n") + "\n\n" + block + "\n", encoding="utf-8")
        print(f"Sources block rewritten in {target}")
        return 0
    print(block)
    return 0


def _cmd_verify(args: argparse.Namespace, path: Path) -> int:
    sources = _sorted_sources(path)
    draft_path = Path(args.draft)
    if not draft_path.is_file():
        print(f"error: no such draft: {draft_path}", file=sys.stderr)
        return 2
    code, errors, warnings = verify_draft(
        draft_path,
        sources,
        strict=args.strict,
        min_coverage=args.min_coverage,
        require_evidence=args.evidence,
    )
    for w in warnings:
        prefix = "info" if w.startswith("stats: ") else "warn"
        print(f"{prefix}: {w}")
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    print("citations OK" if code == 0 else "verification failed")
    return code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sources.py", description="Citation ledger for grounded answers and documents."
    )
    parser.add_argument("--ledger", help="ledger file path (overrides env / default)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("reset", help="start a clean ledger").set_defaults(handler=_cmd_reset)

    p_add = sub.add_parser("add", help="register source url(s), print their ids")
    p_add.add_argument("urls", nargs="+")
    p_add.add_argument("--title", help="title for the source (single-url calls)")
    p_add.add_argument("--accessed", help="access date (default: today)")
    p_add.add_argument("--json", action="store_true", help="emit JSON instead of ids")
    p_add.set_defaults(handler=_cmd_add)

    p_ing = sub.add_parser("ingest", help="register every url in JSON tool output")
    p_ing.add_argument("file", help="JSON file, or - for stdin")
    p_ing.set_defaults(handler=_cmd_ingest)

    p_q = sub.add_parser("quote", help="attach verbatim supporting evidence to a source")
    p_q.add_argument("id", type=int, help="ledger id of the source the quote supports")
    p_q.add_argument("--text", required=True, help="the exact quote, copied from the page")
    p_q.add_argument(
        "--from",
        dest="evidence",
        required=True,
        help="file with the fetched page text (or - for stdin) the quote must appear in",
    )
    p_q.set_defaults(handler=_cmd_quote)

    p_list = sub.add_parser("list", help="show the ledger")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(handler=_cmd_list)

    p_render = sub.add_parser("render", help="render a Sources block")
    p_render.add_argument(
        "--style", default="markdown", choices=["markdown", "plain", "footnotes", "bibtex", "evidence"]
    )
    p_render.add_argument("--only", help="ids to include, e.g. 1,3,5-7")
    p_render.add_argument("--cited-in", help="include only ids cited in this draft file")
    p_render.add_argument(
        "--replace-in",
        help="rewrite this draft's Sources block in place (implies --cited-in on it)",
    )
    p_render.set_defaults(handler=_cmd_render)

    p_ver = sub.add_parser("verify", help="check a draft's citations against the ledger")
    p_ver.add_argument("draft")
    p_ver.add_argument("--strict", action="store_true", help="treat warnings as failures")
    p_ver.add_argument("--min-coverage", type=float, help="required cited-sentence share, e.g. 0.5")
    p_ver.add_argument(
        "--evidence",
        action="store_true",
        help="require every cited source to carry at least one verbatim quote",
    )
    p_ver.set_defaults(handler=_cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ledger CLI.

    Args:
        argv: Arguments without the program name; ``None`` reads ``sys.argv``.

    Returns:
        The exit code: 0 on success, 1 on a failed check or an empty result, 2 on unusable input.
    """
    args = _build_parser().parse_args(argv)
    return args.handler(args, resolve_ledger_path(args.ledger))


if __name__ == "__main__":
    sys.exit(main())
