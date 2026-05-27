import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"


EXPECTED_PLUGINS = {
    "ai-assistant-ops",
    "cloud-storage-tools",
    "dev-workflow",
    "job-hunt-toolkit",
    "langfuse",
    "llm-application-dev",
    "openapi-tools",
    "os-tools",
    "python-dev-workflow",
    "work-session-tools",
}


EXPECTED_SKILLS = {
    "ai-assistant-ops": {
        "agents-md-improver",
        "ai-insights-hunter",
        "ai-setup-audit",
        "md-bloat-hunter",
    },
    "cloud-storage-tools": {"mega-cmd"},
    "dev-workflow": {
        "commit",
        "create-pr",
        "pr-address-comments",
        "pr-checkout",
        "pr-comment",
        "spec-contradiction-hunter",
        "ticket-branch",
        "ticket-comment-status",
        "version-bumper",
    },
    "job-hunt-toolkit": {
        "export-pdf",
        "init-workspace",
        "new-application",
        "prepare-to-send",
        "resume-tailoring",
        "scrub-pdf-metadata",
    },
    "langfuse": {
        "analyze-experiment-results",
        "compare-experiments",
        "configure-remote-experiment",
        "create-dataset",
        "create-evaluator",
        "create-widget",
        "delete-evaluator",
        "delete-widget",
        "design-dataset-schema",
        "discover-datasets",
        "discover-filter-options",
        "discover-models",
        "discover-scores",
        "discover-traces",
        "inspect-evaluator",
        "layout-widgets",
        "list-dataset-runs",
        "list-evaluators",
        "list-widgets",
        "manage-dashboard",
        "manage-dataset-items",
        "query-metrics",
        "suggest-widgets",
        "toggle-evaluator-status",
        "trigger-experiment",
        "update-evaluator",
        "update-widget",
    },
    "llm-application-dev": {"schema-guided-reasoning"},
    "openapi-tools": {"openapi-inspect", "openapi-list"},
    "os-tools": {"loop_macos"},
    "python-dev-workflow": {
        "celery-expert",
        "pytest-redis",
        "writing-unit-tests",
    },
    "work-session-tools": {"daily", "interview", "task-management"},
}


EXPECTED_PLUGIN_AGENTS = {
    "dev-workflow": {
        "ambiguity-contradiction-hunter",
        "release-manager",
        "structural-contradiction-hunter",
        "surface-contradiction-hunter",
    },
    "langfuse": {
        "langfuse-data-explorer",
        "langfuse-dataset-expert",
        "langfuse-eval-manager",
        "langfuse-experiment-manager",
        "langfuse-widget-manager",
    },
    "python-dev-workflow": {"test-runner", "test-unit-reviewer"},
}


class MarketplaceOrganizationTest(unittest.TestCase):
    def test_plugins_are_split_into_target_families(self) -> None:
        actual_plugins = {
            path.name
            for path in PLUGINS_ROOT.iterdir()
            if path.is_dir()
        }

        self.assertEqual(EXPECTED_PLUGINS, actual_plugins)

    def test_each_plugin_has_manifests_and_readme(self) -> None:
        for plugin_name in EXPECTED_PLUGINS:
            plugin_dir = PLUGINS_ROOT / plugin_name

            self.assertTrue((plugin_dir / "README.md").is_file(), plugin_name)
            self.assertTrue((plugin_dir / ".codex-plugin" / "plugin.json").is_file(), plugin_name)
            self.assertTrue((plugin_dir / ".claude-plugin" / "plugin.json").is_file(), plugin_name)

    def test_skills_live_in_expected_plugins(self) -> None:
        for plugin_name, expected_skills in EXPECTED_SKILLS.items():
            actual_skills = {
                path.parent.name
                for path in (PLUGINS_ROOT / plugin_name / "skills").glob("*/SKILL.md")
            }

            self.assertEqual(expected_skills, actual_skills, plugin_name)

    def test_plugin_level_agents_live_in_expected_plugins(self) -> None:
        for plugin_name, expected_agents in EXPECTED_PLUGIN_AGENTS.items():
            actual_agents = {
                path.stem
                for path in (PLUGINS_ROOT / plugin_name / "agents").glob("*.md")
            }

            self.assertEqual(expected_agents, actual_agents, plugin_name)

    def test_skill_owned_agents_stay_nested_under_parent_skills(self) -> None:
        self.assertTrue(
            (PLUGINS_ROOT / "ai-assistant-ops" / "skills" / "ai-insights-hunter" / "agents").is_dir()
        )
        self.assertTrue(
            (PLUGINS_ROOT / "ai-assistant-ops" / "skills" / "md-bloat-hunter" / "agents").is_dir()
        )

    def test_hard_references_use_new_plugin_names(self) -> None:
        insights = (
            PLUGINS_ROOT
            / "ai-assistant-ops"
            / "skills"
            / "ai-insights-hunter"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        pr_address = (
            PLUGINS_ROOT
            / "dev-workflow"
            / "skills"
            / "pr-address-comments"
            / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("ai-assistant-ops:agents-md-improver", insights)
        self.assertNotIn("agents-md-management:agents-md-improver", insights)
        self.assertIn("dev-workflow:commit", pr_address)
        self.assertIn("dev-workflow:pr-comment", pr_address)
        self.assertNotIn("python-dev-workflow:commit", pr_address)
        self.assertNotIn("general-plugins:pr-comment", pr_address)

    def test_marketplace_files_list_target_plugins(self) -> None:
        agents_marketplace = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        claude_marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            EXPECTED_PLUGINS,
            {plugin["name"] for plugin in agents_marketplace["plugins"]},
        )
        self.assertEqual(
            EXPECTED_PLUGINS,
            {plugin["name"] for plugin in claude_marketplace["plugins"]},
        )


if __name__ == "__main__":
    unittest.main()
