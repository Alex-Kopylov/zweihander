"""Stage-2 renderer: render `plugins/` into one harness-specific tree.

Usage: `uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code`

File rules per output path X: copy X byte-for-byte when only X exists,
render X.j2 into X when only X.j2 exists, fail when both exist. Files named
AGENTS.md/CLAUDE.md/README.md and the other harness's runtime metadata
directory are never emitted. Each tree contains exactly the plugins listed
in that harness's marketplace manifest.
"""

import argparse
import json
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, StrictUndefined, TemplateError

MATRIX_PATH = Path(
    "plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness"
    "/references/harness-action-matrix.json"
)
DEV_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "README.md"}
TEMPLATE_SUFFIX = ".j2"
JINJA_MARKERS = ("{{", "{%", "{#")

HARNESS_MANIFESTS = {
    "ClaudeCode": Path(".claude-plugin/marketplace.json"),
    "Codex": Path(".agents/plugins/marketplace.json"),
}
FOREIGN_METADATA_DIRS = {
    "ClaudeCode": ".codex-plugin",
    "Codex": ".claude-plugin",
}
DIST_DIRS = {
    "ClaudeCode": Path("dist/claude-code"),
    "Codex": Path("dist/codex"),
}


class BuildError(Exception):
    """Raised when the build must stop instead of emitting a partial tree."""


class ActionMap(Mapping):
    """Action key -> callable name; a missing key names the action and harness."""

    def __init__(self, names: dict[str, str], harness: str) -> None:
        self._names = names
        self._harness = harness

    def __getitem__(self, key: str) -> str:
        try:
            return self._names[key]
        except KeyError:
            raise BuildError(
                f"action '{key}' is not mapped for harness '{self._harness}' "
                "in the action matrix"
            ) from None

    def __iter__(self):
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)


def load_matrix(matrix_path: Path) -> dict:
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"cannot load action matrix {matrix_path}: {error}") from error

    assistants = matrix.get("assistants")
    actions = matrix.get("actions")
    if not isinstance(assistants, dict) or not assistants or not isinstance(actions, dict):
        raise BuildError(
            f"malformed action matrix {matrix_path}: "
            "'assistants' and 'actions' must be non-empty objects"
        )
    for assistant_key, assistant in assistants.items():
        wrapper = assistant.get("invocation_wrapper")
        if not isinstance(wrapper, str) or wrapper.count("{name}") != 1:
            raise BuildError(
                f"malformed action matrix {matrix_path}: assistant "
                f"'{assistant_key}' needs one invocation_wrapper with one "
                "{name} slot"
            )
    for action_key, action in actions.items():
        if not isinstance(action.get("callable"), bool):
            raise BuildError(
                f"malformed action matrix {matrix_path}: action '{action_key}' "
                "is missing the boolean 'callable' flag"
            )
        if not action["callable"]:
            continue
        for assistant_key in assistants:
            name = action.get(assistant_key, {}).get("name")
            if not isinstance(name, str) or not name:
                raise BuildError(
                    f"malformed action matrix {matrix_path}: callable action "
                    f"'{action_key}' has no name for assistant '{assistant_key}'"
                )
    return matrix


def manifest_plugin_names(manifest_path: Path) -> list[str]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(
            f"cannot load marketplace manifest {manifest_path}: {error}"
        ) from error

    plugins = manifest.get("plugins")
    if not isinstance(plugins, list) or not all(
        isinstance(entry, dict) and isinstance(entry.get("name"), str)
        for entry in plugins
    ):
        raise BuildError(
            f"marketplace manifest {manifest_path} needs a 'plugins' list "
            "of objects with 'name'"
        )
    return [entry["name"] for entry in plugins]


def _render_template(
    source: Path, environment: Environment, context: dict, harness: str
) -> str:
    text = source.read_text(encoding="utf-8")
    try:
        rendered = environment.from_string(text).render(**context)
    except BuildError:
        raise
    except TemplateError as error:
        raise BuildError(
            f"failed to render {source} for harness '{harness}': {error}"
        ) from error

    if "{% raw %}" not in text:
        for marker in JINJA_MARKERS:
            if marker in rendered:
                raise BuildError(
                    f"{source} rendered for harness '{harness}' still "
                    f"contains Jinja marker '{marker}'"
                )
    return rendered


def _render_plugin(
    source_dir: Path,
    target_dir: Path,
    environment: Environment,
    context: dict,
    harness: str,
) -> None:
    foreign_metadata = FOREIGN_METADATA_DIRS[harness]
    for source in sorted(source_dir.rglob("*")):
        relative = source.relative_to(source_dir)
        if foreign_metadata in relative.parts or source.is_dir():
            continue
        if source.name in DEV_FILE_NAMES:
            continue

        if source.name.endswith(TEMPLATE_SUFFIX):
            plain_name = source.name[: -len(TEMPLATE_SUFFIX)]
            if source.with_name(plain_name).exists():
                raise BuildError(
                    f"both {source.with_name(plain_name)} and {source} exist; "
                    "keep exactly one"
                )
            target = target_dir / relative.with_name(plain_name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                _render_template(source, environment, context, harness),
                encoding="utf-8",
            )
        else:
            target = target_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copymode(source, target)


def render_tree(
    repo_root: Path,
    harness: str,
    output_dir: Path,
    matrix_path: Path | None = None,
    manifest_path: Path | None = None,
) -> None:
    repo_root = Path(repo_root)
    matrix = load_matrix(Path(matrix_path) if matrix_path else repo_root / MATRIX_PATH)

    if harness not in matrix["assistants"] or harness not in HARNESS_MANIFESTS:
        known = sorted(set(matrix["assistants"]) & set(HARNESS_MANIFESTS))
        raise BuildError(
            f"unknown harness '{harness}'; supported harnesses: {', '.join(known)}"
        )

    manifest = Path(manifest_path) if manifest_path else repo_root / HARNESS_MANIFESTS[harness]
    plugin_names = manifest_plugin_names(manifest)

    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    wrapper = matrix["assistants"][harness]["invocation_wrapper"]
    environment.filters["call"] = lambda name: wrapper.format(name=name)
    context = {
        "harness": harness,
        "actions": ActionMap(
            {
                action_key: action[harness]["name"]
                for action_key, action in matrix["actions"].items()
                if action["callable"]
            },
            harness,
        ),
    }

    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-staging-", dir=output_dir.parent)
    )
    try:
        for plugin_name in plugin_names:
            source_dir = repo_root / "plugins" / plugin_name
            if not source_dir.is_dir():
                raise BuildError(
                    f"manifest {manifest} lists plugin '{plugin_name}' but "
                    f"{source_dir} does not exist"
                )
            _render_plugin(
                source_dir, staging / plugin_name, environment, context, harness
            )
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    if output_dir.exists():
        shutil.rmtree(output_dir)
    staging.rename(output_dir)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Render plugins/ into one harness-specific dist tree."
    )
    parser.add_argument("--harness", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        render_tree(args.repo_root, args.harness, args.output)
    except BuildError as error:
        raise SystemExit(f"error: {error}") from error
    print(f"rendered {args.harness} -> {args.output}")


if __name__ == "__main__":
    main()
