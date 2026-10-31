# Engine-blind label review: what did B. V. Raman conclude?

You are an independent reviewer. For each ITEM in your packet, read B. V. Raman's printed text and record what Raman himself CONCLUDED about one matter (one house) of one native.

## Files you may read (and nothing else)
- Your packet: given in your task message. Each item starts with a line `######## ITEM Lxx | book | chart name | born | HOUSE n | MATTER: x | cited: WORK:line`. The cited passage follows, shown with 60 lines of context on each side.
- If the conclusion is not inside that window, you may search the full book text and read more of it:
  - HTJAH-I = /home/claude/astro/data/knowledge_library/sources/how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md
  - HTJAH-II = /home/claude/astro/data/knowledge_library/sources/how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md
  - NH = /home/claude/astro/data/knowledge_library/sources/notable_horoscopes_raman/chapter_001_full-text-unsplit.md
  The `cited` line number is the line in that file. Search by the chart number or native's name (Grep).

Do NOT open anything else: no repository code, tests, fixtures, docs, JSON keys or other reviewers' output. This review must not be influenced by what any software says. You are not told what anyone else decided, on purpose.

## What to record per item
- `label`: one of
  - `favourable`: Raman concludes this matter is good, well-promised or fortunate for the native.
  - `afflicted`: Raman concludes it is bad, denied, damaged or unfortunate (early loss of the relative, poverty, no children, unhappy marriage, disease suffered, etc.).
  - `mixed`: Raman's own conclusion is explicitly two-sided (good AND bad, e.g. "wealth comes but is lost", "moderate"). Do not use mixed just because he lists factors on both sides before concluding one way.
  - `none`: Raman reaches no conclusion about THIS matter for THIS native anywhere you can find (it is about another chart, or he only notes a factor without concluding).
- `quote`: the exact words (up to 40) that carry his conclusion, copied from the text. Empty for `none`.
- `line`: the line number in the book file where that quote starts (best effort).
- `confidence`: high / medium / low.
- `note`: one short sentence if anything is unusual (e.g. "conclusion is about the native's brother, not the father", "passage window was for a different chart; found it at line N").

## The key distinction
A CONCLUSION is Raman's judgment of the matter ("the native lost his mother very early", "he was blessed with nine children", "marital life was a tragedy").
An OBSERVATION about one contributing factor is NOT a conclusion ("the 4th lord is debilitated", "Venus is aspected by Saturn"). If Raman only weighs factors and never concludes, label `none`.

Matter meanings: `self` = the native's own body, health, character and general life happiness as Raman sums it up; `wealth` = finances; `children` = progeny; `mother`, `father`, `siblings`, `elder_siblings` = that relative (their life, welfare, the native's relationship to them); `spouse` / `marital_happiness` = the marriage and partner; `career` / `profession_*` = work, status, achievement; `fortune` = general luck and dharma; `gains` = income; `disease_*` / `enemies_disease` = favourable means the native is protected, afflicted means the native suffers the disease or enemies; `moksha` = spiritual liberation, favourable means it is promised.

## Output
Write a JSON file (path given in your task message): an object mapping item id to `{"label","quote","line","confidence","note"}`, covering every item in your packet. Then reply with just: the file path, and counts per label.
