---
name: constants-placement
description: Triages hardcoded values in Python code and moves each one where it belongs - kept in its module, a shared constants module, a pydantic-settings field, or a secret in .env. Use when auditing or refactoring module-level constants, magic numbers, hardcoded URLs, hosts, ports, timeouts, credentials or API keys, constants duplicated across files, scattered os.getenv calls, or when centralizing configuration into a pydantic_settings.BaseSettings.
metadata:
  references:
    "references/settings-class.md": "Load when creating a Settings class or adding config fields to one."
    "references/secrets.md": "Load when a secret becomes a Settings field."
    "references/existing-env-vars.md": "Load when replacing an os.getenv read or any variable a deployment already sets, or when grouping fields into a nested model."
    "references/using-settings.md": "Load when replacing the old constant's usages, or when the project has tests that import the changed modules."
---

# Constants Placement

Apply the changes directly, then report what moved and why.

## 1. Inventory

- module-level and class-level names bound to literals, whatever their case;
- literals inside functions that carry domain meaning: URLs, hosts, ports,
  timeouts, limits, regexes, header names, file paths;
- every `os.getenv` / `os.environ` read, the config module included - each
  becomes a Settings field, so the environment is read in one typed place.

Skip test fixture data, migrations, generated and vendored code, and module
dunders.

## 2. Constant or variable

Classify by behavior, not by case:

- **Variable** - rebound, mutated, or computed from runtime state (time,
  cwd, I/O, randomness). An `UPPER_CASE` registry filled at import is a
  variable. Leave variables alone.
- **Constant with the wrong name** - a lowercase module-level name bound to a
  literal and never rebound. Rename it to `UPPER_CASE`.
- **Mutable container never mutated** - a constant; make it a tuple or
  frozenset when no caller relies on mutability.

## 3. Classify

Take the first match: a secret is also config, and config is also a
constant.

1. **Secret → `.env`** - name says so (`password`, `token`, `secret`,
   `api_key`, `private_key`, `credentials`), or the value looks like one (key
   prefixes such as `sk_`, `ghp_`, `AKIA`, `xox`; `-----BEGIN`; long
   high-entropy strings; a URL with `user:password@`). Publishable
   identifiers (`pk_` keys, public OAuth client IDs) are config.
2. **Config → Settings field** - would staging and production want different
   values, or would an operator tune it without a code change? Hosts, service
   URLs, ports, database and bucket names, timeouts and pool sizes for
   external services, log level, debug and feature flags, data directories.
   Not config: protocol facts (status codes, header names), values tied to
   the code (regexes, a limit that mirrors a database column), business rules
   that change only with a release, unit conversions.
3. **Shared constant → `constants.py`** - used from two or more files, or a
   duplicate of one (step 4).
4. **Local constant → stays in its module.**

## 4. Duplicates are about meaning, not value

Merge the same concept under different names (`TIMEOUT`, `REQUEST_TIMEOUT_S`)
into one definition with units in the name (`REQUEST_TIMEOUT_SECONDS`), and
derive related values from it (`USERS_URL = f"{API_BASE_URL}/users"`).

Equal values with different meanings stay separate: merging `MAX_RETRIES = 3`
and `MIN_PASSWORD_DIGITS = 3` would couple two unrelated decisions.

When one concept has conflicting values, do not pick a winner: unifying
would change behavior. Leave the values and list the conflict in the report.

## 5. Apply

### Local constant

`NAME: Final = value` at the top of the module. Leave self-evident literals
alone (`0`, `1`, `-1`, `""`, the `2` in a pair check).

### Shared `constants.py`

In the lowest common package of the modules using it, as a leaf that imports
only the standard library, so any module in the package can import it
without a cycle. Never `__init__.py`: a submodule importing from its own
package's `__init__.py` is a classic circular import. Point every user at the
new location and delete the old definitions.

### Settings field

Reuse the project's settings class; never create a second one. With none
yet, create one on pydantic-settings `BaseSettings` by
[references/settings-class.md](references/settings-class.md).

- A non-secret field takes the current hardcoded value as its default, so
  behavior does not change.
- An environment variable the code already reads keeps its exact name: a
  deployment sets it, and a renamed variable is silently ignored while the
  default wins. See
  [references/existing-env-vars.md](references/existing-env-vars.md).
- Read settings where the value is used, not at import time: a module-level
  read breaks imports when the environment is incomplete and blocks test
  overrides. The exception: a module that already acts on the value at import
  (`logging.basicConfig(level=LOG_LEVEL)`) keeps doing so. Behavior beats
  lazy reading. See [references/using-settings.md](references/using-settings.md).
- Add every variable to `.env.example` (committed).

### Secret

- A Settings field with no default; a default would leave the secret in
  code. The value goes to `.env`, a placeholder to `.env.example`. See
  [references/secrets.md](references/secrets.md).
- Keep `.env` out of git:
  - `git check-ignore -q .env` fails → add `.env` to the root `.gitignore`;
  - `git ls-files --error-unmatch .env` succeeds → the file is tracked, and
    `.gitignore` does not apply to tracked files; run `git rm --cached .env`
    (the local file stays).
- A secret ever committed is still in history (`git log -S'<value>'`). Tell
  the user to revoke or rotate it - that is the fix; a history rewrite is
  optional and destructive, so leave it to them.
- Never print a secret value in the report or chat; refer to it by name and
  location.

## 6. Verify

Run the project's tests and linters, and search for the old names and
literals to catch stale references.

## Report

A table `Name | Was | Kind | Decision | Now` with `file:line` locations, then
**Security** (secrets moved, `.env` ignore and tracking status, secrets in
history to rotate) and **Left for you** (conflicting values and anything else
not changed, with the reason). Omit empty sections.
