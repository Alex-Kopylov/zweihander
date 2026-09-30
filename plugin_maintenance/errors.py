"""Why a build stops: each error owns its message and takes the facts it names."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Document(StrEnum):
    """A JSON file the renderer reads, named the way its errors name it."""

    ACTION_MATRIX = "action matrix"
    FRONTMATTER_MATRIX = "frontmatter matrix"
    MANIFEST = "marketplace manifest"


class BuildError(Exception):
    """Raised when the build must stop instead of emitting a partial tree."""


@dataclass(eq=False)
class UnreadableDocumentError(BuildError):
    """A JSON input is missing, unreadable, or not JSON."""

    document: Document
    path: Path
    error: Exception

    def __str__(self) -> str:
        """Name the document, its path and the underlying error."""
        return f"cannot load {self.document} {self.path}: {self.error}"


@dataclass(eq=False)
class ActionMatrixShapeError(BuildError):
    """The action matrix lacks its top-level sections."""

    path: Path

    def __str__(self) -> str:
        """Name the sections the matrix needs."""
        return f"malformed action matrix {self.path}: 'assistants' and 'actions' must be non-empty objects"


@dataclass(eq=False)
class InvocationWrapperError(BuildError):
    """An assistant's invocation wrapper is missing or lacks exactly one `{name}` slot."""

    path: Path
    assistant: str

    def __str__(self) -> str:
        """Name the assistant whose wrapper is wrong."""
        return (
            f"malformed action matrix {self.path}: assistant '{self.assistant}' "
            "needs one invocation_wrapper with one {name} slot"
        )


@dataclass(eq=False)
class CallableFlagError(BuildError):
    """An action lacks the boolean `callable` flag."""

    path: Path
    action: str

    def __str__(self) -> str:
        """Name the action missing its flag."""
        return f"malformed action matrix {self.path}: action '{self.action}' is missing the boolean 'callable' flag"


@dataclass(eq=False)
class CallableNameError(BuildError):
    """A callable action has no name for one assistant."""

    path: Path
    action: str
    assistant: str

    def __str__(self) -> str:
        """Name the action and the assistant it has no name for."""
        return (
            f"malformed action matrix {self.path}: callable action '{self.action}' "
            f"has no name for assistant '{self.assistant}'"
        )


@dataclass(eq=False)
class UnmappedActionError(BuildError):
    """A template asks for an action the harness has no callable for."""

    action: str
    harness: str

    def __str__(self) -> str:
        """Name the action and the harness."""
        return f"action '{self.action}' is not mapped for harness '{self.harness}' in the action matrix"


@dataclass(eq=False)
class ManifestShapeError(BuildError):
    """A marketplace manifest lacks a well-formed `plugins` list."""

    path: Path

    def __str__(self) -> str:
        """Name the list the manifest needs."""
        return f"marketplace manifest {self.path} needs a 'plugins' list of objects with 'name'"


@dataclass(eq=False)
class FrontmatterMatrixShapeError(BuildError):
    """The frontmatter matrix lacks its top-level sections."""

    path: Path

    def __str__(self) -> str:
        """Name the sections the matrix needs."""
        return (
            f"malformed frontmatter matrix {self.path}: 'keys' and 'assistants' must be non-empty objects, "
            "'metadata_namespaces' and 'forms' must be objects"
        )


@dataclass(eq=False)
class UndocumentedFormError(BuildError):
    """A key declares a value form the matrix's `forms` section does not document."""

    path: Path
    key: str
    form: object

    def __str__(self) -> str:
        """Name the key and its form."""
        return (
            f"malformed frontmatter matrix {self.path}: key '{self.key}' declares the undocumented form '{self.form}'"
        )


@dataclass(eq=False)
class UnwritableFormError(BuildError):
    """A key declares a documented form the renderer has no writer for."""

    path: Path
    key: str
    form: str

    def __str__(self) -> str:
        """Name the key and its form."""
        return (
            f"malformed frontmatter matrix {self.path}: key '{self.key}' "
            f"declares the form '{self.form}', which the renderer cannot write"
        )


@dataclass(eq=False)
class PlacementError(BuildError):
    """A key gives an assistant a placement the renderer does not know."""

    path: Path
    key: str
    assistant: str
    placement: object
    placements: set[str]

    def __str__(self) -> str:
        """Name the key, the assistant, the placement and the valid ones."""
        return (
            f"malformed frontmatter matrix {self.path}: key '{self.key}' "
            f"gives assistant '{self.assistant}' the placement "
            f"{self.placement!r}; use one of {', '.join(sorted(self.placements))}"
        )


@dataclass(eq=False)
class PlainScalarError(BuildError):
    """A value would change meaning written as an unquoted YAML scalar."""

    key: str
    value: str
    hazard: str

    def __str__(self) -> str:
        """Name the key, the value and what it carries."""
        return f"{self.key} value {self.value!r} cannot be written as a plain YAML scalar: it carries {self.hazard}"


@dataclass(eq=False)
class LineBreakError(BuildError):
    """A value that must fit on one YAML line carries a line break."""

    key: str
    value: str

    def __str__(self) -> str:
        """Name the key and the value."""
        return f"{self.key} value {self.value!r} cannot be written as one YAML line: it carries a line break"


@dataclass(eq=False)
class PlaceholderNameError(BuildError):
    """A name cannot spell a `$name` placeholder."""

    key: str
    name: str

    def __str__(self) -> str:
        """Name the key, the name and the allowed spelling."""
        return (
            f"{self.key} name {self.name!r} cannot spell a `$name` placeholder: use "
            "lowercase letters, digits and underscores, starting with a letter"
        )


@dataclass(eq=False)
class TemplateRenderError(BuildError):
    """Jinja failed to render a template."""

    source: Path
    harness: str
    error: Exception

    def __str__(self) -> str:
        """Name the template, the harness and Jinja's error."""
        return f"failed to render {self.source} for harness '{self.harness}': {self.error}"


@dataclass(eq=False)
class DuplicateFrontmatterKeyError(BuildError):
    """A rendered file's frontmatter carries one key twice."""

    source: Path
    harness: str
    key: str

    def __str__(self) -> str:
        """Name the template, the harness and the repeated key."""
        return f"{self.source} rendered for harness '{self.harness}' carries two '{self.key}:' keys in its frontmatter"


@dataclass(eq=False)
class DevFileTemplateError(BuildError):
    """A template would emit a development file the renderer never ships."""

    source: Path
    name: str

    def __str__(self) -> str:
        """Name the template and the file it would emit."""
        return (
            f"{self.source} would emit the development file {self.name}, "
            "which is never shipped; author it as a plain file"
        )


@dataclass(eq=False)
class TemplateConflictError(BuildError):
    """Both a plain file and its template exist."""

    plain: Path
    template: Path

    def __str__(self) -> str:
        """Name both files."""
        return f"both {self.plain} and {self.template} exist; keep exactly one"


@dataclass(eq=False)
class UnknownHarnessError(BuildError):
    """The requested harness is missing from a matrix or from the manifest table."""

    harness: str
    known: list[str]

    def __str__(self) -> str:
        """Name the harness and the supported ones."""
        return f"unknown harness '{self.harness}'; supported harnesses: {', '.join(self.known)}"


@dataclass(eq=False)
class MissingPluginError(BuildError):
    """A manifest lists a plugin with no source directory."""

    manifest: Path
    plugin: str
    source_dir: Path

    def __str__(self) -> str:
        """Name the manifest, the plugin and the missing directory."""
        return f"manifest {self.manifest} lists plugin '{self.plugin}' but {self.source_dir} does not exist"
