#!/usr/bin/env bash

set -euo pipefail

workspace=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
output="$workspace/APPLICATIONS.md"
records_tmp=$(mktemp "$workspace/.applications-records.XXXXXX")
output_tmp=$(mktemp "$workspace/.APPLICATIONS.md.XXXXXX")

cleanup() {
  rm -f "$records_tmp" "$output_tmp"
}
trap cleanup EXIT HUP INT TERM

parse_record() {
  awk '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }

    function scalar(value, first, last) {
      value = trim(value)
      first = substr(value, 1, 1)
      last = substr(value, length(value), 1)
      if (length(value) >= 2 && ((first == "\"" && last == "\"") || (first == "\047" && last == "\047"))) {
        return substr(value, 2, length(value) - 2)
      }
      sub(/[[:space:]]+#.*$/, "", value)
      sub(/^#.*$/, "", value)
      return trim(value)
    }

    function is_null(value, lowered) {
      lowered = tolower(trim(value))
      return lowered == "" || lowered == "null" || lowered == "~"
    }

    NR == 1 {
      if ($0 != "---") {
        exit 2
      }
      in_frontmatter = 1
      next
    }

    in_frontmatter && $0 == "---" {
      closed = 1
      exit
    }

    in_frontmatter && match($0, /^[A-Za-z_][A-Za-z0-9_]*:[[:space:]]*/) {
      key = substr($0, 1, index($0, ":") - 1)
      value = substr($0, index($0, ":") + 1)
      if (key == "company" || key == "role" || key == "status" || key == "applied") {
        if (seen[key]) {
          exit 2
        }
        seen[key] = 1
        values[key] = scalar(value)
      }
    }

    END {
      if (!closed || !seen["company"] || !seen["role"] || !seen["status"] || !seen["applied"]) {
        exit 2
      }
      if (is_null(values["company"]) || is_null(values["role"])) {
        exit 2
      }
      if (values["applied"] == "") {
        exit 2
      }
      if (values["status"] !~ /^(drafting|applied|screening|interview|offer|signed|rejected|withdrew)$/) {
        exit 2
      }
      gsub(/\t/, " ", values["company"])
      gsub(/\t/, " ", values["role"])
      gsub(/\t/, " ", values["applied"])
      printf "%s\t%s\t%s\t%s\n", values["company"], values["role"], values["status"], values["applied"]
    }
  ' "$1"
}

shopt -s nullglob
for record in "$workspace"/jobs/*/company.md; do
  if ! parsed=$(parse_record "$record"); then
    printf 'Invalid application record: %s\n' "$record" >&2
    exit 1
  fi
  printf '%s\n' "$parsed" >> "$records_tmp"
done

{
  printf '# Applications\n\n'
  printf '| Company | Role | Status | Applied |\n'
  printf '|---|---|---|---|\n'
  LC_ALL=C sort -t $'\t' -k1,1f -k1,1 -k2,2f -k2,2 "$records_tmp" |
    while IFS=$'\t' read -r company role status applied; do
      company=${company//|/\\|}
      role=${role//|/\\|}
      applied=${applied//|/\\|}
      printf '| %s | %s | %s | %s |\n' "$company" "$role" "$status" "$applied"
    done
} > "$output_tmp"

mv -f "$output_tmp" "$output"
