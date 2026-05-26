#!/bin/bash
# Iteration-2 assertion checker — with-skill only
ITER="$(dirname "$0")"
PASS=0; FAIL=0

check() {
  local label="$1" result="$2"
  if [ "$result" = "1" ]; then echo "  ✓ $label"; ((PASS++))
  else echo "  ✗ $label"; ((FAIL++)); fi
}

contains()     { grep -qF "$2" "$1" 2>/dev/null && echo 1 || echo 0; }
not_contains() { grep -qF "$2" "$1" 2>/dev/null && echo 0 || echo 1; }
valid_plist()  { plutil -lint "$1" >/dev/null 2>&1 && echo 1 || echo 0; }

echo "=== eval-0-daily-shell [with_skill] ==="
P="$ITER/eval-0-daily-shell/with_skill/outputs/output.plist"
[ -f "$P" ] || { echo "  MISSING"; ((FAIL++)); }
check "uses_StartCalendarInterval"  "$(contains "$P" '<key>StartCalendarInterval</key>')"
check "script_path_preserved"       "$(contains "$P" 'sync-anthropic-skills.sh')"
check "label_com.user.loop-macos"   "$(contains "$P" 'com.user.loop-macos.')"
check "no_each_day_in_command"      "$(not_contains "$P" 'each day')"
check "tilde_expanded"              "$(not_contains "$P" '~/')"
check "valid_plist"                 "$(valid_plist "$P")"

echo ""
echo "=== eval-1-30min-downloads [with_skill] ==="
P="$ITER/eval-1-30min-downloads/with_skill/outputs/output.plist"
[ -f "$P" ] || { echo "  MISSING"; ((FAIL++)); }
check "uses_StartInterval"          "$(contains "$P" '<key>StartInterval</key>')"
check "interval_is_1800"            "$(contains "$P" '<integer>1800</integer>')"
check "label_com.user.loop-macos"   "$(contains "$P" 'com.user.loop-macos.')"
check "no_30m_in_command"           "$(not_contains "$P" '30m')"
check "uses_shell_not_claude_p"     "$(not_contains "$P" 'claude -p')"
check "valid_plist"                 "$(valid_plist "$P")"

echo ""
echo "=== eval-2-2h-python [with_skill] ==="
P="$ITER/eval-2-2h-python/with_skill/outputs/output.plist"
[ -f "$P" ] || { echo "  MISSING"; ((FAIL++)); }
check "uses_StartInterval"          "$(contains "$P" '<key>StartInterval</key>')"
check "interval_is_7200"            "$(contains "$P" '<integer>7200</integer>')"
check "python_in_command"           "$(contains "$P" 'python')"
check "cleanup_tmp_in_command"      "$(contains "$P" 'cleanup_tmp.py')"
check "no_every_2_hours_in_cmd"     "$(not_contains "$P" 'every 2 hours')"
check "label_com.user.loop-macos"   "$(contains "$P" 'com.user.loop-macos.')"
check "tilde_expanded"              "$(not_contains "$P" '~/')"
check "valid_plist"                 "$(valid_plist "$P")"

echo ""
echo "=== TOTAL: $PASS passed, $FAIL failed ==="
