# Claude Code Harness Notes

Use these notes only when the active harness is Claude Code.

- Use `Glob` to find candidate `*_CV.html` files and `AskUserQuestion` when multiple candidates require a user choice.
- Use `Bash` for browser discovery, running `scripts/html-to-pdf.sh`, checking file size, and printing optional `exiftool` metadata.
- Use `Read` to inspect the produced PDF text for Chromium error-page markers before reporting success.
- Invoke the metadata scrub step as `/job-hunt-toolkit:scrub-pdf-metadata <pdf-absolute-path>`.
- Refer users to `/job-hunt-toolkit:prepare-to-send` for the final freshness and content check.
