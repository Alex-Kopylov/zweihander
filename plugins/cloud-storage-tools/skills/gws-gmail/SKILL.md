---
name: gws-gmail
description: |
  Use this skill for Gmail operations via the Google Workspace (`gws`) CLI: searching messages, reading headers, downloading attachments, and sending email. Useful for invoice/attachment workflows, mailbox triage, and emailing results.
compatibility: |
  - Google Workspace CLI must be installed and accessible via `gws` commands
  - `jq` must be installed for parsing JSON output
  - `gws` must be authenticated for the target Google account (use `"userId": "me"`)
---

# GWS Gmail Skill

Use the `gws` CLI (Google Workspace CLI) for all Gmail operations.
Do not write Python or any scripts — use only gws, jq, and standard unix tools.

## Rules

- Always use `2>/dev/null` to suppress stderr noise.
- Parse JSON output with `jq`.
- Always use `"userId": "me"` for the authenticated account.

## Typical Workflow

1. **Search** — find messages matching a query
2. **Get** — read each message for headers and attachment info
3. **Download** — save attachments to local files (two-step: extract data, then decode)
4. **Process** — organize files, upload to MEGA, etc.
5. **Send** — email results

## Search Messages

```bash
gws gmail users messages list --params '{"userId": "me", "q": "SEARCH_QUERY", "maxResults": 50}' 2>/dev/null
```

Search operators for `q` — combine them in a single string:
- `subject:invoice` — by subject keyword
- `has:attachment` — only emails with attachments
- `newer_than:3m` — last 3 months (`1d`, `2w`, `6m`, `1y`)
- `from:sender@example.com` — by sender
- `filename:pdf` — by attachment type

Example: `"subject:invoice has:attachment newer_than:3m"`

Use `subject:` to narrow results to relevant emails before processing.

Deduplicate results by `threadId` (Gmail can return duplicates):

```bash
gws gmail users messages list --params '{"userId": "me", "q": "subject:invoice has:attachment newer_than:3m", "maxResults": 50}' 2>/dev/null \
  | jq -r '[.messages[] | {id, threadId}] | unique_by(.threadId) | .[].id'
```

## Get Message

```bash
gws gmail users messages get --params '{"userId": "me", "id": "MESSAGE_ID", "format": "full"}' 2>/dev/null
```

Extract subject:

```bash
gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "full"}' 2>/dev/null \
  | jq -r '.payload.headers[] | select(.name == "Subject") | .value'
```

Extract attachment info (ID and filename):

```bash
gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "full"}' 2>/dev/null \
  | jq -r '.payload.parts[] | select(.filename != "") | "\(.body.attachmentId)\t\(.filename)"'
```

If `payload.parts` is null, the message has no attachments — skip it.

## Download Attachment (Two Steps)

Gmail returns attachment data in base64url encoding. Decode it in two separate steps to avoid quoting issues:

**Step 1 — Save raw data to a file:**

```bash
gws gmail users messages attachments get \
  --params '{"userId": "me", "messageId": "MSG_ID", "id": "ATTACH_ID"}' \
  2>/dev/null | jq -r '.data' > attachment.b64
```

**Step 2 — Decode to PDF:**

base64url uses `-` and `_`. Standard base64 uses `+` and `/`.
To decode, convert FROM `-_` TO `+/`:

```bash
tr -- '-_' '+/' < attachment.b64 | base64 -d > output.pdf
rm attachment.b64
```

Do NOT reverse the tr arguments. The order is: `-_` first, `+/` second.
Always save `attachment.b64` in the current directory — not inside destination folders. Clean it up with `rm` after decoding.

## Send Email

To send, you encode in the OPPOSITE direction — standard base64 to base64url:

```bash
RAW=$(cat << 'MAIL' | base64 -w 0 | tr '+/' '-_' | tr -d '='
From: sender@gmail.com
To: recipient@example.com
Subject: Your Subject
Content-Type: text/plain; charset=utf-8

Email body here.
Multiple lines supported.
MAIL
)
gws gmail users messages send --params '{"userId": "me"}' --json "{\"raw\": \"$RAW\"}" 2>/dev/null
```

Returns `{"id": "...", "threadId": "..."}` on success.
