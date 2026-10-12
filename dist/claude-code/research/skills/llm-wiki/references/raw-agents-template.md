# raw/ — rules for agents

- Original sources live here in their native format (PDF, HTML, Markdown), named `<author>-<topic>-<year>.<ext>`.
- Every source has a Markdown copy for the assistant in `raw/converted/`, same name with `.md`.
- A converter may change only the formatting, never the text. These files stay raw: no summaries, no rewording, no fixes, no removed sections.
- Only add new files. Never overwrite or delete without an explicit request from the user.
- A converted file carries the frontmatter fields `title`, `source_url`, `pdf_url`, `published`, `ingested`, `type: full-text`, `fetch_method`, and `sha256` of the body below the frontmatter. On re-ingest, an unchanged hash means skip; a changed hash means source drift, flag it.
- If a source cannot be converted cleanly, keep the original here and say so on the wiki page (`confidence: low`).
- If the original is behind a paywall, there is no raw file. The wiki page is built from the abstract and gets `confidence: low`.
- If the raw file is a preprint rather than the journal version, the wiki page says so.
