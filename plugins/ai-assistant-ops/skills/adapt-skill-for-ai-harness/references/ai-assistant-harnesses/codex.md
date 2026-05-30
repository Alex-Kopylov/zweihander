# Codex Harness Reference

Checked: 2026-05-30

Sources:

- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/plugins/build
- https://developers.openai.com/codex/cli/slash-commands
- https://developers.openai.com/codex/cli/reference#codex-plugin-marketplace
- https://agentskills.io/specification#metadata-field

Use this file only when adapting a target skill for Codex-specific wording.

## Skill And Plugin Metadata

Codex skills use progressive disclosure: name, description, and path are visible first; `SKILL.md` loads when selected; references and scripts load only when needed. Keep Codex-specific adaptation instructions in this file instead of the shared `SKILL.md`.

Codex plugin manifests live at `.codex-plugin/plugin.json`. Codex marketplace entries live in `.agents/plugins/marketplace.json` for this repository.

## File Inspection And Editing

Use shell inspection through the active Codex shell tools. Prefer `rg` and `rg --files` for search and file discovery.

Use `apply_patch` for manual edits when that tool is exposed. Use formatting commands or repository tooling for mechanical rewrites when appropriate.

## Questions And Planning

Ask directly in chat by default. Use structured user-input tools only when the active Codex harness exposes one and the workflow benefits from fixed choices.

Use `update_plan` when exposed for meaningful multi-step work. If it is not available, keep a concise checklist in the response and update it as work progresses.

## Parallelism And Agents

Use native parallel tool execution when the active Codex harness exposes it and the operations are independent.

Use Codex subagents only when the user explicitly requests them or the active harness instructions make subagent use available and appropriate. Do not translate Claude Code `Agent` guidance into shared skill text unless the target skill is specifically about Claude Code.

## Slash Commands

Codex slash commands include `/skills`, `/plugins`, `/goal`, `/plan`, `/review`, `/status`, and `/diff`. Keep slash-command guidance Codex-specific unless the same command exists with the same semantics in the target harness.
