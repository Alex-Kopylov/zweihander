# job-hunt-toolkit — Agent Instructions

Rules the assistant follows when this plugin is active and the user is working on job applications.

## Workspace

Default workspace path: `~/Documents/job_seeking`. Override via env var `JOB_HUNT_WORKSPACE`.

If the user is inside a detected workspace (has `AGENTS.md` referencing this plugin OR a master `*_CV.typ` at the root matching `<First>_<Last>_<Role>_CV.typ`), apply the rules below automatically. Otherwise, offer to run `init-workspace` first.

## Hard rules

- **Typst is the source, PDF is the export.** Never hand-edit PDFs. Edit the `.typ` source → regenerate PDF via `export-pdf` skill.
- **The master Typst source is edit-guarded.** The master `.typ` at workspace root is canonical. The assistant must call AskUserQuestion for explicit user confirmation before modifying it. The master PDF is a build artifact and may be overwritten freely. Tailored variants live in `<workspace-root>/jobs/<company>/`.
- **File and company-folder naming is strict.** See `references/naming-rules.md` for the canonical rules.
- **Clean metadata is the source's job.** Typst writes `Title`/`Author`/`Keywords` from `#set document(...)`, so the master `.typ` sets `title: "CV"` with no keywords and every export is clean by construction. Verify that before sending; never try to fix it by post-processing the PDF.
- **Never fabricate experience.** Only rephrase / re-order / emphasize what the master CV already contains. If the JD requires something absent, flag it to the user — do not invent.
- **Never leak secrets.** Salary offers, recruiter private contacts, passport numbers, home addresses — never include in shared artifacts without explicit user confirmation.

## Tool expectations

| Task | Tool | Install if missing |
|---|---|---|
| Typst → PDF | `typst` | `brew install typst` |

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
| "set up the workspace", "first time setup" | `init-workspace` |

## Skill chaining

- `new-application` should copy the master Typst source, then hand off to `resume-tailoring`.
- `submit-job-application` should prepare a tailored CV and required cover letter before uploading, then stop for explicit final approval before submission.
- `export-pdf` verifies the source sets clean document metadata; it does not scrub the output.
- `prepare-to-send` gates on the PDF's metadata being clean before declaring the file ready.
- `export-pdf` is a utility any skill can call after Typst source edits.

## Reference docs

Shared across skills — read these when a skill asks you to:

- `references/naming-rules.md` — file/folder naming
- `references/workspace-layout.md` — directory structure
- `references/application-lifecycle.md` — end-to-end flow
