---
house: 1
name: Tanu Bhava / Lagna
karaka: Sun (Thanu Karaka)
special_varga: [D1, D9]
source: HTJAH-I:971-2313
---

# House 1 Framework — Tanu Bhava / Lagna

This document is a comprehensive House 1 framework extracted from Raman's first-house chapter and the worked-chart examples in `house_01_lagna.md`.

It is intended as the maximal implementation blueprint for a Raman-inspired engine focused on the first house.

## 1. Executive summary

- Raman builds House 1 around a three-pillar model: **Lagna / first house**, **Lagna-lord**, and **Sun as Thanu Karaka**.
- The **Moon is a mandatory supplementary frame** for mental disposition and liability.
- **Rashi/Bhava + Navamsha** are both decisive; the same combination must be applied to both charts and integrated.
- House 1 readings separate:
  - **Physical constitution and appearance** (body frame)
  - **Health and longevity potential**
  - **Mental characteristics and liability**
  - **General fortune and steady prosperity**
- A practical implementation should treat House 1 as a layered scoring model, not a single yes/no classification.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rashi/Bhava Lagna frame**
   - The principal body/constitution frame.
   - Evaluate Lagna by Bhava position, sign dignity, aspects, occupants, and functional status.

2. **Navamsha Lagna frame (D9)**
   - An equal-weight corrective frame.
   - Used to confirm, strengthen, or reverse Rashi conclusions.
   - Pay special attention to Lagna-lord placement in Navamsha and to Navamsha Lagna occupancy.

3. **Chandra-Lagna / Moon frame**
   - The mind, emotions, liability, and accident-disease frame.
   - Evaluate Moon by sign, aspects, conjunctions, and Navamsha disposition.

### 2.2 Pillars of judgment

- **Lagna / the house itself**
- **Lagna lord**
- **Occupants / planets in 1st**
- **Karaka / Sun**
- **Moon (for mental factors)**

These pillars are synthesized across frames. The engine should compute each pillar separately and then apply interaction rules.

### 2.3 Output dimensions

The engine should produce a multi-dimensional House 1 profile, including:

- `physical_constitution_score`
- `appearance_quality_score`
- `health_risk_flag`
- `mental_liability_score`
- `steady_fortune_flag`
- `travel_tendency_flag`
- `papakartari_penalty`
- `subhakartari_bonus`
- `first_six_contact_flag`

This avoids forcing House 1 into a single scalar output.

## 3. Rule ordering and precedence

Raman's chapter implies a strict evaluation order:

1. **Bhava over Rashi**: always read the first house by Bhava placements first.
2. **Rashi/Bhava + Navamsha integration**: do not finalize a judgment without comparing both.
3. **Longevity/Maraka check first**: verify whether the native reaches the Lagna-lord's Dasha before first-house phala.
4. **Strength of Lagna lord and Sun**: assign central weight to the Lagna lord plus the Sun as body Karaka.
5. **Hemming and aspect quality**: apply hemming rules before assigning positive strength.
6. **Example-based overrides**: use templates from sample charts to validate.

Example rules show that a strong-looking Lagna can still fail when Papakartari or adverse Navamsha influences are present.

## 4. First-house scoring architecture

### 4.1 Core score components

For each candidate chart, compute:

- `lagna_strength`
  - Based on Lagna sign dignity, house placement, occupants, aspects, and hemmed status.
- `lagna_lord_strength`
  - Based on Lagna lord's sign, house, conjunctions, aspects, dignity, and Navamsha placement.
- `sun_karaka_strength`
  - Based on Sun's sign, house, aspects, Navamsha, relation to Lagna and 6th/8th/12th lords.
- `moon_mental_strength`
  - Based on Moon's sign, aspects, conjunctions, Navamsha, and afflictions.
- `hemmed_penalty`
  - Based on Papakartari/Subhakartari rules and the severity of hemming planets.
- `neechabhanga_bonus`
  - When a debilitated lord has cancellation conditions.
- `navamsa_mitigation`
  - A corrective factor derived from D9 placement of Lagna-lord and Lagna.

### 4.2 Pillar aggregation

Compute a composite first-house score from weighted pillars:

- `body_frame` = weighted combination of `lagna_strength` + `sun_karaka_strength`
- `mind_frame` = `moon_mental_strength`
- `life_frame` = composite of `body_frame` + `lagna_lord_strength`
- `steady_fortune_flag` if at least two of {`lagna_strength`, `sun_karaka_strength`, `moon_mental_strength`} are strong.

### 4.3 Recommended weights

These are analytic priorities, not hard constants:

- Lagna strength: 35%
- Lagna-lord strength: 30%
- Sun Karaka strength: 20%
- Moon mental strength: 15%

If `hemmed_penalty` is present, it should reduce the composite by 25–40% depending on severity.

## 5. Detailed first-house rule categories

### 5.1 Lord of the 1st in the 12 houses

Raman provides general descriptors for the Lagna-lord placed in each house. The engine should use these as default qualitative outcomes and amend them with affliction status.

| Lord placed in | Fortified result | Afflicted / un-fortified base result |
|---|---|---|
| 1st | Famous in own community; strong independence | Lives by own exertion; not physically happy if evil | 
| 2nd | Ambitious, good forethought, prominent eyes | Gains but anxious from enemies; good character | 
| 3rd | Rise by brothers, courageous, intelligent | Courageous, happy, two wives | 
| 4th | Landed property, rich, happy, famous | Happy parents, materialistic, fair in build | 
| 5th | Regal favour, diplomacy, auspicious acts | Less happiness from children, short-tempered | 
| 6th | Army/medical service, health expertise | Debts, litigation, physical ailments | 
| 7th | Foreign travel, licentious, marriages | Wife unhappy, detached life, travel profit | 
| 8th | Helping others, occult interest, peaceful end | Learned but mean, gamblers, sudden changes | 
| 9th | Ancestral wealth, philanthropy, good orator | Generally fortunate, rich, protective | 
| 10th | Professional success, honoured, research | 4th-house material success plus career | 
| 11th | Prosperity via elder brother, business gains | Business success, no financial straits | 
| 12th | Charitable living, emotionally balanced | Losses, exile, no business success | 

### 5.2 First-house combination rules

The chapter enumerates 67 rules. The engine should prioritize the ones that appear most frequently in examples and those with explicit reversal conditions.

#### 5.2.1 High-priority first-house rules

- Lord of birth in Lagna with 6th/8th/12th lord conjunct or aspected by malefic → health suffers. (Rule #1)
- Ascendant lord in Lagna subject to evil combinations → native not physically happy. (Rule #2)
- All planets aspect Lagna → strong, wealthy, long-lived. (Rule #3)
- Lord strong + good planets in Kendras + lagna not aspected by evil → great body happiness. (Rule #4)
- Lagna or lord hemmed by two malefics (esp. Saturn & Rahu) → theft and suffering. (Rule #26)
- Rahu in 2nd worse than Rahu in 12th; Saturn in 12th worse than Saturn in 2nd. (Rule #27)
- Lagnadhipati weak and in 3rd/5th/7th from Janma nakshatra → intensified evil. (Rule #35)
- Lagnadhipati strong in those same stars → lessening of favourable indications. (Rule #36)
- Steady fortune if at least two of {Lagna, Sun, Moon} are well disposed. (Rule #67)

#### 5.2.2 Constitution rules

- Dry planet in Lagna → lean body. (Rule #13)
- Sushka ascendant → emaciation. (Rule #14)
- Lagna-lord conjunct Sushka planets → lean. (Rule #15)
- Cancer/Scorpio/Pisces ascendant with benefics → corpulent. (Rule #16)
- Watery Lagna-lord or Jupiter aspector from watery sign → stout. (Rule #17–#19)

#### 5.2.3 Health and affliction rules

- Sun in Lagna aspected by Mars → asthma/lung trouble. (Rule #20)
- Mars in Lagna aspected by Sun or Saturn → wounds/accidents. (Rule #21)
- Lord of Lagna in 8th → weak constitution unless favourable aspects exist. (Rule #9)
- Lord of Lagna conjunct an evil planet and Rahu in Lagna → deception fears. (Rule #5)
- Saturn in Lagna → cheated/stolen. (Rule #11)
- Lord of Lagna in 6th with 6th lord → ailments, litigation, poverty. (Rule #48)
- No contact between lords of 1st and 6th → protective; violation signals illness/defamation. (Rule #66)

#### 5.2.4 Travel and mobility

- Lagna, its lord, Navamsha Lagna, or lord in movable sign → travel abroad profitably. (Rule #22)
- Lord of Lagna in 7th conjunct 7th lord implies journeys; strength of lord determines profit. (Rule #51)

#### 5.2.5 Navamsha moderation rules

- Lagna-lord in 6th/8th/12th in Navamsha from the relevant house-lord reduces the effect. (Rules #41, #43, #45, #47, #50, #53, #57, #60, #62)
- Lagna-lord in 12th in Navamsha → roaming and mind/body suffering. (Rule #39)
- Lagnadhipati in own Navamsha sign + Chara Rashi exalted partner → fortune amplified. (Rule #65)

### 5.3 Planet-in-1st archetypes

The planet occupying 1st has a strong signature, modified by aspects. Use these as baseline archetypes:

- Sun: righteous, ambitious, popular, strong health; afflicted by Saturn/Mars = scars, fevers, eyes.
- Moon: social, changeable, traveller, mental restlessness; Saturn = worried mind; Mars = menstrual disorder; Rahu = hysteria.
- Mars: hot, courageous, handsome, accidents, wounds, restless.
- Mercury: witty, adaptable, occult interest, nervous if with Rahu/Ketu.
- Jupiter: magnetic, optimistic, corpulent when afflicted, dignified.
- Venus: pleasant, artistic, emotional, good spouse relations; afflicted = marital discord.
- Saturn: serious, stable, emaciated, late progress, loss through negligence.
- Rahu: odd, occult, unsatisfactory health, not good for marriage.
- Ketu: psychic, weak constitution, wandering, deceitful, morbid imagination.

### 5.4 Sign and planet tints

Raman provides classic sign tints. The engine can use these to enrich physical and mental descriptions.

- Aries: head diseases; Mars influence = sturdy, red.
- Taurus: stable, material, strong.
- Gemini: intellectual, variable.
- Cancer: emotional, sensitive, corpulent if well-disposed.
- Leo: dignified, kingly.
- Virgo: precise, lean.
- Libra: graceful, balanced.
- Scorpio: intense, secretive.
- Sagittarius: expansive, philosophical.
- Capricorn: serious, lean.
- Aquarius: unusual, aloof.
- Pisces: dreamy, watery.

These should be blended with planetary overlays.

## 6. Pattern families from examples

Raman uses the example charts in deliberate pattern families. The engine should use these as validation clusters.

### 6.1 Hemming and dignity families

- **Charts 8 / 9**: movable Lagna with reversed Rahu/Saturn hemming. These show how a strong Navamsa and supportive lord can create greatness, while Dwirdwadasha/hemmed Lagna produces ordinariness.
- **Charts 26 / 27**: Papakartari contrasted with Saturn aspect on Sun and Lagna lord. These highlight that a seemingly strong first house can still be debilitated.
- **Charts 20 / 21 / 22**: identical Cancer Ascendant structural cluster. Differences stem from Moon and lord disposition, Chandramangala yoga, and Navamsha aspects.
- **Charts 23 / 24 / 25**: Leo Ascendant cluster. They validate the two-of-three strong factor rule and the impact of Lagna occupation vs. aspect.

### 6.2 Navamsa correction families

- **Charts 10 / 11**: same birth data, same Rashi chart, different focus. Chart 10 shows physical expression; Chart 11 shows timing. This pair teaches the engine to separate static physique from Dasha timing.
- **Charts 31 / 32**: nearly identical Rashi but different Sun/Moon positions. Demonstrates the sensitivity of physical build and life station to Sun/Moon changes.
- **Charts 12 / 13**: Saturn and Venus combinations with neechabhanga and Papakartari. These show how a debilitated lord can still support a good appearance while suffering in specific sub-periods.

### 6.3 10th-house caution family

- **Chart 33**: powerful 10th stellium but weak first house. This is the definitive warning that 10th-house strength is an amplifier, not a rescue for Lagna weakness.

### 6.4 Health and 1st-6th contact family

- **Chart 18**: first-house discredit / defamation via 1st-6th lord contact.
- **Chart 13**: serious fever in Venus Dasha / Saturn Bhukti despite otherwise handsome body.
- **Chart 36**: mental abnormality from Moon affliction despite good bodily constitution.

## 7. Decision tree for first-house analysis

A formal decision tree can guide engine flow.

### 7.1 Step 1: Validate the data model

- Confirm Lagna house, sign, degrees.
- Compute Bhava placements precisely.
- Compute D9 Navamsha placements.
- Identify Lagnadhipati, Moon, Sun, 6th/8th/12th lords.
- Determine exact conjunction orbs using Raman's effective-orb thresholds.

### 7.2 Step 2: Evaluate Lagna frame

- Score Lagna by:
  - sign quality (own/friend/enemy/neutral)
  - house occupancy and aspects
  - hemmed/subhakartari/papakartari status
  - Dwirdwadasha / 2nd-12th mutual position penalty
  - presence of all planets aspecting Lagna bonus

- Apply penalties for:
  - Rahu in 2nd > Rahu in 12th
  - Saturn in 12th > Saturn in 2nd
  - Lagna occupied by Rahu/Mars/Saturn without benefic support

### 7.3 Step 3: Evaluate Lagna-lord

- Use the Lord-of-1st table for base meaning.
- Score the lord by sign dignity, age, association with benefics/malefics, and Navamsha house.
- Add `neechabhanga_bonus` when conditions are met.
- Set `lord_illness_warning` if the 6th/8th/12th lords influence it malignly.

### 7.4 Step 4: Evaluate Sun as Karaka

- Evaluate Sun in Rashi and D9.
- If Sun is in an enemy sign or afflicted by Saturn/Mars, reduce body/appearance score and heighten health warning.
- If Sun is vargottama, set a positive body presence flag but still inspect aspect quality.

### 7.5 Step 5: Evaluate Moon frame

- Score Moon by its own dignity, aspects, and Navamsha.
- Add `mental_abnormality_warning` if Moon is afflicted by Saturn, Rahu, Mars, or Ketu in angles.
- Use the Moon frame to override pure physical readings when mental liability is explicit.

### 7.6 Step 6: Apply timing diagnostics

- Compute the five-factor influence set for the 1st house.
- Identify planets with at least two of these functions:
  - owns 1st
  - aspects 1st
  - occupies 1st
  - aspects Lagna lord
  - associates with Lagna lord
- Mark the strongest influencer and generate Dasha/Bhukti predictions accordingly.

### 7.7 Step 7: Synthesize

- If two of {`lagna_strength`, `sun_karaka_strength`, `moon_mental_strength`} are strong, set `steady_fortune_flag`.
- Adjust final body/health results by `papakartari_penalty` and `navamsa_mitigation`.
- If `first_six_contact_flag` is true, add a health/defamation caveat.

## 8. Implementation detail model

### 8.1 Feature schema

```yaml
lagna:
  sign: Aries
  dignity: own/friend/enemy/neutral
  occupants: [Mars, Venus]
  aspects: [Jupiter, Saturn]
  hemmed: true
  hemmed_planets: [Rahu, Saturn]
  papakartari: true
  subhakartari: false
  vargottama: false

lagna_lord:
  planet: Mars
  house: 3
  sign: Taurus
  dignity: friendly
  aspects: [Jupiter]
  navamsha_house: 9
  neechabhanga: false

sun_karaka:
  sign: Libra
  house: 1
  dignity: enemy
  aspects: [Saturn]
  navamsha_aspects: [Mercury]

moon_mental:
  sign: Gemini
  aspects: [Mars, Saturn]
  navamsha_sign: Pisces
  afflicted: true

timing:
  influence_planets: [Saturn, Mars, Venus]
  strongest_influencer: Saturn

flags:
  steady_fortune: false
  papakartari_penalty: true
  first_six_contact: true
  travel_tendency: false
```

### 8.2 Scoring functions

The engine can use normalized scores from 0–100 for each component.

- `score_lagna()` returns a composite including sign, aspects, occupation, and hemming.
- `score_lord()` returns a composite including house placement, dignity, Navamsha, and benefic/malefic associations.
- `score_sun_karaka()` returns a composite based on the Sun's physical vitality, afflictions, and Karaka status.
- `score_moon()` returns a separate mental inclination score.

Then compute:

- `body_frame = 0.55*lagna + 0.30*lord + 0.15*sun`
- `mind_frame = moon`
- `general_fortune = 0.40*body_frame + 0.30*lord + 0.30*moon`

Adjust with:

- `general_fortune -= papakartari_penalty ? 25 : 0`
- `body_frame -= subhakartari_bonus ? -10 : 0`
- `health_risk += first_six_contact_flag ? 30 : 0`

### 8.3 Decision thresholds

- `steady_fortune` if at least two component scores > 65.
- `strong_first_house` if `general_fortune > 70` and `health_risk < 40`.
- `weak_first_house` if `general_fortune < 45` or `papakartari_penalty` is high.

These should be calibrated against the example corpus.

## 9. Example-driven validation

Use the House 1 charts as an initial test suite. For each chart, record the expected interpretations:

- Chart 8: strong body + great fame + travel + learned + fair
- Chart 9: ordinary, no travel, hemmed by theft/injury, weak Lagna despite movable sign
- Chart 11: strong Saturn influence on 1st; loss of mother during Mars Dasha/Saturn Bhukti
- Chart 13: handsome body + fevers in Saturn Bhukti
- Chart 20: all first-house factors unfavourable, nervous, mean, sensitive
- Chart 21: improved outcome via Chandramangala yoga despite same Cancer Lagna
- Chart 22: Mars debilitated in Lagna with neechabhanga, smallpox marks, sturdy body
- Chart 23: weak Leo Lagna, sickly constitution
- Chart 25: strong Leo Lagna via Jupiter/Mars aspect, attractive
- Chart 33: weak first house despite a powerful 10th stellium
- Chart 36: good body but Moon affliction yields mental abnormality

## 10. Edge cases and caveats

### 10.1 10th-house overconfidence

A strong 10th house alone does not guarantee a strong Lagna. Chart 33 is explicit: first-house weakness can persist even under powerful career yoga.

### 10.2 Conjunction orb sensitivity

Effective conjunctions are not automatic. If the separation is large enough (roughly 18°–20°), Raman treats the planets as not truly conjunct.

### 10.3 Bhava vs Rashi placement

Always compute by Bhava. Ketu may appear in Lagna by sign but be in 12th Bhava. Use Bhava-based house placement for the first-house verdict.

### 10.4 Functional malefic/benefic status

Planets like Sun and Moon can behave as functional malefics relative to a given Lagna. Avoid defining malefic status as absolute; derive it chart-relatively.

### 10.5 Timing before results

Never issue a final first-house phala without checking whether the native reaches the Lagna-lord's Dasha and whether a Maraka period obstructs it.

## 11. House 1 engine contract

### 11.1 Input contract

The engine must accept:
- exact birth time and place
- Rashi chart and Bhava placements
- Navamsha (D9) chart placements
- degree-based orbs for conjunctions/aspects
- computed lords of 1st, 6th, 8th, 12th, and 9th houses
- Janma Nakshatra for Tara calculations

### 11.2 Output contract

The engine should output:
- `house_1_body_profile`
- `house_1_health_profile`
- `house_1_mental_profile`
- `house_1_fortune_profile`
- `steady_fortune_flag`
- `travel_tendency_flag`
- `first_six_contact_flag`
- `papakartari_penalty`
- `subhakartari_bonus`
- `primary_1st_house_influencers`
- `dasha_influence_planets`

### 11.3 Invariants

- `steady_fortune_flag` requires two of {Lagna, Sun, Moon} strong.
- `papakartari_penalty` must degrade otherwise favourable Lagna evaluations.
- `navamsa_mitigation` must be applied for any first-house lord-based yoga.
- `health_risk` must include the 1st-6th contact diagnostic.
- `mental_liability` must be at least partially derived from Moon affliction.

## 12. Practical engine rules

The following rules should be implemented verbatim or as strong heuristics:

- If all planets aspect Lagna, set a strong longevity/fame weight.
- If Lagna lord is in 6th/8th/12th and afflicted, mark body health concerns immediately.
- If Lagna has a benefic lord but Papakartari is present, lower the `first_house_strength` by one tier.
- If Moon is afflicted and Lagna is strong, preserve a cautionary mental profile.
- If the lord of Lagna occupies the 9th, 10th, or 11th and is well-disposed, add a stable long-term support flag.
- If the first house is Sushka and Sushka planets dominate, add lean/emaciated constitution descriptors.
- If the first house is watery with benefic support, add corpulent/stout descriptors.

## 13. Recommended development plan

1. Implement the feature schema and scoring functions.
2. Build the first-house decision tree with explicit rule order.
3. Encode the high-priority rule set and sample validation cases.
4. Run the example charts through the engine and compare interpretations.
5. Adjust weights and penalties until the chart outputs match Raman's worked examples.

## 14. Final notes

This framework is intentionally broad and deep. It is designed to support a Raman-inspired House 1 engine in production, not just a quick summary.

The next step is to use this framework as the canonical House 1 engine design document and then build the corresponding code/module.
