# Tasks: harness-invocation-policy

Landed in two PRs into `harness-dist-pipeline`: #110 shipped a compile step and the `Harness` enum; the PR from `invocation-policy-simplify` removed the compile step. The list below is the resulting state.

## 1. Renderer

- [x] 1.1 Remove the invocation-policy compile step and the `PyYAML` dependency
- [x] 1.2 Add `FOREIGN_SKILL_FILES` beside `FOREIGN_METADATA_DIRS` so the Claude Code tree never carries `skills/*/agents/openai.yaml` (design D2)
- [x] 1.3 Turn `Harness` into a `StrEnum` that replaces the `Literal` type and `HARNESSES`, and key every per-harness table and test reference by it (design D5)

## 2. Tests first

- [x] 2.1 Add a renderer unit test: `agents/openai.yaml` ships byte-for-byte to Codex and not at all to Claude Code
- [x] 2.2 Add rendered-tree tests: no `openai.yaml` in the Claude Code tree; Codex `SKILL.md` top-level keys within `specification.portable_keys`; user-only skills agree across trees (design D4)
- [x] 2.3 Let the pairing test accept only skills declared in `INVOCATION_DIVERGES`, empty today, and fail on a declared skill that does not diverge
- [x] 2.4 Assert every per-harness table covers exactly the `Harness` members
- [x] 2.5 Confirm the new tests fail against the unchanged content

## 3. Content and docs

- [x] 3.1 Wrap `disable-model-invocation`, `model`, `context`, and `agent` in a Claude Code harness branch in `handoff`, `wait-what`, `yolo-push`, `schema-guided-reasoning`, and `ai-setup-audit`, turning the last four into templates
- [x] 3.2 Add `agents/openai.yaml` with an interface and `policy.allow_implicit_invocation: false` to `wait-what` and `ai-setup-audit`; make `ai-setup-audit` user-only for Claude Code too and rewrite its description to say what it does
- [x] 3.3 Move `llm-wiki` and `obsidian` upstream `author`, `version`, and `platforms` under `metadata.origin`; drop `resume-tailoring`'s `version`
- [x] 3.4 Rephrase the `schema-guided-reasoning` table row that the template policy read as a callable name
- [x] 3.5 Update `adapt-skill-for-ai-harness/SKILL.md` and the frontmatter matrix `note`: `agents/openai.yaml` ships to Codex only, Claude Code-only keys go in a harness branch, a user-only skill sets both
- [x] 3.6 Mark the `agents/openai.yaml` checks in `tests/integration/rendered/ai_assistant_ops/test_improve_skill.py` Codex-only

## 4. Publish

- [x] 4.1 Bump every plugin whose shipped tree changes, in both runtime manifests
- [x] 4.2 Rebuild `dist/` with `uv run python -m plugin_maintenance.build` and commit it
- [x] 4.3 Run `uv run --python 3.12 pytest tests`, `jq empty` on every manifest, `git diff --check`, and `openspec validate harness-invocation-policy`
