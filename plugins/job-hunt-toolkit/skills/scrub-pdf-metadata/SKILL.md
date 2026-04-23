---
name: scrub-pdf-metadata
description: Use when the user asks to "scrub PDF metadata", "clean the PDF", "strip CV metadata", "remove author from PDF", "clean up before sending", "remove creation date", or after exporting a PDF that will be sent to a recruiter. Strips Author, Title, Producer, Creator, CreationDate, ModifyDate, XMP, and custom metadata fields using exiftool, then sets a clean Author field back. Called automatically by prepare-to-send before any PDF is declared ready.
argument-hint: <pdf-file> [--author="Full Name"]
allowed-tools: Read, Bash, AskUserQuestion
---

# Scrub PDF Metadata

Every PDF carries metadata. Most of it is harmless. Some of it leaks — the export tool you used, the timestamp (looks suspicious if 10 minutes before you applied), the source HTML filename, and sometimes the device name.

This skill strips all of it with `exiftool` and resets a clean Author.

## When to use

- Before sending ANY PDF CV to a recruiter.
- After `export-pdf` runs and before `prepare-to-send` declares the file ready.
- Manually if the user suspects a PDF has stale metadata (e.g. previously edited / renamed).

## Inputs

- **PDF file** (argument, required): absolute path preferred.
- **Author** (optional `--author=`): name to set as the clean Author. Defaults to what Claude can infer from memory/context (e.g. "Aleksei Kopylov"). Ask if unsure.

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

`-all=` removes ALL metadata. This also removes Author, which we re-set next. `-overwrite_original` skips creating a `.pdf_original` backup (we rely on git for history).

### 3. Set clean Author + Title

```bash
exiftool \
  -Author="<Clean Author Name>" \
  -Title="CV" \
  -overwrite_original \
  "$pdf"
```

Title = "CV" (neutral, generic, gives nothing away). Do NOT set company name, role, or date in Title.

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

Even after metadata scrub, the PDF *content* can leak:

```bash
# Check for file paths in visible text
pdftotext "$pdf" - 2>/dev/null | grep -Ei 'file://|/Users/|/home/|Documents|job_seaking' | head
```

If any hits: the HTML template probably renders a path in a header/footer. Fix the HTML, re-export, re-scrub. Do NOT send the PDF.

### 6. Report

```
✓ Scrubbed: <pdf-filename>
  Author: <clean name>
  Title:  CV
  CreateDate: <new timestamp or removed>
  Producer / Creator: empty
  Content scan: no path leaks detected

Ready for sending. Run /job-hunt-toolkit:prepare-to-send for the full pre-send checklist.
```

## Hard rules

- **Require exiftool.** No silent fallbacks. Partial scrubbing is worse than no scrubbing.
- **Strip, then set.** Always run `-all=` first, then set Author/Title. If you only set Author, the other fields (Producer, CreationDate) stick around.
- **Title = "CV".** Not the role, not the company, not a timestamp. Generic.
- **Never embed the company name anywhere in metadata.** Same rule as filenames.
- **Do not silently scrub without showing before/after.** User needs to see what leaked — it teaches pattern recognition for the HTML side too.

## Why this matters

Recruiters and hiring managers sometimes open `File → Properties` on a PDF. ATS tools routinely parse PDF metadata. If your `Title` says "Aleksei_Kopylov_CV_Tailored_for_OpenAI_v3" and you apply to Anthropic, that's a rejection waiting to happen.

## References

- `references/exiftool-commands.md` — full command reference with common patterns
