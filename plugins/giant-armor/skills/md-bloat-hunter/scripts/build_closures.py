#!/usr/bin/env python3
"""Group Markdown files into context closures for the md-bloat-hunter redundancy pass.

A closure is every file one agent loads into one context: a root plus the
files reachable from it along `reads` edges. Traversal stops at dispatch
targets because an orchestrator reads an agent prompt as data and does not
execute that prompt's own read instructions. Every file is tried as a root; a
closure with no editable member or contained in another closure is dropped.

Input JSON:

    {"editable": ["/abs/SKILL.md"],
     "edges": [{"from": "/abs/SKILL.md", "to": "/abs/references/x.md", "kind": "reads"},
               {"from": "/abs/SKILL.md", "to": "/abs/agents/a.md", "kind": "dispatches"}]}
"""

import argparse
import json
from pathlib import Path
from typing import Any

KINDS = {"reads", "dispatches"}


def resolve(raw: str) -> str:
    """Return the absolute, symlink-free form of a user-supplied path."""
    return str(Path(raw).expanduser().resolve())


def closure(root: str, reads: dict[str, set[str]], boundaries: set[str]) -> frozenset[str]:
    """Return the files `root` loads into one context."""
    seen = {root}
    stack = [root]
    while stack:
        node = stack.pop()
        if node != root and node in boundaries:
            continue
        for target in reads.get(node, ()):
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return frozenset(seen)


def build_closures(editable: set[str], edges: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Return the closures worth one redundancy pass each, sorted by root."""
    reads: dict[str, set[str]] = {}
    boundaries: set[str] = set()
    nodes = set(editable)
    for edge in edges:
        nodes.update((edge["from"], edge["to"]))
        if edge["kind"] == "dispatches":
            boundaries.add(edge["to"])
        else:
            reads.setdefault(edge["from"], set()).add(edge["to"])

    candidates = sorted(
        ((root, closure(root, reads, boundaries)) for root in nodes),
        key=lambda candidate: (-len(candidate[1]), candidate[0]),
    )
    kept: list[tuple[str, frozenset[str]]] = []
    for root, members in candidates:
        if members.isdisjoint(editable):
            continue
        if any(members <= larger for _, larger in kept):
            continue
        kept.append((root, members))

    return [
        {
            "root": root,
            "editable": sorted(members & editable),
            "read_only": sorted(members - editable),
        }
        for root, members in sorted(kept)
    ]


def load_graph(path: Path) -> tuple[set[str], list[dict[str, str]], list[str]]:
    """Read the graph JSON, resolve its paths, and list every problem found."""
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    editable = {resolve(item) for item in payload.get("editable", [])}
    edges = [
        {"from": resolve(edge["from"]), "to": resolve(edge["to"]), "kind": edge["kind"]}
        for edge in payload.get("edges", [])
    ]
    errors = [f"unknown edge kind {edge['kind']!r}" for edge in edges if edge["kind"] not in KINDS]
    nodes = editable | {edge["from"] for edge in edges} | {edge["to"] for edge in edges}
    errors.extend(f"not a file: {node}" for node in sorted(nodes) if not Path(node).is_file())
    if not editable:
        errors.append("editable set is empty")
    return editable, edges, errors


def main() -> int:
    """Print the closures for the graph file as JSON."""
    parser = argparse.ArgumentParser(description="Build context closures for md-bloat-hunter.")
    parser.add_argument("graph", type=Path, help="JSON file with `editable` paths and `edges`")
    args = parser.parse_args()

    editable, edges, errors = load_graph(args.graph)
    if errors:
        print(json.dumps({"closures": [], "errors": errors}, indent=2))
        return 1
    print(json.dumps({"closures": build_closures(editable, edges), "errors": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
