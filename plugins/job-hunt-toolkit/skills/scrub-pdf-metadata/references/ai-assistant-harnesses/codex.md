# Codex Harness Notes

Use these notes only when the active harness is Codex.

- For PDF content scans, prefer `pdftotext "$pdf" -` when available, then
  scan for the listed leak patterns. If text cannot be extracted, report that
  limitation.
- When the clean Author is unclear, use `request_user_input` when available and appropriate; otherwise ask the user in chat.
- Do not present `/job-hunt-toolkit:prepare-to-send` as a Codex command. Refer to the `prepare-to-send` skill by name if available.
