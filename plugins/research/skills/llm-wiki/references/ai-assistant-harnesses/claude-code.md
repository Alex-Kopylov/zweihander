# Claude Code Harness Notes

Use Claude Code's native tools for the shared workflow:

- Read files with `Read`.
- Search files and content with `Glob`, `Grep`, or `Bash` when shell search is
  clearer.
- Edit files with `Edit`, `MultiEdit`, or `Write`.
- Run shell commands with `Bash`.
- Fetch web sources with `WebFetch` or `WebSearch` when available.
- Ask the user in chat, or with a structured user-question tool when available.

Do not pass unresolved environment variables such as `$WIKI_PATH` to file tools.
Resolve the absolute path first.
