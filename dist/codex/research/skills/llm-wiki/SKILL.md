---
name: llm-wiki
description: Use when creating, maintaining, querying, ingesting into, or auditing an interlinked Markdown research wiki or knowledge base
---

# LLM Wiki

Build and maintain a persistent, compounding knowledge base as interlinked
Markdown files. Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f),
extended with Wikipedia-style pages and a reader frame for readers with a
small working memory.

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
|-- SCHEMA.md           # Domain parameters, page style, reader frame, thresholds
|-- tags.json           # Tag taxonomy, grouped by key
|-- index.md            # Sectioned content catalog with a "Start here" table
|-- log.md              # Chronological action log, append-only and rotated yearly
|-- _meta/
|   |-- frontmatter.md  # Page frontmatter fields and allowed values
|   `-- freshness.md    # How `freshness` follows from `published`
|-- raw/                # Layer 1: immutable originals in native format
|   |-- AGENTS.md       # Rules for anyone writing into raw/
|   |-- converted/      # Markdown copies of the originals for the assistant
|   `-- assets/         # Images and diagrams referenced by pages
|-- entities/           # Layer 2: one source, one page
|-- concepts/           # Layer 2: topic syntheses, base articles, glossary
|-- comparisons/        # Layer 2: side-by-side analyses
`-- queries/            # Layer 2: filed query results worth keeping
```

- **Raw sources:** Immutable. The original stays in its native format; a
  converted Markdown copy with frontmatter and a body hash serves the
  assistant. Read them, never modify them. The rules live in `raw/AGENTS.md`.
- **Wiki pages:** Assistant-owned Markdown files created, updated, and
  cross-referenced by the assistant.
- **Schema:** `SCHEMA.md` is the contract. Part 1 holds the domain and the
  project parameters; part 2 holds the general rules: layout, page style,
  reader frame, thresholds, update policy. It links to `_meta/` for the
  frontmatter fields and the freshness labels.
- **Tags:** `tags.json` is the taxonomy. Every `tags` value on a page comes
  from it.

## Helper Scripts

- [scripts/body_sha256.sh](scripts/body_sha256.sh) `<file.md>` prints the sha256 of the body below the
  frontmatter. It fills the `sha256` field of a converted raw file and
  recomputes it at lint to detect source drift.
- [scripts/freshness.sh](scripts/freshness.sh) `<YYYY-MM-DD>` prints `fresh`, `recent`, or
  `historical` for a `published` date by today's year. Never pick the label
  by hand.

## Orient First

When the user has an existing wiki, orient before ingesting, querying, or
linting:

1. Read `SCHEMA.md` for the domain, the project parameters, the page style,
   and the thresholds.
2. Read `tags.json` for the allowed tags.
3. Read `index.md` for pages and summaries.
4. Scan the last 20-30 entries of `log.md` for recent activity.
5. For large wikis with 100+ pages, search the wiki for the topic before
   creating anything new.

This prevents duplicate pages, missed cross-references, schema contradictions,
and repeated work.

## Initialize A New Wiki

When the user asks to create or start a wiki:

1. Resolve the wiki path from `WIKI_PATH`, the user's explicit path, or
   `~/wiki`.
2. Create the directory structure above.
3. Ask the user for the domain and for the project or goal the wiki serves;
   the latter becomes `<project>` in headings and TL;DRs.
4. Write `SCHEMA.md` from [references/schema-template.md](references/schema-template.md).
   Fill part 1 with the answers; keep part 2 as it is.
5. Write `tags.json` with 10-20 tags in 3-6 groups, as a JSON object mapping
   each group key to a list of tags.
6. Copy [references/frontmatter.md](references/frontmatter.md) and
   [references/freshness.md](references/freshness.md) into `_meta/`.
7. Write `raw/AGENTS.md` from [references/raw-agents-template.md](references/raw-agents-template.md).
8. Write `index.md` and `log.md` from [references/index-and-log-templates.md](references/index-and-log-templates.md).
9. Confirm the wiki is ready and suggest first sources to ingest.

## Core Operations

### Ingest

When the user provides a URL, file, or paste:

1. Capture the source under `raw/` by the rules in `raw/AGENTS.md`: the
   original in its native format, named `<author>-<topic>-<year>.<ext>`, and
   a converted Markdown copy under `raw/converted/` with frontmatter and the
   body `sha256` from `scripts/body_sha256.sh`. Conversion changes formatting
   only. A paywalled source gets no raw file; its page is built from the
   abstract with `confidence: low`.
2. Discuss takeaways with the user: what is interesting and what matters for
   the domain. Skip this only in automated or cron contexts.
3. Check what already exists by searching `index.md` and wiki pages for
   mentioned entities and concepts.
4. Write or update wiki pages by the page style and reader frame in
   `SCHEMA.md`:
   - Use the section structure for the page type. The TL;DR callout comes
     right after the H1. Sections are connected prose.
   - Explain every term at its first mention, then link it to the base
     article, the glossary, or a Wikipedia article whose existence you checked.
   - Take every figure from `raw/converted/` and confirm it there before
     saving. Footnote claims with `^[raw/converted/<file>.md]`.
   - Check every external link before inserting it: HTTP 200 and the page
     title.
   - Fill the frontmatter by `_meta/frontmatter.md`. Set `freshness` with
     `scripts/freshness.sh <published>`. Use only tags from `tags.json`.
   - Add at least 2 outbound `[[wikilinks]]` and check whether relevant pages
     should link back.
   - End the `<project>` section with a "What to do" list of at most 3
     actions. Keep "See also" at 5 links or fewer, each with a reason.
   - Create pages only when they meet the `SCHEMA.md` thresholds. Update
     existing pages, bump `updated`, and follow the update policy for
     conflicts.
5. Update navigation.
   - Add new pages to `index.md`, alphabetically within the right section.
     Revise "Start here" when the entry pages change.
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
4. Frontmatter completeness by `_meta/frontmatter.md`, and tags that are
   missing from `tags.json`.
5. Stale pages whose `updated` date is more than 90 days older than the most
   recent relevant source.
6. Contradictions, including pages with `contested: true` or `contradictions:`.
7. Quality signals: `confidence: low`, single-source pages without confidence,
   and unsupported high-confidence claims.
8. Source drift: `scripts/body_sha256.sh` on every converted raw file against
   its `sha256` field.
9. Pages over 200 lines.
10. Whether `log.md` exceeds 500 entries and should be rotated.
11. The TL;DR callout right after the H1, 3 or 4 lines.
12. The `<project>` section ending with a "What to do" list of at most 3 items.
13. "See also" with at most 5 links, each with a reason.
14. Source pages whose figures carry no footnote to a raw file.
15. `freshness` that disagrees with `scripts/freshness.sh <published>`.
16. External links that no longer return HTTP 200.
17. Vague quantities ("many", "recently", "significantly") where a number, a
    date, or a range belongs.

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
- `[!tldr]` callouts render as collapsible summary boxes.
- Graph View visualizes the knowledge network.
- YAML frontmatter powers Dataview queries.
- `raw/assets/` holds images referenced via `![[image.png]]`.

For best results, set Obsidian's attachment folder to `raw/assets/`, keep
Wikilinks enabled, and install Dataview. If using the `research:obsidian` skill
alongside this one, set `OBSIDIAN_VAULT_PATH` to the same directory as
`WIKI_PATH`.

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
| A summary or rewording inside `raw/` | Conversion changes formatting only; the summary is a wiki page. |
| Skipping orientation | Read schema, tags, index, and recent log before operations. |
| Skipping `index.md` or `log.md` updates | Keep navigation and history current every time. |
| Creating pages for passing mentions | Follow page thresholds. |
| Creating isolated pages | Add at least 2 outbound links and check backlinks. |
| Freeform tags | Add tags to `tags.json` before using them. |
| Oversized pages | Split pages over about 200 lines into focused pages. |
| Silent overwrite of contradictions | Record both claims, mark frontmatter, and flag for review. |
| A page of bullet points | Write connected prose; lists only for enumerations. |
| A term without a gloss | Explain it at first mention, then link it. |
| An unverified external link | Check HTTP 200 and the page title before inserting. |
| A caveat after the claim | Put the caveat before the number or conclusion it changes. |
| A `freshness` label typed by hand | Run `scripts/freshness.sh`; labels drift with the calendar. |

## Related Tools

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) is a
Node.js CLI that compiles sources into a concept wiki with the same Karpathy
inspiration. Use this skill for agent-in-the-loop curation; use llmwiki when
you want batch compilation of a source directory.
