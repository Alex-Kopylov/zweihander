## MODIFIED Requirements

### Requirement: Foreign runtime metadata stripped
Each harness tree SHALL contain only its own runtime plugin metadata: no `.codex-plugin/` directory under `dist/claude-code/**` and no `.claude-plugin/` directory under `dist/codex/**`. A skill's `agents/openai.yaml` is Codex runtime metadata: the Codex tree SHALL carry it exactly as authored, and the Claude Code tree SHALL NOT carry it.

#### Scenario: Metadata filtered per tree
- **WHEN** the full build completes
- **THEN** `dist/claude-code/**` contains no `.codex-plugin/` directory and `dist/codex/**` contains no `.claude-plugin/` directory

#### Scenario: Codex agent file ships to Codex only
- **WHEN** a skill has `agents/openai.yaml`
- **THEN** the Codex tree carries it byte-for-byte and the Claude Code tree carries no `openai.yaml`

## ADDED Requirements

### Requirement: Codex skill frontmatter carries only specification keys
Every `SKILL.md` in the Codex tree SHALL carry only the top-level keys the Agent Skills specification defines, as listed under `specification.portable_keys` in the frontmatter matrix. A key only Claude Code reads that the frontmatter matrix does not place SHALL sit in a `{% if harness == "ClaudeCode" %}` branch of the template.

#### Scenario: Claude Code-only key stays out of Codex
- **WHEN** a template writes `disable-model-invocation: true` inside a Claude Code harness branch
- **THEN** the Claude Code `SKILL.md` carries the key and the Codex `SKILL.md` does not

#### Scenario: Non-specification key fails the check
- **WHEN** a Codex `SKILL.md` carries a top-level key outside the specification's list
- **THEN** the rendered-tree test fails and names the file and the key

### Requirement: User-only skills agree across harnesses
A skill whose Claude Code `SKILL.md` sets `disable-model-invocation: true` SHALL ship `agents/openai.yaml` with `policy.allow_implicit_invocation: false` in the Codex tree, and a skill with that Codex policy SHALL set that Claude Code key. The renderer SHALL NOT derive either spelling from the other, so a skill MAY set a different policy per harness; the rendered-tree test SHALL accept such a skill only when it is declared as deliberately divergent, and SHALL fail when a declared skill does not diverge. No skill is declared today.

#### Scenario: One spelling missing
- **WHEN** a skill sets `disable-model-invocation: true` for Claude Code and its Codex `agents/openai.yaml` does not set `allow_implicit_invocation: false`
- **THEN** the rendered-tree test fails and names the skill

#### Scenario: Deliberate difference is declared
- **WHEN** a skill is user-only for one harness on purpose and is declared as divergent
- **THEN** the rendered-tree test passes, and it fails again once the skill stops diverging
