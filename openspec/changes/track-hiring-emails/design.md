## Context

A message may contain arbitrary instructions. Giving its reader the parent's mail
connector and shell tools violates the requested boundary. The original Gmail
runbook also batches triggers and reads history only when the newest message is
ambiguous. The implementation separates provider access, assessment, and writes.

## Goals / Non-Goals

Goals: one trigger per reader, complete two-way history, durable deduplication,
shared business rules, enforced tool isolation, exact application updates.
Non-goals: sending/triaging mail, attachment analysis, new application discovery,
provider credential management, or multi-machine synchronization.

## Decisions

### Private message ledger, not cursor/digests

SQLite stores connection/scope, message/thread routing IDs, provider timestamps,
outcomes, review-result tickets, application links, and expiring claims. It does
not store email content or application status. Directory mode is 0700; database
and redacted result files use 0600; initialization adds a gitignore entry.

A digest cannot retrieve an unresolved message. A pruned overlap set cannot reject
an old webhook before body retrieval. Retaining routing IDs solves both, with an
explicit privacy exception limited to private local state. Poll metadata from the
earliest applied date (30-day fallback); merge saved pending IDs independently of
that range. `review-items` retrieves the durable backlog and `--reconsider` retries
it explicitly. No review silently disappears behind an advancing cursor.

### One trigger with complete history

Metadata is deduplicated before body retrieval. Group pending messages by thread;
lease the newest trigger per changed thread for 15 minutes. Process jobs oldest
first. The initial reader gets all messages in its thread, even before the search
bound, including sent replies. After a successful assessment, checkpoint every
message in the snapshot. Unchanged standalone messages never need another reader.

Threads link to an exact existing company/role match. A new thread that identifies
an application with earlier linked threads returns `needs_context`; reassess the
same trigger with all those threads before writing. Known threads always include
that linked set. Missing/truncated history fails before classification. An
application-link conflict requires review, never silent reassignment.

### Provider maps and a body bridge

Gmail instructions only map search, metadata, pagination, full-thread retrieval,
and normalization. They contain no model selection or business policy. A new
provider supplies those read operations and reuses the queue, reader, and writer.
Thread-only search is supported only with metadata-only expansion before dedup.

Provider results stay in a programmatic bridge. The host starts a stdin reader;
the bridge fetches assigned threads and passes one JSON snapshot without returning
bodies to the privileged controlling model. Codex can compose connected tools
and `write_stdin` in one tool execution. A bridge that cannot withhold content
must stop before full reads. Claude's reader supports its CLI, but connectors that
expose bodies directly to a parent require an equivalent bridge.

The interactive PTY bridge disables echo and canonical buffering, waits for a
readiness message, and writes one JSON line. Message data never enters shell text,
process arguments, temporary body files, or user-visible output.

### Native isolation and fixed output

The Codex launcher uses `openai-codex==0.154.0` and its bundled runtime: no environments
on thread/turn, no dynamic tools/MCP, optional tools disabled, no approvals,
ephemeral execution, and output schema. The SDK owns transport and process
lifecycle. Its low-level client accepts explicit environment/tool lists absent
from the high-level facade. The native test inspects an actual bundled-runtime
request against a local fake API endpoint, including in CI.

The Claude launcher uses safe mode, an empty built-in tool set, strict empty MCP,
disabled skills/Chrome, noninteractive permissions, no session persistence, and a
JSON schema. Unsupported flags fail. Managed policy configuration remains an
operator prerequisite. Both launchers inherit runtime model selection, with no
`model` field or CLI model argument.

The reader receives local message handles and company/role/status fields. It
returns evidence and enum values, not commands or paths. The host validates the
result and chooses `.hiring-email/results/<ticket>.json`. Only trusted code writes
the matched `company.md`, generated index, and private processing state.

### Status writes and recovery

PyYAML validates records including quoted values/comments. Matching normalizes
only case and whitespace. Recheck unique company/role matching immediately before
writing under a SQLite transaction. Reject aliases/anchors and block status
scalars whose source spans cannot be safely replaced in place.

Replace one status scalar and append a fixed event phrase under `## Status`.
Use the evidence message's provider date, not body or Date-header text. Equal
status is a no-op; terminal reopening and backward movement require review. Rename
atomically, regenerate the index, save the result, then checkpoint. On failure,
keep pending IDs and release the claim. A retry after partial writes avoids a
duplicate audit entry. A crashed claim expires.

## Risks / Trade-offs

- Semantic injection can still cause a wrong classification. Native controls
  remove execution capabilities; exact matching and fixed writes bound the effect
  to one existing application. The tests do not claim perfect model accuracy.
- Retained routing IDs and review entries grow with mailbox history. They are
  necessary for retrieval/dedup; counts and oldest-review age make backlog visible.
- Full thread history costs context. Never silently truncate; return retryable
  when connector/runtime limits prevent complete assessment.
- A fresh clone rereads the authorized range. Equal-status transitions remain
  idempotent. Cross-machine state sharing is unsupported.
- Codex SDK/runtime dependency updates require native isolation revalidation. Claude connectors still require a programmatic body bridge.

## Migration Plan

Publish the rules, queue, reader, and provider adapter together. Copy both workspace
status scripts on initialization/upgrade. Initialize private state on first run;
existing Gmail labels are ignored and never changed. Update both plugin manifests,
user documentation, and validation tests in the same change.
