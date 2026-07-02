import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "find_versions.py"


def load_find_versions():
    spec = importlib.util.spec_from_file_location("find_versions", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.find_versions


def test_detects_claude_and_codex_plugin_manifests(tmp_path: Path) -> None:
    claude_manifest = tmp_path / ".claude-plugin" / "plugin.json"
    codex_manifest = tmp_path / ".codex-plugin" / "plugin.json"
    claude_manifest.parent.mkdir()
    codex_manifest.parent.mkdir()
    claude_manifest.write_text('{"name": "example", "version": "1.2.3"}\n')
    codex_manifest.write_text('{"name": "example", "version": "1.2.3"}\n')

    versions = load_find_versions()(tmp_path)

    discovered = {Path(str(item["file"])).relative_to(tmp_path) for item in versions}
    assert discovered == {
        Path(".claude-plugin/plugin.json"),
        Path(".codex-plugin/plugin.json"),
    }
    references_by_file = {Path(str(item["file"])).relative_to(tmp_path): item["reference"] for item in versions}
    assert references_by_file == {
        Path(".claude-plugin/plugin.json"): "references/claude-code-plugin-manifests.md",
        Path(".codex-plugin/plugin.json"): "references/codex-plugin-manifests.md",
    }


def test_reports_only_python_project_reference_without_fastapi(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')

    versions = load_find_versions()(tmp_path)

    assert [item["pattern"] for item in versions] == ["project"]
    assert {item["reference"] for item in versions} == {"references/python-project-files.md"}


def test_reports_fastapi_reference_only_when_fastapi_version_detected(tmp_path: Path) -> None:
    src = tmp_path / "src" / "service"
    src.mkdir(parents=True)
    (src / "main.py").write_text('from fastapi import FastAPI\napp = FastAPI(version="1.2.3")\n')

    versions = load_find_versions()(tmp_path)

    assert [item["pattern"] for item in versions] == ["fastapi"]
    assert {item["reference"] for item in versions} == {"references/fastapi-apps.md"}


def test_detects_claude_and_codex_marketplace_manifests(tmp_path: Path) -> None:
    claude_manifest = tmp_path / ".claude-plugin" / "marketplace.json"
    codex_manifest = tmp_path / ".agents" / "plugins" / "marketplace.json"
    claude_manifest.parent.mkdir(parents=True)
    codex_manifest.parent.mkdir(parents=True)
    claude_manifest.write_text('{"name": "example", "version": "1.2.3"}\n')
    codex_manifest.write_text('{"name": "example", "version": "1.2.3"}\n')

    versions = load_find_versions()(tmp_path)

    discovered = {Path(str(item["file"])).relative_to(tmp_path) for item in versions}
    assert discovered == {
        Path(".claude-plugin/marketplace.json"),
        Path(".agents/plugins/marketplace.json"),
    }
    references_by_file = {Path(str(item["file"])).relative_to(tmp_path): item["reference"] for item in versions}
    assert references_by_file == {
        Path(".claude-plugin/marketplace.json"): "references/claude-code-marketplace-manifests.md",
        Path(".agents/plugins/marketplace.json"): "references/codex-marketplace-manifests.md",
    }
