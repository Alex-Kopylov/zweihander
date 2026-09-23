# Design: harness-invocation-policy

## Context

See `proposal.md` for motivation. Current state that shapes the design:

- `plugin_maintenance/render.py` handles frontmatter as text: `FRONTMATTER` and `TOP_LEVEL_KEY` find keys, and nothing parses YAML. The build has no YAML dependency.
- Plain files are copied byte-for-byte; only `.j2` files pass through Jinja. `handoff` is a template, `wait-what` and `yolo-push` are plain files.
- Ten skills ship `agents/openai.yaml`; `handoff` is the only one with a `policy` block. Four skills set `disable-model-invocation`: `handoff`, `wait-what`, and `yolo-push` to `true`, `ai-setup-audit` to the default `false`.
- The frontmatter matrix places a key `top-level` or under `metadata`; both placements keep the key in frontmatter.

## Goals / Non-Goals

**Goals:**

- One setting, written wherever the author already works, reaching both harnesses in the spelling each reads.
- Each tree carries only what its harness reads.
- A contradiction is a build failure that names the skill and both values.

**Non-Goals:**

- A third source of truth, such as a per-skill config file.
- Rules for how a user-only skill's `description` reads.

## Decisions

**D1 — Two spellings, one setting, no config file.** An author may write `disable-model-invocation` in `SKILL.md`, `policy.allow_implicit_invocation` in `agents/openai.yaml`, or both. Both files already exist for other reasons, so neither is a new place to learn.
Alternative — a per-skill `config.yaml` that feeds both: rejected; a third file for one boolean.
Alternative — make one spelling mandatory: rejected; a Claude Code author thinks in frontmatter, a Codex author in `openai.yaml`.

**D2 — Not a frontmatter matrix key.** The matrix answers where a key goes inside frontmatter. For Codex this setting leaves frontmatter entirely, so a `metadata` placement would leave an inert copy beside the real one. The compile step is a renderer rule, like stripping the other harness's metadata directory.

**D3 — Compile after rendering, per skill directory.** Once a plugin is written into the staging tree, the renderer visits each `skills/*/` directory that has a `SKILL.md`. It reads the rendered file, so a template and a plain file behave alike. It reads `agents/openai.yaml` from the staged copy too. The Claude Code pass then deletes that copy, and the now-empty `agents/` directory with it.

**D4 — Read frontmatter as text, `openai.yaml` with PyYAML.** Frontmatter stays on the renderer's text path: the value must be the literal `true` or `false`, so a YAML 1.1 spelling such as `yes` fails instead of meaning different things in different parsers. `agents/openai.yaml` is a whole YAML document with nesting, so it is parsed with `yaml.safe_load` rather than matched by pattern.

**D5 — Write only what changes.** In Claude Code, an authored frontmatter line stays where it is; a value that came from `openai.yaml` is appended as the last frontmatter line. In Codex, the frontmatter line is deleted. An `openai.yaml` that already states the policy is copied byte-for-byte. A missing file is written fresh. A file that lacks the policy is re-serialized with `yaml.safe_dump(sort_keys=False)`: key order and values survive, quoting style may not.

**D6 — The value crosses over as written.** An explicit `false` compiles too, into `allow_implicit_invocation: true`. That keeps the rule free of exceptions. The price is a policy-only `openai.yaml` for a skill that states the default, so `ai-setup-audit` loses its `disable-model-invocation: false` line rather than gaining such a file.

**D7 — `Harness` is a `StrEnum` and the one harness list.** The compile step first branched on `harness == "ClaudeCode"`, the renderer's only string comparison on a harness name. It now dispatches through `POLICY_WRITERS`, keyed like `HARNESS_MANIFESTS`, `FOREIGN_METADATA_DIRS`, and `DIST_DIRS`, and every such table is keyed by `Harness` members. `Harness` replaces both the `Literal` type and `HARNESSES` (test-placement D3): a `StrEnum` member is the string it names, so matrix lookups, Jinja comparisons, pytest ids, and paths are unchanged, while Python code names a harness as `Harness.CODEX` instead of restating it. One test asserts every per-harness table covers exactly the enum. Data stays text: matrix JSON keys, template conditionals, and the lookup script's arguments keep the plain names.
Alternative — keep `HARNESSES = tuple(Harness)`: rejected; a second name for the same list.

## Risks / Trade-offs

- [Re-serialized `openai.yaml` differs in quoting from the source] → the file is generated output; `safe_load` of both yields the same data, and a file that already carries the policy is not re-serialized.
- [A future skill nests `SKILL.md` deeper than `skills/<name>/`] → the step would skip it. Every skill today sits at that depth, and the Claude Code and Codex plugin manifests point at `./skills/`.
- [Deleting `agents/openai.yaml` from the Claude Code tree breaks a test that reads it for both harnesses] → such tests become Codex-only; the file is a Codex artifact.
