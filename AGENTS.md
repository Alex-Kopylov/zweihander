# My Marketplace

## Plugin And Marketplace Versions

- When changing plugin or marketplace content that users should receive, bump versions according to the official Claude Code and Codex plugin marketplace documentation.
- Claude Code uses plugin versions as cache keys for update detection. If an explicit `version` is set in `.claude-plugin/plugin.json`, bump it for every released change; pushing commits without changing that version is not enough. Follow semantic versioning: MAJOR for breaking changes, MINOR for new features, PATCH for fixes.
- Codex plugin and marketplace metadata must be release-ready before adding or updating marketplace entries. Keep `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, and `.claude-plugin/marketplace.json` aligned with the release and install behavior described by the current docs.
- Use this repo's `version-bumper` skill at `plugins/python-dev-workflow/skills/version-bumper/SKILL.md` to discover and bump version-bearing files such as `plugin.json`, `marketplace.json`, and package metadata.
- Official references:
  - Claude Code plugin versioning: https://code.claude.com/docs/en/plugins-reference#version-management
  - Claude Code plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels
  - Codex plugin marketplaces: https://developers.openai.com/codex/plugins/build#how-codex-uses-marketplaces
  - Codex marketplace metadata: https://developers.openai.com/codex/plugins/build#marketplace-metadata
