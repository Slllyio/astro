# Raman Saab — Phase 1c-2a: Cheshta Bala — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Implement **Cheshta Bala** (motional strength) — the Sripathi arc-of-retrogression component of Shadbala — for the 5 non-luminaries, re-derived to B.V. Raman's *Graha & Bhava Balas* and pinned to his worked "Standard Horoscope" to the decimal.

**Architecture:** A pure `shadbala/cheshta.py` (the validated Sripathi formula, given mean/seegrochcha/true longitudes) + a `chart/mean_longitudes.py` (Raman's epoch method computing mean longitudes + seegrochchas for real charts). The pure formula is fixture-pinned via injected means (Track-B); the epoch method is pinned against Raman's stated means (±0.2°).

**Tech Stack:** Python 3.12, frozen dataclasses, pytest. `mean_longitudes.py` uses `swisseph` only for `swe.julday` (the epoch JD); no other ephemeris. No `app/core`.

**Scope.** IN: `shadbala/cheshta.py`, `chart/mean_longitudes.py`, fixture + validation tests. OUT (1c-3): wiring Cheshta into the total Shadbala assembly + `PlanetPos`; the Sun/Moon Cheshta surrogates for Ishta/Kashta (those are §9, a 1c-3/Ishta concern).

**Spec/authority:** `docs/raman_saab/gbb_shadbala_reference.md` §4 (Cheshta, with the resolved OCR correction). Every constant below was **verified live** against Raman's worked example before this plan.

---

## Doctrine (all verified live; reference §4)

**Cheshta formula (Sripathi, OCR-corrected):**
```
ChestaKendra = Seegrochcha − (MeanLong + TrueLong)/2    # NOT (Mean − True) — that was an OCR slip
if ChestaKendra < 0:   ChestaKendra += 360
if ChestaKendra > 180: ChestaKendra = 360 − ChestaKendra
Cheshta = ChestaKendra / 3                              # Shashtiamsas, 0..60
```
Validated to the decimal vs GBB Ex.49-51: Kuja CK 293.15→22.28 · Budha 353.60→2.13 · Guru 105.99→35.33 · Sukra 342.70→5.76 · Sani 63.19→21.06.

**Only 5 planets** (Mars, Mercury, Jupiter, Venus, Saturn). **Sun & Moon get NO Cheshta** in the Shadbala total (the biggest GBB divergence; their Ishta/Kashta surrogates are a separate 1c-3 concern).

**Mean longitudes — Raman's epoch method** (epoch 1900-01-01 00:00 at 76°E Ujjain; `I` = interval days from epoch to birth in UT; `t` = birth_year − 1900), validated to ≤0.12° vs Raman's stated means:
```
MeanSun   = 257.4568 + 0.98560·I
MeanMars  = 270.22   + 0.52402·I
MeanJup   = 220.04   + 0.08310·I − (3.33 + 0.0067·t)
MeanSat   = 236.74   + 0.03344·I + (5    + 0.001·t)
MeanMercury = MeanVenus = MeanSun
SeegBudha = 164.0    + 4.0923·I  + (6.67 − 0.00133·t)
SeegSukra = 328.51   + 1.60214·I − (5    + 0.001·t)
SeegrochchaOf(Mars|Jupiter|Saturn) = MeanSun          # superior planets
```
(all mod 360). Mean longitudes are **sidereal in Raman's frame** — consistent with the chart's Raman-sidereal true longitudes, so no ayanamsa enters the Cheshta arc.

---

## File structure

| File | Responsibility |
|---|---|
| `app/raman_saab/primitives/shadbala/cheshta.py` | `chesta_kendra`, `cheshta_bala` (pure, given seegrochcha/mean/true); `cheshta_bala_for_chart(planet, chart, means)` |
| `app/raman_saab/chart/mean_longitudes.py` | `mean_longitudes(jd_ut, year)` → dict of mean longs + seegrochchas (epoch method) |
| `tests/raman_saab/primitives/shadbala/test_cheshta.py` | pure-formula unit + fixture pin (5 planets, injected means) |
| `tests/raman_saab/chart/test_mean_longitudes.py` | epoch method validated vs Raman's stated means |

---

## Task 1: Cheshta pure formula + fixture pin

**Files:** Create `app/raman_saab/primitives/shadbala/cheshta.py`; Test `tests/raman_saab/primitives/shadbala/test_cheshta.py`

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import cheshta

# GBB Standard Horoscope: stated mean longitudes, seegrochchas, true longitudes (deg).
_TRUE = {"Mars":229+49/60, "Mercury":180+33/60, "Jupiter":83+35/60, "Venus":170+4/60, "Saturn":124+51/60}
_MEAN = {"Mars":266.34, "Mercury":181.2275, "Jupiter":66.91, "Venus":181.2275, "Saturn":111.23}
_SEEG = {"Mars":181.2275, "Mercury":174.49, "Jupiter":181.2275, "Venus":158.35, "Saturn":181.2275}
_EXPECTED = {"Mars":22.28, "Mercury":2.13, "Jupiter":35.33, "Venus":5.76, "Saturn":21.06}

def test_chesta_kendra_pins_ramans_worked_values():
    # Kuja CK 293.15 (reduced 66.85)
    ck = cheshta.chesta_kendra(_SEEG["Mars"], _MEAN["Mars"], _TRUE["Mars"])
    assert abs(ck - 293.15) < 0.2

def test_cheshta_bala_fixture_five_planets():
    for p, exp in _EXPECTED.items():
        got = cheshta.cheshta_bala(_SEEG[p], _MEAN[p], _TRUE[p])
        assert abs(got - exp) < 0.5, f"{p}: got {got}, expected {exp}"

def test_sun_moon_have_no_cheshta_in_total():
    # The public chart-level helper returns 0 for Sun/Moon/nodes (GBB: no Cheshta in total).
    assert cheshta.PLANETS == ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final, Mapping
from app.raman_saab.chart.model import RamanChart

# The 5 planets that receive Cheshta Bala. Sun & Moon get NONE in the Shadbala total
# (GBB-6:23-28); their surrogates are computed only for Ishta/Kashta (Phase 1c-3).
PLANETS: Final[tuple[str, ...]] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def chesta_kendra(seegrochcha: float, mean_lon: float, true_lon: float) -> float:
    """Sripathi Chesta Kendra (Arc of Retrogression), degrees 0..360.
    CK = Seegrochcha − (Mean + True)/2  (OCR-corrected; GBB-6:544-551 + external Sripathi)."""
    ck = (seegrochcha - (mean_lon + true_lon) / 2.0) % 360.0
    return ck


def cheshta_bala(seegrochcha: float, mean_lon: float, true_lon: float) -> float:
    """Cheshta Bala in Shashtiamsas = reduced Chesta Kendra / 3 (0 at 0°, 60 at 180°)."""
    ck = chesta_kendra(seegrochcha, mean_lon, true_lon)
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)


def cheshta_bala_for_chart(planet: str, chart: RamanChart,
                           means: Mapping[str, float], seegrochchas: Mapping[str, float]) -> float:
    """Chart-level Cheshta: 0 for Sun/Moon/nodes, else the formula using the supplied
    mean longitudes + seegrochchas and the planet's true longitude from the chart."""
    if planet not in PLANETS or planet not in chart.planets:
        return 0.0
    return cheshta_bala(seegrochchas[planet], means[planet], chart.planets[planet].lon)
```
- [ ] **Step 4:** PASS. **Step 5:** report (no commit).

---

## Task 2: Mean longitudes (Raman's epoch method)

**Files:** Create `app/raman_saab/chart/mean_longitudes.py`; Test `tests/raman_saab/chart/test_mean_longitudes.py`

Lives in `chart/` (uses `swe.julday` for the epoch JD). The constants/mean-motions were verified to reproduce Raman's stated means to ≤0.12°.

- [ ] **Step 1: failing test**
```python
from app.raman_saab.chart import mean_longitudes as ml

def test_epoch_method_matches_ramans_stated_means():
    # Standard Horoscope interval I = 6862.578 days, t = 18. Reproduce GBB-6:99/104 means.
    out = ml.mean_and_seeg_from_interval(6862.578, t=18)
    assert abs(out["mean"]["Sun"] - 181.2275) < 0.2
    assert abs(out["mean"]["Mars"] - 266.34) < 0.2
    assert abs(out["mean"]["Jupiter"] - 66.91) < 0.2
    assert abs(out["mean"]["Saturn"] - 111.23) < 0.2
    assert abs(out["seeg"]["Mercury"] - 174.49) < 0.2
    assert abs(out["seeg"]["Venus"] - 158.35) < 0.2
    # superior seegrochchas == Mean Sun
    assert out["seeg"]["Mars"] == out["mean"]["Sun"]

def test_interval_from_jd_for_standard_horoscope():
    import swisseph as swe
    # 16 Oct 1918, 13:54 Ujjain (76E) = 08:50 UT. Interval ~6862.578 days from epoch.
    jd = swe.julday(1918, 10, 16, 8 + 50/60.0, swe.GREG_CAL)
    I = ml.interval_days(jd)
    assert abs(I - 6862.578) < 0.6   # within ~half a day (tune if needed)
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement**
```python
from __future__ import annotations
from typing import Final
import swisseph as swe

# Epoch: 1900-01-01 00:00 at 76°E Ujjain. In UT that is 76/360 day earlier than 00:00 UT.
_EPOCH_JD: Final[float] = swe.julday(1900, 1, 1, 0.0, swe.GREG_CAL) - 76.0 / 360.0

# (epoch constant, daily mean motion °/day). Verified to reproduce Raman's means to <=0.12°.
_MEAN: Final[dict[str, tuple[float, float]]] = {
    "Sun": (257.4568, 0.98560), "Mars": (270.22, 0.52402),
    "Jupiter": (220.04, 0.08310), "Saturn": (236.74, 0.03344)}
_SEEG_INNER: Final[dict[str, tuple[float, float]]] = {
    "Mercury": (164.0, 4.0923), "Venus": (328.51, 1.60214)}


def interval_days(jd_ut: float) -> float:
    """Interval in days from the 76°E epoch to the birth moment (UT)."""
    return jd_ut - _EPOCH_JD


def mean_and_seeg_from_interval(interval: float, *, t: int) -> dict[str, dict[str, float]]:
    """Mean longitudes + seegrochchas (Raman's epoch method, GBB-6:88-104). t = year − 1900."""
    mean = {p: (c + m * interval) % 360.0 for p, (c, m) in _MEAN.items()}
    mean["Jupiter"] = (mean["Jupiter"] - (3.33 + 0.0067 * t)) % 360.0
    mean["Saturn"] = (mean["Saturn"] + (5.0 + 0.001 * t)) % 360.0
    mean["Mercury"] = mean["Venus"] = mean["Sun"]                 # inner mean long = mean Sun
    seeg = {p: mean["Sun"] for p in ("Mars", "Jupiter", "Saturn")}  # superior seegrochcha
    seeg["Mercury"] = (_SEEG_INNER["Mercury"][0] + _SEEG_INNER["Mercury"][1] * interval
                       + (6.67 - 0.00133 * t)) % 360.0
    seeg["Venus"] = (_SEEG_INNER["Venus"][0] + _SEEG_INNER["Venus"][1] * interval
                     - (5.0 + 0.001 * t)) % 360.0
    return {"mean": mean, "seeg": seeg}


def mean_longitudes(jd_ut: float, year: int) -> dict[str, dict[str, float]]:
    """Convenience: mean longitudes + seegrochchas for a birth JD (UT) and civil year."""
    return mean_and_seeg_from_interval(interval_days(jd_ut), t=year - 1900)
```
> **Implementer note:** the `interval_days` epoch offset (`76/360` day) and the test's UT conversion may need a small tune so `I≈6862.578`; the means are robust to ~0.5-day interval error (the bala divides by 3). If `test_interval_from_jd` is off by >0.6 day, adjust the epoch-JD longitude term or the test's assumed UT, and keep `test_epoch_method_matches_ramans_stated_means` (the doctrine pin) exact. Do NOT change the epoch constants/mean-motions — they are verified.

- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 3: wire mean longitudes into the chart-level Cheshta (optional convenience)

**Files:** Modify `tests/raman_saab/primitives/shadbala/test_cheshta.py` (add an end-to-end case)

Tie Task 1 + Task 2 together: a real ephemeris chart's Cheshta computed from its `jd_ut` via the epoch method. (Full adapter wiring of `cheshta` into the Shadbala total + `PlanetPos` is Phase 1c-3.)

- [ ] **Step 1: failing test** (append)
```python
def test_cheshta_end_to_end_on_ephemeris_chart():
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.chart import mean_longitudes as ml
    from app.raman_saab.primitives.shadbala import cheshta
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    mns = ml.mean_longitudes(chart.jd_ut, 1990)
    for p in cheshta.PLANETS:
        val = cheshta.cheshta_bala_for_chart(p, chart, mns["mean"], mns["seeg"])
        assert 0.0 <= val <= 60.0      # valid Shashtiamsa range for a real chart
```
- [ ] **Step 2:** Run → should PASS once Tasks 1-2 exist (it's an integration smoke test). If any value is out of [0,60], debug the mean/seeg/true frame consistency.
- [ ] **Step 3:** report.

---

## Phase 1c-2a done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` green (existing 89 + new; import guard passes).
- `cheshta.cheshta_bala` reproduces all 5 GBB worked values (±0.5 Sh); `mean_longitudes` reproduces Raman's stated means (±0.2°).
- Cheshta is 0 for Sun/Moon/nodes in the chart-level helper.
- **Carry-overs to 1c-3:** wire Cheshta into the Shadbala total + `PlanetPos`; the Sun/Moon Cheshta *surrogates* for Ishta/Kashta (§9); confirm the mean-longitude frame on a named-historical chart.

**Next:** Phase 1c-2b — Kala (9 sub-components). Then 1c-3 — total assembly + Bhava-bala + Ishta/Kashta + backfills.
