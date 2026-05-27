# Parse Summary — eval-0-daily-shell

## Input
```
each day run bash ~/.claude/my-marketplace/bin/refresh-local-cache.sh
```

## Parsing (Step 1)
- **Schedule phrase detected:** "each day" → daily calendar schedule
- **Task type:** shell command (starts with `bash`)
- **Clock time:** not specified → defaulted to 9:07 AM per skill rules

## Schedule key chosen (Step 2)
`StartCalendarInterval` with `Hour=9`, `Minute=7`
Rationale: daily cadence requires calendar-based scheduling (catches up after sleep).

## Tilde expansion (Step 3)
- **Tilde expansion performed:** YES
- `$HOME` resolved to: `/Users/jhonsmith`
- `~/.claude/my-marketplace/bin/refresh-local-cache.sh`
  → `/Users/jhonsmith/.claude/my-marketplace/bin/refresh-local-cache.sh`
- Applied in `ProgramArguments` string and both log path strings.
- launchd does NOT expand `~` or `$HOME` in plist strings; all paths use absolute form.

## Label (Step 4)
`com.user.loop-macos.refresh-local-cache-sh`

## Plist validation
`plutil -lint output.plist` → **OK**

## Summary
Tilde was correctly expanded to the absolute path `/Users/jhonsmith` in all plist string values. No literal `~` or `$HOME` tokens appear anywhere in the output plist.
