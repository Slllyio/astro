# Raman Saab — Phase 1c-2b: Kala Bala — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Implement **Kala Bala** (temporal strength) — all 9 sub-components — re-derived to B.V. Raman's *Graha & Bhava Balas* and pinned to his worked "Standard Horoscope" Kala column.

**Architecture:** A pure `shadbala/kala.py` with one function per sub-component, each taking the chart + an injected **`KalaContext`** (the temporal facts Raman derives separately: birth-degrees, day/night third, the year/month/weekday/hora lords, ayanamsa). Track-B / doctrine-first: the fixture injects Raman's stated context, so the 9 **formulae** are pinned without ephemeris. Building the context from a real birth (sunrise, Ahargana, Chaldean hora order) is `chart/kala_context.py` — Task 4, the ephemeris/date piece.

**Tech Stack:** Python 3.12, frozen dataclasses, pytest. `kala_context.py` reuses the `swe.rise_trans` pattern from `chart/upagrahas.py`; `kala.py` is pure. No `app/core`.

**Scope.** IN: `shadbala/kala.py` (9 sub-components + `kala_bala`), `KalaContext`, fixture pin, and `chart/kala_context.py` (real-chart context, with the Ahargana year/month lords flagged if intractable). OUT (1c-3): wiring Kala into the total Shadbala + `PlanetPos`.

**Spec/authority:** `docs/raman_saab/gbb_shadbala_reference.md` §3. Every formula below was **verified live** against Raman's worked example.

---

## Doctrine (all verified live; reference §3)

Fixture Kala column (Shashtiamsas): Sun 104.49 · Moon 202.75 · Mars 28.39 · Mercury 219.92 · Jupiter 211.93 · Venus 116.81 · Saturn 115.69 (≈115.74). Per-sub-component breakdown (all reconcile):

| sub | Sun | Moon | Mars | Merc | Jup | Ven | Sat |
|---|---|---|---|---|---|---|---|
| Nathonnatha | 48.84 | 11.16 | 11.16 | 60.00 | 48.84 | 48.84 | 11.16 |
| Paksha | 15.83 | 88.34 | 15.83 | 44.17 | 44.17 | 44.17 | 15.83 |
| Tribhaga | — | — | — | — | 60.00 | — | 60.00 |
| Abda(15)/Masa(30)/Vara(45) | — | — | — | M30+V45 | — | — | A15 |
| Hora(60) | — | 60.00 | — | — | — | — | — |
| Ayana | 39.82 | 43.26 | **1.40** | 40.75 | 58.92 | **23.80** | 13.75 |
| Yuddha | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

1. **Nathonnatha** (GBB-5:115-147): `bd = (time-from-midnight in hours)·15`; if `bd>180: bd=360−bd`.
   `Diva (Sun,Jup,Venus) = bd/3` · `Ratri (Moon,Mars,Saturn) = (180−bd)/3` · `Mercury = 60 always`.
2. **Paksha** (GBB-5:215-223): `s=(Moon−Sun)%360; if s>180: s=360−s; shubha=s/3`. Benefics
   (Jup,Venus,Mercury,+waxing-Moon) = shubha; malefics (Sun,Mars,Saturn) = 60−shubha. **Moon DOUBLED.**
3. **Tribhaga** (GBB-5:253-320): the ruler of the birth-third gets **60**; day thirds = Mercury/Sun/Saturn,
   night thirds = Moon/Venus/Mars; **Jupiter always 60**. All others 0.
4-7. **Abda 15 / Masa 30 / Vara 45 / Hora 60** to the year/month/weekday/hora lord (GBB-5:563-596).
8. **Ayana** (GBB-5:936-957): `sayana = nirayana + ayanamsa`; `bhuja` = dist to nearest equinox
   (0/90/180/270); declination via the 6×15° table (cumulative [0,362,703,1002,1238,1388,1440]′,
   increments [362,341,299,236,150,52]) with linear interpolation `decl = cum[q] + inc[q]·(bhuja−15q)/15`
   (arc-min→deg). North if sayana≤180 else South. Sign: **Sun/Mars/Jup/Venus N+ S−; Saturn/Moon S+ N−;
   Mercury always +**. `Ayana = ((24 + signed_decl)/48)·60`; **DOUBLE for the Sun**.
9. **Yuddha** (GBB-5:1001-1043): planets (Mars,Merc,Jup,Venus,Saturn) <1° apart are at war; lesser
   longitude wins; `Yuddha = |ΔBala| / Δdisc-diameter`; victor +=, loser −=. Disc diam (″): Mars 9.4,
   Mercury 6.6, Jupiter 190.4, Venus 16.6, Saturn 158.0. (Fixture: none <1° → all 0.)

**Verified-live note:** Ayana reproduces 5/7 exactly; **Mars (formula 1.90 vs book 1.40) and Venus
(formula 24.30 vs book 23.80)** are book self-inconsistencies (the printed total uses the lower value
against the stated formula). Implement the FORMULA; pin the 5 clean cells; `xfail(strict)` Mars/Venus
Ayana with the diagnosis — same policy as the Sthana cusps.

---

## File structure

| File | Responsibility |
|---|---|
| `app/raman_saab/primitives/shadbala/kala.py` | `KalaContext` + 9 sub-component fns + `kala_bala(planet, chart, ctx)` |
| `app/raman_saab/chart/kala_context.py` | build `KalaContext` from a real chart/birth (Task 4) |
| `tests/raman_saab/primitives/shadbala/test_kala.py` | sub-component units + fixture pin (injected ctx) |
| `tests/raman_saab/chart/test_kala_context.py` | real-chart context (weekday/sunrise/hora) |

---

## Task 1: KalaContext + the 4 longitude/time sub-components

**Files:** Create `app/raman_saab/primitives/shadbala/kala.py`; Test `tests/raman_saab/primitives/shadbala/test_kala.py`

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import kala
from app.raman_saab.chart.model import RamanChart

_NIR = {"Sun":179+8/60,"Moon":311+40/60,"Mars":229+49/60,"Mercury":180+33/60,
        "Jupiter":83+35/60,"Venus":170+4/60,"Saturn":124+51/60}
_CHART = RamanChart.from_stated_positions(
    {p:{"lon":l,"bhava":1} for p,l in _NIR.items()}, asc_lon=185.0, ayanamsa="raman")

def test_nathonnatha():
    # birth 2:14pm -> bd=(14.2333*15)=213.5 -> 360-213.5=146.5 ; Diva=48.83, Ratri=11.17, Merc=60
    assert abs(kala.nathonnatha_bala("Sun", 146.5) - 48.83) < 0.1
    assert abs(kala.nathonnatha_bala("Moon", 146.5) - 11.17) < 0.1
    assert kala.nathonnatha_bala("Mercury", 146.5) == 60.0

def test_paksha_moon_doubled():
    assert abs(kala.paksha_bala("Moon", _CHART) - 88.34) < 0.2
    assert abs(kala.paksha_bala("Sun", _CHART) - 15.83) < 0.2     # malefic = 60 - shubha
    assert abs(kala.paksha_bala("Jupiter", _CHART) - 44.17) < 0.2 # benefic = shubha

def test_ayana_clean_cells():
    assert abs(kala.ayana_bala("Sun", _CHART, 21+16/60) - 39.82) < 0.2   # doubled
    assert abs(kala.ayana_bala("Jupiter", _CHART, 21+16/60) - 58.92) < 0.2
    assert abs(kala.ayana_bala("Saturn", _CHART, 21+16/60) - 13.75) < 0.2

def test_yuddha_zero_when_no_war():
    assert kala.yuddha_bala("Mars", _CHART, {}) == 0.0   # no planet within 1 deg
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement** (KalaContext + the 4 functions)
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Final, Mapping
from app.raman_saab.chart.model import RamanChart

_DIVA: Final[frozenset[str]] = frozenset({"Sun", "Jupiter", "Venus"})
_RATRI: Final[frozenset[str]] = frozenset({"Moon", "Mars", "Saturn"})
_KALA_PLANETS: Final[tuple[str, ...]] = ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn")


@dataclass(frozen=True)
class KalaContext:
    """Temporal facts Raman derives outside the longitudes, injected so the Kala formulae
    are testable Track-B. Built from a real chart by chart/kala_context.py (Task 4)."""
    birth_degrees: float          # time-from-midnight in degrees (Nathonnatha)
    is_day: bool                  # day vs night birth (Tribhaga)
    day_third: int                # 0,1,2 — which third of the day/night (Tribhaga)
    year_lord: str                # Abda
    month_lord: str               # Masa
    weekday_lord: str             # Vara
    hora_lord: str                # Hora
    ayanamsa: float               # for Ayana (Sayana = nirayana + ayanamsa)


def nathonnatha_bala(planet: str, birth_degrees: float) -> float:
    if planet not in _KALA_PLANETS:
        return 0.0
    bd = birth_degrees % 360.0
    if bd > 180.0:
        bd = 360.0 - bd
    if planet == "Mercury":
        return 60.0
    return round(bd / 3.0 if planet in _DIVA else (180.0 - bd) / 3.0, 3)


def paksha_bala(planet: str, chart: RamanChart) -> float:
    if planet not in _KALA_PLANETS or "Moon" not in chart.planets or "Sun" not in chart.planets:
        return 0.0
    s = (chart.planets["Moon"].lon - chart.planets["Sun"].lon) % 360.0
    if s > 180.0:
        s = 360.0 - s
    shubha = s / 3.0
    if planet == "Moon":
        return round(shubha * 2.0, 3)                    # Moon doubled
    benefic = planet in ("Jupiter", "Venus", "Mercury")  # + waxing Moon (handled above)
    return round(shubha if benefic else 60.0 - shubha, 3)


# Ayana declination table (arc-min): cumulative at 0,15,..,90 and the per-15° increments.
_CUM: Final[tuple[float, ...]] = (0, 362, 703, 1002, 1238, 1388, 1440)
_INC: Final[tuple[float, ...]] = (362, 341, 299, 236, 150, 52)
_AYANA_ADD_NORTH: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Venus"})


def _declination(sayana_lon: float) -> tuple[float, bool]:
    L = sayana_lon % 360.0
    if L <= 90:    bhuja, north = L, True
    elif L <= 180: bhuja, north = 180 - L, True
    elif L <= 270: bhuja, north = L - 180, False
    else:          bhuja, north = 360 - L, False
    q = min(int(bhuja // 15), 5)
    decl_min = _CUM[q] + _INC[q] * (bhuja - 15 * q) / 15.0
    return decl_min / 60.0, north


def ayana_bala(planet: str, chart: RamanChart, ayanamsa: float) -> float:
    if planet not in _KALA_PLANETS or planet not in chart.planets:
        return 0.0
    decl, north = _declination(chart.planets[planet].lon + ayanamsa)
    if planet == "Mercury":
        signed = decl
    elif planet in _AYANA_ADD_NORTH:
        signed = decl if north else -decl
    else:                                   # Saturn, Moon: S additive, N subtractive
        signed = -decl if north else decl
    val = ((24.0 + signed) / 48.0) * 60.0
    return round(val * 2.0 if planet == "Sun" else val, 3)


_DISC: Final[dict[str, float]] = {"Mars": 9.4, "Mercury": 6.6, "Jupiter": 190.4, "Venus": 16.6, "Saturn": 158.0}


def yuddha_bala(planet: str, chart: RamanChart, prior_bala: Mapping[str, float]) -> float:
    """Planetary-war adjustment (GBB-5:1001-1043). prior_bala = each planet's (Sthana+Dik+Kala-so-far)
    aggregate. Returns the signed Yuddha adjustment (0 if not at war)."""
    if planet not in _DISC or planet not in chart.planets:
        return 0.0
    for other, p in chart.planets.items():
        if other == planet or other not in _DISC:
            continue
        sep = abs(chart.planets[planet].lon - p.lon) % 360.0
        sep = min(sep, 360.0 - sep)
        if sep < 1.0 and prior_bala:
            diff = prior_bala.get(planet, 0.0) - prior_bala.get(other, 0.0)
            yuddha = abs(diff) / abs(_DISC[planet] - _DISC[other])
            winner = planet if chart.planets[planet].lon < p.lon else other
            return round(yuddha if winner == planet else -yuddha, 3)
    return 0.0
```
- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 2: the 5 lord/third sub-components (Tribhaga, Abda, Masa, Vara, Hora)

**Files:** Modify `kala.py`; Test `test_kala.py` (append)

- [ ] **Step 1: failing test** (append)
```python
def test_tribhaga():
    # 3rd day-third (index 2) -> Saturn 60; Jupiter always 60; others 0.
    assert kala.tribhaga_bala("Saturn", is_day=True, day_third=2) == 60.0
    assert kala.tribhaga_bala("Jupiter", is_day=True, day_third=2) == 60.0
    assert kala.tribhaga_bala("Sun", is_day=True, day_third=2) == 0.0

def test_abda_masa_vara_hora():
    assert kala.abda_bala("Saturn", "Saturn") == 15.0
    assert kala.masa_bala("Mercury", "Mercury") == 30.0
    assert kala.vara_bala("Mercury", "Mercury") == 45.0
    assert kala.hora_bala("Moon", "Moon") == 60.0
    assert kala.abda_bala("Sun", "Saturn") == 0.0
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement** (append to kala.py)
```python
# Tribhaga rulers by third (GBB-5:264-273).
_DAY_THIRDS: Final[tuple[str, ...]] = ("Mercury", "Sun", "Saturn")
_NIGHT_THIRDS: Final[tuple[str, ...]] = ("Moon", "Venus", "Mars")


def tribhaga_bala(planet: str, *, is_day: bool, day_third: int) -> float:
    if planet == "Jupiter":
        return 60.0                                  # Jupiter always
    ruler = (_DAY_THIRDS if is_day else _NIGHT_THIRDS)[day_third]
    return 60.0 if planet == ruler else 0.0


def abda_bala(planet: str, year_lord: str) -> float:
    return 15.0 if planet == year_lord else 0.0

def masa_bala(planet: str, month_lord: str) -> float:
    return 30.0 if planet == month_lord else 0.0

def vara_bala(planet: str, weekday_lord: str) -> float:
    return 45.0 if planet == weekday_lord else 0.0

def hora_bala(planet: str, hora_lord: str) -> float:
    return 60.0 if planet == hora_lord else 0.0
```
- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 3: kala_bala assembly + fixture pin

**Files:** Modify `kala.py` (add `kala_bala`); Test `test_kala.py` (append the fixture)

- [ ] **Step 1: implement `kala_bala`** (append to kala.py)
```python
def kala_bala(planet: str, chart: RamanChart, ctx: KalaContext,
              prior_bala: Mapping[str, float] | None = None) -> float:
    """Total Kala Bala (Shashtiamsas) = Σ of the 9 sub-components. Yuddha needs the running
    (Sthana+Dik+Kala) aggregate (prior_bala) — pass {} / None pre-assembly (Yuddha=0)."""
    if planet not in _KALA_PLANETS:
        return 0.0
    total = (nathonnatha_bala(planet, ctx.birth_degrees)
             + paksha_bala(planet, chart)
             + tribhaga_bala(planet, is_day=ctx.is_day, day_third=ctx.day_third)
             + abda_bala(planet, ctx.year_lord)
             + masa_bala(planet, ctx.month_lord)
             + vara_bala(planet, ctx.weekday_lord)
             + hora_bala(planet, ctx.hora_lord)
             + ayana_bala(planet, chart, ctx.ayanamsa)
             + yuddha_bala(planet, chart, prior_bala or {}))
    return round(total, 3)
```
- [ ] **Step 2: fixture test** (append)
```python
# GBB Standard Horoscope context (Raman's stated intermediates).
_CTX = kala.KalaContext(birth_degrees=146.5, is_day=True, day_third=2,
                        year_lord="Saturn", month_lord="Mercury", weekday_lord="Mercury",
                        hora_lord="Moon", ayanamsa=21 + 16/60)
_KALA_TOTAL = {"Sun":104.49, "Moon":202.75, "Mercury":219.92, "Jupiter":211.93, "Saturn":115.69}
#   (Mars 28.39 & Venus 116.81 carry the Ayana book-inconsistency -> separate xfail)

def test_kala_column_clean_cells():
    for p, exp in _KALA_TOTAL.items():
        got = kala.kala_bala(p, _CHART, _CTX)
        assert abs(got - exp) < 1.0, f"{p}: got {got}, expected {exp}"

@pytest.mark.xfail(strict=True, reason="Ayana book self-inconsistency: formula gives Mars 1.90/"
                   "Venus 24.30, Raman's printed totals use 1.40/23.80 (off ~0.5 Sh). Engine "
                   "follows the stated (24+-kranty)/48 formula; carried to 1c-3.")
def test_kala_mars_venus_match_book_totals():
    assert abs(kala.kala_bala("Mars", _CHART, _CTX) - 28.39) < 1.0
    assert abs(kala.kala_bala("Venus", _CHART, _CTX) - 116.81) < 1.0
```
> Add `import pytest` to the test file. The clean cells (Sun/Moon/Mercury/Jupiter/Saturn) must pass;
> Mars/Venus are the documented Ayana xfail. If a clean cell misses, debug the offending
> sub-component against the §3 breakdown table (do NOT loosen past ~1 Sh).

- [ ] **Step 3:** Run `py -3.12 -m pytest tests/raman_saab/primitives/shadbala/test_kala.py -q`; report. **Do not commit.**

---

## Task 4: real-chart KalaContext (ephemeris/date) — build what's tractable, flag the rest

**Files:** Create `app/raman_saab/chart/kala_context.py`; Test `tests/raman_saab/chart/test_kala_context.py`

Build `kala_context(birth, chart, *, ayanamsa) -> KalaContext` from a real chart:
- **birth_degrees** = (local-time-from-midnight hours)·15 — from `BirthData` (pure).
- **weekday_lord** = from `jd_ut` (Vara; `swe.day_of_week` or `int((jd+1.5)%7)` → lord). 
- **is_day / day_third** = from sunrise/sunset (reuse the `swe.rise_trans` pattern in `chart/upagrahas.py`).
- **hora_lord** = Chaldean descending order (Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon) seeded by the
  weekday-lord at sunrise, advanced by horas-elapsed (GBB-5:606-627).
- **ayanamsa** = the chart's ayanamsa value in degrees (compute from the Raman sidereal mode, or pass through).
- **year_lord (Abda) / month_lord (Masa)** = via **Ahargana since creation** (GBB-5:343-423) — this is
  the hard piece (Kali-epoch day-count). **If intractable cleanly, compute weekday/hora/sunrise/birth_degrees
  and leave year_lord/month_lord as a documented `NotImplemented`/flagged carry-over to 1c-3** rather than
  shipping a wrong Ahargana. A real-chart test asserts the tractable fields are sane (weekday lord valid,
  is_day boolean, hora lord valid).

- [ ] TDD per the above; report which fields are computed vs flagged. **Do not commit.**

---

## Phase 1c-2b done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` green (existing + new; import guard passes).
- `kala.kala_bala` reproduces the 5 clean fixture cells (±1 Sh); Mars/Venus Ayana `xfail(strict)`.
- All 9 sub-components unit-tested; `KalaContext` injected for Track-B.
- `kala_context.py` builds the tractable real-chart fields; Ahargana year/month lords computed or flagged.
- **Carry-overs to 1c-3:** Mars/Venus Ayana book-inconsistency; any flagged Ahargana lords; wire Kala into the Shadbala total + `PlanetPos`.

**Next:** Phase 1c-3 — total Shadbala assembly (Sthana+Dik+Kala+Cheshta+Naisargika±Drik) + min-required verdict + Bhava-bala + Ishta/Kashta + `PlanetPos` wiring + all carry-overs.
