---
name: ai-setup-audit
description: This skill should be used when the user asks to "audit my setup", "check my claude.md", "review my AI config", "clean up my instructions", "find conflicts in my setup", "optimize my claude setup", or mentions reviewing instruction files, skills folders, context files, or preferences for contradictions, redundancy, or dead weight.
disable-model-invocation: true
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# AI Setup Audit

Read the entire setup before responding.

## Scope

Check CLAUDE.md, every skill in the skills folder, every file in the context folder, and any other instruction files found.

Then go through every rule, instruction, and preference found.

## Analysis Criteria

For each rule, instruction, or preference, evaluate:

1. **Already default?** — Is this something Claude already does by default without being told?
2. **Conflicts?** — Does this contradict or conflict with another rule somewhere else in the setup?
3. **Redundant?** — Does this repeat something that's already covered by a different rule or file?
4. **Reactive patch?** — Does this read like it was added to fix one specific bad output rather than improve outputs overall?
5. **Too vague?** — Is this so vague that it would be interpreted differently every time? (e.g., "be more natural" or "use a good tone")

## Output Format

Provide:

- A list of everything to cut, with a one-line reason for each
- A list of any conflicts found between files
- A cleaned up version of CLAUDE.md with the dead weight removed
