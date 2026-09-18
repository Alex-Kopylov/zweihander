"""The mermaid-diagrams stage-1 generator package and the job that drives it."""

import inspect

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.generators import mermaid_diagrams
from plugin_maintenance.generators.mermaid_diagrams.generated_docs import (
    load_navigation_metadata,
)


PLUGIN_ROOT = REPO_ROOT / "plugins" / "mermaid-diagrams"
TOOLING_ROOT = REPO_ROOT / "plugin_maintenance" / "generators" / "mermaid_diagrams"


def tooling_text(relative_path: str) -> str:
    return (TOOLING_ROOT / relative_path).read_text(encoding="utf-8")


def test_generator_package_follows_stage_one_convention() -> None:
    signature = inspect.signature(mermaid_diagrams.generate)

    assert not signature.parameters
    assert mermaid_diagrams.PLUGIN_NAME == "mermaid-diagrams"


def test_bundled_navigation_metadata_is_used_without_source_checkout(monkeypatch) -> None:
    monkeypatch.delenv("MERMAID_DOCS_NAVIGATION", raising=False)
    metadata = load_navigation_metadata()

    assert (TOOLING_ROOT / "mermaid_navigation.json").is_file()
    assert metadata["flowchart"].title == "Flowchart"
    assert metadata["flowchart"].order == 0
    assert metadata["sequenceDiagram"].title == "Sequence Diagram"
    assert metadata["sequenceDiagram"].order == 1


def test_python_tooling_is_relocated_to_root_generators() -> None:
    assert (TOOLING_ROOT / "__init__.py").is_file()
    assert (TOOLING_ROOT / "generated_docs.py").is_file()
    assert (TOOLING_ROOT / "sync.py").is_file()
    assert (TOOLING_ROOT / "templates" / "mermaid_skill.md").is_file()
    assert (TOOLING_ROOT / "templates" / "readme.md").is_file()
    assert not (PLUGIN_ROOT / "plugin_maintenance").exists()
    assert not (PLUGIN_ROOT / "pyproject.toml").exists()
    assert not (PLUGIN_ROOT / "uv.lock").exists()
    assert not (PLUGIN_ROOT / "scripts" / "update-generated-docs.mjs").exists()
    assert not (PLUGIN_ROOT / "scripts" / "sync-mermaid-docs.mjs").exists()

    combined = "\n".join(
        [
            tooling_text("generated_docs.py"),
            tooling_text("sync.py"),
            tooling_text("templates/mermaid_skill.md"),
        ]
    )
    assert "skills/mermaid/references" in combined
    assert ".claude/skills" not in combined
    assert "Claude" not in combined
    assert "User requirements: $ARGUMENTS" not in combined


def test_python_sync_preserves_first_port_safety_gates() -> None:
    generated_docs = tooling_text("generated_docs.py")
    sync = tooling_text("sync.py")

    assert "existing_sync_status" in generated_docs
    assert "MERMAID_DOCS_NAVIGATION" in generated_docs
    assert "mermaid_navigation.json" in generated_docs
    assert "Mermaid docs navigation file not found" in generated_docs
    assert "THIRD_PARTY_NOTICES.md" in generated_docs
    assert "render_third_party_notices" in generated_docs
    assert "preflight_sync_source" in sync
    assert "write_bundled_navigation_metadata" in sync
    assert "existing_sync_metadata" in sync
    assert "existing_sync_metadata.commit == source_commit" in sync


def test_sync_workflow_uses_root_project_and_full_build() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "sync-mermaid-docs.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "astral-sh/setup-uv" in workflow
    assert "python -m plugin_maintenance.generators.mermaid_diagrams.sync mermaid-source" in workflow
    assert "python -m plugin_maintenance.build" in workflow
    assert "rm -rf plugins/mermaid-diagrams/mermaid-source" in workflow
    assert "uv run --project plugins/mermaid-diagrams" not in workflow
    assert "validate-generated-files:" not in workflow
    assert "git-auto-commit-action" not in workflow
    assert "create-pull-request" in workflow
    assert "npm run" not in workflow
