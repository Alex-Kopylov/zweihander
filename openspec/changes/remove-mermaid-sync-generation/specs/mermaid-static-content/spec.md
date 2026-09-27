## Purpose

Keep Mermaid diagram authoring and validation available with bundled reference documentation, without maintaining automated upstream documentation synchronization or Mermaid-specific build generation.

## ADDED Requirements

### Requirement: Mermaid documentation has no automatic maintenance interface
The repository SHALL provide neither a scheduled nor a manually dispatched Mermaid documentation synchronization workflow. It SHALL provide no Mermaid-specific documentation generator or sync command. Ordinary builds SHALL neither fetch Mermaid documentation nor rewrite its authored skills, reference files, indexes, or provenance metadata.

#### Scenario: Build preserves the static snapshot
- **WHEN** a maintainer runs the full build from a clean checkout without an upstream Mermaid checkout
- **THEN** the build succeeds without upstream access and leaves the authored Mermaid plugin unchanged

#### Scenario: Upstream adds a diagram type
- **WHEN** upstream Mermaid documentation adds or changes a diagram type
- **THEN** this repository starts no automatic documentation update, generation run, or sync pull request

#### Scenario: Removed commands have no compatibility interface
- **WHEN** a maintainer looks for the former Mermaid sync or generated-documentation command
- **THEN** no supported command, forwarding wrapper, or workflow dispatch remains

### Requirement: Installed Mermaid capabilities remain usable
Both marketplaces SHALL continue to publish `mermaid-diagrams` with the `mermaid` and `mermaid-lint` skills. The removal SHALL preserve the existing syntax and configuration reference snapshot, the choice-report asset, and the lint result schema. Skill links to these local resources SHALL resolve in each rendered plugin. Runtime diagram creation, `mmdc` validation, and missing-dependency reporting SHALL retain their existing behavior.

#### Scenario: User installs either distribution
- **WHEN** a user installs `mermaid-diagrams` from either marketplace after the removal
- **THEN** both skills and their existing references, asset, and lint schema are available under the published plugin

#### Scenario: User follows a skill resource link
- **WHEN** a user follows a local resource link from either rendered Mermaid skill
- **THEN** the target resolves inside that rendered plugin

### Requirement: Static content has accurate ownership and provenance
Plugin descriptions and documentation SHALL describe bundled reference documentation without claiming recurring synchronization or automatic index generation. The editable skill index and plugin README SHALL carry no markers assigning their maintenance to the removed generator. The existing snapshot's source, recorded commit and date, modification notice, and license material SHALL remain available; runtime attribution SHALL ship inside each distribution.

#### Scenario: Snapshot identity survives removal
- **WHEN** synchronization and generation tooling are removed
- **THEN** the bundled notice retains the previously recorded source commit and date without replacing them with the removal date

#### Scenario: Maintainer edits the skill index
- **WHEN** a maintainer updates the authored Mermaid skill index and runs the full build
- **THEN** the build preserves the edit and publishes it through normal distribution rendering
