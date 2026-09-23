# harness-invocation-notation Specification

## Purpose

Defines the single uniform notation each harness build uses to reference callables in rendered narrative, the two allowed name shapes, and the action-matrix contract that supplies names to templates.

## Requirements

### Requirement: One invocation wrapper per harness
Rendered narrative SHALL reference every callable through the target harness's single invocation wrapper — `Skill(<name>)` for Claude Code, `$<name>` for Codex — with no per-surface distinctions, availability footnotes, or fallback clauses. The wrapper SHALL be defined once per harness, not per action.

#### Scenario: Ask-the-user renders uniformly
- **WHEN** a template references the ask-the-user action and both harness trees are rendered
- **THEN** the Claude Code output contains `Skill(AskUserQuestion)` and the Codex output contains `$request_user_input`

#### Scenario: Delegation renders uniformly
- **WHEN** a template references the delegate-work action and both harness trees are rendered
- **THEN** the Claude Code output contains `Skill(Agent)` and the Codex output contains `$spawn_agent`

### Requirement: Notation is a repo convention, not vendor API
The uniform wrapper SHALL NOT be narrowed toward vendor tool-name spelling. Harness vendors write built-in callable names bare in their own documentation and shipped prompts; this repository wraps them anyway, and that divergence is intentional. Repository checks and reviews SHALL treat a mismatch between rendered notation and vendor documentation as expected, and SHALL NOT reintroduce a separate spelling for callables a vendor documents as tools.

#### Scenario: Vendor mismatch is not a defect
- **WHEN** rendered narrative wraps a callable that vendor documentation writes as a bare name
- **THEN** the notation stands unchanged and no repository check reports it

#### Scenario: Per-surface spelling stays rejected
- **WHEN** a change would render one spelling for callables a vendor documents as tools and another spelling for skills
- **THEN** the change is rejected as a revert of this requirement

### Requirement: Exactly two name shapes
Callable names in rendered narrative SHALL have exactly two shapes: a bare `skill-name` — used identically for harness built-ins and for skills from user skill directories — and a plugin-qualified `plugin-name:skill-name` for plugin-installed skills.

#### Scenario: Bare name renders
- **WHEN** a template wraps the bare name `commit`
- **THEN** the Claude Code output contains `Skill(commit)` and the Codex output contains `$commit`

#### Scenario: Plugin-qualified name renders
- **WHEN** a template wraps the qualified name `dev-workflow:commit`
- **THEN** the Claude Code output contains `Skill(dev-workflow:commit)` and the Codex output contains `$dev-workflow:commit`

### Requirement: Matrix maps actions to names
The action matrix SHALL mark every action as callable or non-callable, SHALL map each callable action to exactly one callable name per supported harness — several actions MAY resolve to the same name — SHALL store the invocation wrapper once per harness, and SHALL preserve the action-then-assistant lookup order. Non-callable actions carry reference material and are exempt from the name-and-wrapper rule.

#### Scenario: Action lookup resolves a name
- **WHEN** the matrix is loaded and the delegate-work action is looked up for Codex
- **THEN** the lookup returns the name `spawn_agent`

#### Scenario: Task operations map many-to-one on Codex
- **WHEN** the `CreateTask` and `UpdateTask` actions are looked up for both harnesses
- **THEN** Claude Code returns `TaskCreate` and `TaskUpdate`, and Codex returns `update_plan` for both

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

#### Scenario: Declared argument placeholder is not a callable
- **WHEN** a `.j2` source file spells a `$name` inside a harness conditional and the same file declares that name through the `arguments` global
- **THEN** the repository policy check passes, because the name is a Claude Code argument placeholder rather than a callable
