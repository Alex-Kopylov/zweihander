#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "detector": SKILL_DIR / "references" / "detector-output.schema.json",
    "file-reduction": SKILL_DIR / "references" / "file-reduction.schema.json",
    "size-report": SKILL_DIR / "references" / "size-report.schema.json",
}


def run_jsonschema(instance: Path, schema: Path) -> int:
    try:
        result = subprocess.run(
            ["jsonschema", "-i", str(instance), str(schema)],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        print("jsonschema CLI not found; install with: uv tool install jsonschema", file=sys.stderr)
        return 127

    if result.returncode != 0:
        sys.stderr.write(result.stderr)
    return result.returncode


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def validate_file_reduction_invariants(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["file-reduction output must be a JSON object"]

    for index, finding in enumerate(payload.get("findings", [])):
        if not isinstance(finding, dict):
            errors.append(f"findings[{index}] must be an object")
            continue

        recommended = finding.get("recommended_alternative_index")
        alternatives = finding.get("alternatives", [])
        if recommended is not None:
            if not isinstance(recommended, int):
                errors.append(f"findings[{index}].recommended_alternative_index must be an integer or null")
            elif not isinstance(alternatives, list):
                errors.append(f"findings[{index}].alternatives must be an array")
            elif recommended >= len(alternatives):
                errors.append(
                    f"findings[{index}].recommended_alternative_index={recommended} "
                    f"is out of range for alternatives length {len(alternatives)}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate md-bloat-hunter JSON outputs.")
    parser.add_argument("kind", choices=sorted(SCHEMAS), help="Output contract to validate")
    parser.add_argument("path", type=Path, help="JSON output path")
    args = parser.parse_args()

    schema = SCHEMAS[args.kind]
    status = run_jsonschema(args.path, schema)
    if status != 0:
        return status

    if args.kind == "file-reduction":
        try:
            payload = load_json(args.path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        errors = validate_file_reduction_invariants(payload)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1

    print("validation: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
