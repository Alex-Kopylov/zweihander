#!/usr/bin/env bash
# Append-only decision log and progress counter for the interview skill.
#
# `start` prints the log path; every later call takes it back as `--log`. The
# log is the interview's only counter: progress is the number of distinct items
# already recorded in the file, so the bar reports what was recorded rather
# than what anyone remembers recording.
#
# The default directory is `$INTERVIEW_DECISION_LOG_DIR`, then the system
# temporary directory. `SKILL.md` declares the same default under
# `metadata.config.decision-log-dir`.

set -euo pipefail

SLUG_LIMIT=40
BAR_WIDTH=20
FILLED=▰
EMPTY=▱

die() { printf 'error: %s\n' "$1" >&2; exit 1; }

need() { [ -n "$2" ] || die "$1 is required"; }

# Fit one field into a table cell: single line, no column break.
cell() {
    printf '%s' "$1" | tr -s '[:space:]' ' ' |
        sed -e 's/^ //' -e 's/ $//' -e 's/|/\\|/g'
}

slug() {
    local out
    out=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' |
        sed 's/[^a-z0-9]\{1,\}/-/g' | cut -c1-"$SLUG_LIMIT" |
        sed -e 's/^-*//' -e 's/-*$//')
    [ -n "$out" ] || die "name '$1' has no letters or digits to build a file name"
    printf '%s' "$out"
}

# Render the queue as one cell per item, scaled past BAR_WIDTH items. Both ends
# stay honest under scaling: the first decision fills a cell, and a queue with
# an item left keeps a cell empty however close it rounds.
bar() {
    local taken=$1 total=$2 cells=$2 filled index out=''
    if (( cells > BAR_WIDTH )); then cells=$BAR_WIDTH; fi
    if (( taken >= total )); then
        filled=$cells
    else
        filled=$(( (taken * cells + total - 1) / total ))
        if (( filled > cells - 1 )); then filled=$(( cells - 1 )); fi
    fi
    for (( index = 0; index < cells; index++ )); do
        if (( index < filled )); then out+=$FILLED; else out+=$EMPTY; fi
    done
    printf '%s  %s/%s\n' "$out" "$taken" "$total"
}

# Count distinct recorded items. Rows accumulate on every `record` call,
# including amendments that re-record an already-decided item, so progress
# counts item identities rather than rows. The first two table lines are the
# header and its rule.
recorded() {
    awk -F' \\| ' '
        /^\|/ { if (++row > 2) { item = $1; sub(/^\| /, "", item); seen[item] = 1 } }
        END { count = 0; for (key in seen) count++; print count }' "$1"
}

declared_total() {
    local total
    total=$(sed -n 's/^total: \([0-9]\{1,\}\)$/\1/p' "$1" | head -1)
    [ -n "$total" ] || die "decision log $1 declares no total"
    printf '%s' "$total"
}

readable() {
    [ -r "$1" ] || die "cannot read decision log $1; \`start\` creates the log and prints the path to pass back as --log"
}

whole() {
    case $2 in '' | *[!0-9]*) die "$1" ;; esac
    [ "$2" -ge "$3" ] || die "$1"
}

# Sourcing exposes the helpers to tests; only a direct run dispatches.
[ "${BASH_SOURCE[0]}" = "$0" ] || return 0

command=${1-}
case $command in
    start | record | extend | show) shift ;;
    *) die "usage: decision_log.sh {start|record|extend|show} ..." ;;
esac

log='' decision='' note='' name='' total='' by=''
items=()
while [ $# -gt 0 ]; do
    case $1 in
        --log) log=$2 ;;
        --decision) decision=$2 ;;
        --note) note=$2 ;;
        --item) items+=("$2") ;;
        --name) name=$2 ;;
        --total) total=$2 ;;
        --by) by=$2 ;;
        *) die "unknown argument $1" ;;
    esac
    shift 2
done

case $command in
start)
    need --name "$name"
    need --total "$total"
    whole "total $total is not a number of items to walk through" "$total" 1

    directory=${INTERVIEW_DECISION_LOG_DIR:-${TMPDIR:-/tmp}/interview-decision-logs}
    mkdir -p "$directory"
    read -r stamp started <<<"$(date +'%Y%m%d-%H%M%S %Y-%m-%dT%H:%M:%S')"
    named=$(slug "$name")
    log=$directory/$stamp-$named.md
    if [ -e "$log" ]; then die "decision log $log already exists"; fi

    {
        printf -- '---\nname: %s\nstarted: %s\ntotal: %s\n---\n\n' \
            "$named" "$started" "$total"
        printf '# Interview decision log: %s\n\n' "$name"
        printf '| Item | Decision | Note |\n|------|----------|------|\n'
    } >"$log"

    printf '%s\n' "$log"
    bar 0 "$total"
    ;;

record)
    need --log "$log"
    need --decision "$decision"
    [ ${#items[@]} -gt 0 ] || die "--item is required"
    readable "$log"
    total=$(declared_total "$log")

    chosen=$(cell "$decision")
    aside=$(cell "$note")
    for item in "${items[@]}"; do
        subject=$(cell "$item")
        printf '| %s | %s | %s |\n' "$subject" "$chosen" "$aside" >>"$log"
        if [ -n "$aside" ]; then
            printf '%s: **%s** (%s)\n' "$subject" "$chosen" "$aside"
        else
            printf '%s: **%s**\n' "$subject" "$chosen"
        fi
    done
    bar "$(recorded "$log")" "$total"
    ;;

extend)
    need --log "$log"
    need --by "$by"
    whole "--by $by adds no items to the queue" "$by" 1
    readable "$log"
    total=$(declared_total "$log")
    raised=$(( total + by ))

    sed "s/^total: $total\$/total: $raised/" "$log" >"$log.tmp"
    mv "$log.tmp" "$log"
    bar "$(recorded "$log")" "$raised"
    ;;

show)
    need --log "$log"
    readable "$log"
    cat "$log"
    printf '\n'
    bar "$(recorded "$log")" "$(declared_total "$log")"
    ;;
esac
