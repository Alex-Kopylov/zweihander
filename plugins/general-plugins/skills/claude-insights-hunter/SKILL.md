---
name: claude-insights-hunter
description: Use this skill when the user says "/claude-insights-hunter", "extract insights from conversation", "harvest this session", "what should we remember from this chat", "save insights from this conversation", or provides a path to a Claude Code conversation log and wants to capture decisions, patterns, and preferences for future sessions. This skill reads a full conversation log (or finds it automatically), extracts valuable insights using parallel agents, interviews the user about what to keep, then stores the chosen insights in the right places to improve future Claude interactions. Use PROACTIVELY when a long or complex session is wrapping up and the user wants to preserve learnings.
allowed-tools: AskUserQuestion, Read, Write, Agent, TaskCreate, TaskGet, TaskList, TaskUpdate, TaskOutput, TaskStop, Glob, Bash
---

# Claude Insights Hunter

Extract valuable, reusable knowledge from a Claude Code conversation log and store it in the right places so future Claude sessions start smarter.

## Agent specs

Read these files before spawning the corresponding agents:

- `agents/decisions-hunter.md` — technical decisions & architectural choices
- `agents/preferences-hunter.md` — user preferences & feedback patterns
- `agents/patterns-hunter.md` — reusable patterns & proven approaches
- `agents/project-context-hunter.md` — project-specific facts & context

---

## Step 1 — Locate Conversation Logs

### If a path was provided

Use it directly. If it's a directory, list `.jsonl` files inside and pick the most recent.

### If no path was provided

Claude Code stores conversations at:
```
~/.claude/projects/<project-path-encoded>/conversations/*.jsonl
```

Find logs automatically:
1. Determine the current project path (working directory)
2. Encode it: replace `/` with `-` and leading `/` drops (e.g. `/Users/foo/bar` → `Users-foo-bar`)
3. List JSONL files in `~/.claude/projects/<encoded>/conversations/` sorted by modification time
4. The most recent file is the current session's main log

### Multi-agent sessions

If the session used `Agent` tool with `TeamCreate`, or spawned parallel subagents via `TaskCreate`, those agents ran as separate processes with their own conversation logs. Find them:

1. Note the main log's timestamp
2. List **all** JSONL files across `~/.claude/projects/` modified within ~5 minutes of the main log's mtime
3. Each file from that window is a candidate agent log — read the first few messages of each to confirm relevance (same project context, related task content)
4. Collect all confirmed agent logs alongside the main log

**Run the full insight extraction pipeline on each log independently** — one set of 4 parallel agents per conversation log. Label findings with their source log so the user knows which agent session produced them.

---

## Step 2 — Parallel Insight Extraction

For each conversation log, read the 4 agent spec files, then spawn all 4 agents simultaneously in a single message. Pass the full log content to each agent's prompt.

Agents to spawn (read their spec first):
- `decisions-hunter` — reads `agents/decisions-hunter.md`
- `preferences-hunter` — reads `agents/preferences-hunter.md`
- `patterns-hunter` — reads `agents/patterns-hunter.md`
- `project-context-hunter` — reads `agents/project-context-hunter.md`

If there are multiple logs (multi-agent session), spawn all 4 hunters × N logs in a single message — all in parallel.

Wait for all agents to complete before continuing.

---

## Step 3 — Aggregate and Present

Collect all FINDING blocks. Deduplicate near-identical findings across logs. Group by tier.

Present the full summary:

```
## Insights Hunter — Findings
[N logs analyzed: main session + N agent sessions]

### 🔴 HIGH — Must Store (n items)
1. **[Title]** · Decisions · [source log label]
   [Detail — 1-2 sentences]
...

### 🟡 MEDIUM — Worth Storing (n items)
...

### 🟢 LOW — Optional (n items)
...
```

---

## Step 4 — First Decision: Scope

```
AskUserQuestion({
  questions: [{
    header: "What to store?",
    question: "Found [n-HIGH] must-store, [n-MEDIUM] medium, [n-LOW] low-value insights across [N] conversation logs. Which do you want to walk through?",
    options: [
      { label: "HIGH only", description: "Walk through [n] critical insights" },
      { label: "HIGH + MEDIUM", description: "Walk through [n] insights" },
      { label: "HIGH + MEDIUM + LOW", description: "Walk through all [n] insights" },
      { label: "Skip — store nothing", description: "Exit without saving" }
    ],
    multiSelect: false
  }]
})
```

If "Skip": jump to Step 7.

---

## Step 5 — Build Task List

Create a `TaskCreate` for each selected finding. Each task holds:
- Finding title
- Category (Decisions / Preferences / Patterns / Project Context)
- Tier
- Recommended storage path (your best guess)
- Status: `pending`

Use `TaskList` to confirm all tasks are created before proceeding.

---

## Step 6 — Interview Each Item

Walk through tasks one-by-one using `AskUserQuestion`. For each item, decide: store it? where?

**Storage location guide:**

| Context | Location |
|---------|----------|
| User behavior / how they like Claude to work | `~/.claude/memory/<topic>.md` + pointer in `~/.claude/MEMORY.md` |
| Applies to all projects | `~/.claude/CLAUDE.md` |
| Applies to one project | `{project}/CLAUDE.md` |
| Relates to a specific subdirectory | `{that-dir}/CLAUDE.md` |
| Named reference (patterns log, decisions log) | `{project}/docs/decisions.md` or similar |
| README-level context | `{project}/README.md` |

Include a `preview` showing the exact text that will be written.

**Question format:**

```
AskUserQuestion({
  questions: [{
    header: "#[N] [TIER] — [Category]",
    question: "[Finding title]: [Detail] — Store this?",
    options: [
      {
        label: "Store (Recommended)",
        description: "→ [recommended file path]",
        preview: "[exact content to be written]"
      },
      {
        label: "Store elsewhere",
        description: "I'll tell you where"
      },
      {
        label: "Skip",
        description: "Not worth keeping"
      }
    ],
    multiSelect: false
  }]
})
```

**After each response:**
- **Store**: write immediately, update task to `completed`, acknowledge: `#3 stored → ~/.claude/CLAUDE.md · 3/8 done`
- **Store elsewhere**: ask for path, then write and complete
- **Skip**: mark task `skipped`

**Writing rules:**
- For `CLAUDE.md` files: append to an existing relevant section or add a new one. One insight = 1–3 lines max.
- For `~/.claude/memory/*.md`: use the memory frontmatter format (name, description, type), add pointer to `MEMORY.md`.
- Never create a file for a single sentence — group related insights.
- Prefer editing existing files over creating new ones.

**Digressions are fine.** If the user wants to explore an item, ask questions, or revisit a decision — go with it. After any side conversation, use `TaskList` to re-orient and resume from where you left off.

---

## Step 7 — Audit Only What Was Changed

By the end of the interview you have an exact list of files written to. Run a targeted audit scoped to those files only — not the full setup.

For each file that was modified or created:
1. Read the file
2. Check whether the new content (the lines you just added) conflicts with, duplicates, or contradicts anything already present in that same file
3. If the file is `~/.claude/CLAUDE.md` or a project `CLAUDE.md`, also check against the other CLAUDE.md in the same chain (global → project → subdir) for cross-file conflicts

Then invoke the Skill tool to run the full audit only if conflicts were found — pass context to focus on the affected files:

```
Skill({ skill: "general-plugins:ai-setup-audit" })
```

If no conflicts were found, skip invoking the skill and just report: "No conflicts detected in modified files."

The point is to catch problems introduced *right now*, not to fix pre-existing issues that were there before this session ran.

---

## Step 8 — Summary

```
## Insights Hunter — Complete

Stored [n] insights, skipped [n].

| # | Tier | Finding | Stored at |
|---|------|---------|-----------|
| 1 | HIGH | ... | ~/.claude/CLAUDE.md |
| 2 | HIGH | ... | project/CLAUDE.md |
| 3 | MED  | ... | skipped |
```

---

## Hard rules

- Never store secrets, credentials, tokens, or API keys.
- Keep stored content concise — every word costs future context tokens.
- The Step 7 conflict check is mandatory. It audits only files touched during this session — never pre-existing issues.
