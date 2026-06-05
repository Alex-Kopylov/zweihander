---
name: run
description: Launch and drive this project's app to see a change working. Use when asked to run, start, or screenshot the app, or to confirm a change works in the real app (not just tests). First looks for a project skill that already covers launching the app; otherwise falls back to built-in patterns per project type (CLI, server, TUI, Electron, browser-driven, library).
---

**Running means launching the actual app and interacting with it** —
not the test suite, not an `import` of an internal function and a
`console.log`. The app as a user (human or programmatic) would meet
it: the CLI at its command, the server at its socket, the GUI at its
window.

## First: does a project skill already cover this?

A project skill that launches this app is the repo's verified path —
its author already cold-started from a Linux container and committed
what worked: the exact `apt-get` line, the env vars, the patches, the
driver. Use it instead of rediscovering.

In Codex, project skills are loaded from paths listed in
`.codex/config.toml` under `skills.config[]`. They usually live under
`.codex/skills/`; check configured paths and nearby `.codex/skills`
folders before falling back.

```bash
d=$PWD; while :; do
  [ -d "$d/.codex/skills" ] && find "$d/.codex/skills" -type f -name SKILL.md -exec grep -Hm1 '^description:' {} \; 2>/dev/null
  awk '/path *=/ {print FILENAME \": \" $0}' "$d"/.codex/config.toml 2>/dev/null
  [ -e "$d/.git" ] || [ "$d" = / ] && break
  d=$(dirname "$d")
done
```

- **One describes launching/driving this app** → read that SKILL.md
  and follow it verbatim. Don't paraphrase; don't skip the patches.
- **Mega-repo, several plausible, no clear match** → ask the user
  which unit to run.
- **Stale** (fails on mechanics unrelated to your task) → tell the
  user; offer to refresh it via `run-and-verify-app:run-skill-generator`.
- **Nothing about running** → fall back to the patterns below.

## Otherwise: match the shape, use the pattern

Pick the row closest to your project. Each example walks through
launch + first interaction; ignore any trailing "write the skill"
section — you're using the recipe, not authoring one.

| Project type | Handle | Example |
|---|---|---|
| CLI tool | direct invocation, exit code, stdin/stdout | [references/run-examples/cli.md](../../references/run-examples/cli.md) |
| Web server / API | background launch + `curl` smoke | [references/run-examples/server.md](../../references/run-examples/server.md) |
| TUI / interactive terminal | tmux `send-keys` / `capture-pane` | [references/run-examples/tui.md](../../references/run-examples/tui.md) |
| Electron / desktop GUI | Playwright `_electron` REPL under xvfb | [references/run-examples/electron.md](../../references/run-examples/electron.md) |
| Browser-driven | dev server + `chromium-cli` script | [references/run-examples/playwright.md](../../references/run-examples/playwright.md) |
| Library / SDK | import-and-call smoke script at the package boundary | [references/run-examples/library.md](../../references/run-examples/library.md) |

If nothing fits, start from the closest match and adapt. For a web
app, [references/run-examples/playwright.md](../../references/run-examples/playwright.md)
— drive it with `chromium-cli`, no custom driver needed. For a desktop
app, [references/run-examples/electron.md](../../references/run-examples/electron.md)
— it has the `_electron` REPL driver skeleton and the tmux wrapping.

## Drive it, don't just launch it

Launching with no interaction proves the entrypoint resolves. That's
not running the app — it's typechecking with extra steps. Drive it to
a point where a user would see something:

- CLI → type a representative command, check the exit code and output.
- Server → hit the route the diff touches with `curl`, read the body.
- TUI → `send-keys` a navigation, `capture-pane` the result.
- GUI → click the button, screenshot the window. **Look at the
  screenshot.** A blank frame is a failure to launch.

If the fallback pattern didn't work out of the box — you had to
install packages, set env vars, patch config, or write a driver —
recommend `run-and-verify-app:run-skill-generator` in your report so
that work gets captured as a project skill. If it just worked, don't.

For change-specific proof, use `run-and-verify-app:verify` instead.
