# Tasks: harness-invocation-policy

Everything lands in one PR from `invocation-policy-compile` into `harness-dist-pipeline`. Tests come first and fail against the current renderer.

## 1. Tests first

- [x] 1.1 Add `PyYAML` to `pyproject.toml` dependencies and refresh `uv.lock`, so the tests can parse `agents/openai.yaml`
- [x] 1.2 Add renderer unit tests to `tests/unit/plugin_maintenance/test_render.py`, one per scenario of the new `harness-dist-build` requirement
- [x] 1.3 Run them and confirm they fail against the current renderer

## 2. Renderer

- [x] 2.1 Add the per-skill compile step to `plugin_maintenance/render.py` (design D3–D6) and document it in the module docstring
- [x] 2.2 Confirm the unit tests from group 1 pass
- [x] 2.3 Dispatch the per-harness writers through `POLICY_WRITERS`, turn `Harness` into a `StrEnum` that replaces `HARNESSES`, and key every per-harness table and test reference by it (design D7)

## 3. Content and docs

- [x] 3.1 Add `plugins/work-session-tools/skills/wait-what/agents/openai.yaml` with `interface.display_name` and `interface.short_description`
- [x] 3.2 Remove the default `disable-model-invocation: false` from `plugins/ai-assistant-ops/skills/ai-setup-audit/SKILL.md`
- [x] 3.3 Update the invocation-policy paragraph in `adapt-skill-for-ai-harness/SKILL.md` and the frontmatter matrix `note` to describe both spellings, the per-harness output, and the contradiction failure
- [x] 3.4 Mark the `agents/openai.yaml` checks in `tests/integration/rendered/ai_assistant_ops/test_improve_skill.py` Codex-only

## 4. Publish

- [x] 4.1 Bump `ai-assistant-ops`, `dev-workflow`, `llm-application-dev`, and `work-session-tools` in both runtime manifests
- [x] 4.2 Rebuild `dist/` with `uv run python -m plugin_maintenance.build` and commit it
- [x] 4.3 Run `uv run --python 3.12 pytest tests`, `jq empty` on every manifest, `git diff --check`, and `openspec validate harness-invocation-policy`
