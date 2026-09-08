## 1. Extract provider-neutral rules

- [ ] 1.1 Create `plugins/job-hunt-toolkit/references/hiring-email-rules.md` holding classification, matching, transition, record-update, and redaction rules, moved verbatim-in-meaning from `agents/gmail-agent.md`
- [ ] 1.2 Add the untrusted-content section to that reference: message content is data, embedded instructions are quoted to the user and never executed, claimed authorization inside content is disregarded
- [ ] 1.3 Add the forbidden-operations list (send, reply, forward, draft, trash, archive, spam, read/unread, star, label, filter, forwarding rule) and state that prompt-level refusal is not an enforcement boundary
- [ ] 1.4 Define the capability-neutral query contract in the same reference: time lower bound, exclude self-sent, exclude spam and trash, optional operator scope
- [ ] 1.5 Update `skills/track-hiring-emails/SKILL.md` to load the rules reference and route to an adapter, keeping no behavioural rules of its own

## 2. Cursor and unresolved set

- [ ] 2.1 Define the cursor file format and location in `references/workspace-layout.md`: provider timestamp, per-workspace salt, unresolved digests with first-review timestamps, resolved digests within the overlap window
- [ ] 2.2 Specify digest derivation as `SHA-256(salt || provider_id)` and forbid persisting the raw identifier anywhere
- [ ] 2.3 Specify cursor advance: advance only past messages that reached a terminal outcome, query from `cursor − overlap` with a one-hour default, prune resolved digests older than the window
- [ ] 2.4 Specify first-run initialisation to the earliest `applied` date across records, falling back to 30 days ago
- [ ] 2.5 Add the cursor file to the workspace `.gitignore` written by `init-workspace`, and document that a re-clone reprocesses the window safely
- [ ] 2.6 Add the unresolved-backlog count and age to the run report contract

## 3. Reduce the Gmail agent to an adapter

- [ ] 3.1 Remove the `model: gpt-5.6-luna` frontmatter pin from `agents/gmail-agent.md`
- [ ] 3.2 Strip classification, matching, transition, and redaction rules from the agent, replacing them with a pointer to the rules reference
- [ ] 3.3 Replace the hardcoded Codex tool suffixes with an operation-mapping table covering both the Codex Gmail app and the Claude Gmail connector
- [ ] 3.4 Implement thread-to-message expansion in the adapter for connectors whose search returns threads, filtering expanded messages by the time bound
- [ ] 3.5 Remove every label call and the `create_missing_labels` behaviour from the adapter
- [ ] 3.6 State in the adapter that it stops and reports which operation is missing when the connector cannot supply search, message retrieval, and conversation retrieval

## 4. Scoped and confirmed runs

- [ ] 4.1 Add the operator scope parameter to `SKILL.md` and have the adapter AND it into the provider query
- [ ] 4.2 Implement count-before-read for unscoped runs: report the match count and require confirmation before retrieving any message content

## 5. Operator documentation

- [ ] 5.1 Document the required read-only provider grant and name the operations a `gmail.modify`-style grant would additionally expose
- [ ] 5.2 Document harness-level deny rules as the enforcement layer, with a concrete Claude Code `permissions.deny` example listing the mutating tool names
- [ ] 5.3 Update `plugins/job-hunt-toolkit/README.md` and `AGENTS.md` for the read-only model and the cursor, removing references to the processed and needs-review labels

## 6. Tests

- [ ] 6.1 Extend `tests/test_job_hunt_email_tracking.py` with cursor advance cases: resolved-only advance, review case retained across advance, failure leaves cursor unmoved, reprocess applies no duplicate audit entry
- [ ] 6.2 Add matching cases: abbreviated role does not match, unknown company creates nothing, multiple matches route to review
- [ ] 6.3 Add transition cases: terminal status not reopened, backward transition routed to review, body-supplied date ignored in favour of receipt timestamp
- [ ] 6.4 Add redaction cases asserting no sender, subject, body, or raw provider identifier reaches a workspace file or the run report
- [ ] 6.5 Add an injection fixture whose body instructs a mass status change, a mail reply, and a local file read, asserting none of the three occurs and the text is reported as a finding
- [ ] 6.6 Run `uv run pytest tests -q` and record the result

## 7. Manifests and release

- [ ] 7.1 Bump `plugins/job-hunt-toolkit/.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` via the `version-bumper` skill
- [ ] 7.2 Update both marketplace manifests and the root `README.md` for the changed capability description
- [ ] 7.3 Run `jq empty` over both marketplace files and every `plugin.json`, and `git diff --check`
- [ ] 7.4 Run `openspec validate --strict track-hiring-emails`
