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

# We pass no --root on purpose. Typst already defaults it to the source file's
# own directory, which is the narrowest sandbox and the right one for a
# self-contained CV. Overriding it here would also shadow the user's TYPST_ROOT,
# which is Typst's own supported way to widen the root for a shared template.

# Compile. `set -e` would abort on a failed pipeline before we could read
# PIPESTATUS, so suspend it just long enough to capture typst's own exit code.
# Warnings are captured too: typst exits 0 on them, but a font fallback or a
# non-converging layout means the PDF does not match the master.
# Forces UTC; Typst otherwise stamps the machine's local offset into
# /CreationDate and the XMP packet, leaking the applicant's timezone.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(date -u +%s)}"

set +e
typst_log="$(typst compile "$typ" "$pdf" 2>&1)"
typst_exit=$?
set -e
[[ -n "$typst_log" ]] && printf '%s\n' "$typst_log" | sed 's/^/[typst] /' >&2
if (( typst_exit != 0 )); then
  echo "error: typst exited with status $typst_exit — compilation failed" >&2
  exit 6
fi

# Typst exits 0 on warnings, but every warning it emits for a CV means the
# output differs from what the master looked like. Treat them as failures.
if printf '%s\n' "$typst_log" | grep -q '^warning:'; then
  echo "error: typst emitted warnings — the PDF does not match the master" >&2
  exit 7
fi

# Verify output.
if [[ ! -r "$pdf" ]]; then
  echo "error: PDF not readable at $pdf" >&2
  exit 4
fi

# No byte-size floor: a Typst document whose content vanished still compiles to
# a valid ~2KB PDF, so size cannot distinguish it from a real render. The
# authoritative "did it render" gate is the extracted-text check in export-pdf.
head -c4 "$pdf" | grep -q '%PDF' || { echo "error: not a PDF: $pdf" >&2; exit 5; }

size=$(stat -f%z "$pdf" 2>/dev/null || stat -c%s "$pdf")
echo "ok: $pdf (${size} bytes)"
