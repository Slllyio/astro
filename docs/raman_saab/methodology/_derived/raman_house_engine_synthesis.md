---
house: all
name: Raman House Engine Synthesis
sanskrit: Sarva Bhava Sangrah
karaka: [Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu]
special_varga: [D1, D2, D3, D8, D9, D60]
source: HTJAH-I/II: selected chapters and worked charts
---

# Raman House Engine Synthesis

A compact implementation guide that cross-surfaces all twelve house frameworks
into a single engine-ready reference. This synthesis highlights the shared
architecture, the most important house-to-house connections, and the practical
rules needed to convert Raman's examples into a coherent astrology engine.

## 1. Core engine architecture

### 1.1 Shared design pattern

Every house engine follows the same high-level structure:

- Primary house frame: evaluate the Rasi house, occupancy, aspects, and sign.
- Lord frame: score the house lord by placement, ownership, exchange, and aspect.
- Karaka frame(s): apply planet-specific business rules by sub-matter.
- Navamsa frame: use `D9` as the default validation/correction layer.
- Specialized frames: `D3`, `D8`, `D60`, `D2`, `from-Moon`, `from-Venus` when
  required.

That means a house engine is not a single verdict machine; it is a multi-output
scoring pipeline with shared components.

### 1.2 Standardized outputs

Use a common naming scheme for recurring outputs:

- Strength metrics: `house_strength`, `lord_strength`, `karaka_strength`
- Quality indicators: `fortune_rating`, `support_flag`, `quality_flag`
- Risk signals: `risk_flag`, `loss_risk`, `maraka_flag`
- Timing triggers: `period_flag`, `dasha_flag`, `bhukti_flag`

This makes outputs from different houses composable and easier to reconcile.

### 1.3 Common evaluation flow

A consistent house-engine flow improves reliability and reduces drift:

1. Evaluate the house and house lord together.
2. Determine applicable karaka(s) and apply them by sub-matter.
3. Confirm or adjust the result using Navamsa (`D9`).
4. Apply hemming / Papakartari / Subhakartari / functional dignity rules.
5. Merge secondary frames such as Moon, Venus, or special vargas.

This pattern should appear in every house implementation.

### 1.4 Mandatory auxiliary frames

- `D9` is mandatory for nearly all houses.
- `D3` is essential for sibling, father, and faith themes.
- `D8` is essential for death/crisis timing.
- `D60` is the hidden-karma validator for longevity and deep crisis.
- `D2` is the wealth/earning frame for House 2 and related financial outcomes.

A sound Raman engine never relies on a single frame alone.

### 1.5 The maraka/timing thread

Maraka logic is woven through the entire model:

- House 2 has explicit maraka timing through speech, family, and wealth.
- House 7 uses marital partnerships as potential death/release triggers.
- House 8 is the primary death/longevity house.
- House 12 links loss and exile to spiritual release.

Any house with 2nd/7th/8th/12th involvement needs a dedicated maraka signal.

## 2. House treasure map

| House | Core domain | Primary karaka(s) | Key outputs | Cross-house link |
|---|---|---|---|---|
| 1 | Self, body, mind | Sun, Moon | `constitution`, `health_risk`, `mental_liability` | Validates House 6, moderates House 10 |
| 2 | Wealth, family, speech | Jupiter | `wealth_score`, `maraka_risk`, `speech_flag` | Feeds House 10/11, mirrors House 6/12 |
| 3 | Siblings, courage, travel | Mars | `younger_sibling_count`, `courage_score`, `travel_flag` | Interfaces with House 11 elder siblings, House 9 travel |
| 4 | Home, mother, property | Moon, Jupiter, Venus, Mars | `mother_health`, `property_strength`, `happiness` | Connects to House 5, House 10, House 1 |
| 5 | Children, fertility | Jupiter | `issue_potential`, `fertility_flag`, `creativity_score` | Gates House 2 family, House 7 partner support |
| 6 | Disease, debt, enemies | Mars, Saturn | `disease_risk`, `enemy_flag`, `debt_risk` | Validates House 1 health, House 12 loss |
| 7 | Marriage, spouse | Venus | `marriage_potential`, `spouse_quality`, `maraka_flag` | Linked to House 12 exile, House 8 partner loss |
| 8 | Longevity, crisis | Saturn, Rahu/Ketu | `longevity_rating`, `sudden_death_risk`, `hidden_crisis` | Cross-checks House 12 and House 4 ancestry |
| 9 | Dharma, father, travel | Jupiter, Sun | `father_quality`, `fortune_rating`, `foreign_luck` | Reinforces House 3 travel, House 7 marriage |
| 10 | Career, authority | Sun, Mars, Mercury | `career_type`, `reputation_flag`, `business_flag` | Drives House 2 income, House 11 gains |
| 11 | Gains, social network | Jupiter, Mars | `profit_potential`, `wish_score`, `elder_support` | Harmonizes with House 2 and House 3 |
| 12 | Loss, exile, release | Jupiter, Saturn | `expenditure_risk`, `confinement_risk`, `release_potential` | Balances House 2 spending, House 8 crisis |

## 2.1 House anchor rules

Use these distilled house anchors when validating the engine’s top-level outputs:

- House 1: Strong lagna/lord with supportive Moon produces constitutional resilience; weak lagna lord in 6/8/12 or hemmed by malefics triggers health and physical liability flags.
- House 2: Wealth needs both a strong 2nd lord and positive 2nd-from-Moon support; a malefic-owned 2nd house or weak 2nd lord should raise `maraka_risk` even if material gain appears.
- House 3: Younger sibling counts should come from the house, lord, and Mars, but elder sibling support belongs to House 11; use `D3` to confirm courage and travel energy.
- House 4: Mother/property happiness is only confirmed when Moon/Jupiter are strong and Navamsa is supportive; a debilitated 4th house often means vehicle/property delays rather than guaranteed loss.
- House 5: Treat fertility as a gating condition — `issue_potential` should be blocked when the 5th lord is weak, combust, or hemmed even if Jupiter is well placed.
- House 6: Benefics in the 6th increase service and litigation potential rather than eliminate risk; use the 6th-from-Moon frame to avoid overrating health recovery.
- House 7: Venus-as-Lagna danger rules are the decisive filter for spouse outcomes; a well-placed Venus in the 7th is generally favorable unless the 7th lord is afflicted.
- House 8: Longevity ratings must combine Saturn/Rahu-Ketu strength with D8 timing and D60 karmic confirmation; suddenness risk is a separate signal from long-life capacity.
- House 9: Distinguish father versus dharma by using Sun for paternal identity and Jupiter for fortune/spiritual support; weak father signals do not cancel dharma potential if Jupiter remains strong.
- House 10: Career type is driven by 10th lord sign and placement, but reputation is moderated by the 1st and 7th house lords; Mars or Mercury in the 10th can turn a spiritual career into business action.
- House 11: Wishes are supported by a strong 11th lord and Jupiter, while elder support comes from the 11th house itself; use House 2 income strength to qualify `profit_potential`.
- House 12: Loss is real when the 12th lord is afflicted or in a dusthana, but release is possible when Jupiter/benefics support the house; separate `spiritual_release` from plain `expenditure_risk`.

## 2.2 Common implementation pitfalls

Avoid these recurring mistakes:

- Treating a strong Rasi house as definitive without a Navamsa check.
- Collapsing House 3 and House 11 sibling logic into one model.
- Using Venus in House 7 as a blanket good sign without Venus-as-Lagna danger filtering.
- Evaluating House 5 only by Jupiter and ignoring the 5th lord’s functional strength.
- Reporting longevity by House 8 alone and ignoring D8/D60 timing.

## 3. Cross-house treasure threads

### 3.1 Planetary roles across the cycle

- Sun: House 1 presence → House 9 father → House 10 authority.
- Moon: House 1 mind → House 4 mother → House 12 sleep/isolation.
- Mars: House 3 courage/siblings → House 6 disease → House 7 spouse → House 10 action.
- Mercury: House 2 speech/eyes → House 3 writing → House 4 education → House 10 commerce.
- Jupiter: House 2 wealth → House 5 children → House 9 dharma → House 11 gains → House 12 release.
- Venus: House 4 vehicles/music → House 5 creativity → House 7 marriage → House 12 exile.
- Saturn: House 1 delay/stability → House 6 chronic disease → House 8 longevity → House 12 isolation.
- Rahu/Ketu: House 8 suddenness → House 12 exile → House 2 deception → House 7 unconventional marriage.

This network is the biggest treasure: planets carry evolving roles across houses.

### 3.2 Family and social net

The family thread is a distinct cross-house system:

- House 3 = younger siblings and courage.
- House 5 = children and creativity.
- House 9 = father, mentor, and dharma.
- House 11 = elder siblings, gains, and networks.

A complete family profile must combine 3/5/9/11 rather than treating them
separately.

### 3.3 Wealth and expenditure cascade

Wealth moves through four core houses:

1. House 10 earns.
2. House 2 retains and spends.
3. House 11 amplifies and networks.
4. House 12 drains, expatriates, or spiritualizes.

Use this cascade as the engine’s income/loss flow model.

### 3.4 Health, longevity, and release axis

A second spine runs through:

- House 1 constitution.
- House 6 disease and enemies.
- House 8 longevity and crisis.
- House 12 loss, confinement, and release.

This axis is the engine’s health and karmic lifecycle model.

## 3.5 Foreign / spiritual axis

- House 9 foreign luck and travel signals are the primary cross-checks for
  House 3 courage/travel outcomes and House 7 marriage-abroad patterns.
- House 9 dharma and mentor support can steady weak House 1 physical or House 2
  financial patterns through spiritual guidance rather than literal wealth.
- House 12 foreign residence and exile work with House 9 pilgrimage and House 7
  spouse partnership to distinguish voluntary pilgrimage from enforced exile.

## 3.6 Property / network / career circuit

- House 4 home/property and House 10 career form the native’s private/public
  foundation; House 2 wealth and House 11 gains determine how that foundation is
  funded.
- House 7 spouse outcomes often reflect the quality of House 4 domestic security
  and House 12 foreign or confinement risks.
- House 11 social network can rescue or amplify House 2 income and House 10
  ambition, especially when the 11th lord is strong and benefic.

## 3.7 Karma and release cascade

- House 8 longevity/crisis with House 6 health and House 12 loss is the karmic
  lifecycle axis for the chart.
- Positive House 12 outcomes should be confirmed by Jupiter or benefic support
  and often require House 9 spiritual context to be truly constructive.
- House 5 creativity/children and House 9 dharma anchor the chart’s purpose;
  House 12 then translates that purpose into surrender, release, or service.

## 3.8 Cross-house validation anchors

- Use House 9 travel/foreign flags to refine House 3 communication and House 7
  marriage-abroad signals.
- Use House 4 mother/vehicle and House 10 authority to validate whether career
  success is supported by home stability or is merely external reputation.
- Use House 12 loss and House 2 wealth together to distinguish runaway
  expenditure from charitable or spiritual giving.
- Use House 11 gain and House 3 sibling support to differentiate earned income
  from family-backed fortune.
- Use House 1 constitution with House 6 disease and House 8 longevity to build
  the health lifecycle diagnostic.

## 4. Implementation blueprint

### 4.1 Shared data model

Use shared domain objects:

- `HouseOutcome`:
  - `strength`, `quality`, `risk_flags`, `timing_flags`, `support_flags`
- `PlanetSignal`:
  - `planet`, `karaka_role`, `functional_role`, `navamsa_quality`, `hemmed_status`
- `VargaResult`:
  - `D9`, `D3`, `D8`, `D60`, `D2`, `from_moon`, `from_venus`
- `MarakaProfile`:
  - `maraka_flag`, `death_risk`, `prison_risk`, `spiritual_risk`

These objects let house engines share the same semantics.

### 4.2 House engine contract

Each house module should implement:

1. `compute_house_frame(chart)`
2. `compute_lord_frame(chart)`
3. `compute_karaka_frames(chart)`
4. `confirm_with_navamsa(chart)`
5. `apply_heming_and_penalties(chart)`
6. `assemble_output_profile()`

Special houses add custom steps:

- House 7: `compute_venus_as_lagna()`
- House 8: `compute_d8_timing()`
- House 2: `compute_dhana_lagna()`
- House 5: `compute_beeja_kshetra()`

### 4.3 Validation strategy

Validate each house with both house-specific anchors and cross-house anchors.
Examples:

- House 1: Papakartari/Navamsa overrides and 10th-house failure cases.
- House 2: 2nd-lord maraka timing and poverty blocks.
- House 3: elder vs younger sibling separation.
- House 5: fertility gating and adoption fallback.
- House 6: benefics in 6th increasing enemy counts.
- House 7: Venus-as-Lagna spouse death patterns.
- House 8: D8/D60 longevity fixtures.
- House 9: dual-karaka father vs fortune cases.
- House 10: career type by 10th lord placement.
- House 11: wish fulfillment vs earned income.
- House 12: loss vs spiritual release.

### 4.4 Regression clusters

Build regression cases that combine house interactions:

- Sun in Houses 1, 9, and 10.
- Jupiter in Houses 2, 5, 9, 11, and 12.
- Mars in Houses 3, 6, 7, and 10.
- Navamsa conflicts between Houses 1 and 4 or Houses 1 and 5.

These cross-house fixtures catch drift and preserve consistency.

## 5. Practical rules for the engine

### 5.1 Output naming conventions

Keep outputs consistent across houses:

- Use `_strength` for positive capacity.
- Use `_risk` for threats and losses.
- Use `_flag` for binary diagnostic signals.
- Use `_rating` for composite quality scores.

### 5.2 Reuse modifier patterns

Shared penalties and bonuses are high-value constructs:

- `papakartari_penalty`
- `subhakartari_bonus`
- `neechabhanga_bonus`
- `maraka_penalty`
- `navamsa_mitigation`

These modifiers should be implemented once and reused.

### 5.3 Always confirm with Navamsa

No positive house result is complete without a Navamsa check.
If the Rasi signal is strong but the D9 signal is weak, downgrade or qualify the
result. If the Rasi signal is weak and D9 is strong, use the D9 as a corrective
support signal.

### 5.4 Treat house results as layers

For every house, separate:

- What is promised by the house itself.
- What is promised by the lord.
- What is added or modified by karaka(s).
- What is confirmed or reversed by Navamsa.
- What is penalized by hemming or maraka.

Layering prevents one house from being treated as the whole story.

## 6. The treasure principle

The true value of Raman's model is not a list of isolated rules; it is the way
house signals are woven together by shared planets, shared frames, and shared
karma structures.

Use this document as the engine’s treasure map:

- Start with the shared architecture.
- Build consistent house contracts.
- Use the house table to keep each house’s core domain clear.
- Cross-check outputs with the family, wealth, and health threads.
- Validate with both house-specific and cross-house regression cases.

## 7. Execution checklist

### 7.1 Development priorities

- Create reusable frame evaluators for: house, lord, karaka, Navamsa, hemming,
  and special vargas.
- Keep each house engine pure and data-driven: input = chart state, output =
  `HouseOutcome`.
- Store modifiers centrally so `papakartari_penalty`, `subhakartari_bonus`, and
  `neechabhanga_bonus` behave consistently across all houses.

### 7.2 Validation priorities

- Use chart examples to verify that strong Rasi readings are downgraded when
  D9 is weak, and weak Rasi readings are rescued by a strong D9.
- Test maraka signals in Houses 2, 7, 8, and 12 with both positive and negative
  income cases.
- Confirm sibling logic by comparing House 3 younger sibling outputs with House
  11 elder sibling outputs.

### 7.3 Delivery priorities

- Document each house engine with its primary outputs and key confirmation
  frames.
- Provide a short glossary for terms such as `karaka_strength`, `hemmed_status`,
  `maraka_flag`, and `release_potential`.
- Ship the engine with a concise “top-12 house rules” cheat sheet for reviewers.

## 8. Glossary of core engine terms

- `house_frame`: the Rasi house evaluation for occupancy, lords, aspects, and
  sign strength.
- `lord_frame`: the house lord’s placement, dignity, exchange, and aspect-based
  score.
- `karaka_frame`: planet-specific business rules used to interpret a house’s
  sub-domain.
- `navamsa_check`: the `D9` confirmation layer that moderates or validates Rasi
  signals.
- `hemmed_status`: a combined indicator of Papakartari, Subhakartari,
  Neechabhanga and related functional dignity effects.
- `maraka_flag`: a binary or graded signal showing death/release potential from
  2/7/8/12 influence.
- `support_flag`: an auxiliary positive signal from secondary frames such as the
  Moon, Venus, or special vargas.
- `release_potential`: positive spiritual or karmic liberation in House 12.
- `issue_potential`: House 5 creative/fertility potential gated by functional
  strength.
- `fortune_rating`: a composite score combining house, lord, karaka, and D9.
- `risk_bucket`: one of `{health, wealth, reputation, relationships, karma}`.
- `functional_role`: planet behavior in the chart context, which may differ from
  natural benefic/malefic qualities.
- `from_moon` / `from_venus`: derived evaluation frames using the Moon or Venus as
  an alternate ascendant.

## 9. Rule composition patterns

### 9.1 Scoring pattern

- Base score = `house_frame` + `lord_frame`.
- Karaka modifiers adjust the base score by sub-domain relevance.
- Navamsa applies a validation factor and may downgrade or support the result.
- Hemming and maraka are penalty factors; Subhakartari and Neechabhanga are
  bonus factors.

### 9.2 Gating pattern

- Use gating conditions to block a result when a critical requirement is absent.
- Example: House 5 may generate `issue_potential` only when the 5th lord is
  functionally strong and the house is not heavily afflicted.
- Example: House 12 may generate `release_potential` only when Jupiter or
  benefics support the 12th house alongside a weak material outcome.

### 9.3 Override pattern

- Clear contradictions should trigger overrides rather than additive blending.
- Example: a strong Rasi reading with a very weak D9 should be qualified or
  demoted rather than treated as fully positive.
- Example: a favorable spouse outcome from House 7 should still carry a
  `maraka_flag` if Venus-as-Lagna danger rules are active.

### 9.4 Aggregation pattern

- Build final chart outputs by aggregating house-level results along shared
  threads: family, wealth, health, timing.
- Use normalized scores so House outcomes remain comparable across different
  domains.
- Keep flags and ratings separate so a single house can contribute both positive
  capacity and risk warnings.

## 10. Compact synthesis for reviewers

- The shared architecture is the anchor: house frame + lord frame + karaka
  frame + Navamsa + modifier layer.
- The primary validation engine is `D9`; secondary validation is `D3`, `D8`,
  `D60`, and derived frames.
- The highest-value house threads are family (3/5/9/11), wealth (10/2/11/12),
  and health/longevity (1/6/8/12).
- The engine should be built as a set of composable house modules with uniform
  outputs and reusable modifiers.

## 11. Practical engine recipe

Use this recipe to turn the synthesis into working code:

1. Parse chart state into a shared model containing house positions, lords,
   aspects, and varga placements.
2. Build reusable evaluators:
   - `evaluate_house_frame(house, chart)`
   - `evaluate_lord_frame(house, chart)`
   - `evaluate_karaka_frames(house, chart)`
   - `evaluate_navamsa(chart, house)`
   - `evaluate_special_varga(chart, house)`
3. For each house, compute:
   - `house_base = evaluate_house_frame(...)`
   - `lord_base = evaluate_lord_frame(...)`
   - `karaka_adjustment = evaluate_karaka_frames(...)`
   - `navamsa_adjustment = evaluate_navamsa(...)`
   - `modifier_adjustment = apply_heming_and_maraka(...)`
4. Assemble a `HouseOutcome`:
   - `strength = house_base + lord_base + karaka_adjustment`
   - `quality = fortune_rating(house, navamsa_adjustment, modifier_adjustment)`
   - `risk_flags = collect_risk_flags(...)`
   - `timing_flags = collect_timing_signals(...)`
5. Aggregate all house outcomes into chart-level summaries by thread:
   - family = merge_outcomes([house3, house5, house9, house11])
   - wealth = merge_outcomes([house2, house10, house11, house12])
   - health = merge_outcomes([house1, house6, house8, house12])
6. Run regression fixtures and compare outputs against the house anchor rules.

## 12. Top-12 rule checklist

- House 1: Lagna strength must be confirmed by Moon + 10th house support.
- House 2: Wealth must be gated by 2nd-from-Moon / D2 clarity.
- House 3: Younger siblings belong to House 3; elder siblings belong to House 11.
- House 4: Mother/property happiness requires Moon/Jupiter strength and Navamsa.
- House 5: Fertility is a gating condition; Jupiter alone is not enough.
- House 6: Benefics in the 6th increase service/litigation rather than remove risk.
- House 7: Venus-as-Lagna danger rules are mandatory for spouse output.
- House 8: Longevity requires D8 timing + D60 karmic confirmation.
- House 9: Father = Sun, Dharma = Jupiter; do not collapse these roles.
- House 10: Career type depends on 10th lord placement; reputation depends on the
  broader ascendant network.
- House 11: Wish fulfillment requires both 11th lord strength and income support.
- House 12: Loss is real when afflicted; release is only positive when Jupiter or
  benefics support the 12th.

## 13. How to use this synthesis

- Use Section 1 for architecture and engine structure.
- Use Section 2 for house domains and core business rules.
