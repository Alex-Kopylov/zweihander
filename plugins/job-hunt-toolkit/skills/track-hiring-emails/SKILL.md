---
name: track-hiring-emails
description: Use when the user asks to check email for hiring updates, process recruiting email, update application statuses from email, poll for hiring messages, or handle an email webhook.
---

# Track hiring emails

Update existing applications from incoming and outgoing hiring correspondence.
Keep each `jobs/<company>/company.md` as the only source of application status.

## Inputs

- Workspace: `JOB_HUNT_WORKSPACE`, otherwise `~/Documents/job_seeking`.
- Connected provider and a stable local connection/scope key, without credentials.
- Authorized search filter, scheduled poll, or webhook message IDs.

## Execution

1. Read [orchestration](../../references/hiring-email-orchestration.md) for the
   trusted queue, data bridge, isolated launcher, and checkpoint protocol.
2. Select the installed provider's operation map. Currently available:
   [Gmail](../../agents/gmail-agent.md). Stop if no adapter supports the connection.
3. Validate the workspace, authorize the search breadth, and queue metadata before
   retrieving content. Reuse scope authorization already given in this session.
4. Process one trigger per isolated reader with its complete linked conversations.
   The launcher loads [shared rules](../../references/hiring-email-rules.md) and the
   result schema itself; never copy them into a provider agent.
5. Report counts and redacted review findings as specified by orchestration.
