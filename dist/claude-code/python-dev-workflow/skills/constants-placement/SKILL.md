---
name: constants-placement
description: Triages hardcoded values in Python code and moves each one where it belongs - kept in its module, a shared constants module, a pydantic-settings field, or a secret in .env. Use when auditing or refactoring module-level constants, magic numbers, hardcoded URLs, hosts, ports, timeouts, credentials or API keys, constants duplicated across files, scattered os.getenv calls, or when centralizing configuration into a BaseSettings config.py.
---

# Constants Placement

Find the hardcoded values in a Python codebase, decide where each belongs, and
move it there. Apply the changes directly, then report what moved and why.

## Destinations

| Destination | Holds | Form |
|---|---|---|
| Stay in its module | A constant only one module uses | `UPPER_CASE: Final = ...` at the top of the module |
| Shared `constants.py` | A constant two or more modules use | Leaf module in the lowest common package |
| `config.py` Settings field | A value that can differ between deployments | Field on the project's settings class, current value as default |
| `.env` | A secret | Settings field with no default; the value lives only in `.env` |

Config is whatever may vary between deploys (dev, staging, production);
everything identical in every deploy is a constant and belongs in code. The
test for secrets: could this code be published today without leaking a
credential?

## 1. Inventory

Read the code the user pointed at, or the whole package if they named none.
Candidates:

- module-level and class-level names bound to literals, whatever their case;
- literals inside functions that carry domain meaning: URLs, hosts, ports,
  timeouts, limits, regexes, header names, file paths;
- every `os.getenv` / `os.environ` read, the config module included - each
  becomes a Settings field, so the environment is read in one typed place.

Skip test fixture data, migrations, generated and vendored code, and module
dunders (`__version__`, `__all__`).

## 2. Constant or variable

A constant is bound once, to a value that never changes. Classify by
behavior, not by case:

- **Variable** - rebound (a second assignment, `global X`, `X += ...`),
  mutated (`.append`, `X[k] = v`, `.update`), or computed from runtime state
  (time, cwd, I/O, randomness). An `UPPER_CASE` registry that gets filled at
  import is a variable. Leave variables alone.
- **Constant with the wrong name** - a lowercase module-level name bound to a
  literal and never rebound. Rename it to `UPPER_CASE`.
- **Mutable container never mutated** - a constant; switch a list to a tuple
  or a set to a frozenset when no caller relies on mutability.

## 3. Classify

Take the first match. The order matters: a secret is also config, and config
is also a constant.

1. **Secret** - name says so (`password`, `token`, `secret`, `api_key`,
   `private_key`, `credentials`), or the value looks like one (key prefixes
   such as `sk_`, `ghp_`, `AKIA`, `xox`; `-----BEGIN`; long high-entropy
   strings; a URL with `user:password@`). Publishable identifiers (`pk_`
   keys, public OAuth client IDs) are config, not secrets.
2. **Config** - would staging and production want different values, or would
   an operator tune it without a code change? Hosts, service URLs, ports,
   database and bucket names, timeouts and pool sizes for external services,
   log level, debug and feature flags, data directories.
   Not config: protocol facts (status codes, header names), values tied to
   the code (regexes, a limit that mirrors a database column), business rules
   that change only with a release, unit conversions.
3. **Shared constant** - used from two or more files, or a duplicate of one
   (step 4).
4. **Local constant** - everything else.

## 4. Duplicates are about meaning, not value

Group candidates by what they mean:

- the same concept under different names (`TIMEOUT` in one file,
  `REQUEST_TIMEOUT_S` in another);
- the same literal repeated inline;
- one value derivable from another (a base URL and a full endpoint URL).

Equal values with different meanings stay separate: `MAX_RETRIES = 3` and
`MIN_PASSWORD_DIGITS = 3` merged would couple two unrelated decisions.

Keep one definition per concept under the most descriptive name, with units
in the name (`REQUEST_TIMEOUT_SECONDS`), and derive the rest from it
(`USERS_URL = f"{API_BASE_URL}/users"`).

When one concept holds different values in different places, do not pick a
winner: unifying would change behavior. Leave the values as they are and list
the conflict in the report for the user to decide.

## 5. Apply

### Local constant

Put it at the top of the module, after the imports, as
`NAME: Final = value`. Replace a meaningful magic literal with a named
constant. Leave self-evident literals alone (`0`, `1`, `-1`, `""`, the `2` in
a pair check): naming them adds noise, which is why linters that flag every
literal get switched off.

### Shared `constants.py`

Place it in the lowest package that contains every module using the
constant. It must be a leaf: import only the standard library, so any module
in the package can import it without a cycle. Never use `__init__.py` for
this - a submodule importing from its own package's `__init__.py` is a
classic circular import. Group related values into an `Enum` or `StrEnum`.
Point every user at the new location and delete the old definitions. If the
file starts mixing unrelated topics, split it by topic.

### Settings field

Reuse the project's settings class; never create a second one. With none
yet, create one on pydantic-settings `BaseSettings`. Either way, write the
fields, secrets and access by
[references/pydantic-settings.md](references/pydantic-settings.md).

- A non-secret field takes the current hardcoded value as its default, so
  behavior does not change.
- An environment variable the code already reads keeps its exact name: a
  deployment sets it, and a renamed variable is silently ignored while the
  default wins.
- Read settings where the value is used, not at import time. A module-level
  read makes importing fail whenever the environment is incomplete and
  blocks tests from overriding the value.
- The exception: a module that already acts on the value at import
  (`logging.basicConfig(level=LOG_LEVEL)`) keeps doing so in the same place.
  Behavior beats lazy reading.
- Add every variable to `.env.example` (committed), so the next developer
  knows what to set.

### Secret

- A secret field with no default. A default would leave the secret in code.
- Write the value to `.env` and a placeholder to `.env.example`. Unwrap the
  secret only where it is used.
- Make sure `.env` stays out of git:
  - `git check-ignore -q .env` fails → add `.env` to the root `.gitignore`;
  - `git ls-files --error-unmatch .env` succeeds → the file is tracked, and
    `.gitignore` does not apply to tracked files; run `git rm --cached .env`
    (the local file stays).
- If the secret was ever committed, it is still in history. Check with
  `git log -S'<value>' --oneline`. Tell the user to revoke or rotate it -
  that is the fix; a history rewrite is optional and destructive, so leave it
  to them.
- Never print a secret value in the report or chat. Refer to it by name and
  location.

## 6. Verify

Import the package, then run the project's tests and linters. Search for the
old names and literals to confirm nothing still points at a removed
definition.

## Report

```markdown
| Name | Was | Kind | Decision | Now |
|---|---|---|---|---|
| `STRIPE_KEY` | `shop/payments.py:4` | secret | → .env | `Settings.stripe_key` |
| `TIMEOUT`, `REQUEST_TIMEOUT` | `clients/a.py:3`, `clients/b.py:5` | config, duplicate | → Settings | `Settings.request_timeout_seconds` |

### Security
Secrets moved, `.env` ignore and tracking status, secrets found in history
(rotate these).

### Left for you
Conflicting values for one concept, and anything else not changed, with the
reason.
```

Skip a section that has nothing in it.
