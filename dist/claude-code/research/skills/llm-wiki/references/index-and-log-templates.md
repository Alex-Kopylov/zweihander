# Navigation templates

## `index.md`

```markdown
# Wiki Index

> Content catalog. Every page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N
> When a section exceeds 50 entries, split it by first letter or sub-domain.
> When the index exceeds 200 entries, create topic-map.md grouping pages by theme.

## Start here

| Page | What it gives |
|---|---|
| [[entry-page]] | the entry article with the reading order |
| [[project-context]] | what the project needs from the wiki |

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

## `log.md`

```markdown
# Wiki Log

> Chronological record of high-level changes to wiki content or structure. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, create, archive, delete
> Read-only queries and checks do not create log entries.
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, tags.json, index.md, log.md, raw/AGENTS.md
```
