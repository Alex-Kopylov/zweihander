## MODIFIED Requirements

### Requirement: Generated plugins are a declared class
Stage 1 SHALL execute the generator of every plugin that declares one, in-place under `plugins/<name>/`, and the pipeline SHALL NOT special-case any individual plugin name. A generator is a package under the root maintenance directory's `generators/` folder, named for its plugin, exposing a zero-argument `generate()` entrypoint. Generators SHALL be offline, idempotent, and deterministic; fetching external content happens outside the build. If no plugin declares a generator, stage 1 SHALL succeed without changing authored content, and the full build SHALL continue to distribution.

#### Scenario: New generated plugin joins the class
- **WHEN** a plugin declares a generator package following this convention
- **THEN** stage 1 executes it during the next full build without pipeline changes specific to that plugin

#### Scenario: No generated plugins are declared
- **WHEN** no generator packages are declared and the full build runs
- **THEN** stage 1 succeeds without changing authored content and stage 2 publishes both harness trees
