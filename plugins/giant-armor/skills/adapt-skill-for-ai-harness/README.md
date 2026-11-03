# adapt-skill-for-ai-harness

This skill maintains the AI Assistant Harness Adaptation policy for explicitly
named target skills: harness-specific wording is authored as Jinja templates
(`.j2`) that resolve callable names from
`references/harness-action-matrix.json` at build time, so each harness's
rendered tree speaks only its own vocabulary.

The matrix maps TitleCase action keys to one callable name per assistant and
stores one invocation wrapper per assistant. Lookups are action-first, then
assistant: `matrix["actions"]["CreateAgent"]["Codex"]["name"]`.
`scripts/lookup_harness_action.py` provides scriptable lookup, including the
wrapped invocation form.

Harness tool surfaces are moving targets. When re-verifying names against the
official product documentation, refresh the matrix `checked` date and
assistant `source_urls`, and land matrix changes in focused PRs together with
the tests guarding the affected behavior.
