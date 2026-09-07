---
name: scrub-pdf-metadata
description: Use when the user asks to "scrub PDF metadata", "clean the PDF", "strip CV metadata", "remove author from PDF", "sanitize PDF", "wipe PDF info", "clear PDF properties", "clean up before sending", "remove creation date", or after exporting a PDF that will be sent to a recruiter.
argument-hint: <pdf-file> [--author="Full Name"]
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Scrub PDF Metadata

Some PDF metadata can leak export tools, suspicious timestamps, source Typst filenames, and device names. Strip it with `exiftool`, then reset a clean Author.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## When to use

- Before sending ANY PDF CV to a recruiter.
- After `export-pdf` runs and before `prepare-to-send` declares the file ready.
- Manually if the user suspects a PDF has stale metadata (e.g. previously edited / renamed).

## Inputs

- **PDF file** (argument, required): absolute path preferred.
- **Author** (optional `--author=`): name to set as the clean Author. Infer from memory/context (user's name as it appears on the CV). If unclear, ask the user before proceeding.

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

### 3b. Flatten the file (mandatory)

Steps 2 and 3 only *append* a new version; the original `Title`/`Keywords` are still recoverable from the file bytes. Rewrite the PDF to drop the incremental update:

```bash
qpdf --linearize "$pdf" "$pdf.flat" && mv "$pdf.flat" "$pdf"
```

`mutool clean -gggg "$pdf" "$pdf"` works equally well. Verified: after flattening, `exiftool -PDF-update:all=` reports "File contains no previous ExifTool update", the old title is gone from the raw bytes, and the text layer is unchanged.

If neither tool is installed, **stop and say so** — do not report the PDF as scrubbed.

### 4. Inspect (after)

```bash
exiftool "$pdf" | grep -Ei 'author|title|producer|creator|date|keywords|subject'
```

`exiftool` alone is not proof — it reads the newest update and will report clean either way. Confirm against the raw bytes:

```bash
grep -ac "$(basename "$(dirname "$pdf")")" "$pdf"   # company slug must not appear
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

Metadata scrub does not cover PDF *content*. Extract PDF text, then scan for:

- `file:`
- `/Users/`
- `/home/`
- `C:\`
- `Documents`
- the workspace basename (computed at runtime: `$(basename "${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}")`)
- `.typ`

If any hits: the Typst template probably prints a path in a `#set page(header: …)` / `footer:` rule. Fix the `.typ` source, re-export, re-scrub. Do NOT send the PDF.

### 6. Report

```
✓ Scrubbed: <pdf-filename>
  Author: <clean name>
  Title:  CV
  CreateDate: <new timestamp or removed>
  Producer / Creator: empty
  Content scan: no path leaks detected

Ready for sending. Run the `job-hunt-toolkit:prepare-to-send` skill for the full pre-send checklist.
```

## Hard rules

- **exiftool edits are reversible — you MUST flatten the file afterwards.** exiftool rewrites a PDF as an *incremental update*: the old objects stay in the file and `exiftool -PDF-update:all=` restores them. exiftool says so itself (`Warning: [minor] ExifTool PDF edits are reversible`). A scrubbed CV therefore still contains "tailored for Acme" in its bytes while `exiftool` reports a clean `Title` — exactly the false confidence this skill exists to prevent. Always finish with Step 3b, then verify by grepping the raw bytes, not with `exiftool`.
- **Require exiftool.** No silent fallbacks. Partial scrubbing is worse than no scrubbing.
- **Strip, then set.** Always run `-all=` first, then set Author/Title. If you only set Author, the other fields (Producer, CreationDate) stick around.
- **Title = "CV".** Not the role, not the company, not a timestamp. Generic.
- **Never embed the company name anywhere in metadata.** Same rule as filenames.
- **Do not silently scrub without showing before/after.** User needs to see what leaked — it teaches pattern recognition for the Typst side too.

## Why this matters

Recruiters and hiring managers sometimes open `File → Properties` on a PDF. ATS tools routinely parse PDF metadata. If your `Title` says "<First>_<Last>_CV_Tailored_for_OpenAI_v3" and you apply to Anthropic, that's a rejection waiting to happen.

## Gotchas

- **`exiftool -all=` strips Author too.** Step 3 (Set clean Author + Title) is mandatory; see `references/exiftool-commands.md` for commands.
- **Typst writes its own PDF metadata.** `typst compile` sets `Creator` to the Typst version (it sets no `Producer`), and `#set document(title: …, author: …, keywords: …)` becomes the PDF `Title`/`Author`/`Keywords`. A document title like "CV tailored for Acme" ships in the PDF properties. **Step 2 does not truly remove it** — see the hard rule on reversible edits. Fix the source: the master should set `title: "CV"` and no `keywords`, so there is nothing to strip.
- **Paths printed by a page header/footer render into PDF text and survive metadata stripping.** `exiftool` cannot remove visible header/footer text, so always run Step 5 after a clean report.

## References

- `references/exiftool-commands.md` — full command reference with common patterns
