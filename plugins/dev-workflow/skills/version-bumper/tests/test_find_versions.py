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
