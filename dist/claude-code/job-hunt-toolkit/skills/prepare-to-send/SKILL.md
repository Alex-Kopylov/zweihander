---
name: prepare-to-send
description: Use when the user is about to send a job-application CV or cover letter and asks to "run the pre-send checklist", "prepare this CV to send", "is this CV ready to attach", "check this CV before I apply", or "is this application PDF clean". Only for PDFs in a job-hunt workspace company folder — not for general file, document, or code review.
argument-hint: "[pdf-file] (optional; defaults to most recently modified CV PDF in current company folder)"
---

# Prepare to Send

The last gate before a PDF goes out. This skill drives the checklist section-by-section, collects results, and refuses to declare "ready" unless every gate passes.

## When to use

- Before attaching a CV PDF to an application form or email
- After Skill(job-hunt-toolkit:export-pdf) and before the user hits "send"
- On demand when the user wants reassurance the file is clean

## Inputs

- **PDF file** (optional argument `$1`): the PDF to audit. Resolution order:
  1. If `$1` is passed → use it directly.
  2. Else if CWD contains a sibling `company.md` (i.e. CWD is a per-company folder) → pick the `*_CV.pdf` in CWD; if multiple, take the one with the most recent mtime.
  3. Else → hard error: "No PDF specified and CWD is not a per-company folder. Pass a path or cd into a company folder."
- **Typst counterpart**: inferred by swapping `.pdf` → `.typ` on the same stem in the same directory.

## Workspace root

Derive the workspace root from the environment:

```bash
workspace="${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}"
```

Use `ls -1 "$workspace/jobs"` to enumerate company folders when needed (e.g. cross-company leak checks).

## Preconditions

None. Every gate below runs on the `.typ` source and the PDF's own bytes, so this audit needs no tool beyond what the shell already provides.

## Workflow

Run each section top to bottom and record PASS/FAIL. ANY fail = stop, report the failing section, do not proceed to the next. Do not issue warnings — everything is either pass or fail.

---

## Section 1 — Filename sanity

Validate the PDF filename against `${PLUGIN_ROOT}/references/naming-rules.md`.

**Checklist:**

- [ ] Matches `<First>_<Last>_<Role>_<DocType>.pdf`
- [ ] No spaces, pipes `|`, commas, slashes, emojis, or non-ASCII characters in the filename (hyphens are allowed)
- [ ] No company name anywhere in the filename
- [ ] Length ≤ 70 chars
- [ ] Extension is `.pdf` exactly

---

## Section 2 — Typst + PDF parity

**Checklist:**

- [ ] `.typ` file with same stem exists in the same directory
- [ ] `.typ` mtime ≤ PDF mtime (PDF not stale)

```bash
if [[ "$(stat -f%m "$typ")" -gt "$(stat -f%m "$pdf")" ]]; then
  echo 'FAIL: Typst source edited after PDF exported. Re-run Skill(job-hunt-toolkit:export-pdf).'
  exit 1
fi
```

If the source imports a shared template, check that template's mtime too — editing it also makes the PDF stale.

---

## Section 3 — PDF metadata

This is a **check, not a fix**. A PDF from `export-pdf` is clean because the Typst source made it so; if this section fails, correct `#set document(...)` in the `.typ` and re-export. Do not post-process the PDF.

```bash
grep -aoE '/(Title|Author|Keywords|Subject|Creator) ?\([^)]*\)' "$pdf"
```

**Checklist:**

- [ ] `Title` = "CV" (generic)
- [ ] `Author` = clean legal name
- [ ] `Creator` is the plain Typst version string (Typst sets no `Producer`)
- [ ] The company slug appears nowhere in the file: `grep -ac "$current_company" "$pdf"` returns 0
- [ ] `Keywords` empty
- [ ] `Subject` empty
- [ ] No XMP custom fields mentioning paths, companies, or other identifying strings
- [ ] No embedded file path strings

Fail if `Title` ≠ "CV", if `Keywords` or `Subject` are non-empty, or if any field contains a path or another company name.

---

## Section 4 — Visible content scan

### 4a. PDF text

Extract text from the PDF. Scan the extracted content for:

- `TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{`, `<role>`
- `draft`, `v1`, `v2`, `v3`, `final` as standalone markers
- Absolute path fragments: `/Users/`, `/home/`, `C:\`, `file://`
- ANY company name other than the one being applied to — cross-reference the workspace's per-company folder names

Cross-company leak check:

```bash
current_company="$(basename "$(dirname "$pdf")")"
other_companies="$(ls -1 "$workspace/jobs" 2>/dev/null | grep -v "^${current_company}$" | grep -v '^\.' || true)"
```

Fail on ANY hit for another company name in the PDF text.

**On build paths:** unlike the old browser pipeline, Typst embeds no build path of its own — verified by grepping raw and decompressed PDF streams. A path can only appear if the template prints one, which the `Absolute path fragments` item above already covers. No separate check needed.

**Rasterized PDF check:** After reading the PDF, verify extracted text is at least 200 characters long (configurable via `JOB_HUNT_MIN_PDF_TEXT_CHARS`). If it fails, report: "FAIL: PDF text extraction yielded fewer than `$min_chars` chars. Likely rasterized. Re-export."

**Checklist:**

- [ ] No template markers (`TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{`)
- [ ] No standalone draft/version markers
- [ ] No other-company names
- [ ] No absolute path fragments
- [ ] No email addresses or phone numbers that are not the user's
- [ ] Contact info present and correct (email, LinkedIn URL, phone if included)
- [ ] PDF text length ≥ 200 chars (not rasterized)

### 4b. Typst source scan

Three things live in the source that the PDF-text scan structurally cannot catch.

**Comments.** Typst strips `//` and `/* */` at compile time, so they never reach the PDF. They still matter: the `.typ` is what gets copied into the next company folder, so a stale comment leaks on the *following* application.

```bash
grep -nE '(^|[[:space:]])//|/\*' "$typ" || true
```

The `[[:space:]]` guard keeps `https://` URLs out of the results.

**Vanished content.** In Typst markup `<role>` is a label, not text. An inline one compiles with no error and no warning and renders as nothing, leaving a silently blank spot on the CV.

```bash
grep -nE '<[a-z_][a-z0-9_-]*>' "$typ" || true
```

**Invisible-but-extractable text.** White text is invisible on the page yet fully present in the extracted text layer — keyword stuffing that a visual review cannot see and that many employers treat as instant disqualification. It can arrive via a copied template rather than intent.

```bash
grep -nE 'fill:[[:space:]]*(white|luma\(255\)|rgb\("#([fF]{3}|[fF]{6})"\))' "$typ" || true
```

Match only white fills. Screening for `size: 0` or `#place(` sounds prudent and is not: `size: 0.9em` and `#place(top + right)` are ordinary layout, so those patterns fire on almost every real CV and train the reader to ignore the check.

`#hide[...]` is safe and should not be flagged — it lays content out but emits no glyphs, so it is genuinely absent from the PDF.

**Checklist:**

- [ ] All three source scans clean: no other-company comments, no `<...>` labels where prose was intended, no white text

---

## Section 5 — Sensitive file presence

Check for sensitive files in the workspace that should not travel with the application.

**Checklist:**

- [ ] No `.env`, `*.key`, `id_rsa`, `*.local.md`, `secrets.*`, or `salary_notes.md` in the application folder (unless user has explicitly confirmed their presence is intentional)

```bash
find "$(dirname "$pdf")" -maxdepth 2 \( \
  -name '.env' -o -name '*.key' -o -name 'id_rsa' \
  -o -name '*.local.md' -o -name 'secrets.*' -o -name 'salary_notes.md' \
\) 2>/dev/null
```

If any are found, stop and report them. Do not proceed.

---

## Section 6 — PDF rendering sanity

Read the PDF text and verify:

- [ ] PDF opens without error
- [ ] Text is selectable (not rasterized) — required for ATS
- [ ] The candidate's name appears as a **contiguous** run in the extracted text, within the first few lines. Letter-spacing (`#text(tracking: …)`) on the name shatters it into `A L E X   K O P Y L O V`, and a `#grid` sidebar can push the whole sidebar ahead of the name — both leave the text selectable while making ATS name parsing fail
- [ ] Page count matches expectation (usually 1–2 pages for a CV)
- [ ] Links (LinkedIn, portfolio, email) are present

Reuse Section 4a's `JOB_HUNT_MIN_PDF_TEXT_CHARS` threshold; if it passed there, record PASS here.

---

## Section 7 — Content correctness

The assistant must read both the PDF text and accompanying `company.md` / `job_description.*`, then verify:

- [ ] Name spelling correct
- [ ] Dates consistent (no contradictions between roles)
- [ ] Company names in work history spelled correctly
- [ ] No fabricated experience or inflated seniority beyond defensible (cross-check against master CV)
- [ ] Role title on the CV sensibly matches / reframes the target JD's role
- [ ] Key must-have JD requirements are visibly addressed in the CV text

Also read the master Typst source. Any discrepancy = fail with a specific line-level finding.

---

## Section 8 — company.md present and current

Verify the per-company file exists and has been updated beyond template defaults.

```bash
company_md="$(dirname "$pdf")/company.md"
[[ -f "$company_md" ]] || { echo "FAIL: company.md missing in application folder."; exit 1; }
```

**Checklist:**

- [ ] `company.md` exists in the application folder
- [ ] `status` field reflects current reality (valid values: `drafting | applied | screening | interview | offer | signed | rejected | withdrew`)

If `status` is still `drafting`, surface it as informational so the user can update it after sending; do not fail.

---

## Section 9 — Final sanity

Ask the user with Skill(AskUserQuestion) to confirm these judgment calls; they are not automated gates.

- [ ] Open the PDF in a viewer other than the one you drafted in (Preview, a browser, Acrobat) to catch viewer-specific font or layout bugs
- [ ] Re-read the first sentence of the first bullet — does it instantly signal fit for THIS role?
- [ ] Imagine the recruiter's 6-second scan — is the best thing about the candidate for this role visible first?

---

## Report

Only print the full summary if all automated sections pass:

```
Pre-send audit: <pdf-filename>

[PASS] Filename sanity
[PASS] Typst/PDF pair in sync
[PASS] Metadata clean (Title=CV, Author=<clean name>)
[PASS] Visible content — 0 leaks
[PASS] Sensitive file presence
[PASS] PDF rendering (<chars> text chars)
[PASS] Content correctness (name / dates / companies / no hallucinations)
[PASS] company.md present

Judgment-call gates (confirm with user):
  - Alternate renderer preview OK?
  - First-bullet fit signal strong?
  - 6-second scan surfaces best angle?

Ready to send.

Attach: <absolute-path-to-pdf>
```

If any automated section fails, print ONLY the failing section's diagnostic and stop. Do not continue.

---

## Hard rules

- **Every automated gate must pass — no warnings, no partial pass.** Partial pass = fail.
- **No external tools.** Every gate reads the `.typ` and the PDF bytes directly, so there is nothing to install and nothing to degrade to.
- **Section 3 fails toward the source.** A dirty `Title` means a wrong `#set document(...)` in the `.typ`; fix that and re-export. Scrubbing the PDF instead hides the defect and re-introduces it on the next export.
- **Cross-company leak = catastrophic.** Any other company name in the PDF text or Typst comments is game-over; block.
- **Metadata failures are source failures.** Never "fix" them on the PDF; the next export would reintroduce them anyway.
