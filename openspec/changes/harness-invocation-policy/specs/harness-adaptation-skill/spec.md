## MODIFIED Requirements

### Requirement: Skill documents the frontmatter portability boundary
The skill SHALL document that frontmatter is the portability boundary and that the frontmatter matrix is its only source: the six portable specification fields, the global named after each placed key as that key's only route, both placements, every value form the matrix documents, the merge of a hand-written `metadata:` block, and the namespaced `metadata` shape. The skill SHALL link the vendored Agent Skills specification instead of the network, SHALL state that a product's own UI and tool dependencies belong in `agents/openai.yaml` rather than in frontmatter, SHALL state that invocation policy may be written as `disable-model-invocation` in frontmatter, as `policy.allow_implicit_invocation` in `agents/openai.yaml`, or both, that the build writes it where each harness reads it, and that disagreeing values fail the build, SHALL document the frontmatter matrix contract alongside the action matrix contract, and SHALL provide a scriptable key-then-assistant lookup.

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
- **WHEN** the skill covers a product's UI or tool dependencies
- **THEN** it directs them to `agents/openai.yaml`

#### Scenario: Invocation policy has two spellings
- **WHEN** the skill covers invocation policy
- **THEN** it names `disable-model-invocation` and `policy.allow_implicit_invocation`, says the build writes each harness its own spelling, and says disagreeing values fail the build
