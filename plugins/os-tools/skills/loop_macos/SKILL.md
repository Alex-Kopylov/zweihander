---
name: loop_macos
description: >
  Schedule a recurring shell command or AI Assistant prompt using macOS launchd — persistent, no expiry,
  survives reboots, and catches up missed runs after sleep. Use this instead of /loop whenever the
  user wants a task to keep running permanently (not just 7 days), mentions launchd, says "run this
  every day", "schedule this on macOS", "make this persistent", "set this up for good", "keep this
  running forever", or is frustrated that /loop expired. Also triggers on /loop_macos.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# loop_macos

Use macOS launchd for recurring tasks that persist across reboots. Calendar schedules catch up missed runs after sleep.

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Step 1 — Parse the input

Use these parsing rules:

1. **Leading token** — if the first whitespace-delimited token matches `^\d+[smhd]$` (e.g. `5m`, `2h`, `1d`), that is the interval; everything after is the task.
2. **Trailing "every" clause** — if the input ends with `every <N><unit>` or `every <N> <unit-word>` (e.g. `every 20m`, `every 2 hours`), extract that as the interval and strip it from the task.
3. **Calendar phrases anywhere** — "each day", "daily", "every day", "every morning", "every night" → daily. "every monday/tuesday/…" → weekly on that weekday. Extract explicit clock times ("at 9am", "at 11:30pm") when present.
4. **Default** — interval is `10m`, entire input is the task.

If the resulting task is empty after parsing, ask the user what they want to schedule. Don't proceed.

## Step 2 — Choose the launchd schedule key

Two mechanisms — pick based on interval length:

### `StartInterval` (seconds) — for sub-daily intervals
Fires every N seconds while awake. Sleep resets the timer on wake with no catch-up; acceptable for short intervals.

| User input | `StartInterval` value | Notes |
|---|---|---|
| `Ns` | `ceil(N/60)*60` | Min 60 s; tell the user if rounded |
| `Nm` | `N * 60` | |
| `Nh` | `N * 3600` | |

### `StartCalendarInterval` — for daily/weekly schedules
Fires at specific clock times. **Does** catch up after sleep — fires once on the next wake if the Mac was off at the scheduled time.

```xml
<!-- Every day at 9:07 AM (default when user says "daily" with no time) -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>7</integer>
</dict>

<!-- Every Monday at 9:07 AM -->
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key><integer>1</integer><!-- 0=Sun … 6=Sat -->
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>7</integer>
</dict>
```

Default time when the user doesn't specify: **9:07 AM** (off the :00 mark to avoid server-side pile-ups). Tell the user what time you picked.

## Step 3 — Identify task type and expand paths

**Shell command** — use a shell command when the task:
- starts with `bash`, `python`, `node`, `ruby`, a path (`/`, `~`), or ends with `.sh`, `.py`, `.rb`, `.js`
- describes a deterministic system operation (file listing, backup, sync, cleanup, copy, move, log rotation) that a one-liner or short script handles cleanly

**AI Assistant prompt** — use the user's configured non-interactive AI Assistant command when the task requires reasoning, summarising, deciding, or acting on ambiguous output (e.g. "summarise my emails", "review logs and flag issues").

When in doubt between the two, prefer shell — it's cheaper, faster, and more reliable in a daemon context.

Use `/bin/bash -lc '…'` as the shell so PATH includes Homebrew (`/opt/homebrew/bin`) and user installs (`~/.local/bin`), where AI Assistant CLIs and custom tools typically live.

If the task string contains single quotes, escape them as `'\''` inside the shell string, or write a tiny wrapper script.

**Tilde expansion — critical:** launchd does NOT expand `~` or `$HOME` in plist strings. Replace `~/…` with the absolute home path from `echo "$HOME"` (for example, `/Users/<username>/…`) in shell commands and AI Assistant prompts.

## Step 4 — Generate a label

Format: `com.user.loop-macos.<slug>`

Derive the slug from the task: lowercase, keep alphanumeric and hyphens, collapse everything else to a single hyphen, trim to 30 chars.

Examples:
- `bash ~/my-marketplace/bin/sync.sh` → `com.user.loop-macos.sync-sh`
- `check the deploy log` → `com.user.loop-macos.check-the-deploy-log`

## Step 5 — Write and load the plist

Plist path: `~/Library/LaunchAgents/<label>.plist`
Log path: `~/Library/Logs/loop-macos/<label>.log` (stdout and stderr merged here)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>COMMAND</string>
    </array>

    <!-- Insert StartInterval OR StartCalendarInterval here, not both -->

    <key>StandardOutPath</key>
    <string>LOG_PATH</string>
    <key>StandardErrorPath</key>
    <string>LOG_PATH</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

Installation sequence:
```bash
mkdir -p ~/Library/Logs/loop-macos

# Unload first if label already exists (silent if not)
launchctl unload ~/Library/LaunchAgents/<label>.plist 2>/dev/null || true

# Write the plist (use Write tool, not echo)
# Then load:
launchctl load ~/Library/LaunchAgents/<label>.plist

# Confirm registration:
launchctl list | grep <label>
```

A `-  0  <label>` line means registered and idle (not currently running). That's correct.

## Step 6 — Run immediately, then report

After loading, run the task once right away so the user sees it work immediately:

```bash
launchctl start <label>
```

Then tell the user what is scheduled, when it runs next, where logs go, and the management label.

```
Scheduled: com.user.loop-macos.sync-sh
Runs: daily at 9:07 AM (catches up if Mac was asleep)
Logs: ~/Library/Logs/loop-macos/com.user.loop-macos.sync-sh.log

Management:
  tail -f ~/Library/Logs/loop-macos/<label>.log   # live log
  launchctl start <label>                          # run now
  launchctl stop  <label>                          # stop running instance
  launchctl unload ~/Library/LaunchAgents/<label>.plist && \
    rm ~/Library/LaunchAgents/<label>.plist        # remove permanently
```

## Edge cases

| Situation | What to do |
|---|---|
| No task after parsing | Ask the user what to schedule |
| Sub-minute interval (`5s`) | Round up to 60 s; mention it |
| Daily with no clock time | Default 9:07 AM; mention it |
| Label already exists | Unload old job silently, then overwrite |
| Task has single quotes | Escape as `'\''` or use a wrapper script |
| User only types `/loop_macos` | Ask what to schedule and at what interval |
