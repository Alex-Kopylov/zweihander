# Claude Code Harness Notes

Use these notes only when the active harness is Claude Code.

- Use the `allowed-tools` metadata as written: `Read`, `Write`, `Edit`, `Bash`, and `AskUserQuestion`.
- Use `AskUserQuestion` when the workflow needs missing name, role, CV path, overwrite, abort, or new-path input.
- Preserve `/job-hunt-toolkit:<skill-name>` references in generated next steps and user-facing workflow text.
