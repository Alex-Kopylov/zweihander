# Calibrate Hunger

Use this rubric before scanning a markdown file.

Trust the detector's per-file characterization. Do not require frontmatter
opt-ins, configuration flags, or auto-detection heuristics.

## Intensity Levels

### minimal

Use for tight, focused files that are small and single-purpose.

- Flag only `critical` severity findings.
- Do not touch examples that make the skill, agent, or document clearer.
- Do not restructure sections.
- Prefer returning no findings over shaving language that carries intent,
  tone, trigger behavior, or operational clarity.

### standard

Use for mid-sized adaptable files with enough room for normal cleanup.

- Run the detector's full pass.
- Apply the normal severity threshold for that detector.
- Flag clear redundancy, verbosity, filler, or vocabulary compression
  opportunities when the proposed rewrite preserves meaning.
- Keep clarifying examples, explicit safety notes, and trigger-preserving
  phrasing unless they are clearly bloated.

### aggressive

Use for sprawling files with many trigger paths, repeated workflows, or
cross-section repetition.

- Flag aggressively within the detector's specialty.
- Hunt cross-section duplication inside the same file.
- Prefer canonical wording when multiple sections restate the same rule.
- Still preserve meaning, trigger behavior, safety constraints, and required
  procedural detail; aggressive does not mean speculative.

## Detector Contract

- Choose exactly one intensity for the current file or closure.
- Apply the chosen intensity consistently to every finding in that detector's
  output.
- When the output has an `audit_calibration` block, put the characterization
  in `observation`, the intensity in `chosen_intensity`, and the
  observation-to-intensity reasoning in `reasoning`.
- In a `.md.j2` template, Jinja syntax (`{{ ... }}`, `{% ... %}`,
  `{# ... #}`) is opaque: no `excerpt` or `new_text` may contain, cut into, or
  add it; context fields may quote it. Text in different branches of one
  conditional never renders together, so it is not redundant.
