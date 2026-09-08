---
name: ticket-branch
description: Create git branch from a ticket. Activate when user provides a ticket ID or URL from your issue tracker and wants to create a branch.
---

# Create Branch from Ticket

Create git branches using a ticket ID and summary.

## Instructions

1. **Parse ticket ID** from user input, accepting either a ticket URL or a direct ID such as `1234`.

2. **Fetch ticket details** with `<platform-cli>` to get the ticket title/summary.

3. **Generate branch name**:
   - Format: `<type>/<TICKET-ID>-<short-description>`
   - Convert summary to kebab-case (lowercase, hyphens)
   - Remove special chars, keep alphanumeric and hyphens
   - Limit description to ~5 words max
   - Examples: `feat/1234-add-feature`, `fix/5678-fix-broken-parser`

4. **Ask user to confirm** branch name before creating

5. **Create branch** from project root:

   ```bash
   wt switch -b develop -c <branch-name>
   ```

6. **Report results**: confirm branch was created

## Examples

**Input:** `1234` or ticket URL
**Ticket summary:** "Add user authentication flow"
**Branch:** `feat/1234-add-user-auth-flow`

**Input:** `5678` or ticket URL
**Ticket summary:** "Fix broken CSV parser"
**Branch:** `fix/5678-fix-broken-csv-parser`

## Notes

- Branch format: `<type>/<TICKET-ID>-<short-kebab-description>`
- Always confirm branch name with user before creating
- Always branch from `develop` at the project root
