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
by the writer section of this skill.

Do not commit changes. Reversibility comes from the user's git diff and clean
working tree.

## Writer

The writer is the only part of this skill that mutates audited files. It
performs exact, atomic string edits from approved findings. Do not summarize,
reinterpret, normalize whitespace, use regex matching, or apply fuzzy fallback
matches.

Process one file at a time:

1. Read the current file content once before applying the first finding for
   that file. Keep this original snapshot for failure reporting only.
2. Sort that file's approved findings by the source order returned by
   `agents/file-orchestrator.md`.
3. Apply findings one by one to the evolving file content.
4. After each successful finding, write the updated content back to disk before
   moving to the next finding.

For each finding:

1. Require a verbatim, non-empty `excerpt`.
2. Locate the exact excerpt in the current in-memory content.
3. If `context_before` or `context_after` is present, use it to disambiguate:
   the accepted occurrence must have the provided `context_before`
   immediately before the excerpt and the provided `context_after`
   immediately after it. Missing context values are ignored.
4. If there are zero accepted occurrences, stop applying later findings in
   this file and report the failed finding. If the excerpt existed in the
   original snapshot but is missing from the current content, report:
   "excerpt changed by an earlier applied finding; re-run to pick up shifted
   findings." Otherwise report: "excerpt not found verbatim."
5. If there is more than one accepted occurrence, stop applying later findings
   in this file and report: "excerpt is ambiguous; add context_before /
   context_after and re-run."
6. For `action: "delete"`, replace the accepted excerpt with an empty string.
   `new_text` must be `null`.
7. For `action: "replace"` or `action: "restructure"`, replace the accepted
   excerpt with `new_text`. `new_text` must be a string.
8. Any other action is a writer failure for that finding.

Failure behavior is hard-error and per-file:

- Do not write any change for the failed finding.
- Do not roll back earlier successful findings in that file.
- Do not continue with later findings in that same file after a writer failure.
- Continue processing other files and include the failed file and finding in
  the final report.
- Never silently skip a failed approved finding.

The writer does not commit, stage, stash, or create backups. The reversibility
contract is: the user starts from a clean tree, reviews `git diff`, and uses
git to undo changes if needed.

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
