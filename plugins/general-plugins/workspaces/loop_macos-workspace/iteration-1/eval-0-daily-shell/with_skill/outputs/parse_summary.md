# Parse Summary — eval-0-daily-shell

## Input prompt
```
loop_macos each day run /usr/bin/true
```

## Step 1 — Interval parsed
- Trigger phrase: **"each day"** (matches rule 3: calendar phrase)
- Resolved interval: **daily**
- No explicit clock time in prompt → defaulted to **9:07 AM**
- Task string after stripping interval phrase: `/usr/bin/true`

## Step 2 — Schedule key chosen
- `StartCalendarInterval` (daily/weekly schedules — does catch up after sleep)
- Value: `Hour=9, Minute=7`
- Reason: "each day" is a calendar phrase, not a sub-daily interval, so `StartInterval` (seconds) was not used.

## Step 3 — Task type
- Task is an absolute executable path → **shell command**
- Wrapped as: `/bin/bash -lc '/usr/bin/true'`
- Login shell (`-l`) ensures PATH includes Homebrew and `~/.local/bin`

## Step 4 — Label generated
- Raw task: `/usr/bin/true`
- Slug derivation: lowercase, collapse non-alphanumeric to hyphens → `true` (4 chars, within 30-char limit)
- **Final label: `com.user.loop-macos.true`**

## Step 5 — Output files
- Plist: `outputs/output.plist` (validated OK by `plutil -lint`)
- Log path (when deployed): `~/Library/Logs/loop-macos/com.user.loop-macos.true.log`

## Validation
```
plutil -lint output.plist → OK
```
