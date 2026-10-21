# Merge verdict review — the 78 doctrine-snapshot moves (2026-10-21)

User decision A: review the 78 verdict changes the main merge (4c3cbc4e) introduced against the
doctrine snapshot frozen at 2d65fe57, before re-freezing anything. **Nothing is re-frozen and no
verdict code is changed by this review.** Golden ratchet throughout: 286/397 exact, 362/397
within-1, 35 real errors.

## Method

1. **Diff.** `tools/raman_saab/doctrine_snapshot` frozen (2d65fe57) vs live (claude/merge-fix):
   78 diffs, all of kind VERDICT, over 29 (chart, house) pairs on 26 charts.
2. **Global toggle.** Restricting `yogas.YOGAS` to the 72 pre-merge ids makes the diff **0**.
   Every one of the 78 is caused by main's new yogas; nothing else in the merge moves a verdict.
3. **Per-yoga attribution.** For each moved key, each new yoga firing on that chart was tested
   as *sufficient* (pre-merge set + that yoga reproduces the move) and *necessary* (all yogas
   minus that yoga undoes it). Where no single yoga is necessary, the move has several
   independent sufficient causes and is listed under all of them.
4. **Mechanism.** All moves go through `judges/house_template.py`: the kind-scoped yoga
   modulation (`_yoga_scope_kinds` + the yoga-shift block) and the H11 dhana floor. A fired yoga
   shifts a borderline verdict by its **`kind` tag alone** — any `dhana` yoga on H11
   gains/acquisitions (the floor may even override a decisive `afflicted`), any `raja` yoga on
   H9/H10 fortune/career, any `arishta` yoga on H1 self/body/health. This was calibrated on the
   pre-merge set, where `dhana`/`raja` meant 2/11 and 9/10 lordship combinations and `arishta`
   meant Sakata/Kemadruma. Main's 3HC encoding tags 113 yogas with the same kinds but **without
   saying which house or matter each one is about.**
5. **Scored coverage.** Only 1 of the 29 moved (chart, house) pairs carries a confirmed Raman
   expectation (NH.chart_75 H10, career=mixed, whose own sub-verdict did not move). That is why
   the ratchet held: playbook rule 4's coverage-gap blindness, not evidence of correctness.

The mechanism's own citation is consideration 4 of HTJAH-I:480-482: *"Whether the influence has
been altered by any yogas occurring in any particular house or houses."* Raman ties a yoga to
**the house it occurs in**, not to its kind label.

## Cause groups

| # | Cause | Diffs | Charts | Fire rate (346 goldens) | Class |
|---|---|---|---|---|---|
| 1 | Bhagya (241) → H11 dhana floor | 30 | 14 | 19.1% | **(b)** |
| 2 | Raja 246/250/252/258/260/262 → H9/H10 lift | 29 | 9 | 2.9–72.0% | **(b)**, plus a (c) rollup sub-issue |
| 3 | Arishta, progeny curses → H1 self | 8 | 2 | 2.0–13.3% | **(b)** |
| 4 | Arishta, Vrana/Guhyaroga/Sirachchheda → H1 self | 4 | 1 | 3.2–9.2% | **(c)** |
| 5 | Vishnu (62) → H11 dhana floor | 4 | 2 | 1.2% | **(a)** |
| 6 | Lakshmi (72) → H11 dhana floor | 3 | 1 | 6.1% | **(a)**, friends key (c) |

Total 30 + 29 + 8 + 4 + 4 + 3 = 78.

### 1. Bhagya → H11 gains (30) — (b) contradicts Raman

Charts: HTJAH-I chart_53, chart_55, h5_05, h5_06, h5_11, h6_08, x93; HTJAH-II h7_04, x152,
x173, x186; NH chart_61, chart_63, chart_75. Bhagya is the sole necessary cause on every key.
Seven keys go `afflicted -> favourable`, i.e. the dhana floor overrides a decisive affliction.

- Definition (3HCC:7989-7990): *"A strong benefic should be in Lagna, the 3rd or 5th,
  simultaneously aspecting the 9th."* Result (3HCC:7991-7992): *"extremely fortunate,
  pleasure-loving and rich."* It is a 9th-house (fortune) combination. Main's encoder tagged it
  `kind="dhana"`, which routes it into the H11 gains floor; no Raman text links it to the 11th.
- Raman's own qualification is not encoded (3HCC:8003-8010): *"due consideration must be given
  to the nature of the ownership of the benefic concerned before actually evaluating the yoga
  … The same yoga forming from Mithuna becomes almost ineffective because of Kendradhipatya
  dosha."* `_Bhagya` checks strength (B1) but not ownership.
- Fix direction (not applied): encode the ownership/Kendradhipatya clause in `_Bhagya`, and
  stop the H11 floor from consuming a yoga whose house is the 9th (or retag it).

### 2. Raja 246–262 → H9/H10 (29) — (b) contradicts Raman

Charts: HTJAH-I h4_04, h5_06; HTJAH-II x37, x63, x117, x135, x175, x180; NH chart_75. Mostly
several raja yogas are each sufficient. Raja-258 is the sole necessary cause on x135.

- Results are rulership (3HCC:8155 *"becomes a famous king"*; 8424/8566 *"a ruler or an equal
  to him"*; 8831 *"a great man or a respected ruler"*), so H10 career/status is the right
  matter. **But the lift fires on bare presence**, and Raman forbids exactly that
  (3HCC:8580-8584): *"The theoretical presence of Raja yogas is of no consequence unless the
  Raja Yogas have inherent vitality to produce the results ascribed to them. The student must
  first learn to pick up Raja yogas and then weigh their relative strengths and weaknesses."*
- Measured: Raja-258 fires on **72.0%** of goldens, Raja-250 39.0%, Raja-246 37.9%,
  Raja-262 25.7%. A lift present on most charts is non-differential.
- Fix direction (not applied): gate the raja lift on the yoga-forming planets' strength, the
  way the dhana floor already gates on its pillars.
- **Sub-issue (c), engine design, 3 keys:** on HTJAH-I h5_06, HTJAH-II x117 and NH chart_75 the
  H10 headline falls `mixed -> afflicted` while the only sub-matter change is
  profession_trade rising `mixed -> favourable`. Cause: `house_template._rollup` returns
  `mixed` whenever mixed and favourable are both present, *even with an afflicted sub-matter
  present*. Lifting the sole `mixed` lets the afflicted one through. That masking predates the
  merge; the yoga only exposed it. Which rollup is intended (worst-decided always, or the
  current masking) is not a Raman text question; it needs a user call.

### 3. Progeny-curse arishtas → H1 self/body/health (8) — (b) contradicts Raman

HTJAH-II x71 (Pitrusapa Sutakshaya or Kalanirdesat Putranasa, each sufficient) and NH chart_32
(Sarpasapa or Kalanirdesat Putranasa). All four keys of H1 go `mixed -> afflicted`.

- Sarpasapa (3HCC:6891): *"The 5th should be occupied by Rahu and aspected by Kuja"*.
  Pitrusapa Sutakshaya (3HCC:7017-7018): *"The subject will lose issues on account of his
  father's wrath."* Kalanirdesat Putranasa (3HCC:7487): *"Rahu must occupy the 5th house …"*.
  Raman's subject is the progeny, the 5th house. Nothing in the text bears on the native's own
  body, health or self, which is all the H1 arishta scope covers.
- Fix direction (not applied): scope these to H5 children/progeny, or exclude them from the
  H1 arishta drop.

### 4. Vrana / Guhyaroga / Sirachchheda → H1 self/body/health (4) — (c) needs a doctrine call

HTJAH-II h12_01. Each of the three is independently sufficient.

- **Vrana supports the move.** Raman (3HCC:8930-8935): *"The presence of 6th lord, whether a
  benefic or malefic, in Lagna is always held to deplete the vitality of the horoscope.
  Probably, the malefic 6th lord, in addition to weakening the general structure of the
  horoscope, would also cause physical troubles."* But in the same Remarks (3HCC:8923-8924):
  *"A literal application of the yoga is not at all recommended."*
- Guhyaroga (3HCC:9719-9720, disease of the private parts) and Sirachchheda (3HCC:9344-9345,
  manner of death) are about disease and death, not the self as such.
- The question for the user: may a disease yoga whose Remarks speak of depleted vitality drop H1
  body/health, given Raman's own caution against literal application?

### 5. Vishnu → H11 gains (4) — (a) faithful, accept

HTJAH-I x65, HTJAH-II h12_14; Vishnu is the sole necessary cause; both go `afflicted -> mixed`
(the weak-pillar arm of the floor). Result (3HCC:3499-3500): *"acquire fortunes from various
countries, earn in lakhs"* — wealth and gains in Raman's words. Fires on 1.2% of goldens.

### 6. Lakshmi → H11 (3) — (a) faithful, accept; the friends key is (c)

HTJAH-II x164, `mixed -> favourable` on acquisitions, gains and friends. Raman (3HCH:1563):
*"Lakshmi has predominantly to do with wealth and one born in this combination will be
wealthy, the degree of wealth varying with regard to the degree of strength or weakness of the
planets causing the Yoga"*. The dhana floor's strength gate fits that sentence.
**Caveat:** H11/friends also moves here (and with Bhagya on NH chart_61). It moves because that
signification carries a `gains` rule tag. A wealth yoga lifting *friends* is not textual; that
tag scope is a (c) call.

## What needs the user

1. **Groups 1–3 (67 diffs) contradict Raman's text.** Re-freezing them would bless known
   errors. Fix first (the directions above) or accept them knowingly. Fixing is verdict-code
   work and was out of scope for this review.
2. **Group 4 (4 diffs):** does Vrana's "depletes vitality" justify an H1 drop despite "a
   literal application … is not at all recommended"?
3. **Rollup (3 headline keys in group 2):** should `_rollup` keep masking an afflicted
   sub-matter whenever mixed and favourable co-occur?
4. **Friends scope (2 keys in groups 1 and 6):** should a wealth yoga reach H11/friends?
5. **Groups 5–6 (7 diffs)** are faithful and can be re-frozen as they stand.

## Fix applied (2026-10-21, user decision "fix the yoga step before re-freezing")

**78 → 17 snapshot diffs. Golden ratchet unchanged: 286/397, 362/397, 35.**
`pytest tests/raman_saab`: 2 failed / 7250 passed. The two failures are the held re-freezes.

- `doctrine/yoga_routes.py` (new): each yoga that may modulate names the house and sub-matter
  its own text concerns. **A yoga not in the table modulates nothing.** `house_template`
  (`_yoga_modulate` and the H11 dhana floor) now routes by yoga, not by kind; the kind still
  sets the direction. Pre-merge HTJAH/3HC/HPA-20 yogas keep exactly the reach they were
  calibrated on, except that wealth is narrowed (below).
- **Bhagya** → H9 fortune only. Raman's ownership clause is now encoded in `_Bhagya`: a benefic
  with Kendradhipati dosha (HTJAH-I:583) does not form it (3HCC:8003-8010; "almost ineffective"
  is read as not formed, the conservative variant). Pinned on both of Raman's examples
  (Cancer Jupiter forms it, Mithuna Jupiter does not).
- **Progeny curses** (Sarpasapa, Pitru/Matru/Bhratru-sapa, Pretasapa, Kalanirdesat Putranasa,
  Putrakalatraheena, Vamsacheda) → H5 children only, never H1.
- **Wealth yogas** (Vishnu, Lakshmi, and the pre-merge Dhana yogas) → H2 wealth and H11
  gains/acquisitions only. They no longer reach friends, elder siblings, family, speech or
  vision, which carry a `wealth`/`gains` rule tag but are not wealth.
- **Raja yogas of the completed 3HC (245-263) and Indra** modulate nothing.
  3HCC:8580-8584 makes them conditional on "inherent vitality" but **defines no test** that
  could be encoded without inventing one. FLAGGED: they surface as metadata only until a cited
  vitality test exists. The pre-merge HTJAH lordship raja yogas keep their reach. Whether the
  vitality remark also governs them is open (see below).
- **Unchanged by instruction:** the bodily-affliction / manner-of-death arishtas (Vrana,
  Guhyaroga, Sirachchheda and the rest of that class) keep the H1 reach, pending decision 3;
  `_rollup` is unchanged. Spouse yogas (Kalatrashanda, Vikalangapatni) name H7, which the yoga
  step does not wire, so they modulate nothing (flagged).

### The 17 remaining diffs, re-reviewed

| Cause | Diffs | Charts | Class |
|---|---|---|---|
| Vishnu → H11 gains/acquisitions | 4 | HTJAH-I x65, HTJAH-II h12_14 | (a) "earn in lakhs" (3HCC:3499-3500) |
| Lakshmi → H11 gains/acquisitions | 2 | HTJAH-II x164 | (a) "predominantly to do with wealth" (3HCH:1563) |
| Wealth reach narrowed: Dhana-Chain / Lakshmi no longer lift H11 friends/elder siblings | 3 | HTJAH-I chart_44 | (a) HTJAH-I:2480 names only wealth: "acquires great wealth" |
| Wealth reach narrowed: Dhana-Exch / Dhana-Chain no longer lift H2 family/speech/vision | 4 | HTJAH-I x7 | (a) HTJAH-I:2709 "Financial prosperity"; HTJAH-I:2480 |
| Vrana / Guhyaroga / Sirachchheda → H1 | 4 | HTJAH-II h12_01 | **(c) pending decision 3, left as is** |

None of the 6 moved (chart, house) pairs carries a confirmed Raman expectation.

**Not re-frozen.** 13 of the 17 are faithful. The 4 h12_01 keys are pending decision 3, so
"every remaining change is faithful" does not hold yet. Neither the doctrine snapshot nor yoga
liveness was re-frozen. Once decision 3 is made, both can be re-frozen in one step.

### Open for the user

1. **Decision 3** (Vrana-class arishtas on H1): it unblocks the re-freeze.
2. **Pre-merge raja yogas:** does Raman's "inherent vitality" remark (3HCC:8580-8584) also govern
   the HTJAH-I lordship raja yogas (Raja-KT/910X/910A, Vipareeta, HPA-20 Chamara et al.)? They
   still lift H9/H10 on presence. Turning them off is a verdict change and would need its own
   ratchet measurement.
3. **A cited raja vitality test:** if one exists elsewhere in Raman (HTJAH, HPA), encoding it
   would let the 3HC raja yogas modulate again.
4. **Spouse yogas → H7:** wire them, or keep them non-modulating?
5. **"H11 gains" includes acquisitions**, the key set the dhana floor has always used.
   Confirm or narrow to gains alone.

## Reproduction

The scratch scripts used (not committed) were: snapshot diff dump; global toggle (`YOGAS`
restricted to the 2d65fe57 id set → 0 diffs); per-key sufficient/necessary attribution;
`_rollup` sub-verdict dump; fire rates over the 346 castable goldens; scored-expectation
overlap. Each is a few lines over `tools.raman_saab.doctrine_snapshot` and
`tests/raman_saab/test_goldens`.
