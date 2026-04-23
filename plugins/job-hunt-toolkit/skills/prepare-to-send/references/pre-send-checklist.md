# Pre-Send Checklist

Run through this before attaching any PDF CV to an application. Every box must be ticked — warnings are not acceptable.

## 1. Filename sanity

- [ ] Matches `<First>_<Last>_<Role>_<DocType>.pdf`
- [ ] No spaces, pipes, commas, hyphens, non-ASCII
- [ ] No company name anywhere in filename
- [ ] No version suffixes (`v1`, `v2`, `final`, `draft`, `OLD`)
- [ ] Length ≤ 70 chars
- [ ] Extension is `.pdf` exactly

## 2. HTML + PDF parity

- [ ] HTML file with same stem exists
- [ ] HTML mtime ≤ PDF mtime (PDF not stale)
- [ ] Both staged together in git, OR both untracked

## 3. PDF metadata

Run `exiftool` and confirm:

- [ ] `Title` = "CV" (generic)
- [ ] `Author` = clean legal name
- [ ] `Producer` / `Creator` empty or "exiftool" only
- [ ] `Keywords` / `Subject` empty
- [ ] `CreateDate` / `ModifyDate` reasonable (recent timestamp OR removed)
- [ ] No XMP custom fields mentioning paths, companies, or stale names
- [ ] No embedded file path strings

Scrub command:
```bash
exiftool -all= -overwrite_original "$pdf"
exiftool -Author="<Legal Name>" -Title="CV" -overwrite_original "$pdf"
```

## 4. Visible content — PDF text

Extract with `pdftotext` and check:

- [ ] No `TODO`, `FIXME`, `XXX`, `[placeholder]`, `{{` template markers
- [ ] No `draft`, `v1`/`v2`/`v3`, `final` text
- [ ] No OTHER company names (catastrophic — leaking "OpenAI" in a CV sent to Anthropic kills you)
- [ ] No absolute paths (`/Users/...`, `/home/...`, `file://...`)
- [ ] No email addresses / phone numbers that aren't the user's
- [ ] Contact info present and correct (email, LinkedIn URL clickable, phone if included)

## 5. Visible content — HTML comments

- [ ] No `<!-- ... -->` comments referencing other companies
- [ ] No commented-out bullets from prior tailoring sessions
- [ ] No TODO comments to self

PDF tools sometimes index HTML comments into searchable text; forgotten comments from prior applications are high-risk.

## 6. Git hygiene

- [ ] Both HTML and PDF staged (atomic commit)
- [ ] No `.env`, `*.key`, `id_rsa`, `*.local.md`, secrets
- [ ] No `salary_notes.md` (unless user explicitly chose to commit)
- [ ] Commit message drafted (`add: <company> — <role>`)

## 7. PDF rendering

- [ ] Opens in Preview / browser without warnings
- [ ] Layout not broken (manual visual check)
- [ ] Text is selectable (not rasterized) — ATS can't parse image PDFs
- [ ] Page count matches expectation (usually 1–2 pages for a CV)
- [ ] Fonts render correctly (no missing-glyph boxes)
- [ ] Links (LinkedIn, portfolio, email) are clickable

## 8. Content correctness

- [ ] Name spelling correct
- [ ] Dates correct and consistent format
- [ ] Company names in work history spelled correctly
- [ ] No hallucinated / fabricated experience
- [ ] Role title on the CV matches (or sensibly reframes) the target JD's role
- [ ] Key JD requirements visibly addressed

## 9. Final sanity

- [ ] Open the PDF in a different app than the one that made it (e.g. export via Chrome, view in Preview) — catches tool-specific rendering bugs
- [ ] Re-read the first sentence of the first bullet — does it instantly signal fit for THIS role?
- [ ] Imagine a recruiter spending 6 seconds on this CV — what do they see first? Is it the best thing about you for this role?

## If any box fails

**STOP.** Fix the issue. Re-run the full checklist — don't assume the rest is still clean after a change. Metadata scrubbing in particular must be re-run after any HTML edit + re-export.

## After all boxes pass

```bash
git add <html> <pdf> company.md
git commit -m "add: <company> — <role>"
# attach <pdf> to the application
# update company.md frontmatter: status=applied, applied=<today>
```
