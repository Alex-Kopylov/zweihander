---
name: ai-setup-audit
description: Audit the whole AI assistant setup — AGENTS.md, runtime instruction files, skills, and context files — and list rules to cut as default, conflicting, redundant, reactive, or vague, plus a cleaned-up AGENTS.md.
---

# AI Setup Audit

Read the entire setup before responding.

## Scope

Check AGENTS.md, runtime-specific instruction files, every skill in the skills folder, every context-folder file, and any other instruction files found. Review every rule, instruction, and preference.

## Analysis Criteria

For each rule, instruction, or preference, evaluate:

1. **Already default?** — Is this something the AI Assistant already does by default without being told?
2. **Conflicts?** — Does this conflict with another rule elsewhere in the setup?
3. **Redundant?** — Does this repeat something that's already covered by a different rule or file?
4. **Reactive patch?** — Does this target one specific bad output rather than improve outputs overall?
5. **Too vague?** — Is this so vague that it would be interpreted differently every time? (e.g., "be more natural" or "use a good tone")

## Output Format

Provide:

- A list of everything to cut, with a one-line reason for each
- A list of any conflicts found between files
- A cleaned up version of AGENTS.md with the dead weight removed
