"""The tests-manager output contracts, validated in the tree a user installs."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMAS = ("scenarios", "ledger", "handoff")
EVIDENCE = (
    "non_test_callers",
    "remaining_proof",
    "history",
    "unlocks",
    "risk",
    "validation_command",
)


@pytest.fixture
def schemas_dir(rendered: Path) -> Path:
    return rendered / "python-dev-workflow" / "skills" / "tests-manager" / "references" / "schemas"


def validator(schemas_dir: Path, name: str) -> Draft202012Validator:
    schema = json.loads((schemas_dir / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def scenarios() -> dict:
    return {
        "scenarios": [
            {
                "id": "S1",
                "requirement": "A used reset link is rejected.",
                "actor_preconditions": "A registered user who already used the link.",
                "action": "Open the reset link again.",
                "expected": "The link is rejected and the password is unchanged.",
                "corner_cases": [
                    {
                        "id": "S1.1",
                        "description": "The link expires between two clicks.",
                        "expected": "Rejected as expired.",
                    }
                ],
            }
        ],
        "gaps": ["Is an expired link distinguishable from a used one?"],
    }


def entry(**overrides: object) -> dict:
    payload = {
        "test_id": "tests/unit/billing/test_invoice.py::test_total_empty_returns_zero",
        "mark": "D",
        "contract": "An empty invoice totals zero.",
        "detects": "A regression in the empty-invoice branch.",
        "junk_patterns": ["duplicate-contract"],
        "non_test_callers": ["billing.api.create_invoice"],
        "remaining_proof": "tests/unit/billing/test_invoice.py::test_total_parametrized[empty]",
        "history": "Added with the invoice module; the parametrized table came later.",
        "unlocks": [],
        "risk": "low",
        "validation_command": "uv run pytest tests/unit/billing/test_invoice.py",
    }
    payload.update(overrides)
    return payload


def ledger(mode: str, *entries: dict) -> dict:
    return {"lane": "billing", "mode": mode, "entries": list(entries), "gaps": []}


def handoff() -> dict:
    return {
        "scope": "tests/unit/billing",
        "lanes": [{"name": "billing", "owners": ["billing"], "test_files": ["tests/unit/billing/test_invoice.py"]}],
        "baseline": {"junit_xml": "baseline.xml", "passed": 12, "failed": 0, "failing_tests": []},
        "removed_categories": ["duplicate-contract"],
        "owner_simplifications": [],
        "retained_false_positives": [],
        "mutation_results": [
            {"target": "billing.invoice.total", "killed": 9, "survived": 0, "explained_survivors": []}
        ],
        "proof_runs": [{"command": "uv run pytest tests/unit/billing", "result": "12 passed"}],
        "loc": {"production": {"added": 0, "removed": 4}, "tests": {"added": 0, "removed": 30}},
        "ledger_files": ["ledgers/billing.json"],
        "follow_ups": [],
        "proposed_ownership_rules": [],
    }


@pytest.mark.parametrize("name", SCHEMAS)
def test_schema_passes_its_metaschema(schemas_dir: Path, name: str) -> None:
    schema = json.loads((schemas_dir / f"{name}.schema.json").read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    ("name", "instance"),
    [
        ("scenarios", scenarios()),
        ("ledger", ledger("audit", entry())),
        ("ledger", ledger("review", entry(mark="R", junk_patterns=[]))),
        ("handoff", handoff()),
    ],
)
def test_schema_accepts_minimal_valid_instance(schemas_dir: Path, name: str, instance: dict) -> None:
    errors = list(validator(schemas_dir, name).iter_errors(instance))

    assert errors == []


@pytest.mark.parametrize("field", EVIDENCE)
def test_audit_delete_without_evidence_fails(schemas_dir: Path, field: str) -> None:
    incomplete = entry()
    del incomplete[field]

    assert not validator(schemas_dir, "ledger").is_valid(ledger("audit", incomplete))


def test_review_delete_needs_no_audit_evidence(schemas_dir: Path) -> None:
    light = {key: value for key, value in entry().items() if key not in EVIDENCE}

    assert validator(schemas_dir, "ledger").is_valid(ledger("review", light))


@pytest.mark.parametrize("mode", ["review", "audit"])
def test_consolidate_without_absorbed_by_fails(schemas_dir: Path, mode: str) -> None:
    consolidate = entry(mark="C")

    assert not validator(schemas_dir, "ledger").is_valid(ledger(mode, consolidate))


@pytest.mark.parametrize("mode", ["review", "audit"])
def test_repair_without_repair_fails(schemas_dir: Path, mode: str) -> None:
    repair = entry(mark="F")

    assert not validator(schemas_dir, "ledger").is_valid(ledger(mode, repair))


def test_unknown_junk_pattern_fails(schemas_dir: Path) -> None:
    unknown = entry(junk_patterns=["looks-odd"])

    assert not validator(schemas_dir, "ledger").is_valid(ledger("audit", unknown))
