---
name: mermaid-lint
description: Validate Mermaid code blocks by rendering them with the mmdc CLI. Fails loudly if mmdc is not installed.
compatibility: Requires the mmdc command from @mermaid-js/mermaid-cli; Markdown input support is expected from modern Mermaid CLI versions.
---

# Mermaid Linter

> Note: check current Mermaid version first and ask to upgrade if outdated.

Validate Mermaid diagrams by running `mmdc` from `@mermaid-js/mermaid-cli`. The render output is only a validation mechanism; this skill only reports lint status and errors.

## Workflow

1. Check for Mermaid CLI and version before linting:

   ```bash
   command -v mmdc
   CURR_VERSION="$(mmdc --version 2>/dev/null | tr -d '\r')"
   LATEST_VERSION="$(npm view @mermaid-js/mermaid-cli version)"
   ```

2. If `mmdc` is missing, stop and ask the user whether to install it:

   ```bash
   AskUserQuestion: "mmdc is missing. Install with npm install -g @mermaid-js/mermaid-cli@latest before linting? (yes/no)"
   If yes: npm install -g @mermaid-js/mermaid-cli@latest
   ```

3. If `CURR_VERSION` is not empty and differs from `LATEST_VERSION`, pause the process and run `AskUserQuestion` for permission to update or continue without it:

   ```bash
   AskUserQuestion: "mmdc is outdated ($CURR_VERSION -> $LATEST_VERSION). Update now, or proceed without it? (update/continue)"
   ```

   If the user answers `update`, run:

   ```bash
   npm install -g @mermaid-js/mermaid-cli@latest
   mmdc --version
   ```

   If the user answers `continue`, proceed without updating.

   Do not auto-update Mermaid CLI.

5. If the input is a Markdown file, pass it directly to `mmdc`; Mermaid CLI treats `.md` input as Markdown and extracts fenced Mermaid charts itself.
6. If the input is raw Mermaid code, write it to a temporary `.mmd` file.
7. Render the input with `mmdc` into temporary output paths. For Markdown input, write a temporary rendered Markdown file and a temporary artefacts directory. Discard those files after collecting the result.
6. Report results using the schema in `references/linter_output_schema.json`:
   - `status: "passed"` with `errors: null` when `mmdc` exits successfully.
   - `status: "failed"` with `errors` set to the non-empty list of `mmdc` parser/runtime messages when linting fails.
8. Do not report generated SVG or Markdown artefacts as deliverables; return the errors so the agent can fix the Mermaid source and rerun linting.

## Example Command

```bash
mmdc -i diagram.mmd -o diagram.svg
mmdc -i document.md -o rendered.md --artefacts mermaid-lint-artifacts
```
