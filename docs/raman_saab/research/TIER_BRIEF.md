# Engine-blind grading of negative rules: how much weight does Raman give each one?

You grade rules of a Vedic-astrology engine that encodes B. V. Raman's books. Each rule is one
negative testimony about one matter of life (a house signification), with the line of Raman's
book it was taken from. The question for every rule is ONE thing: **when this testimony is
present in a chart that also has good testimony for the same matter, how does Raman treat it?**

## Hard rules
- Do NOT run or read anything under /home/claude/astro/app, /home/claude/astro/tests,
  /home/claude/astro/tools or /home/claude/astro/docs. Never read /home/claude/astro/data/private/.
- You must not know what the engine concludes for any chart. Work from Raman's printed text only.
- Book files (line numbers as `sed -n` / `grep -n` count them, 1-based):
  - HTJAH-I  -> /home/claude/astro/data/knowledge_library/sources/how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md
  - HTJAH-II -> /home/claude/astro/data/knowledge_library/sources/how_to_judge_horoscope_raman2/ (one .md file)
  - NH       -> /home/claude/astro/data/knowledge_library/sources/notable_horoscopes_raman/chapter_001_full-text-unsplit.md
  - 3HCC     -> /home/claude/astro/data/knowledge_library/sources/three_hundred_combinations_complete/chapter_001_full-text-unsplit.md
  Read about 15 lines either side of the cited line. The OCR is noisy.

## The three tiers
- **decisive**: Raman lets this testimony settle the matter against good testimony. The text
  states a denial, loss or destruction of the matter itself in plain terms (no children, death
  of the father or mother, loss of wife, poverty, imprisonment, a violent death, loss of the
  organ), or Raman says it overrides other factors.
- **ordinary**: a real affliction of the matter that Raman expects to be WEIGHED against good
  testimony; the matter suffers but is not simply denied ("the father will not be long-lived"
  without certainty, "troubles through", "the native will suffer from", "loss of wealth").
- **blemish**: a single minor touch Raman weighs past: a trait of character or body, a minor
  ailment, some delay, a small part of the matter, a mild or qualified effect ("some",
  "slight", "occasional", "may"), or a statement about the yoga's level rather than its presence.
  Raman's own practice (from a separate study of 47 of his cases): he almost never lets one small
  malefic touch cancel a strong combination; he moves it to another matter, has a benefic aspect
  neutralise it, shows it as delay, or lowers the level.
- If the cited text does not support the rule at all (wrong line, nothing about this), say
  `unsupported`; if you cannot tell, say `ordinary` (the default, which changes nothing).

Grade the rule as written in `text` together with Raman's cited passage. Do not grade by how
common the configuration is.

## Output
A JSON list, one object per input rule, same order:
{"id": ..., "tier": "decisive"|"ordinary"|"blemish"|"unsupported", "quote": "<= 200 chars of
Raman's words that decide it", "line": <line number of the quote>, "why": "one sentence"}
Write it to the output path you are given, then reply with the counts per tier and any rule
whose citation you could not find.
