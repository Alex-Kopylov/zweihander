# Proposal: harness-invocation-policy

Builds on `harness-dist-pipeline` (PR #68). Lands as a PR from `invocation-policy-compile` into `harness-dist-pipeline`.

## Why

A skill that only the user may start has to say so twice: Claude Code reads `disable-model-invocation: true` from `SKILL.md` frontmatter, Codex reads `policy.allow_implicit_invocation: false` from `agents/openai.yaml`. The pipeline leaves the pair to author discipline, and the discipline already failed: `handoff` writes both, `wait-what` and `yolo-push` write only the frontmatter key, so Codex lets the model start them on its own. Both trees also carry the other harness's leftovers: `dist/codex` keeps a `disable-model-invocation` key Codex never reads, and `dist/claude-code` ships `agents/openai.yaml` files Claude Code never reads.

## What Changes

- The renderer compiles invocation policy per harness. An author writes `disable-model-invocation` in `SKILL.md`, `policy.allow_implicit_invocation` in `agents/openai.yaml`, or both. The Claude Code tree gets the frontmatter key and no `agents/openai.yaml`. The Codex tree gets the policy in `agents/openai.yaml` (created when the skill has none, merged when it has one) and no frontmatter key.
- The build fails, naming the skill and both values, when the two spellings disagree, and fails on a value that is not a boolean.
- No per-skill config file: the two files the harnesses already read stay the only sources.
- `PyYAML` joins the build dependencies to read and write `agents/openai.yaml`.
- The adaptation skill and the frontmatter matrix note stop saying invocation policy never belongs in frontmatter; they describe both spellings and the compile step.
- Content: `wait-what` gains `agents/openai.yaml` with its Codex display name and short description; `ai-setup-audit` drops the default `disable-model-invocation: false`, which would otherwise compile into a policy-only `agents/openai.yaml`.
- Consequences: tests that read `agents/openai.yaml` run for Codex only; rebuild and commit `dist/`; bump `ai-assistant-ops`, `dev-workflow`, `llm-application-dev`, and `work-session-tools`, whose shipped trees change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness-dist-build`: new requirement — invocation policy is compiled per harness from either spelling, and a contradiction fails the build.
- `harness-adaptation-skill`: the frontmatter-boundary requirement routes invocation policy through either spelling instead of `agents/openai.yaml` only.

## Impact

- Build tooling: `plugin_maintenance/render.py` gains the compile step; `pyproject.toml` and `uv.lock` gain `PyYAML`.
- Tests: new renderer unit tests; `test_improve_skill.py` marks its `agents/openai.yaml` checks Codex-only.
- Shipped content: every `dist/claude-code/**/agents/openai.yaml` disappears; `dist/codex` gains `agents/openai.yaml` for `wait-what` and `yolo-push` and loses `disable-model-invocation` everywhere.
- CI: unchanged. The job name `gate` is a required status check.

## Non-Goals

- Rules for the `description` of a user-only skill. They belong to skill design principles (issue #89), not to the build.
- Generating Codex `interface` fields from frontmatter.
- A per-skill config file that unifies harness settings.
