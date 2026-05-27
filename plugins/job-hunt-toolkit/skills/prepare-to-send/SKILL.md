---
name: prepare-to-send
description: Use when the user asks to "prepare to send", "final check", "ready to send", "pre-send checklist", "is this ready", "is this clean", "can I attach this", "run the checklist", "verify the CV", or "check before sending". Runs the complete pre-send audit — filename sanity, HTML↔PDF parity, metadata scrub, visible content scan, sensitive file presence, content correctness, final sanity — and fails loudly on any issue. Nothing ships with warnings.
argument-hint: "[pdf-file] (optional; defaults to most recently modified CV PDF in current company folder)"
allowed-tools: Read, Bash, Glob, Grep, Skill, AskUserQuestion
---

# Prepare to Send

The last gate before a PDF goes out. This skill drives the checklist section-by-section, delegates metadata scrubbing to `scrub-pdf-metadata`, collects results, and refuses to declare "ready" unless every gate passes.

## When to use

- Before attaching a CV PDF to an application form or email
- After `export-pdf` and before the user hits "send"
- On demand when the user wants reassurance the file is clean

## Inputs

- **PDF file** (optional argument `$1`): the PDF to audit. Resolution order:
  1. If `$1` is passed → use it directly.
  2. Else if CWD contains a sibling `company.md` (i.e. CWD is a per-company folder) → pick the `*_CV.pdf` in CWD; if multiple, take the one with the most recent mtime.
  3. Else → hard error: "No PDF specified and CWD is not a per-company folder. Pass a path or cd into a company folder."
- **HTML counterpart**: inferred by swapping `.pdf` → `.html` on the same stem in the same directory.

## Workspace root

Derive the workspace root from the environment:

```bash
workspace="${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}"
```

Use `ls -1 "$workspace"` to enumerate company folders when needed (e.g. cross-company leak checks).

## Preconditions

Hard-require `exiftool` up front. Do NOT degrade; a partial audit is worse than no audit because it creates false confidence.

```bash
command -v exiftool >/dev/null 2>&1 || { echo "ERROR: exiftool not installed (brew install exiftool)"; exit 1; }
```

If missing, stop immediately. Do not run any section.

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

## Section 2 — HTML + PDF parity

**Checklist:**

- [ ] HTML file with same stem exists in the same directory
- [ ] HTML mtime ≤ PDF mtime (PDF not stale)

```bash
if [[ "$(stat -f%m "$html")" -gt "$(stat -f%m "$pdf")" ]]; then
  echo "FAIL: HTML edited after PDF exported. Re-run /job-hunt-toolkit:export-pdf."
  exit 1
fi
```

---

## Section 3 — PDF metadata scrub

**Invoke the `scrub-pdf-metadata` skill** on the PDF; do not inline exiftool commands here.

If, for some reason, the skill cannot be invoked as a skill, fall back to the exact commands from `${PLUGIN_ROOT}/skills/scrub-pdf-metadata/references/exiftool-commands.md` under "One-liner: scrub + set + verify" — never improvise.

After scrub, verify with:

```bash
exiftool -Title -Author -Producer -Creator -CreatorTool -CreateDate -Keywords -Subject "$pdf"
```

**Checklist:**

- [ ] `Title` = "CV" (generic)
- [ ] `Author` = clean legal name
- [ ] `Producer` / `Creator` empty or "exiftool" only
- [ ] `Keywords` empty
- [ ] `Subject` empty
- [ ] No XMP custom fields mentioning paths, companies, or other identifying strings
- [ ] No embedded file path strings

Fail if `Title` ≠ "CV", if `Keywords` or `Subject` are non-empty, or if any field contains a path or another company name.

---

## Section 4 — Visible content scan

### 4a. PDF text

Use the `Read` tool on the PDF to extract its text. Scan the extracted content for:

- `TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{`, `<role>`
- `draft`, `v1`, `v2`, `v3`, `final` as standalone markers
- Absolute path fragments: `/Users/`, `/home/`, `C:\`, `file://`
- ANY company name other than the one being applied to — cross-reference the workspace's per-company folder names

Cross-company leak check:

```bash
current_company="$(basename "$(dirname "$pdf")")"
other_companies="$(ls -1 "$workspace" 2>/dev/null | grep -v "^${current_company}$" | grep -v '^\.' || true)"
```

Fail on ANY hit for another company name in the PDF text.

**@page CSS path leak:** Some HTML templates embed the source file path in headers/footers via `@page` CSS. When scanning PDF text, also look for path-like strings such as `file:`, `/Users/`, `/home/`, or the workspace basename derived from `$(basename "${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}")`. A match here means the @page rule leaked the build path into the rendered output.

**Rasterized PDF check:** After reading the PDF, verify that the extracted text is at least 200 characters long (configurable via `JOB_HUNT_MIN_PDF_TEXT_CHARS`). Below that floor, even a one-page CV header would not fit — the PDF is likely image-only or the export failed. If it fails, report: "FAIL: PDF text extraction yielded fewer than `$min_chars` chars. Likely rasterized. Re-export."

**Checklist:**

- [ ] No template markers (`TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{`)
- [ ] No standalone draft/version markers
- [ ] No other-company names
- [ ] No absolute path fragments
- [ ] No email addresses or phone numbers that are not the user's
- [ ] Contact info present and correct (email, LinkedIn URL, phone if included)
- [ ] PDF text length ≥ 200 chars (not rasterized)

### 4b. HTML comments

```bash
grep -oE '<!--[^>]*-->' "$html" || true
```

Block if any HTML comment references another company name. Forgotten commented-out bullets from prior applications are a high-risk leak (some PDF indexers parse HTML comments).

**Checklist:**

- [ ] No `<!-- ... -->` comments referencing other companies
- [ ] No commented-out bullets from prior tailoring sessions
- [ ] No TODO comments to self

---

## Section 5 — Sensitive file presence

Check whether sensitive files are present in the workspace that should not travel with the application.

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

Use the `Read` tool on the PDF and verify:

- [ ] PDF opens without error
- [ ] Text is selectable (not rasterized) — required for ATS
- [ ] Page count matches expectation (usually 1–2 pages for a CV)
- [ ] Links (LinkedIn, portfolio, email) are present

Threshold: minimum 200 characters of extracted text (already checked in Section 4a). If it already passed there, record PASS here. If `JOB_HUNT_MIN_PDF_TEXT_CHARS` is set to a higher value for multi-page documents, use that threshold.

---

## Section 7 — Content correctness

The highest-value gate. The assistant must read the PDF text AND the accompanying `company.md` / `job_description.*` and verify:

- [ ] Name spelling correct
- [ ] Dates consistent (no contradictions between roles)
- [ ] Company names in work history spelled correctly
- [ ] No fabricated experience, no inflated seniority beyond defensible (cross-check against master CV)
- [ ] Role title on the CV sensibly matches / reframes the target JD's role
- [ ] Key must-have JD requirements are visibly addressed in the CV text

The assistant does this by reading the PDF text (from Section 4a), the master HTML, the `<company>/company.md`, and `<company>/job_description.*`. Any discrepancy = fail with a specific line-level finding.

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

If `status` is still `drafting`, note it as informational — the user may be preparing to send for the first time and has not yet switched to `applied`. Do not fail on this; surface it so the user can update after sending.

---

## Section 9 — Final sanity

The assistant surfaces these as judgment calls for the user to confirm, not automated gates. Ask via `AskUserQuestion`.

- [ ] Open PDF in a different renderer than the one that made it (Preview if exported via Chrome; vice-versa) to catch tool-specific bugs
- [ ] Re-read the first sentence of the first bullet — does it instantly signal fit for THIS role?
- [ ] Imagine the recruiter's 6-second scan — is the best thing about the candidate for this role visible first?

---

## Report

Only print the full summary if all automated sections pass:

```
Pre-send audit: <pdf-filename>

[PASS] Filename sanity
[PASS] HTML/PDF pair in sync
[PASS] Metadata scrubbed (Title=CV, Author=<clean name>)
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
- **Require exiftool up front.** No silent degradation. Missing tool = abort.
- **Always run `scrub-pdf-metadata` in Section 3.** Never skip even if the user says they "just scrubbed" — HTML edits invalidate prior scrubs.
- **Cross-company leak = catastrophic.** Any other company name in the PDF text or HTML comments is game-over; block.
- **Defer metadata specifics to `scrub-pdf-metadata` and its references.** If you need to fall back, use EXACT commands from `exiftool-commands.md` — never improvise.
