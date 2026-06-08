---
name: init-workspace
description: Use when the user asks to "initialize job hunt workspace", "set up job seeking folder", "create CV workspace", "bootstrap resume folder", "prepare job search folder", "start job hunt setup", "create application tracking workspace", "first time setup for job applications", or is starting the job-hunt-toolkit for the first time. Creates the workspace directory structure, generates README/AGENTS.md/NAMING.md from plugin templates, copies master HTML CV into workspace, and primes the workspace for per-company folders.
argument-hint: "[workspace-path] (optional, defaults to ~/Documents/job_seeking)"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Initialize Workspace

One-time setup for a job-hunt workspace: create the folder structure, generate docs from plugin templates, and copy the master CV.

## When to use

- User has never run this plugin before and wants to start tracking applications.
- User wants to re-seed workspace docs after the plugin has been updated.
- User wants to set up a separate workspace (different path).

## Inputs

- **Workspace path** (optional argument): where to create the workspace. Default `~/Documents/job_seeking`. Resolve `~` to the real home.
- **Name**: first + last name for filename generation (ask user if not obvious from memory/context).
- **Role**: default/primary role for the master CV filename (e.g. `AI_LLM_ML_Engineer`). Ask user.

## Workflow

### 1. Check preconditions

- Resolve target path.
- If the directory already exists AND contains `AGENTS.md`, ask the user:
  - **Overwrite docs** — regenerate README, AGENTS.md, NAMING.md from plugin templates (fresh source of truth)
  - **Abort** — do nothing
  - **New path** — pick a different location
- If the directory exists but is empty, proceed (treat as greenfield).
- If it doesn't exist, create it with `mkdir -p`.

### 2. Gather naming info

Ask via `AskUserQuestion` if not supplied:
- First name
- Last name
- Default role label (e.g. `AI_LLM_ML_Engineer`, `Senior_ML_Engineer`)

Validate against `references/naming-rules.md` (underscores only, ASCII only).

### 3. Prompt for master CV

Use `AskUserQuestion` for the absolute path to the existing master CV HTML file.

- If the user provides a valid, readable `.html` path: **copy** it into the workspace root as `<First>_<Last>_<Role>_CV.html` and leave the source untouched. Print: `✓ Master CV copied to <workspace>/<First>_<Last>_<Role>_CV.html`.
- If the user provides no path, an empty value, or a path that does not exist / is not readable: **HARD ERROR** — print exactly:

  ```
  No CV file provided. A master HTML CV is required to initialize the workspace. Please provide a valid path and re-run.
  ```

  Stop entirely.

### 4. Scaffold files

Write these files from this plugin's `references/` directory and templates at generation time. **Do not copy-paste from stale snapshots.**

- `README.md` — workspace overview. Use `templates/README.md.template`, substituting `<First>`, `<Last>`, `<Role>`.
- `AGENTS.md` — workspace-local agent rules. Use `templates/AGENTS.md.template`. Reference the plugin `AGENTS.md` for authoritative rules.
- `NAMING.md` — quick reference. Use `templates/NAMING.md.template`, but prefer linking back to the plugin's `references/naming-rules.md` rather than duplicating content that will drift.
- `.gitignore` — Write with standard ignore patterns for local notes, editor artifacts, and sensitive files:
  ```
  *.local.md
  salary_notes.md
  .DS_Store
  *~
  .#*
  .vscode/
  .idea/
  ```

### 5. Finalize

Print a "next steps" block pointing to `new-application` and `prepare-to-send`.

## Hard rules

- **A master HTML CV is mandatory.** If not provided, initialization stops with a hard error (see step 3).
- **Never overwrite an existing master CV file** without explicit user confirmation. Master CVs are irreplaceable.
- **Never delete existing `<company>/` folders** — they may contain application history.
- **Always use absolute paths** in bash — `cd` state doesn't persist between tool calls.
- **Regenerate docs from plugin references**, not from prior workspace state. The plugin is the source of truth.

## Error handling

| Scenario | Action |
|---|---|
| No CV path provided or path invalid | Hard error: "No CV file provided. A master HTML CV is required to initialize the workspace. Please provide a valid path and re-run." Stop entirely. |
| Target dir exists with existing docs | Ask user: overwrite / abort / new path |
| User declines to provide name | Use placeholders `<First>_<Last>` and warn that filenames need manual fixup |

## Output

After success, print:

```
✓ Workspace initialized at <path>
✓ Master CV copied to <path>/<First>_<Last>_<Role>_CV.html
✓ Docs generated from plugin templates

Next:
  $job-hunt-toolkit:new-application <company-slug>   # start an application
  $job-hunt-toolkit:export-pdf                       # generate master PDF from HTML
```
