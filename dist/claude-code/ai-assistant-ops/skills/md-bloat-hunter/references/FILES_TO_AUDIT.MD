# Files To Audit

Default: LLM context-loaded files. Explicit audit: user names skipped path.

| Path | Action | Note |
|---|---|---|
| `**/SKILL.md` | include | skill entry |
| `**/references/**/*` | include | context refs; audit Markdown, read schemas/contracts as needed |
| `**/agents/**/*.md` | include | agent prompt |
| `**/commands/**/*.md`, `**/.*/commands/**/*.md` | include | command prompt |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` | include | assistant instructions |
| files linked from included files with read/load/preload/inject/LLM/subagent wording | include | referenced context |
| `README.md`, `docs/**`, install/usage/catalog/changelog/example/generated docs | skip | user-facing |
| `tests/**`, `fixtures/**`, snapshots, eval outputs, specs/design/architecture docs | skip | development |
| manifests, hooks, scripts, copied/executed assets | skip | not prompt text |
