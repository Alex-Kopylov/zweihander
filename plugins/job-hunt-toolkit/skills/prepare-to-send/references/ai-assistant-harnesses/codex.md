# Codex Harness Notes

Apply only these translations while running `prepare-to-send` in Codex.

- Treat `allowed-tools` as Claude Code metadata; use the active Codex tools instead.
- For PDF content checks, extract text with the best available shell capability
  (such as `pdftotext`) before applying the checks.
- For `Skill`, load or invoke the matching `SKILL.md` from the available skill list; if `scrub-pdf-metadata` is unavailable, use the fallback commands named in the shared workflow.
- For `AskUserQuestion`, use `request_user_input` when available, or plain chat when enough.
- Do not translate `/job-hunt-toolkit:export-pdf` to a Codex slash command unless an active Codex command has matching semantics; otherwise refer to the `export-pdf` skill or re-export workflow in prose.
