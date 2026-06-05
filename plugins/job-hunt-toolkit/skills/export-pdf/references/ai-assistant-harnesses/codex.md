# Codex Harness Notes

Use these notes only when the active harness is Codex.

- Use `exec_command` for browser discovery, running `scripts/html-to-pdf.sh`, checking file size, and printing optional `exiftool` metadata.
- Use `rg --files -g '*_CV.html'` through `exec_command` to find candidate CV HTML files when the source file is omitted.
- If multiple candidates require a user choice, use `request_user_input` when available; otherwise ask in chat.
- Inspect generated PDF text with an available shell/PDF-text extraction method, such as `pdftotext` when installed. Do not skip the Chromium error-page marker check.
- Activate the matching job-hunt-toolkit skills by name (`scrub-pdf-metadata`, `prepare-to-send`) instead of relying on Claude Code plugin slash syntax. If a required skill is unavailable in the active skill list, report that blocker instead of claiming completion.
