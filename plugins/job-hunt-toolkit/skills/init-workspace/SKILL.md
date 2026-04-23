---
name: init-workspace
description: Use when the user asks to "initialize job hunt workspace", "set up job seeking folder", "create CV workspace", "bootstrap resume folder", or is starting the job-hunt-toolkit for the first time. Creates the workspace directory structure, generates README/CLAUDE.md/NAMING.md from plugin templates, initializes git, and primes the workspace for master CV + per-company folders.
argument-hint: [workspace-path] (optional, defaults to ~/Documents/job_seaking)
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Initialize Workspace

One-time setup for a job-hunt workspace. Creates folder structure, generates docs from plugin templates, and initializes git.

## When to use

- User has never run this plugin before and wants to start tracking applications.
- User wants to re-seed workspace docs after the plugin has been updated.
- User wants to set up a separate workspace (different path).

## Inputs

- **Workspace path** (optional argument): where to create the workspace. Default `~/Documents/job_seaking`. Resolve `~` to the real home.
- **Name**: first + last name for filename generation (ask user if not obvious from memory/context).
- **Role**: default/primary role for the master CV filename (e.g. `AI_LLM_ML_Engineer`). Ask user.

## Workflow

### 1. Check preconditions

- Resolve target path.
- If the directory already exists AND contains `.git/` AND `CLAUDE.md`, ask the user:
  - **Overwrite docs** — regenerate README, CLAUDE.md, NAMING.md from plugin templates (fresh source of truth)
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

### 3. Scaffold files

Write these files using the plugin's reference docs as source of truth. **Do not copy-paste from stale snapshots.** Always read from `<plugin-root>/references/` at generation time.

- `README.md` — workspace overview. Use `templates/README.md.template`, substituting `<First>`, `<Last>`, `<Role>`.
- `CLAUDE.md` — workspace-local Claude rules. Use `templates/CLAUDE.md.template`. Reference the plugin CLAUDE.md for authoritative rules.
- `NAMING.md` — quick reference. Use `templates/NAMING.md.template`, but prefer linking back to the plugin's `references/naming-rules.md` rather than duplicating content that will drift.
- `.gitignore` — `.DS_Store`, editor cruft, `*.local.md`.

### 4. Initialize git

```bash
cd <workspace-path>
git init -b main
```

Stage and create the initial commit if there are files:

```bash
git add -A
git -c user.email="<email>" -c user.name="<First> <Last>" commit -m "chore: initialize job-hunt workspace"
```

Use the user's configured git identity if present; otherwise ask.

### 5. Prompt for master CV

After scaffolding:

- Tell the user the workspace is ready.
- Ask: "Do you have an existing master CV in HTML format? If yes, provide the path and I'll move it into the workspace as `<First>_<Last>_<Role>_CV.html`."
- If yes: move (not copy) the HTML into workspace root with the canonical filename. Then invoke the `export-pdf` skill to generate the master PDF.
- If no: suggest they create one and run `export-pdf` when ready.

### 6. Finalize

Commit master HTML+PDF if present:

```bash
git add <master>.html <master>.pdf
git commit -m "add: master CV (<Role>)"
```

Print a "next steps" block pointing to `new-application` and `prepare-to-send`.

## Hard rules

- **Never overwrite an existing master CV file** without explicit user confirmation. Master CVs are irreplaceable.
- **Never delete existing `<company>/` folders** — they may contain committed application history.
- **Never commit PII by default** — the initial commit contains only scaffold docs, no personal info beyond name.
- **Always use absolute paths** in bash — `cd` state doesn't persist between tool calls.
- **Regenerate docs from plugin references**, not from prior workspace state. The plugin is the source of truth.

## Error handling

| Scenario | Action |
|---|---|
| Target dir exists with uncommitted changes | Abort; ask user to commit or back up first |
| `git init` fails (git not installed) | Fail loud with install instructions |
| User declines to provide name | Use placeholders `<First>_<Last>` and warn that filenames need manual fixup |
| HTML CV path invalid | Skip master step; workspace still usable |

## Output

After success, print:

```
✓ Workspace initialized at <path>
✓ Docs generated from plugin templates
✓ Git repo initialized on `main`

Next:
  /job-hunt-toolkit:new-application <company-slug>   # start an application
  /job-hunt-toolkit:export-pdf                       # regenerate master PDF if you edit HTML
```
