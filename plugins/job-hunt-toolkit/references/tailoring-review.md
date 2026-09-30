# Tailoring Change Review

Show what the user will send, word for word, and explain each change. Use this
review for CVs, cover letters, later revisions, and each job in a batch.

## Capture the Comparison Before Editing

Record the baseline path and preserve its current text before the first edit:

- For a new tailored CV, use the master or resume the user chose as its base.
  Cite other library documents as evidence for imported content.
- For a new tailored letter, use the golden letter or draft being adapted,
  as identified by workspace rules or the user. A CV is evidence, not an
  earlier version of a letter.
- For a revision, use the target document as it exists when this request
  starts, including uncommitted user edits. Do not substitute Git HEAD or the
  master for that working copy.
- For a letter written from scratch, say there is no previous letter and use
  an empty baseline. Show the whole new letter as additions.

Keep any baseline copies in a unique private directory under
`${ZWEIHANDER_TMP_DIR:-./.tmp/zweihander}/runs/<skill>/<run-id>/`.
Delete only this run's scratch copies after verifying and delivering the review.
If the original text cannot be recovered, disclose that the comparison is
unavailable; never reconstruct it from memory or invent a before version.

## Compare the Actual Text

After the final edit, compare the preserved baseline with the saved final
source. Include edits made during PDF and pre-send checks.

Extract reader-visible text from both sources. Omit Typst commands, styling,
comments, and layout-only changes; decode markup and normalize line wrapping.
Preserve every word, number, punctuation mark, visible label, and link target.
Do not translate, paraphrase, shorten, or replace quoted text with ellipses.
Verify extracted text against the source; check the rendered document when
macros or generated content make the visible text uncertain.

Cover every wording change, addition, deletion, and move, including titles,
summaries, bullets, skills, greetings, and closings. Show a move as removal and
addition of the same text, naming both locations. Keep unchanged passages out
except for context needed to locate a change. If only presentation changed,
state that the text is unchanged and describe the presentation change separately.

## Present the Review in Chat

Link the final files and identify the baseline first. Then group changes by
document and section, in document order. For each change:

1. Name the section or bullet so the user can locate it.
2. Show a fenced `diff` block: `-` contains the exact old text; `+` contains the
   exact saved replacement. For a small edit, show the complete affected
   sentence or bullet. Additions need only `+`; deletions need only `-`.
3. Put **Why** directly below that block. Name the specific JD requirement,
   user instruction, or editorial reason, and explain how this edit serves it.
   Cite the source and section or record supporting changed factual claims.

Use the user's language for explanations. Keep quoted document text in its
original language. A summary such as “emphasized production experience” or a
`Before | After | Why` table of paraphrases does not replace the diff. Include
the full review in chat, not only selected highlights or a link to a report.

Example with fictional input:

**Experience — API project**

```diff
- Built Python services and maintained internal dashboards.
+ Built Python services.
```

**Why:** The JD's Backend section prioritizes Python services. Removing the
dashboard clause keeps this bullet focused on that requirement. The original
API project bullet supports the retained claim; no new experience is claimed.

Finish with unresolved gaps and artifact checks, separately from the diff.
Before delivery, check that every changed passage appears in the review and
that each `-`/`+` passage matches its corresponding source.
