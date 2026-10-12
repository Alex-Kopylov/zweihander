# raw/ — rules for agents

- Originals live here by type: `articles/` for web articles and clippings, `papers/` for PDFs and arXiv papers, `transcripts/` for meeting notes and interviews, `assets/` for images. Names are `<author>-<topic>-<year>.<ext>`.
- An original that is not Markdown gets a Markdown copy in `converted/`, same name with `.md`. A Markdown original is its own copy.
- A converter may change only the formatting, never the text. These files stay raw: no summaries, no rewording, no fixes, no removed sections.
- Only add new files. Never overwrite or delete without an explicit request from the user.
- Every raw Markdown file carries the frontmatter fields `title`, `source_url`, `pdf_url`, `published`, `ingested`, `type: full-text`, `fetch_method`, and `sha256` of the body below the frontmatter. On re-ingest, an unchanged hash means skip; a changed hash means source drift, flag it.
- If a source cannot be converted cleanly, keep the original here and say so on the wiki page (`confidence: low`).
- If the original is behind a paywall, there is no raw file. The wiki page is built from the abstract and gets `confidence: low`.
- If the raw file is a preprint rather than the journal version, the wiki page says so.
