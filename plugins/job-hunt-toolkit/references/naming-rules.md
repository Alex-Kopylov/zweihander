# File Naming Rules

HR recruiters and ATS systems often see only the filename. A good filename makes you findable; a bad one makes you invisible — or worse, signals you tailored the CV for exactly this company.

## Master rule

```
<FirstName>_<LastName>_<Role>_<DocType>.<ext>
```

### Segment rules

- **Underscores only.** No spaces (breaks URLs, terminals, some ATS parsers).
- **No pipes `|`, commas, slashes, emojis, or non-ASCII characters.**
- **ASCII only** — even if the user's name contains accents, filenames use transliterated ASCII.
- **TitleCase segments** or ALL_CAPS acronyms (AI, LLM, ML, NLP, API).
- **`<Role>` is short and scannable**: `ML_Engineer`, `AI_LLM_Engineer`, `Data_Scientist`, `Senior_ML_Engineer`.
- **`<DocType>`**: `CV`, `Resume`, `Cover_Letter`, `Portfolio`.
- **`.pdf` is the default export.** Never send `.docx` unless asked.
- **NO company name in the filename.** Sending `..._CV_OpenAI.pdf` to OpenAI reveals you tailored the CV for them. Folder is the identifier; filename is neutral.
- **Total filename under ~70 chars.** Longer gets truncated in Outlook, Finder, email clients.

## Examples

### Master (at workspace root) — HTML + PDF pair, same stem

```
Aleksei_Kopylov_AI_LLM_ML_Engineer_CV.html
Aleksei_Kopylov_AI_LLM_ML_Engineer_CV.pdf
```

### Tailored (inside company folder)

Same filename shape as master — the role may shift to match the JD, but no company tag:

```
openai/Aleksei_Kopylov_LLM_Engineer_CV.html
openai/Aleksei_Kopylov_LLM_Engineer_CV.pdf
anthropic/Aleksei_Kopylov_AI_Engineer_CV.html
anthropic/Aleksei_Kopylov_AI_Engineer_CV.pdf
acme_robotics/Aleksei_Kopylov_Senior_ML_Engineer_CV.html
acme_robotics/Aleksei_Kopylov_Senior_ML_Engineer_CV.pdf
```

### Cover letters

```
Aleksei_Kopylov_LLM_Engineer_Cover_Letter.pdf
```

## Anti-patterns — DO NOT

| Bad | Why it's bad |
|---|---|
| `cv.pdf` | Invisible in a recruiter's Downloads folder |
| `resume-final-v2-ACTUAL-FINAL.pdf` | Signals chaos and poor attention to detail |
| `Kopylov Aleksei CV AI \| LLM \| ML Engineer.pdf` | Pipes break ATS parsers; spaces break URLs |
| `Kopylov Aleksei CV AI, LLM, Machine Learning Engineer, Data Scienetist.pdf` | Typo, commas, too long |
| `Aleksei_Kopylov_LLM_Engineer_CV_OpenAI.pdf` | Company name in filename screams "tailored for you" |
| `resume_openai.pdf` | Can't identify candidate from filename alone |
| `AlekseiKopylov-CV.pdf` | Hyphens inconsistent; no role; CamelCase with hyphen is a mess |

## Company folder naming

Lowercase with underscores. No hyphens. No spaces. No legal suffixes (Inc, GmbH, Ltd, LLC).

```
acme_robotics/
openai/
anthropic/
deep_mind/
hugging_face/
```

**Why underscores, not hyphens?** Consistency with filenames. Mixed conventions are a sign of rushed work.

## Why no company name in filename?

Three reasons:

1. **Tailoring tell.** HR sees `Aleksei_Kopylov_CV_OpenAI.pdf` and knows immediately you reworked this for OpenAI. That signals lower confidence in your fit.
2. **Forwarding hazard.** Recruiters forward CVs internally. `..._OpenAI.pdf` landing in an Anthropic recruiter's inbox — awkward.
3. **ATS behavior.** Some ATS systems store original filenames in their search index. If you apply to Company A and later to Company B with a CV still carrying A's name in the filename, it can surface in unexpected ways.

The folder is the identifier. The filename is what the recruiter sees.
