# GitHub

## Labels

Set labels on every PR you create.

1. List the labels the repository already has:
   `gh label list --limit 200 --json name,description`
2. Pick the ones that fit the change from that list.
3. Create a new label only when no existing label fits and you are confident
   the PR needs one: `gh label create "<name>" --description "<what it marks>"`.
4. Pass the labels at creation: `gh pr create --label "<name>" --label "<name>"`.
