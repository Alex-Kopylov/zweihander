# Lint Strategy

This repository separates linting into two groups: **fast lint** and
**full lint**.

The split exists because some linters are useful final gates but poor feedback
during active code generation. An AI agent or developer can temporarily create
unused dependencies, incomplete imports, duplicate code, or inconsistent type
flows while a change is still being assembled. Reporting those findings too
early can create false alarms and distract the workflow before the code reaches
a coherent state.

At the same time, commit hooks must not contain hidden checks that CI and manual
commands skip. If a hook can block a commit, developers should be able to run
the same class of check explicitly before they commit.

## Commands

- `mise run lint-fast`: run checks intended for active editing and agent
  feedback loops.
- `mise run lint-full`: run the final lint gate.
- `mise run lint`: conventional alias for `lint-full`; CI uses this command.
- `mise run install-hooks`: install the commit hooks.

## Fast Lint

Fast lint should be safe to run while code is still being generated or edited.
It should prefer checks that are local, deterministic, and unlikely to depend on
unfinished work elsewhere in the repository.

Fast lint is the right place for:

- Formatting checks.
- Syntax and style checks.
- File-local Python linting.
- Configuration syntax checks.
- Markdown, YAML, JSON, TOML, Dockerfile, and configured automation validation.
- Spelling checks when the project accepts that spelling lint may flag prose.

Use fast lint for editor integrations, agent inner loops, and quick local
feedback before the change is complete.

## Full Lint

Full lint is the final quality gate. It can run slower and broader checks
because it is meant for coherent changes, not half-built work.

Full lint is the right place for:

- Everything from fast lint.
- Type checking.
- Unused-code checks.
- Dependency declaration checks such as `deptry`.
- Duplicate-code checks.
- Secret scans.
- Dependency vulnerability audits.
- Automation security scans when that automation is enabled.

CI should run full lint. Commit hooks may run full-gate checks when they are
practical at commit time, but those checks should also be represented in
`mise run lint-full` so they are not hidden from developers.

## Placement Rules

Use these rules when adding a new linter:

- Add it to fast lint when it gives reliable feedback on incomplete work.
- Add it to full lint when it needs the project to be in a coherent final
  state.
- If it can block a commit hook, make sure it is also covered by full lint.
- Keep hook-only exceptions rare and document why they cannot run in CI or
  `lint-full`.
- Keep CI on `mise run lint` so the default lint command stays the authoritative
  final gate.
- Do not hide missing configured targets behind "skip if missing" logic. If a
  task names `src`, `tests`, `Dockerfile`, or an automation file, that target is
  part of the repository contract. Restore the target or update the task
  configuration.

`deptry` belongs in full lint and the commit hook, not fast lint. Dependency
declaration checks are valuable before code is committed, but they can produce
false alarms while dependencies and imports are still being edited.
