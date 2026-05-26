# Build md-bloat-hunter skill (v1)

## Overview

Build the `md-bloat-hunter` skill: a Claude Code skill that audits markdown files (skills, agents, plugin docs) and produces concrete atomic rewrites that reduce tokens while preserving meaning. The skill uses a 3-level dispatch — one top orchestrator (SKILL.md), N file-orchestrators (one per audited file, all parallel), and 4 detector specialists per file-orchestrator (redundancy, verbosity, filler, vocab — also parallel).

Each detector follows Schema-Guided Reasoning order (observe → classify → propose → estimate risk), self-validates its output against `references/schema.json`, and emits findings the top orchestrator gates by `semantic_risk` before writing changes to disk.

## Context

- Skill location: `~/.claude/my-marketplace/plugins/general-plugins/skills/md-bloat-hunter/`
- Pre-existing artifacts:
  - `SPEC.md` — design spec, source of truth for this build
  - `references/schema.json` — JSON Schema (draft 2020-12) for `SpecialistOutput`, already in place; reviewed and refined as Task 1 of this plan
- Runtime dependency: `jsonschema` CLI on PATH (e.g. `uv tool install jsonschema`). The top orchestrator fails fast if missing.
- Reversibility model: writer does not commit; relies on a clean git tree + `git diff` for review and `git checkout` for undo.
- Out of v1 scope (per SPEC): cross-file redundancy, separate semantic-preservation-validator, trigger-preservation test, MUST/NEVER-rule extractor, token-delta computation. These have hook points reserved but no Task in this plan.
- Adopted from `SPEC.md` (free-form design spec, no source task-list).

### Reference materials (consult when this plan is ambiguous)

When a task description is unclear or under-specified, consult these source materials before guessing — they encode the reasoning this plan compresses away:

1. **Original design spec**: `~/.claude/my-marketplace/plugins/general-plugins/skills/md-bloat-hunter/SPEC.md` — the artifact this plan was derived from. Authoritative for architecture, taxonomy, schema shape, failure modes, and what's deliberately out of v1.
2. **Brainstorm conversation log**: `~/.claude/projects/-Users-jhonsmith/d1b3887a-115b-43e3-b816-41362bb9a527.jsonl` — the full conversation where this skill was brainstormed. SPEC.md is its resulting artifact; the log captures the reasoning, rejected alternatives, and tradeoffs that the SPEC condenses. Read with `jq -r 'select(.type=="user" or .type=="assistant") | .message.content[]?.text // .message.content' <path>` or similar to extract human-readable content.

When in doubt: re-read SPEC.md first (faster, denser); fall back to the brainstorm log only when SPEC.md is silent on the specific decision. Do not invent design choices these two artifacts already settled.

## Development Approach

- Testing approach: regular. Agent prompts are not unit-testable in the conventional sense; each Task uses schema validation + smoke runs on fixture MD files instead of a test suite.
- Complete each task fully before moving to the next.
- Update this plan when scope changes during implementation.
- **When a Task is ambiguous, do not guess.** Re-read `SPEC.md` and, if still unclear, the brainstorm log linked in Context above. Both were settled before this plan was written.

## Testing Strategy

- Each detector Task ends with: (1) hand-author one valid sample `SpecialistOutput` JSON for that detector and verify `jsonschema -i sample.json references/schema.json` succeeds; (2) smoke-run the detector via the Task tool on a small fixture MD file containing a known instance of the bloat shape and inspect the returned findings.
- File-orchestrator and top orchestrator Tasks end with an end-to-end smoke run on a fixture file/directory.
- Final acceptance Task re-runs every fixture and confirms `git diff` reverts cleanly.

## Progress Tracking

- Mark completed items with `[x]` immediately when done.
- Update plan if implementation deviates from original scope.

## Technical Details

**Detector taxonomy** (each lives as one agent file under `agents/`):

| Specialist | Hunts | Finding shape |
|---|---|---|
| `redundancy-detector` | Within-file duplication; restated content (rule → example → summary saying the same thing) | 2+ locations + canonical form |
| `verbosity-pruner` | Wordiness in a span: preambles, passive voice, hedging, "it is important to note that" | 1 span, before → after |
| `filler-eliminator` | Pure deletes: empty connectives, restated headings, "designed to help you" intros | 1 span, delete-only |
| `vocab-compressor` | Multi-word phrase → precise term ("can be run multiple times safely with the same result" → "idempotent") | 1 phrase, before → after + equivalence justification |

Cross-file redundancy is **not** in v1.

**Schema-Guided Reasoning field order per Finding**: `excerpt` (+ optional context) → `type` / `rationale` / `severity` → `action` / `new_text` / `justification` → `semantic_risk` / `confidence`. Agents fill fields in cognitive order: observe before classify, classify before propose, assess risk only after committing to a specific fix. Schema fields deliberately absent (LLM is not a linter): `id`, `estimated_token_delta`, `scanned_at`, `specialist_version`. Top orchestrator assigns these after collection.

**Output validation loop (each detector)**:
1. Generate JSON output for the audited file.
2. Write to `/tmp/md-bloat-hunter/<run_id>/<file_hash>/<detector>.json`.
3. Run `jsonschema -i <output_path> references/schema.json`.
4. If validation fails, read the error and retry with self-correction.
5. Repeat steps 2–4 up to **3 attempts total**.
6. After the third attempt, return the output path regardless of validation status. Do not fail the task.

**File-orchestrator overlap resolution** (after collecting 4 `SpecialistOutput` blocks):

| Overlap shape | Resolution |
|---|---|
| Same action + similar `new_text` | Merge silently, present as one finding |
| Same action + meaningfully different `new_text` | Keep both as alternatives; AI marks recommended one |
| Different actions (e.g., `delete` vs `restructure`) | Keep as conflict; AI may recommend "skip both" |

"Meaningfully different" decided by an LLM ask inside the file-orchestrator, not a tuned similarity threshold.

**Top orchestrator gating**: partition findings by `semantic_risk` — `none` / `low` / `medium` auto-apply; `high` triggers AskUserQuestion per finding with AI-recommended option. Specialists are instructed: when in doubt about risk, round up.

**Writer**: read file → string-match `excerpt` (with `context_before` / `context_after` if present) → replace with `new_text` or delete the span if `action == "delete"` → write file back. Hard error on excerpt-not-found (no partial application, no silent fallback). Findings within a file apply in source order; if applying finding N invalidates finding M's excerpt, finding M fails loudly and user re-runs.

**On-disk layout** (target state at end of plan):

```
~/.claude/my-marketplace/plugins/general-plugins/skills/md-bloat-hunter/
├── SKILL.md                          # top orchestrator entry point
├── SPEC.md                           # already present
├── agents/
│   ├── file-orchestrator.md          # per-file fan-out + reducer
│   ├── redundancy-detector.md
│   ├── verbosity-pruner.md
│   ├── filler-eliminator.md
│   └── vocab-compressor.md
└── references/
    ├── schema.json                   # already present; reviewed in Task 1
    └── calibrate-hunger.md           # intensity rubric (shared)
```

Per-detector taxonomy lives **inside** each agent file (taxonomy, examples, what NOT to flag). `references/` holds only shared content. Promotion rule: if agent-local knowledge starts being needed by another agent, extract to `references/`. Not before.

## Implementation Steps

### Task 1: Review and refine references/schema.json

- [x] Re-read existing `references/schema.json` against the SPEC's `Finding schema` section and confirm: SGR ordering reflected in property order, all 4 specialist enum values present, `justification` requirement noted (vocab swaps must defend equivalence), absent fields (id, estimated_token_delta, scanned_at, specialist_version) deliberately omitted
- [x] Hand-author one valid sample `SpecialistOutput` JSON covering all 4 detector types and run `jsonschema -i sample.json references/schema.json` — must validate
- [x] Hand-author a deliberately invalid sample (missing required field, wrong enum) and confirm `jsonschema` rejects it
- [x] Patch schema.json if gaps surface; otherwise leave it untouched and note "no changes needed" in the task notes

Task notes: patched `schema.json` to enforce non-empty `justification` for vocab findings, allow nullable context/justification fields per SPEC, and enforce `new_text: null` for delete actions.

### Task 2: Add references/calibrate-hunger.md (shared intensity rubric)

- [x] Write `references/calibrate-hunger.md` defining the three intensity levels per SPEC: `minimal` (tight focused files — flag only `critical` severity, don't touch clarifying examples, don't restructure), `standard` (mid-sized adaptable files — full passes, normal severity threshold), `aggressive` (sprawling files with many trigger paths — flag aggressively, hunt cross-section duplication)
- [x] Include the "trust the agent's characterization; no frontmatter opt-ins, no auto-detection heuristics" framing
- [x] Spot-check that the file reads as a rubric a detector can apply per-file, not as prose

### Task 3: Build agents/redundancy-detector.md

- [ ] Write the agent file: detector role (hunt within-file duplication; restated content where rule → example → summary all say the same thing), finding shape (2+ locations + canonical form)
- [ ] Embed redundancy taxonomy inline (restated rules, duplicated examples, summary-of-summary) with what-NOT-to-flag examples (legitimate emphasis, contrasting examples that look similar but differ)
- [ ] Reference `references/calibrate-hunger.md` for intensity selection via the `audit_calibration` block
- [ ] Embed the SGR-ordered output protocol: fill `audit_calibration` first; then for each finding, fill phase-1 (excerpt + optional context), phase-2 (type/rationale/severity), phase-3 (action/new_text), phase-4 (semantic_risk/confidence)
- [ ] Embed the "when in doubt about risk, round up" instruction
- [ ] Embed the output validation loop (3-attempt cap, write to /tmp path, jsonschema check, do not fail task after attempt 3)
- [ ] Smoke run: prepare a fixture MD file containing a clear restated rule and verify the detector emits a valid `SpecialistOutput` with at least one redundancy finding

### Task 4: Build agents/verbosity-pruner.md

- [ ] Write the agent file: detector role (wordiness in a span — fewer words for the same idea), finding shape (1 span, before → after)
- [ ] Embed verbosity taxonomy inline: preambles ("It is important to note that…"), passive voice where active is clearer, hedging ("might possibly"), padding clauses
- [ ] Embed what-NOT-to-flag examples (load-bearing hedging where the uncertainty matters; deliberate passive where the actor is irrelevant)
- [ ] Reference `references/calibrate-hunger.md`; embed SGR output protocol, "round up on risk", and 3-attempt validation loop
- [ ] Smoke run: fixture MD file with one obvious wordy span; verify a valid `SpecialistOutput` is produced

### Task 5: Build agents/filler-eliminator.md

- [ ] Write the agent file: detector role (pure deletes — span contributes nothing), finding shape (1 span, delete-only — `action: "delete"`, `new_text: null`)
- [ ] Embed filler taxonomy inline: empty connectives ("As we discussed above"), restated headings (heading text repeated as opening sentence), "designed to help you…" intros, transitional filler
- [ ] Embed what-NOT-to-flag examples (clarifying context that looks like filler but isn't; bridging sentences that aid flow)
- [ ] Reference `references/calibrate-hunger.md`; embed SGR output protocol, "round up on risk", and 3-attempt validation loop
- [ ] Smoke run: fixture MD file with one obvious filler span; verify a valid `SpecialistOutput` with `action: "delete"`

### Task 6: Build agents/vocab-compressor.md

- [ ] Write the agent file: detector role (multi-word phrase → precise term), finding shape (1 phrase, before → after + equivalence justification)
- [ ] Embed vocab examples inline: "can be run multiple times safely with the same result" → "idempotent"; "doesn't depend on any external state" → "pure"; "happens at the same time as" → "concurrent"
- [ ] Embed what-NOT-to-flag examples (domain readers may not know the term; the multi-word form clarifies on purpose)
- [ ] Embed the **`justification` is REQUIRED** rule for every vocab finding — the agent must defend equivalence in writing
- [ ] Reference `references/calibrate-hunger.md`; embed SGR output protocol, "round up on risk" (vocab is highest-risk specialist — calibrate accordingly), and 3-attempt validation loop
- [ ] Smoke run: fixture MD file with one obvious multi-word definition of a known single word; verify a valid `SpecialistOutput` with a non-null `justification`

### Task 7: Build agents/file-orchestrator.md

- [ ] Write the agent file: role (per-file fan-out + reducer for one MD file), input (one absolute file path), output (one reduced finding list)
- [ ] Dispatch the four detector agents in parallel via the Task tool for the input file; collect four `SpecialistOutput` blocks
- [ ] Handle malformed detector output gracefully: JSON parse failure → skip that detector, log, continue; schema validation failure after retries → attempt to extract individually-valid findings, drop the rest
- [ ] Apply the overlap resolution table from Technical Details: merge same-action-similar-text silently; keep meaningfully-different alternatives with a recommended one; flag different-action conflicts (may recommend "skip both")
- [ ] Use an inline LLM ask to decide "meaningfully different" rather than a similarity threshold
- [ ] Return one reduced finding list to caller (the top orchestrator)
- [ ] Smoke run: feed a fixture MD file containing one redundancy + one verbosity + one filler instance; verify all three findings come through the reducer with sensible severity/risk

### Task 8: Build SKILL.md (top orchestrator) — dispatch, gating, reporting

- [ ] Write `SKILL.md` with skill frontmatter (name `md-bloat-hunter`, description matching the natural-language triggers, and any required allowed-tools)
- [ ] Document the slash command form `/md-bloat-hunter [path]` and the natural-language trigger phrasing ("audit `<path>` for verbosity", "find bloat in `<file>`")
- [ ] Implement path handling: if argument omitted, AskUserQuestion for path; accept either a single file or a directory; when given a directory, enumerate `*.md` files inside (do not recurse silently — confirm scope first if many files)
- [ ] Verify `jsonschema` CLI is on PATH before dispatching; fail fast with install hint if missing
- [ ] Dispatch one `file-orchestrator` per input file via the Task tool, all in parallel; collect every reduced finding list into one ranked queue
- [ ] Gate findings by `semantic_risk`: `none` / `low` / `medium` route to auto-apply; `high` triggers AskUserQuestion per finding with the AI-recommended option labeled
- [ ] Hand approved findings to the writer (Task 9) in source order per file
- [ ] After writes finish, report applied / skipped / failed counts plus the file paths touched
- [ ] Smoke run: dispatch on a fixture directory with 2 MD files; verify per-file findings show up, auto-apply runs without prompting on low risk, and a forced-high-risk fixture triggers the gate

### Task 9: Implement the writer logic

- [ ] Implement file mutation inline within SKILL.md (or as a small helper section the orchestrator delegates to): read file content → string-match `excerpt` (with `context_before` / `context_after` if present) → replace match with `new_text` or delete the span if `action == "delete"` → write file back
- [ ] Apply findings within a file in source order
- [ ] Hard-error on excerpt-not-found: stop on that finding, report which finding failed and why, do NOT continue with later findings in that same file (per SPEC's "no partial application, no silent fallback")
- [ ] If applying finding N invalidates finding M's excerpt (M's quoted text changed), fail M loudly with a "re-run to pick up shifted findings" message
- [ ] No commit step; rely on git for reversibility (writer assumes user started on a clean tree)
- [ ] Smoke run: hand-craft a finding whose excerpt is not in the file and verify the writer fails loudly without touching anything; then hand-craft a valid finding and verify the edit lands correctly with `git diff` showing exactly the proposed change

### Task 10: Register skill in plugin manifest and bump version

- [ ] Add the skill to the `general-plugins` plugin manifest at `~/.claude/my-marketplace/plugins/general-plugins/.claude-plugin/plugin.json` so the marketplace exposes `md-bloat-hunter`
- [ ] Bump the plugin version per CLAUDE.md release rules ("Always bump the version in `plugin.json` when adding new skills, agents, or commands")
- [ ] Spot-check that `/md-bloat-hunter` appears in the available-skills list after a reload and the natural-language trigger resolves

### Task 11: Verify acceptance criteria

- [ ] On a clean git tree, run the skill end-to-end on one fixture MD file containing a deliberate mix of all 4 bloat shapes; confirm findings appear, auto-apply runs, high-risk gating triggers AskUserQuestion, and the writer produces a `git diff` matching the proposed changes
- [ ] Run the skill on a known-tight MD file (e.g. a short single-purpose skill) and confirm `audit_calibration` chooses `minimal` and total finding count is low or zero
- [ ] Run `git checkout .` after the audit and verify all changes revert cleanly (reversibility story holds)
- [ ] Validate one real-world `SpecialistOutput` from a detector against `references/schema.json` via `jsonschema -i <path> references/schema.json` and confirm it passes
- [ ] Re-read SPEC.md's "Deferred to future iterations" table and confirm none of those items leaked into v1
- [ ] Spot-check that no hard-coded magic numbers, retry frameworks, session managers, or config systems were introduced (per SPEC's "Trust the simple path")

## Post-Completion

*Items requiring manual intervention — no checkboxes, informational only.*

- Commit and push are deliberately out of scope for this plan. Run them manually once acceptance criteria are met.
- If new bloat shapes surface during real-world use that don't fit the 4-detector taxonomy, add a new agent file under `agents/` rather than bending an existing one (per SPEC's DOTADIW principle).
- Future work hook points already documented in SPEC.md's "Deferred to future iterations" table — do not start any of them as part of this plan.
