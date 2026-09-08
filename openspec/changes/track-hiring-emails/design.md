## Context

See proposal.md — Why. Two constraints shape everything below.

The capability's entire input is text written by third parties, and the runtimes it
executes in put mail-mutating operations in the same context as that text. Nothing in
a prompt can prevent a model from calling a tool that exists; the design's job is to
remove the need for those tools and to make their absence checkable.

Provider connectors differ more than a rename. The Codex Gmail app exposes
message-level search and message-level labelling. The Claude Gmail connector exposes
thread-level search, message retrieval, and a read-write label API that also carries
send, trash, and spam. A contract written against one connector's operation names
does not survive contact with the other.

Current state: `agents/gmail-agent.md` holds the entire runbook — connector names,
classification, matching, transitions, redaction, checkpointing. `SKILL.md` routes to
it. `sync-application-statuses.sh` validates records and regenerates the index and is
unaffected by this design.

## Goals / Non-Goals

**Goals:**

- One set of behavioural rules, loaded by every provider, with the adapter reduced to
  what genuinely differs between connectors.
- A run that needs no mailbox write grant, so the blast radius of a successful prompt
  injection is bounded by the grant rather than by the model's compliance.
- Progress tracking that survives a provider with no per-message labels.

**Non-Goals:**

- Triaging, filing, or replying to mail. The capability reads and reports.
- Detecting hiring mail the user has not already applied to. Matching is against
  existing records only; discovery is out of scope.
- Multi-machine synchronisation of processing state. Two checkouts may each process
  the same message; updates are idempotent, so the cost is duplicated work, not a
  corrupt record.

## Decisions

### Cursor plus unresolved set, replacing the mailbox label

The completion checkpoint moves into the workspace as a cursor file holding one
provider timestamp and a set of digests for messages awaiting user review.

Alternatives considered:

- **Keep the mailbox label.** Rejected. It is the single reason the capability needs
  a write grant, and with `gmail.modify` that grant also carries trash and spam.
  It is also the least portable piece of the contract — the checkpoint is per-message,
  and a thread-only connector cannot express it.
- **Store raw provider message IDs locally.** Rejected. It contradicts the redaction
  requirement, and the ID set is a durable map of who has mailed the user about work.
- **Timestamp cursor alone, no unresolved set.** Rejected. A message routed to review
  would be passed over by the advancing cursor and silently never revisited. The
  review case is precisely the one a human still needs.

Digests are `SHA-256(salt || provider_id)` with a random per-workspace salt generated
on first run and stored beside the cursor. The digest is what "cannot be recovered"
means in the spec: an attacker holding the workspace cannot enumerate the ID space
without the salt. The salt is not a secret to be protected in transit — it exists to
break offline correlation between a leaked workspace and a mailbox.

### Cursor advance uses an overlap window

The cursor stores the newest resolved message's timestamp; the next query asks for
messages at or after `cursor − overlap`, with a default overlap of one hour, and
discards anything whose digest is already resolved.

Provider search granularity is coarse — Gmail's date operators are day-resolution and
its internal timestamps are second-resolution — and messages arriving in the same
second as the cursor would otherwise be skipped. The overlap costs a small amount of
repeated retrieval and eliminates a silent-loss class of bug. Rework is bounded
because resolved digests are cheap to check before any content is fetched.

The resolved-digest set is pruned to entries newer than `cursor − overlap`; only the
unresolved set is retained indefinitely.

### Adapter boundary

An adapter supplies exactly three operations, and the query language is expressed in
capability-neutral terms — a time lower bound, an exclusion of self-sent mail, an
exclusion of spam and trash, and an optional operator scope — which the adapter
translates.

A thread-only connector satisfies message search by expanding each matching thread
into its messages and filtering by the time bound in the adapter. That expansion is
the adapter's problem precisely because it is what differs between connectors; making
it the adapter's problem is what lets the rules stay identical.

Placement: rules move from `agents/gmail-agent.md` to a reference document loaded by
`SKILL.md`. The agent file keeps operation mapping, query translation, and pagination.
The `model:` pin is removed — it is a Codex model id, and it makes the agent
unloadable elsewhere.

### Scope and confirmation for live runs

Runs accept an operator scope that is ANDed into the query. Without a scope, the
capability counts matches first and asks before retrieving any content.

This exists because the realistic test and first-use environment is a mailbox that
also holds real correspondence. An unscoped first run against a 244-message inbox
reads 244 real bodies into a model context to discover that three of them are
relevant. Counting first is cheap and makes the breadth of a run visible before it
happens rather than after.

### Refusal is documented as insufficient

The spec requires refusing mutating operations, and the documentation states plainly
that this is a prompt-level control rather than a boundary, with harness deny rules
and a read-only grant given as the actual controls. Stating the limitation is part of
the deliverable; a reader who believes the refusal is enforcement will under-configure
the grant.

## Risks / Trade-offs

- **A model calls a mutating tool despite the rules.** → The rules are the weakest of
  three layers. A read-only grant makes the call fail at the provider; harness deny
  rules make it fail before it leaves the runtime. Both are documented as required for
  live use, not optional hardening.
- **Injection succeeds at the classification layer** — a message argues its way into a
  status change it should not get. → Bounded by the evidence rules and exact matching:
  the worst case is one wrong status on one matched record, recorded with an audit
  entry, in a version-controlled file where `git diff` shows it. Terminal statuses
  cannot be reopened without review.
- **Unresolved set grows without bound** when the user never acts on review cases. →
  Reported as a count every run; entries carry the timestamp of first review so the
  backlog is visible and ageable.
- **Cursor lost or workspace re-cloned** → the cursor is machine state and is
  gitignored, so a fresh clone reprocesses the window. Updates are idempotent and the
  mailbox is read-only, so reprocessing is safe; the cost is retrieval.
- **Overlap window is too small for a badly skewed provider clock.** → Configurable;
  the failure mode is a skipped message, which the unresolved set does not catch
  because the message was never seen. Documented as the one case requiring a manual
  cursor rewind.
- **Two machines process the same mailbox** → duplicate work, no corruption, because
  a transition whose proposed status equals the current status is a no-op.

## Migration Plan

The label-based implementation from PR #94 has not been released to users, so there is
no state to migrate in the field.

1. Land the rules reference, the neutral contract in `SKILL.md`, and the reduced Gmail
   adapter together — the intermediate state where rules exist in two places is worth
   avoiding.
2. Initialise the cursor on first run to the earliest `applied` date across existing
   records, falling back to 30 days ago when no record carries one. This makes the
   first run cover the applications the user actually has.
3. For anyone who ran the label version, the two `job-hunt-toolkit-*` labels become
   inert. Removal is manual and optional; the capability never reads them again.
4. Rollback is reverting the plugin version. No workspace data is destroyed by either
   direction — the cursor file is additive and ignored by the old implementation.

## Open Questions

- Whether the unresolved set should expire entries after a long interval, or grow
  until the user acts. Deferrable: it changes a default, not the contract, and the
  run report makes the backlog visible either way.
