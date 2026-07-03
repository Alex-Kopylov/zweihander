---
name: ai-insights-hunter
description: Use this skill when the user says "/ai-insights-hunter", "extract insights from conversation", "harvest this session", "what should we remember from this chat", "save insights from this conversation", or provides a path to an AI Assistant conversation log and wants to capture decisions, patterns, and preferences for future sessions. This skill reads a full conversation log (or finds it automatically), extracts valuable insights using parallel agents, interviews the user about what to keep, then stores the chosen insights in the right places to improve future AI Assistant interactions. Use PROACTIVELY when a long or complex session is wrapping up and the user wants to preserve learnings.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
allowed-tools: AskUserQuestion, Read, Write, Agent, TaskCreate, TaskGet, TaskList, TaskUpdate, TaskOutput, TaskStop, Glob, Bash
---

# AI Insights Hunter

Extract valuable, reusable knowledge from an AI Assistant conversation log and store it in the right places so future AI Assistant sessions start smarter.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## References

- `references/writing-conventions.md` — diff format, inline command style, pre-write checklist. Read when writing to files.

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

Use the default conversation-log directory for the active AI Assistant runtime.

Find logs automatically:
1. Determine the current project path (working directory)
2. Encode it: replace `/` with `-` and leading `/` drops (e.g. `/Users/foo/bar` → `Users-foo-bar`)
3. List JSONL files under the default conversation-log directory for the active AI Assistant runtime, sorted by modification time
4. The most recent file is the current session's main log

### Multi-agent sessions

If the session used `Agent` with `TeamCreate` or parallel `TaskCreate` subagents, find their separate conversation logs:

1. Note the main log's timestamp
2. List **all** JSONL files across known AI Assistant conversation-log roots modified within ~5 minutes of the main log's mtime
3. Each file from that window is a candidate agent log — read the first few messages of each to confirm relevance (same project context, related task content)
4. Collect all confirmed agent logs alongside the main log

**Run the full insight extraction pipeline on each log independently** — one set of 4 parallel agents per conversation log. Label findings with their source log so the user knows which agent session produced them.

---

## Step 2 — Parallel Insight Extraction

For each conversation log, read all agent specs defined in `agents/`, then spawn those agents simultaneously in a single message. Pass the full log content to each agent's prompt.

If there are multiple logs (multi-agent session), spawn every `agents/` hunter for each log in a single message — all in parallel.

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
| User behavior / how they like AI Assistants to work | Runtime memory file or `<path_to_where_the_ai_assistant_stores_memory>/<memory_file>` |
| Applies to all projects | Global agent instruction file |
| Applies to one project | `{project}/AGENTS.md` or the runtime-specific project instruction file |
| Relates to a specific subdirectory | `{that-dir}/AGENTS.md` or the runtime-specific instruction file |
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
- **Store**: write immediately, update task to `completed`, acknowledge: `#3 stored -> {path} · 3/8 done`
- **Store elsewhere**: ask for path, then write and complete
- **Skip**: mark task `skipped`

**Writing rules:**

For **agent instruction files** — show a diff block first, explain why in one line, then apply only after the user confirms "Store":

```
### Update: {file path}
**Why:** [one-line reason this helps future sessions]

\`\`\`diff
+ [the addition — keep it brief, one concept per line]
\`\`\`
```

For memory files — use the memory frontmatter format (name, description, type), add a pointer from the runtime's memory index when one exists. Show the full content in the `preview` before writing.

General: prefer editing existing files over creating new ones. Group related insights into the same file rather than scattering them.

Avoid writing:
- Generic best practices ("always write tests", "use meaningful names") — universal advice, not session-specific
- One-off fixes unlikely to recur
- Verbose explanations — if a one-liner suffices, use it

If the user explores an item, asks questions, or revisits a decision, continue the side conversation, then use `TaskList` to re-orient and resume.

---

## Step 7 — Targeted Quality Check on Modified Files

Use `$ai-assistant-ops:agents-md-improver` when available, scoped only to the files written during Step 6.

Before it runs, tell it explicitly: "Focus only on these files that were just modified: [list]. Do not audit pre-existing content — only check whether the new additions conflict with, duplicate, or contradict what was already there."

The `$ai-assistant-ops:agents-md-improver` skill will read the files, score the additions, and flag any issues. Its quality criteria (conciseness, actionability, no obvious info) apply directly to what we just wrote.

If no issues are found, it will say so — no further action needed.

---

## Step 8 — Summary

```
## Insights Hunter — Complete

Stored [n] insights, skipped [n].

| # | Tier | Finding | Stored at |
|---|------|---------|-----------|
| 1 | HIGH | ... | ~/.agents/AGENTS.md |
| 2 | HIGH | ... | project/AGENTS.md |
| 3 | MED  | ... | skipped |
```

---

## Hard rules

- Never store secrets, credentials, tokens, or API keys.
- Keep it concise — one line per concept.
- Step 7 with `$ai-assistant-ops:agents-md-improver` is mandatory when the skill is available and must be scoped to only files modified during this session — never a full repo audit of pre-existing content.
