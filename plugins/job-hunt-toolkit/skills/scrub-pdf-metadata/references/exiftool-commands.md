# exiftool Command Reference

Cheatsheet for PDF metadata operations. All commands assume `$pdf` is a quoted absolute path.

## Install

```bash
brew install exiftool
```

## Inspect — what's in the PDF right now

Full dump:
```bash
exiftool "$pdf"
```

Just the fields that matter for CVs:
```bash
exiftool -Title -Author -Producer -Creator -CreatorTool -CreateDate -ModifyDate -MetadataDate -Keywords -Subject "$pdf"
```

Machine-readable (JSON):
```bash
exiftool -j "$pdf"
```

Every XMP field including custom ones:
```bash
exiftool -XMP:all "$pdf"
```

## Scrub — strip everything

```bash
qpdf --remove-info --remove-metadata "$pdf" "$pdf.clean" && mv "$pdf.clean" "$pdf"
```

Drops the Info dictionary and the whole XMP packet in one irreversible pass.
Output is smaller than the input and the tagged-PDF structure survives.

Do **not** use `exiftool -all=` for this — it is reversible; see below.
Requires qpdf ≥ 11.10 for these two flags.

## Set clean fields

```bash
exiftool \
  -Author="<Your Name>" \
  -Title="CV" \
  -overwrite_original \
  "$pdf"
```

Rules:
- `Title = "CV"` — neutral, generic
- `Author` = your clean, properly-cased name
- Do NOT set: Company, Keywords, Subject, Role

## Remove timestamps specifically

Exiftool sometimes writes a fresh CreateDate during `-all=`. Remove explicitly:

```bash
exiftool \
  -CreateDate= \
  -ModifyDate= \
  -MetadataDate= \
  -overwrite_original \
  "$pdf"
```

Tradeoff: some ATS tools flag PDFs with no date at all as "tampered". A recent but not suspicious date is usually safer than no date.

## One-liner: strip + set + verify

qpdf strips, exiftool sets. That order is required — see "Reversible edits".

```bash
qpdf --remove-info --remove-metadata "$pdf" "$pdf.clean" && mv "$pdf.clean" "$pdf" && \
exiftool -Author="<Your Name>" -Title="CV" -overwrite_original "$pdf" && \
exiftool -Title -Author -Creator -CreateDate "$pdf"
```

## Reversible edits — the trap

exiftool writes PDFs as an *incremental update*: it appends a new trailer and
leaves the original objects in place. It warns about this itself:

```
Warning: [minor] ExifTool PDF edits are reversible. Deleted tags may be recovered!
```

So `exiftool -all=` does **not** delete anything. Demonstrated on a real Typst
CV: after `-all=` plus setting a clean Title, the file *grew* from 11829 to
15467 bytes, `exiftool` reported `Title: CV`, and:

```bash
exiftool -PDF-update:all= -overwrite_original "$pdf"
exiftool -Title -Keywords "$pdf"
# Title    : Alex CV tailored for Acme
# Keywords : acme, llm
```

`qpdf --remove-info --remove-metadata` rewrites the whole file, so it cannot
leave an update history. Running it first also defuses the exiftool step that
follows: the incremental update is still there, but what it could restore is
already empty.

## Diff — before vs after

```bash
exiftool "$pdf" > /tmp/before.txt
qpdf --remove-info --remove-metadata "$pdf" "$pdf.clean" && mv "$pdf.clean" "$pdf"
exiftool -Author="<Your Name>" -Title="CV" -overwrite_original "$pdf"
exiftool "$pdf" > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

## Check PDF text for path leaks

Metadata scrub does not cover visible content. Use Read, then scan extracted text for:

- `file:`
- `/Users/`
- `/home/`
- `C:\`
- `Documents`
- the workspace basename (computed at runtime: `$(basename "${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}")`)
- `.typ`

If hits: the Typst template prints a path somewhere visible via a page header, footer, or running head. Fix the `.typ` source and re-export.

## Common leaking fields, ranked by damage

| Field | Why it leaks | Severity |
|---|---|---|
| `Title` | Comes from `#set document(title: …)`; often a stale variant name or a company-tagged one | HIGH — visible in File → Properties |
| `Keywords` | Comes from `#set document(keywords: …)`; templates sometimes set role / company tags | HIGH |
| `Author` | Comes from `#set document(author: …)`; if blank or "user", signals you're new to this CV or templating lazily | MEDIUM |
| `Creator` | Typst writes its version string here (it sets no `Producer`). Doesn't leak tailoring but breaks consistency if you swap tools between applications | MEDIUM |
| `CreateDate` | "Generated 8 minutes before application submit" is a tell. Worse, Typst stamps the **local UTC offset** — `+03:00` vs `-07:00` narrows where the applicant lives. Set `SOURCE_DATE_EPOCH` to pin it to UTC | MEDIUM |
| XMP custom | Some templates embed the source file path | HIGH if present |

## Do NOT

- Rely on `exiftool -all=` to remove anything — it appends rather than deletes. Strip with qpdf.
- Leave `.pdf_original` backup files that exiftool creates by default sitting in your workspace. Use `-overwrite_original` to avoid them.
- Scrub a PDF, then edit the `.typ` source, then re-export and forget to re-scrub. Every new PDF needs a fresh scrub.
- Trust `File → Properties` in Preview.app for verification — it doesn't show XMP or custom fields. Always verify with `exiftool`.
