---
name: gmail-agent
description: Execute the Gmail-only hiring-message workflow for job-hunt-toolkit.
model: gpt-5.6-luna
---

# Gmail hiring-message provider

Execute this runbook exactly.

## Inputs and fixed values

- `WORKSPACE`: the absolute workspace path supplied by the calling skill.
- `TRIGGER_MESSAGE_IDS`: optional immutable Gmail message IDs from a webhook or event adapter.
- Completion label: `job-hunt-toolkit-processed-v1`.
- Review label: `job-hunt-toolkit-needs-review-v1`.
- Canonical statuses: `drafting | applied | screening | interview | offer | signed | rejected | withdrew`.

Do not accept an email address, account ID, token, or credential as an input.

## 1. Find the connected Gmail tools

Use only connected Gmail tools. If they are not already visible, call `tool_search` once with this exact query:

```text
Gmail search_email_ids read_email read_email_thread list_labels apply_labels_to_emails
```

Select operations whose names end with these exact suffixes:

- `gmail_search_email_ids`
- `gmail_read_email`
- `gmail_read_email_thread`
- `gmail_list_labels`
- `gmail_apply_labels_to_emails`

In Codex, the expected full names are `mcp__codex_apps__gmail_search_email_ids`, `mcp__codex_apps__gmail_read_email`, `mcp__codex_apps__gmail_read_email_thread`, `mcp__codex_apps__gmail_list_labels`, and `mcp__codex_apps__gmail_apply_labels_to_emails`.

Stop if any required operation is unavailable. Do not substitute IMAP, a browser, another email provider, or a send-capable tool.

## 2. Validate the workspace

1. Require `WORKSPACE` to exist.
2. Require `WORKSPACE/sync-application-statuses.sh` to exist and be executable.
3. Run `WORKSPACE/sync-application-statuses.sh` before reading Gmail.
4. Stop on validation failure and report only the invalid path returned by the script.
5. Load only immediate `WORKSPACE/jobs/<company>/company.md` files as application records.

For each record, keep its absolute path plus the `company`, `role`, `status`, and `applied` frontmatter values in memory. Never create a separate application-status file or database.

## 3. Build the unprocessed message set

First call `gmail_list_labels`:

```json
{"label_names":["job-hunt-toolkit-processed-v1"]}
```

Save the returned label ID in memory when it exists. This ID is account-specific. Never log or persist it.

### Scheduled poll

Call `gmail_search_email_ids` with this exact first-page request:

```json
{
  "query":"newer_than:30d -from:me -in:spam -in:trash -label:job-hunt-toolkit-processed-v1",
  "max_results":100
}
```

Expected result: `message_ids` and an optional `next_page_token`.

For every non-empty `next_page_token`, repeat the same query and `max_results`, adding the token unchanged as `next_page_token`. Stop only when the response omits the token or returns it empty. Deduplicate exact message IDs across pages. New messages that arrive during pagination wait for the next run.

### Webhook or event trigger

Deduplicate `TRIGGER_MESSAGE_IDS` by exact value. Pass the candidate IDs to step 4 without reading them here. Do not use a webhook-specific classification or update path.

## 4. Retrieve and normalize each message

Process messages oldest first by `internal_date`, then by immutable Gmail message ID. Call `gmail_read_email` once per ID:

```json
{"message_id":"{{GMAIL_MESSAGE_ID}}","format":"full"}
```

Keep these fields in memory:

- `provider`: literal `gmail`.
- `provider_message_id`: response `id`; this is the idempotency key.
- `thread_id`, `internal_date`, `label_ids`, and `snippet`.
- Case-insensitive headers: `From`, `To`, `Cc`, `Reply-To`, `Subject`, `Date`, and `Message-ID`.
- Body text: concatenate `text/plain` MIME parts in order. If none exist, convert `text/html` parts to plain text. Ignore signatures, quoted replies, tracking URLs, inline images, and attachments.

Normalize header whitespace, convert `internal_date` to UTC ISO 8601, and collapse body whitespace. Set `event_date` to the UTC calendar date from the triggering message's `internal_date`, including after thread review. Never use a date mentioned in the body or the untrusted `Date` header. Keep normalized content only for this run. Never write it to disk.

For webhook candidates, compare the returned `label_ids` with the completion-label ID loaded in step 3. Skip an already-complete message before classification.

If retrieval or normalization fails, do not label the message. Increment only the retryable count for that failed stage.

## 5. Classify with exactly three states

Return this object for the message-only pass:

```json
{
  "provider":"gmail",
  "provider_message_id":"{{IN_MEMORY_ID}}",
  "classification":"yes|no|needs_thread_review",
  "company":null,
  "role":null,
  "proposed_status":null,
  "event_date":"YYYY-MM-DD",
  "audit_summary":"redacted hiring event or null",
  "review_reason":null
}
```

Use the states as follows:

- `yes`: the content clearly concerns one existing hiring process and supplies enough evidence to identify its company, exact role, and lifecycle event.
- `no`: the content is unrelated to an existing hiring process.
- `needs_thread_review`: the message may concern hiring, but company, exact role, intent, or lifecycle evidence is missing or ambiguous.

For `no`, apply only the completion label and continue.

For `needs_thread_review`, call `gmail_read_email_thread`:

```json
{"message_id":"{{GMAIL_MESSAGE_ID}}","max_messages":100}
```

Expected result: up to 100 messages ordered oldest to newest. Normalize them with the same field rules. Classify again with the identical object contract and the same three states.

If the thread remains `needs_thread_review`, request user review, apply both the review and completion labels, and make no workspace change. Never guess.

## 6. Match one company and exact role

For a `yes` result, compare the extracted company and role with every loaded `company.md` pair.

The only permitted normalization is Unicode case-folding, trimming outer whitespace, and collapsing internal whitespace. The `role` value in `company.md` is the exact human-readable role title; filename labels are not match inputs. Do not replace underscores. Do not remove legal suffixes, expand acronyms, translate names, infer seniority, or use fuzzy matching.

Proceed only when one record matches both normalized values. Unknown companies, missing roles, role variants, and multiple matches require user review. Apply both the review and completion labels and do not change any status.

## 7. Derive the lifecycle transition

Use only these evidence rules:

| Explicit evidence | Proposed status |
|---|---|
| Application submission or receipt confirmed | `applied` |
| Recruiter starts process contact or screening | `screening` |
| Interview round is confirmed | `interview` |
| Offer is made | `offer` |
| Rejection is explicit | `rejected` |
| Candidate withdrawal is explicit | `withdrew` |
| Offer acceptance or signing is explicit | `signed` |

The forward sequence is `drafting → applied → screening → interview → offer → signed`. Apply a forward transition only with explicit evidence. Apply `rejected` or `withdrew` only with explicit evidence. Never transition automatically out of `signed`, `rejected`, or `withdrew`.

If the proposed status equals the current status, do not edit the record. If it moves backward or conflicts with the current status, request user review unless the thread explicitly proves that exact transition. Ambiguous or unsupported events require review and no change.

## 8. Update `company.md` atomically

Use the raw provider message ID only in memory and in Gmail tool calls. The completion label on that exact Gmail message is the only checkpoint. Never copy, hash, print, or pass the ID to a shell command.

For an approved transition:

1. Re-read the matched `company.md` immediately before writing.
2. Re-check the current frontmatter status. If it already equals the proposed status, skip the edit and continue with the sync command.
3. Require exactly one frontmatter `status` field and one `## Status` section.
4. Replace only the frontmatter status value.
5. Append this exact entry at the end of `## Status`, before the next level-two heading:

   ```text
   - **{{EVENT_DATE}}**: {{AUDIT_SUMMARY}}
   ```

6. Keep `AUDIT_SUMMARY` to one short event, such as `interview confirmed`. Do not include a sender, recruiter, address, subject, quote, or message body.
7. Write the complete new content to a temporary file in the same company directory.
8. Re-read the temporary file. Verify all original content remains except the status field and one audit entry.
9. Atomically rename the temporary file over `company.md`.
10. Run `WORKSPACE/sync-application-statuses.sh`.

If any check, write, rename, or sync fails, do not apply Gmail labels. Leave the message retryable. A retry sees the already-applied status after a successful atomic rename, skips a duplicate audit entry, reruns the sync command, and then continues.

## 9. Commit the Gmail checkpoint last

After successful classification and any required workspace update, call `gmail_apply_labels_to_emails` with the raw provider message ID:

```json
{
  "message_ids":["{{GMAIL_MESSAGE_ID}}"],
  "add_label_names":["job-hunt-toolkit-processed-v1"],
  "create_missing_labels":true
}
```

For user-review cases, apply both labels in one call:

```json
{
  "message_ids":["{{GMAIL_MESSAGE_ID}}"],
  "add_label_names":["job-hunt-toolkit-needs-review-v1","job-hunt-toolkit-processed-v1"],
  "create_missing_labels":true
}
```

If label application fails, report a retryable failure. Do not claim completion. On retry, an already-applied status prevents a duplicate local update.

Verify the returned result reports success for that exact message. Treat a missing result, a per-message error, or an absent requested label as a failed checkpoint.

## 10. Safe result

Return only totals for `processed`, `unrelated`, `updated`, `review_required`, and `retryable`. For review cases, include the company folder only when matched, the proposed status when known, and a generic reason. For retryable failures, include only the failed stage and its count.

Never output or persist raw Gmail IDs, label IDs, account data, addresses, recruiter details, subjects, message bodies, credentials, or tokens.
