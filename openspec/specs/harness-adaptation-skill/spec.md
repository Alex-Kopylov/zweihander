# harness-adaptation-skill Specification

## Purpose

Defines what the rewritten `adapt-skill-for-ai-harness` skill instructs: authoring harness-parametric Jinja templates against the action matrix, written as if the template model had always been the only distribution model.

## Requirements

### Requirement: Skill instructs template authoring
The skill SHALL instruct converting an explicitly named target skill's harness-specific wording into template form: callable names via action-map lookups and the wrapper mechanism, harness conditionals only for genuinely divergent narrative, and the `.j2` marking with its plain/template collision rule.

#### Scenario: Adapting a target produces a template
- **WHEN** the skill is invoked to adapt an explicitly named target skill that contains harness-specific wording
- **THEN** the result is a `.j2` template using action-map lookups, and no per-harness reference files are created

#### Scenario: Only the named target changes
- **WHEN** the skill is invoked with one named target skill
- **THEN** no other skill's files are modified

### Requirement: Skill carries no legacy pattern
The skill SHALL be written greenfield: every file in the skill directory — `SKILL.md`, references, scripts, evals, and any other content — SHALL NOT instruct creating `references/ai-assistant-harnesses/` files, dispatch sentences, or harness metadata links, and SHALL NOT mention the retired runtime-dispatch pattern, its migration, or its history. Files with no greenfield replacement SHALL be deleted.

#### Scenario: Legacy pattern scan passes
- **WHEN** the skill's content files are scanned for legacy dispatch-pattern instructions
- **THEN** the scan finds none

### Requirement: Skill documents the frontmatter portability boundary
The skill SHALL document that frontmatter is the portability boundary and that the frontmatter matrix is its only source: the six portable specification fields, the global named after each placed key as that key's only route, both placements, every value form the matrix documents, the merge of a hand-written `metadata:` block, and the namespaced `metadata` shape. The skill SHALL link the vendored Agent Skills specification instead of the network, SHALL state that a product's own UI, invocation policy and tool dependencies belong in `agents/openai.yaml` rather than in frontmatter, SHALL document the frontmatter matrix contract alongside the action matrix contract, and SHALL provide a scriptable key-then-assistant lookup.

#### Scenario: Boundary documented
- **WHEN** the skill content is checked against the renderer's frontmatter behavior
- **THEN** the portable key set, the global call form of every placed key, both placements, every documented value form, and the metadata namespaces are documented in the skill

#### Scenario: Frontmatter lookup resolves a placement
- **WHEN** the skill's frontmatter lookup runs for one key and one assistant
- **THEN** it returns that key's placement, form, and how to declare it

#### Scenario: Specification is read locally
- **WHEN** the skill points an author at the format specification
- **THEN** it links the vendored document in the skill's own references rather than a URL

#### Scenario: Product settings are routed out of frontmatter
- **WHEN** the skill covers a product's UI, invocation policy, or tool dependencies
- **THEN** it directs them to `agents/openai.yaml`

### Requirement: Skill documents matrix maintenance
The skill SHALL document the matrix contract: one callable name per mapped action per harness, one invocation wrapper per harness, stable TitleCase action keys, stable assistant keys, and the action-then-assistant lookup order.

#### Scenario: Matrix contract documented
- **WHEN** the skill content is checked against the matrix schema used by the renderer
- **THEN** every schema element the renderer depends on is documented in the skill
