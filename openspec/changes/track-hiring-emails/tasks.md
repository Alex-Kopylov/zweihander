## 1. Shared rules and provider routing

- [x] 1.1 Extract assessment, matching, transitions, redaction, and untrusted-content rules
- [x] 1.2 Add the strict assessment schema and trusted orchestration reference
- [x] 1.3 Reduce Gmail to discovery/metadata/history mapping; remove model and label operations
- [x] 1.4 Route the entrypoint to common orchestration and provider maps
- [x] 1.5 Document authorized scope, count-before-read, both directions, and complete pagination

## 2. Queue, conversations, and recovery

- [x] 2.1 Implement private SQLite metadata checkpoints and expiring claims
- [x] 2.2 Deduplicate before body reads and select one newest trigger per changed conversation
- [x] 2.3 Validate complete snapshots and link threads to exact application matches
- [x] 2.4 Reassess newly linked history before committing status
- [x] 2.5 Retain pending/review routing IDs and implement backlog retrieval/reconsideration
- [x] 2.6 Report safe counts and review age; document local-state permissions and recovery

## 3. Isolated assessment and writes

- [x] 3.1 Use the official Codex Python SDK and isolated Claude launcher with no action tools or model pin
- [x] 3.2 Pass body snapshots through stdin without privileged-parent exposure
- [x] 3.3 Validate results and choose fixed output paths in trusted code
- [x] 3.4 Use PyYAML for comments/quoted status values and precise atomic updates
- [x] 3.5 Recheck matching and lifecycle constraints, synchronize the index, checkpoint last

## 4. Verification

- [x] 4.1 Cover deduplication, complete two-way history, linked threads, and review retries
- [x] 4.2 Cover exact matching, transition constraints, receipt dates, and partial-write retries
- [x] 4.3 Cover redaction, malicious content, and native Codex empty-tool/schema requests
- [x] 4.4 Exercise the streaming bridge and adversarial native tool-call rejection
- [x] 4.5 Finish independent review and resolve actionable findings
- [x] 4.6 Run the full repository tests and required validation

## 5. Documentation and manifests

- [x] 5.1 Update workspace initialization, layout, plugin instructions, and user READMEs
- [x] 5.2 Bump both plugin versions to 0.8.0 and update applicable catalog descriptions
- [x] 5.3 Replace stale cursor/digest, inbound-only, and verbatim-injection-quote requirements
- [x] 5.4 Validate OpenSpec, JSON, shell syntax, and Markdown whitespace
