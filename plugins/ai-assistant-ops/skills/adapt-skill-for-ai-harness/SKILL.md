---
name: adapt-skill-for-ai-harness
description: "Use when adapting skills for AI Assistant Harness Adaptation, using an assistant harness action matrix, or making explicitly named target skills render correctly for every supported harness."
---

# Adapt Skill For AI Harness

Convert an explicitly named target skill's harness-specific wording into a
harness-parametric Jinja template. Authored sources under `plugins/` are
rendered at build time into one complete tree per harness; each rendered tree
speaks only its own harness's vocabulary.

Adapt only an explicitly named target skill or target skill path. If the user
did not name one target skill, ask for the target before editing. Only the
named target changes.

## Source Of Truth

`references/harness-action-matrix.json` is the only source of callable names.
Lookups are action-first, then assistant:

```python
matrix = load_json("references/harness-action-matrix.json")
codex_delegate = matrix["actions"]["CreateAgent"]["Codex"]["name"]  # spawn_agent
```

Use `scripts/lookup_harness_action.py --action CreateAgent --assistant Codex`
for scriptable lookup; it also returns the wrapped invocation form.

## Template Contract

For every output path `X`, the build applies exactly one rule: a plain `X` is
copied byte-for-byte, an `X.j2` template is rendered with the harness context
and emitted as `X`, and `X` plus `X.j2` together fail the build — keep exactly
one source per output path.

Templates render with this context:

- `harness` — the assistant key being rendered (`ClaudeCode` or `Codex`).
- `actions` — action key → that harness's callable name, from the matrix.
- `call` — a filter that wraps any name in the harness's invocation wrapper.

Reference callables only through these mechanisms:

- Mapped mechanism, wrapped for invocation: `{{ actions.AskUser | call }}`.
- Mapped mechanism, name only (narrative mention): `{{ actions.AskUser }}`.
- Skill invocation by literal name: `{{ "plugin-name:skill-name" | call }}`
  for plugin-installed skills, `{{ "skill-name" | call }}` for bare names.

Never write another harness mechanism's callable name as a literal in a
template; the repository policy test names the offending file. Never select a
callable name inside a harness conditional — names always come from the
action map, so they never need branching.

Use harness conditionals only for narrative that genuinely differs between
harnesses:

```jinja
{% if harness == "Codex" %}
Codex-only guidance in Codex vocabulary.
{% else %}
Claude Code-only guidance in Claude Code vocabulary.
{% endif %}
```

When rendered output needs literal `{{` or `{%` sequences, wrap that content
in `{% raw %}` blocks. Plain (non-template) files never need this; they are
copied byte-for-byte.

## Workflow

1. Resolve the explicitly named target skill directory or path.
2. Inspect only files that enter LLM invocation context: the skill file,
   `references/`, `agents/`, examples, and scripts the skill loads or
   describes. Ignore README files, tests, and development-only support files.
3. Find harness-specific wording: mechanism callable names, invocation
   syntax, and harness-specific facts such as context-file locations.
4. Leave baseline capabilities alone. Every harness reads, searches, creates,
   edits, and writes files and runs shell commands natively; delete baseline
   tool coaching instead of templating it.
5. Replace each mapped-mechanism reference with an action-map lookup or the
   `call` filter. If a needed action is missing from the matrix, add it there
   first (see Matrix Contract) rather than hardcoding a name.
6. Put genuinely divergent narrative into harness conditionals; keep
   everything harness-shared outside them.
7. If the file now contains Jinja, rename it with the `.j2` suffix and make
   sure no plain sibling remains. If nothing harness-specific was found, the
   file stays plain — a skill without harness-specific wording needs no
   template at all.
8. Run the full build, read the rendered target in each harness tree, and
   run the repository test suite.
9. Report the exact files changed and the verification commands run.

## Matrix Contract

The renderer depends on every element below; keep them stable:

- Action keys are stable TitleCase (`AskUser`, `CreateAgent`, `CreateTask`)
  and never equal any callable name.
- Assistant keys are stable and product-oriented: `ClaudeCode` and `Codex`.
- Every action carries a boolean `callable` flag.
- Callable actions map to exactly one callable name per assistant — one
  `name` string under each assistant key. Several actions may resolve to the
  same name (`CreateTask` and `UpdateTask` both map to `update_plan` on
  Codex, which rewrites the whole plan).
- When a harness has no counterpart for an action, that assistant entry
  repeats the other harness's name and carries a `note` saying so. `GetTask`,
  `ListTasks`, and `StopTask` do this for Codex: reading one item, listing
  the plan, and stopping a tracked task have no Codex tool. Naming a real
  concept beats naming a tool that cannot do the job.
- Non-callable actions carry reference material (file paths, command lists)
  instead of names.
- Each assistant defines exactly one `invocation_wrapper` with a single
  `{name}` slot, stored once in the top-level `assistants` section — never
  per action.
- Keep `lookup_order: ["action", "assistant"]`.
- When names are re-verified against official documentation, refresh
  `checked` and the assistant `source_urls`, and land matrix changes in
  focused commits together with the tests guarding them.

## Verification

For each adapted target, check that:

- Exactly one source exists per output path (no plain/template collision).
- Rendered output for each harness contains only that harness's callable
  names, with the wrapper applied uniformly.
- No template hardcodes a matrix-mapped callable name and no conditional
  selects a callable name.
- Literal `{{` or `{%` output is produced only through `{% raw %}` blocks.
- Only the explicitly requested target skill changed.

Run the repository's build, tests, JSON validation, and Markdown whitespace
checks before finishing.
