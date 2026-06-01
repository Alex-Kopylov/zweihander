# Claude Code Harness

Use this file only when the active harness is Claude Code.

- User approval questions: use `AskUserQuestion` when a structured choice is
  useful; otherwise ask in chat and wait.
- Detector dispatch: use `Agent` to spawn all selected detector agents in one
  batch, then wait for every spawned agent before reducing findings.
- If older instructions or tools expose `Task`, treat it as legacy wording for
  `Agent`.
