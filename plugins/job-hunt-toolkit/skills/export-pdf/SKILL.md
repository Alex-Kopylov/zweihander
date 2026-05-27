---
name: export-pdf
description: Use when the user asks to "export the PDF", "regenerate PDF", "build PDF from HTML", "convert HTML CV to PDF", "refresh the PDF", "HTML to PDF", "render CV to PDF", "produce PDF from HTML", "generate PDF", or after editing a CV HTML and needs a fresh PDF. Converts an HTML CV into a PDF using headless Chromium, ensuring consistent rendering across all applications.
argument-hint: "[html-file] (optional; defaults to the current file context or detected CV)"
allowed-tools: Read, Bash, Glob, AskUserQuestion
---

# Export PDF

Convert an HTML CV to PDF using headless Chromium. Every PDF in the workspace comes from this skill — consistent rendering across applications is critical (a recruiter comparing two PDFs from the same candidate shouldn't see inconsistent fonts / margins / layouts).

## When to use

- After any edit to a CV HTML file
- When regenerating the master PDF after the master HTML changes
- When initial scaffolding needs a PDF export
- Invoked manually by the user after editing HTML. Also called by `prepare-to-send` to verify PDF freshness. NOT called by `new-application` (user tailors HTML first, then runs export-pdf).

## Inputs

- **HTML file** (argument or inferred): path to the source HTML. If omitted:
  - If exactly one `*_CV.html` exists in the current working directory, use it.
  - If multiple, ask the user which one.

## Preconditions

### 1. Chromium available

Check in order:
```bash
which chromium || which chromium-browser || which google-chrome || which 'Google Chrome' || ls /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome 2>/dev/null
```

Prefer this order on macOS:
1. `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
2. `/Applications/Chromium.app/Contents/MacOS/Chromium`
3. `chromium` on PATH
4. `chromium-browser` on PATH

If none found, fail loudly:

```
ERROR: No Chromium-based browser found. Install Chrome (brew install --cask google-chrome) or Chromium (brew install --cask chromium).

Do NOT silently fall back to another PDF tool — cross-application PDF consistency is critical.
```

### 2. HTML file exists and is readable

Fail fast if not.

## Workflow

### 1. Resolve paths

- HTML: absolute path.
- PDF: same directory, same stem, `.pdf` extension.
- If a PDF already exists, note that it will be overwritten.

### 2. Run Chromium headless

Use `scripts/html-to-pdf.sh` which wraps the browser invocation. Call it with absolute paths:

```bash
bash ${PLUGIN_ROOT}/skills/export-pdf/scripts/html-to-pdf.sh <html-absolute-path> <pdf-absolute-path>
```

Where `${PLUGIN_ROOT}` resolves to the plugin's root directory.

### 3. Verify output

- PDF file exists at the target path
- File size > 1KB (anything smaller is a failed render)
- If `exiftool` is installed, print a quick summary of PDF metadata so the user sees what leaked in

### 3b. Sanity-check PDF content

Use the Read tool to read the produced PDF and inspect its text content. If the content contains any of the following strings, the render almost certainly captured a browser error page rather than the CV:

- `This page isn't working`
- `ERR_CONNECTION_REFUSED`
- `chrome-error://`
- `This site can't be reached`
- `HTTP ERROR`

If any such string is found, fail immediately:

```
ERROR: PDF content suggests render failure; re-run export-pdf or inspect HTML.
```

Do NOT report success or proceed to scrubbing if this check fails.

### 4. Scrub metadata

Auto-invoke `scrub-pdf-metadata` on the produced PDF as the final step:

```
/job-hunt-toolkit:scrub-pdf-metadata <pdf-absolute-path>
```

Every exported PDF is scrubbed, even when attached directly without `prepare-to-send`.

### 5. Report

```
✓ Exported: <html-filename> → <pdf-filename>
  Size: <bytes>
  Metadata scrubbed.
```

## Hard rules

- **Use the same tool (Chromium) every time.** Cross-application rendering consistency matters. Never fall back to weasyprint or wkhtmltopdf even if Chromium is missing — prompt the user to install it.
- **Use absolute paths.** Chromium's `--print-to-pdf` writes to CWD otherwise, which is unpredictable across tool calls.
- **Always scrub metadata after export.** This skill auto-invokes `scrub-pdf-metadata` as its final step. `prepare-to-send` still verifies scrubbing as a gate, but scrubbing can no longer be bypassed by exporting and attaching directly.
- **Warn if the HTML has never-rendered markers** like `TODO`, `<!-- draft -->`, `[placeholder]` — these will appear in the PDF unless scrubbed at HTML level.

## Error handling

| Scenario | Action |
|---|---|
| Chromium not found | Fail loudly with install instructions |
| HTML file missing or unreadable | Fail loudly |
| Chromium exits non-zero | Print stderr, fail loudly |
| Output PDF < 1KB | Treat as failure; delete partial PDF |
| Target PDF is read-only / directory not writable | Fail loudly |

## After export

Remind user:
1. Visually review the PDF (open it, check layout)
2. Metadata has already been scrubbed by this skill
3. Run `/job-hunt-toolkit:prepare-to-send` before attaching to any application for a final freshness and content check

## Gotchas

- Chromium's `--print-to-pdf` writes to CWD unless given an absolute path. `html-to-pdf.sh` handles this by building absolute paths — always pass absolute paths to it.
