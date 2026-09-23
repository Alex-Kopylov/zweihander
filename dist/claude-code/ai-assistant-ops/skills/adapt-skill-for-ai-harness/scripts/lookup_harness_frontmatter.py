#!/usr/bin/env python3
"""Look up one key/assistant entry from harness-frontmatter-matrix.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_MATRIX = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "harness-frontmatter-matrix.json"
)
VERBATIM_FORM = "verbatim"


def load_entry(matrix_path: Path, key: str, assistant: str) -> dict[str, Any]:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    try:
        key_entry = matrix["keys"][key]
        assistant_entry = key_entry[assistant]
    except KeyError as exc:
        available_keys = ", ".join(sorted(matrix.get("keys", {})))
        available_assistants = ", ".join(sorted(matrix.get("assistants", {})))
        raise SystemExit(
            f"Unknown lookup {key!r}/{assistant!r}. "
            f"Keys: {available_keys}. Assistants: {available_assistants}."
        ) from exc

    form = key_entry["form"]
    entry = {
        "key": key,
        "assistant": assistant,
        "form": form,
        "form_rule": matrix["forms"][form],
        "intent": key_entry["intent"],
        **assistant_entry,
    }
    entry["declaration"] = (
        f"write `{key}:` literally in frontmatter"
        if form == VERBATIM_FORM
        else f"{{{{ {key.replace('-', '_')}(...) }}}}"
    )
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--key", required=True)
    parser.add_argument("--assistant", required=True)
    args = parser.parse_args()

    print(
        json.dumps(
            load_entry(args.matrix, args.key, args.assistant),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
