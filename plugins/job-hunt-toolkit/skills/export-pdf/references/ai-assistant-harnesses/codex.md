# Codex Harness Notes

Use these notes only when the active harness is Codex.

- If multiple candidates require a user choice, use `request_user_input` when available; otherwise ask in chat.
- Inspect generated PDF text with an available shell/PDF-text extraction method, such as `pdftotext` when installed. Do not skip the Chromium error-page marker check.
- `$job-hunt-toolkit:scrub-pdf-metadata` and `$job-hunt-toolkit:prepare-to-send` in the shared workflow are already Codex direct-invocation forms; activate those skills from the available skill list. If a required skill is unavailable, report that blocker instead of claiming completion.
