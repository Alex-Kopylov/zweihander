# Wiki Schema

Two parts. **Part 1, domain and project:** what the wiki covers and the values that fill the placeholders `<project>` and `<glossary>` in part 2. **Part 2, general rules:** how every page is built. Part 1 is this wiki's own; part 2 changes rarely.

# Part 1. Domain and project

## Domain

[What this wiki covers and the project or goal it serves, in 2–4 sentences. Then 2–4 links: the entry page with the reading order, the project context page, the source ranking if one exists.]

## Project parameters

| Placeholder | Value in this wiki |
|---|---|
| `<project>` | [short project name used in section headings and in the TL;DR] |
| `<glossary>` | [[glossary]] |
| Catalogs a new page joins | [index.md](index.md) [plus any ranking or hub page] |
| Example "What to do" actions | ["check X against dataset Y", "ask the client about Z"] |

## Base articles

One base article per core term of the domain, plus the glossary. Terms link here, not to Wikipedia.

| Article | File |
|---|---|
| [Term] | [[slug]] |
| Glossary | [[glossary]] |

## Tag taxonomy

Tags live in [tags.json](tags.json), grouped by key. A new tag is added there first, then used.

# Part 2. General rules

## Layout

| Folder | Holds | File name |
|---|---|---|
| `raw/articles/`, `raw/papers/`, `raw/transcripts/` | originals by type, in native format; rules in [raw/AGENTS.md](raw/AGENTS.md) | `<author>-<topic>-<year>.<ext>` |
| `raw/converted/` | Markdown copies of originals that are not Markdown; conversion changes formatting only, never text | `<author>-<topic>-<year>.md` |
| `raw/assets/` | images and diagrams referenced by pages | |
| `entities/` | people, organizations, products, models | `<name>.md` |
| `concepts/` | topics and concepts; base articles; glossary | `<topic>.md` |
| `comparisons/` | side-by-side analyses | `<topic>.md` |
| `queries/` | filed query answers worth keeping | `<question>.md` |

File names are lowercase with hyphens, no spaces.

## Conventions

- Every page starts with YAML frontmatter.
- Links are `[[wikilinks]]`, at least 2 outbound per page.
- Updating a page bumps `updated`.
- A new page joins the catalogs from part 1.
- Every action is appended to [log.md](log.md).
- Figures and claims come from `raw/`. Verify each by grep over the raw Markdown before saving.
- Markdown tables and mermaid diagrams where they fit, in moderation.
- Reader-friendly text: rules in "Reader frame" below.

## Page style: like Wikipedia

The reader is entering the domain. Pages are connected prose, not compressed bullets.

- **TL;DR.** Callout `[!tldr]` right after the H1; format in "Reader frame".
- **Lead paragraph.** The first sentence defines the subject: "**Term** is…". For an entity: "**Name** is a [what it is], [where and since when]. It…".
- **Prose.** Sections are paragraphs of 3–6 full sentences. Lists only for enumerations, tables only for numbers and comparisons.
- **Terms.** Every term and abbreviation is explained at its first mention on the page, then linked to its base article or to `<glossary>`.
- **Wikipedia links.** The first mention of a term on a page links to its English Wikipedia article. Link only to an article whose existence was checked through the Wikipedia API: `https://en.wikipedia.org/api/rest_v1/page/summary/<Title>` returns 200. A term with a base article links there instead; its Wikipedia link lives only in the base article and the glossary. "See also" and "Sources" get no term links.
- **No Wikipedia article.** An entity or concept with a wiki page links to it (`[[slug|name]]`). A dataset, library, or product links to its official source: the publisher's site, the repository, the documentation. A paper links to arXiv or DOI. Check the address before inserting: HTTP 200 and the page title. Inside tables, write the link label separator as `\|`, or the table breaks.
- **Numbers with meaning.** Next to every metric, say what it measures and whether the value is good.
- **Entity page structure:** TL;DR → lead → Overview → Key facts and dates → Relationships → Relevance to `<project>` → See also → Sources.
- **Concept page structure:** TL;DR → lead → History → How it works → Current state of knowledge → Open questions and debates → Relevance to `<project>` → See also → Sources.
- **Comparison structure:** TL;DR → lead with the snapshot date → What is compared and how → Comparison table → Verdict → Relevance to `<project>` → See also → Sources.
- **Footnotes.** A claim from a specific source gets `^[raw/<path>.md]`. Textbook knowledge without a footnote marks the page `confidence: medium`.

## Reader frame

The reader has a small working memory, finds starting hard, cannot tell vague estimates apart, and loses the main point in the middle of a text. So every page has a rigid frame: at the top, the answer to "what is this and why should I care"; at the bottom, what to do and what to read next. Between them, a long body with headings to jump by. The rules follow ISO 24495-1 (plain language), ASD-STE100, and W3C COGA guidance.

### Frame

- **TL;DR right after the H1**, before the metadata line. Obsidian callout `[!tldr]` with three fixed lines, sample below. If `confidence: low`, `contested: true`, or the raw file is a preprint or an abstract only, add a fourth line **Caution:** with the reason.
- **The `<project>` section** ends with a **What to do** list of at most 3 items. Each item is one bounded action with a verb. No actions: say so, "no actions, context only".
- **See also** has at most 5 links, each with a one-line reason. The first link is the one to read next.
- **Check before saving:** from the TL;DR and the "What to do" list alone, the reader knows what this is and why it matters, without reading the middle.

TL;DR sample:

```markdown
> [!tldr]
> **What it is:** one sentence.
> **Key point:** one conclusion or one number.
> **For <project>:** what it changes for the project, one sentence.
```

### Sentences and words

- One idea per sentence, active voice, named actor. Sentences up to 25 words, paragraphs up to 6 sentences.
- One term, one word across the wiki. The word is fixed in `<glossary>`; synonyms are not used.
- A gloss at first mention is five words or fewer, then a link.
- Split a chain of 3+ nouns with a preposition or a hyphen.
- Prose uses full sentences with conjunctions. List and table rows may use a bold subject plus a short clause.
- No vague estimates: instead of "many", "recently", "significantly", give a number, a date, or a range.

### Never

- An announcing paragraph ("below we first cover…, then…"). Headings are the map.
- A caveat after the claim. A caveat that changes how a number or conclusion reads stands before it, in the same paragraph. "Limitations and critique" stays at the end as the summary.
- A second emoji on a line. The only emoji system in the wiki is freshness 🟢🟡⚪️.

## Raw layer

All rules for `raw/` are in [raw/AGENTS.md](raw/AGENTS.md). Read it before writing into `raw/` and before writing a page from a source.

## Frontmatter

[Paste the body of [frontmatter.md](frontmatter.md) here, without its H1.]

## Freshness: the main value signal

[Paste the body of [freshness.md](freshness.md) here, without its H1.]

## Page thresholds

- Create a page when an entity or concept appears in 2+ sources or is central to one source.
- Add to an existing page when a source mentions something already covered.
- Do not create pages for passing mentions, minor details, or out-of-domain items.
- Split a page when it exceeds about 200 lines.
- Archive a fully superseded page under `_archive/` and remove it from the index.

## Update policy

1. A new source contradicts an old one: check dates; the newer one usually wins.
2. The contradiction is real: record both positions with dates and sources, set `contested: true`.
3. A single unverified claim: `confidence: low`.
