# job-hunt-toolkit

A paranoid, disciplined workflow for job applications. Assumes every PDF leaks metadata, every filename signals something, and every company you apply to will find a way to notice if you cut corners.

## What it does

Turns your chaotic Downloads folder into a disciplined, structured workspace:

- **HTML is source, PDF is export.** Edit HTML; regenerate PDF. Never hand-edit PDFs.
- **One folder per company.** Each holds a tailored CV, the JD, research notes, and status.
- **HR-safe file naming.** `FirstName_LastName_Role_CV.pdf` — no company tags in filenames (that's a tailoring tell). Forbidden characters: spaces, pipes `|`, commas, slashes, emojis, non-ASCII. Hyphens and underscores are fine.
- **PDF metadata scrubbing.** Author / CreationDate / Producer fields are tracked by ATS tools and recruiters alike. Strip them before sending.
- **Pre-send checklist.** Catch leaks before they leave your machine.
- **Integrated resume tailoring.** The `resume-tailoring` skill lives here — truth-preserving optimization against a job description.

## Components

### Skills

| Skill | Trigger | Purpose |
|---|---|---|
| `init-workspace` | slash command | One-time setup: scaffolds `~/Documents/job_seeking/` (or configured path) with README, AGENTS.md, and NAMING.md |
| `new-application` | slash command | Start a new company application: create folder, scaffold `company.md`, copy master HTML, invoke tailoring |
| `resume-tailoring` | conversational | Tailor the CV against a JD. Research → template → discovery → assembly → export. Moved from general-plugins. |
| `export-pdf` | slash command or auto | HTML → PDF via headless Chromium. Consistent rendering across applications. |
| `scrub-pdf-metadata` | auto (after export) | Strip PDF metadata with exiftool. Required before sending any PDF. |
| `prepare-to-send` | slash command | Run the full pre-send checklist: naming, metadata, visible content, and HTML↔PDF parity. |

### Natural-language triggers

You can invoke skills conversationally — The assistant recognizes these phrases and routes to the right skill automatically:

| If you say… | Skill invoked |
|---|---|
| "set up my job search workspace", "first-time setup", "initialise the workspace", "create the job hunt folder", "bootstrap my applications folder", "I'm starting fresh, set things up" | `init-workspace` |
| "start a new application at Acme", "apply to Stripe", "new job application for Shopify", "create a folder for FAANG", "I want to apply to this company", "kick off an application" | `new-application` |
| "tailor my CV for this JD", "customise my resume for this role", "optimise my CV against this job description", "adapt my CV to this posting", "rewrite my CV for this position", "help me tailor my resume" | `resume-tailoring` |
| "export the PDF", "rebuild the PDF", "regenerate my CV PDF", "convert HTML to PDF", "re-export", "refresh the PDF" | `export-pdf` |
| "scrub PDF metadata", "clean the PDF", "strip metadata before sending", "remove author from PDF", "sanitise the PDF", "wipe exif data" | `scrub-pdf-metadata` |
| "ready to send", "final check", "run the pre-send checklist", "is my CV ready?", "check before I apply", "validate before sending", "am I good to go?" | `prepare-to-send` |

### References

Shared knowledge consumed by skills:

- `references/naming-rules.md` — file/folder naming conventions
- `references/workspace-layout.md` — folder structure and per-company contents
- `references/application-lifecycle.md` — from first JD to offer signed

## Requirements

| Tool | Purpose | Install |
|---|---|---|
| **exiftool** | PDF metadata scrubbing | `brew install exiftool` |
| **Chromium or Chrome** | HTML → PDF export | any Chromium-based browser on `PATH` |

## Configuration

Plugin reads the workspace path from a plugin setting. Default: `~/Documents/job_seeking`. Override by setting `JOB_HUNT_WORKSPACE` in your environment or per-session.

### Migration

The default workspace was previously named `job_seaking` (typo). It is now `job_seeking`. If you had an existing workspace at `~/Documents/job_seaking`, either rename the folder:

```bash
mv ~/Documents/job_seaking ~/Documents/job_seeking
```

or set `JOB_HUNT_WORKSPACE=~/Documents/job_seaking` in your shell rc to preserve the old path.

## Philosophy

- **Truth-preserving optimization.** Tailor CVs by reframing and emphasizing; never fabricate experience.
- **Assume breach.** Recruiters use ATS systems, PDF inspectors, and human intuition. Every tell costs you an interview.
- **Single source of truth.** Plugin skills own the workspace rules. `init-workspace` regenerates workspace docs from plugin references. Don't edit workspace docs by hand — edit plugin references and re-init.

## Install

From this marketplace:

```bash
/plugin install job-hunt-toolkit
```

Or point the active runtime at a local path:

```bash
<agent-cli> --plugin-dir /path/to/job-hunt-toolkit
```

## Typical flow

```
1. /job-hunt-toolkit:init-workspace                 # once, ever
2. Edit master HTML, export PDF                     # establish canonical version
3. /job-hunt-toolkit:new-application acme-robotics  # per application
4. Walk through resume-tailoring                    # per application
5. /job-hunt-toolkit:prepare-to-send                # before attaching PDF
6. Send PDF                                         # ship it
```
