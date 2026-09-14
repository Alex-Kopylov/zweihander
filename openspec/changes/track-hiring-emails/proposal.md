# Track hiring updates from email

## Why

Hiring updates arrive across incoming and outgoing messages, but application
records drift. The initial PR #94 runbook puts business rules, Gmail operations,
and writes in one broadly privileged agent. It rereads completed messages, can
miss old thread history and sent replies, and cannot enforce a content boundary.

## What Changes

- Extract one provider-neutral assessment reference and a slim provider map.
- Process one new message trigger with complete incoming/outgoing history and all
  known threads linked to the same application.
- **BREAKING**: replace Gmail labels with a private SQLite message ledger. Deduplicate
  metadata before body reads; retain pending/review routing IDs for recovery.
- Launch the content reader with native tool isolation and schema output. A trusted
  host validates the result and writes fixed destinations; no console, file, or
  mail tools are available to the reader. Remove the agent's `model` field.
- Preserve exact matching, explicit lifecycle evidence, redacted audits, and
  `company.md` as the sole status source. Parse YAML using PyYAML so quoted scalar
  values and comments work correctly.
- Keep body data inside the connector bridge and reader process, with no quotes
  or message content in shared artifacts or results.

## Capabilities

### New Capabilities

- `hiring-email-tracking`: isolated assessment of complete hiring conversations,
  provider-neutral scheduling and checkpoints, and validated application updates.

### Modified Capabilities

None.

## Impact

- Tracking skill, Gmail adapter, shared rules/schema/orchestration reference.
- Trusted Python queue/writer, official Codex Python SDK, and isolated Claude launcher.
- Workspace status wrapper plus YAML implementation, initialization, and layout.
- PyYAML and Codex SDK dependencies, behavioral and native isolation tests.
- Both plugin versions become 0.8.0; plugin/catalog descriptions and READMEs change.
  Codex marketplace membership/category stay unchanged; it has no plugin version
  or description field to update.
- Existing Gmail labels become unused. No compatibility migration is required;
  private checkpoints are initialized from the authorized range.
