#!/bin/bash
# Fast assertion checker for loop_macos evals
# Usage: bash grade.sh
# Reads output.plist from each eval dir and checks assertions

ITER="$(dirname "$0")"
PASS=0; FAIL=0

check() {
  local label="$1" result="$2"
  if [ "$result" = "1" ]; then
    echo "  ✓ $label"; ((PASS++))
  else
    echo "  ✗ $label"; ((FAIL++))
  fi
}

plist_contains() { grep -qF "$2" "$1" 2>/dev/null && echo 1 || echo 0; }
plist_not_contains() { grep -qF "$2" "$1" 2>/dev/null && echo 0 || echo 1; }
plist_valid() { plutil -lint "$1" >/dev/null 2>&1 && echo 1 || echo 0; }

run_eval() {
  local name="$1" dir="$2"
  local plist="$dir/output.plist"
  echo ""
  echo "=== $name ==="
  if [ ! -f "$plist" ]; then echo "  MISSING: output.plist not found"; ((FAIL++)); return; fi

  case "$name" in
    eval-0-*)
      check "uses_StartCalendarInterval"  "$(plist_contains "$plist" '<key>StartCalendarInterval</key>')"
      check "command_preserved"       "$(plist_contains "$plist" '/usr/bin/true')"
      check "label_com.user.loop-macos"   "$(plist_contains "$plist" 'com.user.loop-macos.')"
      check "no_each_day_in_command"      "$(plist_not_contains "$plist" 'each day')"
      check "valid_plist"                 "$(plist_valid "$plist")"
      ;;
    eval-1-*)
      check "uses_StartInterval"          "$(plist_contains "$plist" '<key>StartInterval</key>')"
      check "interval_is_1800"            "$(plist_contains "$plist" '<integer>1800</integer>')"
      check "label_com.user.loop-macos"   "$(plist_contains "$plist" 'com.user.loop-macos.')"
      check "no_30m_in_command"           "$(plist_not_contains "$plist" '30m')"
      check "valid_plist"                 "$(plist_valid "$plist")"
      ;;
    eval-2-*)
      check "uses_StartInterval"          "$(plist_contains "$plist" '<key>StartInterval</key>')"
      check "interval_is_7200"            "$(plist_contains "$plist" '<integer>7200</integer>')"
      check "python_in_command"           "$(plist_contains "$plist" 'python')"
      check "cleanup_tmp_in_command"      "$(plist_contains "$plist" 'cleanup_tmp.py')"
      check "no_every_2_hours_in_cmd"     "$(plist_not_contains "$plist" 'every 2 hours')"
      check "label_com.user.loop-macos"   "$(plist_contains "$plist" 'com.user.loop-macos.')"
      check "valid_plist"                 "$(plist_valid "$plist")"
      ;;
  esac
}

for eval_dir in "$ITER"/eval-*/; do
  eval_name="$(basename "$eval_dir")"
  run_eval "$eval_name [with_skill]"   "$eval_dir/with_skill/outputs"
  run_eval "$eval_name [without_skill]" "$eval_dir/without_skill/outputs"
done

echo ""
echo "=== TOTAL: $PASS passed, $FAIL failed ==="
