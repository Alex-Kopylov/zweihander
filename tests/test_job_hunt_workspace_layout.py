import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/job-hunt-toolkit"

SLUG_RE = "^[a-z0-9]+(?:_[a-z0-9]+)*$"


def test_canonical_layout_is_jobs_company() -> None:
    layout = (PLUGIN / "references/workspace-layout.md").read_text(encoding="utf-8")
    assert "jobs/<company>/" in layout
    assert SLUG_RE in layout
    assert "no fallback" in layout


def test_new_application_enforces_slug_regex_and_jobs_prefix() -> None:
    skill = (PLUGIN / "skills/new-application/SKILL.md").read_text(encoding="utf-8")
    assert SLUG_RE in skill
    assert "mkdir -p <workspace>/jobs/<slug>" in skill
    assert "deny-list" not in skill.lower()


def test_naming_rules_forbid_hyphenated_slugs() -> None:
    naming = (PLUGIN / "references/naming-rules.md").read_text(encoding="utf-8")
    assert SLUG_RE in naming
    assert "acme-robotics" not in naming
    assert "jobs/acme_robotics/" in naming


def test_plugin_manifests_agree_on_version() -> None:
    claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert claude["version"] == codex["version"] == "0.4.0"
