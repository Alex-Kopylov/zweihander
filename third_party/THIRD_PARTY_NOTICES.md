# Third-Party Notices

This marketplace includes material copied, ported, or synced from the projects
listed below. See [README.md](README.md) for the linked inventory.

## Superpowers-Derived Test-First Process

The test-first process of `python-dev-workflow:tests-manager` was absorbed from
Superpowers:

- Upstream: https://github.com/obra/superpowers
- Upstream plugin version: `5.1.3`
- Author: Jesse Vincent
- License: MIT

| Local plugin/skill | Relationship | Upstream source |
|---|---|---|
| `python-dev-workflow:tests-manager` | Test-first process absorbed from the formerly separate `dev-workflow:test-driven-development` copied skill; its testing anti-patterns ported from TypeScript to Python and pytest in `references/rules/mocking.md` | https://github.com/obra/superpowers/tree/main/skills/test-driven-development |

### MIT License Notice

MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## pstack

The `giant-armor` and `formal-verification` plugins, and the skills listed
below in `dev-workflow`, `work-session-tools` and `ai-assistant-ops`, were
ported from pstack (the zstack port, Alex-Kopylov/zweihander#173). Files were
copied byte-for-byte, then adapted: `poteto-mode` became `fire`, pstack
became zstack, Bugbot became AI Reviewer, the principle skills became
reference files, Cursor tool names map through the harness action matrix,
and user-only invocation is declared for each harness.

| Local plugin/skill | Relationship | Upstream source |
|---|---|---|
| `giant-armor:fire` | Router skill `poteto-mode`, renamed; its first paragraph became the Leaf skills rule | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/poteto-mode/SKILL.md |
| `giant-armor:fire` `playbooks/` | 15 of 23 playbooks, as-is apart from the rename and vocabulary rules | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/poteto-mode/playbooks |
| `giant-armor:fire` `references/ai-reviewer-triage.md` | `bugbot-triage.md`, Bugbot renamed to AI Reviewer | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/poteto-mode/references/bugbot-triage.md |
| `giant-armor:fire` `references/principles/` | The 24 `principle-*` skills as reference files | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills |
| `dev-workflow:how` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/how |
| `dev-workflow:why` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/why |
| `dev-workflow:teach` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/teach |
| `dev-workflow:architect` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/architect |
| `dev-workflow:arena` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/arena |
| `dev-workflow:swarm` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/swarm |
| `dev-workflow:interrogate` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/interrogate |
| `dev-workflow:blast-radius` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/blast-radius |
| `dev-workflow:benchmark-checklist` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/benchmark-checklist |
| `dev-workflow:no-comments` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/no-comments |
| `dev-workflow:typescript-best-practices` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/typescript-best-practices |
| `work-session-tools:recall` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/recall |
| `work-session-tools:ketchup` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/ketchup |
| `work-session-tools:bro` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/bro |
| `work-session-tools:in-your-own-words` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/in-your-own-words |
| `work-session-tools:sharpen` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/sharpen |
| `work-session-tools:show-me-your-work` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/show-me-your-work |
| `ai-assistant-ops:reflect` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/reflect |
| `ai-assistant-ops:correct` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/correct |
| `ai-assistant-ops:unslop` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/unslop |
| `ai-assistant-ops:technical-writing` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/technical-writing |
| `formal-verification:create-formal-verification-skill` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/create-formal-verification-skill |
| `formal-verification:maintain-formal-verification-skill` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/maintain-formal-verification-skill |
| `formal-verification:statechart` | Copied skill without `scripts/test/` (#176) | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/statechart |
| `giant-armor:figure-it-out` | Copied skill | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/figure-it-out |
| `dev-workflow` agent `comment-sicko` | Copied agent | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/agents/comment-sicko.md |
| `giant-armor` agent `poteto-agent` | Copied agent | https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack/agents/poteto-agent.md |

- Upstream: https://github.com/cursor/plugins/tree/main/pstack
- Synced commit: `ae5650febf4320793844c12c4adaa937f417f8da` (pstack v0.15.36)
- Author: Lauren Tan
- License: MIT

### MIT License Notice

See [pstack-LICENSE.txt](pstack-LICENSE.txt).

## Matt Pocock Skills

The following `work-session-tools` skill was copied from Matt Pocock's skills
repository and adapted for this marketplace.

| Local skill | Upstream source |
|---|---|
| `work-session-tools:handoff` | https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff |

- Upstream: https://github.com/mattpocock/skills
- Synced commit: `84fdeffd12f2ee307994d1eb6feb48173b6e0502`
- Author: Matt Pocock
- License: MIT

### MIT License Notice

See [mattpocock-skills-LICENSE.txt](mattpocock-skills-LICENSE.txt).

## Hermes Agent-Derived Skills

The following skills were ported from Nous Research's Hermes Agent and adapted
for Codex and Claude Code. Upstream authors are recorded here because the
ported skills no longer carry them in frontmatter.

| Local skill | Upstream source | Upstream author |
|---|---|---|
| `research:arxiv` | https://github.com/NousResearch/hermes-agent/tree/main/skills/research/arxiv | Hermes Agent |
| `research:grounded-citations` | https://github.com/NousResearch/hermes-agent/tree/main/skills/research/grounded-citations | Hermes Agent, Teknium |
| `research:llm-wiki` | https://github.com/NousResearch/hermes-agent/tree/main/skills/research/llm-wiki | Hermes Agent |
| `research:obsidian` | https://github.com/NousResearch/hermes-agent/tree/main/skills/note-taking/obsidian | Teknium (teknium1), Hermes Agent |
| `web:reddit-reading` | https://github.com/NousResearch/hermes-agent/tree/main/optional-skills/social-media/reddit-reading | Teknium (teknium1), Hermes Agent |
| `web:rss-feeds` | https://github.com/NousResearch/hermes-agent/tree/main/optional-skills/research/rss-feeds | Teknium (teknium1), Hermes Agent |
| `web:blogwatcher` | https://github.com/NousResearch/hermes-agent/tree/main/optional-skills/research/blogwatcher | JulienTant (fork of Hyaxia/blogwatcher) |
| `web:youtube-content` | https://github.com/NousResearch/hermes-agent/tree/main/skills/media/youtube-content | Teknium (teknium1), Hermes Agent |
| `web:xurl` | https://github.com/NousResearch/hermes-agent/tree/main/skills/social-media/xurl | xdevplatform, openclaw, Hermes Agent |
| `web:blocked-page-recovery` | https://github.com/NousResearch/hermes-agent/tree/main/skills/web/blocked-page-recovery | Hermes Agent |

The script tests under `tests/unit/plugins/research/skills/grounded-citations/`
and `tests/unit/plugins/web/skills/` are adapted from Hermes Agent's
`tests/skills/` suite. Hermes Agent adapted `xurl` from
https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md (MIT).

- Upstream: https://github.com/NousResearch/hermes-agent
- Synced commit: `5f045f842a60184748dda30acb9fecbd961cc18b`
- License: MIT

### MIT License Notice

MIT License

Copyright (c) 2025 Nous Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## OpenClaw Test Audit

The value bar, junk patterns, retention bar, and audit method in
`python-dev-workflow:tests-manager` were adapted from OpenClaw's `test-audit`
skill, rewritten for Python and pytest, with the repository-specific tooling,
landing flow, and examples removed.

| Local file | Upstream source |
|---|---|
| `plugins/python-dev-workflow/skills/tests-manager/references/rules/test-value.md` | https://github.com/openclaw/openclaw/blob/bf636cc1bcdd59e65d5074a1bc309d903bf18e65/.agents/skills/test-audit/SKILL.md |
| `plugins/python-dev-workflow/skills/tests-manager/references/workflows/audit.md` | https://github.com/openclaw/openclaw/blob/bf636cc1bcdd59e65d5074a1bc309d903bf18e65/.agents/skills/test-audit/CAMPAIGN.md |

- Upstream: https://github.com/openclaw/openclaw
- Synced commit: `bf636cc1bcdd59e65d5074a1bc309d903bf18e65`
- Author: OpenClaw Foundation
- License: MIT

### MIT License Notice

See [openclaw-LICENSE.txt](openclaw-LICENSE.txt).

## Mermaid Documentation

The Markdown files in `plugins/mermaid-diagrams/skills/mermaid/references/` are
synced from Mermaid:

- Upstream: https://github.com/mermaid-js/mermaid
- Synced commit: `9bae92cd3214f9ec99369ab314ef41ffb283f6b6`
- License: MIT
- Sync details: `plugins/mermaid-diagrams/THIRD_PARTY_NOTICES.md`

### MIT License Notice

The MIT License (MIT)

Copyright (c) 2014 - 2022 Knut Sveidqvist

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Agent Skills Specification

The file
`plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/references/agent-skills-specification.md`
is a copy of the Agent Skills format specification, kept locally so the
adaptation skill reads the specification it renders against instead of the
network.

- Upstream: https://github.com/agentskills/agentskills
- Source document: https://agentskills.io/specification.md
- Retrieved: 2026-08-26
- Author: Anthropic, PBC
- License: Apache-2.0
- Change from upstream: the site's "Documentation Index" preamble block is
  removed; the specification text itself is unmodified.

### Apache License 2.0 Notice

Copyright 2025 Anthropic, PBC

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

The complete license text is in [agentskills-LICENSE.txt](agentskills-LICENSE.txt).
