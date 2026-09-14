---
name: gmail-agent
description: Map one Gmail message trigger to a complete conversation snapshot for the isolated hiring-email reader.
---

# Gmail adapter

This is an operation map for the trusted orchestrator, not the content reader.
Follow [orchestration](../references/hiring-email-orchestration.md).
Business rules belong in [hiring-email-rules.md](../references/hiring-email-rules.md).
Never launch this Markdown agent with inherited tools to classify email.

## Connected operations

Discover installed schemas before use. Require these read operations:

| Operation | Codex Gmail app suffix | Claude Gmail connector |
|---|---|---|
| Paged message-ID search | `gmail_search_email_ids` | Discover search; expand thread results using metadata only |
| Message metadata | `gmail_read_email`, `format: "minimal"` | Require IDs, thread IDs, provider dates, and flags without bodies |
| Full conversation | `gmail_read_email_thread` | Discover full thread retrieval, including sent messages and pagination |

Codex names normally start with `mcp__codex_apps__`. Claude connector names vary;
bind operations by their schemas, never by guessed tool names. Stop and name the
missing operation if metadata-only expansion, full history, or the orchestration
bridge is unavailable. Do not fall back to browser or IMAP.

## Search and metadata

Translate the authorized scope as `after:<lower-bound> -in:spam -in:trash -in:drafts`
AND the operator's filter. Include sent mail. Use a UTC epoch lower bound where
supported; otherwise widen the date filter and enforce the bound on `internal_date`.
Never exclude `from:me` or require an inbox/unread label.

Page `gmail_search_email_ids` with `max_results: 100` and every `next_page_token`.
Deduplicate exact IDs. Request `minimal` for each ID, extract only
`{id, conversation_id: thread_id, internal_date}` (integer milliseconds), and pass
metadata to `plan`. Discard snippets even if metadata includes them. Webhooks use
this same path. Thread-search connectors must expand IDs without bodies before
applying the time bound and calling `plan`.

## One trigger and its history

Each assignment has one `trigger_id` and a fixed `conversation_ids` set. Fetch
only those threads. In Codex call `gmail_read_email_thread` by `thread_id` with
explicit `max_messages`. A full page may be truncated: increase the limit until
fewer messages return, or verify an authoritative total. Never treat the default
20 or a full 100-message response as complete. If the connector caps/truncates
output or cannot prove completeness, leave the assignment retryable.

Normalize in the tool bridge without displaying bodies to the orchestrator:

- Preserve every delivered message, including history before the search date.
  Exclude drafts; classify `SENT` as outgoing, other delivered messages as incoming.
- Keep immutable IDs, thread ID, integer `internal_date`, direction, and headers.
- Use decoded `text/plain` MIME parts; otherwise convert `text/html` to text without
  fetching URLs. Skip attachments and inline images. Missing required text is a
  retrieval failure. Do not delete messages because they quote old replies.
- Produce `{id, complete: true, message_count, messages}` only after checking all
  pages/counts. Each message has `{id, internal_date, direction, body, headers}`.

The host verifies the trigger and sorts the snapshot. `needs_context` supplies
additional linked thread IDs for this same trigger; rerun the isolated reader
with the complete set. No mailbox mutations belong to this adapter.
