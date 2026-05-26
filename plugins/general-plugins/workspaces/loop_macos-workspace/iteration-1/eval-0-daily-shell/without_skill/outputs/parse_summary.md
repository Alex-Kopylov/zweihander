# parse_summary — eval-0-daily-shell

## Prompt interpretation

| Field | Value |
|---|---|
| Raw prompt | `loop_macos each day run bash ~/.claude/my-marketplace/bin/sync-anthropic-skills.sh` |
| Recurrence | Daily |
| Trigger time | 09:00 local time (chosen default — no time was specified) |
| Command | `/bin/bash /Users/jhonsmith/.claude/my-marketplace/bin/sync-anthropic-skills.sh` |

The phrase "each day" maps unambiguously to a once-per-day schedule. No specific clock time was given, so 09:00 was chosen as a sensible working-hours default that fires after the machine is likely already awake.

## Key design decisions

### 1. StartCalendarInterval over StartInterval

`StartCalendarInterval` (calendar-based) was used instead of `StartInterval` (seconds-based) because:
- "Each day" is a human calendar concept — the user expects it to fire once per day at a predictable clock time, not every N seconds from an arbitrary start epoch.
- `StartCalendarInterval` with only `Hour`/`Minute` set fires at that time every day of every week of every month, which is exactly the intended behavior.
- `StartInterval` with 86400 seconds would drift and not honour DST transitions cleanly.

### 2. Absolute path for the script

`~` is not expanded by launchd because it runs without a shell. The tilde in the user's prompt was expanded to the full absolute path `/Users/jhonsmith/.claude/my-marketplace/bin/sync-anthropic-skills.sh`.

### 3. Explicit bash invocation

`ProgramArguments` uses `["/bin/bash", "<script>"]` rather than pointing directly at the script as `Program`. This ensures:
- The shebang line inside the script is irrelevant — bash is guaranteed.
- The script does not need to be chmod +x.

### 4. RunAtLoad = false

`RunAtLoad` is set to `false` (and is included explicitly for clarity). The user asked for a daily cadence, not "also run immediately when the agent is loaded". Firing at load could cause an unexpected sync run during a launchctl bootstrap.

### 5. Log files

stdout and stderr are directed to separate files under `.../logs/` so runs are auditable without having to query `log show`. The log directory (`~/.claude/my-marketplace/logs/`) must exist before the job fires — it is not created automatically by launchd.

### 6. What was intentionally omitted

| Key | Reason omitted |
|---|---|
| `EnvironmentVariables` | Not needed; the script is expected to be self-contained. Add if the script relies on PATH entries not present in launchd's minimal environment. |
| `WorkingDirectory` | Not required unless the script uses relative paths. |
| `UserName` | Omitted — this plist is intended for `~/Library/LaunchAgents/` (per-user agent), so launchd already runs it as the owning user. |
| `KeepAlive` | Not a daemon; no need to restart on exit. |
| `ThrottleInterval` | Not needed for a once-daily calendar job. |

## Validation result

```
plutil -lint output.plist
output.plist: OK
```

## Activation instructions (not executed)

To activate (do this manually when ready):

```bash
# 1. Ensure the log directory exists
mkdir -p ~/.claude/my-marketplace/logs

# 2. Copy the plist to the user LaunchAgents directory
cp output.plist ~/Library/LaunchAgents/com.user.claude.sync-anthropic-skills.plist

# 3. Load it into launchd
launchctl load ~/Library/LaunchAgents/com.user.claude.sync-anthropic-skills.plist

# 4. Verify it is registered
launchctl list | grep sync-anthropic-skills
```

To change the firing time, edit `Hour`/`Minute` in the plist and reload.
