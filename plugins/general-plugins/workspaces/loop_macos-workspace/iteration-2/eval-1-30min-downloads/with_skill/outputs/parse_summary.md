# parse_summary

## Task type decision: shell command

The task is "check if there are any new files in ~/Downloads and print their names to a log".

Per the skill's Step 3 rules, this qualifies as a **shell command** (not `claude -p`) because:
- It is a deterministic system operation (file listing / directory monitoring).
- It maps cleanly to a `find` one-liner — no reasoning, summarising, or ambiguous output handling required.
- The skill explicitly states "prefer shell — it's cheaper, faster, and more reliable in a daemon context" when in doubt.

## Actual command string used

```
find /Users/jhonsmith/Downloads -maxdepth 1 -mmin -30 -not -name '.*' -newer /Users/jhonsmith/Downloads | while read -r f; do echo "$(date '+%Y-%m-%d %H:%M:%S') NEW: $f"; done
```

### Explanation
- `-maxdepth 1` — only immediate children of Downloads, not subdirectory contents.
- `-mmin -30` — files modified within the last 30 minutes (matching the 30 m interval).
- `-not -name '.*'` — exclude hidden/dot files (e.g. `.DS_Store`, partial downloads).
- `-newer /Users/jhonsmith/Downloads` — secondary guard: only items newer than the directory entry itself (catches truly new additions).
- The `while read` loop prefixes each filename with a timestamp before printing to stdout, which launchd redirects to the log file.

### Tilde expansion
`~/Downloads` was expanded to `/Users/jhonsmith/Downloads` per the skill's critical note that launchd does not expand `~` or `$HOME` in plist strings.

## Schedule
- Mechanism: `StartInterval`
- Value: `1800` seconds (30 minutes × 60)
- Behaviour: fires every 30 minutes while the Mac is awake; timer resets on wake after sleep (no catch-up — acceptable for a short sub-daily interval per skill rules).

## Label
`com.user.loop-macos.check-if-there-are-any-new`

Slug derived from task text: lowercase, non-alphanumeric runs collapsed to `-`, trimmed to 30 chars.

## Log path
`/Users/jhonsmith/Library/Logs/loop-macos/com.user.loop-macos.check-if-there-are-any-new.log`
