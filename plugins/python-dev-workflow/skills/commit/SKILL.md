---
name: commit
description: Commit staged changes following Conventional Commits v1.0.0. Activate when user asks to commit, create a commit, or says /commit.
---

# Commit (Conventional Commits v1.0.0)

Create git commits following the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Format

```
<type>[optional scope]: <description>
```

Single line only. No body, no footer, no multiline.

## Types

| Type | Meaning |
|------|---------|
| `feat` | New feature (MINOR in semver) |
| `fix` | Bug fix (PATCH in semver) |
| `build` | Build system or external dependencies |
| `chore` | Other changes (no src/test modification) |
| `ci` | CI configuration files/scripts |
| `docs` | Documentation only |
| `perf` | Performance improvement |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `revert` | Reverts a previous commit |
| `style` | Formatting, whitespace, semicolons (no code change) |
| `test` | Adding or correcting tests |
| `bump` | Version bump (include old → new version in description) |

## Breaking Changes

Append `!` before the colon to indicate a breaking change:

```
feat!: drop support for python 3.11
```

## Scope

Optional. Describes the section of the codebase affected, in parentheses:

```
fix(payments): resolve decimal rounding
feat(auth): add oauth2 support
```

## Description Rules

- Lower-case first letter
- No period at end
- Imperative mood ("add" not "added", "fix" not "fixed")
- Concise — describe what was done briefly

## Instructions

1. Run `git diff --staged` to analyze staged changes
2. Determine the appropriate **type** from the table above
3. Optionally determine a **scope** (component/module affected)
4. Write a concise description of what was done
5. Commit with single-line message:
   ```bash
   git commit -m "type: description"
   # or with scope:
   git commit -m "type(scope): description"
   ```
6. **Never** include body or footer — single line only
7. **Never** mention claude or claude code in commit message

## Examples

```
feat: add user authentication endpoint
fix(payments): resolve decimal rounding
refactor: extract validation logic into helpers
docs: update API changelog
test: add unit tests for order service
chore: update ruff config
feat!: drop support for python 3.11
bump: v0.4.0 → v0.5.0
bump(deps): upgrade pydantic to 2.10.0
build: migrate from pip to uv
ci: add staging deployment step
perf(queries): optimize merchant lookup query
style: fix indentation in config files
revert: undo migration changes from previous commit
```
