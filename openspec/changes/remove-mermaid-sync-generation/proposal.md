## Why

Automatic Mermaid documentation synchronization and its generated indexes now cost more maintenance than they provide. Remove that machinery while keeping the installed diagram authoring and linting skills useful.

## What Changes

- **BREAKING for maintainers:** remove the scheduled/manual sync workflow and the entire Mermaid generator package, including its module commands, templates, navigation snapshot, and environment-variable interface. Do not provide replacement commands or compatibility wrappers.
- Keep `mermaid-diagrams` in both marketplaces. Keep `mermaid`, `mermaid-lint`, bundled syntax/config references, the choice-report asset, and the lint schema.
- Treat the current bundled documentation as a static snapshot. Maintain the skill index directly, remove generated-block markers and recurring-sync claims, and preserve snapshot attribution and licenses.
- Retire checks specific to synchronization or generated Mermaid metadata. Keep shared build checks and compact checks of the installed plugin's integrity.
- Keep the general two-stage build. Stage 1 may have no generators; stage 2 still renders both distributions and checks freshness.

Scope assumption: “generation and checking” refers to documentation upkeep. Runtime diagram creation and `mmdc` validation remain unchanged. Removing the entire plugin or changing its runtime validation requires a separate decision.

## Capabilities

### New Capabilities

- `mermaid-static-content`: ship usable Mermaid skills and a static reference snapshot without an upstream synchronization or documentation-generation interface.

### Modified Capabilities

- `harness-dist-build`: replace the requirement that Mermaid has a generator with a generic zero-generator scenario; preserve generator discovery and build ordering.
- `dist-publication`: remove the weekly Mermaid scenario while retaining the publication rules for any other automated generation job.

## Impact

Removal touches `.github/workflows/sync-mermaid-docs.yml`, `plugin_maintenance/generators/mermaid_diagrams/`, and the generator-specific tests. Content changes touch Mermaid skill/catalog descriptions, the root and plugin README files, `AGENTS.md`, and provenance wording. Both runtime manifests and relevant version fields must follow the repository release policy. A later implementation rebuilds both `dist/` trees; it does not edit them directly.

This change is planning only. Its branch starts from PR #68 (`harness-dist-pipeline`), and its separate planning PR targets that branch. The proposal does not execute removals or alter historical OpenSpec changes.
