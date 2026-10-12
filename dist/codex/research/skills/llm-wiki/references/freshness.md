# Freshness: the main value signal

`freshness` is derived from `published` and today's date. A label picked from a fixed year drifts: what was fresh last year is recent now.

| Label | `published` | How to use |
|---|---|---|
| 🟢 `fresh` | this year or last year | current state of the field |
| 🟡 `recent` | two years ago | check for newer work by the same authors |
| ⚪️ `historical` | older | history only: "this is how it used to be done" |

`published` is the date of the newest source the page rests on; for a paper, the last arXiv version or the journal's online publication date. Recompute every label at lint time and correct the field where it drifted.
