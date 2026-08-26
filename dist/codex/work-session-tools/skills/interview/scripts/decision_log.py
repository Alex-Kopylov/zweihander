#!/usr/bin/env python3
"""Append-only decision log and progress counter for the interview skill.

Usage:
    decision_log.py start --total 10 --name pr-68-review [--dir DIR]
    decision_log.py record --log LOG --decision "Fix now" --item "#3 HIGH — null check"
    decision_log.py extend --log LOG --by 2
    decision_log.py show --log LOG

`start` prints the log path; every later call takes it back as `--log`. The
log is the interview's only counter: progress is the number of rows already
in the file, so the bar reports what was recorded rather than what anyone
remembers recording.

The default directory is `$INTERVIEW_DECISION_LOG_DIR`, then the system
temporary directory. `SKILL.md` declares the same default under
`metadata.config.decision-log-dir`.
"""

import argparse
import math
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

DIR_ENV = "INTERVIEW_DECISION_LOG_DIR"
DIR_NAME = "interview-decision-logs"
TIMESTAMP = "%Y%m%d-%H%M%S"
SLUG_LIMIT = 40
BAR_WIDTH = 20
FILLED, EMPTY = "▰", "▱"
TABLE_HEADER = "| Item | Decision | Note |\n|------|----------|------|\n"
ROW = re.compile(r"^\|", re.MULTILINE)
TOTAL = re.compile(r"^total: (?P<total>\d+)$", re.MULTILINE)


class LogError(Exception):
    """Raised when the log cannot be read or written as asked."""


def default_dir() -> Path:
    override = os.environ.get(DIR_ENV)
    return Path(override) if override else Path(tempfile.gettempdir()) / DIR_NAME


def slug(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:SLUG_LIMIT]
    if not cleaned:
        raise LogError(f"name {name!r} has no letters or digits to build a file name")
    return cleaned.rstrip("-")


def cell(text: str) -> str:
    """Fit one field into a table cell: single line, no column break."""
    return " ".join(text.split()).replace("|", r"\|")


def bar(done: int, total: int) -> str:
    """Render the queue as one cell per item, scaled past `BAR_WIDTH` items.

    Both ends stay honest under scaling: the first decision fills a cell, and
    a queue with an item left keeps a cell empty however close it rounds.
    """
    cells = min(total, BAR_WIDTH)
    if done >= total:
        filled = cells
    elif done:
        filled = min(math.ceil(done / total * cells), cells - 1)
    else:
        filled = 0
    return f"{FILLED * filled}{EMPTY * (cells - filled)}  {done}/{total}"


def read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise LogError(
            f"cannot read decision log {path}: {error}; `start` creates the log "
            "and prints the path to pass back as --log"
        ) from error


def totals(text: str, path: Path) -> tuple[int, int]:
    """Return the recorded row count and the declared item total."""
    match = TOTAL.search(text)
    if not match:
        raise LogError(f"decision log {path} declares no total")
    recorded = max(len(ROW.findall(text)) - 2, 0)
    return recorded, int(match.group("total"))


def start(args: argparse.Namespace) -> str:
    if args.total < 1:
        raise LogError(f"total {args.total} is not a number of items to walk through")

    directory = Path(args.dir) if args.dir else default_dir()
    directory.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    path = directory / f"{now.strftime(TIMESTAMP)}-{slug(args.name)}.md"
    body = (
        f"---\nname: {slug(args.name)}\n"
        f"started: {now.isoformat(timespec='seconds')}\n"
        f"total: {args.total}\n---\n\n"
        f"# Interview decision log: {args.name}\n\n{TABLE_HEADER}"
    )
    try:
        with path.open("x", encoding="utf-8") as log:
            log.write(body)
    except FileExistsError as error:
        raise LogError(f"decision log {path} already exists") from error

    return f"{path}\n{bar(0, args.total)}"


def record(args: argparse.Namespace) -> str:
    path = Path(args.log)
    text = read_log(path)
    recorded, total = totals(text, path)

    lines = []
    note = f" ({cell(args.note)})" if args.note else ""
    with path.open("a", encoding="utf-8") as log:
        for item in args.item:
            log.write(f"| {cell(item)} | {cell(args.decision)} | {cell(args.note)} |\n")
            lines.append(f"{cell(item)}: **{cell(args.decision)}**{note}")

    return "\n".join([*lines, bar(recorded + len(args.item), total)])


def extend(args: argparse.Namespace) -> str:
    if args.by < 1:
        raise LogError(f"--by {args.by} adds no items to the queue")

    path = Path(args.log)
    text = read_log(path)
    recorded, total = totals(text, path)
    path.write_text(
        TOTAL.sub(f"total: {total + args.by}", text, count=1), encoding="utf-8"
    )
    return bar(recorded, total + args.by)


def show(args: argparse.Namespace) -> str:
    path = Path(args.log)
    text = read_log(path)
    recorded, total = totals(text, path)
    return f"{text.rstrip()}\n\n{bar(recorded, total)}"


def parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    opened = commands.add_parser("start", help="create the log and print its path")
    opened.add_argument("--total", type=int, required=True)
    opened.add_argument("--name", required=True, help="short name for this interview")
    opened.add_argument("--dir", help=f"default: ${DIR_ENV}, then the temp directory")
    opened.set_defaults(run=start)

    appended = commands.add_parser("record", help="append one row per item")
    appended.add_argument("--log", required=True)
    appended.add_argument("--decision", required=True)
    appended.add_argument("--note", default="")
    appended.add_argument(
        "--item",
        required=True,
        action="append",
        help="repeat once per item; several items share one grouped decision",
    )
    appended.set_defaults(run=record)

    grown = commands.add_parser("extend", help="raise the total for new items")
    grown.add_argument("--log", required=True)
    grown.add_argument("--by", type=int, required=True)
    grown.set_defaults(run=extend)

    printed = commands.add_parser("show", help="print the log and the bar")
    printed.add_argument("--log", required=True)
    printed.set_defaults(run=show)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse(argv)
    try:
        print(args.run(args))
    except LogError as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
