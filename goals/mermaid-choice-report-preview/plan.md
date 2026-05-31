# Mermaid Choice Report Preview Plan

## Solution Approach

Update `plugins/mermaid-diagrams/skills/mermaid/assets/choice_report_template.html` from a single-block carousel into a normal scrollable review page that renders every block in document flow, keeps keyboard navigation as scroll-jump behavior, and adds per-option fullscreen preview. Keep generated per-diagram examples only in the temporary local audit page used for development, not in `SKILL.md` or runtime agent instructions.

Update Mermaid plugin docs so the main skill and README say generated diagrams are linted before presentation and syntax errors are fixed and relinted when possible.

## Ordered Steps

1. Update runtime documentation wording.
   - Files: `plugins/mermaid-diagrams/README.md`, `plugins/mermaid-diagrams/plugin_maintenance/templates/readme.md`, `plugins/mermaid-diagrams/skills/mermaid/SKILL.md`, `plugins/mermaid-diagrams/plugin_maintenance/templates/mermaid_skill.md`.
   - Change the notes and linting language from "runs linter before presenting" to "runs linter, fixes Mermaid syntax errors when possible, and relints before presenting".
   - Verification: `rg` should find no stale wording that implies lint failures are merely reported without a fix attempt.

2. Rework the choice report HTML structure.
   - File: `plugins/mermaid-diagrams/skills/mermaid/assets/choice_report_template.html`.
   - Render one `.block-section` per source block in normal page flow.
   - Preserve the visual two-column source/diagram layout per block.
   - Keep the top submit and stat controls visible as normal page content, not a viewport-trapping fixed carousel.
   - Verification: browser smoke test confirms all data blocks exist as DOM sections and document height exceeds viewport for multi-block audit data.

3. Add stats and decision semantics.
   - File: `choice_report_template.html`.
   - Track approved option count, rejected option count, options with notes, total blocks, and current block position.
   - Left/right arrows update the currently selected option and immediately refresh stats.
   - Multiple options in the same source block remain independently approvable.
   - Verification: Playwright keyboard test approves two options in one block, rejects another option, edits notes, and checks counters.

4. Add wrapping scroll-jump navigation.
   - File: `choice_report_template.html`.
   - Up/down arrows move to previous/next block, wrap at the edges, and call `scrollIntoView` on the selected block.
   - Verification: Playwright starts at first block, presses ArrowUp and lands on the final block; presses ArrowDown and lands on first block; checks viewport scroll position changes.

5. Add Mermaid preview controls.
   - File: `choice_report_template.html`.
   - Add a fullscreen button that opens the same diagram in a fullscreen dialog/overlay.
   - Do not implement zoom, reset, fit-to-panel, or code-toggle controls because the detailed preview-control answer selected fullscreen only.
   - Verification: Playwright opens fullscreen, verifies SVG or fallback code is present, then closes fullscreen.

6. Update submit payload behavior.
   - File: `choice_report_template.html`.
   - Output JSON with each block code, APPROVE/REGECT status per option, optional notes, and aggregate stats.
   - Treat still-pending options as approved by default when a general note is submitted and the option was not explicitly rejected, matching the accepted fact.
   - Verification: Playwright submits after mixed statuses and confirms JSON includes code, status, notes, and stats.

7. Regenerate and present the local audit page.
   - Generated files outside source tree: `/tmp/mermaid-choice-audit/index.html`, `/tmp/mermaid-choice-audit/choice-report-data.json`.
   - Use one block per supported diagram type and keep lint status visible only in this dev/test page.
   - Start a local server on an available localhost port and report the URL.
   - Verification: `mmdc --version` is `11.15.0`, generated audit data has 30 blocks, and browser smoke test confirms first rendered diagram, keyboard navigation, and fullscreen.

## Verification Commands

- `jq empty .agents/plugins/marketplace.json .claude-plugin/marketplace.json`
- `find plugins -path '*/plugin.json' -print0 | xargs -0 jq empty`
- `git diff --check`
- `mmdc --version`
- Render the sample Mermaid from `choice_report_template.html` with `mmdc`.
- Playwright smoke tests through the served audit URL for stats, keyboard navigation, wrapping behavior, fullscreen, submit JSON, and mobile overflow.

## Risks And Open Questions

- Browser Mermaid rendering can support a different diagram set than local `mmdc`; audit data must keep lint status visible so failures are not hidden.
- The accepted fact uses `REGECT` spelling. Preserve the submitted status wording in JSON if that is what downstream tooling expects, while keeping visible button text as `Reject` unless explicitly changed.
- The local audit page is a dev/test artifact only. Do not add generated per-diagram examples to `SKILL.md`, agent instructions, plugin manifests, or runtime docs.
