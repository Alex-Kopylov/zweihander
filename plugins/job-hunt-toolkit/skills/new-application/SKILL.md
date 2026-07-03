---
name: new-application
description: Use when the user asks to "apply to <company>", "start a new application", "new company folder", "scaffold application for", "I'm applying to", "track this job", "set up application for", "create folder for", or provides a JD and wants to set up a tracked application. Creates a per-company folder in the workspace, scaffolds company.md with YAML frontmatter, saves the job description, copies the master HTML for tailoring, and optionally hands off to the resume-tailoring skill.
argument-hint: <company-slug> [role]
allowed-tools: Read, Write, Edit, Bash, WebFetch, AskUserQuestion, Skill
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

- **Company slug** (argument, required): lowercase with underscores. Examples: `openai`, `acme_robotics`, `hugging_face`. Used verbatim as the folder name after deny-list validation.
- **Role** (argument, optional): role the user is targeting. Default to the master's role.
- **JD source** (ask): text paste, file path, or URL.

## Workflow

### 1. Locate workspace

Read `JOB_HUNT_WORKSPACE` env var; fall back to `~/Documents/job_seeking`. Resolve `~`.

If the workspace doesn't exist or lacks a master CV, stop and direct user to run `$job-hunt-toolkit:init-workspace` first.

### 2. Validate company slug

- Deny-list: spaces, pipes `|`, commas, slashes, emojis, non-ASCII characters
- If the slug contains any denied character, reject it and ask the user for a corrected slug
- The slug is used verbatim as the folder name — no normalisation, no suffix stripping
- Check `<workspace>/<slug>/` doesn't already exist. If it does, ask:
  - **Resume existing** — work inside the existing folder
  - **New variant** — append `_2` (or ask user for a distinguisher)
  - **Abort**

### 3. Gather role

Ask if not provided:
- Role label (e.g. `Senior_ML_Engineer`, `LLM_Engineer`, `AI_Engineer`)
- Must follow naming rules (TitleCase segments, underscores, ASCII).

### 4. Create folder

```bash
mkdir -p <workspace>/<slug>
```

### 5. Save the JD

Ask user how they'll provide the JD:
- **Paste text** → write to `<slug>/job_description.md` (wrap with a header noting source and date)
- **URL** → use WebFetch to grab the content; write to `<slug>/job_description.md` with a `> Source: <url>` line and fetch date at the top
- **File path** → copy into `<slug>/job_description.<original-ext>`, preserving the original extension as-is. Do NOT convert the format.

### 6. Scaffold company.md

Use `templates/company.md.template`, substituting:
- `{{COMPANY}}` — original casing (e.g. "Acme Robotics", not the slug)
- `{{ROLE}}` — the role label
- `{{DATE}}` — today's date in ISO (YYYY-MM-DD)
- `{{PORTAL}}` — ask user if known, else leave blank

### 7. Copy master HTML

Find the master: `<workspace>/<First>_<Last>_<Role>_CV.html` (glob for `*_CV.html` at workspace root, not inside company folders).

Copy to `<slug>/<First>_<Last>_<NewRole>_CV.html`. The role in the filename matches the **target role**, not the master's role, since tailoring often reframes the title.

**Do not generate the PDF yet**; tailoring will edit the HTML first.

### 8. Offer to chain

Prompt user:
- **Tailor now** → invoke `resume-tailoring` skill with the JD and this company's HTML as context
- **Tailor later** → stop here; user can run tailoring manually

### 9. Output summary

```
✓ Created <workspace>/<slug>/
  ├── company.md
  ├── job_description.md
  └── <First>_<Last>_<NewRole>_CV.html

Next:
  - Edit company.md with company details
  - Run resume-tailoring to tailor the CV
  - $job-hunt-toolkit:export-pdf to regenerate PDF
  - $job-hunt-toolkit:prepare-to-send before sending
```

## Hard rules

- **Validate company slug** against the deny-list before creating the folder. Reject slugs containing spaces, pipes, commas, slashes, emojis, or non-ASCII characters.
- **Never overwrite an existing company folder** without explicit confirmation.
- **Never copy the master PDF** — only HTML. The PDF will be regenerated after tailoring.
- **Never include the company name in the CV filename** (see `references/naming-rules.md` in the plugin).
- **Save the JD verbatim.** Don't paraphrase or summarize. The raw JD is evidence for tailoring decisions.

## Error handling

| Scenario | Action |
|---|---|
| Workspace doesn't exist | Stop; direct user to `init-workspace` |
| Master HTML not found | Stop; ask user to create one or run `init-workspace` |
| WebFetch fails on JD URL | Ask user to paste the JD text instead |
| Slug contains denied characters | Reject; show deny-list; ask user for corrected slug |
| Role label contains invalid characters | Reject; show naming rules; ask again |
