---
name: export-pdf
description: Use when the user asks to "export the PDF", "regenerate PDF", "build PDF from Typst", "compile the Typst CV", "refresh the PDF", "Typst to PDF", "render CV to PDF", "produce PDF from .typ", "generate PDF", or after editing a CV Typst source and needs a fresh PDF.
argument-hint: "[typ-file] (optional; defaults to the current file context or detected CV)"
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Export PDF

Compile a Typst CV to PDF using the Typst CLI; every workspace PDF should use this skill for consistent rendering.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## When to use

- After any edit to a CV Typst source
- When regenerating the master PDF after the master Typst source changes
- When initial scaffolding needs a PDF export

## Inputs

- **Typst file** (argument or inferred): path to the `.typ` source. If omitted:
  - If exactly one `*_CV.typ` exists in the current working directory, use it.
  - If multiple, ask the user which one.

## Preconditions

### 1. Typst available

```bash
command -v typst
```

If not found, fail loudly:

```
ERROR: typst not found on PATH. Install it (brew install typst, or cargo install --locked typst-cli).

Do NOT silently fall back to another PDF tool — cross-application PDF consistency is critical.
```

### 2. Typst file exists and is readable

Fail fast if not.

## Workflow

### 1. Resolve paths

- Typst source: absolute path.
- PDF: same directory, same stem, `.pdf` extension.
- If a PDF already exists, note that it will be overwritten.

### 2. Run the Typst compiler

Use `scripts/typst-to-pdf.sh` which wraps the `typst compile` invocation. Call it with absolute paths:

```bash
bash ${PLUGIN_ROOT}/skills/export-pdf/scripts/typst-to-pdf.sh <typ-absolute-path> <pdf-absolute-path>
```

Where `${PLUGIN_ROOT}` resolves to the plugin's root directory.

Typst may only read files under its project root, which defaults to the source file's own directory. If the CV imports a shared template from higher up, set Typst's own `TYPST_ROOT` to that directory — the script passes no `--root`, so this works natively.

Two cautions. Inside a `.typ`, a leading `/` means the *project root*, not the filesystem root, so a shared template must be imported as `#import "/template.typ"`; a plain `#import "template.typ"` resolves next to the importing file and raising the root will not fix it. And widening the root widens Typst's read sandbox to every company folder under it, so prefer copying the template into the company folder.

### 3. Verify output

- PDF file exists at the target path
- If `exiftool` is installed, print a quick summary of PDF metadata so the user sees what leaked in

Note there is deliberately **no byte-size floor**. A Typst document whose content vanished still compiles to a valid ~2KB PDF, so size cannot tell a blank render from a real one. Step 3b is the gate that can.

### 3b. Sanity-check the compile output

Compile errors exit non-zero and produce no PDF, and the script now also fails on warnings (exit 7) — Typst exits 0 on those, but `unknown font family` means a substitute font was silently used and `did not converge` means the layout is unstable, and either way the PDF no longer matches the master.

What the script cannot catch is content that compiled cleanly into nothing. Extract the PDF text and fail if:

- It is shorter than `JOB_HUNT_MIN_PDF_TEXT_CHARS` (default 200) — the render is blank or rasterized
- It contains `TODO`, `FIXME`, `[placeholder]`, or `{{` — markers that survived into the output

Then check the **source**, because the most dangerous failure leaves no trace in the PDF at all:

```bash
grep -nE '<[a-z_][a-z0-9_-]*>' "$typ"
```

In Typst markup `<role>` is a *label*, not text. An inline one compiles with no error and no warning and renders as nothing, so the CV ships with a silently blank spot. Scanning the PDF text for `<role>` cannot work — by then it is already gone.

If any check fails:

```
ERROR: PDF is blank, contains leftover markers, or the source has unescaped <...> labels; inspect the .typ source and re-run export-pdf.
```

Do NOT report success or proceed to scrubbing if this check fails.

### 4. Verify the metadata came out clean

Typst writes the PDF `Title`, `Author` and `Keywords` from `#set document(...)`, so clean metadata is a property of the **source**, not something to fix afterwards. Check the source, not the PDF:

```bash
grep -n '#set document(' "$typ"
```

Require `title: "CV"` and no `keywords:`. Anything else — a role, a company, a date — fails here, and the fix is to edit the `.typ`.

Do **not** run a metadata scrubber over the output as a matter of course. On an already-clean PDF it is strictly harmful: it inflates the file ~30% and replaces `Creator: Typst <version>` with `XMP Toolkit: Image::ExifTool <version>`, trading a neutral tell for "this candidate ran a metadata scrubber". The `job-hunt-toolkit:scrub-pdf-metadata` skill exists for PDFs that did *not* come out of this pipeline.

### 5. Report

```
✓ Exported: <typ-filename> → <pdf-filename>
  Size: <bytes>
  Metadata clean at source (Title=CV, no keywords).
```

## Hard rules

- **Use Typst every time.** Never fall back to a browser, weasyprint, wkhtmltopdf, or pandoc; prompt the user to install Typst if missing.
- **Use absolute paths for the CLI arguments.** Typst resolves relative paths against CWD otherwise, which is unpredictable across tool calls. This is the opposite of paths *inside* the source, where a leading `/` means the project root.
- **Never pass `--no-pdf-tags`.** Typst writes a tagged PDF by default; those tags are the ordered text layer ATS parsers prefer. Do not pass `--pdf-standard` either — no ATS requires PDF/A, and PDF/UA-1 refuses to compile without a document title you would then have to scrub.
- **Fix metadata at the source, never on the output.** The master `.typ` sets `title: "CV"` and no `keywords`, so there is nothing to strip. Running a scrubber over a clean PDF makes it bigger and more identifiable, not less.
- **Warn if the Typst source has leftover markers** like `TODO`, `[placeholder]`, `{{` — written as content they render straight into the PDF. Typst strips `//` and `/* */` comments at compile time, so those never reach the PDF; they still leak forward when the source is copied to the next company folder, which `job-hunt-toolkit:prepare-to-send` checks.

## Error handling

| Scenario | Action |
|---|---|
| `typst` not found | Fail loudly with install instructions |
| Typst file missing or unreadable | Fail loudly |
| `typst compile` exits non-zero | Print stderr, fail loudly (exit 6) |
| Compile succeeds with warnings (font fallback, non-converging layout) | Script fails with exit 7; report the warning |
| Extracted PDF text below the minimum | Treat as a blank render; fail |
| Typst cannot read an imported file | Import it as `/…` from the project root and set `TYPST_ROOT`, or copy it into the company folder |
| Target PDF is read-only / directory not writable | Fail loudly |

## After export

Remind user:
1. Visually review the PDF (open it, check layout)
2. Metadata has already been scrubbed by this skill
3. Run the `job-hunt-toolkit:prepare-to-send` skill before attaching to any application for a final freshness and content check
