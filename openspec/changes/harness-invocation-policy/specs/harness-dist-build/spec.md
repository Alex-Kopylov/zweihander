## ADDED Requirements

### Requirement: Invocation policy compiled per harness
A skill's invocation policy SHALL be one setting with two authored spellings: `disable-model-invocation` in the `SKILL.md` frontmatter and `policy.allow_implicit_invocation` in the skill's `agents/openai.yaml`. An author MAY write either or both; `disable-model-invocation: true` and `allow_implicit_invocation: false` mean the same setting. The renderer SHALL write the setting where each harness reads it: the Claude Code tree SHALL carry `disable-model-invocation` in `SKILL.md` and SHALL NOT carry `agents/openai.yaml`; the Codex tree SHALL carry `policy.allow_implicit_invocation` in `agents/openai.yaml`, creating the file when the skill has none and keeping every other entry when it has one, and its `SKILL.md` SHALL NOT carry `disable-model-invocation`. The renderer SHALL read `SKILL.md` after rendering, so a template and a plain file behave alike. The build SHALL fail, naming the skill and both values, when the two spellings disagree, and SHALL fail when either value is not a boolean.

#### Scenario: Frontmatter declaration reaches Codex
- **WHEN** a skill sets `disable-model-invocation: true` in `SKILL.md` and has no `agents/openai.yaml`
- **THEN** the Codex tree contains `agents/openai.yaml` with `policy.allow_implicit_invocation: false`, the Codex `SKILL.md` carries no `disable-model-invocation`, and the Claude Code `SKILL.md` keeps `disable-model-invocation: true`

#### Scenario: Codex declaration reaches Claude Code
- **WHEN** a skill sets `policy.allow_implicit_invocation: false` in `agents/openai.yaml` and its `SKILL.md` does not set `disable-model-invocation`
- **THEN** the Claude Code `SKILL.md` frontmatter carries `disable-model-invocation: true`

#### Scenario: Codex interface entries survive the merge
- **WHEN** a skill's `agents/openai.yaml` carries `interface` entries and no policy, and its `SKILL.md` sets `disable-model-invocation: true`
- **THEN** the Codex `agents/openai.yaml` carries the same `interface` entries and `policy.allow_implicit_invocation: false`

#### Scenario: Claude Code tree carries no Codex agent file
- **WHEN** a skill has `agents/openai.yaml`
- **THEN** the Claude Code tree does not contain that file

#### Scenario: Contradiction fails the build
- **WHEN** a skill sets `disable-model-invocation: true` and `policy.allow_implicit_invocation: true`
- **THEN** the build fails and names the skill and both values

#### Scenario: Non-boolean value fails the build
- **WHEN** a skill sets `disable-model-invocation` or `policy.allow_implicit_invocation` to anything but `true` or `false`
- **THEN** the build fails and names the skill and the value
