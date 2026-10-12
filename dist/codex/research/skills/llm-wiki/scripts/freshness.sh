#!/usr/bin/env bash
# freshness.sh — print the freshness label for a publication date.
#
# Usage: freshness.sh <YYYY-MM-DD>
#
# Compares the year of the date with today's year: fresh = this year or last
# year, recent = two years ago, historical = older. Run it instead of picking a
# label by hand, so labels never depend on a year written into a schema.
set -euo pipefail

published="${1:?usage: freshness.sh <YYYY-MM-DD>}"
[[ "${published}" =~ ^[0-9]{4}(-[0-9]{2}){0,2}$ ]] || { echo "not a date: ${published}" >&2; exit 2; }

this_year="$(date +%Y)"
age=$(( this_year - ${published:0:4} ))
if (( age <= 1 )); then
  echo fresh
elif (( age == 2 )); then
  echo recent
else
  echo historical
fi
