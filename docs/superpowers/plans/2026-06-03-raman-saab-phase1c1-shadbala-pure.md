# Raman Saab — Phase 1c-1: GBB Shadbala — the Pure/Cusp Components — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Implement the four Shadbala components that need **no new ephemeris** — **Sthana** (positional, 5 sub-components), **Naisargika** (natural constants), **Dig** (directional, from bhava cusps), and **Drik** (aspectual) — each re-derived to B.V. Raman's *Graha & Bhava Balas* and pinned to the book's worked "Standard Horoscope" fixture.

**Architecture:** New `app/raman_saab/primitives/shadbala/` sub-package, one module per component, each a pure function returning **Shashtiamsas** (1 Rupa = 60 Shashtiamsas). A new `primitives/varga_lords.py` supplies the D2/D7/D12/D30 lords that Saptavargaja-bala needs (D1/D3/D9 lords already exist in `dispositor.py`). Components reuse the Phase-1a `dignity._compound_relation`, `relationships`, `sign_attributes`. Ephemeris-heavy Cheshta + Kala are **Phase 1c-2**; total-assembly + Bhava-bala + Ishta/Kashta + adapter wiring are **Phase 1c-3**.

**Tech Stack:** Python 3.12, frozen dataclasses, pytest. No new dependencies, no `swisseph`. All components are computable from `RamanChart.from_stated_positions(...)` (Track-B), so the GBB fixture is ephemeris-free.

**Spec:** `docs/raman_saab/gbb_shadbala_reference.md` (THE authority — §1 Sthana, §2 Dig, §5 Naisargika, §6 Drik, §10 fixture, §11 fidelity traps). Engine design `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` §4 (`ShadbalaBreakdown`), §4.6 (re-derive to GBB, ±1-rupa fixture; do NOT import `app/core/shadbala`).

**Scope.** IN: `varga_lords`, `shadbala/naisargika`, `shadbala/sthana`, `shadbala/dig`, `shadbala/drik`, and a Track-B fixture test. OUT (later sub-phases): Cheshta (mean longitudes), Kala (declination/sunrise/Ahargana), total Shadbala assembly, Bhava-bala, Ishta/Kashta, `PlanetPos.shadbala_rupas` wiring, maraka `strength_rank` backfill.

---

## Doctrine constants (verified live before this plan; see reference §)

- **Unit:** every function returns **Shashtiamsas** (float). Rupas = Shashtiamsas/60 (assembly is 1c-3).
- **7 planets only** (Sun..Saturn). Nodes get no Shadbala → component functions return `0.0` for Rahu/Ketu (or are never called on them).
- **Fidelity traps honored here:** Kendra-bala by SIGN not bhava (§1.4); Saptavargaja 45-only-in-D1, hard-coded 22.5/1.875 (§1.2); Drekkana-bala by Raman's planetary sex (§1.5); Dig from the **bhava-madhya cusp** (§2); Drik 30–60 branch = `(K−30)/2` (the one extraction bug caught live).

---

## File structure

| File | Responsibility |
|---|---|
| `app/raman_saab/primitives/varga_lords.py` | `hora_lord_of`, `saptamsa_lord_of`, `dwadasamsa_lord_of`, `thrimsamsa_lord_of` (D2/D7/D12/D30) |
| `app/raman_saab/primitives/shadbala/__init__.py` | package marker (assembly lands in 1c-3) |
| `app/raman_saab/primitives/shadbala/naisargika.py` | `naisargika_bala(planet)` |
| `app/raman_saab/primitives/shadbala/sthana.py` | `sthana_bala(planet, chart)` + 5 sub-component helpers |
| `app/raman_saab/primitives/shadbala/dig.py` | `dig_bala(planet, chart)` |
| `app/raman_saab/primitives/shadbala/drik.py` | `drik_bala(planet, chart)`, `dristi_value(K)` |
| `tests/raman_saab/primitives/shadbala/test_*.py` | paired unit tests |
| `tests/raman_saab/primitives/shadbala/test_fixture_standard_horoscope.py` | Track-B ±1-rupa pins to GBB §10 |

---

## Task 0: sub-package skeleton

- [ ] Create `app/raman_saab/primitives/shadbala/__init__.py` (empty) and `tests/raman_saab/primitives/shadbala/__init__.py` (empty).
- [ ] `py -3.12 -c "import app.raman_saab.primitives.shadbala"` → no error. **Do not commit** (orchestrator commits).

---

## Task 1: Varga lords (D2/D7/D12/D30)

**Files:** Create `app/raman_saab/primitives/varga_lords.py`; Test `tests/raman_saab/primitives/test_varga_lords.py`

Verified live: Hora (odd sign 1st-half→Sun, 2nd→Moon; even reversed); Saptamsa (odd start=sign, even start=7th-from; +part); Dwadasamsa (start=sign, +part of 2.5°); Thrimsamsa (odd: Mars0-5/Saturn5-10/Jupiter10-18/Mercury18-25/Venus25-30; even reversed Venus/Mercury/Jupiter/Saturn/Mars).

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives import varga_lords as v

def test_hora_lord():
    assert v.hora_lord_of(5.0) == "Sun"     # Aries 5° (odd sign, 1st half) -> Sun
    assert v.hora_lord_of(20.0) == "Moon"   # Aries 20° (odd sign, 2nd half) -> Moon
    assert v.hora_lord_of(35.0) == "Moon"   # Taurus 5° (even sign, 1st half) -> Moon
    assert v.hora_lord_of(50.0) == "Sun"    # Taurus 20° (even sign, 2nd half) -> Sun
def test_saptamsa_lord():
    assert v.saptamsa_lord_of(2.0) == "Mars"        # Aries 2° -> Aries -> Mars
    assert v.saptamsa_lord_of(32.0) == "Mars"       # Taurus 2° (even) -> Scorpio -> Mars
def test_dwadasamsa_lord():
    assert v.dwadasamsa_lord_of(2.0) == "Mars"      # Aries 2° -> Aries
    assert v.dwadasamsa_lord_of(6.0) == "Mercury"   # Aries 6° (part 2) -> Gemini -> Mercury
def test_thrimsamsa_lord():
    assert v.thrimsamsa_lord_of(3.0) == "Mars"      # Aries 3° (odd, 0-5) -> Mars
    assert v.thrimsamsa_lord_of(27.0) == "Venus"    # Aries 27° (odd, 25-30) -> Venus
    assert v.thrimsamsa_lord_of(33.0) == "Venus"    # Taurus 3° (even, 0-5) -> Venus
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from app.raman_saab.chart.constants import SIGN_LORDS

def _sign_deg(lon: float) -> tuple[int, float]:
    lon %= 360.0
    return int(lon // 30) + 1, lon % 30.0

def hora_lord_of(lon: float) -> str:
    """D2: odd sign -> 1st half Sun, 2nd half Moon; even sign -> reversed (Parashara hora)."""
    sign, deg = _sign_deg(lon)
    first_half = deg < 15.0
    if sign % 2 == 1:                      # odd
        return "Sun" if first_half else "Moon"
    return "Moon" if first_half else "Sun"  # even

def saptamsa_lord_of(lon: float) -> str:
    """D7: odd sign counts from itself; even sign from the 7th sign; lord = sign-lord of result."""
    sign, deg = _sign_deg(lon)
    part = int(deg * 7 / 30)               # 0..6
    start = sign if sign % 2 == 1 else ((sign - 1 + 6) % 12) + 1
    return SIGN_LORDS[((start - 1 + part) % 12) + 1]

def dwadasamsa_lord_of(lon: float) -> str:
    """D12: 2.5° parts counting from the sign itself; lord = sign-lord of result."""
    sign, deg = _sign_deg(lon)
    part = int(deg / 2.5)                  # 0..11
    return SIGN_LORDS[((sign - 1 + part) % 12) + 1]

def thrimsamsa_lord_of(lon: float) -> str:
    """D30: unequal 5-fold by planet directly. Odd: Mars/Saturn/Jupiter/Mercury/Venus at
    5/10/18/25/30; even: Venus/Mercury/Jupiter/Saturn/Mars at 5/12/20/25/30."""
    sign, deg = _sign_deg(lon)
    odd = sign % 2 == 1
    bounds = ([(5, "Mars"), (10, "Saturn"), (18, "Jupiter"), (25, "Mercury"), (30, "Venus")]
              if odd else
              [(5, "Venus"), (12, "Mercury"), (20, "Jupiter"), (25, "Saturn"), (30, "Mars")])
    for hi, p in bounds:
        if deg < hi:
            return p
    return bounds[-1][1]
```
- [ ] **Step 4:** Run → PASS. **Step 5:** report (no commit).

---

## Task 2: Naisargika Bala

**Files:** Create `app/raman_saab/primitives/shadbala/naisargika.py`; Test `.../shadbala/test_naisargika.py`

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala.naisargika import naisargika_bala

def test_naisargika_constants():
    assert naisargika_bala("Sun") == 60.0
    assert abs(naisargika_bala("Saturn") - 8.57) < 0.01
    assert abs(naisargika_bala("Moon") - 51.43) < 0.01
    assert naisargika_bala("Rahu") == 0.0
```
- [ ] **Step 2:** FAIL. **Step 3: implement**
```python
from __future__ import annotations
from typing import Final

# Fixed 60/7 ladder (Shashtiamsas), GBB-7:44-63. Saturn rank1 .. Sun rank7.
_RANK: Final[dict[str, int]] = {
    "Saturn": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Moon": 6, "Sun": 7}

def naisargika_bala(planet: str) -> float:
    """Natural strength in Shashtiamsas (fixed per planet). 0 for nodes."""
    rank = _RANK.get(planet)
    return round(rank * 60.0 / 7.0, 2) if rank else 0.0
```
> The fixture uses 8.57/17.14/25.70/34.28/42.85/51.43/60.00. `round(...,2)` gives 8.57/17.14/25.71/34.29/42.86/51.43/60.0 — within the ±1-rupa fixture tolerance; the unit test asserts ±0.01 against 8.57/51.43 and exact 60.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 3: Sthana Bala (5 sub-components)

**Files:** Create `app/raman_saab/primitives/shadbala/sthana.py`; Test `.../shadbala/test_sthana.py`

Reference §1. Sub-components (Shashtiamsas): Ochcha = corrected-arc-from-debilitation/3; Saptavargaja = Σ over 7 vargas of the dignity value (45 only in D1); Ojayugma = 15(rasi parity match)+15(navamsa parity match); Kendra = 60/30/15 by **rasi-house**; Drekkana = 15 if planet in its sex-decanate.

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import sthana
from app.raman_saab.chart.model import RamanChart

def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")

def test_ochcha_bala_exalted_is_max_debilitated_is_zero():
    assert abs(sthana.ochcha_bala("Sun", _c({"Sun": 10.0})) - 60.0) < 0.1   # Aries 10 = deep exalt
    assert sthana.ochcha_bala("Sun", _c({"Sun": 190.0})) < 0.1              # Libra 10 = deep debil

def test_kendra_bala_by_sign():
    # Aries lagna, planet in 1st (kendra)=60, in 2nd (panapara)=30, in 3rd (apoklima)=15.
    assert sthana.kendra_bala("Mars", _c({"Mars": 5.0}, 0.0)) == 60.0
    assert sthana.kendra_bala("Mars", _c({"Mars": 35.0}, 0.0)) == 30.0
    assert sthana.kendra_bala("Mars", _c({"Mars": 65.0}, 0.0)) == 15.0

def test_drekkana_bala_by_sex():
    # Sun (masculine) gains 15 only in the 1st decanate (0-10).
    assert sthana.drekkana_bala("Sun", _c({"Sun": 5.0})) == 15.0
    assert sthana.drekkana_bala("Sun", _c({"Sun": 15.0})) == 0.0
    # Moon (feminine) gains in the 3rd decanate (20-30).
    assert sthana.drekkana_bala("Moon", _c({"Moon": 25.0})) == 15.0

def test_ojayugma_bala():
    # Sun prefers ODD; in Aries(odd rasi) gets 15 for rasi; navamsa parity adds 0/15.
    val = sthana.ojayugma_bala("Sun", _c({"Sun": 5.0}))
    assert val in (15.0, 30.0)

def test_sthana_bala_sums_subcomponents():
    c = _c({"Sun": 10.0}, 280.0)   # Sun deep-exalt, Capricorn lagna
    total = sthana.sthana_bala("Sun", c)
    assert total == (sthana.ochcha_bala("Sun", c) + sthana.saptavargaja_bala("Sun", c)
                     + sthana.ojayugma_bala("Sun", c) + sthana.kendra_bala("Sun", c)
                     + sthana.drekkana_bala("Sun", c))
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives import relationships as r, varga_lords as vl
from app.raman_saab.primitives.dignity import _compound_relation
from app.raman_saab.chart import varga

_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Saptavargaja dignity ladder (Shashtiamsas), GBB-3:462-476. 45 ONLY in D1.
_DIGNITY_SH: Final[dict[str, float]] = {
    "moolatrikona": 45.0, "own": 30.0, "great_friend": 22.5, "friend": 15.0,
    "neutral": 7.5, "enemy": 3.75, "great_enemy": 1.875}
# Drekkana-bala sex -> required decanate index (0,1,2), GBB-3:653-671.
_SEX_DECAN: Final[dict[str, int]] = {
    "Sun": 0, "Jupiter": 0, "Mars": 0, "Saturn": 1, "Mercury": 1, "Moon": 2, "Venus": 2}
_ODD_PREF: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Mercury", "Saturn"})


def ochcha_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    debil = r.DEBILITATION[planet][0]                       # debilitation SIGN (1..12)
    debil_lon = (debil - 1) * 30 + r.DEBILITATION[planet][1]  # deep-debilitation longitude
    diff = (chart.planets[planet].lon - debil_lon) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return round(diff / 3.0, 3)


def _varga_lord(planet: str, lon: float, varga_name: str) -> str:
    if varga_name == "D1":  return SIGN_LORDS[int(lon // 30) + 1]
    if varga_name == "D2":  return vl.hora_lord_of(lon)
    if varga_name == "D3":  return SIGN_LORDS[varga.drekkana_sign(lon)] if hasattr(varga, "drekkana_sign") else _d3(lon)
    if varga_name == "D7":  return vl.saptamsa_lord_of(lon)
    if varga_name == "D9":  return SIGN_LORDS[varga.navamsa_sign(lon)]
    if varga_name == "D12": return vl.dwadasamsa_lord_of(lon)
    if varga_name == "D30": return vl.thrimsamsa_lord_of(lon)
    raise ValueError(varga_name)


def _d3(lon: float) -> str:
    sign_idx = int(lon // 30); drek = int((lon % 30) // 10)
    return SIGN_LORDS[((sign_idx + drek * 4) % 12) + 1]


def saptavargaja_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    lon = chart.planets[planet].lon
    total = 0.0
    for vname in ("D1", "D2", "D3", "D7", "D9", "D12", "D30"):
        lord = _varga_lord(planet, lon, vname)
        if lord == planet:
            # own varga: D1 own-sign could be moolatrikona; only D1 gets the 45 tier.
            if vname == "D1":
                s, d = int(lon // 30) + 1, lon % 30
                mt_s, lo, hi = r.MOOLATRIKONA[planet]
                total += _DIGNITY_SH["moolatrikona"] if (s == mt_s and lo <= d < hi) else _DIGNITY_SH["own"]
            else:
                total += _DIGNITY_SH["own"]
            continue
        rel = _compound_relation(planet, lord, chart)        # friend|enemy|neutral (Phase 1a)
        # map compound 3-state onto the 7-rung ladder via great/ordinary by naisargika agreement
        nat = r.naisargika(planet, lord)
        key = _ladder_key(rel, nat)
        total += _DIGNITY_SH[key]
    return round(total, 3)


def _ladder_key(compound: str, naisargika: str) -> str:
    # great_friend if compound==friend AND naisargika friend; great_enemy if both enemy; else ordinary.
    if compound == "friend":
        return "great_friend" if naisargika == "friend" else "friend"
    if compound == "enemy":
        return "great_enemy" if naisargika == "enemy" else "enemy"
    return "neutral"


def ojayugma_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    p = chart.planets[planet]
    prefers_odd = planet in _ODD_PREF
    rasi_odd = p.sign % 2 == 1
    nav_odd = p.navamsa_sign % 2 == 1
    val = 0.0
    if rasi_odd == prefers_odd:
        val += 15.0
    if nav_odd == prefers_odd:
        val += 15.0
    return val


def kendra_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    h = chart.planets[planet].rasi_house               # by SIGN (rasi), GBB-3:609
    if h in (1, 4, 7, 10):  return 60.0
    if h in (2, 5, 8, 11):  return 30.0
    return 15.0


def drekkana_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _SEX_DECAN or planet not in chart.planets:
        return 0.0
    decan = int((chart.planets[planet].lon % 30) // 10)   # 0,1,2
    return 15.0 if decan == _SEX_DECAN[planet] else 0.0


def sthana_bala(planet: str, chart: RamanChart) -> float:
    return round(ochcha_bala(planet, chart) + saptavargaja_bala(planet, chart)
                 + ojayugma_bala(planet, chart) + kendra_bala(planet, chart)
                 + drekkana_bala(planet, chart), 3)
```
> **Implementer note:** check whether `app/raman_saab/chart/varga.py` exposes a `drekkana_sign`/D3 helper and `navamsa_sign` (it does — Phase 0). Use them; the `_d3` fallback mirrors `dispositor.drekkana_lord_of`. Also confirm `dignity._compound_relation(of, lord, chart)` and `relationships.MOOLATRIKONA/DEBILITATION/naisargika` signatures (Phase 1a) — adjust calls to the real APIs. The `_ladder_key` great-vs-ordinary mapping reproduces GBB's 7-rung ladder from the project's 3-state compound relation; if the fixture column (Task 6) disagrees for a planet, refine this mapping, not the ladder constants.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 4: Dig Bala

**Files:** Create `app/raman_saab/primitives/shadbala/dig.py`; Test `.../shadbala/test_dig.py`

Reference §2. Powerful house per planet: Jup/Merc→1, Sun/Mars→10, Saturn→7, Moon/Venus→4. Powerless point = the **bhava-madhya** 180° from the powerful cusp. `arc/3` (Shashtiamsas).

- [ ] **Step 1: failing test** (pin Saturn to Raman's worked value 56.7 using the stated 7th-madhya)
```python
import dataclasses
from app.raman_saab.primitives.shadbala.dig import dig_bala, _powerless_madhya
from app.raman_saab.chart.model import RamanChart

def test_dig_bala_saturn_standard_horoscope():
    # GBB-4:91-100: Saturn lon 124°51', 7th-bhava-madhya 114°57' -> powerless 294°57' -> 56.7 Sh.
    c = RamanChart.from_stated_positions({"Saturn": {"lon": 124 + 51/60, "bhava": 1}},
                                         asc_lon=185.0, ayanamsa="raman")
    # Saturn's powerful house = 7th -> powerless = 1st; _powerless_madhya reads madhyas[0].
    # Set the 1st-madhya to 294.95° (= 7th-madhya 114.95° + 180) so Saturn's arc = 56.7.
    madhyas = tuple(((114.95 + 180.0) + i * 30) % 360 for i in range(12))
    c = dataclasses.replace(c, bhava_madhyas=madhyas)
    assert abs(dig_bala("Saturn", c) - 56.7) < 1.0

def test_dig_bala_full_at_powerful_cusp():
    # A planet exactly on its powerful bhava-madhya -> ~60.
    c = RamanChart.from_stated_positions({"Jupiter": {"lon": 0.0, "bhava": 1}},
                                         asc_lon=0.0, ayanamsa="raman")
    madhyas = tuple((i * 30) for i in range(12))   # 1st madhya = 0° (Jupiter's powerful cusp)
    c = dataclasses.replace(c, bhava_madhyas=madhyas)
    assert abs(dig_bala("Jupiter", c) - 60.0) < 1.0
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart

# Powerful house (full Dig) per planet, GBB-4:35-43.
_POWERFUL_HOUSE: Final[dict[str, int]] = {
    "Jupiter": 1, "Mercury": 1, "Sun": 10, "Mars": 10, "Saturn": 7, "Moon": 4, "Venus": 4}


def _powerless_madhya(planet: str, chart: RamanChart) -> float:
    """Bhava-madhya of the house OPPOSITE the planet's powerful house (the zero point)."""
    powerful = _POWERFUL_HOUSE[planet]
    powerless_house = ((powerful - 1 + 6) % 12) + 1
    if chart.bhava_madhyas:
        return chart.bhava_madhyas[powerless_house - 1]
    # ephemeris-free fallback: equal-house cusp mid-points from the Lagna
    return (chart.asc_lon + (powerless_house - 1) * 30) % 360.0


def dig_bala(planet: str, chart: RamanChart) -> float:
    """Directional strength in Shashtiamsas: arc from the powerless bhava-madhya / 3.
    Reference point is the Bhava-MADHYA cusp (GBB-4:91), not the rasi/bhava-begin."""
    if planet not in _POWERFUL_HOUSE or planet not in chart.planets:
        return 0.0
    arc = (chart.planets[planet].lon - _powerless_madhya(planet, chart)) % 360.0
    if arc > 180.0:
        arc = 360.0 - arc
    return round(arc / 3.0, 3)
```
> **Note on the fallback:** Track-B charts have no cusps; the equal-house fallback is an approximation (Raman uses real Sripati cusps). The fixture pins **Saturn only** (the book's one worked Dig example) via an injected synthetic 7th-madhya. Full-Dig-column reconciliation needs the real cusps → deferred to the ephemeris-cast fixture in Phase 1c-3. Document this clearly.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 5: Drik Bala

**Files:** Create `app/raman_saab/primitives/shadbala/drik.py`; Test `.../shadbala/test_drik.py`

Reference §6. Piecewise `dristi_value(K)` (verified continuous, hits Raman's anchors), Visesha Dristi (Mars 4/8=15, Jupiter 5/9=30, Saturn 3/10=45), signed by benefic/malefic, `Drik = DristiPinda/4`.

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala.drik import dristi_value, drik_bala
from app.raman_saab.chart.model import RamanChart

def test_dristi_value_anchors():
    assert dristi_value(30) == 0.0
    assert dristi_value(60) == 15.0     # Raman's anchor (NOT 30)
    assert dristi_value(90) == 45.0
    assert dristi_value(150) == 0.0
    assert dristi_value(180) == 60.0
    assert dristi_value(300) == 0.0
    assert dristi_value(20) == 0.0      # below 30 -> no aspect

def test_drik_bala_signed_by_benefic_malefic():
    # Jupiter (benefic) at 0°, Saturn (malefic) at 180° from a target at 90°.
    c = RamanChart.from_stated_positions(
        {"Jupiter": {"lon": 0.0, "bhava": 1}, "Saturn": {"lon": 180.0, "bhava": 1},
         "Mars": {"lon": 90.0, "bhava": 1}}, asc_lon=0.0, ayanamsa="raman")
    val = drik_bala("Mars", c)
    assert isinstance(val, float)       # signed; sign reflects net benefic vs malefic
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart

# Visesha (special) aspect: (lo, hi) arc window -> bonus Shashtiamsas, GBB-8:172-191.
_VISESHA: Final[dict[str, list[tuple[float, float, float]]]] = {
    "Mars": [(90, 120, 15.0), (210, 240, 15.0)],
    "Jupiter": [(120, 150, 30.0), (240, 270, 30.0)],
    "Saturn": [(60, 90, 45.0), (270, 300, 45.0)],
}
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})  # + waning Moon, bad Mercury


def dristi_value(K: float) -> float:
    """Sripathi piecewise aspect strength (Shashtiamsas) for separation K (degrees)."""
    K %= 360.0
    if 30 <= K < 60:    return (K - 30) / 2.0
    if 60 <= K < 90:    return (K - 60) + 15.0
    if 90 <= K < 120:   return 45.0 - (K - 90) / 2.0
    if 120 <= K < 150:  return 150.0 - K
    if 150 <= K < 180:  return (K - 150) * 2.0
    if 180 <= K <= 300: return (300.0 - K) / 2.0
    return 0.0


def _is_malefic(planet: str, chart: RamanChart) -> bool:
    if planet in _MALEFICS:
        return True
    if planet == "Moon" and "Sun" in chart.planets:           # waning Moon = malefic
        sep = (chart.planets["Moon"].lon - chart.planets["Sun"].lon) % 360.0
        return sep > 180.0
    return False                                              # Jupiter, Venus, waxing Moon, Mercury: benefic


def drik_bala(planet: str, chart: RamanChart) -> float:
    """Aspectual strength in Shashtiamsas = (signed Dristi Pinda) / 4 (GBB-8:241).
    Benefic aspects add, malefic subtract; Mars/Jupiter/Saturn add Visesha Dristi."""
    if planet not in chart.planets:
        return 0.0
    target = chart.planets[planet].lon
    pinda = 0.0
    for other, p in chart.planets.items():
        if other == planet or other in ("Rahu", "Ketu"):
            continue
        K = (target - p.lon) % 360.0
        val = dristi_value(K)
        for lo, hi, bonus in _VISESHA.get(other, []):
            if lo <= K < hi:
                val += bonus
        if val == 0.0:
            continue
        pinda += -val if _is_malefic(other, chart) else val
    return round(pinda / 4.0, 3)
```
> **Implementer note:** the benefic/malefic split for Mercury ("well/badly associated") and the waning-Moon test are simplified to the computable subset (Mercury treated benefic; Moon by phase). If the fixture Drik column (Task 6) disagrees for a planet, refine `_is_malefic` (e.g. Mercury-with-malefic), not the piecewise function. The piecewise was verified live against Raman's anchors — do not alter it.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 6: Track-B fixture — GBB "Standard Horoscope"

**Files:** Create `tests/raman_saab/primitives/shadbala/test_fixture_standard_horoscope.py`

Reference §10. Inject the stated longitudes with **Libra Lagna (asc_lon 185°)** — this is
**verified correct**: all 7 Kendra-bala values reproduce the book's Kendra row with Libra (the
"lagna lord Saturn / Saturn-in-7th" hints refer to the Dig-bala 7th-*bhava*/Chalita, a separate
thing from the rasi-lagna). **Tolerance:** the spec's "±1 rupa" = ±60 Shashtiamsas, which is
useless on a 150–295 Sh component; pin clean component cells at **±0.2 rupa (~12 Sh)** and the
genuinely-clean ones at **~6 Sh**, never looser to hide a real gap.

```python
from app.raman_saab.primitives.shadbala import naisargika, sthana
from app.raman_saab.chart.model import RamanChart

# GBB Standard Horoscope stated Nirayana longitudes (deg), Libra Lagna (asc 185°).
_POS = {"Sun": 179+8/60, "Moon": 311+40/60, "Mars": 229+49/60, "Mercury": 180+33/60,
        "Jupiter": 83+35/60, "Venus": 170+4/60, "Saturn": 124+51/60}
_CHART = RamanChart.from_stated_positions(
    {p: {"lon": l, "bhava": 1} for p, l in _POS.items()}, asc_lon=185.0, ayanamsa="raman")

_NAISARGIKA = {"Sun":60.0,"Moon":51.43,"Mars":17.14,"Mercury":25.70,"Jupiter":34.28,"Venus":42.85,"Saturn":8.57}
# Sthana cells that reconcile to the gold table AND the computation (verified in plan review):
_STHANA_CLEAN = {"Sun":147.975, "Mercury":294.800, "Jupiter":157.450}

def test_naisargika_column():
    for p, exp in _NAISARGIKA.items():
        assert abs(naisargika.naisargika_bala(p) - exp) < 0.5

def test_sthana_clean_cells_reconcile():
    for p, exp in _STHANA_CLEAN.items():
        got = sthana.sthana_bala(p, _CHART)
        assert abs(got - exp) < 6.0, f"{p}: got {got}, expected {exp}"
```
> **Load-bearing fidelity test + a localization task.** Naisargika and the 3 clean Sthana cells
> MUST pass. **Mars/Venus/Saturn/Moon Sthana do NOT yet reconcile** (plan review measured Mars
> −22, Venus +15, Saturn +15, Moon −15 Sh) and the gap is **in Saptavargaja, not Kendra** (Kendra
> is verified to match all 7). To localize it, pin **each sub-component** of one failing planet
> against the book's per-sub-component row and find which varga's compound-relation diverges:
>
> | sub-component | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn | cite |
> |---|---|---|---|---|---|---|---|---|
> | Ochcha | 3.6 | 32.9 | 37.2 | 54.8 | 56.2 | 2.3 | 34.9 | GBB-3:716 |
> | Saptavargaja | 129.375 | 48.750 | **112.500** | 150.000 | 71.250 | **110.625** | **82.500** | GBB-3:514-543 |
> | Ojayugma | 0 | 15 | 15 | 30 | 15 | 30 | 15 | GBB-3:586-601 |
> | Kendra | 15 | 30 | 30 | 60 | 15 | 15 | 30 | GBB-3:642-651 (✓verified) |
> | Drekkana | 15 | 0 | 0 | 0 | 0 | 0 | 0 | GBB-3:716 (Sun only) |
>
> Add a `test_saptavargaja_per_planet` that pins the Saptavargaja column at ~6 Sh; for any planet
> that still diverges after debugging the per-varga dignity (check each of D1/D2/D3/D7/D9/D12/D30
> lord + compound relation against GBB-3:496-543), mark it `@pytest.mark.xfail` with a written
> reason and carry it to Phase 1c-3 — do NOT delete the assertion or loosen tolerance. **Drik and
> Dig column reconciliation are deferred** (Drik needs the benefic/malefic refinement; Dig needs
> real cusps) — note them as 1c-3 carry-overs.

- [ ] Run `py -3.12 -m pytest tests/raman_saab/primitives/shadbala/ -q`; report which fixture cells reconcile and which are `xfail`-carried. **Do not commit; report to orchestrator.**

---

## Phase 1c-1 done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` green (existing 67 + new), import guard still passes (no `app/core`).
- `varga_lords` + `shadbala/{naisargika,sthana,dig,drik}` importable, unit-tested, returning Shashtiamsas.
- Naisargika column reconciles to the GBB fixture near-exactly; the 5 OCR-clean Sthana cells reconcile within ~0.1 rupa; Saturn Dig ≈56.7; Drik column reconciled or explicitly `xfail`-flagged for the benefic/malefic refinement.
- **Documented carry-overs:** full Dig column (needs real cusps), Drik Mercury-association refinement, Sun/Moon Sthana OCR ambiguity → revisit in 1c-3 with the ephemeris-cast fixture.

**Next:** Phase 1c-2 — Cheshta (mean longitudes) + Kala (declination, sunrise/ghatis, Ahargana), the ephemeris-heavy columns. Then 1c-3 — total Shadbala assembly + min-required verdict + Bhava-bala + Ishta/Kashta + `PlanetPos` wiring + maraka/balarishta strength backfills.
