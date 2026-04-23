# job-hunt-toolkit

A paranoid, version-controlled workflow for job applications. Assumes every PDF leaks metadata, every filename signals something, and every company you apply to will find a way to notice if you cut corners.

## What it does

Turns your chaotic Downloads folder into a disciplined, git-tracked workspace:

- **HTML is source, PDF is export.** Edit HTML; regenerate PDF. Never hand-edit PDFs.
- **One folder per company.** Each holds a tailored CV, the JD, research notes, and status.
- **HR-safe file naming.** `FirstName_LastName_Role_CV.pdf` — no company tags in filenames (that's a tailoring tell), no spaces, no pipes.
- **PDF metadata scrubbing.** Author / CreationDate / Producer fields are tracked by ATS tools and recruiters alike. Strip them before sending.
- **Pre-send checklist.** Catch leaks before they leave your machine.
- **Integrated resume tailoring.** The `resume-tailoring` skill lives here — truth-preserving optimization against a job description.

## Components

### Skills

| Skill | Trigger | Purpose |
|---|---|---|
| `init-workspace` | slash command | One-time setup: scaffolds `~/Documents/job_seaking/` (or configured path) with README, CLAUDE.md, NAMING.md, .gitignore, and git init |
| `new-application` | slash command | Start a new company application: create folder, scaffold `company.md`, copy master HTML, invoke tailoring |
| `resume-tailoring` | conversational | Tailor the CV against a JD. Research → template → discovery → assembly → export. Moved from general-plugins. |
| `export-pdf` | slash command or auto | HTML → PDF via headless Chromium. Consistent rendering across applications. |
| `scrub-pdf-metadata` | auto (before send) | Strip PDF metadata with exiftool. Required before sending any PDF. |
| `prepare-to-send` | slash command | Run the full pre-send checklist: naming, metadata, visible content, HTML↔PDF parity, git hygiene. |

### References

Shared knowledge consumed by skills:

- `references/naming-rules.md` — file/folder naming conventions
- `references/workspace-layout.md` — folder structure and per-company contents
- `references/application-lifecycle.md` — from first JD to offer signed

## Requirements

- **exiftool** (metadata scrubbing) — `brew install exiftool`
- **Chromium or Chrome** (PDF export) — any Chromium-based browser on `PATH` works
- **git** (version tracking)

## Configuration

Plugin reads the workspace path from a plugin setting. Default: `~/Documents/job_seaking`. Override by setting `JOB_HUNT_WORKSPACE` in your environment or per-session.

## Philosophy

- **Truth-preserving optimization.** Tailor CVs by reframing and emphasizing; never fabricate experience.
- **Assume breach.** Recruiters use ATS systems, PDF inspectors, and human intuition. Every tell costs you an interview.
- **Single source of truth.** Plugin skills own the workspace rules. `init-workspace` regenerates workspace docs from plugin references. Don't edit workspace docs by hand — edit plugin references and re-init.
- **Atomic commits.** HTML and PDF commit together, always. Never one without the other.

## Install

From this marketplace (`~/.claude/my-marketplace`):

```bash
# in Claude Code
/plugin install job-hunt-toolkit
```

Or point Claude Code at a local path:

```bash
cc --plugin-dir /path/to/job-hunt-toolkit
```

## Typical flow

```
1. /job-hunt-toolkit:init-workspace                 # once, ever
2. Edit master HTML, export PDF                     # establish canonical version
3. /job-hunt-toolkit:new-application acme-robotics  # per application
4. Walk through resume-tailoring                    # per application
5. /job-hunt-toolkit:prepare-to-send                # before attaching PDF
6. git commit, send PDF                             # ship it
```
