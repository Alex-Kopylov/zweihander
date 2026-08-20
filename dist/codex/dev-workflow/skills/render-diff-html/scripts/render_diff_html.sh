#!/usr/bin/env bash
set -uo pipefail

DIFF2HTML_CLI_VERSION="${DIFF2HTML_CLI_VERSION:-5.2.15}"
SOURCE="working"
STYLE="side"
FORMAT="html"
OUTPUT=""
TITLE=""
RANGE=""
DIFF_FILE=""
FILE_A=""
FILE_B=""
declare -a IGNORE_ARGS=()
declare -a GIT_ARGS=()

usage() {
  cat <<'USAGE'
Usage:
  render_diff_html.sh [options] [-- <git diff pathspecs>]

Sources:
  --scope working|staged|unstaged|last  Diff source. Default: working
  --working                            Shortcut for --scope working
  --staged, --cached                   Shortcut for --scope staged
  --unstaged                           Shortcut for --scope unstaged
  --last                               Shortcut for --scope last
  --range <range>                      Run git diff <range>
  --diff-file <file>                   Render an existing unified diff or patch
  --files <old> <new>                  Compare two files or directories

Output:
  -o, --output <file>                  Output file. Default: /tmp/codex-diff2html/*.html
  -s, --style line|side                Diff layout. Default: side
  -f, --format html|json               Output format. Default: html
  --title <text>                       HTML report title
  --ignore <path>                      Ignore a path in the rendered report. Repeatable
  -h, --help                           Show this help

Environment:
  DIFF2HTML_CLI_VERSION                diff2html-cli npm version. Default: 5.2.15

Examples:
  render_diff_html.sh --scope staged -- README.md
  render_diff_html.sh --range origin/main...HEAD --style side
  render_diff_html.sh --files old.txt new.txt
  render_diff_html.sh --diff-file changes.patch -o /tmp/changes.html
USAGE
}

die() {
  printf 'render_diff_html: %s\n' "$*" >&2
  exit 2
}

need_value() {
  local flag="$1"
  local value="${2:-}"
  [[ -n "$value" ]] || die "$flag requires a value"
}

while (($#)); do
  case "$1" in
    --scope)
      need_value "$1" "${2:-}"
      SOURCE="$2"
      shift 2
      ;;
    --working)
      SOURCE="working"
      shift
      ;;
    --staged|--cached)
      SOURCE="staged"
      shift
      ;;
    --unstaged)
      SOURCE="unstaged"
      shift
      ;;
    --last)
      SOURCE="last"
      shift
      ;;
    --range)
      need_value "$1" "${2:-}"
      SOURCE="range"
      RANGE="$2"
      shift 2
      ;;
    --diff-file)
      need_value "$1" "${2:-}"
      SOURCE="diff-file"
      DIFF_FILE="$2"
      shift 2
      ;;
    --files)
      need_value "$1" "${2:-}"
      need_value "$1" "${3:-}"
      SOURCE="files"
      FILE_A="$2"
      FILE_B="$3"
      shift 3
      ;;
    -o|--output)
      need_value "$1" "${2:-}"
      OUTPUT="$2"
      shift 2
      ;;
    -s|--style)
      need_value "$1" "${2:-}"
      STYLE="$2"
      shift 2
      ;;
    -f|--format)
      need_value "$1" "${2:-}"
      FORMAT="$2"
      shift 2
      ;;
    --title)
      need_value "$1" "${2:-}"
      TITLE="$2"
      shift 2
      ;;
    --ignore|--ig)
      need_value "$1" "${2:-}"
      IGNORE_ARGS+=(--ignore "$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      GIT_ARGS+=("$@")
      break
      ;;
    *)
      GIT_ARGS+=("$1")
      shift
      ;;
  esac
done

case "$SOURCE" in
  working|staged|unstaged|last|range|diff-file|files) ;;
  *) die "--scope must be one of: working, staged, unstaged, last" ;;
esac

case "$STYLE" in
  line|side) ;;
  *) die "--style must be 'line' or 'side'" ;;
esac

case "$FORMAT" in
  html|json) ;;
  *) die "--format must be 'html' or 'json'" ;;
esac

if [[ "$SOURCE" == "diff-file" || "$SOURCE" == "files" ]]; then
  ((${#GIT_ARGS[@]} == 0)) || die "pathspecs after -- only apply to git diff sources"
fi

tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/render-diff-html.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT
raw_diff="$tmp_dir/input.diff"

require_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git worktree"
}

write_git_diff() {
  require_git_repo
  if ! "$@" >"$raw_diff"; then
    die "failed to generate raw git diff"
  fi
}

case "$SOURCE" in
  working)
    write_git_diff git diff HEAD -- "${GIT_ARGS[@]}"
    ;;
  staged)
    write_git_diff git diff --cached -- "${GIT_ARGS[@]}"
    ;;
  unstaged)
    write_git_diff git diff -- "${GIT_ARGS[@]}"
    ;;
  last)
    write_git_diff git show --format= --find-renames HEAD -- "${GIT_ARGS[@]}"
    ;;
  range)
    [[ -n "$RANGE" ]] || die "--range requires a git revision range"
    write_git_diff git diff "$RANGE" -- "${GIT_ARGS[@]}"
    ;;
  diff-file)
    [[ -f "$DIFF_FILE" ]] || die "diff file not found: $DIFF_FILE"
    cp "$DIFF_FILE" "$raw_diff" || die "failed to read diff file: $DIFF_FILE"
    ;;
  files)
    [[ -e "$FILE_A" ]] || die "left path not found: $FILE_A"
    [[ -e "$FILE_B" ]] || die "right path not found: $FILE_B"
    status=0
    git diff --no-index -- "$FILE_A" "$FILE_B" >"$raw_diff" || status=$?
    if [[ "$status" -gt 1 ]]; then
      die "failed to compare files with git diff --no-index"
    fi
    ;;
esac

if [[ ! -s "$raw_diff" ]]; then
  printf 'No differences found for source: %s\n' "$SOURCE" >&2
  exit 3
fi

if [[ -z "$OUTPUT" ]]; then
  tmp_base="${TMPDIR:-/tmp}"
  tmp_base="${tmp_base%/}"
  safe_pwd_name="$(printf '%s' "$(basename "$PWD")" | tr -c '[:alnum:]_.-' '-')"
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  extension="$FORMAT"
  OUTPUT="${tmp_base}/codex-diff2html/${safe_pwd_name}-${SOURCE}-${timestamp}.${extension}"
elif [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PWD/$OUTPUT"
fi

mkdir -p "$(dirname "$OUTPUT")" || die "failed to create output directory"

declare -a cmd=(
  npx --yes "diff2html-cli@${DIFF2HTML_CLI_VERSION}"
  --style "$STYLE"
  --format "$FORMAT"
  --input file
  --file "$OUTPUT"
)

if [[ -n "$TITLE" ]]; then
  cmd+=(--title "$TITLE")
fi

cmd+=("${IGNORE_ARGS[@]}")
cmd+=(-- "$raw_diff")

if ! "${cmd[@]}"; then
  die "diff2html-cli failed"
fi

[[ -s "$OUTPUT" ]] || die "diff2html-cli did not create a non-empty output file"

printf '%s\n' "$OUTPUT"
