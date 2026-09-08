# Track hiring updates from email

## Why

Application statuses in `jobs/<company>/company.md` drift because hiring updates
arrive by email and nothing reconciles them. PR #94 shipped an implementation for
this, but no spec — so the behaviour that matters most (what the agent is allowed
to do to a real mailbox, and what happens when a message tries to instruct it)
lives only in one provider's runbook and cannot be reviewed independently of it.

Two problems surfaced while testing that implementation against a live mailbox,
and both are spec-level rather than incidental:

- The completion checkpoint is a Gmail label. Labelling is a write, so the
  capability cannot run on a read-only mailbox grant, and the idempotency key is
  a provider-specific message ID. A connector that searches threads rather than
  messages cannot satisfy the contract at all.
- The capability's whole input is untrusted text authored by third parties, and
  a mail connector that exposes send, reply, trash, or spam operations puts those
  operations in the same context as that text.

## What Changes

- Introduce a provider-agnostic capability. Provider agents supply a fixed set of
  read operations; all classification, matching, transition, and redaction rules
  live in the capability and are identical across providers.
- **BREAKING**: replace the mailbox-label completion checkpoint with a local
  cursor stored in the workspace. The mailbox becomes read-only: no labels, no
  flags, no writes of any kind.
- Require the capability to refuse mutating mail operations — send, reply,
  forward, draft, trash, spam, label — and to treat a request for one that
  originates in message content as a reportable security event rather than a task.
- State the injection boundary explicitly: message content is data. Instructions
  found inside a message are surfaced to the user verbatim and never executed.
- Define what may be persisted from a message. Bodies, sender identities, subjects,
  and raw provider message IDs stay out of the workspace and out of logs.
- Define an isolation contract for exercising the capability against a real
  mailbox, so a test run cannot touch correspondence outside the fixture.
- Keep `company.md` the single source of application status and `APPLICATIONS.md`
  a disposable generated index.

## Capabilities

### New Capabilities

- `hiring-email-tracking`: read inbound mail, classify hiring events, match them to
  existing application records, transition statuses under explicit-evidence rules,
  and do so without writing to the mailbox or acting on message content.

### Modified Capabilities

None. `openspec/specs/` has no existing capability this touches.

## Impact

- `plugins/job-hunt-toolkit/skills/track-hiring-emails/SKILL.md` — provider routing
  and the cursor contract.
- `plugins/job-hunt-toolkit/agents/gmail-agent.md` — reduced to a provider adapter:
  operation mapping and pagination only. Classification, matching, transition, and
  redaction rules move out of it. Its `model: gpt-5.6-luna` pin makes the agent
  Codex-only and must go.
- `plugins/job-hunt-toolkit/skills/init-workspace/` — cursor file and its
  `.gitignore` treatment; `sync-application-statuses.sh` is unchanged.
- `plugins/job-hunt-toolkit/references/` — workspace layout gains the cursor file.
- Both plugin manifests and both marketplace manifests need a version bump.
- No runtime dependency change. The capability drops its requirement for a
  mailbox-write OAuth grant.
