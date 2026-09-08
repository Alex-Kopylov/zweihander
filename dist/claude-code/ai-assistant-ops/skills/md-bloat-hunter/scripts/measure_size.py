#!/usr/bin/env python3
import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_SOFT_BUDGET_TOKENS = 4096
DEFAULT_HARD_BUDGET_TOKENS = 8192
DEFAULT_MODEL = "gpt-4o"
FALLBACK_TOKEN_SOURCE = "estimate:max(chars/4,words/0.75)"
WORD_RE = re.compile(r"\S+")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def estimate_tokens(characters: int, words: int) -> int:
    by_chars = math.ceil(characters / 4)
    by_words = math.ceil(words / 0.75)
    return max(by_chars, by_words)


def budget_status(tokens: int, soft_budget_tokens: int, hard_budget_tokens: int) -> str:
    if tokens > hard_budget_tokens:
        return "over_budget"
    if tokens > soft_budget_tokens:
        return "warning"
    return "ok"


def warning_for_status(tokens: int, soft_budget_tokens: int, hard_budget_tokens: int, status: str) -> str | None:
    if status == "over_budget":
        return f"File is {tokens} tokens, above hard budget {hard_budget_tokens}."
    if status == "warning":
        return f"File is {tokens} tokens, above soft budget {soft_budget_tokens}."
    return None


def load_tiktoken_encoder(model: str) -> tuple[Any | None, str | None]:
    try:
        import tiktoken  # type: ignore[import-not-found]
    except Exception:
        return None, None

    try:
        return tiktoken.encoding_for_model(model), f"tiktoken:{model}"
    except Exception:
        pass

    for encoding_name in ("o200k_base", "cl100k_base"):
        try:
            return tiktoken.get_encoding(encoding_name), f"tiktoken:{encoding_name}"
        except Exception:
            continue

    return None, None


def measure_file(
    path: Path,
    *,
    soft_budget_tokens: int = DEFAULT_SOFT_BUDGET_TOKENS,
    hard_budget_tokens: int = DEFAULT_HARD_BUDGET_TOKENS,
    encoder: Any | None = None,
    tokenizer_name: str | None = None,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    encoded_bytes = text.encode("utf-8")
    characters = len(text)
    words = count_words(text)

    if encoder is not None:
        tokens = len(encoder.encode(text))
        token_source = tokenizer_name or "tiktoken"
    else:
        tokens = estimate_tokens(characters, words)
        token_source = FALLBACK_TOKEN_SOURCE

    status = budget_status(tokens, soft_budget_tokens, hard_budget_tokens)

    return {
        "file_path": str(path.resolve()),
        "bytes": len(encoded_bytes),
        "characters": characters,
        "words": words,
        "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
        "tokens": tokens,
        "token_source": token_source,
        "soft_budget_tokens": soft_budget_tokens,
        "hard_budget_tokens": hard_budget_tokens,
        "status": status,
        "warning": warning_for_status(tokens, soft_budget_tokens, hard_budget_tokens, status),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure Markdown size for md-bloat-hunter.")
    parser.add_argument("path", type=Path, help="Markdown file to measure")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="tiktoken model name")
    parser.add_argument(
        "--soft-budget-tokens",
        type=int,
        default=DEFAULT_SOFT_BUDGET_TOKENS,
        help="Warning threshold, in tokens",
    )
    parser.add_argument(
        "--hard-budget-tokens",
        type=int,
        default=DEFAULT_HARD_BUDGET_TOKENS,
        help="Over-budget threshold, in tokens",
    )
    parser.add_argument(
        "--no-tiktoken",
        action="store_true",
        help="Skip optional tiktoken and use the deterministic fallback estimate",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.soft_budget_tokens <= 0 or args.hard_budget_tokens <= 0:
        print("token budgets must be positive integers", file=sys.stderr)
        return 2
    if args.hard_budget_tokens <= args.soft_budget_tokens:
        print("hard budget must be greater than soft budget", file=sys.stderr)
        return 2

    encoder = None
    tokenizer_name = None
    if not args.no_tiktoken:
        encoder, tokenizer_name = load_tiktoken_encoder(args.model)

    report = measure_file(
        args.path,
        soft_budget_tokens=args.soft_budget_tokens,
        hard_budget_tokens=args.hard_budget_tokens,
        encoder=encoder,
        tokenizer_name=tokenizer_name,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
