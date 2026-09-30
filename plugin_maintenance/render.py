"""Stage-2 renderer: render `plugins/` into one harness-specific tree.

Usage: `uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code`

File rules per output path X: copy X byte-for-byte when only X exists,
render X.j2 into X when only X.j2 exists, fail when both exist. Files named
AGENTS.md/CLAUDE.md/README.md, the other harness's runtime metadata
directory and skill files, and every path `.gitignore` excludes are never
emitted. Each tree
contains exactly the plugins listed in that harness's marketplace manifest.

Frontmatter is the portability boundary, and the frontmatter matrix draws it:
each key carries a placement per harness and a value form. A key placed
`top-level` for one harness and under `metadata` for another is declared once
in a template through the global named after it, and the renderer places it.
"""

import argparse
import functools
import json
import re
import shutil
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import pathspec
from jinja2 import Environment, StrictUndefined, TemplateError

from plugin_maintenance.errors import (
    ActionMatrixShapeError,
    BuildError,
    CallableFlagError,
    CallableNameError,
    DevFileTemplateError,
    Document,
    DuplicateFrontmatterKeyError,
    FrontmatterMatrixShapeError,
    InvocationWrapperError,
    LineBreakError,
    ManifestShapeError,
    MissingPluginError,
    PlaceholderNameError,
    PlacementError,
    PlainScalarError,
    TemplateConflictError,
    TemplateRenderError,
    UndocumentedFormError,
    UnknownHarnessError,
    UnmappedActionError,
    UnreadableDocumentError,
    UnwritableFormError,
)


class Harness(StrEnum):
    """The one list of harnesses; each value is its key in both matrices."""

    CLAUDE_CODE = "ClaudeCode"
    CODEX = "Codex"


MATRIX_PATH = Path("plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/references/harness-action-matrix.json")
# The frontmatter matrix sits beside the action matrix, so overriding one path
# in a test moves both.
FRONTMATTER_MATRIX_NAME = "harness-frontmatter-matrix.json"
IGNORE_FILE = Path(".gitignore")
DEV_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "README.md"}
TEMPLATE_SUFFIX = ".j2"
FRONTMATTER = re.compile(r"\A---\n(?P<body>.*?\n)---\n", re.DOTALL)
TOP_LEVEL_KEY = re.compile(r"\A(?P<key>[A-Za-z_][\w.-]*):")
METADATA_KEY = "metadata:"
# A named argument becomes a `$name` placeholder, so the name is limited to
# what a placeholder can spell without swallowing the text that follows it.
ARGUMENT_NAME = re.compile(r"\A[a-z][a-z0-9_]*\Z")
# Characters that make YAML read a plain scalar as something other than text.
YAML_INDICATORS = set("*&!|>%@`{}[],#\"'?")

CLAUDE_PLUGIN_DIR = ".claude-plugin"
CODEX_PLUGIN_DIR = ".codex-plugin"
HARNESS_METADATA_DIRS = {
    Harness.CLAUDE_CODE: CLAUDE_PLUGIN_DIR,
    Harness.CODEX: CODEX_PLUGIN_DIR,
}
PLUGIN_METADATA_DIRS = set(HARNESS_METADATA_DIRS.values())
HARNESS_MANIFESTS = {
    Harness.CLAUDE_CODE: Path(CLAUDE_PLUGIN_DIR) / "marketplace.json",
    Harness.CODEX: Path(".agents/plugins/marketplace.json"),
}
DIST_DIRS = {
    Harness.CLAUDE_CODE: Path("dist/claude-code"),
    Harness.CODEX: Path("dist/codex"),
}
# Codex reads a skill's UI and invocation policy from `agents/openai.yaml`;
# Claude Code never reads it, so its tree never carries it.
FOREIGN_SKILL_FILES = {
    Harness.CLAUDE_CODE: ("skills/*/agents/openai.yaml",),
    Harness.CODEX: (),
}


class ActionMap(Mapping):
    """Action key -> callable name; a missing key names the action and harness."""

    def __init__(self, names: dict[str, str], harness: str) -> None:
        """Map action keys to callable names for `harness`."""
        self._names = names
        self._harness = harness

    def __getitem__(self, key: str) -> str:
        """Return the callable name, or raise UnmappedActionError."""
        try:
            return self._names[key]
        except KeyError:
            raise UnmappedActionError(key, self._harness) from None

    def __iter__(self):
        """Iterate over the mapped action keys."""
        return iter(self._names)

    def __len__(self) -> int:
        """Return the number of mapped actions."""
        return len(self._names)


def load_matrix(matrix_path: Path) -> dict:
    """Load the harness action matrix and validate its shape."""
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UnreadableDocumentError(Document.ACTION_MATRIX, matrix_path, error) from error

    assistants = matrix.get("assistants")
    actions = matrix.get("actions")
    if not isinstance(assistants, dict) or not assistants or not isinstance(actions, dict):
        raise ActionMatrixShapeError(matrix_path)
    for assistant_key, assistant in assistants.items():
        wrapper = assistant.get("invocation_wrapper")
        if not isinstance(wrapper, str) or wrapper.count("{name}") != 1:
            raise InvocationWrapperError(matrix_path, assistant_key)
    for action_key, action in actions.items():
        if not isinstance(action.get("callable"), bool):
            raise CallableFlagError(matrix_path, action_key)
        if not action["callable"]:
            continue
        for assistant_key in assistants:
            name = action.get(assistant_key, {}).get("name")
            if not isinstance(name, str) or not name:
                raise CallableNameError(matrix_path, action_key, assistant_key)
    return matrix


def manifest_plugin_names(manifest_path: Path) -> list[str]:
    """Return the plugin names a marketplace manifest lists."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UnreadableDocumentError(Document.MANIFEST, manifest_path, error) from error

    plugins = manifest.get("plugins")
    if not isinstance(plugins, list) or not all(
        isinstance(entry, dict) and isinstance(entry.get("name"), str) for entry in plugins
    ):
        raise ManifestShapeError(manifest_path)
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
    patterns = ignore_file.read_text(encoding="utf-8").splitlines() if ignore_file.is_file() else []
    spec = pathspec.GitIgnoreSpec.from_lines(patterns)
    return lambda path: spec.match_file(path.relative_to(repo_root))


def tree_snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under `root` by content and mode, for comparing two trees."""
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode & 0o777,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


# What stops a value from being a plain YAML scalar, checked in order; the
# first hit names the problem. `{first}` is the value's first character.
PLAIN_SCALAR_HAZARDS: tuple[tuple[str, Callable[[str], bool]], ...] = (
    ("leading or trailing whitespace", lambda value: value != value.strip()),
    ("a line break", lambda value: "\n" in value or "\r" in value),
    ("a key separator", lambda value: ": " in value or value.endswith(":")),
    ("a comment marker", lambda value: " #" in value),
    ("the leading YAML indicator {first!r}", lambda value: value[0] in YAML_INDICATORS),
    ("a leading sequence marker", lambda value: value.startswith("- ")),
)


def _plain_scalar(key: str, value: str | list[str]) -> str:
    """Write the value unquoted, the form the Agent Skills specification shows.

    The specification writes `allowed-tools` unquoted, so the renderer writes
    it unquoted too and refuses a value that would change meaning in that
    position instead of quoting it into a different shape.
    """
    written = value if isinstance(value, str) else " ".join(value)
    if not written:
        return ""

    for hazard, applies in PLAIN_SCALAR_HAZARDS:
        if applies(written):
            raise PlainScalarError(key, written, hazard.format(first=written[0]))
    return written


def _quoted_scalar(key: str, value: str | list[str]) -> str:
    """Write the value double-quoted, so YAML reads it as one string.

    A hint describes an argument list, so it reaches for the characters YAML
    claims: `argument-hint: [file] [format]` parses as a two-item list, and a
    hint that explains itself after a colon parses as a nested key.
    """
    written = value if isinstance(value, str) else " ".join(value)
    if not written:
        return ""

    if "\n" in written or "\r" in written:
        raise LineBreakError(key, written)
    escaped = written.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _placeholder_names(key: str, value: str | list[str]) -> str:
    """Write names that can each spell a `$name` placeholder."""
    names = value.split() if isinstance(value, str) else list(value)
    if not names:
        return ""

    for name in names:
        if not ARGUMENT_NAME.match(name):
            raise PlaceholderNameError(key, name)
    return " ".join(names)


VERBATIM_FORM = "verbatim"
VALUE_FORMS: dict[str, Callable[[str, str | list[str]], str]] = {
    "plain-scalar": _plain_scalar,
    "quoted-scalar": _quoted_scalar,
    "placeholder-names": _placeholder_names,
}
PLACEMENTS = {"top-level", "metadata"}


def frontmatter_key(placement: str, key: str, form: str, value: str | list[str]) -> str:
    """Write one frontmatter key where the target harness reads it.

    `top-level` is for a harness that reads the key itself. `metadata` is for
    one that does not: the key travels in the free-form map every harness
    accepts, rather than sitting at the top level as a key the harness never
    asked for. An empty value emits no key at all.

    Placement, key and form are bound when the global is registered, so a
    template passes the value alone and cannot branch on the harness.
    """
    written = VALUE_FORMS[form](key, value)
    if not written:
        return ""
    if placement == "metadata":
        return f"{METADATA_KEY}\n  {key}: {written}"
    return f"{key}: {written}"


def load_frontmatter_matrix(matrix_path: Path) -> dict:
    """Load the frontmatter matrix and check every element the renderer uses."""
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UnreadableDocumentError(Document.FRONTMATTER_MATRIX, matrix_path, error) from error

    keys = matrix.get("keys")
    assistants = matrix.get("assistants")
    forms = matrix.get("forms")
    if (
        not isinstance(keys, dict)
        or not keys
        or not isinstance(assistants, dict)
        or not isinstance(matrix.get("metadata_namespaces"), dict)
        or not isinstance(forms, dict)
    ):
        raise FrontmatterMatrixShapeError(matrix_path)

    for key, entry in keys.items():
        form = entry.get("form")
        if form not in forms:
            raise UndocumentedFormError(matrix_path, key, form)
        if form != VERBATIM_FORM and form not in VALUE_FORMS:
            raise UnwritableFormError(matrix_path, key, form)
        for assistant_key in assistants:
            placement = entry.get(assistant_key, {}).get("placement")
            if placement not in PLACEMENTS:
                raise PlacementError(matrix_path, key, assistant_key, placement, PLACEMENTS)
    return matrix


def frontmatter_lines(text: str) -> list[str] | None:
    """Return the frontmatter block's lines, or None when there is none."""
    match = FRONTMATTER.match(text)
    return match.group("body").splitlines() if match else None


def merge_metadata_blocks(text: str) -> str:
    """Fold every frontmatter `metadata:` block into the first one.

    `allowed_tools` emits its own block for Codex, so a skill that also
    hand-writes `metadata:` would render a duplicate YAML key. Each entry line
    crosses over exactly as authored. A file with one block is returned
    unchanged, which keeps the step invisible to every existing template.
    """
    match = FRONTMATTER.match(text)
    if not match:
        return text

    lines = match.group("body").splitlines()
    heads = [index for index, line in enumerate(lines) if line == METADATA_KEY]
    if len(heads) < 2:  # ruff: ignore[magic-value-comparison] - a single block needs no merge
        return text

    bodies: dict[int, list[str]] = {}
    consumed: set[int] = set()
    for head in heads:
        end = head + 1
        while end < len(lines) and (not lines[end] or lines[end].startswith(" ")):
            end += 1
        bodies[head] = lines[head + 1 : end]
        consumed.update(range(head, end))

    merged: list[str] = []
    for index, line in enumerate(lines):
        if index == heads[0]:
            merged.append(METADATA_KEY)
            for head in heads:
                merged.extend(bodies[head])
        elif index not in consumed:
            merged.append(line)

    return text.replace(match.group("body"), "\n".join(merged) + "\n", 1)


def duplicate_frontmatter_key(text: str) -> str | None:
    """Return the first frontmatter key that appears twice, or None."""
    lines = frontmatter_lines(text)
    if lines is None:
        return None

    seen: set[str] = set()
    for line in lines:
        match = TOP_LEVEL_KEY.match(line)
        if not match:
            continue
        key = match.group("key")
        if key in seen:
            return key
        seen.add(key)
    return None


@dataclass(frozen=True)
class RenderContext:
    """What every plugin of one harness's render shares."""

    harness: Harness
    environment: Environment
    variables: dict
    is_ignored: Callable[[Path], bool]


def _render_context(repo_root: Path, harness: str, matrix_file: Path) -> RenderContext:
    """Load both matrices, check `harness` against them, and build its Jinja environment."""
    matrix = load_matrix(matrix_file)
    frontmatter_matrix = load_frontmatter_matrix(matrix_file.with_name(FRONTMATTER_MATRIX_NAME))

    known_assistants = set(matrix["assistants"]) & set(frontmatter_matrix["assistants"])
    if harness not in known_assistants or harness not in HARNESS_MANIFESTS:
        raise UnknownHarnessError(harness, sorted(known_assistants & set(HARNESS_MANIFESTS)))
    harness = Harness(harness)

    # Templates render Markdown, YAML and scripts, never HTML: escaping would corrupt them.
    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True, autoescape=False)  # ruff: ignore[jinja2-autoescape-false]
    wrapper = matrix["assistants"][harness]["invocation_wrapper"]
    environment.filters["call"] = lambda name: wrapper.format(name=name)
    # One global per placed key, named after the key. The matrix decides which
    # keys exist and where each lands, so adding a key is a data change.
    for key, entry in frontmatter_matrix["keys"].items():
        if entry["form"] == VERBATIM_FORM:
            continue
        # ty infers `globals` from jinja's default namespace; any callable is a valid global.
        environment.globals[key.replace("-", "_")] = functools.partial(  # ty: ignore[invalid-assignment]
            frontmatter_key, entry[harness]["placement"], key, entry["form"]
        )
    variables = {
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
    return RenderContext(harness, environment, variables, ignored_path(repo_root))


def _render_template(render: RenderContext, source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    try:
        rendered = render.environment.from_string(text).render(**render.variables)
    except BuildError:
        raise
    except TemplateError as error:
        raise TemplateRenderError(source, render.harness, error) from error

    rendered = merge_metadata_blocks(rendered)
    duplicate = duplicate_frontmatter_key(rendered)
    if duplicate:
        raise DuplicateFrontmatterKeyError(source, render.harness, duplicate)
    return rendered


def _render_plugin(render: RenderContext, source_dir: Path, target_dir: Path) -> None:
    foreign_metadata = PLUGIN_METADATA_DIRS - {HARNESS_METADATA_DIRS[render.harness]}
    for source in sorted(source_dir.rglob("*")):
        relative = source.relative_to(source_dir)
        if foreign_metadata.intersection(relative.parts) or source.is_dir():
            continue
        if any(relative.match(pattern) for pattern in FOREIGN_SKILL_FILES[render.harness]):
            continue
        if render.is_ignored(source):
            continue
        is_template = source.name.endswith(TEMPLATE_SUFFIX)
        plain_name = source.name[: -len(TEMPLATE_SUFFIX)] if is_template else source.name
        if plain_name in DEV_FILE_NAMES:
            if is_template:
                raise DevFileTemplateError(source, plain_name)
            continue

        if is_template:
            if source.with_name(plain_name).exists():
                raise TemplateConflictError(source.with_name(plain_name), source)
            target = target_dir / relative.with_name(plain_name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_render_template(render, source), encoding="utf-8")
        else:
            target = target_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copymode(source, target)


def render_tree(
    repo_root: Path,
    harness: Harness,
    output_dir: Path,
    matrix_path: Path | None = None,
    manifest_path: Path | None = None,
) -> None:
    """Render the plugins `harness`'s manifest lists into `output_dir`, replacing it atomically."""
    repo_root = Path(repo_root)
    render = _render_context(repo_root, harness, Path(matrix_path) if matrix_path else repo_root / MATRIX_PATH)

    manifest = Path(manifest_path) if manifest_path else repo_root / HARNESS_MANIFESTS[render.harness]
    plugin_names = manifest_plugin_names(manifest)
    for plugin_name in plugin_names:
        source_dir = repo_root / "plugins" / plugin_name
        if not source_dir.is_dir():
            raise MissingPluginError(manifest, plugin_name, source_dir)

    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    # `mkdtemp` always creates its directory 0o700 and `rename` keeps that mode,
    # which would publish a tree that other users cannot traverse. Take the mode
    # of `dist/` itself, so a fresh checkout and a post-build tree agree and the
    # published mode stays a function of the source tree, not of what was there.
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-staging-", dir=output_dir.parent))
    staging.chmod(output_dir.parent.stat().st_mode & 0o777)
    try:
        for plugin_name in plugin_names:
            _render_plugin(render, repo_root / "plugins" / plugin_name, staging / plugin_name)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    if output_dir.is_dir():
        shutil.rmtree(output_dir)
    elif output_dir.exists():
        output_dir.unlink()
    staging.rename(output_dir)


def main(argv: list[str] | None = None) -> None:
    """Render one harness tree from the command line."""
    parser = argparse.ArgumentParser(description="Render plugins/ into one harness-specific dist tree.")
    parser.add_argument("--harness", required=True, choices=list(Harness))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        render_tree(args.repo_root, args.harness, args.output)
    except BuildError as error:
        # SystemExit prints its argument as the process's last word; that is the CLI's contract, not a reusable message.
        raise SystemExit(f"error: {error}") from error  # ruff: ignore[raise-vanilla-args]
    print(f"rendered {args.harness} -> {args.output}")


if __name__ == "__main__":
    main()
