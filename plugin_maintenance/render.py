"""Stage-2 renderer: render `plugins/` into one harness-specific tree.

Usage: `uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code`

File rules per output path X: copy X byte-for-byte when only X exists,
render X.j2 into X when only X.j2 exists, fail when both exist. Files named
AGENTS.md/CLAUDE.md/README.md, the other harness's runtime metadata
directory, and every path `.gitignore` excludes are never emitted. Each tree
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
from pathlib import Path
from typing import Literal

import pathspec
from jinja2 import Environment, StrictUndefined, TemplateError

Harness = Literal["ClaudeCode", "Codex"]

MATRIX_PATH = Path(
    "plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness"
    "/references/harness-action-matrix.json"
)
# The frontmatter matrix sits beside the action matrix, so overriding one path
# in a test moves both.
FRONTMATTER_MATRIX_NAME = "harness-frontmatter-matrix.json"
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

FRONTMATTER = re.compile(r"\A---\n(?P<body>.*?\n)---\n", re.DOTALL)
TOP_LEVEL_KEY = re.compile(r"\A(?P<key>[A-Za-z_][\w.-]*):")
METADATA_KEY = "metadata:"
# A named argument becomes a `$name` placeholder, so the name is limited to
# what a placeholder can spell without swallowing the text that follows it.
ARGUMENT_NAME = re.compile(r"\A[a-z][a-z0-9_]*\Z")
# Characters that make YAML read a plain scalar as something other than text.
YAML_INDICATORS = set("*&!|>%@`{}[],#\"'?")

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


def _plain_scalar_problem(value: str) -> str | None:
    """Name what stops `value` from being a plain YAML scalar, or return None.

    The Agent Skills specification writes `allowed-tools` unquoted, so the
    renderer writes it unquoted too and refuses a value that would change
    meaning in that position instead of quoting it into a different shape.
    """
    if value != value.strip():
        return "leading or trailing whitespace"
    if "\n" in value or "\r" in value:
        return "a line break"
    if ": " in value or value.endswith(":"):
        return "a key separator"
    if " #" in value:
        return "a comment marker"
    if value[0] in YAML_INDICATORS:
        return f"the leading YAML indicator {value[0]!r}"
    if value.startswith("- "):
        return "a leading sequence marker"
    return None


def _plain_scalar(key: str, value: str | list[str]) -> str:
    """Write the value unquoted, the form the Agent Skills specification shows."""
    written = value if isinstance(value, str) else " ".join(value)
    if not written:
        return ""

    problem = _plain_scalar_problem(written)
    if problem:
        raise BuildError(
            f"{key} value {written!r} cannot be written as a plain YAML "
            f"scalar: it carries {problem}"
        )
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
        raise BuildError(
            f"{key} value {written!r} cannot be written as one YAML line: "
            "it carries a line break"
        )
    escaped = written.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _placeholder_names(key: str, value: str | list[str]) -> str:
    """Write names that can each spell a `$name` placeholder."""
    names = value.split() if isinstance(value, str) else list(value)
    if not names:
        return ""

    for name in names:
        if not ARGUMENT_NAME.match(name):
            raise BuildError(
                f"{key} name {name!r} cannot spell a `$name` placeholder: use "
                "lowercase letters, digits and underscores, starting with a "
                "letter"
            )
    return " ".join(names)


VERBATIM_FORM = "verbatim"
VALUE_FORMS: dict[str, Callable[[str, str | list[str]], str]] = {
    "plain-scalar": _plain_scalar,
    "quoted-scalar": _quoted_scalar,
    "placeholder-names": _placeholder_names,
}
PLACEMENTS = {"top-level", "metadata"}


def frontmatter_key(
    placement: str, key: str, form: str, value: str | list[str]
) -> str:
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
        raise BuildError(
            f"cannot load frontmatter matrix {matrix_path}: {error}"
        ) from error

    keys = matrix.get("keys")
    assistants = matrix.get("assistants")
    forms = matrix.get("forms")
    if not isinstance(keys, dict) or not keys or not isinstance(assistants, dict):
        raise BuildError(
            f"malformed frontmatter matrix {matrix_path}: "
            "'keys' and 'assistants' must be non-empty objects"
        )
    if not isinstance(matrix.get("metadata_namespaces"), dict) or not isinstance(
        forms, dict
    ):
        raise BuildError(
            f"malformed frontmatter matrix {matrix_path}: "
            "'metadata_namespaces' and 'forms' must be objects"
        )

    for key, entry in keys.items():
        form = entry.get("form")
        if form not in forms:
            raise BuildError(
                f"malformed frontmatter matrix {matrix_path}: key '{key}' "
                f"declares the undocumented form '{form}'"
            )
        if form != VERBATIM_FORM and form not in VALUE_FORMS:
            raise BuildError(
                f"malformed frontmatter matrix {matrix_path}: key '{key}' "
                f"declares the form '{form}', which the renderer cannot write"
            )
        for assistant_key in assistants:
            placement = entry.get(assistant_key, {}).get("placement")
            if placement not in PLACEMENTS:
                raise BuildError(
                    f"malformed frontmatter matrix {matrix_path}: key '{key}' "
                    f"gives assistant '{assistant_key}' the placement "
                    f"{placement!r}; use one of {', '.join(sorted(PLACEMENTS))}"
                )
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
    if len(heads) < 2:
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


def _render_template(
    source: Path, environment: Environment, context: dict, harness: Harness
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

    rendered = merge_metadata_blocks(rendered)
    duplicate = duplicate_frontmatter_key(rendered)
    if duplicate:
        raise BuildError(
            f"{source} rendered for harness '{harness}' carries two "
            f"'{duplicate}:' keys in its frontmatter"
        )
    return rendered


def _render_plugin(
    source_dir: Path,
    target_dir: Path,
    environment: Environment,
    context: dict,
    harness: Harness,
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
    harness: Harness,
    output_dir: Path,
    matrix_path: Path | None = None,
    manifest_path: Path | None = None,
) -> None:
    repo_root = Path(repo_root)
    matrix_file = Path(matrix_path) if matrix_path else repo_root / MATRIX_PATH
    matrix = load_matrix(matrix_file)
    frontmatter_matrix = load_frontmatter_matrix(
        matrix_file.with_name(FRONTMATTER_MATRIX_NAME)
    )

    known_assistants = set(matrix["assistants"]) & set(frontmatter_matrix["assistants"])
    if harness not in known_assistants or harness not in HARNESS_MANIFESTS:
        known = sorted(known_assistants & set(HARNESS_MANIFESTS))
        raise BuildError(
            f"unknown harness '{harness}'; supported harnesses: {', '.join(known)}"
        )

    manifest = Path(manifest_path) if manifest_path else repo_root / HARNESS_MANIFESTS[harness]
    plugin_names = manifest_plugin_names(manifest)
    is_ignored = ignored_path(repo_root)

    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    wrapper = matrix["assistants"][harness]["invocation_wrapper"]
    environment.filters["call"] = lambda name: wrapper.format(name=name)
    # One global per placed key, named after the key. The matrix decides which
    # keys exist and where each lands, so adding a key is a data change.
    for key, entry in frontmatter_matrix["keys"].items():
        if entry["form"] == VERBATIM_FORM:
            continue
        environment.globals[key.replace("-", "_")] = functools.partial(
            frontmatter_key, entry[harness]["placement"], key, entry["form"]
        )
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
