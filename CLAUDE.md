# My Marketplace

## Plugin Release Rules

- Always bump the version in `plugin.json` when adding new skills, agents, or commands. The plugin manager uses version comparison, not git diff — unchanged versions are skipped during updates.
- After bumping, use the version bumper and commit workflow skills to update config files and commit the release.

## General Plugins

- `md-bloat-hunter` uses a three-level prompt architecture: top-level
  `SKILL.md`, one per-file `agents/file-orchestrator.md`, and detector agents
  under `agents/`.
- Detector output is governed by
  `plugins/general-plugins/skills/md-bloat-hunter/references/schema.json` and
  validated with `jsonschema -i <output> references/schema.json` from the
  `md-bloat-hunter` skill directory.
- Install the runtime validator with `uv tool install jsonschema`.
- Run the committed regression harness with
  `bash plugins/general-plugins/skills/md-bloat-hunter/tests/validate.sh` after
  changing the skill, detector prompts, schema, or related docs.
