---
name: mermaid-lint
description: Validate Mermaid code blocks by rendering them with the mmdc CLI. Fails loudly if mmdc is not installed.
compatibility: Requires the mmdc command from @mermaid-js/mermaid-cli; Markdown input support is expected from modern Mermaid CLI versions.
---

# Mermaid Linter

> Note: check current Mermaid version first and ask to upgrade if outdated.

Validate Mermaid diagrams by running `mmdc` from `@mermaid-js/mermaid-cli`. The render output is only a validation mechanism; this skill only reports lint status and errors.

## Workflow

1. Check for Mermaid CLI:

   ```bash
   command -v mmdc
   ```

2. If `mmdc` is not available, fail loudly and ask the user to install it:

   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

   Do not silently skip linting in this skill.

3. If the input is a Markdown file, pass it directly to `mmdc`; Mermaid CLI treats `.md` input as Markdown and extracts fenced Mermaid charts itself.
4. If the input is raw Mermaid code, write it to a temporary `.mmd` file.
5. Render the input with `mmdc` into temporary output paths. For Markdown input, write a temporary rendered Markdown file and a temporary artefacts directory. Discard those files after collecting the result.
6. Report results using the schema in `references/linter_output_schema.json`:
   - `status: "passed"` with `errors: null` when `mmdc` exits successfully.
   - `status: "failed"` with `errors` set to the non-empty list of `mmdc` parser/runtime messages when linting fails.
7. Do not report generated SVG or Markdown artefacts as deliverables; return the errors so the agent can fix the Mermaid source and rerun linting.

## Example Command

```bash
mmdc -i diagram.mmd -o diagram.svg
mmdc -i document.md -o rendered.md --artefacts mermaid-lint-artifacts
```
