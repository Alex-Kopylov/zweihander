#!/usr/bin/env python3
"""Look up one action/assistant entry from harness-action-matrix.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_MATRIX = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "harness-action-matrix.json"
)


def load_entry(matrix_path: Path, action: str, assistant: str) -> dict[str, Any]:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    try:
        action_entry = matrix["actions"][action]
        assistant_entry = action_entry[assistant]
    except KeyError as exc:
        available_actions = ", ".join(sorted(matrix.get("actions", {})))
        available_assistants = ", ".join(sorted(matrix.get("assistants", {})))
        raise SystemExit(
            f"Unknown lookup {action!r}/{assistant!r}. "
            f"Actions: {available_actions}. Assistants: {available_assistants}."
        ) from exc

    return {
        "action": action,
        "assistant": assistant,
        "kind": action_entry["kind"],
        "intent": action_entry["intent"],
        **assistant_entry,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--action", required=True)
    parser.add_argument("--assistant", required=True)
    args = parser.parse_args()

    print(
        json.dumps(
            load_entry(args.matrix, args.action, args.assistant),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
