## 1. Remove the documentation maintenance chain

- [ ] 1.1 Confirm affected paths against the latest PR #68 branch and record the current reference snapshot and runtime assets before editing.
- [ ] 1.2 Delete `.github/workflows/sync-mermaid-docs.yml` and `plugin_maintenance/generators/mermaid_diagrams/` together, including templates and navigation metadata.
- [ ] 1.3 Keep the generic generator package/discovery and two-stage commands; verify that no Mermaid stub, wrapper, environment-variable interface, or replacement job remains.

## 2. Make retained content explicitly static

- [ ] 2.1 Remove generated markers and sync claims from `plugins/mermaid-diagrams/skills/mermaid/SKILL.md`; keep its index, runtime workflow, reference snapshot, choice-report asset, lint template, and schema.
- [ ] 2.2 Update the root README, both plugin manifests, affected marketplace description fields, and root AGENTS example to describe bundled references without recurring synchronization.
- [ ] 2.3 Convert the plugin README to brief static-maintenance guidance and retain source/commit/date attribution in the shipped notice; preserve both license copies and root third-party inventory/notices.

## 3. Simplify checks around observable behavior

- [ ] 3.1 Remove `tests/unit/plugin_maintenance/generators/test_mermaid_diagrams.py` and obsolete imports; retain the renderer's untracked-generated-file test with a generic explanation.
- [ ] 3.2 Add build-layer coverage for empty generator discovery, fixture-generator execution, and unchanged authored Mermaid content after a full build.
- [ ] 3.3 Adapt rendered Mermaid tests for static provenance and resolvable local skill links; preserve checks for both skills, snapshot resources, schema, license, and both marketplace entries through the existing harness fixtures.

## 4. Publish consistent artifacts and verify

- [ ] 4.1 Use the repository version-bumper skill for affected plugin and marketplace versions, updating both runtime manifests without removing their catalog entries.
- [ ] 4.2 Run `uv run python -m plugin_maintenance.build`; inspect that only intended source, metadata, and matching `dist/` files change and that retained references/assets are unchanged from the pre-edit snapshot.
- [ ] 4.3 Run `uv run pytest tests`, both marketplace JSON checks, all plugin manifest JSON checks, and `git diff --check`; confirm a second full build introduces no further changes.
- [ ] 4.4 Scan active code, workflows, maintainer docs, and plugin content for removed module commands, `MERMAID_SYNC_*`, `MERMAID_SOURCE_COMMIT`, `MERMAID_DOCS_NAVIGATION`, weekly-sync claims, and generated markers. Exclude historical OpenSpec records and this removal plan from stale-reference findings.
- [ ] 4.5 Sync this change's deltas into current specs through the OpenSpec workflow after implementation, then run `openspec validate remove-mermaid-sync-generation --strict` and strict validation of the affected main specs. Leave completed historical changes intact.
