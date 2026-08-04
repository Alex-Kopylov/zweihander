# dist-publication

## Purpose

Makes the committed `dist/` trees the published installable source for both marketplaces and keeps them provably in sync with the authored sources.

## ADDED Requirements

### Requirement: Marketplace manifests point at dist trees
`.claude-plugin/marketplace.json` SHALL source every plugin from `./dist/claude-code/<plugin-name>`, and `.agents/plugins/marketplace.json` SHALL source every plugin from `./dist/codex/<plugin-name>`. No manifest entry SHALL point into `plugins/`.

#### Scenario: Manifest paths resolve into dist
- **WHEN** either marketplace manifest is read
- **THEN** every plugin source path points into the manifest's own `dist/` tree and resolves to an existing directory

### Requirement: Committed dist equals a fresh build
The committed `dist/` trees SHALL always equal the output of a full build from the committed sources, and continuous integration SHALL reject changes where they differ.

#### Scenario: Stale dist fails CI
- **WHEN** a pull request changes files under `plugins/` without re-rendering `dist/`
- **THEN** the freshness check fails

#### Scenario: Fresh dist passes CI
- **WHEN** a pull request includes source changes together with the matching re-rendered `dist/` output
- **THEN** the freshness check passes

### Requirement: Scheduled generation keeps dist current
Any automated job that regenerates content under `plugins/` SHALL run the distribution stage afterwards and commit the resulting `dist/` changes together with the source changes.

#### Scenario: Weekly mermaid sync updates dist in the same commit
- **WHEN** the scheduled mermaid documentation sync changes files under `plugins/mermaid-diagrams/`
- **THEN** the commit it pushes also contains the corresponding re-rendered files under both `dist/` trees
