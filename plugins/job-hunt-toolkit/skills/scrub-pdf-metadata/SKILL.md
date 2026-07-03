---
name: scrub-pdf-metadata
description: Use when the user asks to "scrub PDF metadata", "clean the PDF", "strip CV metadata", "remove author from PDF", "sanitize PDF", "wipe PDF info", "clear PDF properties", "clean up before sending", "remove creation date", or after exporting a PDF that will be sent to a recruiter. Strips Author, Title, Producer, Creator, CreationDate, ModifyDate, XMP, and custom metadata fields using exiftool, then sets a clean Author field back. Called automatically by export-pdf as its final step.
argument-hint: <pdf-file> [--author="Full Name"]
allowed-tools: Read, Bash, AskUserQuestion
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Scrub PDF Metadata

Some PDF metadata can leak export tools, suspicious timestamps, source HTML filenames, and device names. Strip it with `exiftool`, then reset a clean Author.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## When to use

- Before sending ANY PDF CV to a recruiter.
- After `export-pdf` runs and before `prepare-to-send` declares the file ready.
- Manually if the user suspects a PDF has stale metadata (e.g. previously edited / renamed).

## Inputs

- **PDF file** (argument, required): absolute path preferred.
- **Author** (optional `--author=`): name to set as the clean Author. Infer from memory/context (user's name as it appears on the CV). If unclear, ask the user via AskUserQuestion before proceeding.

## Preconditions

### exiftool installed

```bash
command -v exiftool >/dev/null 2>&1
```

If missing:

```
ERROR: exiftool is not installed. Install it:
  brew install exiftool

We don't fall back to other scrubbers — different tools handle different
metadata fields, and partial scrubbing is worse than no scrubbing because
it creates false confidence.
```

## Workflow

### 1. Inspect (before)

Show the user what's in the PDF right now:

```bash
exiftool "$pdf"
```

Specifically highlight any of these that are non-empty:
- `Title`
- `Author`
- `Producer`
- `Creator`
- `CreationDate`
- `ModifyDate`
- `Keywords`
- `Subject`
- `Creator Tool`
- Any `XMP` custom fields
- File path embedded in header/footer — grep the PDF text for `file://` or absolute path fragments

### 2. Strip everything

```bash
exiftool -all= -overwrite_original "$pdf"
```

`-all=` removes all metadata, including Author; re-set it next. `-overwrite_original` skips creating a `.pdf_original` backup alongside the PDF.

### 3. Set clean Author + Title

```bash
exiftool \
  -Author="<Clean Author Name>" \
  -Title="CV" \
  -overwrite_original \
  "$pdf"
```

Use `Title = "CV"`; do not include company, role, or date.

### 4. Inspect (after)

```bash
exiftool "$pdf" | grep -Ei 'author|title|producer|creator|date|keywords|subject'
```

Confirm:
- `Author` = the clean name you set
- `Title` = "CV"
- `Producer` / `Creator` — should be empty OR only show generic "exiftool" (acceptable; recruiters don't pattern-match on exiftool)
- `Create Date` / `Modify Date` — after stripping, these often become the time of the scrub. That's acceptable (time-of-send timestamp is normal). If you want to eliminate them entirely:

```bash
exiftool -CreateDate= -ModifyDate= -MetadataDate= -overwrite_original "$pdf"
```

### 5. Scan PDF text for leaks

Metadata scrub does not cover PDF *content*. Use Read, then scan extracted text for:

- `file:`
- `/Users/`
- `/home/`
- `C:\`
- `Documents`
- the workspace basename (computed at runtime: `$(basename "${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}")`)
- `.html`

If any hits: the HTML template probably renders a path in a header/footer via `@page` CSS. Fix the HTML, re-export, re-scrub. Do NOT send the PDF.

### 6. Report

```
✓ Scrubbed: <pdf-filename>
  Author: <clean name>
  Title:  CV
  CreateDate: <new timestamp or removed>
  Producer / Creator: empty
  Content scan: no path leaks detected

Ready for sending. Run $job-hunt-toolkit:prepare-to-send for the full pre-send checklist.
```

## Hard rules

- **Require exiftool.** No silent fallbacks. Partial scrubbing is worse than no scrubbing.
- **Strip, then set.** Always run `-all=` first, then set Author/Title. If you only set Author, the other fields (Producer, CreationDate) stick around.
- **Title = "CV".** Not the role, not the company, not a timestamp. Generic.
- **Never embed the company name anywhere in metadata.** Same rule as filenames.
- **Do not silently scrub without showing before/after.** User needs to see what leaked — it teaches pattern recognition for the HTML side too.

## Why this matters

Recruiters and hiring managers sometimes open `File → Properties` on a PDF. ATS tools routinely parse PDF metadata. If your `Title` says "<First>_<Last>_CV_Tailored_for_OpenAI_v3" and you apply to Anthropic, that's a rejection waiting to happen.

## Gotchas

- **`exiftool -all=` strips Author too.** Step 3 (Set clean Author + Title) is mandatory; see `references/exiftool-commands.md` for commands.
- **HTML `@page` paths render into PDF text and survive metadata stripping.** `exiftool` cannot remove visible header/footer text, so always run Step 5 after a clean report.

## References

- `references/exiftool-commands.md` — full command reference with common patterns
