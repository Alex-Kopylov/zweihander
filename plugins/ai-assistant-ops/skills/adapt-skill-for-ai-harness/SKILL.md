---
name: adapt-skill-for-ai-harness
description: "Use when adapting skills for AI Assistant Harness Adaptation, using an assistant harness action matrix or frontmatter matrix, or making explicitly named target skills render correctly for every supported harness."
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

## Frontmatter Portability Boundary

Frontmatter is the one region where a wrong key is a hard incompatibility
rather than noise. `references/harness-frontmatter-matrix.json` is the only
source of frontmatter placement, as the action matrix is the only source of
callable names. Lookups are key-first, then assistant:

```python
matrix = load_json("references/harness-frontmatter-matrix.json")
placement = matrix["keys"]["argument-hint"]["Codex"]["placement"]  # metadata
```

Use `scripts/lookup_harness_frontmatter.py --key argument-hint --assistant Codex`
for scriptable lookup; it also returns how to declare the key.

A key whose form is `verbatim` is portable — every harness reads it — so write
it literally. `name` and `description` are the two. Every other key carries a
placement per harness, and the renderer registers one global named after it:

```jinja
{{ allowed_tools("Bash(git:*) Read") }}
{{ argument_hint("[issue] to work through") }}
{{ arguments("issue") }}
```

Claude Code renders each at the top level; Codex renders each under
`metadata:`, the free-form map both harnesses accept. An empty value emits no
key. Never write a placed key by hand and never wrap the call in a harness
conditional — the global already carries the harness.

Each key's `form` decides how the value is written, and the matrix documents
every form:

- `plain-scalar` — written unquoted, the form the Agent Skills specification
  shows; a list argument joins with spaces, and a value that would not survive
  as a plain YAML scalar fails the build.
- `quoted-scalar` — always double-quoted, because `argument-hint: [file]
  [format]` would otherwise parse as a YAML list; a line break fails the build.
- `placeholder-names` — names that can each spell a `$name` placeholder, so a
  name with a space, a capital, or a leading digit fails the build.

Claude Code substitutes `$name` in the body; Codex documents no substitution. So
spell a placeholder inside a harness conditional and write prose in the Codex
branch. This is the only `$name` that may sit inside a conditional.

A skill may also hand-write `metadata:`. For Codex that would collide with the
block a global emits, so the renderer folds every frontmatter `metadata:`
block into the first one. Duplicates of any other key stay a build failure.

Group `metadata` entries one level deep, under a namespace the matrix
declares — `references`, `agents`, `skills`, `origin`, or `config` — and keep
entry keys as paths that resolve from the declaring file. `config` is the
exception: its entries name the skill's own runtime defaults.

```yaml
metadata:
  references:
    "references/gitlab.md": "Load when the merge request lives on GitLab."
  agents:
    "../../agents/test-runner.md": "Use for focused pytest execution."
  config:
    output-dir: "${TMPDIR:-/tmp}/skill-output"
```

## Workflow

1. Resolve the explicitly named target skill directory or path.
2. Inspect only files that enter LLM invocation context: the skill file,
   `references/`, `agents/`, examples, and scripts the skill loads or
   describes. Ignore README files, tests, and development-only support files.
3. Find harness-specific wording: mechanism callable names, invocation
   syntax, frontmatter keys outside the portable set, and harness-specific
   facts such as context-file locations.
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

Both matrices answer one question each — the action matrix "what is this
mechanism called here", the frontmatter matrix "where does this key go here" —
so a new harness fact belongs in one of them rather than in a template.

The frontmatter matrix keeps these stable:

- Key names are the frontmatter keys themselves, so the global is the key with
  hyphens turned into underscores.
- Every key carries a `form` the matrix documents under `forms`, and every
  non-`verbatim` form is one the renderer can write.
- Every key carries a `placement` per assistant: `top-level` where the harness
  reads the key, `metadata` where it does not.
- A `metadata` placement carries a `note` recording why the harness does not
  read the key.
- `metadata_namespaces` lists the namespaces authors may write, and never
  repeats a key name.
- Keep `lookup_order: ["key", "assistant"]`.

The action matrix keeps these stable:

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
- Frontmatter hand-writes no key the frontmatter matrix places, and every
  `metadata` entry sits under a declared namespace.
- Rendered output for each harness contains only that harness's callable
  names, with the wrapper applied uniformly.
- No template hardcodes a matrix-mapped callable name and no conditional
  selects a callable name.
- Literal `{{` or `{%` output is produced only through `{% raw %}` blocks.
- Only the explicitly requested target skill changed.

Run the repository's build, tests, JSON validation, and Markdown whitespace
checks before finishing.
