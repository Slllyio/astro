# Raman Saab Engine Contract

This document defines the implementation contract for the `raman_saab` methodology engine.
It is derived from:
- `00_method_overview.md` — chart-wide method, timing, longevity, yoga/rules mapping
- `README.md` — corpus structure and per-house file template
- `house_01_lagna.md` … `house_12_vyaya.md` — house-specific rules, combinations, examples
- `house_08_ayur.md` — longevity and death-specific 8th-house rules

## Core execution invariants

1. Apply every combination to three charts:
   - **Rashi** / zodiac chart
   - **Bhava** / cusp chart (Chalita)
   - **Navamsa**
   - If a rule is explicitly Navamsa-only, evaluate it there; otherwise evaluate it in all three.

2. Preserve the three reference frames:
   - **Lagna**: refer to the ascendant and house positions from Lagna.
   - **Moon**: refer to Chandra-Lagna and house positions from the Moon.
   - **Karaka**: refer to the relevant karaka treated as a Lagna-origin when the rule says "from the Karaka".

3. Longevity and maraka must be resolved before house judgments.
   - The longevity sub-engine is a **pre-pass** that can gate or modify house-level predictions.
   - Death/maraka results may override or suppress otherwise positive house outcomes when the chart is classified as Balarishta/Alpayu or when a maraka period is active.

4. Bhava is the primary house of judgment.
   - House interpretations operate on bhava position first.
   - Rashi position is relevant where Raman explicitly uses it, but it is not the default evaluation.
   - Chalita is mandatory for all house evaluations.

5. Navamsa is equally important.
   - Every house evaluation includes the Navamsa position of the house, lord, occupants, and karaka.
   - Many rules have explicit Navamsa reversal or mitigation clauses; these must be applied.

6. Rule polarity is explicit.
   - A rule labelled `fortified` provides the positive outcome when the relevant planet/house is strong.
   - A rule labelled `afflicted` or containing a malefic condition provides the negative outcome.
   - If the source text does not provide an afflicted clause, treat the base phrasing as the default outcome unless specifically negated by later qualifiers.

## Rule order and precedence

1. **Source precedence**
   - Primary: `HTJAH-I` and `HTJAH-II` (How to Judge a Horoscope Volumes I & II)
   - Secondary: `HPA` (Hindu Predictive Astrology) and `GBB` (Graha & Bhava Balas)
   - Tertiary: any other supporting Raman texts or commentaries referenced in the methodology.

2. **Macro execution order**
   1. Chart cast and ayanamsa fixed to Raman.
   2. Longevity span-class and maraka determination.
   3. House-by-house evaluation, houses 1 through 12.
   4. Timing and dasha/bhukti results.
   5. Chart-level synthesis and exception handling.

3. **Within-house order**
   1. Evaluate the house itself (bhava) including sign, strength, aspects, conjunctions, and hemming.
   2. Evaluate the lord of the house in its current placement and associations.
   3. Evaluate the karaka and its strength in context.
   4. Evaluate occupants and configured planets.
   5. Apply yoga-specific modifiers and special combinations.
   6. Evaluate timing factors and dasha phala.

4. **Timing precedence**
   - When multiple planets influence a house, rank periods as follows:
     1. Both MD-lord and AD-lord directly related to the house → *par excellence* result.
     2. MD-lord related and AD-lord not related → limited result.
     3. AD-lord related and MD-lord not related → feeble result.
   - If two planets both satisfy the same level, prefer the planet whose relationship is stronger by:
     - ownership of the house,
     - direct occupancy of the house,
     - aspect on the house,
     - association with the house lord.

## Special doctrine invariants

- **Functional benefic/malefic per Lagna** must be computed from Raman's classification, not from generic traditional tables.
- **Yoga Karaka** detection must follow Raman's definition: planet owning both a kendra and a trikona.
- **Rahu/Ketu aspects** are only opposition-based in this engine unless a specific Raman passage requires otherwise.
- **Maraka logic** must treat the 2nd and 7th houses as death-inflicting and carry maraka flags into longevity/timing.
- **6/8/12-from-Navamsa mitigation**: if a house lord is in the 6th/8th/12th of Navamsa from the relevant chart, its negative effect is often reduced or reversed.
- **Papakartari / Subha-Papa hemming** and **neecha-bhanga** must be evaluated before final scoring, as these can cancel or invert otherwise standard outcomes.

## Implementation guidance

- Encode each `house_NN` document as a structured rule set with fields:
  - `condition`
  - `result`
  - `reference_frame`
  - `source`
  - `strength_modifier`
  - `navamsa_override`
  - `timing_factors`
- Explicitly label the frame for every rule as `Lagna`, `Moon`, or `Karaka`.
- Keep the house chapters as read-only bodies; derive implementation logic from them, not the other way around.
- Use worked example charts from the house files as regression fixtures.

## Validation checkpoints

- All house evaluations must be verified against at least one canonical chart example where available.
- Longevity results must be tested for all four span classes and the Pindayu/Amsayu exemptions.
- Ragged conditions such as `if any beneficial aspects exist` must be converted into precise condition logic and absorbed into the rule set.
- Death-cause and place-of-death predictions in `house_08_ayur.md` should only be triggered when the chart qualifies as a death-forming configuration.

## Notes

- This contract is intentionally narrower than a full algorithm spec; it is the operational boundary between the methodology corpus and the engine implementation.
- If an implementation choice is not explicitly stated here, default to the nearest Raman source cited in the method files.
- When two Raman citations conflict, prefer the one that applies to the same evaluation context (house, timing, or longevity) rather than a general statement.
