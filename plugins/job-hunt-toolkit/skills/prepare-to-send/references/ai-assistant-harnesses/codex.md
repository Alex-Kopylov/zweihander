# Codex Harness Notes

Apply only these translations while running `prepare-to-send` in Codex.

- Treat `allowed-tools` as Claude Code metadata; use the active Codex tools instead.
- For `Read`, use scoped file reads through `exec_command`, such as `sed` or `nl` for text files. For PDFs, extract text with the best available Codex file-reading or shell capability before applying the checks.
- For `Bash`, use `exec_command`; use `write_stdin` only to continue an existing command session.
- For `Glob` and `Grep`, prefer `rg` or `rg --files` through `exec_command` when available.
- For `Skill`, load or invoke the matching `SKILL.md` from the available skill list; if `scrub-pdf-metadata` is unavailable, use the fallback commands named in the shared workflow.
- For `AskUserQuestion`, use `request_user_input` when available, or plain chat when enough.
- Do not translate `/job-hunt-toolkit:export-pdf` to a Codex slash command unless an active Codex command has matching semantics; otherwise refer to the `export-pdf` skill or re-export workflow in prose.
