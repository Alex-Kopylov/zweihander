---
name: resume-tailoring
version: 1.0.0
description: "Tailor my resume, customize CV for a job, optimize resume for a role, update resume for a position, rewrite resume for this JD, generate a targeted CV, fit my resume to this posting, tailor CV for job description, batch resumes for multiple jobs, multi-job resume tailoring."
argument-hint: <job description text or URL>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, AskUserQuestion, Skill, Agent
metadata:
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Resume Tailoring

Generate tailored, multi-format resumes optimized for specific job descriptions while maintaining factual integrity. Build resumes around the whole person by surfacing undocumented experiences through conversational discovery.

**Core Principle:** Truth-preserving optimization - maximize fit without fabricating experience. Reframe and emphasize relevant aspects; never invent work history.

## References

- **`references/research-prompts.md`** - JD parsing templates, company research queries, role benchmarking strategy, success profile synthesis
- **`references/matching-strategies.md`** - Weighted scoring formula (Direct 40%, Transferable 30%, Adjacent 20%, Impact 10%), confidence bands, reframing strategies, gap handling options
- **`references/branching-questions.md`** - Technical/soft-skill/recent-work question trees, branching logic, multi-job context framing, capture structure
- **`references/multi-job-workflow.md`** - Batch initialization, aggregate gap analysis, shared discovery, per-job processing, incremental batch addition, pause/resume support

## Harness Adaptation

Identify the active assistant harness before running this skill. When
harness-specific adaptation is needed for tool names or workflow surfaces, load
exactly one matching metadata-linked harness reference for the active harness
and skip every non-matching harness file. A harness with no matching metadata
link uses the shared Claude Code-baseline workflow as written. If no
harness-specific adaptation is needed, continue with the shared workflow as
written.

## Requirements

**From user:**
1. Job description (text or URL)
2. Resume library location (defaults to `<workspace>/library/` where workspace = `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}`)

**Sub-skill dependencies:**
- `export-pdf` - HTML → PDF export via `${PLUGIN_ROOT}/skills/export-pdf/scripts/html-to-pdf.sh`

## Workflow

### Multi-Job Detection

Before starting, check if the user provides 2+ JDs, mentions "multiple jobs", "batch", "several positions", or lists multiple company/role pairs. If detected, confirm with user and follow `references/multi-job-workflow.md`. Otherwise proceed with single-job workflow below.

### Phase 0: Library Initialization

1. Locate resume library directory (user-provided or `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/library/`)
2. Scan for HTML and markdown files using Glob
3. Parse each resume: extract roles, bullets, skills, education
4. Build in-memory experience database - tag each bullet with themes, metrics, keywords, and source resume
5. Announce library size to user

### Phase 1: Research

Follow templates in `references/research-prompts.md`.

1. Parse JD: extract requirements (must-have vs nice-to-have), keywords, implicit preferences, red flags, role archetype
2. Research company via WebSearch: mission, values, culture, recent news, engineering blog
3. Benchmark role via WebSearch/WebFetch: LinkedIn profiles of similar role holders, common backgrounds, terminology
4. Synthesize into a **success profile**: core requirements, valued capabilities, cultural fit signals, narrative themes, terminology map, risk factors

**Checkpoint:** Present success profile summary to user. Wait for confirmation before proceeding.

### Phase 2: Template Generation

1. Analyze library for role archetypes, experience clusters, career progression
2. Make role consolidation decisions (merge same-company roles when responsibilities overlap; keep separate when different companies or dramatically different scope)
3. Propose title reframing options - stay truthful, emphasize aspects most relevant to target role
4. Generate template skeleton with bullet allocation per role (more bullets to more relevant roles), section ordering, and guidance per slot

**Checkpoint:** Present template structure with consolidation decisions, title options, and bullet allocation. Wait for user approval.

### Phase 3: Experience Discovery (Optional)

Trigger after template approval if gaps identified (confidence < 60% on critical requirements).

1. Present identified gaps with current confidence levels
2. Offer structured brainstorming session (typically 10-15 minutes)
3. Conduct branching interview per gap using patterns from `references/branching-questions.md`:
   - Start with open probe (technical, soft skill, or recent work)
   - Branch based on answer: YES/direct -> deep dive; INDIRECT -> explore transferability; ADJACENT -> explore related; PERSONAL -> assess recency; NO -> try broader category or move on
4. Capture each discovery immediately: context, scope, metrics, bullet draft, which gaps it addresses
5. Present integration options per experience: add to current resume, add to library only, refine further, or discard

### Phase 4: Assembly

Follow scoring from `references/matching-strategies.md`.

1. For each template slot, score all candidate bullets:
   - Overall = (Direct x 0.4) + (Transferable x 0.3) + (Adjacent x 0.2) + (Impact x 0.1)
2. Rank by score and assign confidence bands: DIRECT (90-100%), TRANSFERABLE (75-89%), ADJACENT (60-74%), WEAK/GAP (<60%)
3. Present top 3 matches per slot with analysis and source resume
4. Apply reframing where needed (keyword alignment, emphasis shift, abstraction level, scale emphasis) - show before/after transparently
5. Handle gaps (<60%): offer reframe, flag for cover letter, omit slot, or use best-available with disclosure

**Checkpoint:** Present coverage summary (direct/transferable/adjacent/gap percentages), reframings applied, gap recommendations. Wait for approval.

### Phase 5: Generation

Output directory: `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/<company>/`
Filename format: `<First>_<Last>_<Role>_CV.<ext>` — NO company name in the filename.

**Edit-guard:** If this skill needs to modify the master HTML at `${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/<First>_<Last>_<Role>_CV.html`, call `AskUserQuestion` for explicit confirmation before doing so.

1. **HTML:** Compile mapped content into a tailored HTML file following the master CV's template. Save as `<First>_<Last>_<Role>_CV.html` inside the company subfolder.
2. **PDF:** Run the export-pdf skill:
   ```
   bash "${PLUGIN_ROOT}/skills/export-pdf/scripts/html-to-pdf.sh" \
     "<workspace>/<company>/<First>_<Last>_<Role>_CV.html" \
     "<workspace>/<company>/<First>_<Last>_<Role>_CV.pdf"
   ```
   Always use absolute paths for both arguments.
3. **Report:** Generate metadata file with coverage stats, reframings, source resumes, gap analysis before/after, interview prep recommendations. Save as `<First>_<Last>_<Role>_CV_Report.md` inside the company subfolder.

Present files and quality metrics to user.

### Phase 6: Library Update

Present three options:
1. **Save to library** - move files, rebuild library database, preserve generation metadata
2. **Need revisions** - collect feedback, make changes, re-present
3. **Save without library update** - keep files in current location only

## Error Handling

| Scenario | Action |
|----------|--------|
| Insufficient library (1-2 resumes) | Warn about limited matching; recommend discovery phase; proceed with available content |
| No good matches (<60% on critical requirement) | Offer: run discovery, reframe adjacent, omit slot, note for cover letter |
| Research failures (WebSearch unavailable, sparse results) | Fall back to JD-only analysis; ask user for additional context |
| Vague JD | Flag missing areas; ask user for context; proceed with best-effort |
| Content exceeds page limit | Rank bullets by relevance; suggest pruning lowest-scored; let user decide |
| PDF export failure (html-to-pdf.sh non-zero exit) | HTML is still saved; report error with exit code; user can re-run export-pdf separately |

## Hard Rules

- NEVER fabricate experience or inflate seniority beyond defensible
- Company names and dates MUST be exact
- Show all reframings transparently with before/after and justification
- Every checkpoint requires user confirmation before proceeding
- Help articulate genuine experience; never create false experience
