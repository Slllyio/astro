# Can the Navamsa flip a verdict? Raman's answer and the engine's behaviour (2026-10-24)

User question: "the Navamsa step then flips the verdict — research this; can the Navamsa do it?
Use Raman sir's knowledge only." Full reports:
`/mnt/project-files/astro/research/raman-navamsa-doctrine.md` (books only, every quote line-cited) and
`/mnt/project-files/astro/research/engine-navamsa-step.md` (code audit and measurement at 0cb6058).

## Raman

- The Navamsa is "equally important… the pivot on which the horoscope revolves… every combination
  should be applied to the Rashi, Bhava and Navamsha charts and then a conclusion drawn"
  (HTJAH-I:974-980). It is weighed together with the Rasi, not used as a judge over it.
- In worked charts it almost always changes **degree, not direction**: about 29 degree-only cases,
  about 20 where it only confirms, about 12 where it adds a sub-matter (number of wives, temperament,
  timing). Eight of the degree cases say outright that the Rasi wins: "The moderate affliction… in
  Navamsha is more than counterbalanced by his strong disposition in Rashi" (HTJAH-I:4688-4689);
  "Navamsha cannot deny elder co-borns" (HTJAH:16704); a 9th lord in the 6/8/12 Navamsa gives
  results "good but… only middling" (HTJAH:12894-12896).
- Reversal by the Navamsa: only 2 worked charts, and it is citable only inside named rules: certain
  Three Hundred Combinations yogas (e.g. 248: exalted planets in evil navamsas, "the yoga does not
  function"; 158, 244) and the HTJAH Vol I dasha-result rules (HTJAH-I:1739-1740).
- No printed rule makes the Navamsa a tie-breaker when the Rasi shows both a good and a bad factor.
  In four cases (Vivekananda, Ramakrishna, Shivaji, Chart 75) he decided from the Rasi despite a bad
  Navamsa. "The Navamsa is the fruit" does not appear in his books.

## The engine

- `house_template._navamsa_status` reads the lead lord and karaka: "weakens" if debilitated in D9 or
  in the 6/8/12 from the Navamsa Lagna. That 6/8/12 test produces 80 of 132 "weakens", and Raman
  gives it only inside specific combinations, where it tempers rather than reverses.
- The clause-2 guard (when a contradiction exists and the Navamsa "weakens", go to afflicted) has
  **no Raman citation**; it came from tuning on the golden pool. The occupant quotes in that code
  appear in none of the books.
- "Weakens" rows are afflicted in Raman 44.7% of the time, "confirms" rows 44.0%: the status barely
  predicts his direction.
- Out of sample, every change the step makes is on a contradictory row; the guard fired 6 times on
  the hold-outs, 2 correct and 4 new inversions.

| Variant (exact / within one / real) | Pool | Hold-out 1 | Hold-out 2 |
|---|---|---|---|
| Engine now | 277/350/39 | 23/28/8 | 58/98/36 |
| Navamsa may move one step, never favourable to afflicted | 269/354/35 | 22/30/6 | 57/100/34 |
| Navamsa off | 253/348/41 | 24/30/6 | 50/103/31 |

Caveat: both hold-outs were already spent, so these hold-out numbers describe the change; they are
not a clean test of it.

## Recommendation

Encode what Raman does: the Navamsa moves a matter at most one step (strengthens or weakens the
grade) and never turns a favourable Rasi reading into afflicted, or the reverse, except inside the
named yogas and dasha rules where he says so. Remove the uncited clause-2 guard, and keep the
general 6/8/12 test as degree-only. This is doctrine-led (the guard has no citation), and on all
three sets it lowers real errors and raises within-one, at a cost of 8 exact rows in the pool.
