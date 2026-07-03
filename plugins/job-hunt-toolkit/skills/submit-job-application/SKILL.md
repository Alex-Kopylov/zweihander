---
name: submit-job-application
description: Use when filling, reviewing, automating, uploading files to, or preparing final submission for an employer job application portal or candidate profile form.
argument-hint: <application-portal-url-or-company-folder>
---

# Submit Job Application

Fill employer application portals from verified workspace data, prepare the required artifacts, and stop before final submission until the user gives fresh explicit approval.

## Hard Gates

- Before any CV upload, invoke `job-hunt-toolkit:resume-tailoring` unless the company folder already contains a current tailored CV HTML/PDF pair for this JD.
- Before any required cover-letter upload, invoke `job-hunt-toolkit:cover-letter-writing` unless a current cover letter HTML/PDF pair already exists. If that skill is unavailable, stop and report a blocker. For optional cover letters, upload or generate only when the user explicitly approves that upload; otherwise skip and report.
- Run `job-hunt-toolkit:prepare-to-send` on every PDF that will be uploaded.
- Never click final `Submit`, `Send application`, `Apply`, or equivalent without a fresh approval after the filled-value report.

Prior user messages like "I trust you" or "submit when ready" do not satisfy the final approval gate.

Current tailored artifacts must be in the target company folder, match the current role and JD content, and be newer than the JD source. If the JD was captured from the portal, existing artifacts are stale unless their source report or `company.md` shows they were generated from that captured JD. If freshness is unclear, regenerate.

## Data Sources

Read in this order:

1. Local workspace rules: `README.md`, `AGENTS.md`, `CLAUDE.md`, and `NAMING.md` when present
2. `USER.md` at the workspace root
3. Per-company `company.md`
4. `job_description.*`
5. Tailored CV HTML and generated PDFs

If `USER.md` lacks legal, demographic, authorization, consent, salary, or availability data, leave the field blank or choose "prefer not to say" only when that exact option is available and appropriate. Do not infer sensitive answers from the CV.

If `USER.md` is missing, report it as a blocker for personal, legal, consent, salary, availability, and demographic fields. Fill only fields explicitly supported by other approved sources.

Never enter placeholder salary values such as `0`, `1`, `negotiable`, or `open` unless `USER.md` or a fresh user reply explicitly provides that exact strategy for this application.

## Browser Strategy

Use the Playwright CLI for normal portal automation: page inspection, field filling, select boxes, textareas, file uploads, and screenshots. Switch to an available real browser or computer-use capability when Playwright is blocked by complex widgets, manual login, SSO, CAPTCHA, anti-bot checks, native file pickers, or visual-only flows.

If neither Playwright nor a real browser path can safely operate the portal, stop and hand the user exact manual steps.

## Fill Workflow

Progress:
- [ ] Step 1: Resolve the company folder (create it if needed and save the portal URL in `company.md`)
- [ ] Step 2: Discover portal requirements (open read-only if the portal is the only JD or upload source; do not fill or submit)
- [ ] Step 3: Prepare artifacts (complete the hard gates for tailored CV, cover letter when required, and `job-hunt-toolkit:prepare-to-send`)
- [ ] Step 4: Open the portal for filling (capture screenshots or DOM notes for field names without submitting)
- [ ] Step 5: Fill supported fields (use only approved sources)
- [ ] Step 6: Upload prepared PDFs (use company-folder PDFs only, never master CV files)
- [ ] Step 7: Pause on unsupported sensitive fields (legal, demographic, paid, consent, or availability fields missing from `USER.md`)
- [ ] Step 8: Confirm attestations (show background check, data processing, legal, or acknowledgement wording and ask for field-specific approval)
- [ ] Step 9: Stop on unanswered required fields (report `required unanswered`; do not use placeholders)
- [ ] Step 10: Produce the filled-value report (use the exact `**entity_name**: value` format below)
- [ ] Step 11: Ask for explicit final approval (do not click final submit before approval)

For dry runs, tests, or reviews, describe choices and report shape without opening the portal or editing files.

## Required Filled-Value Report

Report every touched field, upload, skipped sensitive field, and required unanswered field:

```markdown
**legal_name**: ExampleName ExampleSurname
**email**: <value filled>
**resume_upload**: <absolute PDF path uploaded>
**cover_letter_upload**: <absolute PDF path uploaded>
**work_authorization**: left blank - not present in USER.md
**submit_application**: not clicked - waiting for explicit approval
```

Use the portal's machine-readable field name when available. Otherwise use a stable snake_case label derived from the visible field label.

## Final Approval

Ask this after the report:

```text
Please review the filled values above. I will submit only if you explicitly approve submitting this application now.
```

Only proceed when the user explicitly approves this specific application after seeing the report. If the page changes after approval, produce a new report and ask again.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Clicking Submit because the deadline is close | Stop for the report and fresh approval |
| Uploading the master CV | Tailor, export, scrub, and upload the company-folder PDF |
| Guessing demographic or consent fields | Ask or leave blank according to the portal options |
| Filling from memory | Use `USER.md`, company files, JD, and CV evidence |
| Hiding skipped fields | Report skipped/unanswered fields in `**entity_name**: value` format |
