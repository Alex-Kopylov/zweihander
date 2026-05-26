---
name: md-bloat-hunter
description: Use this skill when the user says "/md-bloat-hunter", asks to audit a markdown file or directory for verbosity, asks to find bloat in a file, or wants markdown compressed while preserving meaning. This skill audits markdown files for redundancy, verbosity, filler, and over-expanded vocabulary, then applies approved atomic rewrites.
allowed-tools: AskUserQuestion, Read, Write, Edit, MultiEdit, Glob, Bash, Agent
---

# md-bloat-hunter

Audit markdown files for token bloat and apply concrete, atomic rewrites that
reduce tokens while preserving meaning.

Use the three-level dispatch from `SPEC.md`:

1. This skill is the top orchestrator.
2. One `agents/file-orchestrator.md` worker audits each input file.
3. Each file orchestrator dispatches the four detector agents for its file.

This skill coordinates input scope, dependency checks, file-level fan-out,
finding aggregation, risk gating, writer handoff, and final reporting. It does
not hunt bloat directly.

## Invocation

Slash command:

```text
/md-bloat-hunter [path]
```

Natural-language triggers include:

- "audit `<path>` for verbosity"
- "find bloat in `<file>`"
- "compress this markdown"
- "trim token waste in these docs"

If the user did not provide a path, ask for one with `AskUserQuestion`.

## References

Before dispatching, read:

- `SPEC.md`
- `agents/file-orchestrator.md`
- `references/schema.json`

Read detector agent files only when you need to debug a file-orchestrator
failure. The file orchestrator owns detector dispatch.

## Preflight

Resolve the input path before scanning:

- Expand `~` and relative paths against the current working directory.
- Accept one markdown file or one directory.
- For a file, require a `.md` extension.
- For a directory, enumerate only direct child `*.md` files. Do not recurse
  silently.
- If a directory contains many markdown files, confirm scope with
  `AskUserQuestion` before dispatching. Show the file list and ask whether to
  audit all listed files or provide a narrower path.
- If no markdown files are found, stop and report that nothing was audited.

Verify the runtime dependency before any agent dispatch:

```sh
command -v jsonschema
```

If `jsonschema` is missing, fail fast with this install hint and do not start
any file orchestrators:

```sh
uv tool install jsonschema
```

Create one `run_id` for the whole audit and pass it to every file
orchestrator.

## File Dispatch

Dispatch one file orchestrator per input file with the Agent tool, all in
parallel. Treat Agent as Claude Code's Task tool for this workflow.

For each worker, provide:

- The absolute markdown file path.
- The shared `run_id`.
- The instruction to follow `agents/file-orchestrator.md` exactly.
- The instruction to return only the reduced JSON object described by the
  file orchestrator.

Do not queue files or run file orchestrators one after another. Wait for every
file orchestrator to finish before aggregating results.

If a file orchestrator returns malformed JSON, record that file as failed and
continue aggregating the other files.

## Aggregation

Each valid file-orchestrator result has this shape:

```json
{
  "file_path": "/absolute/path/to/file.md",
  "detector_status": [],
  "findings": []
}
```

Collect every finding into one queue while preserving:

- `file_path`
- the finding's order within that file's `findings` array
- `resolution`
- `recommendation`
- `semantic_risk`
- every edit field needed by the writer: `excerpt`, `context_before`,
  `context_after`, `action`, and `new_text`

Rank the queue for review by severity first (`critical`, `major`, `minor`),
then by semantic risk (`high`, `medium`, `low`, `none`), then by file path and
source order. Do not invent token deltas or IDs.

## Risk Gate

Handle reducer recommendations before risk gating:

- `skip`: skip the finding and record it as skipped.
- `ask-user`: ask the user even when semantic risk is not high.
- `apply`: send the finding through the semantic-risk gate.
- `apply-recommended`: send the recommended alternative through the
  semantic-risk gate and keep alternatives available for the prompt.

Semantic-risk gate:

- `none`, `low`, and `medium`: approve automatically.
- `high`: ask the user with `AskUserQuestion` before applying.

Ask one question per high-risk finding. Include:

- file path
- excerpt
- proposed action
- proposed replacement or delete
- rationale
- semantic risk and confidence
- alternatives when present

Label the AI-recommended option clearly. Offer at least:

- Apply recommended
- Skip

When alternatives exist, include an option to apply a specific alternative if
one is clearly safe to expose. If the user skips a finding, record it as
skipped and continue.

## Writer Handoff

After gating, group approved findings by `file_path`. Within each file, apply
findings in the source order returned by the file orchestrator, not the global
ranked-review order.

Hand each approved finding to the writer with these fields:

- `file_path`
- `excerpt`
- `context_before`
- `context_after`
- `action`
- `new_text`
- `resolution`
- `source_specialists`
- `rationale`

The writer implementation is the mutation step defined in `SPEC.md` and owned
by the writer section of this skill. If that section is not present yet, stop
after producing the approved queue and report that mutation is deferred until
the writer is implemented. Do not improvise a second writer.

Do not commit changes. Reversibility comes from the user's git diff and clean
working tree.

## Reporting

After writer execution, report:

- number of findings applied
- number skipped
- number failed
- file paths touched
- file paths with file-orchestrator failures
- any writer failure messages

If no findings are approved, report that no files were changed.

Keep the report concise and factual. Do not include the full detector JSON
unless the user asks for it.

## Smoke Behavior

A valid smoke run on a fixture directory with two markdown files should show:

- both files dispatched through separate file orchestrators in parallel
- findings from each file appearing in the aggregate queue
- `none`, `low`, and `medium` risk findings approved without prompting
- a forced `high` risk finding routed through `AskUserQuestion`
- approved findings passed to the writer in source order per file
- final counts for applied, skipped, failed, and touched files
