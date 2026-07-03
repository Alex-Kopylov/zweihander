---
name: llm-wiki
description: Use when creating, maintaining, querying, ingesting into, or auditing an interlinked Markdown research wiki or knowledge base
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  origin.url: https://raw.githubusercontent.com/NousResearch/hermes-agent/refs/heads/main/skills/research/llm-wiki/SKILL.md
  origin.repository: NousResearch/hermes-agent
---

# Karpathy's LLM Wiki

Build and maintain a persistent, compounding knowledge base as interlinked
Markdown files. Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Unlike traditional RAG, which rediscovers knowledge from scratch per query, the
wiki compiles knowledge once and keeps it current. Cross-references are already
there, contradictions have already been flagged, and synthesis reflects
everything ingested.

**Division of labor:** The human curates sources and directs analysis. The
assistant summarizes, cross-references, files, and maintains consistency.

## When To Use

Use this skill when the user:

- Asks to create, build, or start a wiki or knowledge base.
- Asks to ingest, add, or process a source into their wiki.
- Asks a question and an existing wiki is present at the configured path.
- Asks to lint, audit, or health-check their wiki.
- References their wiki, knowledge base, or notes in a research context.

## Wiki Location

Use `WIKI_PATH` when set. Otherwise default to `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

The wiki is just a directory of Markdown files. It can be opened in Obsidian, VS
Code, or any editor. No database or special tooling is required.

## Architecture

```text
wiki/
|-- SCHEMA.md           # Conventions, structure rules, domain config
|-- index.md            # Sectioned content catalog with one-line summaries
|-- log.md              # Chronological action log, append-only and rotated yearly
|-- raw/                # Layer 1: immutable source material
|   |-- articles/       # Web articles and clippings
|   |-- papers/         # PDFs and arXiv papers
|   |-- transcripts/    # Meeting notes and interviews
|   `-- assets/         # Images and diagrams referenced by sources
|-- entities/           # Layer 2: people, orgs, products, models
|-- concepts/           # Layer 2: topics and concepts
|-- comparisons/        # Layer 2: side-by-side analyses
`-- queries/            # Layer 2: filed query results worth keeping
```

- **Raw sources:** Immutable. Read them, but do not modify them.
- **Wiki pages:** Assistant-owned Markdown files created, updated, and
  cross-referenced by the assistant.
- **Schema:** `SCHEMA.md` defines structure, conventions, thresholds, and tag
  taxonomy.

## Orient First

When the user has an existing wiki, orient before ingesting, querying, or
linting:

1. Read `SCHEMA.md` for the domain, conventions, thresholds, and tags.
2. Read `index.md` for pages and summaries.
3. Scan the last 20-30 entries of `log.md` for recent activity.
4. For large wikis with 100+ pages, search the wiki for the topic before
   creating anything new.

This prevents duplicate pages, missed cross-references, schema contradictions,
and repeated work.

## Initialize A New Wiki

When the user asks to create or start a wiki:

1. Resolve the wiki path from `WIKI_PATH`, the user's explicit path, or
   `~/wiki`.
2. Create the directory structure above.
3. Ask what domain the wiki covers; be specific.
4. Write `SCHEMA.md` customized to that domain.
5. Write initial `index.md`.
6. Write initial `log.md` with a creation entry.
7. Confirm the wiki is ready and suggest first sources to ingest.

### `SCHEMA.md` Template

Adapt this to the user's domain:

````markdown
# Wiki Schema

## Domain
[What this wiki covers, such as "AI/ML research", "personal health", or
"startup intelligence".]

## Conventions
- File names: lowercase, hyphens, no spaces, for example `transformer-architecture.md`.
- Every wiki page starts with YAML frontmatter.
- Use `[[wikilinks]]` to link between pages; minimum 2 outbound links per page.
- When updating a page, bump the `updated` date.
- Add every new page to `index.md` under the correct section.
- Append every action to `log.md`.
- On pages that synthesize 3+ sources, append provenance markers like
  `^[raw/articles/source-file.md]` to paragraphs whose claims come from a
  specific source.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

`confidence`, `contested`, and `contradictions` are optional but recommended for
opinion-heavy, single-source, fast-moving, or unresolved claims.

### Raw Source Frontmatter

Raw sources also get frontmatter so re-ingests can detect drift:

```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of body content below the frontmatter>
---
```

Compute `sha256` over the body only. On re-ingest, skip unchanged sources and
flag changed hashes as source drift.

## Tag Taxonomy
[Define 10-20 top-level tags. Add new tags here before using them.]

Example for AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine-tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

Every page tag must appear in this taxonomy.

## Page Thresholds
- Create a page when an entity or concept appears in 2+ sources or is central
  to one source.
- Add to an existing page when a source mentions something already covered.
- Do not create pages for passing mentions, minor details, or out-of-domain
  items.
- Split a page when it exceeds about 200 lines.
- Archive a fully superseded page under `_archive/` and remove it from the
  index.

## Entity Pages
Include overview, key facts and dates, relationships, wikilinks, and source
references.

## Concept Pages
Include definition, current state of knowledge, open questions or debates, and
related concepts.

## Comparison Pages
Include what is being compared, comparison dimensions, verdict or synthesis,
and sources.

## Update Policy
When new information conflicts with existing content:
1. Check dates; newer sources usually supersede older ones.
2. If genuinely contradictory, record both positions with dates and sources.
3. Mark the contradiction in frontmatter.
4. Flag it for user review in the lint report.
````

### `index.md` Template

```markdown
# Wiki Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

When any section exceeds 50 entries, split it by first letter or sub-domain.
When the index exceeds 200 entries total, create `_meta/topic-map.md` grouping
pages by theme.

### `log.md` Template

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, index.md, log.md
```

## Core Operations

### Ingest

When the user provides a URL, file, or paste:

1. Capture the raw source.
   - URL: fetch clean Markdown and save under `raw/articles/`.
   - PDF: extract text/Markdown and save under `raw/papers/`.
   - Pasted text: save under the appropriate `raw/` subdirectory.
   - Name files descriptively, such as `raw/articles/karpathy-llm-wiki-2026.md`.
   - Add raw frontmatter with `source_url`, `ingested`, and body `sha256`.
2. Discuss takeaways with the user: what is interesting and what matters for
   the domain. Skip this only in automated or cron contexts.
3. Check what already exists by searching `index.md` and wiki pages for
   mentioned entities and concepts.
4. Write or update wiki pages.
   - Create pages only when they meet `SCHEMA.md` thresholds.
   - Update existing pages, bump `updated`, and follow the update policy for
     conflicts.
   - Add at least 2 outbound `[[wikilinks]]` and check whether relevant pages
     should link back.
   - Use only tags from `SCHEMA.md`.
   - Add provenance markers on pages synthesizing 3+ sources.
   - Use `confidence: medium` or `confidence: low` for weak, single-source, or
     fast-moving claims.
5. Update navigation.
   - Add new pages to `index.md`, alphabetically within the right section.
   - Update "Total pages" and "Last updated".
   - Append a `log.md` entry and list every file created or updated.
6. Report every wiki file created or updated.

Ask before mass-updating if an ingest would touch 10 or more existing pages.

### Query

When the user asks a question about the wiki's domain:

1. Read `index.md` to identify relevant pages.
2. For wikis with 100+ pages, search all Markdown pages for key terms.
3. Read relevant pages.
4. Synthesize an answer from the compiled knowledge and cite wiki pages, for
   example "Based on [[page-a]] and [[page-b]]...".
5. File valuable answers back into `queries/` or `comparisons/` only when the
   answer is substantial, novel, or painful to rederive.
6. Update `log.md` with the query and whether it was filed.

### Lint

When the user asks to lint, health-check, or audit the wiki, check:

1. Orphan pages with no inbound `[[wikilinks]]`.
2. Broken `[[links]]` pointing to pages that do not exist.
3. Index completeness by comparing wiki files against `index.md`.
4. Frontmatter completeness and tag taxonomy compliance.
5. Stale pages whose `updated` date is more than 90 days older than the most
   recent relevant source.
6. Contradictions, including pages with `contested: true` or `contradictions:`.
7. Quality signals: `confidence: low`, single-source pages without confidence,
   and unsupported high-confidence claims.
8. Source drift by recomputing raw source body hashes.
9. Pages over 200 lines.
10. Tags used but not defined in `SCHEMA.md`.
11. Whether `log.md` exceeds 500 entries and should be rotated.

Report findings by severity: broken links, orphans, source drift, contested
pages, stale content, then style issues. Append a lint entry to `log.md`.

## Bulk Ingest

When ingesting multiple sources at once:

1. Read all sources first.
2. Identify entities and concepts across all sources.
3. Check existing pages for all of them in one search pass.
4. Create or update pages in one pass.
5. Update `index.md` once at the end.
6. Write one `log.md` entry covering the batch.

## Archiving

When content is fully superseded or the domain scope changes:

1. Create `_archive/` if needed.
2. Move the page to `_archive/` with its original path.
3. Remove it from `index.md`.
4. Replace inbound wikilinks with plain text plus "(archived)".
5. Log the archive action.

## Obsidian Integration

The wiki directory works as an Obsidian vault:

- `[[wikilinks]]` render as clickable links.
- Graph View visualizes the knowledge network.
- YAML frontmatter powers Dataview queries.
- `raw/assets/` holds images referenced via `![[image.png]]`.

For best results, set Obsidian's attachment folder to `raw/assets/`, keep
Wikilinks enabled, and install Dataview. If using the `obsidian` skill alongside
this one, set `OBSIDIAN_VAULT_PATH` to the same directory as `WIKI_PATH`.

On headless machines, `obsidian-headless` can sync a wiki via Obsidian Sync
without a GUI:

```bash
npm install -g obsidian-headless
ob login --email <email> --password '<password>'
ob sync-create-remote --name "LLM Wiki"
cd ~/wiki
ob sync-setup --vault "<vault-id>"
ob sync --continuous
```

## Pitfalls

| Pitfall | Correction |
|---|---|
| Modifying `raw/` files | Treat raw sources as immutable; corrections belong in wiki pages. |
| Skipping orientation | Read schema, index, and recent log before operations. |
| Skipping `index.md` or `log.md` updates | Keep navigation and history current every time. |
| Creating pages for passing mentions | Follow page thresholds. |
| Creating isolated pages | Add at least 2 outbound links and check backlinks. |
| Freeform tags | Add tags to the schema taxonomy before using them. |
| Oversized pages | Split pages over about 200 lines into focused pages. |
| Silent overwrite of contradictions | Record both claims, mark frontmatter, and flag for review. |

## Related Tools

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) is a
Node.js CLI that compiles sources into a concept wiki with the same Karpathy
inspiration. Use this skill for agent-in-the-loop curation; use llmwiki when
you want batch compilation of a source directory.
