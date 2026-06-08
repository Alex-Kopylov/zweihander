---
name: pr-address-comments
description: This skill should be used when the user asks to "address PR comments", "fix PR feedback", "resolve PR threads", "handle review comments", "address review feedback", "respond to PR comments", "fix code review comments", "fix what reviewers said", "work on PR comments", "iterate on PR", or "rework PR". It fetches unresolved PR review threads, presents them for user confirmation, then makes code fixes, replies to threads, and resolves them.
allowed-tools: AskUserQuestion, Agent, Skill(dev-workflow:commit, dev-workflow:pr-comment)
---

# PR Address Comments

Fetch reviewer comments from a pull request, present them for confirmation, then make code fixes, reply to threads, and resolve them.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PR link or ID | No | URL or numeric ID. Auto-detected from current branch if omitted. |

## Workflow

### 1. Resolve the PR

Follow the resolution flow in `references/platform-detection.md` to identify the platform, org, repo, and PR ID. Auto-detect from the current branch when no PR link is provided.

### 2. Fetch All Review Threads

Retrieve all threads from the PR. For each thread, collect:
- Thread ID and status (active, fixed, closed, etc.)
- File path and line range (if inline comment)
- All comments in the thread (author, content, timestamp)

**Filter out:**
- Already-resolved threads (status = fixed/closed/byDesign/wontFix)
- System-generated threads (build status, policy checks)
- Threads authored by the current user (self-comments)

### 3. Present Comments for Confirmation

Group remaining threads by file path (general comments grouped separately). For each thread, display:
- Reviewer name
- Comment text (truncated if very long)
- File path and line range (if inline)

Use **AskUserQuestion** with multiSelect to let the user pick which comments to address. Include an "All of them" option as the first choice.

### 4. Address Selected Comments

For each selected comment:

1. **Read the relevant code** — open the file at the referenced lines (or broader context if needed)
2. **Understand the ask** — interpret what the reviewer wants changed
3. **Make the fix** — edit the code to address the feedback
4. **Reply to the thread** — invoke `$dev-workflow:pr-comment` to post a reply explaining what was done (e.g. `"Fixed: extracted validation into helper"`)
5. **Resolve the thread** — mark the thread status as "fixed" via platform tools (see platform reference files for status codes)

If a comment is unclear or requires a judgment call, use **AskUserQuestion** to clarify before making changes.

### 5. Post-Fix Actions

After addressing selected comments, present options via **AskUserQuestion**:

- **Commit changes** — invoke `$dev-workflow:commit`
- **Push to remote** — push the current branch
- **Done for now** — leave changes uncommitted

Do not commit or push without explicit user confirmation via AskUserQuestion.

## References

### Platform Detection
- **`references/platform-detection.md`** — URL parsing, auto-detect logic, PR lookup flow

### Platform-Specific Guides
- **`references/platforms/azure-devops.md`** — MCP tools and CLI for threads, replies, resolution
- **`references/platforms/github.md`** — `gh` CLI and GraphQL for review threads, replies, resolution

## Error Handling

- If no active threads exist — report "No unresolved review comments found" and exit
- If a referenced file no longer exists — reply to the thread noting the file was removed/renamed, ask user how to proceed
- If a fix requires architectural discussion — flag via AskUserQuestion rather than making a unilateral decision
