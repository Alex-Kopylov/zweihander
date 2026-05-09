# Marketplace Tools

Utility scripts for managing the local Claude Code skills marketplace.

## sync-anthropic-skills.sh

**Purpose**: Synchronize specific skills from [Anthropic's skills repository](https://github.com/anthropics/skills) into the local marketplace.

### What it does

This script maintains an efficient sync channel for 5 curated skills from Anthropic's official `anthropics/skills` repository:

**Document Processing** (`plugins/file-manager/`):
- `pdf` — PDF manipulation, form handling, OCR, metadata extraction
- `pptx` — PowerPoint creation, editing, slide generation
- `xlsx` — Excel spreadsheet creation, formulas, data manipulation
- `docx` — Word document creation, editing, tracked changes

**Utility** (`plugins/general-plugins/`):
- `skill-creator` — Framework for building and evaluating custom skills

### How it works

1. **First run**: Clones `github.com/anthropics/skills` with sparse checkout (only `example-skills/skills/` folder)
   - Uses `--filter=blob:none` for lightweight clone (~5MB instead of 100MB)
   - Configures git sparse-checkout to fetch only needed directories

2. **Subsequent runs**: Updates the upstream clone
   - `git fetch origin` + `git pull origin main`
   - Pulls latest changes from Anthropic's main branch

3. **Sync step**: For each skill:
   - Copies from `.upstream/example-skills/skills/{skill}/` to destination
   - Replaces entire skill folder (no merging)
   - Preserves LICENSE.txt, SKILL.md, scripts, documentation

4. **Output**: Lists what was synced and prompts for git commit

### Usage

```bash
# From anywhere, run:
~/.claude/my-marketplace/bin/sync-anthropic-skills.sh
```

Or from the marketplace root:
```bash
./bin/sync-anthropic-skills.sh
```

### Example output

```
🔄 Syncing skills from https://github.com/anthropics/skills.git
📦 Updating upstream repository...
📋 Syncing skills...
  ✓ pdf -> ~/.claude/my-marketplace/plugins/file-manager/skills/pdf
  ✓ pptx -> ~/.claude/my-marketplace/plugins/file-manager/skills/pptx
  ✓ xlsx -> ~/.claude/my-marketplace/plugins/file-manager/skills/xlsx
  ✓ docx -> ~/.claude/my-marketplace/plugins/file-manager/skills/docx
  ✓ skill-creator -> ~/.claude/my-marketplace/plugins/general-plugins/skills/skill-creator

✅ Sync complete!

Next steps:
  1. Review changes: git status
  2. Stage files: git add plugins/
  3. Commit: git commit -m 'sync: update skills from anthropics/skills'
```

### After syncing

```bash
# Review what changed
git -C ~/.claude/my-marketplace status

# Stage the skill updates
git -C ~/.claude/my-marketplace add plugins/

# Commit with conventional format
git -C ~/.claude/my-marketplace commit -m "sync: update skills from anthropics/skills"
```

### Design choices

**Sparse checkout** (not submodules):
- ✅ Lightweight — only syncs needed folders, not entire history
- ✅ Simple — no submodule complexity or configuration issues
- ✅ Controllable — explicit list of which skills to sync
- ✅ Mergeable — updated skills show as regular file changes in git

**Full replacement** (not merging):
- ✅ Simple — no conflict resolution needed
- ✅ Clean — removes abandoned files from old versions
- ✅ Explicit — you review diffs before committing
- ❌ No local modifications — if you edit a skill, sync will overwrite it

### Licensing notes

- **Document skills** (pdf, pptx, xlsx, docx): Source-available under Anthropic proprietary license
  - See `LICENSE.txt` in each skill folder
  - Provided for reference and educational purposes
  
- **skill-creator**: Apache 2.0 open source
  - Fully redistributable and modifiable
  - See `LICENSE.txt` in skill-creator folder

Attribution: All skills are authored by Anthropic, PBC. See `plugins/file-manager/ATTRIBUTION.md` for details.

### Troubleshooting

**"Skill 'X' not found in upstream"**
- The skill may have been renamed or removed in Anthropic's repository
- Check [github.com/anthropics/skills/tree/main/example-skills/skills](https://github.com/anthropics/skills/tree/main/example-skills/skills)
- Update `SKILLS_TO_SYNC` array in the script if needed

**Sync is slow**
- First sync is slower (cloning ~5MB)
- Subsequent syncs are fast (just `git pull`)
- If stuck, delete `.upstream/` and re-run (will re-clone)

**Merge conflicts after sync**
- This shouldn't happen (script replaces entire folders)
- If you get conflicts, you may have local modifications in a skill folder
- Review the skill's changes with `git diff plugins/file-manager/skills/pdf/` before committing

### Related files

- `.upstream/` — Shallow clone of github.com/anthropics/skills (git sparse-checkout)
- `plugins/file-manager/` — Document processing skills
- `plugins/general-plugins/` — Utility skills including skill-creator
- `plugins/*/ATTRIBUTION.md` — Source and licensing information
