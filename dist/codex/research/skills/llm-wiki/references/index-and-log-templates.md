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

## `log.jsonl`

Each line is one JSON object with exactly these fields:

- `date`: `YYYY-MM-DD`.
- `action`: `create`, `ingest`, `update`, `archive`, or `delete`.
- `summary`: one sentence with the result.
- `reason`: the user's intent: the outcome they want, their motivation,
  constraints, and preferences. Quote their wording when it helps. Mark
  inferred intent as inferred and missing intent as unstated. May be longer
  than one sentence.
- `links`: wiki-relative paths to the pages a reader should open. Not a list
  of every changed file; Git keeps that.

Append one line per high-level change, not per commit. Never rewrite existing
lines. Read-only queries and checks do not create objects. The file has no
header. Escape line breaks inside strings so each object stays on one line.

```json
{"date":"YYYY-MM-DD","action":"create","summary":"Initialized a wiki for [domain].","reason":"[What the user wants the wiki for.]","links":["SCHEMA.md","index.md"]}
```
