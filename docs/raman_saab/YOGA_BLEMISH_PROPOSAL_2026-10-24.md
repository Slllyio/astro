# A good yoga with one small blemish: what Raman does, what the engine does, and how to code it

2026-10-24. The user asked: "There is a positive thing in the horoscope through a combination,
but one small negative thing is attached to it. How do we deal with it in the engine?" Two research
agents answered: one read only Raman's books, the other measured the engine. Full reports:
`/mnt/project-files/astro/research/raman-yoga-blemish-doctrine.md` (47 cases with line citations)
and `/mnt/project-files/astro/research/engine-yoga-blemish-handling.md` (115 rows with fired rules).

## What Raman does

He almost never lets one small malefic touch cancel a strong yoga. In about 38 of 47 cases the good
verdict stands, either plainly or with a qualification. The blemish is put somewhere else:

| What he does with the blemish | Charts | General statements |
|---|---|---|
| Moves it to another matter (children, spouse, father, accidents) while the yoga stands | 17 | 0 |
| A clean benefic aspect (usually Jupiter) neutralises it; an afflicted rescuer fails | 12 | 1 |
| It shows as delay, or in the afflicting planet's sub-period | 9 | 2 |
| It lowers the yoga's level ("Kesari manifested in its lower plane") | 9 | 0 |
| The afflicting planet's own condition defuses it (dispositor, friendly star, wide orb, sandhi) | 8 | 1 |
| Weighed by strength and net result; equal testimony is "neutral" | 6 | 8 |
| Outright cancellation | 7 | 11 |

Key sentences: Truman (NH 10921-10926), where the yoga's "inherent capacity" is "in no way affected
or lessened" and the evil shows "in terms of accidents"; Three Hundred Combinations 877-888, where
negative units weaken a good yoga but "no evil results will be given"; and 3HC 10264-10267, "the
mere debilitation of the Sun cannot destroy all the Raja Yogas".

He cancels a yoga only for heavy or structural causes: the yoga falls in the 6th or 12th, "all the
evil forces" concentrate on it, the yoga planet is debilitated without cancellation and also in a
6th-house exchange, a named Raja-yoga-bhanga is present, or a whole-chart yoga (Kemadruma,
Kalasarpa) has no cancellation.

## What the engine does

Rule evidence reaches the verdict as two yes/no flags: did any benefic rule fire, did any malefic
rule fire (`house_template._decide` clause 2). One small malefic counts the same as ten. Once both
have fired, the decision goes to the strength pillars and then the Navamsa:

- 75 of the 122 rows where the engine is more negative than Raman go through this path.
- 15 of the 16 favourable-to-afflicted inversions there are made by the Navamsa "weakens" step,
  after the small negative opened the contradiction.
- When both sides fire and the engine says "mixed", Raman agrees only about 13% of the time.
- A yoga can lift a "mixed" verdict only if no malefic fired at all; 22 rows are blocked this way,
  and Raman calls 18 of them favourable.
- Nothing weighs the blemish by the afflicting planet's strength, by a benefic aspect on it, or by
  whether it touches the lord or karaka. Yoga cancellation is wired only for Kemadruma; the Raja
  Yoga Bhanga yogas are detected but never cancel anything.

Two warnings from the measurement. Simply ignoring small negatives would raise real errors from 16
to 39 on these rows, because some lone combinations (mostly ones hitting the lord or karaka) are
exactly what Raman calls afflicted. And counting rules was already tried (R3b, R4) and failed.
The weight has to come from *what* the blemish is and *where* it lands, which is what Raman's
cases say too.

## Proposed design (nothing coded yet)

1. **A tier on every malefic rule, set from its citation by engine-blind review:** *decisive*
   (Raman lets it decide: the existing `_DECISIVE_AFFLICTION_RULE_IDS`, plus afflictions of the
   lord or karaka that he judges heavy), *ordinary*, or *blemish* (a single touch he weighs past).
   Attach it in `_bucket_fired`.
2. **Clause 2 reads the tier.** A blemish-tier malefic alone does not open the contradiction. It
   lowers the degree ("favourable, mild") and is reported as its own qualified finding, never
   hidden.
3. **Defusers and rescue, from Raman's own list:** the afflicting planet is the dispositor, in a
   friendly or own star, in a sandhi, or wide in orb; or a clean benefic aspects the afflicted
   point. A defused or rescued ordinary malefic drops to blemish tier.
4. **Navamsa cannot invert a blemish-only contradiction** (`_navamsa_modulate`).
5. **Yoga lift needs real cancellation, not "any malefic":** wire the Raja Yoga Bhanga yogas and
   the dusthana / concentration / debilitation-plus-exchange conditions into `_yoga_modulate`, and
   check the yoga's own causing planets.
6. **Timing.** The blemish's effect is attached to the afflicting planet's sub-period, which the
   timing layer already computes.

## How it would be tested honestly

Both hold-outs are now spent. Following the project's rules, this needs, in order: engine-blind
citation review of the tiers and defusers; a pre-registration committed before any number exists;
the pool measurement; and a third sealed hold-out of unseen Raman conclusions. Few unseen worked
charts remain. The best source is the HTJAH charts rejected only because their dates are garbled
in the OCR, which page images could recover.
