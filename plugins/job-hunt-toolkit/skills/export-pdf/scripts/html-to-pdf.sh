#!/usr/bin/env bash
# html-to-pdf.sh — render an HTML file to PDF via headless Chromium.
#
# Usage: html-to-pdf.sh <html-abs-path> <pdf-abs-path>
#
# Contract:
# - Inputs MUST be absolute paths (Chromium writes to CWD otherwise)
# - Exits non-zero on any failure; callers must check $?
# - Prints stderr from Chromium on failure for debugging
# - Does NOT scrub metadata — that's a separate skill

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $(basename "$0") <html-abs-path> <pdf-abs-path>" >&2
  exit 2
fi

html="$1"
pdf="$2"

# Refuse relative paths — Chromium interprets them relative to CWD, which is unpredictable across tool calls.
case "$html" in /*) ;; *) echo "error: html path must be absolute: $html" >&2; exit 2 ;; esac
case "$pdf"  in /*) ;; *) echo "error: pdf path must be absolute: $pdf"  >&2; exit 2 ;; esac

[[ -f "$html" ]] || { echo "error: html file not found: $html" >&2; exit 2; }
[[ -r "$html" ]] || { echo "error: html file not readable: $html" >&2; exit 2; }

# Locate a Chromium-based browser in a deterministic order.
# We do NOT fall back to other PDF tools — cross-application rendering consistency matters.
browser=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  "chromium" \
  "chromium-browser" \
  "google-chrome"
do
  if [[ -x "$candidate" ]]; then
    browser="$candidate"
    break
  elif command -v "$candidate" >/dev/null 2>&1; then
    browser="$(command -v "$candidate")"
    break
  fi
done

if [[ -z "$browser" ]]; then
  cat >&2 <<'EOF'
error: no Chromium-based browser found.

Install one and retry:
  brew install --cask google-chrome      # recommended
  brew install --cask chromium           # alternative

We deliberately do NOT fall back to weasyprint / wkhtmltopdf:
different tools render differently, and inconsistent PDFs across
applications signal flakiness to recruiters.
EOF
  exit 3
fi

# Use a fresh, isolated user-data-dir so we don't touch the user's profile
# or get blocked by a running browser instance.
tmp_profile="$(mktemp -d -t job-hunt-chromium.XXXXXX)"
trap 'rm -rf "$tmp_profile"' EXIT

# Render.
# --no-pdf-header-footer hides Chrome's default "Page 1 of N / URL" bar.
# --virtual-time-budget gives JS/fonts time to settle before print.
"$browser" \
  --headless=new \
  --disable-gpu \
  --user-data-dir="$tmp_profile" \
  --no-pdf-header-footer \
  --virtual-time-budget="${JOB_HUNT_RENDER_TIMEOUT:-15000}" \
  --print-to-pdf="$pdf" \
  --print-to-pdf-no-header \
  "file://$html" \
  2>&1 | sed 's/^/[chrome] /' >&2
browser_exit=${PIPESTATUS[0]}
if (( browser_exit != 0 )); then
  echo "error: Chromium exited with status $browser_exit — rendering failed" >&2
  exit 6
fi

# Verify output.
if [[ ! -r "$pdf" ]]; then
  echo "error: PDF not readable at $pdf" >&2
  exit 4
fi

size=$(stat -f%z "$pdf" 2>/dev/null || stat -c%s "$pdf")
if (( size < 1024 )); then
  echo "error: rendered PDF is suspiciously small ($size bytes)" >&2
  exit 5
fi

echo "ok: $pdf (${size} bytes)"
