# md-bloat-hunter — SPEC

## Problem

AI-generated markdown (skills, agents, plugin docs) accumulates token waste: restated content, verbose constructions, empty filler, multi-word definitions of terms that already exist as single words. These cost tokens and dilute attention — each added token lowers the relative weight of every previously seen token.

This skill audits MD files and produces concrete atomic rewrites that reduce tokens while preserving meaning. It does not refactor for aesthetics, validate style, or introduce abstractions.

## Core principles

- **DOTADIW.** Each detector hunts one shape of bloat.
- **Semantic preservation is non-negotiable.** A token saved by changing meaning is a regression.
- **LLM is not a linter.** Schema does not ask the LLM for things it's bad at: IDs, line numbers, token counts, timestamps.
- **Trust the simple path.** No config knobs, no concurrency caps, no abstraction for hypothetical needs.
- **Excerpt is truth.** Location is verbatim quoting, not line numbers.

## Architecture — 3-level dispatch

```
SKILL.md (top orchestrator)
   ├── file-orchestrator (one per file, parallel)
   │     ├── redundancy-detector
   │     ├── verbosity-pruner
   │     ├── filler-eliminator
   │     └── vocab-compressor
   ⋮  one file-orchestrator per file, all parallel
```

For N files at runtime: 1 top orchestrator + N file-orchestrators + 4N detectors, all in parallel. No queueing.

**Why two-level:** the top orchestrator's concern is fan-out + aggregation + gating + writing. The file-orchestrator's concern is producing a reduced finding list for one file. Each level does one thing.

## Detector taxonomy

| Specialist | Hunts | Finding shape |
|---|---|---|
| `redundancy-detector` | Within-file duplication; restated content (rule → example → summary saying the same thing) | 2+ locations + canonical form |
| `verbosity-pruner` | Wordiness in a span: preambles, passive voice, hedging, "it is important to note that" | 1 span, before → after |
| `filler-eliminator` | Pure deletes: empty connectives, restated headings, "designed to help you" intros | 1 span, delete-only |
| `vocab-compressor` | Multi-word phrase → precise term ("can be run multiple times safely with the same result" → "idempotent") | 1 phrase, before → after + equivalence justification |

The verbosity/vocab split is deliberate. Verbosity is mechanical ("fewer words for the same idea"). Vocab is semantic ("you used the definition; the term for it exists"). Different risk profile, different scrutiny.

Cross-file redundancy is **not** in v1. Each file is treated independently.

## Finding schema

**Source of truth:** `references/schema.json` (JSON Schema, draft 2020-12). The inline YAML below is a human-readable quick reference — when they disagree, `schema.json` wins.

Schema-Guided Reasoning order: `preliminary_analysis → identified_problem → proposal → estimated_risk`. The LLM fills fields in cognitive order: observe before classify, classify before propose, assess risk only after committing to a specific fix.

```yaml
SpecialistOutput:
  specialist: enum                  # "redundancy-detector" | "verbosity-pruner" | "filler-eliminator" | "vocab-compressor"
  file_path: str

  audit_calibration:                # outer SGR: characterize file before scanning
    observation: str                # 1-line file characterization, e.g. "20-line single-purpose skill"
    chosen_intensity: enum          # "minimal" | "standard" | "aggressive"
    reasoning: str                  # connects observation → intensity

  findings: list[Finding]           # may be empty

Finding:

  # --- SGR phase 1: preliminary_analysis (observe before judging) ---
  excerpt: str                      # verbatim quote from file
  context_before: str | null        # exact adjacent text before, ONLY if excerpt isn't unique in file
  context_after: str | null         # exact adjacent text after, same condition

  # --- SGR phase 2: identified_problem (classify the observation) ---
  type: enum                        # "redundancy" | "verbosity" | "filler" | "vocab"
  rationale: str                    # one-line WHY
  severity: enum                    # "critical" | "major" | "minor"

  # --- SGR phase 3: proposal (commit to a fix) ---
  action: enum                      # "delete" | "replace" | "restructure"
  new_text: str | null              # null when action="delete"
  justification: str | null         # REQUIRED for vocab swaps (defend equivalence)

  # --- SGR phase 4: estimated_risk (assess the proposal, not the original problem) ---
  semantic_risk: enum               # "none" | "low" | "medium" | "high"
  confidence: enum                  # "high" | "medium" | "low"
```

**Fields deliberately absent** (LLM is not a linter):
- `id` — top orchestrator assigns after collection
- `estimated_token_delta` — orchestrator tokenizes if needed
- `scanned_at` — orchestrator timestamps
- `specialist_version` — orchestrator already knows what it dispatched

## Output validation loop

Each detector validates its own output against `references/schema.json` before returning. Protocol:

1. Generate JSON output for the audited file.
2. Write to `/tmp/md-bloat-hunter/<run_id>/<file_hash>/<detector>.json`.
3. Run `jsonschema -i <output_path> references/schema.json`.
4. If validation fails, read the error and retry with self-correction.
5. Repeat steps 2–4 up to **3 attempts total**.
6. After the third attempt, return the output path regardless of validation status. **Do not fail the task.**

The file-orchestrator handles malformed output gracefully:
- JSON parse failure → skip this detector's contribution; log; continue with other detectors.
- Schema validation failure after retries → attempt to extract individually-valid findings; drop the rest.

This trade prefers degraded coverage over hard failure. A detector that hallucinates structure costs one detector's findings on one file, not the whole audit.

**Runtime dependency:** `jsonschema` CLI (e.g. `uv tool install jsonschema`). The top orchestrator verifies it's on PATH before dispatching and fails fast if missing.

## Calibration rubric

Each detector picks its own `chosen_intensity` per file using the SGR `audit_calibration` block. Shared rubric in `references/calibrate-hunger.md`:

- **minimal** — tight focused files (small, single-purpose). Flag only `critical` severity. Don't touch examples that make the skill clear. Don't restructure.
- **standard** — mid-sized adaptable files. Full passes; normal severity threshold.
- **aggressive** — sprawling files with many trigger paths. Flag aggressively; hunt cross-section duplication.

Trust the agent's characterization. No frontmatter opt-ins, no auto-detection heuristics.

## File-orchestrator: per-file reducer

After collecting four `SpecialistOutput` blocks for one file, the file-orchestrator resolves overlapping findings. Two specialists may flag overlapping spans. Three resolution shapes:

| Overlap shape | Resolution |
|---|---|
| Same action + similar `new_text` | Merge silently, present as one finding |
| Same action + meaningfully different `new_text` | Keep both as alternatives; AI marks recommended one |
| Different actions (e.g., `delete` vs `restructure`) | Keep as conflict; AI may recommend "skip both" |

"Meaningfully different" is decided by an LLM ask inside the file-orchestrator ("are these two rewrites materially the same?") rather than a tuned similarity threshold.

The file-orchestrator returns: one reduced finding list for its file.

## Top orchestrator: aggregation, gating, writing

After all file-orchestrators complete:

1. **Aggregate** — collect every reduced finding list into one ranked queue.
2. **Gate** — partition by `semantic_risk`:
   - `none` / `low` / `medium` → auto-apply
   - `high` → AskUserQuestion per finding with AI-recommended option
3. **Write** — apply each approved finding via the writer (below).
4. **Report** — summary of applied, skipped, and failed findings.

**Specialists are instructed: when in doubt about risk, round up.** False positives cost a click; false negatives change meaning silently. The entire safety story rests on this calibration discipline.

## Writer

For each finding, applied per file:
1. Read file content.
2. String-match `preliminary_analysis.excerpt` (with exact adjacent
   `context_before` / `context_after` if present) against the file.
3. Replace match with `proposal.new_text`, or delete the span if `proposal.action == "delete"`.
4. Write file back.

**Failure mode is hard error.** If excerpt is not found verbatim, the writer stops on that finding and reports. No partial application, no silent fallback. An unfindable excerpt is a hallucination, not a recoverable state.

**Finding ordering within a file:** apply in source order. If applying finding N invalidates finding M's excerpt (its quoted text changed), finding M fails loudly. The user re-runs to pick up shifted findings. No retry logic in v1.

**Reversibility:** the writer does not commit. v1 expects a clean git tree before running and relies on `git diff` for review and `git checkout` for undo.

## On-disk layout

```
~/.claude/my-marketplace/plugins/general-plugins/skills/md-bloat-hunter/
├── SKILL.md                          # top orchestrator entry point
├── SPEC.md                           # this file
├── agents/
│   ├── file-orchestrator.md          # per-file fan-out + reducer
│   ├── redundancy-detector.md
│   ├── verbosity-pruner.md
│   ├── filler-eliminator.md
│   └── vocab-compressor.md
└── references/
    ├── schema.json                   # JSON Schema (draft 2020-12) — source of truth, used by jsonschema CLI
    └── calibrate-hunger.md           # intensity rubric (shared)
```

Per-detector taxonomy lives **inside** each agent file (taxonomy, examples, what NOT to flag). `references/` holds only shared content. This mirrors the existing `claude-insights-hunter` pattern.

Promotion rule: if knowledge in an agent file starts being needed by another agent, extract to `references/`. Not before.

## Invocation

- **Slash command:** `/md-bloat-hunter [path]` — path optional; if omitted, the skill asks via AskUserQuestion.
- **Natural-language trigger:** "audit `<path>` for verbosity", "find bloat in `<file>`", etc.

Path may be a single file or a directory. The top orchestrator dispatches accordingly.

## Deferred to future iterations

v1 hook points are designed so these slot in cleanly without rework:

| Future feature | Where it slots |
|---|---|
| Separate semantic-preservation-validator agent | Between reducer aggregation and user gate; routes by `semantic_risk` |
| Trigger-preservation test for skill `description:` rewrites | Pre-commit guard in the writer; fires only when target has a `description:` frontmatter field |
| MUST/NEVER-rule extractor | Pre-commit guard in the writer; checks no hard rules were softened |
| Cross-file redundancy detection | Promote from per-file to top-orchestrator step; new top-level pass after per-file reduction |
| Token-delta computation | Top orchestrator tokenizes pre- and post-rewrite using a real tokenizer; reports actual savings |

None of these are in v1. Listed here so v1 architecture does not paint itself into a corner.

## Open risks

Honest uncertainties, not implementation blockers.

1. **Specialists may under-report `semantic_risk`.** If specialists mark medium-risk findings as low, those auto-apply with no gate. Mitigation: explicit "round up when in doubt" instruction in every detector's system prompt. Future mitigation: validator agent (see deferred slots).

2. **Excerpt collisions for short phrases.** A 5-word excerpt might appear
   multiple times in a long file. Exact adjacent `context_before` /
   `context_after` handle this when the specialist remembers to add them. The
   writer fails loudly on ambiguity, but ambiguity should be caught earlier.

3. **No undo built in.** v1 relies on git for reversibility. The user must audit on a clean tree.

4. **The 4-detector taxonomy may be incomplete.** Real audits will surface patterns that don't fit. New specialists drop in as new agent files — the architectural payoff for DOTADIW.

5. **Calibration discipline determines the entire safety surface.** Gating only on `high` means everything else auto-applies. The system inherits the honesty of its specialists.
