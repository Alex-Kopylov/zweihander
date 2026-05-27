---
name: daily
description: Generate a daily note summarizing recent activity across all detected project sources. Use this skill whenever the user asks for a daily note, daily summary, standup report, daily digest, "what happened today/yesterday", end-of-day recap, or wants to capture progress across git, PRs, tasks, and communication channels. Trigger even for casual phrasing like "write up what I did" or "catch me up on the project".
---

# Daily Note Generator

Create a markdown daily note by gathering activity from every source detected in the project.

## Usage

```
/daily [output-dir]
```

- `output-dir` — where to save the note (default: current working directory)
- The **source detection** always runs from the project root (where you are), not the output dir

## Time Window

The window always starts at **previous day's 06:00** and ends at **now**.

```
From: yesterday 06:00  →  To: now
```

If run before 06:00, "yesterday" shifts back one more day (rounding to ~24h).

Examples:
- Run **Tuesday 12:00** → window: **Monday 06:00 – Tuesday 12:00**
- Run **Tuesday 18:00** → window: **Monday 06:00 – Tuesday 18:00**
- Run **Monday 04:00** (before 06:00) → window: **Sunday 06:00 – Monday 04:00**

Use 24h time format everywhere (no AM/PM).

## Workflow

### 1. Detect sources

Read `references/source-detection.md` and follow it to scan the project root. This produces a list of active sources (e.g. `git`, `azure-devops`, `slack`).

### 2. Gather activity per source

For each detected source, read its reference file from `references/sources/<source>.md`. Each file explains:
- What to fetch (PRs, commits, work items, messages...)
- How to fetch it (CLI commands, MCP tools, APIs)
- What fields matter for the daily note

Fetch items **created, updated, or deleted** within the time window. If a source fails or is unavailable, note it and move on — never block the entire note on one source.

### 3. Compose the note

Read `references/daily-note-template.md` for the output format. Write a single markdown file:

```
daily-DD-MM-YYYY.md
```

Saved to the output directory.

### 4. Present summary

After saving, print a short summary to the user: which sources were checked, how many items found, and the file path.
