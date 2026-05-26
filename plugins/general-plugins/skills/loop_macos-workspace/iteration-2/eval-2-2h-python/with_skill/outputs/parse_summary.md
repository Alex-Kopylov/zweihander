# Parse Summary

## Input
`schedule running python ~/scripts/cleanup_tmp.py every 2 hours`

## Parsing (Step 1)
- **Interval detection:** trailing "every" clause matched — `every 2 hours` → 2h
- **Task:** `python ~/scripts/cleanup_tmp.py`

## Schedule key (Step 2)
- 2h is a sub-daily interval → `StartInterval`
- Value: 2 × 3600 = **7200 seconds**

## Task type & tilde expansion (Step 3)
- Task starts with `python` and ends with `.py` → classified as **shell command**
- Shell wrapper: `/bin/bash -lc '...'`
- **Tilde expansion applied:** `~` → `/Users/jhonsmith` (via `echo $HOME`)
- `~/scripts/cleanup_tmp.py` → `/Users/jhonsmith/scripts/cleanup_tmp.py`
- No unexpanded `~` or `$HOME` remains in the plist

## Label (Step 4)
- Raw slug from task: `python-users-jhonsmith-scripts-cleanup-tmp-py`
- Trimmed to 30 chars: `python-users-jhonsmith-scripts`
- **Label:** `com.user.loop-macos.python-users-jhonsmith-scripts`

## Plist validation
- `plutil -lint output.plist` → **OK**

## Tilde expansion: PASS
All paths in the plist use absolute `/Users/jhonsmith/...` paths. No tilde characters present.
