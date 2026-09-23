# Proposal: harness-invocation-policy

Builds on `harness-dist-pipeline` (PR #68). Landed first as PR #110, which compiled one spelling of the policy into the other; revised by the PR from `invocation-policy-simplify`, which drops that compile step.

## Why

A skill that only the user may start has to say so twice: Claude Code reads `disable-model-invocation: true` from `SKILL.md` frontmatter, Codex reads `policy.allow_implicit_invocation: false` from `agents/openai.yaml`. Nothing checked the pair: `handoff` wrote both, `wait-what` and `yolo-push` wrote only the frontmatter key, so Codex let the model start them on its own. Both trees also carried the other harness's leftovers: `dist/codex` kept frontmatter keys Codex never reads, and `dist/claude-code` shipped `agents/openai.yaml` files Claude Code never reads.

## What Changes

- `agents/openai.yaml` is Codex runtime metadata: the renderer ships it to the Codex tree as written and never to the Claude Code tree.
- A frontmatter key only Claude Code reads and the frontmatter matrix does not place — `disable-model-invocation`, `model`, `context`, `agent` — sits in a `{% if harness == "ClaudeCode" %}` branch of the template, so a Codex `SKILL.md` carries only the Agent Skills specification's keys.
- A user-only skill states both spellings itself. Nothing compiles one into the other.
- Three rendered-tree tests keep this honest: the Claude Code tree carries no `openai.yaml`; every Codex `SKILL.md` carries only specification keys; the skills Claude Code may not start are exactly the skills Codex may not start.
- `Harness` becomes a `StrEnum`, the one list of harness names; per-harness tables and tests key by its members, and `HARNESSES` is removed.
- The adaptation skill and the frontmatter matrix note describe `agents/openai.yaml`, the Claude Code branch, and the pairing.
- Content: `wait-what` gains `agents/openai.yaml` with its interface and policy. `handoff`, `wait-what`, `yolo-push`, `ai-setup-audit`, and `schema-guided-reasoning` put their Claude Code-only keys in a harness branch; the last four become templates. `llm-wiki` and `obsidian` move upstream `author`, `version`, and `platforms` under `metadata.origin`. `resume-tailoring` drops its `version` key, and `ai-setup-audit` drops the default `disable-model-invocation: false`.
- Consequences: rebuild and commit `dist/`; bump every plugin whose shipped tree changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness-dist-build`: the Claude Code tree no longer carries `agents/openai.yaml`; new requirements that Codex `SKILL.md` frontmatter carries only specification keys and that user-only skills agree across harnesses.
- `harness-adaptation-skill`: the frontmatter-boundary requirement routes Claude Code-only keys through a harness branch and states the user-only pairing.

## Impact

- Build tooling: `plugin_maintenance/render.py` gains `FOREIGN_SKILL_FILES`; `Harness` becomes a `StrEnum`.
- Tests: three rendered-tree invariants and one renderer unit test.
- Shipped content: every `dist/claude-code/**/agents/openai.yaml` disappears; `dist/codex` gains `agents/openai.yaml` for `wait-what` and `yolo-push` and loses every non-specification top-level key.
- CI: unchanged. The job name `gate` is a required status check.

## Non-Goals

- Rules for the `description` of a user-only skill. They belong to skill design principles (issue #89), not to the build.
- Generating any part of `agents/openai.yaml` from frontmatter, or the reverse.
- A per-skill config file that unifies harness settings.
