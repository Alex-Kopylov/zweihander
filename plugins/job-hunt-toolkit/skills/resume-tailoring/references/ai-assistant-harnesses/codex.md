# Codex Harness Adaptation

Use this file only when the active harness is Codex.

Translate the shared Claude Code tool vocabulary narrowly for this skill:

- `AskUserQuestion`: use `request_user_input` for bounded choices when available, or plain chat for open-ended resume discovery and confirmations.
- `Skill`: load or invoke the matching available skill by name or path, including `export-pdf` when producing PDFs.
- `Agent`: delegate with Codex subagent tooling such as `spawn_agent` only when available and permitted; otherwise perform the work directly.

For the master HTML edit guard, ask for explicit confirmation with `request_user_input` or chat before modifying the master HTML file.
