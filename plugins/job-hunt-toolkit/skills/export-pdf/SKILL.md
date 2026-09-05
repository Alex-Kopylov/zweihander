---
name: export-pdf
description: Use when the user asks to "export the PDF", "regenerate PDF", "build PDF from Typst", "compile the Typst CV", "refresh the PDF", "Typst to PDF", "render CV to PDF", "produce PDF from .typ", "generate PDF", or after editing a CV Typst source and needs a fresh PDF. Compiles a Typst CV into a PDF using the Typst CLI, ensuring consistent rendering across all applications.
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
- Invoked manually by the user after editing the Typst source. Also called by the `job-hunt-toolkit:prepare-to-send` skill to verify PDF freshness. NOT called by the `job-hunt-toolkit:new-application` skill (user tailors the Typst source first, then exports the PDF).

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

Typst may only read files under its project root, which the script defaults to the source file's own directory. If the CV imports a shared template from higher up (e.g. a workspace-level `template.typ`), set `JOB_HUNT_TYPST_ROOT` to that directory before calling the script.

### 3. Verify output

- PDF file exists at the target path
- File size > 1KB (anything smaller is a failed render)
- If `exiftool` is installed, print a quick summary of PDF metadata so the user sees what leaked in

### 3b. Sanity-check the compile output

A Typst compile error exits non-zero and produces no PDF, so the script already catches it. Warnings are the dangerous case: they still produce a PDF, but a visibly wrong one. Read the `[typst]` lines the script printed to stderr and fail on any of these:

- `unknown font family` — the layout silently fell back to a substitute font, so the PDF will not match the master
- `did not converge` — the layout is unstable across pages
- Any unresolved-reference or unresolved-label warning — these render as a literal `?` in the output

Then inspect the produced PDF text for markers that survived the compile: `TODO`, `FIXME`, `[placeholder]`, `{{`.

If any of the above is found, fail immediately:

```
ERROR: Typst emitted warnings or the PDF contains unresolved markers; inspect the .typ source and re-run export-pdf.
```

Do NOT report success or proceed to scrubbing if this check fails.

### 4. Scrub metadata

Invoke the `job-hunt-toolkit:scrub-pdf-metadata` skill on the produced PDF as the final step.

Every exported PDF is scrubbed, even when attached directly without the `job-hunt-toolkit:prepare-to-send` skill.

### 5. Report

```
✓ Exported: <typ-filename> → <pdf-filename>
  Size: <bytes>
  Metadata scrubbed.
```

## Hard rules

- **Use Typst every time.** Never fall back to a browser, weasyprint, wkhtmltopdf, or pandoc; prompt the user to install Typst if missing.
- **Use absolute paths.** Typst resolves relative paths against CWD otherwise, which is unpredictable across tool calls.
- **Always scrub metadata after export.** Invoke the `job-hunt-toolkit:scrub-pdf-metadata` skill; the `job-hunt-toolkit:prepare-to-send` skill also verifies scrubbing.
- **Warn if the Typst source has leftover markers** like `TODO`, `[placeholder]`, `{{` — written as content they render straight into the PDF. Typst strips `//` and `/* */` comments at compile time, so those never reach the PDF; they still leak forward when the source is copied to the next company folder, which `job-hunt-toolkit:prepare-to-send` checks.

## Error handling

| Scenario | Action |
|---|---|
| `typst` not found | Fail loudly with install instructions |
| Typst file missing or unreadable | Fail loudly |
| `typst compile` exits non-zero | Print stderr, fail loudly |
| Compile succeeds with warnings (font fallback, unresolved refs) | Treat as failure; report the warning |
| Output PDF < 1KB | Treat as failure; delete partial PDF |
| Typst cannot read an imported file | Re-run with `JOB_HUNT_TYPST_ROOT` set to the directory containing the import |
| Target PDF is read-only / directory not writable | Fail loudly |

## After export

Remind user:
1. Visually review the PDF (open it, check layout)
2. Metadata has already been scrubbed by this skill
3. Run the `job-hunt-toolkit:prepare-to-send` skill before attaching to any application for a final freshness and content check
