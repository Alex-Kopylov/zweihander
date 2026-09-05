---
name: new-application
description: Use when the user asks to "apply to <company>", "start a new application", "new company folder", "scaffold application for", "I'm applying to", "track this job", "set up application for", "create folder for", or provides a JD and wants to set up a tracked application. Creates a per-company folder in the workspace, scaffolds company.md with YAML frontmatter, saves the job description, copies the master HTML for tailoring, and optionally hands off to the resume-tailoring skill.
argument-hint: <company-slug> [role]
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# New Application

Scaffold a per-company application folder inside the workspace and set up everything needed to start tailoring.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## When to use

- User says "I'm applying to X" / "let's apply to Acme" / "start a new application"
- User pastes a JD and wants it tracked
- User provides a `<company-slug>` argument

## Inputs

- **Company slug** (argument, required): must match `^[a-z0-9]+(?:_[a-z0-9]+)*$` (lowercase alphanumerics separated by single underscores). Examples: `openai`, `acme_robotics`, `hugging_face`. Used verbatim as the folder name under `jobs/` after validation.
- **Role** (argument, optional): role the user is targeting. Default to the master's role.
- **JD source** (ask): text paste, file path, or URL.

## Workflow

### 1. Locate workspace

Read `JOB_HUNT_WORKSPACE` env var; fall back to `~/Documents/job_seeking`. Resolve `~`.

If the workspace doesn't exist or lacks a master CV, stop and direct the user to use the `job-hunt-toolkit:init-workspace` skill first.

### 2. Validate company slug

- The slug must match `^[a-z0-9]+(?:_[a-z0-9]+)*$`. This rejects spaces, pipes `|`, commas, slashes, hyphens, emojis, uppercase, and non-ASCII characters.
- If the slug doesn't match, reject it and ask the user for a corrected slug
- The slug is used verbatim as the folder name — no normalisation, no suffix stripping
- Check `<workspace>/jobs/<slug>/` doesn't already exist. If it does, ask:
  - **Resume existing** — work inside the existing folder
  - **New variant** — append `_2` (or ask user for a distinguisher)
  - **Abort**

### 3. Gather role

Ask if not provided:
- Role label (e.g. `Senior_ML_Engineer`, `LLM_Engineer`, `AI_Engineer`)
- Must follow naming rules (TitleCase segments, underscores, ASCII).

### 4. Create folder

```bash
mkdir -p <workspace>/jobs/<slug>
```

### 5. Save the JD

Ask user how they'll provide the JD:
- **Paste text** → write to `jobs/<slug>/job_description.md` (wrap with a header noting source and date)
- **URL** → use WebFetch to grab the content; write to `jobs/<slug>/job_description.md` with a `> Source: <url>` line and fetch date at the top
- **File path** → copy into `jobs/<slug>/job_description.<original-ext>`, preserving the original extension as-is. Do NOT convert the format.

### 6. Scaffold company.md

Use `templates/company.md.template`, substituting:
- `{{COMPANY}}` — original casing (e.g. "Acme Robotics", not the slug)
- `{{ROLE}}` — the role label
- `{{DATE}}` — today's date in ISO (YYYY-MM-DD)
- `{{PORTAL}}` — ask user if known, else leave blank

### 7. Copy master HTML

Find the master: `<workspace>/<First>_<Last>_<Role>_CV.html` (glob for `*_CV.html` at workspace root, not inside company folders).

Copy to `jobs/<slug>/<First>_<Last>_<NewRole>_CV.html`. The role in the filename matches the **target role**, not the master's role, since tailoring often reframes the title.

**Do not generate the PDF yet**; tailoring will edit the HTML first.

### 8. Offer to chain

Ask the user to choose:
- **Tailor now** → invoke the `job-hunt-toolkit:resume-tailoring` skill with the JD and this company's HTML as context
- **Tailor later** → stop here; user can run tailoring manually

### 9. Output summary

```
✓ Created <workspace>/jobs/<slug>/
  ├── company.md
  ├── job_description.md
  └── <First>_<Last>_<NewRole>_CV.html

Next:
  - Edit company.md with company details
  - Use the `job-hunt-toolkit:resume-tailoring` skill to tailor the CV
  - Use the `job-hunt-toolkit:export-pdf` skill to regenerate the PDF
  - Use the `job-hunt-toolkit:prepare-to-send` skill before sending
```

## Hard rules

- **Validate company slug** against `^[a-z0-9]+(?:_[a-z0-9]+)*$` before creating the folder. Reject anything that doesn't match.
- **Never overwrite an existing company folder** without explicit confirmation.
- **Never copy the master PDF** — only HTML. The PDF will be regenerated after tailoring.
- **Never include the company name in the CV filename** (see `references/naming-rules.md` in the plugin).
- **Save the JD verbatim.** Don't paraphrase or summarize. The raw JD is evidence for tailoring decisions.

## Error handling

| Scenario | Action |
|---|---|
| Workspace doesn't exist | Stop; direct user to the `job-hunt-toolkit:init-workspace` skill |
| Master HTML not found | Stop; ask user to create one or use the `job-hunt-toolkit:init-workspace` skill |
| WebFetch fails on JD URL | Ask user to paste the JD text instead |
| Slug doesn't match `^[a-z0-9]+(?:_[a-z0-9]+)*$` | Reject; show the pattern; ask user for corrected slug |
| Role label contains invalid characters | Reject; show naming rules; ask again |
