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
Files named `AGENTS.md`, `CLAUDE.md`, or `README.md` under `plugins/` are authoring-time files; the renderer SHALL NOT emit them into either harness tree.

#### Scenario: Dev files absent from dist
- **WHEN** the full build completes
- **THEN** neither `dist/` tree contains a file named `AGENTS.md`, `CLAUDE.md`, or `README.md`

### Requirement: Build fails loudly
The build SHALL fail — without falling back to another harness's values — on: an unknown harness key, an action or name missing from the matrix, a malformed matrix, a template render error, leftover Jinja markers in a rendered file (one emitted from a `.j2` source; output of `{% raw %}` blocks is exempt), or a plain/template collision.

#### Scenario: Missing action aborts the build
- **WHEN** a template references an action absent from the matrix for the target harness
- **THEN** the build fails with an error naming the action and harness, and emits no partial tree for silent use

#### Scenario: Unknown harness aborts the build
- **WHEN** the renderer is invoked with a harness key not present in the matrix
- **THEN** the build fails before rendering any file

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

### Requirement: Deterministic rendering
Rendering SHALL be deterministic: identical source, matrix, and harness inputs SHALL produce byte-identical output trees.

#### Scenario: Consecutive renders identical
- **WHEN** the full build runs twice with no intervening changes
- **THEN** the two `dist/` outputs are byte-identical
