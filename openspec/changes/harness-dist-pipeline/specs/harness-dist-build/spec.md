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
Stage 1 SHALL execute the build entrypoint of every plugin that declares one, in-place under `plugins/<name>/`, and the pipeline SHALL NOT special-case any individual plugin name.

#### Scenario: New generated plugin joins the class
- **WHEN** a plugin declares a build entrypoint following the documented convention
- **THEN** stage 1 executes it during the next full build without pipeline changes specific to that plugin

#### Scenario: Mermaid generator runs as a class member
- **WHEN** the full build runs
- **THEN** the `mermaid-diagrams` generator executes through the same class mechanism as any other generated plugin

### Requirement: Template and plain-file rules
For every output path `X`, the renderer SHALL apply exactly one of: copy `X` byte-for-byte when only `X` exists in source; render `X.j2` with the harness context and emit it as `X` when only `X.j2` exists; fail the build when both `X` and `X.j2` exist.

#### Scenario: Plain file copied byte-for-byte
- **WHEN** a source file without a `.j2` suffix contains literal `{{` or `{%` sequences
- **THEN** the emitted file is byte-identical to the source, including those sequences

#### Scenario: Template rendered per harness
- **WHEN** `SKILL.md.j2` exists and the build renders a harness tree
- **THEN** the tree contains `SKILL.md` with all Jinja markers resolved and contains no `SKILL.md.j2`

#### Scenario: Collision fails the build
- **WHEN** both `SKILL.md` and `SKILL.md.j2` exist in the same source directory
- **THEN** the build fails and names the colliding path

### Requirement: Complete tree per harness
The renderer SHALL emit one complete installable tree per supported harness, containing every plugin in the catalog, including plugins with no templates.

#### Scenario: Harness-agnostic plugin ships in both trees
- **WHEN** a plugin contains no `.j2` files and the full build runs
- **THEN** the plugin appears complete in both `dist/claude-code/` and `dist/codex/`

### Requirement: Foreign runtime metadata stripped
Each harness tree SHALL contain only its own runtime plugin metadata: no `.codex-plugin/` directory under `dist/claude-code/**` and no `.claude-plugin/` directory under `dist/codex/**`.

#### Scenario: Metadata filtered per tree
- **WHEN** the full build completes
- **THEN** `dist/claude-code/**` contains no `.codex-plugin/` directory and `dist/codex/**` contains no `.claude-plugin/` directory

### Requirement: Build fails loudly
The build SHALL fail — without falling back to another harness's values — on: an unknown harness key, an action or name missing from the matrix, a malformed matrix, a template render error, leftover Jinja markers in a rendered file, or a plain/template collision.

#### Scenario: Missing action aborts the build
- **WHEN** a template references an action absent from the matrix for the target harness
- **THEN** the build fails with an error naming the action and harness, and emits no partial tree for silent use

#### Scenario: Unknown harness aborts the build
- **WHEN** the renderer is invoked with a harness key not present in the matrix
- **THEN** the build fails before rendering any file

### Requirement: Rendered output carries no foreign harness vocabulary
Rendered files under `dist/claude-code/**` SHALL contain no Codex-only invocation vocabulary, and rendered files under `dist/codex/**` SHALL contain no Claude Code-only invocation vocabulary.

#### Scenario: Vocabulary scan passes on rendered trees
- **WHEN** the full build completes and rendered files are scanned against the per-harness foreign-vocabulary lists
- **THEN** the scan reports zero matches

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
