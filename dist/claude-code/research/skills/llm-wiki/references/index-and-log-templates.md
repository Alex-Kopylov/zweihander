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
- `subject`: short description of the operation.
- `files`: relative paths for every changed wiki file, in lexicographic order.
- `summary`: one sentence with the result.

Append one line per high-level change. Never rewrite existing lines. Read-only
queries and checks do not create objects. The file has no header.

```json
{"date":"YYYY-MM-DD","action":"create","subject":"Wiki initialized","files":["SCHEMA.md","index.md","log.jsonl","raw/AGENTS.md","tags.json"],"summary":"Initialized a wiki for [domain]."}
```
