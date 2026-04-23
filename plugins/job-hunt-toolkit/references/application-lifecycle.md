# Application Lifecycle

End-to-end flow from spotting a JD to signing an offer.

## Stage 0: Workspace exists

Run once. Never again unless you wipe and restart.

- `/job-hunt-toolkit:init-workspace` — creates folder structure, generates docs, initializes git.
- Drop your master HTML CV in the root.
- Run `/job-hunt-toolkit:export-pdf` to create the master PDF.
- Commit: `chore: initialize workspace with master CV`.

## Stage 1: New application

Triggered by finding a JD worth applying to.

1. `/job-hunt-toolkit:new-application <company-slug>` (e.g. `acme_robotics`).
2. Paste or link the JD — saved to `<company>/job_description.md`.
3. `company.md` scaffolded with frontmatter — fill in snapshot, stack, comp band.
4. Master HTML copied into `<company>/` as the tailoring starting point.
5. **Decision point**: tailor now, or research first?

## Stage 2: Research (optional but recommended)

- Company mission / values / recent news (check engineering blog, last 3 PR announcements, LinkedIn).
- Role archetype (what does this role look like at similar companies?).
- Comp benchmarking (levels.fyi, Glassdoor — cross-reference).
- Red flags (layoffs, funding issues, Glassdoor scores < 3.0).

Capture findings in `company.md`. This context drives tailoring decisions.

## Stage 3: Tailor

- Invoke `resume-tailoring` skill: research → template → optional discovery → assembly → generation.
- Edit HTML in `<company>/<name>_<role>_CV.html`.
- `resume-tailoring` enforces truth-preserving optimization: reframe, emphasize, reorder — never invent.
- Checkpoint with user at each phase (success profile, template, coverage).

## Stage 4: Export

- `/job-hunt-toolkit:export-pdf` — HTML → PDF via headless Chromium.
- PDF written next to HTML with the same stem.
- Visual review: open the PDF, scan for layout breakage.

## Stage 5: Pre-send

**Mandatory before attaching.**

- `/job-hunt-toolkit:prepare-to-send` runs the full checklist:
  1. Filename sanity (no company tag, no spaces, matches `naming-rules.md`).
  2. `scrub-pdf-metadata` — strip Title/Author/Producer/CreationDate.
  3. Visible content scan (stray drafts, wrong company names in body, placeholders).
  4. HTML ↔ PDF parity.
  5. Git hygiene (both files staged, no secrets).

If any step fails, it fails loudly. Nothing goes out with warnings.

## Stage 6: Ship

- `git add <company>/<name>_<role>_CV.{html,pdf} <company>/company.md`
- `git commit -m "add: <company> — <role>"`
- Update `company.md` frontmatter: `status: applied`, `applied: <today>`.
- Attach the PDF to the application / email.

## Stage 7: Track

As the process moves, update `company.md`:

- `status: screening` after the recruiter reaches out
- `status: interview` before the first technical round
- Add `interview_notes.md` per round
- Add `questions_to_ask.md` for interviewers
- Add `followups.md` for thank-you drafts

Commit each update: `update: <company> — <what changed>`.

## Stage 8: Outcome

### Offer
- Capture comp + terms in `company.md` (commit only if user confirms it's safe to track).
- Update frontmatter: `status: offer`.
- If negotiating, keep `salary_notes.md` LOCAL (not committed unless user insists).

### Rejection
- Update `status: rejected`.
- Note the reason if they share one (feedback is gold).
- Move on — don't waste cycles mourning rejections.

### Withdraw
- Update `status: withdrew`, note why.

### Signed
- Update `status: signed`. Consider archiving the folder or tagging the repo.

## Anti-patterns

- **Don't tailor without researching first.** Generic tailoring is nearly as bad as no tailoring.
- **Don't send before running `prepare-to-send`.** Metadata leaks have killed callbacks.
- **Don't edit PDFs.** Edit HTML, regenerate.
- **Don't commit WIP per-company folders with half-filled `company.md`.** Either fill it or don't start the folder.
- **Don't apply to 50 places at once with the same CV.** Focus beats volume.
