#!/usr/bin/env bash
# body_sha256.sh — print the sha256 of a Markdown file's body below its frontmatter.
#
# Usage: body_sha256.sh <file.md>
#
# The frontmatter is the block between the first two lines that are exactly
# `---`; a file that does not open with `---` is hashed whole. The digest goes
# into the `sha256` field of a converted raw file and is recomputed at lint to
# detect source drift.
set -euo pipefail

file="${1:?usage: body_sha256.sh <file.md>}"
[[ -f "${file}" ]] || { echo "not a file: ${file}" >&2; exit 2; }

if command -v sha256sum >/dev/null 2>&1; then
  hasher=(sha256sum)
else
  hasher=(shasum -a 256)
fi

first_line=""
read -r first_line < "${file}" || true
if [[ "${first_line}" == "---" ]]; then
  awk 'f >= 2 { print } /^---$/ { f++ }' "${file}" | "${hasher[@]}" | awk '{ print $1 }'
else
  "${hasher[@]}" < "${file}" | awk '{ print $1 }'
fi
