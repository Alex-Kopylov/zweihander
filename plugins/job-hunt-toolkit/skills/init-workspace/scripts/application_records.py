# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0.3,<7"]
# ///
"""Validate application records and preserve text when changing status."""

import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

import yaml

STATUSES = ("drafting", "applied", "screening", "interview", "offer", "signed", "rejected", "withdrew")
TERMINAL = {"signed", "rejected", "withdrew"}
EVENTS = {
    "application_received": ("applied", "application received"),
    "screening_started": ("screening", "screening started"),
    "interview_confirmed": ("interview", "interview confirmed"),
    "offer_received": ("offer", "offer received"),
    "rejected": ("rejected", "application rejected"),
    "withdrew": ("withdrew", "application withdrawn"),
    "accepted": ("signed", "offer accepted or signed"),
}


def normalize(value):
    return " ".join(value.casefold().split())


def atomic_write(path, content, mode=0o600):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Symlink output is not allowed")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_record(path):
    path = Path(path)
    try:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError()
        text = path.read_bytes().decode("utf-8")
        front = re.match(r"\A---\r?\n(.*?)^---[ \t]*\r?$", text, re.S | re.M)
        if front is None:
            raise ValueError()
        node = yaml.compose(front[1], Loader=yaml.SafeLoader)
        if any(isinstance(token, (yaml.AliasToken, yaml.AnchorToken)) for token in yaml.scan(front[1])):
            raise ValueError()
        if not isinstance(node, yaml.MappingNode):
            raise ValueError()
        keys = [key.value for key, _ in node.value]
        if len(keys) != len(set(keys)):
            raise ValueError()
        data = yaml.safe_load(front[1])
        if not {"company", "role", "status", "applied"} <= data.keys():
            raise ValueError()
        for field in ("company", "role"):
            if not isinstance(data[field], str) or not data[field].strip():
                raise ValueError()
        if data["status"] not in STATUSES:
            raise ValueError()
        applied = data["applied"]
        if applied is not None:
            if isinstance(applied, str):
                applied = date.fromisoformat(applied)
            if type(applied) is not date:
                raise ValueError()
        status_node = next(value for key, value in node.value if key.value == "status")
        if not isinstance(status_node, yaml.ScalarNode) or status_node.style in {"|", ">"}:
            raise ValueError()
        return {
            "path": path, "text": text, "company": data["company"], "role": data["role"],
            "status": data["status"], "applied": applied,
            "status_span": (front.start(1) + status_node.start_mark.index,
                            front.start(1) + status_node.end_mark.index),
        }
    except (ValueError, TypeError, KeyError, StopIteration, UnicodeError, yaml.YAMLError) as error:
        raise ValueError(f"Invalid application record: {path}") from error


def load_records(workspace):
    jobs = Path(workspace) / "jobs"
    if jobs.is_symlink():
        raise ValueError("Symlink jobs directory is not allowed")
    return [load_record(path) for path in sorted(jobs.glob("*/company.md"))]


def match_record(records, company, role):
    if not isinstance(company, str) or not isinstance(role, str):
        return None
    matches = [record for record in records
               if normalize(record["company"]) == normalize(company)
               and normalize(record["role"]) == normalize(role)]
    return matches[0] if len(matches) == 1 else None


def sync_index(workspace):
    records = load_records(workspace)
    records.sort(key=lambda r: (r["company"].casefold(), r["company"], r["role"].casefold(), r["role"]))
    lines = ["# Applications", "", "| Company | Role | Status | Applied |", "|---|---|---|---|"]
    for record in records:
        values = [record["company"], record["role"], record["status"], record["applied"]]
        cells = ["null" if value is None else str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("\t", " ") for value in values]
        lines.append("| " + " | ".join(cells) + " |")
    atomic_write(Path(workspace) / "APPLICATIONS.md", ("\n".join(lines) + "\n").encode())


def transition(record, event, event_date):
    """Return updated, unchanged or review; only fixed audit phrases reach disk."""
    previous = record
    record = load_record(record["path"])
    if any(record[key] != previous[key] for key in ("company", "role")):
        raise ValueError("Application identity changed during assessment")
    proposed, summary = EVENTS[event]
    current = record["status"]
    if current == proposed:
        return "unchanged"
    if current in TERMINAL or (proposed not in TERMINAL and STATUSES.index(proposed) < STATUSES.index(current)):
        return "review"
    date.fromisoformat(event_date)
    text = record["text"]
    sections = list(re.finditer(r"^## Status[ \t]*\r?$", text, re.M))
    if len(sections) != 1:
        raise ValueError(f"Invalid status section: {record['path']}")
    following = re.search(r"^## ", text[sections[0].end():], re.M)
    insertion = sections[0].end() + following.start() if following else len(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    entry = f"- **{event_date}**: {summary}{newline}"
    if insertion and not text[:insertion].endswith("\n"):
        entry = newline + entry
    start, end = record["status_span"]
    updated = text[:start] + proposed + text[end:insertion] + entry + text[insertion:]
    if record["path"].read_bytes() != text.encode():
        raise ValueError("Application record changed during update")
    atomic_write(record["path"], updated.encode(), record["path"].stat().st_mode & 0o777)
    return "updated"


if __name__ == "__main__":
    try:
        sync_index(Path(__file__).resolve().parent)
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
