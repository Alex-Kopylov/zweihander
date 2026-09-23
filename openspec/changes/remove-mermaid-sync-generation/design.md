## Context

See [proposal.md](proposal.md) for motivation and scope. This plan is based on PR #68 at `4681eb260326c725c61bdd4a190b267963feb82e`.

The weekly workflow checks out upstream Mermaid syntax, configuration, and navigation files. Its Python sync command replaces the reference directory and saves navigation metadata. The offline generator then rewrites `skills/mermaid/SKILL.md`, the plugin README, and the plugin notice. Ordinary full builds also execute that generator through package discovery.

The current snapshot contains 30 syntax documents, six configuration documents, and an examples document. The recorded upstream commit is `9bae92cd3214f9ec99369ab314ef41ffb283f6b6`, with date `2026-05-31T00:57:11.442Z`. These are existing provenance values, not a claim that the snapshot matches current upstream releases.

The source/render boundary remains mandatory: edits belong in `plugins/`, rendered content belongs in `dist/`, and tests of installed skills use `rendered`.

## Goals / Non-Goals

**Goals:** Remove the whole Mermaid documentation maintenance dependency chain. Preserve the current installed resources and make their ownership explicit. Exercise the general pipeline with no registered generators.

**Non-Goals:** Fetching a newer snapshot; removing the plugin; changing `mmdc` installation, upgrade prompts, or runtime linting; replacing the shared build; adding a replacement crawler, schedule, or metadata validator. Historical completed OpenSpec changes remain historical records.

## Decisions

### 1. Delete the maintenance chain together

Remove `.github/workflows/sync-mermaid-docs.yml` and all of `plugin_maintenance/generators/mermaid_diagrams/`: `__init__.py`, `sync.py`, `generated_docs.py`, `mermaid_navigation.json`, and `templates/`.

Deleting only the workflow leaves ordinary builds rewriting Mermaid files and keeps the parser/template upkeep. Disabling the generator behind a flag retains dead configuration. Neither alternative achieves the requested reduction.

Keep `plugin_maintenance/generators/__init__.py`, generic discovery, and the two-stage commands. The current runner already iterates discovered packages, so an empty collection needs no special Mermaid branch or replacement stub. A generic fixture verifies that behavior; a fixture generator keeps discovery testable without Mermaid.

### 2. Use the existing artifacts as static source

Retain all bundled reference files without a refresh or content rewrite. Retain the skill workflow, choice-report HTML, `mermaid-lint/SKILL.md.j2`, and its result schema. Edit `mermaid/SKILL.md` directly: remove generated table markers and replace “synced” with wording about bundled references. Keep its existing useful index; do not replace generation machinery with a new index generator.

The root `README.md` owns user-facing catalog and usage information. Remove recurring-sync claims there and in both plugin manifests, the Claude marketplace description, and any other affected catalog field. Retain both marketplace entries and their `dist/` source paths.

Rewrite the plugin README as brief maintainer guidance for editing static content, since the renderer excludes that file. Remove its generated blocks and weekly-sync instructions. Put the static-snapshot explanation in the shipped skill/notice as well, so installed users receive it. Remove the obsolete weekly Mermaid example from root `AGENTS.md` and generic test comments.

Keeping a scheduled refresh with less validation would preserve the source of friction. Replacing bundled references with network links would alter the runtime workflow and remove local documentation. Both are outside this design.

### 3. Preserve attribution as static metadata

Keep `plugins/mermaid-diagrams/LICENSE`, `third_party/mermaid-LICENSE.txt`, the Mermaid entry in `third_party/README.md`, and both root/plugin third-party notices. Change active “synced” wording into historical “snapshot” wording where needed. Preserve the recorded source, commit, date, and upstream-banner modification statement; do not stamp the removal date as a new import.

The shipped plugin notice remains the runtime provenance source. Tests can assert that source/commit/date and the MIT license exist without reconstructing a generated README or consulting upstream navigation.

### 4. Remove obsolete tests and retain bounded artifact checks

Delete `tests/unit/plugin_maintenance/generators/test_mermaid_diagrams.py`, whose assertions require the removed package, workflow, templates, and generated README. Keep and adapt `tests/integration/rendered/mermaid_diagrams/test_skill_content.py` for both harnesses: skill/resource availability, local skill links, lint schema, marketplace membership, and snapshot attribution.

Add generic build-layer coverage for no discovered generators and for a fixture generator executing through discovery. Verify that a full build does not alter the authored Mermaid tree. Source-tree inspection stays under `tests/unit/plugin_maintenance/`; installed-content tests use `rendered`. Preserve the existing build freshness, determinism, and renderer-policy tests. Replace the weekly-Mermaid explanation in `tests/unit/plugin_maintenance/test_render.py` with a generic generated-file example; keep the test's behavior.

Do not add exhaustive link checking of copied upstream Markdown, upstream navigation comparisons, live downloads, or a test per deleted file. A focused repository reference scan covers obsolete operational commands during implementation review.

### 5. Reconcile current specifications through deltas

The main `harness-dist-build` spec currently requires a Mermaid generator scenario. Replace that scenario with the empty-generator behavior while preserving the full generic requirement. The `dist-publication` spec's weekly Mermaid example becomes a generic automated-generation example; its publication rule stays intact.

Add the static-content contract in this change. During later implementation/finalization, sync these deltas into main specs through the OpenSpec workflow. Do not rewrite completed `harness-dist-pipeline` or `test-placement` change artifacts to pretend the earlier behavior never existed.

## Risks / Trade-offs

- Static references can become old → document the snapshot honestly; future content edits are explicit, scoped maintenance work.
- Removing the generator could accidentally remove its outputs → preserve the reference snapshot and runtime assets, then check both rendered plugins.
- README-only provenance would disappear on install → keep attribution in the emitted notice and static-content wording in the skill.
- Existing tests require the removed tooling → delete those tests and keep checks of observable installed behavior.
- PR #68 can move while this plan is reviewed → rebase the planning branch onto its latest head and recheck affected paths before publication or implementation.

## Migration Plan

1. Submit only this OpenSpec change in a separate PR against `harness-dist-pipeline`. Leave all implementation tasks unchecked.
2. In the later implementation, remove the workflow and generator together, convert their outputs to static ownership, and adapt the bounded tests.
3. Apply the repository's version-bumper skill to affected plugin/marketplace version fields, then run the full build and commit source plus generated distribution changes.
4. Validate tests, manifests, Markdown whitespace, OpenSpec deltas, and a clean second build. Sync current specs when implementation is complete.
5. Merge the reviewed change into the PR #68 branch. GitHub stops scheduling the removed workflow only once its removal reaches the default branch; merging a planning PR alone changes no runtime behavior.

Rollback, if needed after implementation, is a normal revert of the complete implementation change, restoring workflow, tooling, and matching outputs together. No compatibility command or migration service is introduced.
