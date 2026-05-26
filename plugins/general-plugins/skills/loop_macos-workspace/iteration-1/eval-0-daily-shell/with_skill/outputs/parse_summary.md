# Parse Summary — eval-0-daily-shell

## Input prompt
```
loop_macos each day run bash ~/.claude/my-marketplace/bin/sync-anthropic-skills.sh
```

## Step 1 — Interval parsed
- Trigger phrase: **"each day"** (matches rule 3: calendar phrase)
- Resolved interval: **daily**
- No explicit clock time in prompt → defaulted to **9:07 AM**
- Task string after stripping interval phrase: `bash ~/.claude/my-marketplace/bin/sync-anthropic-skills.sh`

## Step 2 — Schedule key chosen
- `StartCalendarInterval` (daily/weekly schedules — does catch up after sleep)
- Value: `Hour=9, Minute=7`
- Reason: "each day" is a calendar phrase, not a sub-daily interval, so `StartInterval` (seconds) was not used.

## Step 3 — Task type
- Task starts with `bash` → **shell command**
- Wrapped as: `/bin/bash -lc 'bash ~/.claude/my-marketplace/bin/sync-anthropic-skills.sh'`
- Login shell (`-l`) ensures PATH includes Homebrew and `~/.local/bin`

## Step 4 — Label generated
- Raw task: `bash ~/.claude/my-marketplace/bin/sync-anthropic-skills.sh`
- Slug derivation: strip `bash `, lowercase, collapse non-alphanumeric to hyphens → `sync-anthropic-skills-sh` (24 chars, within 30-char limit)
- **Final label: `com.user.loop-macos.sync-anthropic-skills-sh`**

## Step 5 — Output files
- Plist: `outputs/output.plist` (validated OK by `plutil -lint`)
- Log path (when deployed): `~/Library/Logs/loop-macos/com.user.loop-macos.sync-anthropic-skills-sh.log`

## Validation
```
plutil -lint output.plist → OK
```
