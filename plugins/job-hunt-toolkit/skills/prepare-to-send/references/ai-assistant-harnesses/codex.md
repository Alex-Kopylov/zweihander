# Codex Harness Notes

Use this file only when running `prepare-to-send` in Codex.

- For PDF content checks, extract text with the best available shell capability
  (such as `pdftotext`) before applying the checks.
- Skill handoffs: load or invoke the matching `SKILL.md` from the available skill list; if `scrub-pdf-metadata` is unavailable, use the fallback commands named in the shared workflow.
- User confirmations: use `request_user_input` when available, or plain chat when enough.
- Export handoff: keep `/job-hunt-toolkit:export-pdf` as a skill reference; otherwise refer to the `export-pdf` skill or re-export workflow in prose.
