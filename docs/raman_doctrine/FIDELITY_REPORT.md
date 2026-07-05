# Raman Doctrine Compendium — Fidelity Report (Gate 1 + full-system P7)

"Truest to Raman" is measured here, not asserted. The gate runs on every
commit (`tests/doctrine/test_fidelity.py`).

## Mechanism fidelity (constructed golden charts)

Each chart is hand-built from a rule's **prose** definition — never from its
encoded antecedent — then the encoded antecedent is evaluated. A positive
case must fire; a control (one clause deliberately broken) must stay quiet.
A divergence is a real encoding bug. Cases: `data/raman_doctrine/golden_cases.json`.

- Distinct rules covered: **20** (HPA, HTJAH Vol 1, Three Hundred, Prasna
  Marga Part 2, Studies in Jaimini)
- Cases: 37 (20 positive, 17 control)
- **Precision: 1.000  Recall: 1.000  Accuracy: 1.000**
- Polarity agreement (firing rule vs. Raman's verdict): **1.000**
- Frames exercised: lagna, moon, **arudha** and **karakamsa** — the last two
  built from explicit longitudes (a fixed Atmakaraka), so the frame-derived
  antecedents (Jaimini karakamsa education, Arudha wealth) are gate-covered,
  not just the sign-placement rules.

The table below lists the tranche-1 rules; the P7 additions (12 rules from
Prasna Part 2 marriage/progeny and Jaimini karakamsa/arudha) are exercised by
the same gate and enumerated in `data/raman_doctrine/golden_cases.json`.

| rule | golden chart | expected | fired | result |
|---|---|---|---|---|
| `y001.gajakesari` | Jupiter in the 4th from the Moon (kendra) | True | True | PASS |
| `y001.gajakesari` | control: Jupiter in the 2nd from the Moon (not a kendra) | False | False | PASS |
| `y007.adhi` | benefic in the 7th from the Moon | True | True | PASS |
| `y007.adhi` | control: no benefic in the 6/7/8 from the Moon | False | False | PASS |
| `y002.sunapha` | Mars in the 2nd from the Moon | True | True | PASS |
| `y002.sunapha` | control: no planet in the 2nd from the Moon | False | False | PASS |
| `xvii.aries_key_planets` | Aries lagna | True | True | PASS |
| `xvii.aries_key_planets` | control: Taurus lagna | False | False | PASS |
| `xvii.virgo_key_planets` | Virgo lagna | True | True | PASS |
| `ch4.lagna_lord_in_7` | Aries lagna, its lord Mars in the 7th | True | True | PASS |
| `ch4.lagna_lord_in_7` | control: Aries lagna, Mars in the 1st | False | False | PASS |
| `ch5.lord2_in_11` | Aries lagna, 2nd lord Venus in the 11th | True | True | PASS |
| `xv.sun_venus_kendradhipatya_maraka` | Cancer lagna: the Sun owns the 2nd (Leo) -> sure maraka | True | True | PASS |

## Printed-chart smoke (Raman's own horoscopes)

B. V. Raman's worked charts (printed positions, his ayanamsa) are evaluated
through the entire executable compendium. Every rule must evaluate without
interpreter error, and at least one rule must fire.

| chart | compendium rules fired |
|---|---|
| Bala Gangadhara Tilak | 81 |
| Mahatma Gandhi | 91 |
| Sri Ramana Maharshi | 79 |
| Albert Einstein | 83 |
| Jawaharlal Nehru | 81 |

## Full-system run (P7)

The whole enlarged compendium — **937 records across 10 books, 709 with an
executable antecedent** — was evaluated end to end on Raman's five printed
horoscopes. Every rule — including the HPA planets-in-bhavas/signs enumerations
and the frame-heavy karakamsa/arudha/prasna rules — evaluates cleanly:

- **0 interpreter errors** across 709 rules × 5 charts (3,545 evaluations).
- computability mix: full 533 · partial 176 · manual 131 · unfalsifiable 97.

The P7 domain engine (`domains/houses.py`) was then run per chart — each of
the 12 houses read both by the fired compendium rules and by the three-pillar
`bhava_judge` verdict, reported side by side:

| chart | domain rules fired | houses agreeing with framework |
|---|---:|---:|
| Bala Gangadhara Tilak | 54 | 10 / 12 |
| Mahatma Gandhi | 61 | 6 / 12 |
| Sri Ramana Maharshi | 52 | 7 / 12 |
| Albert Einstein | 57 | 9 / 12 |
| Jawaharlal Nehru | 48 | 10 / 12 |

Agreement is *observed, not enforced*: the compendium reading and the framework
scorer are independent by design ("activation, not mutation"), so divergences
are signal — houses where Raman's book-level doctrine and the classical scorer
point different ways — not failures. The zero-error and domain-engine passes
are enforced on every commit by
`tests/doctrine/test_fidelity.py::TestFullSystemP7`.

## Thresholds (gate)

- Mechanism precision == 1.0 and recall == 1.0 (no encoded antecedent may
  diverge from its prose on the golden set).
- Polarity agreement == 1.0.
- Every printed chart evaluates without error and fires >= 1 rule.
- Full-system: every executable rule evaluates without interpreter error on
  every printed chart (0 errors over the 745-record compendium).

All thresholds met through P7. The golden set grows with each tranche;
mechanism-overlap Jaccard against Raman's *named* mechanisms on the printed
death charts is wired (`score.mechanism_jaccard`) and expands as the
longevity-mechanism rules gain their fired-id tags.
