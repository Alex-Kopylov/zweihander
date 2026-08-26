# harness-dist-build

## Purpose

Turns the authored `plugins/` tree into one complete, installable, harness-specific plugin tree per supported harness under `dist/`, through a two-stage build: per-plugin content generation, then per-harness template rendering.

## ADDED Requirements

### Requirement: Two-stage build order
The build SHALL run generation (stage 1) before distribution (stage 2), and stage 2 SHALL consume the `plugins/` tree exactly as stage 1 left it.

#### Scenario: Generator output reaches dist
- **WHEN** a generated plugin's build script updates files under `plugins/<name>/` and the full build runs
- **THEN** both `dist/` trees contain content derived from the updated files

### Requirement: Generated plugins are a declared class
Stage 1 SHALL execute the generator of every plugin that declares one, in-place under `plugins/<name>/`, and the pipeline SHALL NOT special-case any individual plugin name. A generator is a package under the root maintenance directory's `generators/` folder, named for its plugin, exposing a zero-argument `generate()` entrypoint. Generators SHALL be offline, idempotent, and deterministic; fetching external content happens outside the build.

#### Scenario: New generated plugin joins the class
- **WHEN** a plugin declares a generator package following this convention
- **THEN** stage 1 executes it during the next full build without pipeline changes specific to that plugin

#### Scenario: Mermaid generator runs as a class member
- **WHEN** the full build runs
- **THEN** the `mermaid-diagrams` generator executes through the same class mechanism as any other generated plugin

### Requirement: Template and plain-file rules
For every output path `X`, the renderer SHALL apply exactly one of: copy `X` byte-for-byte when only `X` exists in source; render `X.j2` with the harness context and emit it as `X` when only `X.j2` exists; fail the build when both `X` and `X.j2` exist. Emitted files SHALL preserve the source file's mode bits. A template whose output needs literal `{{` or `{%` SHALL wrap that content in `{% raw %}` blocks.

#### Scenario: Plain file copied byte-for-byte
- **WHEN** a source file without a `.j2` suffix contains literal `{{` or `{%` sequences
- **THEN** the emitted file is byte-identical to the source, including those sequences

#### Scenario: Template rendered per harness
- **WHEN** `SKILL.md.j2` exists and the build renders a harness tree
- **THEN** the tree contains `SKILL.md` with all Jinja markers resolved and contains no `SKILL.md.j2`

#### Scenario: Raw block emits literal braces
- **WHEN** a `.j2` source wraps `{{COMPANY}}` in a `{% raw %}` block and the build renders it
- **THEN** the emitted file contains literal `{{COMPANY}}` and the build succeeds

#### Scenario: Collision fails the build
- **WHEN** both `SKILL.md` and `SKILL.md.j2` exist in the same source directory
- **THEN** the build fails and names the colliding path

#### Scenario: Executable bit survives the copy
- **WHEN** a source script with the executable bit set is emitted into a harness tree
- **THEN** the emitted file is executable

### Requirement: Complete tree per harness, membership from the harness's manifest
The renderer SHALL emit one complete installable tree per supported harness, containing exactly the plugins listed in that harness's marketplace manifest — including plugins with no templates — and no others. The two catalogs MAY list different plugin sets.

#### Scenario: Harness-agnostic plugin ships in both trees
- **WHEN** a plugin listed in both marketplace manifests contains no `.j2` files and the full build runs
- **THEN** the plugin appears complete in both `dist/claude-code/` and `dist/codex/`

#### Scenario: Single-harness plugin ships to its harness only
- **WHEN** a plugin is listed in the Codex manifest but not the Claude Code manifest and the full build runs
- **THEN** `dist/codex/` contains the plugin and `dist/claude-code/` contains no directory for it

### Requirement: Foreign runtime metadata stripped
Each harness tree SHALL contain only its own runtime plugin metadata: no `.codex-plugin/` directory under `dist/claude-code/**` and no `.claude-plugin/` directory under `dist/codex/**`.

#### Scenario: Metadata filtered per tree
- **WHEN** the full build completes
- **THEN** `dist/claude-code/**` contains no `.codex-plugin/` directory and `dist/codex/**` contains no `.claude-plugin/` directory

### Requirement: Development files excluded
Files named `AGENTS.md`, `CLAUDE.md`, or `README.md` under `plugins/` are authoring-time files; the renderer SHALL NOT emit them into either harness tree. The rule is a predicate on the emitted name, so it SHALL apply to a `.j2` template of a skipped name and SHALL NOT apply to a longer name that merely contains one. Runtime context a plugin needs SHALL live in a file the renderer emits: `plugins/<plugin-name>/references/<topic>.md`, linked from the skill that needs it, or the `SKILL.md` itself.

#### Scenario: Dev files absent from dist
- **WHEN** the full build completes
- **THEN** neither `dist/` tree contains a file named `AGENTS.md`, `CLAUDE.md`, or `README.md`

#### Scenario: Dev-file template rejected, not skipped
- **WHEN** a plugin contains `AGENTS.md.j2`, `CLAUDE.md.j2`, or `README.md.j2`
- **THEN** the build fails and names the development file the template would have emitted

#### Scenario: Longer name containing a skipped one still ships
- **WHEN** a plugin contains `templates/AGENTS.md.template`
- **THEN** both `dist/` trees contain that file

#### Scenario: Plugin runtime context reaches the user
- **WHEN** a skill needs shared context that would otherwise sit in a plugin-level `AGENTS.md`
- **THEN** that context ships under the plugin's `references/` directory and the skill's link to it resolves inside each `dist/` tree

### Requirement: Repository-ignored artifacts excluded
The renderer SHALL skip every source path the repository's root `.gitignore` matches, so tooling artifacts that appear under `plugins/` never reach a published tree. The test SHALL read `.gitignore` and SHALL NOT read the git index, because stage 1 writes generated files into `plugins/` before anything commits them.

#### Scenario: Tooling artifact stays out of the tree
- **WHEN** a `__pycache__/` directory exists under a plugin and the full build runs
- **THEN** neither `dist/` tree contains it

#### Scenario: Freshly generated content still ships
- **WHEN** stage 1 writes an uncommitted file under `plugins/` that `.gitignore` does not match
- **THEN** the file appears in every `dist/` tree whose manifest lists that plugin

### Requirement: Build fails loudly
The build SHALL fail — without falling back to another harness's values — on: an unknown harness key, an action or name missing from the matrix, a malformed matrix, a template render error, leftover Jinja markers in a rendered file, a template whose emitted name is a development file, or a plain/template collision. The marker scan SHALL exempt the output of `{% raw %}` blocks per block rather than per file, and SHALL recognise every spelling Jinja accepts for the tag, including the whitespace-control forms.

#### Scenario: Missing action aborts the build
- **WHEN** a template references an action absent from the matrix for the target harness
- **THEN** the build fails with an error naming the action and harness, and emits no partial tree for silent use

#### Scenario: Unknown harness aborts the build
- **WHEN** the renderer is invoked with a harness key not present in the matrix
- **THEN** the build fails before rendering any file

#### Scenario: Whitespace-control raw block emits literal braces
- **WHEN** a `.j2` source wraps literal braces in a `{%- raw -%}` block and the build renders it
- **THEN** the emitted file keeps those braces and the build succeeds

#### Scenario: Marker outside a raw block still fails
- **WHEN** a `.j2` source holds one `{% raw %}` block and an unresolved Jinja marker elsewhere in the same file
- **THEN** the build fails and names the file

### Requirement: Rendered output carries no foreign harness vocabulary
Files rendered from `.j2` sources into `dist/claude-code/**` SHALL contain no Codex callable names, and files rendered from `.j2` sources into `dist/codex/**` SHALL contain no Claude Code callable names. The foreign-name lists SHALL be derived from the matrix's callable names. A spec-level exemption list — successor of the retired `AGNOSTIC_EXEMPT` — SHALL cover files whose subject matter is another harness (seeded with the version-bumper harness reference docs and the action matrix file); exempt files are skipped by the scan.

#### Scenario: Vocabulary scan passes on rendered files
- **WHEN** the full build completes and files rendered from `.j2` sources are scanned against the matrix-derived foreign-name lists
- **THEN** the scan reports zero matches outside the exemption list

### Requirement: Legacy dispatch artifacts absent from output
`dist/` trees SHALL contain no `references/ai-assistant-harnesses/` directories, no harness-dispatch sentences, and no `ai-assistant-harness-adaptation.<harness>` metadata links.

#### Scenario: Dispatch pattern scan passes
- **WHEN** the full build completes
- **THEN** a scan of both trees finds none of the legacy dispatch artifacts

### Requirement: Skill frontmatter is the portability boundary
Rendered frontmatter SHALL carry only keys the target harness accepts, and the frontmatter matrix SHALL be the only source of that judgement. The six fields the Agent Skills specification defines — `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` — are portable and SHALL be placed `top-level` for every harness. A key whose form is `verbatim` MAY be written literally; every other key SHALL be produced by the renderer global named after it, with hyphens turned into underscores. The renderer SHALL register exactly one global per placed key, take the placement from the rendered harness's matrix entry — `top-level` for a key that harness reads, `metadata` for a key it does not read and for a key the product defines as a `metadata` sub-key — and emit no key for an empty value. The renderer SHALL fold every frontmatter `metadata:` block of a rendered file into the first one, and SHALL fail the build on a duplicate of any other frontmatter key.

#### Scenario: A placed key lands where each harness reads it
- **WHEN** a template declares allowed tools through the global and both trees render
- **THEN** the Claude Code file carries a top-level `allowed-tools` key, and the Codex file carries it under `metadata:` and carries no top-level `allowed-tools`

#### Scenario: Placement follows the matrix, not the renderer
- **WHEN** a key's placement for one harness changes in the matrix and that tree renders
- **THEN** the key moves to the new placement with no renderer change

#### Scenario: A key outside the matrix has no global
- **WHEN** a template calls a global named after a key the matrix does not declare
- **THEN** the build fails and names the key

#### Scenario: Hand-written metadata merges instead of duplicating
- **WHEN** a template both declares allowed tools through the global and hand-writes a `metadata:` block
- **THEN** the rendered Codex file contains exactly one `metadata:` key holding the entries of both blocks

#### Scenario: Merge leaves a single-block file untouched
- **WHEN** a rendered file's frontmatter holds one `metadata:` block
- **THEN** the file is byte-identical to the same file rendered before the merge step existed

#### Scenario: Duplicate of another frontmatter key fails the build
- **WHEN** a rendered file's frontmatter holds two `description:` keys
- **THEN** the build fails and names the file and the key

#### Scenario: Hand-written placed key rejected in sources
- **WHEN** a skill or agent source writes a placed key in its frontmatter instead of calling the global
- **THEN** the repository policy check fails and names the file and the key

#### Scenario: Argument keys land where each harness reads them
- **WHEN** a template declares an argument hint and argument names through the globals and both trees render
- **THEN** the Claude Code file carries top-level `argument-hint` and `arguments` keys, and the Codex file carries both under one `metadata:` block and neither at the top level

### Requirement: Frontmatter matrix declares every key's placement and form
The frontmatter matrix SHALL declare, for every frontmatter key the repository writes, one `form` documented in its own `forms` section and one `placement` per assistant. Every non-`verbatim` form SHALL be one the renderer can write, and a `metadata` placement SHALL carry a note recording why the key lives there. The matrix SHALL preserve the key-then-assistant lookup order and SHALL declare the `metadata` namespaces authors may write, none of which repeats a key name. The matrix SHALL name the vendored Agent Skills specification document and the portable keys it defines, and every named portable key SHALL appear in that document. A malformed matrix SHALL fail the build before any file renders.

#### Scenario: Matrix schema holds
- **WHEN** the frontmatter matrix is validated
- **THEN** every key carries a documented form and one placement per assistant, and every `metadata` placement carries its note

#### Scenario: Undocumented form fails the build
- **WHEN** a key declares a form the matrix does not document, or one the renderer cannot write
- **THEN** the build fails and names the key and the form

#### Scenario: Unknown placement fails the build
- **WHEN** a key gives an assistant a placement outside `top-level` and `metadata`
- **THEN** the build fails and names the key and the placement

#### Scenario: Portable keys stay top level in both trees
- **WHEN** the matrix's portable key list is checked against every key's placement
- **THEN** each portable key is placed `top-level` for every assistant

#### Scenario: A product's nested key is metadata-placed everywhere
- **WHEN** a key a product defines as a `metadata` sub-key is looked up for either assistant
- **THEN** its placement is `metadata`, carrying the note that says why

#### Scenario: Vendored specification backs the portable list
- **WHEN** the matrix names a specification document and its portable keys
- **THEN** the document exists beside the matrix and names every one of those keys

### Requirement: Value form decides how a key is written
Each form SHALL write its value one way and fail the build rather than change its meaning. `plain-scalar` writes the value unquoted, joins a list argument with spaces, and fails on a value that would not survive as a plain YAML scalar. `quoted-scalar` writes the value double-quoted with its own quotes escaped and fails on a line break. `placeholder-names` writes a space-separated list of names that can each spell a `$name` placeholder and fails on any other name.

#### Scenario: Quoted form keeps a hint one string
- **WHEN** a template passes the hint `[file] [format]`
- **THEN** the rendered key reads `argument-hint: "[file] [format]"` rather than a YAML list

#### Scenario: Argument name that cannot spell a placeholder fails the build
- **WHEN** a template declares an argument name carrying a space, a capital letter, or a leading digit
- **THEN** the build fails and names the placeholder rule

#### Scenario: Unquotable plain-scalar value fails the build
- **WHEN** a template passes a `plain-scalar` value that cannot be written as a plain YAML scalar
- **THEN** the build fails and names the value

### Requirement: Frontmatter metadata entries carry a namespace
Frontmatter `metadata` entries in every skill and agent source SHALL sit one level deep under a namespace the frontmatter matrix declares — `references`, `agents`, `skills`, `origin`, or `config` — rather than directly under `metadata:`. Entry keys SHALL stay paths or identifiers that resolve relative to the declaring file, except under `config`, whose entries name a skill's own runtime defaults. A key the matrix places also names a `metadata` entry, so the namespace scan SHALL accept it alongside the declared namespaces.

#### Scenario: Namespace scan passes
- **WHEN** every skill and agent source that declares frontmatter metadata is scanned
- **THEN** each entry sits under a declared namespace and no entry sits directly under `metadata:`

#### Scenario: Grouped reference entry still resolves
- **WHEN** a metadata entry under the `references` namespace names a path
- **THEN** that path resolves from the directory of the file declaring it

#### Scenario: Skill default sits under the config namespace
- **WHEN** a skill declares a runtime default such as an output directory
- **THEN** the entry sits under the `config` namespace and the namespace scan passes

### Requirement: Deterministic rendering
Rendering SHALL be deterministic: identical source, matrix, and harness inputs SHALL produce byte-identical output trees.

#### Scenario: Consecutive renders identical
- **WHEN** the full build runs twice with no intervening changes
- **THEN** the two `dist/` outputs are byte-identical
