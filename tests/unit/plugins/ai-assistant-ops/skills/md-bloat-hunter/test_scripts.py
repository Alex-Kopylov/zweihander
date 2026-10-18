"""The md-bloat-hunter scripts, loaded from the tree a user installs."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from plugin_maintenance.render import TEMPLATE_SUFFIX


@pytest.fixture
def skill_dir(rendered: Path) -> Path:
    return rendered / "ai-assistant-ops" / "skills" / "md-bloat-hunter"


@pytest.fixture
def scripts_dir(skill_dir: Path) -> Path:
    return skill_dir / "scripts"


def load_script(scripts_dir: Path, name: str) -> ModuleType:
    path = scripts_dir / f"{name}.py"
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


def test_apply_findings_uses_context_to_disambiguate(scripts_dir: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
    content = "alpha target omega\nbeta target omega\n"

    matches = apply_findings.accepted_occurrences(content, "target", "beta ", " omega")

    assert matches == [(24, 30)]


def test_apply_findings_rejects_ambiguous_excerpt_without_writing(scripts_dir: Path, tmp_path: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
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


def test_apply_findings_reports_unencodable_text_without_emptying_the_file(scripts_dir: Path, tmp_path: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
    target = tmp_path / "doc.md"
    target.write_text("old words\n", encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(
        target,
        [
            {
                "source_order": 0,
                "excerpt": "old",
                "context_before": None,
                "context_after": None,
                "action": "replace",
                "new_text": "lone \ud800 surrogate",
            }
        ],
    )

    assert applied == 0
    assert "surrogates not allowed" in failures[0]["reason"]
    assert target.read_text(encoding="utf-8") == "old words\n"


def test_apply_findings_stops_file_after_first_failure(scripts_dir: Path, tmp_path: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
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


def test_apply_findings_cli_reports_failures(scripts_dir: Path, tmp_path: Path) -> None:
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
        [sys.executable, str(scripts_dir / "apply_findings.py"), str(approved)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["applied"] == 0
    assert summary["failed"] == 1


TEMPLATE = 'Ask with {{ actions.AskUser | call }} now.\n{% if harness == "Codex" %}\nWait here.\n{% endif %}\n'


def replace_finding(excerpt: str, new_text: str, source_order: int = 0, **context: str) -> dict:
    return {
        "source_order": source_order,
        "excerpt": excerpt,
        "context_before": context.get("before"),
        "context_after": context.get("after"),
        "action": "replace",
        "new_text": new_text,
    }


@pytest.mark.parametrize(
    ("excerpt", "new_text"),
    [
        pytest.param("{{ actions.AskUser | call }}", "the ask tool", id="excerpt-is-expression"),
        pytest.param("AskUser", "Ask", id="excerpt-inside-expression"),
        pytest.param("Wait here.\n{% endif %}", "Wait.", id="excerpt-spans-tag"),
        pytest.param("now.", "{{ now }}.", id="new-text-adds-expression"),
        pytest.param("now.", "now {%", id="new-text-adds-stray-marker"),
        pytest.param("Ask with ", "{", id="edit-joins-into-marker"),
    ],
)
def test_apply_findings_refuses_template_edits_that_touch_jinja(
    scripts_dir: Path, tmp_path: Path, excerpt: str, new_text: str
) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
    target = tmp_path / f"SKILL.md{TEMPLATE_SUFFIX}"
    target.write_text(TEMPLATE, encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(target, [replace_finding(excerpt, new_text)])

    assert applied == 0
    assert failures[0]["reason"] == "edit touches Jinja syntax; Jinja blocks in a template are not editable"
    assert target.read_text(encoding="utf-8") == TEMPLATE


def test_apply_findings_edits_template_text_around_jinja(scripts_dir: Path, tmp_path: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
    target = tmp_path / f"SKILL.md{TEMPLATE_SUFFIX}"
    target.write_text(TEMPLATE, encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(
        target,
        [
            replace_finding("Ask with ", "Use ", after="{{ actions"),
            replace_finding("Wait here.", "Wait.", source_order=1),
        ],
    )

    assert (applied, failures) == (2, [])
    assert target.read_text(encoding="utf-8") == (
        'Use {{ actions.AskUser | call }} now.\n{% if harness == "Codex" %}\nWait.\n{% endif %}\n'
    )


def test_apply_findings_edits_literal_braces_in_plain_markdown(scripts_dir: Path, tmp_path: Path) -> None:
    apply_findings = load_script(scripts_dir, "apply_findings")
    target = tmp_path / "doc.md"
    target.write_text("Render {{ name }} literally.\n", encoding="utf-8")

    applied, failures = apply_findings.apply_file_findings(target, [replace_finding("{{ name }}", "`{{ name }}`")])

    assert (applied, failures) == (1, [])
    assert target.read_text(encoding="utf-8") == "Render `{{ name }}` literally.\n"


def test_validate_output_invariants_reject_invalid_recommended_indexes(scripts_dir: Path) -> None:
    validate_output = load_script(scripts_dir, "validate_output")

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


def test_validate_output_reports_missing_jsonschema(scripts_dir: Path, monkeypatch) -> None:
    validate_output = load_script(scripts_dir, "validate_output")

    monkeypatch.setattr(validate_output.shutil, "which", lambda _name: None)

    status = validate_output.run_jsonschema(Path("instance.json"), Path("schema.json"))

    assert status == 127


def test_measure_size_uses_tiktoken_count_when_encoder_is_available(scripts_dir: Path, tmp_path: Path) -> None:
    measure_size = load_script(scripts_dir, "measure_size")
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


def test_measure_size_fallback_uses_conservative_char_word_estimate(scripts_dir: Path, tmp_path: Path) -> None:
    measure_size = load_script(scripts_dir, "measure_size")
    target = tmp_path / "doc.md"
    target.write_text(("word " * 900).strip(), encoding="utf-8")

    report = measure_size.measure_file(target, soft_budget_tokens=1000, hard_budget_tokens=2000)

    assert report["tokens"] == 1200
    assert report["token_source"] == "estimate:max(chars/4,words/0.75)"
    assert report["characters"] == 4499
    assert report["words"] == 900
    assert report["status"] == "warning"


def test_measure_size_marks_hard_budget_exceeded(scripts_dir: Path, tmp_path: Path) -> None:
    measure_size = load_script(scripts_dir, "measure_size")
    target = tmp_path / "doc.md"
    target.write_text("x" * 9000, encoding="utf-8")

    report = measure_size.measure_file(target, soft_budget_tokens=1000, hard_budget_tokens=2000)

    assert report["tokens"] == 2250
    assert report["status"] == "over_budget"


def test_size_budget_markdown_delegates_calculation_to_script(skill_dir: Path) -> None:
    markdown_files = [
        skill_dir / "SKILL.md",
        skill_dir / "agents" / "size-budget-reporter.md",
        skill_dir / "docs" / "SPEC.md",
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


def test_tiktoken_optional_requirement_uses_compatibility_frontmatter(skill_dir: Path) -> None:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]

    assert "compatibility:" in frontmatter
    assert "Optional `tiktoken`" in frontmatter
    assert "allowed-tools:" not in frontmatter


def test_preflight_validate_target_accepts_clean_tracked_markdown(scripts_dir: Path, tmp_path: Path) -> None:
    preflight = load_script(scripts_dir, "preflight")
    repo, target = clean_git_repo(tmp_path)

    result = preflight.validate_target(target)

    assert result["file_path"] == str(target.resolve())
    assert result["repo_root"] == str(repo.resolve())
    assert result["git_relative_path"] == "doc.md"
    assert result["sha256"] == preflight.sha256(target)


def test_preflight_validate_target_accepts_uppercase_markdown_extension(scripts_dir: Path, tmp_path: Path) -> None:
    preflight = load_script(scripts_dir, "preflight")
    repo, target = clean_git_repo(tmp_path, "doc.MD")

    result = preflight.validate_target(target)

    assert result["file_path"] == str(target.resolve())
    assert result["repo_root"] == str(repo.resolve())
    assert result["git_relative_path"] == "doc.MD"


@pytest.mark.parametrize("name", [f"SKILL.md{TEMPLATE_SUFFIX}", f"agent.MD{TEMPLATE_SUFFIX.upper()}"])
def test_preflight_validate_target_accepts_markdown_template(scripts_dir: Path, tmp_path: Path, name: str) -> None:
    preflight = load_script(scripts_dir, "preflight")
    _repo, target = clean_git_repo(tmp_path, name)

    result = preflight.validate_target(target)

    assert result["git_relative_path"] == name


@pytest.mark.parametrize("name", ["notes.txt", f"config.yaml{TEMPLATE_SUFFIX}", f"doc{TEMPLATE_SUFFIX}"])
def test_preflight_rejects_non_markdown_target(scripts_dir: Path, tmp_path: Path, name: str) -> None:
    preflight = load_script(scripts_dir, "preflight")
    _repo, target = clean_git_repo(tmp_path, name)

    with pytest.raises(ValueError, match=f"^{re.escape(preflight.TargetError.NOT_MARKDOWN)}$"):
        preflight.validate_target(target)


def test_preflight_rejects_dirty_target(scripts_dir: Path, tmp_path: Path) -> None:
    preflight = load_script(scripts_dir, "preflight")
    _repo, target = clean_git_repo(tmp_path)
    target.write_text("# Title\n\nChanged.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="^target has staged or unstaged changes$"):
        preflight.validate_target(target)


def test_preflight_rejects_untracked_target(scripts_dir: Path, tmp_path: Path) -> None:
    preflight = load_script(scripts_dir, "preflight")
    repo, _target = clean_git_repo(tmp_path)
    untracked = repo / "untracked.md"
    untracked.write_text("draft\n", encoding="utf-8")

    with pytest.raises(ValueError, match="^target is not tracked by git$"):
        preflight.validate_target(untracked)


def test_preflight_main_rejects_changed_hash_from_expect_map(scripts_dir: Path, tmp_path: Path) -> None:
    repo, target = clean_git_repo(tmp_path)
    expect_map = tmp_path / "preflight.json"
    first = subprocess.run(
        [sys.executable, str(scripts_dir / "preflight.py"), str(target)],
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
        [sys.executable, str(scripts_dir / "preflight.py"), "--expect-map", str(expect_map), str(target)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert second.returncode == 1
    payload = json.loads(second.stdout)
    assert payload["errors"][0]["error"] == "target content hash changed since preflight"


def touch_markdown(directory: Path, *names: str) -> list[str]:
    paths = []
    for name in names:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name}\n", encoding="utf-8")
        paths.append(str(path))
    return paths


def test_build_closures_follows_reads_and_stops_at_dispatch_targets(scripts_dir: Path, tmp_path: Path) -> None:
    build_closures = load_script(scripts_dir, "build_closures")
    skill, ref, shared, agent, agent_ref = touch_markdown(
        tmp_path, "SKILL.md", "references/ref.md", "references/shared.md", "agents/agent.md", "references/agent-only.md"
    )
    edges = [
        {"from": skill, "to": ref, "kind": "reads"},
        {"from": ref, "to": shared, "kind": "reads"},
        {"from": skill, "to": agent, "kind": "reads"},
        {"from": skill, "to": agent, "kind": "dispatches"},
        {"from": agent, "to": agent_ref, "kind": "reads"},
    ]

    closures = build_closures.build_closures({skill, ref, shared, agent}, edges)

    assert closures == [
        {"root": skill, "editable": sorted([skill, ref, shared, agent]), "read_only": []},
        {"root": agent, "editable": [agent], "read_only": [agent_ref]},
    ]


def test_build_closures_cli_rejects_missing_files(scripts_dir: Path, tmp_path: Path) -> None:
    (skill,) = touch_markdown(tmp_path, "SKILL.md")
    graph = write_json(
        tmp_path / "graph.json",
        {"editable": [skill], "edges": [{"from": skill, "to": str(tmp_path / "missing.md"), "kind": "reads"}]},
    )

    result = subprocess.run(
        [sys.executable, str(scripts_dir / "build_closures.py"), str(graph)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert json.loads(result.stdout)["errors"] == [f"not a file: {tmp_path / 'missing.md'}"]
