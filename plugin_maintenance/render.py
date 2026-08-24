"""Stage-2 renderer: render `plugins/` into one harness-specific tree.

Usage: `uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code`

File rules per output path X: copy X byte-for-byte when only X exists,
render X.j2 into X when only X.j2 exists, fail when both exist. Files named
AGENTS.md/CLAUDE.md/README.md, the other harness's runtime metadata
directory, and every path `.gitignore` excludes are never emitted. Each tree
contains exactly the plugins listed in that harness's marketplace manifest.
"""

import argparse
import json
import re
import shutil
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

import pathspec
from jinja2 import Environment, StrictUndefined, TemplateError

MATRIX_PATH = Path(
    "plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness"
    "/references/harness-action-matrix.json"
)
IGNORE_FILE = Path(".gitignore")
DEV_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "README.md"}
TEMPLATE_SUFFIX = ".j2"
JINJA_MARKERS = ("{{", "{%", "{#")
# One raw block in any spelling Jinja accepts: `{% raw %}`, `{%raw%}`, and the
# whitespace-control forms `{%- raw -%}` / `{%- endraw -%}`. The body is lazy
# because Jinja closes a raw block at its first `endraw` tag and treats a
# nested `raw` tag as literal text.
RAW_BLOCK = re.compile(
    r"\{%-?\s*raw\s*(?P<trim_head>-?)%\}"
    r"(?P<literal>.*?)"
    r"\{%(?P<trim_tail>-?)\s*endraw\s*-?%\}",
    re.DOTALL,
)

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


def ignored_path(repo_root: Path) -> Callable[[Path], bool]:
    """Return the test for paths `.gitignore` keeps out of the repository.

    Tooling drops artifacts into `plugins/`: `__pycache__/` from running a
    plugin's own scripts, `.DS_Store` from a file browser, scratch
    `*.local.md` notes. `.gitignore` is the repository's one declaration of
    what is not content, so publication reuses it instead of keeping a second
    list that would drift from it.

    The test reads `.gitignore`, never the git index. Stage 1 writes generated
    files into `plugins/` before anything commits them, so an index-driven
    test would drop newly generated content from the tree. A tree with no
    `.gitignore` ignores nothing.
    """
    ignore_file = repo_root / IGNORE_FILE
    patterns = (
        ignore_file.read_text(encoding="utf-8").splitlines()
        if ignore_file.is_file()
        else []
    )
    spec = pathspec.GitIgnoreSpec.from_lines(patterns)
    return lambda path: spec.match_file(path.relative_to(repo_root))


def raw_literals(template_text: str) -> list[str]:
    """Return each raw block's text exactly as it reaches the rendered output.

    Jinja copies raw content verbatim, so the output holds the same characters
    at a different offset. Only the block's own edges move: `-%}` on the `raw`
    tag strips the leading whitespace of the content, and `{%-` on the
    `endraw` tag strips its trailing whitespace.
    """
    literals = []
    for block in RAW_BLOCK.finditer(template_text):
        literal = block.group("literal")
        if block.group("trim_head"):
            literal = literal.lstrip()
        if block.group("trim_tail"):
            literal = literal.rstrip()
        if literal:
            literals.append(literal)
    return literals


def leftover_jinja_markers(template_text: str, rendered: str) -> list[str]:
    """Return the Jinja markers left in `rendered` outside its raw blocks.

    Raw blocks declare literal braces, so their text is removed by content
    before the scan. Every other region of the file stays under the scan.
    """
    scanned = rendered
    for literal in raw_literals(template_text):
        scanned = scanned.replace(literal, "")
    return [marker for marker in JINJA_MARKERS if marker in scanned]


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

    markers = leftover_jinja_markers(text, rendered)
    if markers:
        raise BuildError(
            f"{source} rendered for harness '{harness}' still contains Jinja "
            f"marker '{markers[0]}' outside any raw block"
        )
    return rendered


def _render_plugin(
    source_dir: Path,
    target_dir: Path,
    environment: Environment,
    context: dict,
    harness: str,
    is_ignored: Callable[[Path], bool],
) -> None:
    foreign_metadata = FOREIGN_METADATA_DIRS[harness]
    for source in sorted(source_dir.rglob("*")):
        relative = source.relative_to(source_dir)
        if foreign_metadata in relative.parts or source.is_dir():
            continue
        if is_ignored(source):
            continue
        is_template = source.name.endswith(TEMPLATE_SUFFIX)
        plain_name = source.name[: -len(TEMPLATE_SUFFIX)] if is_template else source.name
        if plain_name in DEV_FILE_NAMES:
            if is_template:
                raise BuildError(
                    f"{source} would emit the development file {plain_name}, "
                    "which is never shipped; author it as a plain file"
                )
            continue

        if is_template:
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
    is_ignored = ignored_path(repo_root)

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
    # `mkdtemp` always creates its directory 0o700 and `rename` keeps that mode,
    # which would publish a tree that other users cannot traverse. Take the mode
    # of `dist/` itself, so a fresh checkout and a post-build tree agree and the
    # published mode stays a function of the source tree, not of what was there.
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-staging-", dir=output_dir.parent)
    )
    staging.chmod(output_dir.parent.stat().st_mode & 0o777)
    try:
        for plugin_name in plugin_names:
            source_dir = repo_root / "plugins" / plugin_name
            if not source_dir.is_dir():
                raise BuildError(
                    f"manifest {manifest} lists plugin '{plugin_name}' but "
                    f"{source_dir} does not exist"
                )
            _render_plugin(
                source_dir,
                staging / plugin_name,
                environment,
                context,
                harness,
                is_ignored,
            )
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    if output_dir.is_dir():
        shutil.rmtree(output_dir)
    elif output_dir.exists():
        output_dir.unlink()
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
