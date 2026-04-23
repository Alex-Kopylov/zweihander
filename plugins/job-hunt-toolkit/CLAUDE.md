# job-hunt-toolkit — Claude instructions

Rules Claude follows when this plugin is active and the user is working on job applications.

## Workspace

Default workspace path: `~/Documents/job_seaking`. Override via env var `JOB_HUNT_WORKSPACE`.

If the user is inside a detected workspace (has `CLAUDE.md` referencing this plugin OR a master `Aleksei_Kopylov_*_CV.html` at the root), apply the rules below automatically. Otherwise, offer to run `init-workspace` first.

## Hard rules

- **HTML is the source, PDF is the export.** Never hand-edit PDFs. Edit HTML → regenerate PDF via `export-pdf` skill.
- **Master is sacred.** `<workspace-root>/<name>_CV.html` / `.pdf` at the workspace root is canonical and read-only in Claude's view. Tailored variants live in `<workspace-root>/<company>/`.
- **File naming is strict.** Follow `references/naming-rules.md`. Summary:
  - `<First>_<Last>_<Role>_<DocType>.<ext>` — underscores only, ASCII only, no spaces, no pipes, no commas
  - **NEVER embed the company name in a filename.** That's the #1 tailoring tell.
- **Company folder naming.** lowercase with underscores (`acme_robotics/`, never `Acme Robotics/` or `acme-robotics/`).
- **Atomic commits.** HTML + PDF always commit together. Never one without the other. Commit message: `add: <company> — <role>` or `update: <company> — <reason>`.
- **Metadata scrubbing is mandatory before any PDF leaves the workspace.** Always run `scrub-pdf-metadata` before reporting a CV as "ready to send". No exceptions.
- **Never fabricate experience.** Only rephrase / re-order / emphasize what the master CV already contains. If the JD requires something absent, flag it to the user — do not invent.
- **Never leak secrets.** Salary offers, recruiter private contacts, passport numbers, home addresses — never commit without explicit user confirmation.

## Tool expectations

| Task | Tool | Install if missing |
|---|---|---|
| PDF metadata inspect/strip | `exiftool` | `brew install exiftool` |
| HTML → PDF | Chromium / Chrome headless | Any Chromium browser on `PATH` |
| Version tracking | `git` | comes with macOS CLT |

If a required tool is missing, say so loudly. Do NOT silently fall back to a worse tool — inconsistent PDFs across applications are a red flag. One tool, always the same tool.

## Workflow routing

Match user intent to the right skill:

| User says… | Skill to invoke |
|---|---|
| "start a new application at X", "apply to Y" | `new-application` |
| "tailor my CV for this JD" | `resume-tailoring` |
| "export the PDF", "rebuild the PDF", "regenerate" | `export-pdf` |
| "ready to send", "final check", "what's the checklist" | `prepare-to-send` |
| "scrub metadata", "clean the PDF" | `scrub-pdf-metadata` |
| "set up the workspace", "first time setup" | `init-workspace` |

## Skill chaining

- `new-application` should copy master HTML, then hand off to `resume-tailoring`.
- `prepare-to-send` should call `scrub-pdf-metadata` internally before declaring the file ready.
- `export-pdf` is a utility any skill can call after HTML edits.

## Reference docs

Shared across skills — read these when a skill asks you to:

- `references/naming-rules.md` — file/folder naming
- `references/workspace-layout.md` — directory structure
- `references/application-lifecycle.md` — end-to-end flow

## Gotchas

- PDFs diff as opaque binaries in git. HTML diffs cleanly — that's where the real version history lives.
- Stripping metadata with `exiftool -all=` removes EVERYTHING including the author. After stripping, set a clean `Author` back. Example in `skills/scrub-pdf-metadata/references/exiftool-commands.md`.
- Chromium's `--print-to-pdf` writes to the current working directory unless given an absolute path. Use absolute paths always.
- Some HTML templates embed the source file path in headers/footers via `@page`. That leaks into the PDF. Scan PDF text for path-like strings during pre-send checklist.
