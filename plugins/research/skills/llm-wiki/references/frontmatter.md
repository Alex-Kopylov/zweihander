# Frontmatter

Every wiki page opens with this block. Fields marked optional may be omitted.

```yaml
---
title: Page Title
source_url: https://example.org/source      # optional
published: YYYY-MM-DD                        # date of the newest source the page rests on
ingested: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
freshness: fresh | recent | historical       # derived from published
tags: [from tags.json]
sources: [raw/articles/author-topic-year.md]
confidence: high | medium | low
contested: true              # optional
contradictions: [other-slug] # optional
---
```

`updated` moves on every edit of the page. `freshness` is never typed by hand; it follows from `published` by the Freshness rules.
