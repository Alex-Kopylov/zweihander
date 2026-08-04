# harness-invocation-notation

## Purpose

Defines the single uniform notation each harness build uses to reference callables in rendered narrative, the two allowed name shapes, and the action-matrix contract that supplies names to templates.

## ADDED Requirements

### Requirement: One invocation wrapper per harness
Rendered narrative SHALL reference every callable through the target harness's single invocation wrapper — `Skill(<name>)` for Claude Code, `$<name>` for Codex — with no per-surface distinctions, availability footnotes, or fallback clauses. The wrapper SHALL be defined once per harness, not per action.

#### Scenario: Ask-the-user renders uniformly
- **WHEN** a template references the ask-the-user action and both harness trees are rendered
- **THEN** the Claude Code output contains `Skill(AskUserQuestion)` and the Codex output contains `$request_user_input`

#### Scenario: Delegation renders uniformly
- **WHEN** a template references the delegate-work action and both harness trees are rendered
- **THEN** the Claude Code output contains `Skill(Agent)` and the Codex output contains `$spawn_agent`

### Requirement: Exactly two name shapes
Callable names in rendered narrative SHALL have exactly two shapes: a bare `skill-name` — used identically for harness built-ins and for skills from user skill directories — and a plugin-qualified `plugin-name:skill-name` for plugin-installed skills.

#### Scenario: Bare name renders
- **WHEN** a template wraps the bare name `commit`
- **THEN** the Claude Code output contains `Skill(commit)` and the Codex output contains `$commit`

#### Scenario: Plugin-qualified name renders
- **WHEN** a template wraps the qualified name `dev-workflow:commit`
- **THEN** the Claude Code output contains `Skill(dev-workflow:commit)` and the Codex output contains `$dev-workflow:commit`

### Requirement: Matrix maps actions to names
The action matrix SHALL map each mapped action to one callable name per supported harness, SHALL store the invocation wrapper once per harness, and SHALL preserve the action-then-assistant lookup order.

#### Scenario: Action lookup resolves a name
- **WHEN** the matrix is loaded and the delegate-work action is looked up for Codex
- **THEN** the lookup returns the name `spawn_agent`

#### Scenario: Wrapper stored once per harness
- **WHEN** the matrix is validated
- **THEN** each harness defines exactly one invocation wrapper, and no per-action entry defines its own wrapper or invocation-form list

### Requirement: Templates take names from the matrix
Template sources SHALL obtain callable names through the resolved action map or the wrapper mechanism, SHALL NOT hardcode another mechanism's harness-specific callable names as literals, and SHALL use harness conditionals only for narrative that genuinely differs between harnesses.

#### Scenario: Literal mapped names rejected in template sources
- **WHEN** a `.j2` source file names a matrix-mapped callable literally instead of through the action map
- **THEN** the repository policy check fails and names the file

#### Scenario: Names never branch on harness
- **WHEN** a `.j2` source file selects a callable name inside a harness conditional
- **THEN** the repository policy check fails and names the file
