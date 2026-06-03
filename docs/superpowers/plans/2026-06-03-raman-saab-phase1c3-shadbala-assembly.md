# Raman Saab — Phase 1c-3 (capstone): Shadbala Assembly + Verdict + Ishta/Kashta — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Tie all six Graha-Bala components into the **total Shadbala** (`ShadbalaBreakdown`, Rupas) with the **min-required "powerful" verdict**, and add **Ishta/Kashta Phala** — both pinned to Raman's worked "Standard Horoscope" totals. This is the capstone that proves the whole strength engine reconciles.

**Architecture:** `shadbala/total.py` (`assemble_shadbala` sums the 6 components — Drik signed — into a `ShadbalaBreakdown`; `is_powerful` compares total Rupas to the per-planet thresholds). `shadbala/ishta_kashta.py` (√-mean of Ochcha & Cheshta, incl. the Sun/Moon Cheshta surrogates). Both pure. The component computations + their fixtures already exist (1c-1, 1c-2a, 1c-2b).

**Tech Stack:** Python 3.12, frozen dataclasses, pytest. No `app/core`.

**Scope.** IN: `shadbala/total.py`, `shadbala/ishta_kashta.py`, fixture pins. OUT (1c-3 continuation, a later round): Bhava-bala (`shadbala/bhava_bala.py`); wiring `PlanetPos.shadbala_rupas/ishta/kashta` via the adapter; the backfills (maraka `strength_rank`+weakest-planet, balarishta strength, navamsa64 pin, Ahargana Kala lords, the Mars/Venus-Ayana & Saptavargaja-cusp xfail decisions).

**Authority:** `docs/raman_saab/gbb_shadbala_reference.md` §7 (assembly + thresholds), §9 (Ishta/Kashta), §10 (fixture). Both formulae **verified live** against Raman's worked totals before this plan.

---

## Doctrine (verified live)

**Total (GBB-8:262):** `ShadbalaPinda(Sh) = Sthana + Dik + Kala + Cheshta + Naisargika + Drik` (Drik is
**signed** — added, since it already carries its sign). `Rupas = Sh / 60`. Verified vs the fixture
component values → Total-Rupas: Sun 6.288 · Moon 6.936 · Mars 5.381 · **Mercury 9.674** · Jupiter
7.381 · Venus 5.949 · Saturn 6.196.
> **Book OCR note:** the printed "Mercury 9.743" (reference §10) is wrong — Mercury's six cited
> components sum to 580.46 Sh = **9.674** Rupas (9.743×60=584.58 ≠ 580.46). Pin **9.674**; the verdict
> (≥7 → powerful) holds either way.

**Min-required Shadbala (Rupas), GBB-8:303-312:** Sun 5 · Moon 6 · Mars 5 · Mercury 7 · Jupiter 6.5 ·
Venus 5.5 · Saturn 5. A planet is "powerful" iff total ≥ its threshold. Fixture: **all 7 powerful**
(Mercury strongest, Mars weakest — GBB-8:317).

**Ishta/Kashta (GBB-10), Shashtiamsas 0-60:**
```
Ishta  = sqrt(OchchaBala × ChestaBala)
Kashta = sqrt((60 − OchchaBala) × (60 − ChestaBala))
```
**Sun/Moon Chesta surrogates (here only):** Sun `CK = (Sayana_lon + 90)`, fold >180 → 360−, /3
(= 23.2 for the fixture); Moon `CK = (Moon − Sun)%360`, fold, /3 (= 44.2). Verified vs fixture
(all 7 ≤0.05): e.g. Venus Ishta 3.63/Kashta 55.94, Jupiter 44.56/9.73, Saturn 27.11/31.26.

---

## File structure

| File | Responsibility |
|---|---|
| `app/raman_saab/primitives/shadbala/total.py` | `assemble_shadbala(sthana,dig,kala,cheshta,naisargika,drik) -> ShadbalaBreakdown` · `is_powerful(planet, total_rupas) -> bool` · `MIN_REQUIRED` |
| `app/raman_saab/primitives/shadbala/ishta_kashta.py` | `ishta_phala`, `kashta_phala`, `sun_chesta_surrogate`, `moon_chesta_surrogate` |
| `tests/raman_saab/primitives/shadbala/test_total.py` | assembly + verdict, fixture-pinned |
| `tests/raman_saab/primitives/shadbala/test_ishta_kashta.py` | Ishta/Kashta, fixture-pinned |

---

## Task 1: Total Shadbala assembly + min-required verdict

**Files:** Create `app/raman_saab/primitives/shadbala/total.py`; Test `.../shadbala/test_total.py`

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import total
from app.raman_saab.chart.model import ShadbalaBreakdown

# GBB Standard Horoscope component values (Shashtiamsas): (sthana,dig,kala,cheshta,naisargika,drik)
_COMP = {
 "Sun":    (147.975, 48.070, 104.490,  0.000, 60.000,  16.720),
 "Moon":   (141.650, 32.250, 202.750,  0.000, 51.430, -11.900),
 "Mars":   (194.700, 55.030,  28.390, 22.280, 17.140,   5.350),
 "Mercury":(294.800, 21.860, 219.920,  2.130, 25.700,  16.050),
 "Jupiter":(157.450, 10.450, 211.930, 35.330, 34.280,  -6.570),
 "Venus":  (157.925, 14.950, 116.810,  5.760, 42.850,  18.670),
 "Saturn": (162.400, 56.700, 115.690, 21.060,  8.570,   7.370),
}
_EXPECTED_RUPAS = {"Sun":6.288,"Moon":6.936,"Mars":5.381,"Mercury":9.674,
                   "Jupiter":7.381,"Venus":5.949,"Saturn":6.196}

def test_assembly_reproduces_total_rupas():
    for p, c in _COMP.items():
        br = total.assemble_shadbala(*c)
        assert isinstance(br, ShadbalaBreakdown)
        assert abs(br.total / 60.0 - _EXPECTED_RUPAS[p]) < 0.01, f"{p}: {br.total/60.0}"

def test_drik_is_signed_in_the_sum():
    # Moon's negative Drik (−11.9) must subtract.
    br = total.assemble_shadbala(*_COMP["Moon"])
    assert abs(br.total - 416.180) < 0.1

def test_min_required_thresholds_and_all_powerful():
    assert total.MIN_REQUIRED == {"Sun":5.0,"Moon":6.0,"Mars":5.0,"Mercury":7.0,
                                  "Jupiter":6.5,"Venus":5.5,"Saturn":5.0}
    for p, r in _EXPECTED_RUPAS.items():
        assert total.is_powerful(p, r) is True          # fixture: all 7 powerful
    assert total.is_powerful("Saturn", 4.9) is False
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import ShadbalaBreakdown

# Minimum-required total Shadbala in Rupas per planet (GBB-8:303-312).
MIN_REQUIRED: Final[dict[str, float]] = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}


def assemble_shadbala(sthana: float, dig: float, kala: float, cheshta: float,
                      naisargika: float, drik: float) -> ShadbalaBreakdown:
    """Sum the six components (Shashtiamsas; Drik is signed) into a ShadbalaBreakdown.
    `total` is in Shashtiamsas; divide by 60 for Rupas (GBB-8:262)."""
    total_sh = sthana + dig + kala + cheshta + naisargika + drik
    return ShadbalaBreakdown(sthana=sthana, dig=dig, kala=kala, cheshta=cheshta,
                             naisargika=naisargika, drik=drik, total=round(total_sh, 3))


def is_powerful(planet: str, total_rupas: float) -> bool:
    """True iff the planet's total Shadbala (Rupas) meets its minimum required (GBB-8:303)."""
    req = MIN_REQUIRED.get(planet)
    return req is not None and total_rupas >= req
```
> Check `ShadbalaBreakdown`'s field order/names in `app/raman_saab/chart/model.py` (it is
> `sthana, dig, kala, cheshta, naisargika, drik, total`) and that `total` is in Shashtiamsas here
> (Rupas = /60 at the call site). If the dataclass expects Rupas in `total`, adjust + note it.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 2: Ishta / Kashta Phala

**Files:** Create `app/raman_saab/primitives/shadbala/ishta_kashta.py`; Test `.../shadbala/test_ishta_kashta.py`

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import ishta_kashta as ik

# GBB Standard Horoscope: Ochcha (Sh) and Chesta (Sh, incl. Sun/Moon surrogates).
_OCHCHA = {"Sun":3.6,"Moon":32.9,"Mars":37.2,"Mercury":54.8,"Jupiter":56.2,"Venus":2.3,"Saturn":34.9}
_CHESTA = {"Sun":23.2,"Moon":44.2,"Mars":22.28,"Mercury":2.13,"Jupiter":35.33,"Venus":5.76,"Saturn":21.06}
_ISHTA  = {"Sun":9.14,"Moon":38.13,"Mars":28.79,"Mercury":10.83,"Jupiter":44.56,"Venus":3.63,"Saturn":27.11}
_KASHTA = {"Sun":45.54,"Moon":20.66,"Mars":29.32,"Mercury":17.34,"Jupiter":9.73,"Venus":55.94,"Saturn":31.26}

def test_ishta_kashta_fixture():
    for p in _OCHCHA:
        assert abs(ik.ishta_phala(_OCHCHA[p], _CHESTA[p]) - _ISHTA[p]) < 0.1, p
        assert abs(ik.kashta_phala(_OCHCHA[p], _CHESTA[p]) - _KASHTA[p]) < 0.1, p

def test_sun_moon_chesta_surrogates():
    # Sun: (Sayana 200.4 + 90) folded /3 = 23.2 ; Moon: (Moon 311.67 − Sun 179.13)/3 = 44.2
    assert abs(ik.sun_chesta_surrogate(200.4) - 23.2) < 0.2
    assert abs(ik.moon_chesta_surrogate(311.67, 179.13) - 44.18) < 0.2
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
import math


def ishta_phala(ochcha_bala: float, chesta_bala: float) -> float:
    """Benefic effect = sqrt(Ochcha × Chesta), Shashtiamsas 0-60 (GBB-10:93)."""
    return round(math.sqrt(max(0.0, ochcha_bala) * max(0.0, chesta_bala)), 3)


def kashta_phala(ochcha_bala: float, chesta_bala: float) -> float:
    """Malefic effect = sqrt((60−Ochcha) × (60−Chesta)), Shashtiamsas 0-60 (GBB-10:114)."""
    return round(math.sqrt(max(0.0, 60.0 - ochcha_bala) * max(0.0, 60.0 - chesta_bala)), 3)


def sun_chesta_surrogate(sayana_sun_lon: float) -> float:
    """Sun has no true Cheshta; for Ishta/Kashta use CK = (Sayana + 90) folded, /3 (GBB-10:46)."""
    ck = (sayana_sun_lon + 90.0) % 360.0
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)


def moon_chesta_surrogate(moon_lon: float, sun_lon: float) -> float:
    """Moon Cheshta surrogate = (Moon − Sun) folded, /3 (GBB-10:72)."""
    ck = (moon_lon - sun_lon) % 360.0
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)
```
- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Phase 1c-3 (capstone) done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` green (existing 112 + new; import guard passes).
- `assemble_shadbala` reproduces the fixture Total-Rupas (6/7 exact; Mercury 9.674 per the OCR note);
  `is_powerful` gives all 7 powerful with the GBB thresholds.
- `ishta_phala`/`kashta_phala` reproduce all 7 fixture values (±0.1 Sh), incl. the Sun/Moon surrogates.

**1c-3 continuation (next round):** Bhava-bala (`shadbala/bhava_bala.py`, reference §8); wire
`PlanetPos.shadbala_rupas/ishta/kashta` via the adapter (compute all 6 components + Kala context +
mean longitudes per planet); then the **backfills** — maraka `strength_rank`+weakest-planet (now that
Shadbala exists), balarishta "powerfully situated" strength checks, navamsa64 external pin, the
Ahargana Kala year/month lords, and the Mars/Venus-Ayana + Saptavargaja-cusp xfail decisions. After
that Phase 1 is **complete** → Phase 2 (`doctrine/conditions.py` + rule encoding).
