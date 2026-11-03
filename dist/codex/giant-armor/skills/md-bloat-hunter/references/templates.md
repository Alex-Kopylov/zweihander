# Templates

A `.md.j2` file is a Jinja template that renders `X.md`. It is a target
whenever `X.md` would be. In scope, a reference to `X.md` that exists only as
`X.md.j2` leads to the template, and the closure scope for one file is the
nearest ancestor directory holding a `SKILL.md` or `SKILL.md.j2`.

Jinja syntax (`{{ ... }}`, `{% ... %}`, `{# ... #}`) is opaque. No `excerpt`
or `new_text` may contain, cut into, or add it; context fields may quote it.
Text in different branches of one conditional never renders together, so it
is not redundant. `scripts/apply_findings.py` refuses an edit that overlaps or
changes Jinja syntax.

A size count on a template includes the Jinja syntax and every branch, so it
is an upper bound on any file it renders.

Evals and tests read the rendered file, not the template. After editing a
template, rebuild its render before verifying; how to rebuild comes from the
repository's own instructions, never from this skill.
