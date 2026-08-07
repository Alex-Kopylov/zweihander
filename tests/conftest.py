"""Shared fixtures for harness dist-pipeline tests.

`fixture_repo` builds a minimal marketplace repo in tmp_path: two root
marketplace manifests, plugins with and without templates, a Codex-only
plugin, and an unlisted plugin. Renderer unit tests exercise the stage-2
renderer against this tree instead of the real `plugins/`.
"""

import json
import os
from pathlib import Path

import pytest


FIXTURE_MATRIX = {
    "schema_version": 2,
    "checked": "2026-08-07",
    "lookup_order": ["action", "assistant"],
    "assistants": {
        "ClaudeCode": {
            "id": "claude-code",
            "display_name": "Claude Code",
            "invocation_wrapper": "Skill({name})",
        },
        "Codex": {
            "id": "codex",
            "display_name": "Codex",
            "invocation_wrapper": "${name}",
        },
    },
    "actions": {
        "AskUser": {
            "callable": True,
            "intent": "Ask the user for clarification or a bounded choice.",
            "ClaudeCode": {"name": "AskUserQuestion"},
            "Codex": {"name": "request_user_input"},
        },
        "CreateAgent": {
            "callable": True,
            "intent": "Delegate work to an isolated agent context.",
            "ClaudeCode": {"name": "Agent"},
            "Codex": {"name": "spawn_agent"},
        },
        "SlashCommand": {
            "callable": False,
            "intent": "Refer to slash-command workflows.",
            "ClaudeCode": {"commands": ["/plugin-name:skill-name"]},
            "Codex": {"commands": ["/skills", "/plugins"]},
        },
    },
}

DEMO_SKILL_TEMPLATE = """\
---
name: demo
---

# Demo

Ask via {{ actions.AskUser | call }}, the {{ actions.AskUser }} mechanism.
Delegate via {{ actions.CreateAgent | call }}.
Invoke {{ "commit" | call }} or {{ "dev-workflow:commit" | call }}.
{% if harness == "Codex" %}Codex-specific narrative.{% else %}Claude Code-specific narrative.{% endif %}
{% raw %}Keep the literal {{COMPANY}} placeholder.{% endraw %}
"""

PLAIN_REFERENCE = "Literal {{ mustache }} and {% marker %} stay untouched.\n"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_plugin_metadata(plugin_dir: Path, name: str, runtimes: tuple[str, ...]) -> None:
    manifest = json.dumps(
        {"name": name, "version": "0.1.0", "skills": "./skills/"}, indent=2
    )
    for runtime_dir in runtimes:
        _write(plugin_dir / runtime_dir / "plugin.json", manifest + "\n")


def _claude_entry(name: str) -> dict:
    return {
        "name": name,
        "source": f"./dist/claude-code/{name}",
        "description": "Fixture plugin.",
        "category": "development",
    }


def _codex_entry(name: str) -> dict:
    return {
        "name": name,
        "source": {"source": "local", "path": f"./dist/codex/{name}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Development",
    }


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"

    _write(
        repo / ".claude-plugin" / "marketplace.json",
        json.dumps(
            {
                "name": "fixture",
                "owner": {"name": "Fixture Owner"},
                "plugins": [_claude_entry("demo-plugin"), _claude_entry("plain-plugin")],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        repo / ".agents" / "plugins" / "marketplace.json",
        json.dumps(
            {
                "name": "fixture",
                "interface": {"displayName": "Fixture"},
                "plugins": [
                    _codex_entry("demo-plugin"),
                    _codex_entry("plain-plugin"),
                    _codex_entry("codex-only-plugin"),
                ],
            },
            indent=2,
        )
        + "\n",
    )

    demo = repo / "plugins" / "demo-plugin"
    _write_plugin_metadata(demo, "demo-plugin", (".claude-plugin", ".codex-plugin"))
    _write(demo / "README.md", "# Dev-only readme\n")
    _write(demo / "AGENTS.md", "Dev-only instructions.\n")
    _write(demo / "CLAUDE.md", "@AGENTS.md\n")
    _write(demo / "skills" / "demo" / "SKILL.md.j2", DEMO_SKILL_TEMPLATE)
    _write(demo / "skills" / "demo" / "references" / "plain.md", PLAIN_REFERENCE)
    hook = _write(demo / "scripts" / "hook.sh", "#!/bin/sh\necho demo\n")
    os.chmod(hook, 0o755)

    plain = repo / "plugins" / "plain-plugin"
    _write_plugin_metadata(plain, "plain-plugin", (".claude-plugin", ".codex-plugin"))
    _write(plain / "skills" / "plain" / "SKILL.md", "# Plain\n\nNo templates here.\n")

    codex_only = repo / "plugins" / "codex-only-plugin"
    _write_plugin_metadata(codex_only, "codex-only-plugin", (".codex-plugin",))
    _write(codex_only / "skills" / "solo" / "SKILL.md", "# Solo\n")

    unlisted = repo / "plugins" / "unlisted-plugin"
    _write_plugin_metadata(unlisted, "unlisted-plugin", (".claude-plugin", ".codex-plugin"))
    _write(unlisted / "skills" / "ghost" / "SKILL.md", "# Ghost\n")

    return repo


@pytest.fixture
def fixture_matrix(fixture_repo: Path) -> Path:
    return _write(
        fixture_repo / "matrix.json", json.dumps(FIXTURE_MATRIX, indent=2) + "\n"
    )
