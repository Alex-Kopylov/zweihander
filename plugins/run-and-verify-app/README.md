# run-and-verify-app

Run and verify applications through their real runtime surface.

Inspired by Claude Code's bundled run and verify app workflow, this Codex plugin
launches an app, confirms a code change against the running app, and records a
reusable per-project launch recipe.

This is an opinionated adaptation, not a 1-to-1 port. It reflects this
marketplace's preferences for runtime evidence and reusable project run skills.

Claude Code users can use Claude Code's built-in run and verify skills.

<details>
<summary>Skills</summary>

| Skill | Purpose |
|---|---|
| `run` | Launch and drive the app to see a change working. |
| `verify` | Build and run the app to confirm a code change does what it should, without falling back to tests or type checks. |
| `run-skill-generator` | Teach `run` and `verify` how to build and launch the project by recording a verified project-specific run skill. |

</details>
