# Compendium Extraction Guide

Contract for extraction sweeps. Every draft record passes the deterministic
merge gate (`python -m app.medini.doctrine.tools.sweep`) which verifies the
quote against the pinned OCR, assigns the printed page mechanically,
schema-validates, and compiles the antecedent. **A single unverifiable
quote or unknown DSL op rejects the whole draft file.**

## Draft record (one JSON object per line)

```json
{"id": "raman.hpa.xiv.balarishta_moon_kendra_malefics",
 "book": "hpa",
 "quote": "The Moon in a kendra (quadrant) with malefics.",
 "domain": "longevity",
 "rule_type": "graha_effect",
 "antecedent": {"op": "all", "args": [
   {"op": "planet_in_house", "planet": "Moon", "house": "kendra"},
   {"op": "planet_in_house", "planet": "malefic", "house": "kendra"}]},
 "consequent": {"polarity": "unfavorable", "magnitude": "strong",
   "timing": null, "text": "Produces Balarishta (infant mortality)."},
 "inputs_required": ["planet_houses"],
 "computability": "partial",
 "ambiguity_notes": "'with malefics' read as same-kendra-house; the DSL any-kendra form is looser than co-occupancy.",
 "provenance": {"sweep_id": "p4_t1", "extractor": "agent", "chapter": "XIV"}}
```

Omit `quote_sha256`, `page`, `quote_verified`, `archive_item`,
`conflicts_with`, `supersedes` — the gate stamps them.

## Quotes — the honesty gate

- Copy the OCR **verbatim**, including its typos ("Rajayogakamka",
  "Aries*"). Never paraphrase, never fix spelling.
- You MAY join hyphenated line breaks (`combi- nation` → `combination`)
  and collapse whitespace — matching is tolerant of exactly that.
- Do NOT let a quote span a printed page break (a standalone folio line
  or a running head interrupts the text and the match fails). Quote the
  contiguous span that states the rule; ≥ 20 chars.
- One rule per doctrinal claim. A yoga's `Definition` becomes the
  antecedent, its `Results` the consequent text; quote the span covering
  both when contiguous, else quote the Definition and put the Results
  wording in `consequent.text` prefixed `Results:` with a second record
  only if the Results state a separable claim.

## id scheme

`raman.<book>.<chapter>.<slug>` — chapter is the lowercase label
(`xiv`, `26`, or the yoga number for three_hundred: `y042`); slug is a
short snake_case name. Corrections mint `_r2`, never edits.

## Computability (decides antecedent)

- `full` — antecedent completely expresses the condition in DSL.
- `partial` — DSL captures the main condition; quote the un-encoded
  remainder in `ambiguity_notes`.
- `manual` — needs data we don't carry (birth-time-of-day rituals,
  omens): `antecedent: null`.
- `unfalsifiable` — prose with no testable condition: `antecedent: null`.

Qualifiers like "if strong" compile to `{"op": "strong", "planet": X}`
(threshold is an engine setting, recorded as an encoding decision).

## DSL reference (combinators: all, any, not, count_gte{n,args})

Frames: every house-valued op takes optional `"frame"`:
`lagna` (default) | `moon` | `navamsa` | `arudha` | `karakamsa`.

| op | args |
|---|---|
| lagna_sign_is | sign (name or 1..12), frame? |
| planet_in_house | planet (name, list, "malefic", "benefic"), house (int, list, "kendra"/"trikona"/"dusthana"/"upachaya"/"maraka"), frame? |
| planet_in_sign | planet, sign |
| planets_conjunct | planets (list), frame? |
| lord_of_house_in_house | of_house, in_house (int/list/group), frame? (lagna/moon) |
| planet_is_lord_of | planet, house |
| planet_aspects_house | planet (or class), house (int/list/group) |
| planet_aspects_planet | planet, target |
| varga_sign_is | planet, divisor (1..60 of the 16), sign |
| varga_lord_is | planet, divisor, lord (name/list) |
| vargottama | planet |
| dignity_is | planet, state (exalted/own/debilitated/friendly/neutral/inimical, or list) |
| exalted / debilitated / own_sign | planet |
| strength_gte | planet, value (0..1) |
| strong | planet |
| combust | planet |
| waxing_moon | — |
| yoga_present | yoga (adhi/lakshmi/saraswati/daridra/chamara/vipareeta/parivartana/kala_sarpa/neech_bhanga) |
| av_bindus_gte | planet, value, sign? (default: planet's own sign) |
| sav_bindus_gte | house, value |
| reduced_av_total_cmp | planet, cmp (gte/lte/eq), value |
| tara_class | planet, tara (1..9 or list) |
| dasha_lord_is | planet (or list), level? (md/ad) — timeline-only |
| karaka_is | planet — atmakaraka |
| occupies_khara / occupies_chidra | planet, orb? |

Escape hatch: `"antecedent": "impl:python:<id>"` ONLY for registered
impls — do not invent ids; propose new impls in `ambiguity_notes` instead
and mark the rule `partial` with the closest DSL encoding.

## Enums

- domain: general, longevity, health_body, mind_character, wealth, family,
  siblings, education, property, children, enemies_obstacles, marriage,
  inheritance_occult, fortune_father, career, fame, gains, losses_moksha
- rule_type: yoga, bhava_judgment, graha_effect, functional_role,
  dasha_timing, transit, strength, cancellation, electional, prasna,
  definition, method
- polarity: favorable, unfavorable, mixed, neutral; magnitude: slight,
  moderate, strong, null
- timing: null or {mode: dasha|bhukti|transit|age_band|election,
  of?: planet or "lord_of_<n>", detail?: str}

## inputs_required (informational, snake_case)

The chart data the rule consumes: lagna_sign, planet_houses, planet_signs,
aspects, varga_signs, dignity, strength, combustion, moon_phase,
ashtakavarga, dasha_context, nakshatra, sensitive_points.
