# diff2html-cli Notes

Use this reference only when the wrapper script is not enough.

`diff2html-cli` reads git-style unified diffs and renders HTML or JSON. The
wrapper pins `diff2html-cli@5.2.15` by default and can be overridden with
`DIFF2HTML_CLI_VERSION`.

Useful raw options from `diff2html --help`:

| Option | Purpose |
|---|---|
| `--input file|command|stdin` | Select diff input source. |
| `--file <path>` | Write output to a file. |
| `--summary closed|open|hidden` | Control the file summary. |
| `--colorScheme auto|dark|light` | Control report color scheme. |

Raw CLI examples:

```bash
npx --yes diff2html-cli@5.2.15 --input file --file /tmp/diff.html -- /tmp/input.diff
npx --yes diff2html-cli@5.2.15 --style side --format html --file /tmp/diff.html -- -M HEAD~1
```

The `--` separator belongs to `diff2html-cli`: arguments after it are either a
diff file path when `--input file` is used or git diff arguments when the input
source is `command`.
