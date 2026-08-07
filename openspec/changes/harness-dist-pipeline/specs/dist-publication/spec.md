# dist-publication

## Purpose

Makes the committed `dist/` trees the published installable source for both marketplaces and keeps them provably in sync with the authored sources.

## ADDED Requirements

### Requirement: Marketplace manifests point at dist trees
`.claude-plugin/marketplace.json` SHALL source every plugin it lists from `./dist/claude-code/<plugin-name>`, and `.agents/plugins/marketplace.json` SHALL source every plugin it lists from `./dist/codex/<plugin-name>`. No manifest entry SHALL point into `plugins/`. Each manifest is the catalog authority for its harness; the two manifests MAY list different plugin sets.

#### Scenario: Manifest paths resolve into dist
- **WHEN** either marketplace manifest is read
- **THEN** every plugin source path points into the manifest's own `dist/` tree and resolves to an existing directory

#### Scenario: Codex-only plugin is a valid catalog divergence
- **WHEN** a plugin appears in `.agents/plugins/marketplace.json` but not in `.claude-plugin/marketplace.json`
- **THEN** its source path resolves under `dist/codex/` and no `dist/claude-code/` directory exists for it

### Requirement: Committed dist equals a fresh build
The committed `dist/` trees SHALL always equal the output of a full build from the committed sources, and continuous integration SHALL reject changes where they differ.

#### Scenario: Stale dist fails CI
- **WHEN** a pull request changes files under `plugins/` without re-rendering `dist/`
- **THEN** the freshness check fails

#### Scenario: Fresh dist passes CI
- **WHEN** a pull request includes source changes together with the matching re-rendered `dist/` output
- **THEN** the freshness check passes

### Requirement: Scheduled generation publishes through a pull request
Any automated job that regenerates content under `plugins/` SHALL run the full build afterwards and SHALL open a pull request carrying the source and `dist/` changes together — no direct pushes to the default branch. The pull request SHALL pass the standard CI gate before merge.

#### Scenario: Weekly mermaid sync opens a combined PR
- **WHEN** the scheduled mermaid documentation sync changes files under `plugins/mermaid-diagrams/`
- **THEN** it opens a pull request containing those changes together with the corresponding re-rendered files under both `dist/` trees
