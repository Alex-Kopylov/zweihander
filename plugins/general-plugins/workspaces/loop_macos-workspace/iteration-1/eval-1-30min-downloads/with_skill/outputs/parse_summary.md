# Parse Summary — eval-1-30min-downloads

## Input prompt
```
loop_macos 30m check if there are any new files in ~/Downloads and print their names to a log
```

## Step 1 — Interval parsed
- **Rule applied:** Leading token (`30m`) matches `^\d+[smhd]$`
- **Interval:** 30 minutes
- **Task (remainder):** `check if there are any new files in ~/Downloads and print their names to a log`

## Step 2 — Schedule key used
- **Key:** `StartInterval`
- **Value:** `1800` seconds (30 × 60)
- **Rationale:** Sub-daily interval → `StartInterval`. Note: timer resets on wake; no catch-up after sleep. Acceptable for short polling intervals.

## Step 3 — Task type decision
- **Decision:** Claude prompt (not a shell command)
- **Reason:** Task string does not start with `bash`, `python`, `node`, `ruby`, a `/` or `~` path, and does not end with `.sh`, `.py`, `.rb`, or `.js`.
- **Wrap applied:** `claude -p '...'` inside `/bin/bash -lc '...'`

## Step 4 — Command string
```
/bin/bash -lc "claude -p 'check if there are any new files in ~/Downloads and print their names to a log'"
```

(In the plist ProgramArguments array, the third `<string>` element is the `-lc` argument.)

## Step 5 — Label
- **Slug derivation:** task text → lowercase → collapse non-`[a-z0-9]` runs to `-` → `check-if-there-are-any-new-files-in-downloads-and-print-their-names-to-a-log` → trim to 30 chars → `check-if-there-are-any-new-fi`
- **Full label:** `com.user.loop-macos.check-if-there-are-any-new-fi`

## Validation
```
plutil -lint output.plist
output.plist: OK
```

## Output files
| File | Path |
|---|---|
| Plist | `outputs/output.plist` |
| This summary | `outputs/parse_summary.md` |

## What would happen at runtime (not executed)
- Plist destination: `~/Library/LaunchAgents/com.user.loop-macos.check-if-there-are-any-new-fi.plist`
- Log destination: `~/Library/Logs/loop-macos/com.user.loop-macos.check-if-there-are-any-new-fi.log`
- Fires every 30 minutes while Mac is awake (no catch-up on wake from sleep)
