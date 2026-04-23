---
name: prepare-to-send
description: Use when the user asks to "prepare to send", "final check", "ready to send", "pre-send checklist", "is this ready", "is this clean", "can I attach this now", "run the checklist", or wants to verify a tailored CV is safe to attach to an application. Runs the complete pre-send audit — filename sanity, HTML↔PDF parity, metadata scrub, visible content scan, git hygiene, content correctness, final sanity — and fails loudly on any issue. Nothing ships with warnings.
argument-hint: [pdf-file] (optional; defaults to most recently modified CV PDF in current company folder)
allowed-tools: Read, Bash, Glob, Grep, Skill, AskUserQuestion
---

# Prepare to Send

The last gate before a PDF goes out. The full checklist lives in `references/pre-send-checklist.md` — treat it as the single source of truth. This skill's job is to drive that checklist section-by-section, delegate metadata scrubbing to `scrub-pdf-metadata`, collect results, and refuse to declare "ready" unless every gate passes.

## When to use

- Before attaching a CV PDF to an application form or email
- After `export-pdf` and before the user hits "send"
- On demand when the user wants reassurance the file is clean

## Inputs

- **PDF file** (optional argument): the PDF to audit. If not given:
  - Look in CWD for `*_CV.pdf` (most recent by mtime).
  - If CWD is a per-company folder (siblings include `company.md`), prefer that folder's CV PDF.
  - If ambiguous, ask the user via AskUserQuestion.
- **HTML counterpart**: inferred by swapping `.pdf` → `.html` on the same stem in the same directory.

## Preconditions

Hard-require both tools up front. Do NOT degrade; a partial audit is worse than no audit because it creates false confidence.

```bash
command -v exiftool   >/dev/null 2>&1 || { echo "ERROR: exiftool not installed (brew install exiftool)"; exit 1; }
command -v pdftotext  >/dev/null 2>&1 || { echo "ERROR: pdftotext not installed (brew install poppler)"; exit 1; }
```

If either is missing, stop immediately. Do not run any section.

## Workflow

Drive the reference checklist `references/pre-send-checklist.md` from top to bottom. Run each section and record PASS/FAIL. ANY fail = stop, report the failing section, do not proceed to the next. Do not issue warnings — everything is either pass or fail.

### Section 1 — Filename sanity

Checklist: section 1. Validate the PDF filename against `<plugin>/references/naming-rules.md`.

Block on any of: spaces, pipes, commas, hyphens, non-ASCII, company name in filename, version suffixes (`v1`/`v2`/`final`/`draft`), length > 70 chars, extension not exactly `.pdf`.

### Section 2 — HTML + PDF parity

Checklist: section 2.

- Verify HTML file with same stem exists in the same directory.
- Compare mtimes. **Rule: `HTML_mtime <= PDF_mtime`**. Equal is acceptable (fast export pipelines produce equal timestamps); only HTML strictly newer than PDF fails, because that means the PDF is stale.

```bash
if [[ "$(stat -f%m "$html")" -gt "$(stat -f%m "$pdf")" ]]; then
  echo "FAIL: HTML edited after PDF exported. Re-run /job-hunt-toolkit:export-pdf."
  exit 1
fi
```

- Check git state: either BOTH files staged, or BOTH untracked. Mixed state = fail.

### Section 3 — PDF metadata scrub

Checklist: section 3. **Invoke the `scrub-pdf-metadata` skill** on the PDF; do not inline exiftool commands here.

If, for some reason, the skill cannot be invoked as a skill, fall back to the exact commands from `<plugin>/skills/scrub-pdf-metadata/references/exiftool-commands.md` under "One-liner: scrub + set + verify" — never improvise.

After scrub, verify with:

```bash
exiftool -Title -Author -Producer -Creator -CreatorTool -CreateDate -Keywords -Subject "$pdf"
```

Fail if `Title` ≠ "CV", if `Keywords`/`Subject` non-empty, or if any field contains a path, another company name, or a stale variant string.

### Section 4 — Visible content scan

Checklist: section 4 (PDF text) and section 5 (HTML comments).

#### 4a. PDF text

```bash
pdftotext "$pdf" - 2>/dev/null > /tmp/prepare-to-send-pdftext.$$
```

Block on any of:
- `TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{`, `<role>`
- `draft`, `v1`, `v2`, `v3`, `final` as standalone markers
- Absolute path fragments (`/Users/`, `/home/`, `C:\\`, `file://`)
- ANY company name other than the one being applied to — cross-reference the workspace's per-company folder names

```bash
# Grab sibling company folder names (excluding current) to check for leaks
current_company="$(basename "$(dirname "$pdf")")"
workspace="$(dirname "$(dirname "$pdf")")"
other_companies="$(ls -1 "$workspace" 2>/dev/null | grep -v "^${current_company}$" | grep -v '^\.' || true)"
```

Fail on ANY hit for another company name in the PDF text.

#### 4b. HTML comments

```bash
grep -oE '<!--[^>]*-->' "$html" || true
```

Block if any HTML comment references another company name. Forgotten commented-out bullets from prior applications are a high-risk leak (some PDF indexers parse HTML comments).

### Section 5 — Git hygiene

Checklist: section 6.

- Both HTML + PDF staged together, OR both untracked.
- No staged `.env`, `*.key`, `id_rsa`, `*.local.md`, `secrets.*`, `salary_notes.md` (unless user explicitly confirmed).
- A proposed commit message is drafted (`add: <company> — <role>` or `update: <company> — <reason>`).

```bash
git status --short
git diff --cached --name-only
```

### Section 6 — PDF rendering sanity

Checklist: section 7.

- [ ] PDF opens without warnings
- [ ] Text is selectable (not rasterized) — required for ATS

Threshold rationale: a minimum character count in `pdftotext` output distinguishes image-only (rasterized) PDFs from text PDFs. Use **200 characters** as the floor — below that, even a one-page CV header alone won't fit, so anything lower means the PDF is image-only or the export failed. This value is tuned for short CVs; raise to 500 for multi-page documents via env var `JOB_HUNT_MIN_PDF_TEXT_CHARS` if needed.

```bash
min_chars="${JOB_HUNT_MIN_PDF_TEXT_CHARS:-200}"
chars="$(pdftotext "$pdf" - 2>/dev/null | wc -c | tr -d ' ')"
if (( chars < min_chars )); then
  echo "FAIL: PDF text extraction yielded $chars chars (< $min_chars). Likely rasterized. Re-export."
  exit 1
fi
```

### Section 7 — Content correctness

Checklist: section 8. The highest-value gate. Claude MUST read the PDF text AND the accompanying `company.md` / `job_description.*` and verify:

- Name spelling correct
- Dates consistent (no contradictions between roles)
- Company names in work history spelled correctly
- No fabricated experience, no inflated seniority beyond defensible (cross-check against master CV)
- Role title on the CV sensibly matches / reframes the target JD's role
- Key must-have JD requirements are visibly addressed in the CV text

Claude does this by reading the PDF text (from Section 4a extraction), the master HTML, the `<company>/company.md`, and `<company>/job_description.*`. Any discrepancy = fail with a specific line-level finding.

### Section 8 — company.md present and current

Checklist: implicit — the report references `company.md`, so verify it exists and has been updated beyond template defaults.

```bash
company_md="$(dirname "$pdf")/company.md"
[[ -f "$company_md" ]] || { echo "FAIL: company.md missing in application folder."; exit 1; }
grep -q '^status: drafting$' "$company_md" && echo "WARN: company.md status still 'drafting'."
```

Block if `company.md` is absent. Warn (but do not fail) if frontmatter still has placeholder defaults — the user can decide.

### Section 9 — Final sanity

Checklist: section 9.

- [ ] Open PDF in a different renderer than the one that made it (Preview if exported via Chrome; vice-versa) to catch tool-specific bugs
- [ ] Re-read the first sentence of the first bullet — does it instantly signal fit for THIS role?
- [ ] Imagine the recruiter's 6-second scan — is the best thing about the candidate for this role visible first?

Claude surfaces these as judgment calls for the user to confirm, not automated gates. Ask via AskUserQuestion.

## Report

Only print if all automated sections pass:

```
Pre-send audit: <pdf-filename>

[PASS] Filename sanity
[PASS] HTML/PDF pair in sync
[PASS] Metadata scrubbed (Title=CV, Author=<clean name>)
[PASS] Visible content — 0 leaks
[PASS] Git hygiene
[PASS] PDF rendering (<chars> text chars)
[PASS] Content correctness (name / dates / companies / no hallucinations)
[PASS] company.md present

Judgment-call gates (confirm with user):
  - Alternate renderer preview OK?
  - First-bullet fit signal strong?
  - 6-second scan surfaces best angle?

✓ Ready to send.

Suggested commit:
  git add <html-path> <pdf-path> <company>/company.md
  git commit -m "add: <company> — <role>"

Attach: <absolute-path-to-pdf>
```

If any automated section fails, print ONLY the failing section's diagnostic and stop. Do not continue.

## Hard rules

- **Every automated gate must pass — no warnings, no partial pass.** Partial pass = fail.
- **Require exiftool AND pdftotext up front.** No silent degradation. Missing tool = abort.
- **Always run `scrub-pdf-metadata` in Section 3.** Never skip even if the user says they "just scrubbed" — HTML edits invalidate prior scrubs.
- **Cross-company leak = catastrophic.** Any other company name in the PDF text or HTML comments is game-over; block.
- **Never commit for the user.** Propose the commit command; the user runs it.
- **Defer metadata specifics to `scrub-pdf-metadata` and its references.** If you need to fall back, use EXACT commands from `exiftool-commands.md` — never improvise.
- **The reference checklist is authoritative.** This skill drives it; it does not replace it. When in doubt, re-read `references/pre-send-checklist.md`.

## References

- `references/pre-send-checklist.md` — the authoritative checklist. Read it once per session. This skill executes against it; do not inline the whole checklist here.
