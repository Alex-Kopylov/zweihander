# Third-Party Notices

This marketplace includes material copied, ported, or synced from the projects
listed below. See [README.md](README.md) for the linked inventory.

## Superpowers-Derived Dev Workflow Skills

Several `dev-workflow` skills and supporting files were copied from and adapted
from Superpowers:

- Upstream: https://github.com/obra/superpowers
- Upstream plugin version: `5.1.3`
- Author: Jesse Vincent
- License: MIT

The following copied skills and supporting files come from that upstream
Superpowers distribution.

| Local plugin/skill | Relationship | Upstream source |
|---|---|---|
| `dev-workflow` | Existing plugin integrating copied skills | https://github.com/obra/superpowers |
| `dev-workflow:dispatching-parallel-agents` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/dispatching-parallel-agents |
| `dev-workflow:requesting-code-review` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/requesting-code-review |
| `dev-workflow:systematic-debugging` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/systematic-debugging |
| `dev-workflow:test-driven-development` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/test-driven-development |
| `dev-workflow:using-git-worktrees` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/using-git-worktrees |
| `dev-workflow:verification-before-completion` | Copied skill | https://github.com/obra/superpowers/tree/main/skills/verification-before-completion |

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

## Matt Pocock Skills

The following `work-session-tools` skills were copied from Matt Pocock's skills
repository and adapted for this marketplace.

| Local skill | Upstream source |
|---|---|
| `work-session-tools:handoff` | https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff |
| `work-session-tools:wait-what` | https://github.com/mattpocock/skills/tree/main/skills/productivity/wait-what |

- Upstream: https://github.com/mattpocock/skills
- Synced commit: `84fdeffd12f2ee307994d1eb6feb48173b6e0502`
- Author: Matt Pocock
- License: MIT

### MIT License Notice

See [mattpocock-skills-LICENSE.txt](mattpocock-skills-LICENSE.txt).

## Hermes Agent-Derived Research Skills

The following `research` skills were ported from Nous Research's Hermes Agent
and adapted for Codex and Claude Code:

| Local skill | Upstream source |
|---|---|
| `research:llm-wiki` | https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md |
| `research:obsidian` | https://github.com/NousResearch/hermes-agent/blob/main/skills/note-taking/obsidian/SKILL.md |

- Upstream: https://github.com/NousResearch/hermes-agent
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
