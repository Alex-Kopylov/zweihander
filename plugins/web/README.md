# web

Web, social, and feed reading workflows.

## Origin

This plugin ports six MIT-licensed skills from
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent):

| Skill | Upstream path |
|---|---|
| `reddit-reading` | `optional-skills/social-media/reddit-reading` |
| `rss-feeds` | `optional-skills/research/rss-feeds` |
| `blogwatcher` | `optional-skills/research/blogwatcher` |
| `youtube-content` | `skills/media/youtube-content` |
| `xurl` | `skills/social-media/xurl` |
| `blocked-page-recovery` | `skills/web/blocked-page-recovery` |

The port drops Hermes-only frontmatter and replaces Hermes tool names with
harness-neutral wording. References to other skills are optional or
situational, so they are written as plain skill names rather than through the
harness `call` filter. Script tests live under `tests/unit/plugins/web/`.
