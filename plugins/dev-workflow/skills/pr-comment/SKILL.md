---
name: pr-comment
description: Post a review comment to a pull request. Use whenever the user asks to "post a comment", "add review comment", "comment on PR", "leave feedback on PR", "post inline comment", "add PR note", "review comment", or wants to post any kind of feedback to a pull request. Handles both general PR comments and inline file-specific comments. Works with Azure DevOps (via MCP or CLI). If no PR link is given, auto-detects from the current branch.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# PR Comment

Post review comments to pull requests — general or inline on specific lines.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PR link or ID | No | URL or numeric ID of the PR. Auto-detected if omitted. |
| Comment text | Yes | The review message to post |
| File path | No | Path to file for inline comment |
| Start line | No | First line of the comment range |
| End line | No | Last line of the comment range |

## Workflow

### 1. Resolve the PR

**If a PR link/URL is provided**, parse it to extract:
- Platform (Azure DevOps, GitHub, etc.)
- Org, project, repo, and PR ID

**If no PR link is provided**:
1. Run `git remote get-url origin` to identify the platform and repo
2. Run `git branch --show-current` to get the current branch name
3. Search for open PRs from this branch (see `references/azure.md` for platform-specific lookup)
4. If exactly one PR is found — use it
5. If multiple PRs are found — ask the user to choose from the list
6. If no PR is found — ask the user for the PR link

### 2. Compose the comment

Use readable review formatting by default:

- Start with the issue and impact in one or two sentences.
- Put metadata such as severity, risk, validation, or recommendation in short
  labeled lines.
- Keep prose compact; do not bury the suggested fix inside a paragraph or a
  table.
- When the comment proposes a concrete replacement and a file/line range is
  available, include a platform-native inline suggestion by default. Omit it
  only when the user explicitly asks for no suggestion, the platform cannot
  support it, or the target range cannot be anchored safely.
- For GitHub-specific review-comment and suggestion syntax, read
  `references/github.MD`.

Take the user's message after applying the formatting rules above and append
the signature:

```
{user's comment text}

---
_Co-Authored by AI Reviewer_
```

### 3. Post the comment

**General comment** (no file path provided):
- Create a new comment thread on the PR with the composed message

**Inline comment** (file path provided):
- Create a comment thread anchored to the file and line range
- If only start line is given, end line = start line
- If neither start nor end line is given but file path is — post a file-level comment

### 4. Confirm

Report back: "Posted comment on PR #{id}" with a link to the PR.

## Platform Detection

Parse the origin URL or PR link to determine the platform:

| Pattern | Platform |
|---------|----------|
| `dev.azure.com` or `visualstudio.com` | Azure DevOps |
| `github.com` | GitHub |
| `gitlab.com` | GitLab |

Use the matching platform's tools/CLI. See `references/azure.md` for Azure DevOps specifics.

If the platform cannot be determined, ask the user.
