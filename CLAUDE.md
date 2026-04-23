# My Marketplace — Claude Code Plugin Marketplace

## Plugin Release Rules

- Always bump the version in `plugin.json` when adding new skills, agents, or commands. The plugin manager uses version comparison, not git diff — unchanged versions are skipped during updates.
- After bumping, use `/python-dev-workflow:version-bumper` to handle version updates across config files, then `/python-dev-workflow:commit` to commit.
