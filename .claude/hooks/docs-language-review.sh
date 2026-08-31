#!/bin/sh
# PostToolUse hook. Hand one written documentation file to a separate agent.
#
# The `if` rules in .claude/settings.json decide the scope. This script holds no
# path logic. It starts a separate `claude` process so the rewrite never runs in
# the session that triggered the hook. `--bare` skips hook discovery, so the
# agent's own edit cannot re-enter this hook.

# Prefer jaq. Fall back to jq. Without either, the hook does nothing.
if command -v jaq >/dev/null 2>&1; then
  json=jaq
elif command -v jq >/dev/null 2>&1; then
  json=jq
else
  exit 0
fi

file=$("$json" -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)
[ -n "$file" ] && [ -f "$file" ] || exit 0

claude -p "Read ${CLAUDE_PROJECT_DIR}/common/docs-language-guidelines.md and apply it to exactly one file: ${file}. Edit no other file. If ${file} already follows the guidelines, change nothing." \
  --bare --model haiku --permission-mode acceptEdits \
  --tools Read,Edit --max-turns 30 >/dev/null 2>&1

exit 0
