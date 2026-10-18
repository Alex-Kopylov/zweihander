#!/usr/bin/env python3
"""Look up one key/assistant entry from harness-frontmatter-matrix.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_MATRIX = Path(__file__).resolve().parents[1] / "references" / "harness-frontmatter-matrix.json"
VERBATIM_FORM = "verbatim"


class UnknownLookupError(SystemExit):
    """The key or assistant is not in the matrix; exits naming what is."""

    def __init__(self, key: str, assistant: str, matrix: dict[str, Any]) -> None:
        """Build the exit message from the matrix's available names."""
        available_keys = ", ".join(sorted(matrix.get("keys", {})))
        available_assistants = ", ".join(sorted(matrix.get("assistants", {})))
        super().__init__(
            f"Unknown lookup {key!r}/{assistant!r}. Keys: {available_keys}. Assistants: {available_assistants}."
        )


def load_entry(matrix_path: Path, key: str, assistant: str) -> dict[str, Any]:
    """Return the matrix entry for one frontmatter key and assistant, with its declaration."""
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    try:
        key_entry = matrix["keys"][key]
        assistant_entry = key_entry[assistant]
    except KeyError as exc:
        raise UnknownLookupError(key, assistant, matrix) from exc

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
    """Print the requested entry as JSON."""
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
