# Multi-Job Resume Tailoring Workflow

## Overview

Handle 3-5 similar jobs efficiently by consolidating experience discovery while maintaining per-job research depth.

**Architecture:** Shared Discovery + Per-Job Tailoring

**Target Use Case:**
- Small batches (3-5 jobs)
- Moderately similar roles (60%+ requirement overlap)
- Continuous workflow (add jobs incrementally)

## Phase 0: Job Intake & Batch Initialization

**Goal:** Collect all job descriptions and initialize batch structure.

Present intake options:
1. Paste all JDs at once (recommended)
2. Provide one at a time
3. Provide URLs to fetch

For each job, collect:
- Job description (text or URL)
- Company name (extract from JD if possible)
- Role title (extract from JD if possible)
- Priority (high/medium/low, default: medium)
- Optional notes (e.g., "referral from X")

Assign job IDs: "job-1", "job-2", etc.

**Batch Directory Structure:**

```
resumes/batches/batch-{YYYY-MM-DD}-{slug}/
├── _batch_state.json
├── _aggregate_gaps.md
├── _discovered_experiences.md
└── (job directories created during per-job processing)
```

**Batch State JSON:**

```json
{
  "batch_id": "batch-{date}-{slug}",
  "created": "{timestamp}",
  "current_phase": "intake",
  "processing_mode": "interactive",
  "jobs": [
    {
      "job_id": "job-1",
      "company": "Company Name",
      "role": "Role Title",
      "priority": "high",
      "status": "pending",
      "requirements": [],
      "gaps": []
    }
  ],
  "discoveries": [],
  "aggregate_gaps": {}
}
```

Run standard library initialization once for the entire batch: scan resume directory for markdown files, parse each resume to extract roles/bullets/skills/education, build tagged experience database.

**Checkpoint:** Confirm batch is complete before proceeding.

## Phase 1: Aggregate Gap Analysis

**Goal:** Build unified gap list across all jobs for efficient discovery.

### Process

1. **Extract requirements from all JDs** - quick parsing for requirements, technical skills, soft skills, domain areas
2. **Match against library** - score each requirement using matching-strategies.md; flag as gap if confidence < 60%
3. **Build aggregate gap map** - deduplicate across jobs, prioritize:
   - Critical (3+ jobs): Priority 3
   - Important (2 jobs): Priority 2
   - Job-specific (1 job): Priority 1
4. **Generate `_aggregate_gaps.md`** with coverage summary per job, gaps by priority tier, and estimated discovery time

**Output to user:**
- Coverage summary per job (percentage)
- Aggregate gaps: X critical, Y important, Z job-specific
- Recommended discovery time estimate
- Options: start discovery / skip discovery / review gaps first

**Checkpoint:** User chooses next action.

## Phase 2: Shared Experience Discovery

**Goal:** Surface undocumented experiences across all gaps through single conversational session.

### Session Flow

1. Process gaps in priority order: critical first, then important, then job-specific
2. For each gap, provide multi-job context before branching interview (see branching-questions.md for templates)
3. Conduct branching interview using standard patterns
4. Capture each discovery to `_discovered_experiences.md` with:
   - Context, scope, metrics
   - Which jobs/gaps it addresses
   - Confidence improvement (before/after)
   - Bullet draft
5. Track coverage improvement in real-time - update user after each discovery
6. Present integration options per experience: add to library for all jobs / add selectively / skip
7. Enrich library with approved experiences

**Checkpoint:** User approves before moving to per-job processing.

## Phase 3: Per-Job Processing

**Goal:** Process each job independently through research/template/matching/generation using enriched library.

### Processing Modes

Ask user before starting:
- **INTERACTIVE** (default) - checkpoints at each step per job
- **EXPRESS** - auto-approve using best judgment, review all finals together

Recommendation: INTERACTIVE for first 1-2 jobs, then switch to EXPRESS.

### Per-Job Loop

For each pending job:

**3A: Research** - same depth as single-job Phase 1. Save `success_profile.md`. Checkpoint if INTERACTIVE.

**3B: Template Generation** - same as single-job Phase 2. Save `template.md`. Checkpoint if INTERACTIVE.

**3C: Content Matching** - same as single-job Phase 3, using enriched library. Save `content_mapping.md`. Checkpoint if INTERACTIVE.

**3D: Generation** - produce MD + DOCX + Report. No checkpoint, just generate.

Job directory structure: `job-{N}-{company-slug}/`

### Progress Tracking

After each job completes, report: quality metrics, jobs remaining, estimated time. Offer to continue, pause, or switch processing mode.

### Pause/Resume

Save batch state after each major milestone. Provide resume instructions with batch ID.

## Phase 4: Batch Finalization

**Goal:** Present all resumes for review and handle library update.

### Batch Summary

Generate `_batch_summary.md` with:
- Per-job status, coverage, key strengths, remaining gaps, file listings
- Discovery impact stats (experiences found, coverage improvement)
- Coverage metrics (average JD coverage, average direct matches)
- Gap resolution stats
- Interview prep recommendations
- Cover letter focus per job
- Application priority ranking based on coverage scores

### Review Options

1. **APPROVE ALL** - save all to library, rebuild indices
2. **REVIEW INDIVIDUALLY** - approve/revise each job separately
3. **REVISE BATCH** - make cross-resume changes (e.g., "make all summaries shorter")
4. **SAVE WITHOUT LIBRARY UPDATE** - keep files, don't enrich library

## Incremental Batch Addition

Support adding new jobs to completed batches.

### Process

1. Load existing batch state
2. Intake new jobs (continue job numbering)
3. Run **incremental** gap analysis - only check new requirements not already covered
4. Run **incremental** discovery - only ask about NEW gaps (skip previously answered)
5. Process new jobs through per-job loop
6. Update batch summary with new jobs and stats

### Time Savings

- Avoid re-asking previously discovered experiences
- Skip gaps already covered by existing library enrichment
- Typical: ~33% time savings vs starting from scratch

## Edge Cases

### Jobs Are More Diverse Than Expected

If <40% gap overlap between jobs, recommend splitting into sub-batches by similarity. Offer: split into batches / continue unified / remove dissimilar jobs.

### Discovery Only Addresses Some Jobs

If an experience is cloud-specific (e.g., Azure only), tag it for specific jobs. Offer to explore broader concepts that transfer across platforms.

### One Job's Research Fails

Fall back to JD-only analysis for that job. Do not block other jobs. Offer: continue with JD-only / skip job / user provides context / remove job.

### Add/Remove Jobs Mid-Process

**Add:** Run quick gap check, incremental discovery if needed, then process.
**Remove:** Keep discovered experiences in library. Archive (don't delete) job files.

### Batch Processing Interrupted

Auto-save state after each milestone. On resume, pick up exactly where left off.

### No Gaps Found

Skip discovery. Proceed directly to per-job processing with existing library.

### Library Update Conflicts (Mixed Approval)

Support individual approval: add approved jobs now, defer pending jobs, revisit rejected jobs.

## Error Recovery Principles

1. Never lose progress - auto-save batch state frequently
2. Partial success is success - some jobs completing is better than none
3. Transparent failures - always explain what went wrong and present options
4. Graceful degradation - fall back to JD-only, single-job mode, or skip as needed
5. User control - always provide options, never force a path
