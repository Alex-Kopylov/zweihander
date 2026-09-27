# Multi-Job Resume Tailoring Workflow

## Overview

Handle 3-5 similar jobs by consolidating experience discovery while preserving per-job research depth.

**Architecture:** Shared Discovery + Per-Job Tailoring

**Target Use Case:**
- Small batches (3-5 jobs)
- Moderately similar roles (60%+ requirement overlap)
- Continuous workflow (add jobs incrementally)

## Phase 0: Job Intake & Batch Initialization

Accept JDs together, individually, or as URLs.

For each job, collect:
- Job description (text or URL)
- Company name (extract from JD if possible)
- Role title (extract from JD if possible)
- Priority (high/medium/low, default: medium)
- Optional notes (e.g., "referral from X")

Assign job IDs: "job-1", "job-2", etc.

**Batch Directory Structure:**

```
${JOB_HUNT_WORKSPACE:-$HOME/Documents/job_seeking}/batches/batch-{YYYY-MM-DD}-{slug}/
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

Run single-job Phase 0 once for the entire batch.

## Phase 1: Aggregate Gap Analysis

### Process

1. **Extract requirements from all JDs** - quick parsing for requirements, technical skills, soft skills, domain areas
2. **Match against library** - score each requirement using matching-strategies.md; flag as gap if confidence < 60%
3. **Build aggregate gap map** - deduplicate across jobs, prioritize:
   - Critical (3+ jobs): Priority 3
   - Important (2 jobs): Priority 2
   - Job-specific (1 job): Priority 1
4. **Generate `_aggregate_gaps.md`** with coverage summary per job, gaps by priority tier, and estimated discovery time

**Record for final review:**
- Coverage summary per job (percentage)
- Aggregate gaps: X critical, Y important, Z job-specific
- Recommended discovery time estimate

## Phase 2: Shared Experience Discovery

### Session Flow

Run single-job Phase 3 once across the aggregate gaps, ordered critical, important, then job-specific. Record discoveries in `_discovered_experiences.md`, map them to affected jobs and gaps, track batch coverage improvements, and use confirmed evidence in each affected job's later tailoring.

## Phase 3: Per-Job Processing

### Per-Job Loop

For each pending job, run single-job Phases 1, 2, 4, and 5 with the enriched library. Save `success_profile.md`, `template.md`, and `content_mapping.md` as working artifacts.

Job directory structure: `job-{N}-{company-slug}/` (working scratch only; final outputs go to company subfolder in workspace root)

### Progress Tracking

Save progress after each job.

### Pause/Resume

Save batch state after each major milestone. Provide resume instructions with batch ID.

## Phase 4: Batch Finalization

### Batch Summary

Generate `_batch_summary.md` with:
- Per-job status, coverage, key strengths, remaining gaps, file listings
- Per-resume change review using `Before | After | Why | Evidence`
- Discovery impact stats (experiences found, coverage improvement)
- Coverage metrics (average JD coverage, average direct matches)
- Gap resolution stats
- Interview prep recommendations
- Cover letter focus per job
- Application priority ranking based on coverage scores

Present the completed batch and apply requested revisions. Leave the master library unchanged unless the user requested an update.

## Incremental Batch Addition

### Process

1. Load existing batch state
2. Intake new jobs (continue job numbering)
3. Run **incremental** gap analysis - only check new requirements not already covered
4. Run **incremental** discovery only for new, unanswered gaps
5. Process new jobs through per-job loop
6. Update batch summary with new jobs and stats

### Time Savings

- Avoid re-asking previously discovered experiences
- Skip gaps already covered by existing library enrichment
- Typical: ~33% time savings vs starting from scratch

## Edge Cases

### Jobs Are More Diverse Than Expected

If <40% gap overlap between jobs, split into sub-batches by similarity and report the decision.

### Discovery Only Addresses Some Jobs

Tag cloud-specific experience (e.g., Azure only) to relevant jobs; use broader transferable concepts only when supported.

### One Job's Research Fails

Fall back to JD-only analysis for that job and continue with the others.

### Add/Remove Jobs Mid-Process

**Add:** Run quick gap check, incremental discovery if needed, then process.
**Remove:** Keep discovered experiences in library. Archive (don't delete) job files.

### Batch Processing Interrupted

Auto-save state after each milestone. On resume, pick up exactly where left off.

### No Gaps Found

Skip discovery. Proceed directly to per-job processing with existing library.

### Library Update Conflicts (Mixed Approval)

If a library update was requested, add only confirmed experiences and leave disputed material out.

## Error Recovery Principles

1. Never lose progress - auto-save batch state frequently
2. Partial success is success - some jobs completing is better than none
3. Explain failures, apply the safest fallback, and include alternatives in the final review
4. Graceful degradation - fall back to JD-only, single-job mode, or skip as needed
