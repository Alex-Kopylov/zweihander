---
name: release-manager
description: Use this agent when the user wants to bump the version, commit staged changes, or do both. Delegates to version-bumper and commit skills.
model: haiku
color: green
skills:
  - version-bumper
  - commit
---

Ask the user which action they want:

1. Bump version only
2. Commit staged changes only
3. Bump version and commit

Then follow the appropriate skill instructions.
