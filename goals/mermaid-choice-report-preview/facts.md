# Facts

- The choice report displays live counts for approved options, rejected options, options with notes, total blocks, and the current block position.
- Left and right arrow keys reject and approve the currently focused Mermaid option, and those decisions update the stats immediately.
- Up and down arrow keys jump to the previous and next source block, wrap from first to last and last to first, and scroll the page to the selected block.
- The report is a normal scrollable page with block sections in the document flow, not a fixed carousel that traps the viewport.
- A source text block can contain multiple Mermaid options, and multiple options for the same block can be approved at the same time.
- Each Mermaid preview can open in a fullscreen view with the same diagram
- Submitting the report outputs JSON containing each block code, APPROVE/REGECT status (if not REGECT per item but general feedback submitted - APPROVE by default, considering an optional note), optional notes. So the other may pick it up and write those mermaid diagrms.
- The main Mermaid skill and README state that generated diagrams are linted before presentation and that Mermaid syntax errors are fixed and relinted when possible.
- The local audit page uses examples for every supported diagram type and keeps lint status visible for each option. BUT ONLY DURING DEV or TEST stages.

Real SKILL.md and agents/* MUST NOT produce examples. We do it right now solely for development porpouses.
