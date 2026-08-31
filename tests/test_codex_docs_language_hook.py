"""Tests for the Codex PostToolUse documentation-language hook."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / ".codex" / "hooks" / "docs_language_guard.py"
HOOKS_CONFIG = REPO_ROOT / ".codex" / "hooks.json"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("docs_language_guard", HOOK_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_patch(*paths: str) -> str:
    body = "".join(
        f"*** Update File: {path}\n@@\n-old line\n+new line\n" for path in paths
    )
    return f"*** Begin Patch\n{body}*** End Patch\n"


def make_event(patch_text: str, cwd: Path) -> str:
    return json.dumps(
        {
            "session_id": "test-session",
            "transcript_path": None,
            "cwd": str(cwd),
            "hook_event_name": "PostToolUse",
            "model": "test-model",
            "permission_mode": "default",
            "turn_id": "turn-1",
            "tool_name": "apply_patch",
            "tool_use_id": "call-1",
            "tool_input": {"command": patch_text},
            "tool_response": {"output": "Success."},
        }
    )


def run_hook(payload: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["CODEX_DOCS_LANG_HOOK_DRY_RUN"] = "1"
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=environment,
        timeout=60,
        check=False,
    )


@pytest.fixture(scope="module")
def sample_repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("sample-repo")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "common").mkdir()
    (root / "common" / "docs-language-guidelines.md").write_text("# Guidelines\n")
    for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md"):
        (root / name).write_text(f"# {name}\n")
    (root / "docs" / "guide").mkdir(parents=True)
    (root / "docs" / "guide" / "setup.md").write_text("# Setup\n")
    (root / "docs" / "index.md").write_text("# Index\n")
    (root / "docs" / "diagram.svg").write_text("<svg></svg>\n")
    skill_directory = root / "plugins" / "dev-workflow" / "skills" / "commit"
    skill_directory.mkdir(parents=True)
    (skill_directory / "SKILL.md").write_text("# Skill\n")
    (root / "plugins" / "dev-workflow" / "docs").mkdir()
    (root / "plugins" / "dev-workflow" / "docs" / "notes.md").write_text("# Notes\n")
    (root / "plugins" / "dev-workflow" / "README.md").write_text("# Plugin\n")
    (root / "plugins" / "dev-workflow" / "AGENTS.md").write_text("# Agents\n")
    return root


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "CONTRIBUTING.md",
        "docs/guide/setup.md",
        "docs/index.md",
        "plugins/dev-workflow/README.md",
        "plugins/dev-workflow/docs/notes.md",
    ],
)
def test_in_scope_paths_dispatch(sample_repository: Path, path: str) -> None:
    result = run_hook(make_event(make_patch(path), sample_repository), sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == f"dispatch: {path}"


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "CLAUDE.md",
        "plugins/dev-workflow/AGENTS.md",
        "plugins/dev-workflow/skills/commit/SKILL.md",
        "docs/diagram.svg",
    ],
)
def test_out_of_scope_paths_do_not_dispatch(sample_repository: Path, path: str) -> None:
    result = run_hook(make_event(make_patch(path), sample_repository), sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == "no-dispatch"


def test_mixed_patch_dispatches_only_in_scope_files(sample_repository: Path) -> None:
    patch_text = make_patch("README.md", "AGENTS.md", "docs/guide/setup.md")
    result = run_hook(make_event(patch_text, sample_repository), sample_repository)
    assert result.returncode == 0
    assert result.stdout.split() == [
        "dispatch:",
        "README.md",
        "dispatch:",
        "docs/guide/setup.md",
    ]


def test_missing_file_does_not_dispatch(sample_repository: Path) -> None:
    patch_text = make_patch("docs/does-not-exist.md")
    result = run_hook(make_event(patch_text, sample_repository), sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == "no-dispatch"


def test_deleted_file_does_not_dispatch(sample_repository: Path) -> None:
    patch_text = "*** Begin Patch\n*** Delete File: README.md\n*** End Patch\n"
    result = run_hook(make_event(patch_text, sample_repository), sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == "no-dispatch"


def test_other_tool_does_not_dispatch(sample_repository: Path) -> None:
    payload = json.loads(make_event(make_patch("README.md"), sample_repository))
    payload["tool_name"] = "Bash"
    result = run_hook(json.dumps(payload), sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_broken_stdin_exits_cleanly(sample_repository: Path) -> None:
    result = run_hook("not json at all", sample_repository)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_rename_target_is_used(sample_repository: Path) -> None:
    module = load_hook_module()
    patch_text = (
        "*** Begin Patch\n"
        "*** Update File: notes.md\n"
        "*** Move to: docs/notes.md\n"
        "@@\n-a\n+b\n"
        "*** End Patch\n"
    )
    assert module.patched_paths(patch_text) == ["docs/notes.md"]


def test_hooks_config_registers_post_tool_use_handler() -> None:
    config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
    groups = config["hooks"]["PostToolUse"]
    assert len(groups) == 1
    handler = groups[0]["hooks"][0]
    assert handler["type"] == "command"
    assert handler["async"] is True
    assert "docs_language_guard.py" in handler["command"]
    assert "git rev-parse --show-toplevel" in handler["command"]


def test_hook_script_is_executable() -> None:
    assert os.access(HOOK_SCRIPT, os.X_OK)
