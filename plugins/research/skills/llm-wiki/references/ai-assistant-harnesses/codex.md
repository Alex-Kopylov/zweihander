# Codex Harness Notes

Use Codex's native tools for the shared workflow:

- Read files with scoped shell commands such as `sed` or `nl` through
  `exec_command`.
- Search files and content with `rg` or `rg --files` through `exec_command`.
- Edit files with `apply_patch` for manual edits. Use formatters only for
  mechanical rewrites.
- Run shell commands with `exec_command`, and continue long-running sessions
  with `write_stdin`.
- Fetch web sources with `web.run` when browsing is required. For OpenAI docs,
  use the OpenAI docs MCP first.
- Ask the user in chat, or use `request_user_input` when it is available and a
  bounded structured choice is needed.

Do not pass unresolved environment variables such as `$WIKI_PATH` to file tools.
Resolve the absolute path first.
