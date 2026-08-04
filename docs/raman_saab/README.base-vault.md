---
title: "About this vault"
note: "Deliberately untagged — the Bases filter on tag `raman-saab`, so this meta note stays out of the tables it describes."
---
# About this vault

`docs/raman_saab/` is an Obsidian vault. Two `.base` files turn the 36 doctrine and
decision documents into queryable tables:

| Base | What it is for |
|---|---|
| `Doctrine Library.base` | All 36 docs. Grouped by topic; views for measured results, design/intent, recently touched, and a card gallery. |
| `Validation Evidence.base` | The `topic: validation` subset — the project's measured-truth axis read as one body. |

Open either file in Obsidian. Nothing outside this folder is affected, and no prose was
edited: frontmatter was prepended to each document and nothing was removed (verifiable as
`36 files changed, 324 insertions(+)` with zero deletions).

## Which frontmatter fields are facts, and which are judgement

This distinction matters in this corpus more than most, so it is stated plainly.

**Extracted from the document itself — factual:**

- `title` — the document's own H1, with a trailing `(YYYY-MM-DD)` stripped.
- `updated` — the latest ISO date appearing anywhere in the document; falls back to file
  mtime for the six documents that carry no date.
- `words` — a word count.

**Assigned classification — my judgement, not a claim the documents make:**

- `kind` — `analysis` / `spec` / `record` / `plan` / `reference` / `worksheet` / `guide`.
- `topic` — `validation` / `doctrine` / `process` / `corpus` / `llm` / `report`.
- `measured` — whether the document reports EMPIRICAL measurements rather than design or
  intent. 15 of 36 are `true`.

Disagree with any of these and edit the frontmatter; the Bases pick it up immediately.

## There is deliberately no `status` field

The obvious field to want is `status: open | closed | frozen`. It is missing on purpose.

Grepping for those markers returns whichever of them appear anywhere in a document's body,
so `DOCTRINE_BACKLOG.md` and `PROGRESS_LOG.md` each match *all seven at once* — they are
logs that enumerate items in every state. There is no reliable document-level status to
extract, and assigning one per document by eye would be invention. In a corpus whose entire
premise is measuring honestly and reporting both axes rather than the flattering one, a
fabricated status column would be exactly the wrong artefact.

If a real status is wanted, the honest route is to write it into each document by hand, and
the Bases will surface it the moment the field exists.
