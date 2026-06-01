# Codex Harness Notes

Map shared tool names narrowly while running this skill in Codex:

- Treat `Bash` command steps as `exec_command`; use `write_stdin` only to continue an existing command session.
- Treat `Read` in Step 5 and `references/exiftool-commands.md` as the active local file or PDF text-inspection capability. For PDF content scans, prefer shell extraction such as `pdftotext "$pdf" -` when available, then scan for the listed leak patterns. If text cannot be extracted, report that limitation.
- When the clean Author is unclear, use `request_user_input` when available and appropriate; otherwise ask the user in chat.
- Do not present `/job-hunt-toolkit:prepare-to-send` as a Codex command. Refer to the `prepare-to-send` skill by name if available.
