#!/usr/bin/env python3
"""Apply approved md-bloat-hunter findings to Markdown files by exact string matching."""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Jinja's default delimiters, as whole blocks or unpaired markers, so a block cut in half still counts.
JINJA_SYNTAX = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}|\{\{|\}\}|\{%|%\}|\{#|#\}", re.DOTALL)


class InputError(ValueError):
    """The approved-findings file does not hold the expected JSON."""

    NOT_ARRAY = "findings must be an array"

    @classmethod
    def invalid_json(cls, path: Path, exc: json.JSONDecodeError) -> "InputError":
        """Name the file and the parser error."""
        return cls(f"{path}: invalid JSON: {exc}")


class FindingError(ValueError):
    """A finding that cannot be applied; the message is the reported reason."""

    EMPTY_EXCERPT = "excerpt must be non-empty"
    NOT_FOUND = "excerpt not found verbatim"
    SHIFTED = "excerpt changed by an earlier applied finding; re-run to pick up shifted findings"
    AMBIGUOUS = "excerpt is ambiguous; add context_before / context_after and re-run"
    DELETE_WITH_TEXT = "delete findings must use new_text: null"
    TOUCHES_JINJA = "edit touches Jinja syntax; Jinja blocks in a template are not editable"

    @classmethod
    def text_not_string(cls, action: str) -> "FindingError":
        """Name the action whose new_text must be a string."""
        return cls(f"{action} findings must use string new_text")

    @classmethod
    def unsupported_action(cls, action: object) -> "FindingError":
        """Name the action this script does not apply."""
        return cls(f"unsupported action: {action!r}")


def load_json(path: Path) -> Any:
    """Parse a JSON file, naming the file on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError.invalid_json(path, exc) from exc


def accepted_occurrences(
    content: str,
    excerpt: str,
    context_before: str | None,
    context_after: str | None,
) -> list[tuple[int, int]]:
    """Return the (start, end) spans of `excerpt` whose surroundings match the given context."""
    if not excerpt:
        raise FindingError(FindingError.EMPTY_EXCERPT)

    occurrences: list[tuple[int, int]] = []
    start = 0
    while True:
        index = content.find(excerpt, start)
        if index == -1:
            break
        end = index + len(excerpt)
        before_ok = context_before is None or content[:index].endswith(context_before)
        after_ok = context_after is None or content[end:].startswith(context_after)
        if before_ok and after_ok:
            occurrences.append((index, end))
        start = index + 1
    return occurrences


def replacement_for(finding: dict[str, Any]) -> str:
    """Return the text that replaces the finding's excerpt."""
    action = finding.get("action")
    new_text = finding.get("new_text")

    if action == "delete":
        if new_text is not None:
            raise FindingError(FindingError.DELETE_WITH_TEXT)
        return ""
    if action in {"replace", "restructure"}:
        if not isinstance(new_text, str):
            raise FindingError.text_not_string(action)
        return new_text
    raise FindingError.unsupported_action(action)


def locate(content: str, original: str, finding: dict[str, Any]) -> tuple[int, int]:
    """Return the one span the finding applies to in the current content."""
    excerpt = finding["excerpt"]
    matches = accepted_occurrences(content, excerpt, finding.get("context_before"), finding.get("context_after"))
    if not matches:
        raise FindingError(FindingError.SHIFTED if excerpt in original else FindingError.NOT_FOUND)
    if len(matches) > 1:
        raise FindingError(FindingError.AMBIGUOUS)
    return matches[0]


def touches_jinja(content: str, start: int, end: int, updated: str) -> bool:
    """Return whether the edit of content[start:end] overlaps Jinja syntax or changes the template's Jinja syntax."""
    tokens = list(JINJA_SYNTAX.finditer(content))
    overlaps = any(match.start() < end and start < match.end() for match in tokens)
    return overlaps or [match.group() for match in tokens] != JINJA_SYNTAX.findall(updated)


def edited(content: str, original: str, finding: dict[str, Any], *, template: bool) -> str:
    """Return the content with the finding applied, refusing a template edit that touches Jinja."""
    start, end = locate(content, original, finding)
    updated = content[:start] + replacement_for(finding) + content[end:]
    if template and touches_jinja(content, start, end, updated):
        raise FindingError(FindingError.TOUCHES_JINJA)
    return updated


def apply_file_findings(file_path: Path, findings: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    """Apply one file's findings in source order, stopping at the first failure."""
    content = file_path.read_text(encoding="utf-8")
    original = content
    applied = 0
    failures: list[dict[str, Any]] = []
    is_template = file_path.suffix.lower() == ".j2"

    for finding in sorted(findings, key=lambda item: int(item.get("source_order", 0))):
        try:
            content = edited(content, original, finding, template=is_template)
            # write_text truncates before it encodes; fail first, or an
            # unencodable replacement leaves the file empty.
            content.encode("utf-8")
            file_path.write_text(content, encoding="utf-8")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            failures.append(
                {
                    "file_path": str(file_path),
                    "source_order": finding.get("source_order"),
                    "excerpt": finding.get("excerpt"),
                    "reason": str(exc),
                }
            )
            break
        applied += 1

    return applied, failures


def load_findings(path: Path) -> list[Any]:
    """Return the `findings` array of an approved-findings file."""
    findings = load_json(path)["findings"]
    if not isinstance(findings, list):
        raise InputError(InputError.NOT_ARRAY)
    return findings


def main() -> int:
    """Apply every approved finding and print a JSON summary."""
    parser = argparse.ArgumentParser(description="Apply approved md-bloat-hunter findings with exact string matching.")
    parser.add_argument(
        "approved_findings",
        type=Path,
        help='JSON object shaped like {"findings": [{"file_path": "...", "excerpt": "...", ...}]}',
    )
    args = parser.parse_args()

    try:
        findings = load_findings(args.approved_findings)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    by_file: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        if not isinstance(finding, dict):
            print("each finding must be an object", file=sys.stderr)
            return 1
        try:
            by_file[Path(str(finding["file_path"]))].append(finding)
        except KeyError:
            print("each finding must include file_path", file=sys.stderr)
            return 1

    total_applied = 0
    all_failures: list[dict[str, Any]] = []
    for file_path, file_findings in sorted(by_file.items(), key=lambda item: str(item[0])):
        applied, failures = apply_file_findings(file_path, file_findings)
        total_applied += applied
        all_failures.extend(failures)

    summary = {"applied": total_applied, "failed": len(all_failures), "failures": all_failures}
    print(json.dumps(summary, indent=2))
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
