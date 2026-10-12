# Frontmatter

Every wiki page opens with this block. Fields marked optional may be omitted.

```yaml
---
title: "Author et al. — what the source is about"
source_url: https://example.org/paper
published: YYYY-MM-DD
ingested: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
kind: review | method | benchmark | position   # entity only
freshness: fresh | recent | historical          # derived from published
tags: [from tags.json]
sources: [raw/converted/author-topic-year.md]
confidence: high | medium | low
contested: true              # optional
contradictions: [other-slug] # optional
---
```

`updated` moves on every edit of the page. `freshness` is never typed by hand; see [freshness.md](freshness.md).
