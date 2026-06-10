---
name: obsidian
description: Use when reading, searching, creating, appending to, or editing notes in a filesystem-first Obsidian vault
platforms: [linux, macos, windows]
metadata:
  origin.url: https://raw.githubusercontent.com/NousResearch/hermes-agent/refs/heads/main/skills/note-taking/obsidian/SKILL.md
  origin.repository: NousResearch/hermes-agent
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing
notes, searching note files, creating notes, appending content, targeted edits,
and adding wikilinks.

## Harness Adaptation

Before using harness-specific tools, identify the active assistant harness. When
the active harness matches one metadata-linked reference above, load exactly
that one reference and skip the non-matching harness files. Use the shared
workflow below for decisions and the harness reference only to translate file,
search, shell, and edit operations into the active toolset.

## Vault Path

Use a known or resolved vault path before calling file tools.

The vault-path convention is `OBSIDIAN_VAULT_PATH`. If it is unset, use
`~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing
`$OBSIDIAN_VAULT_PATH` to file tools; resolve the vault path first and pass a
concrete absolute path. Vault paths may contain spaces, so prefer file tools or
carefully quoted shell commands.

If the vault path is unknown, use a shell command to resolve
`OBSIDIAN_VAULT_PATH` or check whether the fallback path exists. Once the path
is known, switch back to the harness's preferred file tools.

## Operations

| Task | Workflow |
|---|---|
| Read a note | Read the resolved absolute path to the note. |
| List notes | Search file names under the resolved vault path. Use `*.md` for all Markdown notes. |
| Search note contents | Search content under the resolved vault path and restrict to `*.md` when needed. |
| Create a note | Write the full Markdown content to the resolved absolute path. |
| Append to a note | Read the note, then use an anchored edit when stable context exists. Rewrite the whole note only when that is clearer. |
| Targeted edits | Use focused exact edits based on current content and stable context. |

For a simple append with no stable context, a carefully quoted shell append is
acceptable if it is the clearest safe option.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating or updating
notes, use wikilinks to connect related content.
