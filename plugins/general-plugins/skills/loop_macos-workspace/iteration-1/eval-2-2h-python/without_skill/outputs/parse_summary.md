# parse_summary.md

## What the user asked for

> schedule running python ~/scripts/cleanup_tmp.py every 2 hours

## Interpretation

- **Script**: `~/scripts/cleanup_tmp.py` — expanded to the absolute path `/Users/jhonsmith/scripts/cleanup_tmp.py` (launchd does not expand `~` at runtime, so the absolute path is required).
- **Interpreter**: `/usr/bin/python3` — the macOS system Python 3. If the user manages Python via pyenv, Homebrew, or uv, the path should be updated to the appropriate interpreter (e.g. the output of `which python3` in their active shell).
- **Schedule**: every 2 hours = every 7200 seconds.

## Key decisions

### `StartInterval` vs `StartCalendarInterval`

Two launchd mechanisms exist for recurring schedules:

| Key | Behaviour |
|-----|-----------|
| `StartInterval <seconds>` | Fires every N seconds measured from the last run. Simple, drift-free for fixed intervals. |
| `StartCalendarInterval` | Fires at wall-clock times (like cron). Requires specifying exact hours. |

"Every 2 hours" is an interval-based request (not "at 00:00, 02:00, …"), so `StartInterval 7200` is the natural fit. It is simpler and avoids having to enumerate 12 calendar entries.

### `RunAtLoad false`

Set to `false` so the job does not run immediately when the plist is loaded — it waits for the first 2-hour tick. If the user wants an immediate first run on load, this should be changed to `<true/>`.

### Label

`local.cleanup_tmp` follows the reverse-DNS convention (`<domain>.<job>`). The `local.` prefix is conventional for user-defined agents that are not tied to an application bundle.

### Log paths

stdout and stderr are redirected to `/tmp/cleanup_tmp.{stdout,stderr}.log`. `/tmp` is writable by all users and is appropriate for transient logs. If the user wants persistent logs they should change these paths to something under `~/Library/Logs/` or a project directory.

## What was NOT done (intentionally)

- `launchctl load` was not run — the plist was not installed into `~/Library/LaunchAgents/`. The file is a generated artifact only.
- `launchctl start` was not run.
- The script itself was not modified or inspected.

## To actually install (user must do this manually)

```bash
cp output.plist ~/Library/LaunchAgents/local.cleanup_tmp.plist
launchctl load ~/Library/LaunchAgents/local.cleanup_tmp.plist
```

Verify it is registered:
```bash
launchctl list | grep cleanup_tmp
```
