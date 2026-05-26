# Parse Summary

## Input
`schedule running python ~/scripts/cleanup_tmp.py every 2 hours`

## Step 1 — Interval extraction
- Rule applied: **Trailing "every" clause** (Rule 2)
- Detected phrase: `every 2 hours`
- Interval parsed: `2h`
- Task string after stripping interval: `python ~/scripts/cleanup_tmp.py`
  - Note: leading word `schedule running` is retained but interpreted naturally;
    the meaningful task is `python ~/scripts/cleanup_tmp.py`

## Step 2 — Schedule key
- 2h is a sub-daily interval → `StartInterval`
- Value: `2 * 3600 = 7200` seconds

## Step 3 — Task type
- Task starts with `python` → **shell command** (not a Claude prompt)
- Execution wrapper: `/bin/bash -lc 'python ~/scripts/cleanup_tmp.py'`

## Step 4 — Label
- Slug derived from task `python ~/scripts/cleanup_tmp.py`:
  - Lowercase, collapse non-alphanumeric runs to `-`: `python-scripts-cleanup-tmp-py`
  - Length: 29 chars (within 30-char limit)
- **Label:** `com.user.loop-macos.python-scripts-cleanup-tmp-py`

## Output files
- Plist: `output.plist`
- Log path (runtime): `~/Library/Logs/loop-macos/com.user.loop-macos.python-scripts-cleanup-tmp-py.log`

## Validation
`plutil -lint output.plist` → **OK**
