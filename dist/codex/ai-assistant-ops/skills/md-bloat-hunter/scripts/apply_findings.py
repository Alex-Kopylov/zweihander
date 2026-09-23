#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def accepted_occurrences(
    content: str,
    excerpt: str,
    context_before: str | None,
    context_after: str | None,
) -> list[tuple[int, int]]:
    if not excerpt:
        raise ValueError("excerpt must be non-empty")

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
    action = finding.get("action")
    new_text = finding.get("new_text")

    if action == "delete":
        if new_text is not None:
            raise ValueError("delete findings must use new_text: null")
        return ""
    if action in {"replace", "restructure"}:
        if not isinstance(new_text, str):
            raise ValueError(f"{action} findings must use string new_text")
        return new_text
    raise ValueError(f"unsupported action: {action!r}")


def apply_file_findings(file_path: Path, findings: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    content = file_path.read_text(encoding="utf-8")
    original = content
    applied = 0
    failures: list[dict[str, Any]] = []

    for finding in sorted(findings, key=lambda item: int(item.get("source_order", 0))):
        try:
            excerpt = finding["excerpt"]
            matches = accepted_occurrences(
                content,
                excerpt,
                finding.get("context_before"),
                finding.get("context_after"),
            )
            if not matches:
                reason = (
                    "excerpt changed by an earlier applied finding; re-run to pick up shifted findings"
                    if excerpt in original
                    else "excerpt not found verbatim"
                )
                raise ValueError(reason)
            if len(matches) > 1:
                raise ValueError("excerpt is ambiguous; add context_before / context_after and re-run")

            start, end = matches[0]
            content = content[:start] + replacement_for(finding) + content[end:]
            file_path.write_text(content, encoding="utf-8")
            applied += 1
        except Exception as exc:
            failures.append(
                {
                    "file_path": str(file_path),
                    "source_order": finding.get("source_order"),
                    "excerpt": finding.get("excerpt"),
                    "reason": str(exc),
                }
            )
            break

    return applied, failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply approved md-bloat-hunter findings with exact string matching."
    )
    parser.add_argument(
        "approved_findings",
        type=Path,
        help='JSON object shaped like {"findings": [{"file_path": "...", "excerpt": "...", ...}]}',
    )
    args = parser.parse_args()

    try:
        payload = load_json(args.approved_findings)
        findings = payload["findings"]
        if not isinstance(findings, list):
            raise ValueError("findings must be an array")
    except Exception as exc:
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
