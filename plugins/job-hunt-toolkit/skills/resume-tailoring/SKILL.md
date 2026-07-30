---
name: resume-tailoring
version: 1.0.0
description: "Tailor my resume, customize CV for a job, optimize resume for a role, update resume for a position, rewrite resume for this JD, generate a targeted CV, fit my resume to this posting, tailor CV for job description, batch resumes for multiple jobs, multi-job resume tailoring."
argument-hint: <job description text or URL>
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Resume Tailoring

Generate tailored, multi-format resumes optimized for specific job descriptions while maintaining factual integrity. Use existing evidence first and ask targeted discovery questions only when critical facts are missing.

**Core Principle:** Truth-preserving optimization - maximize fit without fabricating experience. Reframe and emphasize relevant aspects; never invent work history.

## References

- **`references/research-prompts.md`** - JD parsing templates, company research queries, role benchmarking strategy, success profile synthesis
- **`references/matching-strategies.md`** - Weighted scoring formula (Direct 40%, Transferable 30%, Adjacent 20%, Impact 10%), confidence bands, reframing strategies, gap handling options
- **`references/branching-questions.md`** - Technical/soft-skill/recent-work question trees, branching logic, multi-job context framing, capture structure
- **`references/multi-job-workflow.md`** - Batch initialization, aggregate gap analysis, shared discovery, per-job processing, incremental batch addition, pause/resume support

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Requirements

**From user:**
1. Job description (text or URL)
2. Resume library location (defaults to `<workspace>/library/` where workspace = `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}`)

**Sub-skill dependencies:**
- `job-hunt-toolkit:export-pdf` - HTML → PDF export via `${PLUGIN_ROOT}/skills/export-pdf/scripts/html-to-pdf.sh`

## Workflow

### Multi-Job Detection

Before starting, check if the user provides 2+ JDs, mentions "multiple jobs", "batch", "several positions", or lists multiple company/role pairs. If detected, follow `references/multi-job-workflow.md`. Otherwise proceed with the single-job workflow below.

### Phase 0: Library Initialization

1. Locate resume library directory (user-provided or `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/library/`)
2. Scan for HTML and markdown files
3. Parse each resume: extract roles, bullets, skills, education
4. Build in-memory experience database - tag each bullet with themes, metrics, keywords, and source resume
5. Record library size for the final report

### Phase 1: Research

Follow templates in `references/research-prompts.md`.

1. Parse JD: extract requirements (must-have vs nice-to-have), keywords, implicit preferences, red flags, role archetype
2. Research company: mission, values, culture, recent news, engineering blog
3. Benchmark role: LinkedIn profiles of similar role holders, common backgrounds, terminology
4. Synthesize into a **success profile**: core requirements, valued capabilities, cultural fit signals, narrative themes, terminology map, risk factors

### Phase 2: Template Generation

1. Analyze library for role archetypes, experience clusters, career progression
2. Consolidate same-company roles when responsibilities overlap; keep roles separate for different companies or dramatically different scopes
3. Choose truthful title framing that emphasizes aspects most relevant to the target role
4. Generate template skeleton with bullet allocation per role (more bullets to more relevant roles), section ordering, and guidance per slot

### Phase 3: Experience Discovery (Optional)

After template generation, trigger this phase for critical-requirement gaps below 60% confidence.

1. Record identified gaps with current confidence levels
2. Search the existing library for overlooked direct, transferable, or adjacent evidence
3. Ask a targeted question only when a critical gap cannot be handled truthfully by omission or disclosure; use patterns from `references/branching-questions.md`:
   - Start with open probe (technical, soft skill, or recent work)
   - Branch based on answer: YES/direct -> deep dive; INDIRECT -> explore transferability; ADJACENT -> explore related; PERSONAL -> assess recency; NO -> try broader category or move on
4. Capture each discovery immediately: context, scope, metrics, bullet draft, which gaps it addresses
5. Integrate confirmed evidence into the tailored resume and record its source; do not update the master library unless requested

### Phase 4: Assembly

Follow scoring from `references/matching-strategies.md`.

1. For each template slot, score all candidate bullets:
   - Overall = (Direct x 0.4) + (Transferable x 0.3) + (Adjacent x 0.2) + (Impact x 0.1)
2. Rank by score and assign confidence bands: DIRECT (90-100%), TRANSFERABLE (75-89%), ADJACENT (60-74%), WEAK/GAP (<60%)
3. Select the highest-scoring truthful match per slot and record its source
4. Apply reframing where needed (keyword alignment, emphasis shift, abstraction level, scale emphasis) - show before/after transparently
5. Handle gaps (<60%) with the safest available option: reframe supported evidence, flag for cover letter, omit the slot, or use the best available evidence with disclosure

### Phase 5: Generation

Output directory: `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/<company>/`
Filename format: `<First>_<Last>_<Role>_CV.<ext>` — NO company name in the filename.

**Edit-guard:** If this skill needs to modify the master HTML at `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/<First>_<Last>_<Role>_CV.html`, ask the user for explicit confirmation before doing so.

1. **HTML:** Using the master CV template, compile mapped content and save it as `<First>_<Last>_<Role>_CV.html` in the company subfolder.
2. **PDF:** Invoke the `job-hunt-toolkit:export-pdf` skill for the generated HTML. Always use absolute paths.
3. **Review:** Present the completed files, remaining gaps, and every substantive rewrite using `Before | After | Why`.

### Phase 6: Library Update

Keep tailored files in the company directory. Update the master library only when the user explicitly requested it; otherwise leave it unchanged and say so in the final summary.

## Error Handling

| Scenario | Action |
|----------|--------|
| Insufficient library (1-2 resumes) | Warn about limited matching; recommend discovery phase; proceed with available content |
| No good matches (<60% on critical requirement) | Use targeted discovery only for missing critical facts; otherwise reframe supported evidence, omit the slot, or disclose the gap |
| Research failures (WebSearch unavailable, sparse results) | Fall back to JD-only analysis and note the limitation |
| Vague JD | Record assumptions and proceed with best effort |
| Content exceeds page limit | Rank bullets by relevance, prune the lowest-scored content, and record the decision |
| PDF export failure | HTML is still saved; report error with exit code; user can use the `job-hunt-toolkit:export-pdf` skill separately |

## Hard Rules

- NEVER fabricate experience or inflate seniority beyond defensible
- Company names and dates MUST be exact
- Show every substantive reframe transparently with before/after, justification, and evidence
- Help articulate genuine experience; never create false experience

## Completion Check

- [ ] Company output directory exists
- [ ] HTML tailored to the target vacancy and role is saved in that directory
- [ ] PDF was generated from that HTML by the `job-hunt-toolkit:export-pdf` script; never create or edit PDF content directly
- [ ] Final response shows `Before | After | Why` for substantive changes
