import json
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DETECTOR_SCHEMA = SKILL_DIR / "references" / "detector-output.schema.json"
FILE_REDUCTION_SCHEMA = SKILL_DIR / "references" / "file-reduction.schema.json"
SIZE_REPORT_SCHEMA = SKILL_DIR / "references" / "size-report.schema.json"


def run_jsonschema(instance: Path, schema: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jsonschema", "-i", str(instance), str(schema)],
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def detector_output(**overrides: object) -> dict:
    payload = {
        "specialist": "verbosity-pruner",
        "file_path": "/tmp/example.md",
        "audit_calibration": {
            "observation": "short markdown file",
            "chosen_intensity": "standard",
            "reasoning": "normal cleanup pass",
        },
        "findings": [
            {
                "excerpt": "in order to",
                "context_before": None,
                "context_after": None,
                "type": "verbosity",
                "rationale": "The phrase can be shortened without changing meaning.",
                "severity": "major",
                "action": "replace",
                "new_text": "to",
                "justification": None,
                "semantic_risk": "none",
                "confidence": "high",
            }
        ],
    }
    payload.update(overrides)
    return payload


def detector_status() -> list[dict]:
    return [
        {
            "specialist": name,
            "status": "included",
            "output_path": f"/tmp/private-run/example/{name}.json",
            "findings_included": 0,
            "notes": "ok",
        }
        for name in [
            "redundancy-detector",
            "verbosity-pruner",
            "filler-eliminator",
            "vocab-compressor",
        ]
    ]


def file_reduction(**finding_overrides: object) -> dict:
    finding = {
        "resolution": "single",
        "recommendation": "apply",
        "source_specialists": ["verbosity-pruner"],
        "source_order": 12,
        "recommended_alternative_index": None,
        "excerpt": "in order to",
        "context_before": None,
        "context_after": None,
        "type": "verbosity",
        "rationale": "The phrase can be shortened.",
        "severity": "major",
        "action": "replace",
        "new_text": "to",
        "justification": None,
        "semantic_risk": "none",
        "confidence": "high",
        "alternatives": [],
        "resolution_notes": "single finding",
    }
    finding.update(finding_overrides)
    return {
        "file_path": "/tmp/example.md",
        "detector_status": detector_status(),
        "findings": [finding],
    }


def size_report(**overrides: object) -> dict:
    payload = {
        "file_path": "/tmp/example.md",
        "bytes": 256,
        "characters": 240,
        "words": 60,
        "lines": 12,
        "tokens": 80,
        "token_source": "estimate:max(chars/4,words/0.75)",
        "soft_budget_tokens": 4096,
        "hard_budget_tokens": 8192,
        "status": "ok",
        "warning": None,
    }
    payload.update(overrides)
    return payload


def test_detector_output_schema_accepts_valid_output(tmp_path: Path) -> None:
    payload = write_json(tmp_path / "detector.json", detector_output())

    result = run_jsonschema(payload, DETECTOR_SCHEMA)

    assert result.returncode == 0, result.stderr


def test_detector_output_schema_rejects_wrong_specialist_type(tmp_path: Path) -> None:
    bad = detector_output(specialist="filler-eliminator")
    bad["findings"][0]["type"] = "verbosity"
    bad["findings"][0]["action"] = "replace"
    payload = write_json(tmp_path / "bad-detector.json", bad)

    result = run_jsonschema(payload, DETECTOR_SCHEMA)

    assert result.returncode != 0


def test_file_reduction_schema_accepts_valid_reduction(tmp_path: Path) -> None:
    payload = write_json(tmp_path / "file-reduction.json", file_reduction())

    result = run_jsonschema(payload, FILE_REDUCTION_SCHEMA)

    assert result.returncode == 0, result.stderr


def test_file_reduction_schema_accepts_directory_redundancy_reduction(tmp_path: Path) -> None:
    payload = file_reduction(
        source_specialists=["directory-redundancy-detector"],
        type="redundancy",
        rationale="The same instruction appears in an invoked agent prompt.",
        action="delete",
        new_text=None,
    )
    payload["detector_status"] = [
        {
            "specialist": "directory-redundancy-detector",
            "status": "included",
            "output_path": "/tmp/private-run/directory-redundancy.json",
            "findings_included": 1,
            "notes": "ok",
        }
    ]
    path = write_json(tmp_path / "directory-reduction.json", payload)

    result = run_jsonschema(path, FILE_REDUCTION_SCHEMA)

    assert result.returncode == 0, result.stderr


def test_file_reduction_schema_rejects_duplicate_detector_status(tmp_path: Path) -> None:
    payload = file_reduction()
    payload["detector_status"][1]["specialist"] = "redundancy-detector"
    path = write_json(tmp_path / "duplicate-status.json", payload)

    result = run_jsonschema(path, FILE_REDUCTION_SCHEMA)

    assert result.returncode != 0


def test_validate_output_script_rejects_out_of_range_recommended_index(tmp_path: Path) -> None:
    payload = file_reduction(
        resolution="alternatives",
        recommendation="apply-recommended",
        recommended_alternative_index=1,
        alternatives=[
            {
                "source_specialist": "verbosity-pruner",
                "source_index": 0,
                "source_order": 12,
                "excerpt": "in order to",
                "context_before": None,
                "context_after": None,
                "type": "verbosity",
                "rationale": "The phrase can be shortened.",
                "severity": "major",
                "action": "replace",
                "new_text": "to",
                "justification": None,
                "semantic_risk": "none",
                "confidence": "high",
            }
        ],
    )
    path = write_json(tmp_path / "bad-index.json", payload)

    result = subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "validate_output.py"),
            "file-reduction",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "recommended_alternative_index" in result.stderr


def test_size_report_schema_accepts_valid_report(tmp_path: Path) -> None:
    payload = write_json(tmp_path / "size-report.json", size_report())

    result = run_jsonschema(payload, SIZE_REPORT_SCHEMA)

    assert result.returncode == 0, result.stderr


def test_size_report_schema_rejects_invalid_budget_status(tmp_path: Path) -> None:
    payload = write_json(tmp_path / "bad-size-report.json", size_report(status="critical"))

    result = run_jsonschema(payload, SIZE_REPORT_SCHEMA)

    assert result.returncode != 0


def test_apply_findings_script_applies_exact_single_match(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("Use in order to keep the example clear.\n", encoding="utf-8")
    approved = write_json(
        tmp_path / "approved.json",
        {
            "findings": [
                {
                    "file_path": str(target),
                    "source_order": 0,
                    "excerpt": "in order to",
                    "context_before": None,
                    "context_after": None,
                    "action": "replace",
                    "new_text": "to",
                }
            ]
        },
    )

    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "apply_findings.py"), str(approved)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == "Use to keep the example clear.\n"
