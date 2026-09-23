# Design: harness-invocation-policy

## Context

See `proposal.md` for motivation. Current state that shapes the design:

- Plain files are copied byte-for-byte; only `.j2` files pass through Jinja, with the `harness` context and no `trim_blocks`.
- The renderer already strips the other harness's plugin metadata directory (`FOREIGN_METADATA_DIRS`).
- The frontmatter matrix places a key `top-level` or under `metadata`, and records the specification's six portable keys under `specification.portable_keys`.
- Before this change, Codex `SKILL.md` files carried twelve top-level keys outside the specification across eight skills: `disable-model-invocation`, `model`, `context`, `agent`, `version`, `author`, and `platforms`.

## Goals / Non-Goals

**Goals:**

- Each tree carries only what its harness reads.
- The build stays a copy-and-render step: what an author writes is what a harness gets.
- A missing or contradictory pair is a test failure on the rendered trees.

**Non-Goals:**

- A per-skill config file.
- Rules for how a user-only skill's `description` reads.

## Decisions

**D1 — No compile step; each file says what its harness reads.** `agents/openai.yaml` is copied as written, and a Claude Code-only frontmatter key is branched in the template. A user-only skill therefore writes the setting twice, once per harness.
Alternative — compile one spelling into the other (shipped in #110, then removed): extra renderer code and tests, a rule where either file may or may not exist, and a tree that could only differ per harness in that one setting.
Alternative — a per-skill `config.yaml` that feeds both: rejected; a third file for settings each harness already has a home for.

**D2 — `agents/openai.yaml` is foreign skill metadata for Claude Code.** `FOREIGN_SKILL_FILES` sits beside `FOREIGN_METADATA_DIRS` and names, per harness, the skill files its tree never carries. Claude Code's entry is `skills/*/agents/openai.yaml`; Codex's is empty.

**D3 — Claude Code-only keys go in a harness branch, not the matrix.** The matrix places a key inside frontmatter; `metadata` placement would still leave an inert copy in the Codex tree. A branch at the end of the frontmatter emits nothing for Codex:

```jinja
{% if harness == "ClaudeCode" -%}
disable-model-invocation: true
{% endif -%}
---
```

Keys that neither harness reads, such as an upstream skill's `author`, `version`, and `platforms`, are provenance: they move under `metadata.origin`, and a skill's own `version` key is dropped.

**D4 — Tests read the rendered trees.** The Codex frontmatter test reads the allowed keys from the matrix's `specification.portable_keys`, so the list has one home. The pairing test compares two sets, the skills whose Claude Code `SKILL.md` sets `disable-model-invocation: true` and the skills whose Codex `openai.yaml` sets `allow_implicit_invocation: false`, and needs both trees, so it runs once rather than per harness. Because the renderer derives nothing, a per-harness difference stays possible: the test accepts a skill only when `INVOCATION_DIVERGES` declares it, and fails on a declared skill that no longer diverges. The set is empty today; every current user-only skill is user-only in both harnesses.

**D5 — `Harness` is a `StrEnum` and the one harness list.** Per-harness tables key by `Harness` members, and one test asserts every such table covers exactly the enum. `Harness` replaces both the `Literal` type and `HARNESSES` (test-placement D3): a `StrEnum` member is the string it names, so matrix lookups, Jinja comparisons, pytest ids, and paths are unchanged, while Python code names a harness as `Harness.CODEX` instead of restating it. Data stays text: matrix JSON keys, template conditionals, and the lookup script's arguments keep the plain names.
Alternative — keep `HARNESSES = tuple(Harness)`: rejected; a second name for the same list.

## Risks / Trade-offs

- [An author sets one spelling and forgets the other] → the pairing test fails and names the difference between the two sets.
- [Turning a plain `SKILL.md` into a template puts its body under the template policy] → a literal that matches a mapped callable name fails the policy test; `schema-guided-reasoning` rephrased one table row for this.
- [A future skill nests `SKILL.md` deeper than `skills/<name>/`] → neither the strip rule nor the pairing test would see it. Every skill today sits at that depth.
