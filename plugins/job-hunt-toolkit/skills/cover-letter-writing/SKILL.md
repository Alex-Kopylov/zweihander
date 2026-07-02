---
name: cover-letter-writing
description: Use when drafting, tailoring, generating, exporting, or preparing a cover letter for a tracked job application, especially when a JD, company folder, tailored CV, or application portal asks for a letter.
argument-hint: <company-folder-or-jd>
---

# Cover Letter Writing

Create a truthful, role-specific cover letter from the job description, `company.md`, `USER.md`, and the CV evidence already in the workspace.

## Required Inputs

- Per-company folder with `company.md` and `job_description.*`
- `USER.md` at the workspace root, if present
- Tailored CV HTML/PDF for the role; if missing or stale, invoke `job-hunt-toolkit:resume-tailoring` first
- Master CV only as evidence; never edit it for a cover letter

If the company folder or tailored CV is missing, stop and ask whether to create or run those prerequisites. Do not produce only a PDF or skip source HTML/pre-send checks under deadline pressure.

If evidence is missing for a claim the JD wants, ask or mark it as a gap. If the user asks to imply, exaggerate, or obscure unsupported ownership, refuse that part explicitly. Do not generate final artifacts until the claim is confirmed, reframed honestly, or omitted.

## Workflow

Progress:
- [ ] Step 1: Read workspace rules (`README.md`, `AGENTS.md`, `CLAUDE.md`, and `NAMING.md` when present)
- [ ] Step 2: Read source materials (`USER.md`, `company.md`, the JD, and the tailored CV HTML)
- [ ] Step 3: Extract evidence (target role, company motivation, 3 strongest fit points, and honest gap handling)
- [ ] Step 4: Draft the letter (direct opening, evidence body, honest gap framing if needed, concise close)
- [ ] Step 5: Save the HTML (`<First>_<Last>_<Role>_Cover_Letter.html` in the company folder, with no company name)
- [ ] Step 6: Export the PDF (invoke `job-hunt-toolkit:export-pdf`)
- [ ] Step 7: Run pre-send checks (invoke `job-hunt-toolkit:prepare-to-send` before calling it ready)

## Content Rules

- Truth-preserving only: reframe, connect, and emphasize; never invent.
- "Punchy" means concise and specific, not inflated.
- Deadlines do not waive evidence checks, HTML/PDF parity, export, or pre-send checks.
- Never imply ownership of a requirement unless the source CV, `USER.md`, or the user explicitly confirms that ownership.
- Use the user's voice from `USER.md` when available. If tone preferences are absent, use concise professional prose.
- Keep the letter under one page unless the user explicitly asks otherwise.
- Prefer concrete evidence from the CV over generic enthusiasm.
- Address gaps only when they matter for screening; do not apologize for every mismatch.
- Do not include salary, private IDs, home address, or sensitive personal details unless the user explicitly confirmed them for this application.

For unsupported JD requirements, choose exactly one: ask a focused question, frame adjacent evidence honestly, or omit the requirement.

## Output Report

After generation, report:

```markdown
Cover letter files:
- HTML: <absolute path>
- PDF: <absolute path>

Evidence used:
- <fit point> -> <CV/company/JD source>

Gaps handled:
- <gap> -> <wording strategy or left out>
```

## Common Mistakes

| Mistake | Correction |
|---|---|
| Producing only PDF | HTML is source; PDF is export |
| Naming it `cover_letter.pdf` | Use `<First>_<Last>_<Role>_Cover_Letter.pdf` |
| Claiming a missing JD skill indirectly | Ask, omit, or frame as adjacent experience |
| Using master CV as the edited artifact | Read master for evidence only; write in company folder |
| Treating urgency as permission to skip checks | Deadlines do not change truth or artifact gates |
