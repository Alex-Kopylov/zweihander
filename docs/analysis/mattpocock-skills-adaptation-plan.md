# Adapting mattpocock/skills into Zweihander — high-level plan

Source: <https://github.com/mattpocock/skills> (MIT, © 2026 Matt Pocock).
Scope analysed: `skills/engineering/` (17) + `skills/productivity/` (5) = 22 skills.
Machine-readable graph: [`mattpocock-skills-graph.json`](./mattpocock-skills-graph.json).

Only `name` / `description` frontmatter was read. Skill bodies were scanned for
cross-references, not loaded.

## 1. What the graph says

45 invocation edges; 25 once the router `ask-matt` (which points at all 20 other
user-invoked skills) is excluded. Five tiers:

| Tier | Skills | Property |
|---|---|---|
| Router | `ask-matt` | 20 out-edges, 0 in |
| Repo config contract | `setup-matt-pocock-skills` | in=5, out=5 — everything depends on it |
| Flow orchestrators | `wayfinder` `triage` `implement` `to-tickets` `to-spec` `improve-codebase-architecture` `grill-with-docs` `grill-me` `diagnosing-bugs` | out ≥ 1 |
| Shared primitives | `grilling` `domain-modeling` `codebase-design` `tdd` `code-review` `research` `prototype` | out = 0, in ≥ 1 |
| Standalone | `resolving-merge-conflicts` `handoff` `teach` `writing-great-skills` | no invocation edges |

Most-depended-on primitives: `grilling` (5), `domain-modeling` (5).

`disable-model-invocation: true` on 13 of 22 skills, and the split is not
arbitrary: **every orchestrator is user-invoked, every primitive is
model-invokable.** Orchestrators are expensive multi-step flows the model must
not wander into; primitives are vocabulary the model should reach for freely.

## 2. Two kinds of edge — and the one that breaks on cherry-pick

Not every edge is a call. Two distinct kinds exist:

- **Invocation** — `/name`, `` `/name` ``, `**`/name`**`. A real call.
- **Shared vocabulary** — the skill name is a *label or ticket-type string* both
  sides agree on. No call, but a hard coupling.

The vocabulary edges are the dangerous ones because nothing fails loudly:

- `setup-matt-pocock-skills` writes tracker labels `wayfinder:map` and
  `wayfinder:<type>` where `<type>` ∈ `research` / `prototype` / `grilling` / `task`.
  `wayfinder` then reads those labels back.
- `to-spec` and `to-tickets` apply the `ready-for-agent` triage label defined by
  `setup-matt-pocock-skills`, not by `triage`.

**Consequence for us: `wayfinder`, `to-tickets`, `to-spec` and `triage` cannot be
lifted without also lifting the setup skill's label vocabulary.** They will run
and produce plausible-looking output against labels that do not exist.

## 3. Unformatted skill-name mentions (explicitly requested)

Bare occurrences — name with no backtick, bold, or slash — split cleanly in two.

### 3a. Prose collisions — false positives, ignore

English words that happen to be skill names. Every line was read to confirm.

| Edge | Evidence |
|---|---|
| `code-review` → `implement` | "does the code faithfully **implement** the originating issue" |
| `codebase-design` → `implement` | "**implement** an HTTP adapter for production" |
| `triage` → `implement` | "not **how** to implement it" (AGENT-BRIEF.md) |
| `to-spec` → `prototype` | "if a **prototype** produced a snippet…" |
| `to-tickets` → `prototype` | same sentence, duplicated file |

Lesson for our own skills: **do not name a skill after a bare English verb**
(`implement`, `research`, `prototype`, `triage`) unless every in-repo reference is
formatted. Our `run`, `verify`, `commit`, `interview`, `daily`, `mermaid` have the
same hazard.

### 3b. Real references left unformatted — worth flagging

| Edge | Where | Why it matters |
|---|---|---|
| `wayfinder` → `research` / `prototype` / `grilling` | `wayfinder/SKILL.md:78-80,105,115` | Ticket *types* named after skills, written unformatted in prose ("nothing to decide, prototype, or research"). A reader cannot tell type from skill. |
| `setup-matt-pocock-skills` → `wayfinder` | `issue-tracker-{github,gitlab}.md:40-42` | Label namespace `wayfinder:*` — pure vocabulary contract, no call. |
| `setup-matt-pocock-skills` → `triage` | `SKILL.md:12,55,57`, `triage-labels.md` | "triage roles" / "triage label" used as domain nouns, colliding with the skill name. |
| `triage` → `grilling` | `triage/SKILL.md:74,90,108` | "before any grilling", "Skip grilling" — refers to the skill's *behaviour*, formatted elsewhere in the same file. |
| `ask-matt` → 5 skills | `ask-matt/SKILL.md` | Bare mentions sit next to correctly formatted ones — harmless redundancy. |

## 4. Overlap against Zweihander's 53 skills

### Bucket A — take nearly as-is (no equivalent, zero out-edges)

| Their skill | Assets | Zweihander gap | Suggested home |
|---|---|---|---|
| `resolving-merge-conflicts` | — | none | `dev-workflow` |
| `codebase-design` | `DEEPENING.md`, `DESIGN-IT-TWICE.md` | none (closest is third-party `ponytail`) | new `engineering-design` |
| `prototype` | `LOGIC.md`, `UI.md` | none | new `engineering-design` |
| `teach` | 4 format docs | none | `work-session-tools` |
| `handoff` | — | partial (`ai-insights-hunter` is long-term memory, not next-session handoff) | `work-session-tools` |
| `grilling` | — | we have interview *flows*, not the interrogation *vocabulary* | `work-session-tools` |

### Bucket B — strong overlap, take the idea and merge

| Their skill | Our skill(s) | What theirs adds |
|---|---|---|
| `code-review` | `dev-workflow:requesting-code-review` | Two named axes (Standards vs Spec) run as parallel sub-agents; "since a fixed point" (commit/branch/tag/merge-base) |
| `tdd` | `dev-workflow:test-driven-development`, `python-dev-workflow:tests-manager` | `mocking.md` / `tests.md` references; "refactor is not in the loop" stance |
| `diagnosing-bugs` | `dev-workflow:systematic-debugging` | `scripts/hitl-loop.template.sh` — a scripted human-in-the-loop diagnosis loop |
| `research` | `research:llm-wiki`, `research:obsidian` | Ours store knowledge; theirs is the *investigation* loop → cited Markdown, run as a background agent |
| `writing-great-skills` | `ai-assistant-ops:improve-skill`, `md-bloat-hunter`, `adapt-skill-for-ai-harness` | `GLOSSARY.md` — a shared vocabulary for skill anatomy that our three skills each re-invent |
| `to-spec`, `grill-with-docs` | `dev-workflow:spec-interview` | `to-spec` is explicitly *no interview* — synthesis of an existing conversation. Complementary, not duplicate |
| `grill-me` | `work-session-tools:interview` | The thin-entrypoint-over-primitive pattern |

### Bucket C — architectural patterns, not skills

These are the highest-leverage items and none of them is a copy-paste.

1. **`setup-<x>` config skill + `docs/agents/*.md` contract.**
   One skill writes tracker choice, label vocabulary, and doc layout; every other
   skill reads it. Zweihander currently re-derives "your platform" independently in
   `ticket-branch`, `ticket-comment-status`, `create-pr`, `approve-pr`, `pr-checkout`,
   `pr-comment`, `pr-address-comments`, `yolo-push`. This is our single biggest DRY win.
2. **`agents/openai.yaml` per skill.** All 22 have one:
   `interface.display_name`, `interface.short_description`, and
   `policy.allow_implicit_invocation`. Zweihander is a declared dual-runtime
   marketplace and has **zero** of these — Codex gets no display metadata and no
   implicit-invocation policy. Directly aligned with our stated purpose.
3. **`disable-model-invocation` discipline.** They use it on 13/22. We use it once,
   and set to `false`. Our expensive flows (`yolo-push`, `resume-tailoring`,
   `init-workspace`, `submit-job-application`, `run-skill-generator`) are all
   currently model-reachable.
4. **A router skill.** `ask-matt` exists purely for discoverability. We have 53
   skills across 14 plugins with no entry point.
5. **README split by invocation mode.** `skills/engineering/README.md` lists
   "User-invoked" and "Model-invoked" separately. Plus `scripts/list-skills.sh`.
6. **Thin entrypoint over primitive.** `grill-me` (user-invoked) → `grilling`
   (model-invokable). Lets one behaviour be both a slash command and an auto-trigger.

### Bucket D — substantial new capability, heavy adaptation

Ordered by value-to-effort. All four depend on the Bucket C #1 config contract.

| Their skill | Why it is new for us | Blocking dependency |
|---|---|---|
| `to-tickets` | Tracer-bullet tickets carrying explicit blocking edges, as native tracker links or local files. Closest we have is `work-session-tools:task-management` (in-session only) | setup contract |
| `triage` | Issue/PR state machine with five canonical roles. We have no triage anything | setup contract (label vocabulary) |
| `implement` | Spec/tickets → build, driving `/tdd` at agreed seams, closing with `/code-review` | `tdd`, `code-review` |
| `improve-codebase-architecture` | Scan → HTML report → grill the chosen finding. Pairs with our `render-diff-html` | `codebase-design`, `domain-modeling`, `grilling` |
| `domain-modeling` | Ubiquitous language + ADRs + `CONTEXT.md`, with `ADR-FORMAT.md` / `CONTEXT-FORMAT.md` | none |
| `wayfinder` | Multi-session planning as a tracker map of decision tickets. Most novel, most expensive | setup contract + `grilling` + `research` + `prototype` |

## 5. Proposed waves

**Wave 0 — legal and scaffolding.** MIT requires attribution. Add
`third_party/mattpocock-skills-LICENSE.txt`, entries in
`third_party/THIRD_PARTY_NOTICES.md` and `ACKNOWLEDGEMENTS.md`, matching the
existing `superpowers` / `hermes-agent` pattern. Decide plugin placement (below).

**Wave 1 — Bucket A, free wins.** Six standalone skills, no dependency untangling.
Manifest + marketplace + README updates per `CLAUDE.md`, version bump via
`version-bumper`.

**Wave 2 — Bucket C, the patterns.** Highest leverage, and it unblocks Wave 4.
Order: `agents/openai.yaml` backfill (mechanical, 53 files) → `disable-model-invocation`
audit → `setup-dev-workflow` config skill → router skill → README/script conventions.

**Wave 3 — Bucket B, the merges.** Requires reading both sides in full. Per skill,
decide: absorb their reference docs, adopt their structure, or leave ours alone.

**Wave 4 — Bucket D, the new flows.** `domain-modeling` first (no deps), then
`to-tickets` → `triage` → `implement`, then `improve-codebase-architecture`, then
`wayfinder` last.

### Plugin placement sketch

| Target plugin | Incoming |
|---|---|
| `dev-workflow` (existing) | `resolving-merge-conflicts`, `setup-dev-workflow`, `implement` |
| `work-session-tools` (existing) | `grilling`, `grill-me`, `handoff`, `teach` |
| `ai-assistant-ops` (existing) | `writing-great-skills` (merge into `improve-skill`) |
| `research` (existing) | `research` investigation loop, `domain-modeling` |
| new: `engineering-design` | `codebase-design`, `prototype`, `improve-codebase-architecture` |
| new: `issue-flow` | `to-spec`, `to-tickets`, `triage`, `wayfinder` |

Two new plugins keeps the tracker-coupled flows (which all share the setup
contract) behind one install boundary, so cherry-picking one of them without the
label vocabulary is not possible.

## 6. Open questions for the next pass

1. Does `setup-matt-pocock-skills` write to `docs/agents/` in a shape that fits our
   `AGENTS.md` + sibling `CLAUDE.md` convention?
2. `ask-matt` is a router over *one* repo's skills. Does a Zweihander router live at
   the marketplace level, or one per plugin?
3. `grilling` vs `spec-interview` vs `interview` vs `spec-contradiction-hunter` —
   four interrogation skills after the merge. Which survive?
4. Their skills assume a `.scratch/` directory for the local-tracker mode. Compatible
   with our `.gitignore`?
