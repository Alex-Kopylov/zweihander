#!/usr/bin/env bash
# typst-to-pdf.sh — compile a Typst source file to PDF via the Typst CLI.
#
# Usage: typst-to-pdf.sh <typ-abs-path> <pdf-abs-path>
#
# Contract:
# - Inputs MUST be absolute paths (typst resolves relative paths against CWD)
# - Exits non-zero on any failure; callers must check $?
# - Prints stderr from typst on failure for debugging
# - Does NOT scrub metadata — that's a separate skill

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $(basename "$0") <typ-abs-path> <pdf-abs-path>" >&2
  exit 2
fi

typ="$1"
pdf="$2"

# Refuse relative paths — typst interprets them relative to CWD, which is unpredictable across tool calls.
case "$typ" in /*) ;; *) echo "error: typst path must be absolute: $typ" >&2; exit 2 ;; esac
case "$pdf" in /*) ;; *) echo "error: pdf path must be absolute: $pdf"   >&2; exit 2 ;; esac

[[ -f "$typ" ]] || { echo "error: typst file not found: $typ" >&2; exit 2; }
[[ -r "$typ" ]] || { echo "error: typst file not readable: $typ" >&2; exit 2; }

# We do NOT fall back to another engine — cross-application rendering consistency matters.
if ! command -v typst >/dev/null 2>&1; then
  cat >&2 <<'EOF'
error: typst not found on PATH.

Install it and retry:
  brew install typst                     # recommended
  cargo install --locked typst-cli       # alternative

We deliberately do NOT fall back to a browser, weasyprint, or pandoc:
different tools render differently, and inconsistent PDFs across
applications signal flakiness to recruiters.
EOF
  exit 3
fi

# Typst can only read files under the project root. It defaults to the source
# file's own directory, which is right for a self-contained CV. Set
# JOB_HUNT_TYPST_ROOT when the CV imports a shared template from higher up
# (e.g. a workspace-level template.typ shared by every company folder).
root="${JOB_HUNT_TYPST_ROOT:-$(dirname "$typ")}"

# Compile. `set -e` would abort on a failed pipeline before we could read
# PIPESTATUS, so suspend it just long enough to capture typst's own exit code.
set +e
typst compile --root "$root" "$typ" "$pdf" 2>&1 | sed 's/^/[typst] /' >&2
typst_exit=${PIPESTATUS[0]}
set -e
if (( typst_exit != 0 )); then
  echo "error: typst exited with status $typst_exit — compilation failed" >&2
  exit 6
fi

# Verify output.
if [[ ! -r "$pdf" ]]; then
  echo "error: PDF not readable at $pdf" >&2
  exit 4
fi

size=$(stat -f%z "$pdf" 2>/dev/null || stat -c%s "$pdf")
if (( size < 1024 )); then
  echo "error: compiled PDF is suspiciously small ($size bytes)" >&2
  exit 5
fi

echo "ok: $pdf (${size} bytes)"
