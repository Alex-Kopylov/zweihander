import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"


def load_script(name: str) -> ModuleType:
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def clean_git_repo(tmp_path: Path, target_name: str = "doc.md") -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert run_git(repo, "init").returncode == 0

    target = repo / target_name
    target.write_text("# Title\n\nUse concise prose.\n", encoding="utf-8")
    assert run_git(repo, "add", target_name).returncode == 0
    commit = run_git(
        repo,
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "add doc",
    )
    assert commit.returncode == 0, commit.stderr
    return repo, target


def test_apply_findings_uses_context_to_disambiguate() -> None:
    apply_findings = load_script("apply_findings")
    content = "alpha target omega\nbeta target omega\n"

    matches = apply_findings.accepted_occurrences(content, "target", "beta ", " omega")

    assert matches == [(24, 30)]


def test_apply_findings_rejects_ambiguous_excerpt_without_writing(tmp_path: Path) -> None:
    apply_findings = load_script("apply_findings")
    target = tmp_path / "doc.md"
    original = "repeat repeat\n"
    target.write_text(original, encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(
        target,
        [
            {
                "source_order": 0,
                "excerpt": "repeat",
                "context_before": None,
                "context_after": None,
                "action": "replace",
                "new_text": "single",
            }
        ],
    )

    assert applied == 0
    assert failures[0]["reason"] == "excerpt is ambiguous; add context_before / context_after and re-run"
    assert target.read_text(encoding="utf-8") == original


def test_apply_findings_stops_file_after_first_failure(tmp_path: Path) -> None:
    apply_findings = load_script("apply_findings")
    target = tmp_path / "doc.md"
    target.write_text("first second\n", encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(
        target,
        [
            {
                "source_order": 0,
                "excerpt": "missing",
                "context_before": None,
                "context_after": None,
                "action": "replace",
                "new_text": "x",
            },
            {
                "source_order": 1,
                "excerpt": "second",
                "context_before": None,
                "context_after": None,
                "action": "replace",
                "new_text": "changed",
            },
        ],
    )

    assert applied == 0
    assert failures[0]["reason"] == "excerpt not found verbatim"
    assert target.read_text(encoding="utf-8") == "first second\n"


def test_apply_findings_cli_reports_failures(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("repeat repeat\n", encoding="utf-8")
    approved = write_json(
        tmp_path / "approved.json",
        {
            "findings": [
                {
                    "file_path": str(target),
                    "source_order": 0,
                    "excerpt": "repeat",
                    "context_before": None,
                    "context_after": None,
                    "action": "replace",
                    "new_text": "single",
                }
            ]
        },
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "apply_findings.py"), str(approved)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["applied"] == 0
    assert summary["failed"] == 1


def test_validate_output_invariants_reject_invalid_recommended_indexes() -> None:
    validate_output = load_script("validate_output")

    errors = validate_output.validate_file_reduction_invariants(
        {
            "findings": [
                {"recommended_alternative_index": "0", "alternatives": []},
                {"recommended_alternative_index": 0, "alternatives": "not-list"},
                {"recommended_alternative_index": 1, "alternatives": [{}]},
            ]
        }
    )

    assert errors == [
        "findings[0].recommended_alternative_index must be an integer or null",
        "findings[1].alternatives must be an array",
        "findings[2].recommended_alternative_index=1 is out of range for alternatives length 1",
    ]


def test_validate_output_reports_missing_jsonschema(monkeypatch) -> None:
    validate_output = load_script("validate_output")

    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(validate_output.subprocess, "run", fake_run)

    status = validate_output.run_jsonschema(Path("instance.json"), Path("schema.json"))

    assert status == 127


def test_measure_size_uses_tiktoken_count_when_encoder_is_available(tmp_path: Path) -> None:
    measure_size = load_script("measure_size")
    target = tmp_path / "doc.md"
    target.write_text("alpha beta gamma\n", encoding="utf-8")

    class FakeEncoder:
        def encode(self, text: str) -> list[int]:
            return [1, 2, 3]

    report = measure_size.measure_file(
        target,
        soft_budget_tokens=4,
        hard_budget_tokens=8,
        encoder=FakeEncoder(),
        tokenizer_name="tiktoken:test",
    )

    assert report["tokens"] == 3
    assert report["token_source"] == "tiktoken:test"
    assert report["status"] == "ok"


def test_measure_size_fallback_uses_conservative_char_word_estimate(tmp_path: Path) -> None:
    measure_size = load_script("measure_size")
    target = tmp_path / "doc.md"
    target.write_text(("word " * 900).strip(), encoding="utf-8")

    report = measure_size.measure_file(target, soft_budget_tokens=1000, hard_budget_tokens=2000)

    assert report["tokens"] == 1200
    assert report["token_source"] == "estimate:max(chars/4,words/0.75)"
    assert report["characters"] == 4499
    assert report["words"] == 900
    assert report["status"] == "warning"


def test_measure_size_marks_hard_budget_exceeded(tmp_path: Path) -> None:
    measure_size = load_script("measure_size")
    target = tmp_path / "doc.md"
    target.write_text("x" * 9000, encoding="utf-8")

    report = measure_size.measure_file(target, soft_budget_tokens=1000, hard_budget_tokens=2000)

    assert report["tokens"] == 2250
    assert report["status"] == "over_budget"


def test_size_budget_markdown_delegates_calculation_to_script() -> None:
    markdown_files = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "size-budget-reporter.md",
        SKILL_DIR / "docs" / "SPEC.md",
    ]
    forbidden_calculation_fragments = [
        "ceil(",
        "characters / 4",
        "words / 0.75",
        "1 token ~=",
        "1 token ≈",
        "fallback tokens =",
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in markdown_files)

    assert "@scripts/measure_size.py" in combined
    assert "scripts/measure_size.py" not in combined.replace("@scripts/measure_size.py", "")
    for fragment in forbidden_calculation_fragments:
        assert fragment not in combined


def test_tiktoken_optional_requirement_uses_compatibility_frontmatter() -> None:
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]

    assert "compatibility:" in frontmatter
    assert "Optional `tiktoken`" in frontmatter
    assert "allowed-tools:" not in frontmatter


def test_preflight_validate_target_accepts_clean_tracked_markdown(tmp_path: Path) -> None:
    preflight = load_script("preflight")
    repo, target = clean_git_repo(tmp_path)

    result = preflight.validate_target(target)

    assert result["file_path"] == str(target.resolve())
    assert result["repo_root"] == str(repo.resolve())
    assert result["git_relative_path"] == "doc.md"
    assert result["sha256"] == preflight.sha256(target)


def test_preflight_validate_target_accepts_uppercase_markdown_extension(tmp_path: Path) -> None:
    preflight = load_script("preflight")
    repo, target = clean_git_repo(tmp_path, "doc.MD")

    result = preflight.validate_target(target)

    assert result["file_path"] == str(target.resolve())
    assert result["repo_root"] == str(repo.resolve())
    assert result["git_relative_path"] == "doc.MD"


def test_preflight_rejects_dirty_target(tmp_path: Path) -> None:
    preflight = load_script("preflight")
    _repo, target = clean_git_repo(tmp_path)
    target.write_text("# Title\n\nChanged.\n", encoding="utf-8")

    try:
        preflight.validate_target(target)
    except ValueError as exc:
        assert str(exc) == "target has staged or unstaged changes"
    else:
        raise AssertionError("dirty target was accepted")


def test_preflight_rejects_untracked_target(tmp_path: Path) -> None:
    preflight = load_script("preflight")
    repo, _target = clean_git_repo(tmp_path)
    untracked = repo / "untracked.md"
    untracked.write_text("draft\n", encoding="utf-8")

    try:
        preflight.validate_target(untracked)
    except ValueError as exc:
        assert str(exc) == "target is not tracked by git"
    else:
        raise AssertionError("untracked target was accepted")


def test_preflight_main_rejects_changed_hash_from_expect_map(tmp_path: Path) -> None:
    repo, target = clean_git_repo(tmp_path)
    expect_map = tmp_path / "preflight.json"
    first = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "preflight.py"), str(target)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    expect_map.write_text(first.stdout, encoding="utf-8")

    target.write_text("# Title\n\nChanged.\n", encoding="utf-8")
    run_git(repo, "add", "doc.md")
    commit = run_git(
        repo,
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "change doc",
    )
    assert commit.returncode == 0, commit.stderr

    second = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "preflight.py"), "--expect-map", str(expect_map), str(target)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert second.returncode == 1
    payload = json.loads(second.stdout)
    assert payload["errors"][0]["error"] == "target content hash changed since preflight"
