# job-hunt-toolkit — Agent Instructions

Rules the assistant follows when this plugin is active and the user is working on job applications.

## Workspace

Default workspace path: `~/Documents/job_seeking`. Override via env var `JOB_HUNT_WORKSPACE`.

If the user is inside a detected workspace (has `AGENTS.md` referencing this plugin OR a master `*_CV.html` at the root matching `<First>_<Last>_<Role>_CV.html`), apply the rules below automatically. Otherwise, offer to run `init-workspace` first.

## Hard rules

- **HTML is the source, PDF is the export.** Never hand-edit PDFs. Edit HTML → regenerate PDF via `export-pdf` skill.
- **Master HTML is edit-guarded.** Master HTML at workspace root is canonical. The assistant must call AskUserQuestion for explicit user confirmation before modifying the master HTML. The master PDF is a build artifact and may be overwritten freely. Tailored variants live in `<workspace-root>/<company>/`.
- **File naming is strict.** See `references/naming-rules.md` for the canonical naming rules.
- **Company folder naming.** See `references/naming-rules.md` for the canonical naming rules.
- **Metadata scrubbing is mandatory before any PDF leaves the workspace.** Always run `scrub-pdf-metadata` before reporting a CV as "ready to send". No exceptions.
- **Never fabricate experience.** Only rephrase / re-order / emphasize what the master CV already contains. If the JD requires something absent, flag it to the user — do not invent.
- **Never leak secrets.** Salary offers, recruiter private contacts, passport numbers, home addresses — never include in shared artifacts without explicit user confirmation.

## Tool expectations

| Task | Tool | Install if missing |
|---|---|---|
| PDF metadata inspect/strip | `exiftool` | `brew install exiftool` |
| HTML → PDF | Chromium / Chrome headless | Any Chromium browser on `PATH` |

If a required tool is missing, say so loudly. Do NOT silently fall back to a worse tool — inconsistent PDFs across applications are a red flag. One tool, always the same tool.

## Workflow routing

Match user intent to the right skill:

| User says… | Skill to invoke |
|---|---|
| "start a new application at X", "apply to Y" | `new-application` |
| "tailor my CV for this JD" | `resume-tailoring` |
| "write a cover letter", "draft cover letter" | `cover-letter-writing` |
| "fill this application portal", "submit this application" | `submit-job-application` |
| "export the PDF", "rebuild the PDF", "regenerate" | `export-pdf` |
| "ready to send", "final check", "what's the checklist" | `prepare-to-send` |
| "scrub metadata", "clean the PDF" | `scrub-pdf-metadata` |
| "set up the workspace", "first time setup" | `init-workspace` |

## Skill chaining

- `new-application` should copy master HTML, then hand off to `resume-tailoring`.
- `submit-job-application` should prepare a tailored CV and required cover letter before uploading, then stop for explicit final approval before submission.
- `export-pdf` auto-invokes `scrub-pdf-metadata` as its final step. Every exported PDF is scrubbed.
- `prepare-to-send` verifies scrubbing as a gate before declaring the file ready.
- `export-pdf` is a utility any skill can call after HTML edits.

## Reference docs

Shared across skills — read these when a skill asks you to:

- `references/naming-rules.md` — file/folder naming
- `references/workspace-layout.md` — directory structure
- `references/application-lifecycle.md` — end-to-end flow
