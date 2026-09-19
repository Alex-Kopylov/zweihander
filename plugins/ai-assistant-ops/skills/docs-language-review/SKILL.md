---
name: docs-language-review
description: Use when the user asks to review or rewrite Markdown documentation for plain language, Simplified Technical English, cognitive accessibility, or clearer public-facing prose.
---

# Documentation Language Review

Review or rewrite only the documentation files that the user selected.

This skill runs only when invoked. Do not install hooks or automatic triggers.

## Workflow

1. Resolve the target files from the request. Ask before expanding an ambiguous scope.
2. Read every target file and [references/documentation-language-guidelines.md](references/documentation-language-guidelines.md).
3. Audit without writing when the user asks for review only. Otherwise, edit the target files directly.
4. Inspect the diff and restore any accidental change to meaning or protected content.
5. Run relevant Markdown and repository checks.
6. Report the files changed, the main improvements, and unresolved ambiguities.

Edit no file outside the selected target set unless the user explicitly expands the task.
