---
name: render-diff-html
description: Render git diffs and file-to-file comparisons as HTML or JSON reports with diff2html-cli. Use when the user asks to get, render, open, export, or show a visual diff; compare staged, unstaged, working tree, commit range, or last commit changes; convert a patch or .diff file; or show differences between two files or directories.
---

# Render Diff HTML

Generate a visual diff report with `scripts/render_diff_html.sh`, which wraps
`diff2html-cli` and keeps raw diff generation consistent.

## Quick Start

Use the wrapper first. Pass git pathspecs after `--` when narrowing a git diff:

```bash
SCRIPT=plugins/dev-workflow/skills/render-diff-html/scripts/render_diff_html.sh
bash "$SCRIPT" --scope working
bash "$SCRIPT" --scope staged -- README.md
bash "$SCRIPT" --range origin/main...HEAD --style side
bash "$SCRIPT" --files old.txt new.txt
bash "$SCRIPT" --diff-file change.patch
```

Report the absolute output path to the user. If the user asks to preview it,
open that HTML path with the available browser or OS tool after generation.

## Source Selection

Prefer these simple mappings:

| User request | Wrapper option |
|---|---|
| "show my diff", "render the git diff" | `--scope working` |
| "staged changes" | `--scope staged` |
| "unstaged changes" | `--scope unstaged` |
| "last commit" | `--scope last` |
| "diff against main" | `--range origin/main...HEAD` |
| "compare A and B files" | `--files A B` |
| "convert this patch" | `--diff-file path/to/file.patch` |

Use `--output <path>` when the user gives a destination. Otherwise leave the
default `/tmp/codex-diff2html/...` output in place.

## Options

- Use `--style side` for side-by-side diffs and `--style line` for inline diffs.
- Use `--format html` by default; use `--format json` only when the user asks for machine-readable output.
- Use repeated `--ignore <path>` for noisy generated files such as lockfiles.
- Use `--title <text>` when a named report would help.
- Treat exit code `3` from the wrapper as "no differences found."

Read `references/diff2html-cli.md` only when you need raw `diff2html-cli`
details beyond the wrapper.

## Verification

After generation, verify that the output file exists and is non-empty. For HTML
reports, a basic check is enough:

```bash
test -s /absolute/path/to/report.html
```
