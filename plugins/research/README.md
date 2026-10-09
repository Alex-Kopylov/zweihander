# research

Research workflows: arXiv paper search, grounded citations, an LLM-maintained
Markdown wiki, and Obsidian vault notes.

## Origin

This plugin ports four MIT-licensed skills from
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent):

| Skill | Upstream path |
|---|---|
| `arxiv` | `skills/research/arxiv` |
| `grounded-citations` | `skills/research/grounded-citations` |
| `llm-wiki` | `skills/research/llm-wiki` |
| `obsidian` | `skills/note-taking/obsidian` |

The port drops Hermes-only frontmatter, replaces Hermes tool names with
harness-neutral wording, and wires skill-to-skill references through the
harness `call` filter. `grounded-citations` routes its multi-platform sweeps
through the `web` plugin's skills.

<details>
<summary>Skills</summary>

| Skill | Description |
|---|---|
| `arxiv` | Search arXiv by keyword, author, category, or ID; generate BibTeX; look up citations and related papers via Semantic Scholar. |
| `grounded-citations` | Cite fetched sources inline with a ledger that assigns stable ids, renders Sources blocks, and verifies drafts and verbatim evidence. |
| `llm-wiki` | Build, query, ingest into, and lint an interlinked Markdown research wiki inspired by Andrej Karpathy's LLM Wiki pattern. |
| `obsidian` | Read, search, create, append to, and edit notes in a filesystem-first Obsidian vault. |

</details>
