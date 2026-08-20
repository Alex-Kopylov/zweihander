# File and Folder Naming Rules

**Scope.** This document is the single, authoritative source for all file and folder naming conventions in the job-hunt-toolkit plugin. Every other plugin doc that mentions naming defers here with "See `references/naming-rules.md`." No other doc defines or overrides these rules.

HR recruiters and ATS systems often see only the filename. A good filename makes you findable; a bad one makes you invisible — or worse, signals you tailored the CV for exactly this company.

## Deny-list (always forbidden)

The following characters are **never** allowed in any filename or folder name:

| Forbidden | Reason |
|---|---|
| Spaces | Break URLs, terminals, some ATS parsers |
| Pipes `\|` | Break ATS parsers |
| Commas `,` | Break ATS parsers and CSV tooling |
| Slashes `/` `\` | Path separator collision |
| Emojis | Non-ASCII; break many systems |
| Any non-ASCII character | Use transliterated ASCII instead |

Everything else — including **hyphens** — is permitted where the segment rules below allow it.

## Master rule

```
<FirstName>_<LastName>_<Role>_<DocType>.<ext>
```

### Filename segment rules

- **Underscores between segments.** No spaces. Hyphens are allowed within a segment (e.g. a multi-word role like `ML-Engineer` is fine; underscores between segments remain the separator).
- **No characters from the deny-list.**
- **ASCII only** — even if the user's name contains accents, filenames use transliterated ASCII.
- **TitleCase segments** or ALL_CAPS acronyms (AI, LLM, ML, NLP, API).
- **`<Role>` is short and scannable**: `ML_Engineer`, `AI_LLM_Engineer`, `Data_Scientist`, `Senior_ML_Engineer`.
- **`<DocType>`**: `CV`, `Resume`, `Cover_Letter`, `Portfolio`.
- **`.pdf` is the default export.** Never send `.docx` unless asked.
- **NO company name in the filename.** Sending `..._CV_OpenAI.pdf` to OpenAI reveals you tailored the CV for them. Folder is the identifier; filename is neutral.
- **Total filename under ~70 chars.** Longer gets truncated in Outlook, Finder, email clients.

## Good / bad examples

| Example | Good or bad | Why |
|---|---|---|
| `Alex_Smith_ML_Engineer_CV.pdf` | Good | Clear candidate, role, doc type |
| `Alex_Smith_AI-LLM_Engineer_CV.pdf` | Good | Hyphen within a segment is fine |
| `cv.pdf` | Bad | Invisible in a recruiter's Downloads folder |
| `resume-final-v2-ACTUAL-FINAL.pdf` | Bad | Signals chaos and poor attention to detail |
| `Lastname Firstname CV AI \| LLM \| ML Engineer.pdf` | Bad | Spaces and pipes from deny-list |
| `Lastname Firstname CV AI, LLM, Machine Learning Engineer, Data Scienetist.pdf` | Bad | Spaces, commas from deny-list; typo; too long |
| `Alex_Smith_LLM_Engineer_CV_OpenAI.pdf` | Bad | Company name in filename screams "tailored for you" |
| `resume_openai.pdf` | Bad | Cannot identify candidate from filename alone |
| `FirstnameLastname_CV.pdf` | Bad | No role; CamelCase without segment separator |

## Company folder naming

Lowercase. No spaces. No characters from the deny-list. Hyphens are allowed.

```
acme-robotics/
acme_robotics/
openai/
anthropic/
deep-mind/
hugging-face/
```

Both underscore and hyphen forms are acceptable. Pick one style and stay consistent within a workspace.

## Examples

### Master (at workspace root) — HTML + PDF pair, same stem

```
<First>_<Last>_<Role>_CV.html
<First>_<Last>_<Role>_CV.pdf
```

### Tailored (inside company folder)

Same filename shape as master — the role may shift to match the JD, but no company tag:

```
openai/<First>_<Last>_LLM_Engineer_CV.html
openai/<First>_<Last>_LLM_Engineer_CV.pdf
anthropic/<First>_<Last>_AI_Engineer_CV.html
anthropic/<First>_<Last>_AI_Engineer_CV.pdf
acme-robotics/<First>_<Last>_Senior_ML_Engineer_CV.html
acme-robotics/<First>_<Last>_Senior_ML_Engineer_CV.pdf
```

### Cover letters

```
<First>_<Last>_<Role>_Cover_Letter.pdf
```

## Why no company name in filename?

Three reasons:

1. **Tailoring tell.** HR sees `<First>_<Last>_CV_OpenAI.pdf` and knows immediately you reworked this for OpenAI. That signals lower confidence in your fit.
2. **Forwarding hazard.** Recruiters forward CVs internally. `..._OpenAI.pdf` landing in an Anthropic recruiter's inbox — awkward.
3. **ATS behavior.** Some ATS systems store original filenames in their search index. If you apply to Company A and later to Company B with a CV still carrying A's name in the filename, it can surface in unexpected ways.

The folder is the identifier. The filename is what the recruiter sees.
