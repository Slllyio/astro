# Raman Doctrine Compendium — Fidelity Report (Gate 1, tranche 1)

"Truest to Raman" is measured here, not asserted. The gate runs on every
commit (`tests/doctrine/test_fidelity.py`).

## Mechanism fidelity (constructed golden charts)

Each chart is hand-built from a rule's **prose** definition — never from its
encoded antecedent — then the encoded antecedent is evaluated. A positive
case must fire; a control (one clause deliberately broken) must stay quiet.
A divergence is a real encoding bug. Cases: `data/raman_doctrine/golden_cases.json`.

- Distinct rules covered: **8** (across HPA, HTJAH Vol 1, Three Hundred)
- Cases: 13 (8 positive, 5 control)
- **Precision: 1.000  Recall: 1.000  Accuracy: 1.000**
- Polarity agreement (firing rule vs. Raman's verdict): **1.000**

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
| Bala Gangadhara Tilak | 54 |
| Mahatma Gandhi | 65 |
| Sri Ramana Maharshi | 52 |
| Albert Einstein | 54 |
| Jawaharlal Nehru | 53 |

## Thresholds (gate)

- Mechanism precision == 1.0 and recall == 1.0 (no encoded antecedent may
  diverge from its prose on the golden set).
- Polarity agreement == 1.0.
- Every printed chart evaluates without error and fires >= 1 rule.

All thresholds met at tranche 1. The golden set grows with each tranche;
mechanism-overlap Jaccard against Raman's *named* mechanisms on the printed
death charts is wired (`score.mechanism_jaccard`) and expands in P6 as the
longevity-mechanism rules gain their fired-id tags.
