# parse_summary — eval-1-30min-downloads

## Prompt interpretation

| Field | Decision |
|-------|----------|
| Interval | 30 minutes (`StartInterval = 1800` seconds) |
| Trigger | `RunAtLoad true` so the first check fires immediately on load, then every 30 min |
| Detection scope | `~/Downloads`, depth 1 (no subdirectory recursion), dotfiles excluded |
| "New files" definition | Files whose mtime is newer than the timestamp written by the previous run |
| Output | Appended lines in `~/Library/Logs/downloads-new-files.log` |

## Key design decisions

### Schedule key: `StartInterval` vs `StartCalendarInterval`
`StartInterval 1800` was chosen over `StartCalendarInterval` because the prompt says "every 30 minutes" (a fixed cadence), not "at :00 and :30 past every hour" (wall-clock alignment). `StartInterval` counts seconds since the last run, which is the natural interpretation of a polling loop.

### "New files" tracking via a timestamp file (`~/.downloads_last_check`)
`find -newer <file>` compares mtime against the mtime of a reference file, which is the simplest portable approach on macOS without requiring any external tool. The stamp is updated at the end of each run so:
- First ever run: compares against `now - 1800` (synthesised) to avoid a false-positive flood of every existing file.
- Subsequent runs: compares against the real previous run time.

### Why not `find -mmin -30`?
`-mmin -30` measures wall time from *now*, so if launchd fires 31 minutes late (system sleep, load spike) a file that landed at minute 29 would be missed on the next run. The stamp-file approach is edge-safe.

### maxdepth 1
`~/Downloads` is a flat drop zone by convention; users generally do not want subdirectory churn logged as "new files". Depth-1 matches the common mental model.

### Log location: `~/Library/Logs/`
`~/Library/Logs/` is the standard per-user log directory on macOS (visible in Console.app). It is writable without elevated permissions and is excluded from iCloud Drive sync.

### `StandardErrorPath`
Shell errors (permission denied, missing binary) go to a separate error log so they do not pollute the structured file list log.

### `Label`
Reverse-DNS style (`com.user.downloads-new-files-check`) is the launchd convention. Using a descriptive suffix makes the job easy to find with `launchctl list | grep downloads`.

## How to install (not run here per instructions)

```bash
cp output.plist ~/Library/LaunchAgents/com.user.downloads-new-files-check.plist
launchctl load ~/Library/LaunchAgents/com.user.downloads-new-files-check.plist
```

## Log location

```
~/Library/Logs/downloads-new-files.log
~/Library/Logs/downloads-new-files-errors.log
```
