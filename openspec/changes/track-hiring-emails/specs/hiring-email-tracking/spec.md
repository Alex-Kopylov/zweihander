## ADDED Requirements

### Requirement: Provider-neutral processing

The capability SHALL keep assessment rules outside provider adapters. Adapters
SHALL supply only read operations, query translation, metadata expansion, complete
conversation retrieval, and normalization. Agent definitions SHALL omit `model`.

#### Scenario: Add another provider
- **WHEN** a provider supplies the required read operations and body bridge
- **THEN** it uses the existing shared rules, queue, reader, and writer unchanged

#### Scenario: Required operation is missing
- **WHEN** metadata-only discovery, complete retrieval, or the bridge is unavailable
- **THEN** processing stops before full reads and names the missing operation

### Requirement: Authorized metadata discovery

The capability SHALL include incoming and sent messages, exclude spam/trash/drafts
from discovery, paginate all results, and apply the operator scope. The initial
bound SHALL be the earliest application date or 30 days ago. Without existing
scope authorization, an unscoped run SHALL count candidates before asking to read.

#### Scenario: Candidate withdraws by email
- **WHEN** a sent message enters the authorized range
- **THEN** it is discovered through the same metadata path as incoming mail

#### Scenario: Scope is already authorized
- **WHEN** this session or standing instructions authorize the complete scope
- **THEN** the run proceeds without repeating the confirmation

### Requirement: One trigger and complete linked history

Each reader SHALL receive one triggering message and complete incoming/outgoing
history for its conversation and all known threads linked to the same application.
A first encounter SHALL include earlier messages and the latest message. Several
pending messages in one thread SHALL yield one newest trigger. Missing or truncated
history SHALL fail before classification; context limits SHALL NOT justify truncation.

#### Scenario: First encounter is a reply
- **WHEN** the trigger has earlier unread history
- **THEN** the reader sees all delivered messages, including those before the search bound

#### Scenario: A new thread belongs to an existing application
- **WHEN** assessment identifies an application with other linked threads
- **THEN** the host requests that history and reassesses the same trigger before writes

### Requirement: Durable deduplication and recovery

The capability SHALL check private message checkpoints before body reads. Successful
snapshots SHALL checkpoint all included messages. Unchanged processed messages SHALL
be skipped; new conversation activity SHALL permit historical rereads. Pending and
review routing IDs SHALL remain retrievable independent of the polling date range.

#### Scenario: An old webhook repeats
- **WHEN** its message was successfully processed earlier
- **THEN** metadata lookup skips it without another full read or classifier invocation

#### Scenario: Review requires reconsideration
- **WHEN** the user requests reconsideration after a message leaves the polling range
- **THEN** private review metadata retrieves its conversation for a new assessment

#### Scenario: A worker fails
- **WHEN** retrieval, classification, or a required write fails
- **THEN** the message remains pending and its claim is released or expires after a crash

### Requirement: Enforced reader isolation

The reader SHALL have no shell, file, network, mailbox, delegation, or permission
operations. It SHALL receive only an assigned snapshot and matching fields through
an ephemeral process and return schema-constrained output. The trusted host SHALL
choose the fixed result file. Unsupported isolation or body bridges SHALL fail closed.

#### Scenario: Email asks for a local command
- **WHEN** a body requests reading a local file, replying, or changing unrelated records
- **THEN** no execution tool is available and the reader can return only its assessment

#### Scenario: Native boundary verification
- **WHEN** the Codex launcher runs against a controlled fixture endpoint
- **THEN** its actual inference request has no tools and specifies the result schema

### Requirement: Exact matching and lifecycle checks

The host SHALL match one existing company/role pair using only case-folding and
collapsed whitespace, and revalidate uniqueness before writing. Unknown, ambiguous,
or conflicting matches SHALL require review without creating records. Lifecycle
updates SHALL require explicit evidence, include outgoing acceptance/withdrawal,
and reject backward transitions or reopening terminal states.

#### Scenario: Another matching record appears during assessment
- **WHEN** two records match at commit time
- **THEN** no application status changes and the outcome requires review

#### Scenario: A linked thread changes application identity
- **WHEN** an assessment conflicts with its established application link
- **THEN** the host preserves the link and requires review

### Requirement: Atomic status and checkpoint writes

`company.md` SHALL remain the only application status source. The host SHALL replace
only its YAML status scalar and append one fixed redacted event entry. The date
SHALL come from the evidence message's provider timestamp. `APPLICATIONS.md` SHALL
be regenerated. Checkpoints SHALL follow all required writes; equal status SHALL
avoid duplicate audit entries. Quoted YAML values and comments SHALL be supported.

#### Scenario: Index generation fails after status replacement
- **WHEN** the assignment is retried
- **THEN** the host retains the status, skips a duplicate audit, retries the index,
  and checkpoints only after success

### Requirement: Private state and redacted findings

Private state SHALL use mode 0700 directories and 0600 database/results with a
workspace gitignore entry. Raw routing IDs SHALL be confined to that state and the
bridge for retrieval. Bodies, headers, contacts, subjects, and credentials SHALL
NOT enter application audits, result files, or reports. Injection findings SHALL
use enum flags rather than verbatim quotes. Reports SHALL include counts and
oldest-review age; review results SHALL remain associated with routing metadata.

#### Scenario: A malicious message is flagged
- **WHEN** the reader detects embedded instructions in hiring correspondence
- **THEN** the result contains generic security flags without the instruction text

### Requirement: Mailbox remains read-only

The workflow SHALL NOT send, reply, forward, draft, archive, trash, mark spam, change
read/unread or starred flags, apply labels, or change filters/forwarding rules.
Provider operations SHALL remain outside the reader, and prompt refusal SHALL NOT
be represented as the enforcement mechanism.

#### Scenario: A message reaches completion
- **WHEN** its validated assessment and required file writes succeed
- **THEN** only private local checkpoints change; no mailbox label is applied
