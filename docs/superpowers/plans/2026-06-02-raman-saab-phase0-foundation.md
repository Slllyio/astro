# Raman Saab — Phase 0: Foundation & Chart Adapter — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `app/raman_saab/` package and a deterministic, ayanamsa-isolated chart adapter that turns birth data into a `RamanChart` (planets + Chalita/Sripati bhavas + Navamsa), printable via a CLi — the foundation every later phase depends on.

**Architecture:** A new self-contained package. The adapter is the ONLY module that touches Swiss Ephemeris; it sets the chosen sidereal mode (default **Raman**), computes, and **restores** the prior global mode via a context manager so the repo's Lahiri-based `app/core` is never corrupted. Houses use **Sripati bhava** (Porphyry cusps reinterpreted as bhava-*madhyas*; a planet's bhava is decided by the sandhi/junction bracket it falls in — this is the "Bhava, not Rashi" fidelity fix). Strength/special fields (Shadbala, upagrahas, etc.) are typed `Optional` here and filled in Phase 1.

**Tech Stack:** Python 3.12, `pyswisseph` (`import swisseph as swe`), frozen dataclasses, pytest (`pythonpath=["."]`, run with `py -3.12 -m pytest`).

**Scope:** This is **Plan 1 of ~7** (one per spec phase). It implements spec §3–§4 (package + data model + adapter) and the §11 doctrine-lock guards relevant to the adapter. It produces working, testable software on its own: `python -m app.raman_saab ...` prints a cast chart. Phases 1–7 (primitives, doctrine-data, judges, longevity, timing, surfaces, golden-harness) get their own plans.

**Spec:** `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md`

---

## File structure (created in this plan)

| File | Responsibility |
|---|---|
| `app/raman_saab/__init__.py` | package marker + `__version__` |
| `app/raman_saab/chart/__init__.py` | re-export the public chart API |
| `app/raman_saab/chart/model.py` | frozen dataclasses (`BirthData`, `PlanetPos`, `RamanChart`, supporting structs) + `RamanChart.from_stated_positions` |
| `app/raman_saab/chart/constants.py` | sign lords, planet ids, element table (doctrine-neutral) |
| `app/raman_saab/chart/ayanamsa.py` | `sidereal_mode(name)` context manager (set + restore) |
| `app/raman_saab/chart/varga.py` | pure geometry: navamsa sign, nakshatra/pada, dispositor, vargottama |
| `app/raman_saab/chart/cusps.py` | Sripati bhava-madhyas, sandhis, `bhava_of(lon)` |
| `app/raman_saab/chart/adapter.py` | `cast_chart(birth, *, ayanamsa="raman") -> RamanChart` |
| `app/raman_saab/cli.py` + `__main__.py` | `python -m app.raman_saab` prints JSON/text chart |
| `tests/raman_saab/test_*.py` | paired tests (one per module) |

---

## Task 0: Package + test scaffolding

**Files:**
- Create: `app/raman_saab/__init__.py`, `app/raman_saab/chart/__init__.py`, `tests/raman_saab/__init__.py`

- [ ] **Step 1: Create the package files**

`app/raman_saab/__init__.py`:
```python
"""Raman Saab — an independent engine replicating B.V. Raman's
*How to Judge a Horoscope* methodology. See docs/raman_saab/methodology/."""
from __future__ import annotations

__version__ = "0.0.0"
```
`app/raman_saab/chart/__init__.py` and `tests/raman_saab/__init__.py`: empty files.

- [ ] **Step 2: Verify the package imports**

Run: `py -3.12 -c "import app.raman_saab; print(app.raman_saab.__version__)"`
Expected: prints `0.0.0`

- [ ] **Step 3: Commit**

```bash
git add app/raman_saab/__init__.py app/raman_saab/chart/__init__.py tests/raman_saab/__init__.py
git commit -m "feat(raman_saab): package skeleton"
```

---

## Task 1: Constants (doctrine-neutral)

**Files:**
- Create: `app/raman_saab/chart/constants.py`
- Test: `tests/raman_saab/test_constants.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.chart import constants as c

def test_sign_lords_complete():
    """All 12 signs have a lord; Aries->Mars, Leo->Sun, Pisces->Jupiter (BPHS rulerships)."""
    assert len(c.SIGN_LORDS) == 12
    assert c.SIGN_LORDS[1] == "Mars" and c.SIGN_LORDS[5] == "Sun" and c.SIGN_LORDS[12] == "Jupiter"

def test_grahas_are_nine():
    assert c.GRAHAS == ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/raman_saab/test_constants.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write minimal implementation**
```python
from __future__ import annotations
from typing import Final
import swisseph as swe

GRAHAS: Final[tuple[str, ...]] = (
    "Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu")

# Swiss Ephemeris ids for the 7 visible grahas (Rahu/Ketu handled via the node).
SWE_PLANETS: Final[dict[str, int]] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

SIGN_LORDS: Final[dict[int, str]] = {
    1:"Mars",2:"Venus",3:"Mercury",4:"Moon",5:"Sun",6:"Mercury",
    7:"Venus",8:"Mars",9:"Jupiter",10:"Saturn",11:"Saturn",12:"Jupiter"}

# Navamsa element start-signs (Fire->Aries, Earth->Cap, Air->Libra, Water->Cancer).
NAVAMSA_START: Final[tuple[int, ...]] = (1, 10, 7, 4)  # indexed by (sign-1) % 4
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/raman_saab/test_constants.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/constants.py tests/raman_saab/test_constants.py
git commit -m "feat(raman_saab): doctrine-neutral constants (sign lords, planet ids)"
```

---

## Task 2: The data model

**Files:**
- Create: `app/raman_saab/chart/model.py`
- Test: `tests/raman_saab/test_model.py`

> Note: spec §4 typed the strength/special fields non-optionally for illustration. Phase 0
> makes them `Optional[...] = None` (filled in Phase 1) so the adapter ships a valid chart now.

- [ ] **Step 1: Write the failing test**
```python
import dataclasses, pytest
from app.raman_saab.chart.model import BirthData, PlanetPos, RamanChart

def test_chart_is_frozen():
    p = PlanetPos(name="Sun", lon=100.0, sign=4, rasi_house=10, bhava=10,
                  bhava_sandhi=False, nakshatra=9, pada=2, retrograde=False,
                  navamsa_sign=7, vargottama=False, dispositor="Moon")
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.lon = 1.0  # type: ignore[misc]

def test_from_stated_positions_builds_chart_without_ephemeris():
    """Track-B constructor: inject Raman's printed positions, derive the rest, no swisseph."""
    stated = {"Sun": {"lon": 100.0, "bhava": 10}, "Moon": {"lon": 40.0, "bhava": 6}}
    chart = RamanChart.from_stated_positions(stated, asc_lon=15.0, ayanamsa="raman")
    assert chart.asc_sign == 1                      # 15° -> Aries
    assert chart.planets["Sun"].sign == 4            # 100° -> Cancer
    assert chart.planets["Sun"].bhava == 10          # taken from stated
    assert chart.planets["Sun"].rasi_house == 4      # whole-sign Cancer from Aries lagna
    assert chart.ayanamsa == "raman"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/raman_saab/test_model.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write minimal implementation**
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Mapping, Optional
from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS

@dataclass(frozen=True)
class BirthData:
    name: str; year: int; month: int; day: int
    hour: int; minute: int; tz_offset: float
    latitude: float; longitude: float

@dataclass(frozen=True)
class ShadbalaBreakdown:
    sthana: float; dig: float; kala: float
    cheshta: float; naisargika: float; drik: float; total: float

@dataclass(frozen=True)
class SpecialPoint:
    name: str; lon: float; sign: int; bhava: int; navamsa_sign: int

@dataclass(frozen=True)
class MarakaUnit:
    graha: str; tier: Literal["primary","secondary","tertiary"]; strength_rank: int

@dataclass(frozen=True)
class MarakaPoints:
    units: tuple[MarakaUnit, ...]; drekkana22_lord: str; navamsa64_lord: str

@dataclass(frozen=True)
class BalarishtaState:
    applies: bool; cancelled: bool; reasons: tuple[str, ...]

@dataclass(frozen=True)
class PlanetPos:
    name: str
    lon: float
    sign: int
    rasi_house: int
    bhava: int
    bhava_sandhi: bool
    nakshatra: int
    pada: int
    retrograde: bool
    navamsa_sign: int
    vargottama: bool
    dispositor: str
    combust_fraction: float = 0.0
    shadbala_rupas: Optional[ShadbalaBreakdown] = None   # Phase 1
    ishta: Optional[float] = None                         # Phase 1
    kashta: Optional[float] = None                        # Phase 1

@dataclass(frozen=True)
class RamanChart:
    ayanamsa: str
    jd_ut: Optional[float]            # None for from_stated_positions (no ephemeris)
    asc_sign: int
    asc_lon: float
    bhava_madhyas: tuple[float, ...]
    bhava_sandhis: tuple[float, ...]
    planets: Mapping[str, PlanetPos]
    birth: Optional[BirthData] = None
    upagrahas: Mapping[str, SpecialPoint] = None          # Phase 1
    arudha_lagna: Optional[SpecialPoint] = None           # Phase 1
    karakamsa: Optional[SpecialPoint] = None              # Phase 1
    maraka_points: Optional[MarakaPoints] = None          # Phase 1
    balarishta: Optional[BalarishtaState] = None          # Phase 1

    @classmethod
    def from_stated_positions(cls, stated: Mapping[str, Mapping[str, float]], *,
                              asc_lon: float, ayanamsa: str) -> "RamanChart":
        """Build a chart from a book's printed positions (Track-B / Tier-3 tests).
        `stated[planet] = {"lon": float, "bhava": int}`. Bhava is taken as given;
        rasi_house / navamsa / nakshatra / dispositor are derived from lon."""
        asc_sign = int(asc_lon // 30) + 1
        planets: dict[str, PlanetPos] = {}
        for name, d in stated.items():
            lon = float(d["lon"]); sign = int(lon // 30) + 1
            nak, pada = varga.nakshatra_pada(lon)
            nav = varga.navamsa_sign(lon)
            planets[name] = PlanetPos(
                name=name, lon=lon, sign=sign,
                rasi_house=((sign - asc_sign) % 12) + 1,
                bhava=int(d["bhava"]), bhava_sandhi=False,
                nakshatra=nak, pada=pada, retrograde=False,
                navamsa_sign=nav, vargottama=(nav == sign),
                dispositor=SIGN_LORDS[sign])
        return cls(ayanamsa=ayanamsa, jd_ut=None, asc_sign=asc_sign, asc_lon=asc_lon,
                   bhava_madhyas=(), bhava_sandhis=(), planets=planets)
```

- [ ] **Step 4: Run test to verify it passes** (Task 3 `varga` is needed — implement Task 3 first if red on import, or stub `varga` functions). Run: `py -3.12 -m pytest tests/raman_saab/test_model.py -v` → Expected: PASS once Task 3 lands.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/model.py tests/raman_saab/test_model.py
git commit -m "feat(raman_saab): chart data model + from_stated_positions (Track-B constructor)"
```

> Build order note: implement **Task 3 (varga) before** running Task 2's test, since `model` imports `varga`.

---

## Task 3: Varga geometry (pure, ayanamsa-agnostic)

**Files:**
- Create: `app/raman_saab/chart/varga.py`
- Test: `tests/raman_saab/test_varga.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.chart import varga

def test_navamsa_fire_sign_starts_aries():
    # 1° Aries -> first navamsa -> Aries (fire start). 100° (Cancer 10°) per element rule.
    assert varga.navamsa_sign(1.0) == 1

def test_nakshatra_pada_boundaries():
    # Each nakshatra = 13°20'. 0° -> Ashwini(1) pada 1; 13.5° -> Bharani(2) pada 1.
    assert varga.nakshatra_pada(0.0) == (1, 1)
    assert varga.nakshatra_pada(13.5)[0] == 2

def test_vargottama_helper():
    assert varga.is_vargottama(sign=1, navamsa=1) is True
    assert varga.is_vargottama(sign=1, navamsa=2) is False
```

- [ ] **Step 2: Run** `py -3.12 -m pytest tests/raman_saab/test_varga.py -v` → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.constants import NAVAMSA_START

_NAK_SPAN = 360.0 / 27.0
_PADA_SPAN = _NAK_SPAN / 4.0

def navamsa_sign(lon: float) -> int:
    """D9 sign (1..12). Element-based start: Fire->Aries, Earth->Cap, Air->Libra, Water->Cancer."""
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    part = int(deg_in_sign // (30 / 9))               # 0..8
    start = NAVAMSA_START[sign_idx % 4]               # 1-indexed start sign
    return ((start - 1 + part) % 12) + 1

def nakshatra_pada(lon: float) -> tuple[int, int]:
    nak = int(lon // _NAK_SPAN) + 1                   # 1..27
    pada = int((lon % _NAK_SPAN) // _PADA_SPAN) + 1   # 1..4
    return nak, pada

def is_vargottama(*, sign: int, navamsa: int) -> bool:
    return sign == navamsa
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/varga.py tests/raman_saab/test_varga.py
git commit -m "feat(raman_saab): navamsa / nakshatra / vargottama geometry"
```

---

## Task 4: Ayanamsa isolation context manager

**Files:**
- Create: `app/raman_saab/chart/ayanamsa.py`
- Test: `tests/raman_saab/test_ayanamsa_guard.py`

This is a **doctrine-lock guard**: Raman Saab must never leave the global swisseph sidereal mode changed (the repo's `app/core` re-sets Lahiri per call, but we restore anyway as belt-and-suspenders).

- [ ] **Step 1: Write the failing test**
```python
import swisseph as swe
from app.raman_saab.chart.ayanamsa import sidereal_mode, AYANAMSA

def test_mode_is_restored_after_context():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    before = swe.get_ayanamsa_ut(2451545.0)          # Lahiri value at J2000
    with sidereal_mode("raman"):
        inside = swe.get_ayanamsa_ut(2451545.0)
        assert abs(inside - before) > 0.1            # Raman differs from Lahiri (~0.9°)
    after = swe.get_ayanamsa_ut(2451545.0)
    assert abs(after - before) < 1e-9                # restored exactly

def test_unknown_ayanamsa_raises():
    import pytest
    with pytest.raises(ValueError):
        with sidereal_mode("nonsense"):
            pass
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
import contextlib
from typing import Final, Iterator
import swisseph as swe

AYANAMSA: Final[dict[str, int]] = {"raman": swe.SIDM_RAMAN, "lahiri": swe.SIDM_LAHIRI}

@contextlib.contextmanager
def sidereal_mode(name: str) -> Iterator[None]:
    """Set the swisseph sidereal mode for the duration, then restore the prior mode.
    Keeps Raman Saab from corrupting the repo's global (Lahiri) ayanamsa."""
    if name not in AYANAMSA:
        raise ValueError(f"unknown ayanamsa {name!r}; expected one of {sorted(AYANAMSA)}")
    prior = swe.get_sid_mode()                        # (mode, t0, ayan_t0)
    try:
        swe.set_sid_mode(AYANAMSA[name])
        yield
    finally:
        # restore prior mode (set_sid_mode takes mode, optional t0, ayan_t0)
        swe.set_sid_mode(prior[0], prior[1], prior[2]) if isinstance(prior, (tuple, list)) \
            else swe.set_sid_mode(prior)
```
> If `swe.get_sid_mode` is unavailable in the installed pyswisseph build, fall back to restoring `swe.SIDM_LAHIRI` (the repo default) in `finally`; add a comment and keep the test asserting Lahiri is restored.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/ayanamsa.py tests/raman_saab/test_ayanamsa_guard.py
git commit -m "feat(raman_saab): ayanamsa isolation context manager (set + restore)"
```

---

## Task 5: Sripati bhava (Chalita) cusps

**Files:**
- Create: `app/raman_saab/chart/cusps.py`
- Test: `tests/raman_saab/test_cusps.py`

The fidelity centrepiece: Porphyry cusps are reinterpreted as **bhava-madhyas** (Asc = madhya of the 1st, MC = madhya of the 10th); the **sandhis** (junctions) are the circular midpoints between consecutive madhyas; a planet's **bhava** is the bracket `[sandhi_i, sandhi_{i+1})` it falls in.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.chart import cusps

def test_sandhis_are_midpoints_of_madhyas():
    madhyas = tuple(float(x) for x in range(0, 360, 30))  # 12 evenly-spaced madhyas
    s = cusps.sandhis_from_madhyas(madhyas)
    assert len(s) == 12
    assert abs(s[0] - 345.0) < 1e-9        # midpoint(330, 0) wrapping = 345

def test_bhava_of_uses_sandhi_brackets():
    madhyas = tuple(float(x) for x in range(0, 360, 30))   # madhya[i]=30*i
    s = cusps.sandhis_from_madhyas(madhyas)
    # a planet exactly on madhya[3]=90 is squarely in bhava 4 (1-indexed)
    assert cusps.bhava_of(90.0, s) == 4
    # near a sandhi -> flagged
    assert cusps.is_on_sandhi(s[3], s, orb=1.0) is True
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations

def _circ_mid(a: float, b: float) -> float:
    """Circular midpoint of two longitudes, going the short way."""
    diff = (b - a) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (a + diff / 2.0) % 360.0

def sandhis_from_madhyas(madhyas: tuple[float, ...]) -> tuple[float, ...]:
    """sandhi[i] = junction *starting* bhava (i+1) = midpoint(madhya[i-1], madhya[i])."""
    n = len(madhyas)
    return tuple(_circ_mid(madhyas[i - 1], madhyas[i]) for i in range(n))

def _in_arc(x: float, start: float, end: float) -> bool:
    span = (end - start) % 360.0
    off = (x - start) % 360.0
    return off < span

def bhava_of(lon: float, sandhis: tuple[float, ...]) -> int:
    """Bhava (1..12) whose [sandhi_i, sandhi_{i+1}) arc contains lon."""
    n = len(sandhis)
    for i in range(n):
        if _in_arc(lon, sandhis[i], sandhis[(i + 1) % n]):
            return i + 1
    return 1  # unreachable for valid input

def is_on_sandhi(lon: float, sandhis: tuple[float, ...], *, orb: float = 1.0) -> bool:
    for s in sandhis:
        d = abs((lon - s + 180.0) % 360.0 - 180.0)
        if d < orb:
            return True
    return False
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/cusps.py tests/raman_saab/test_cusps.py
git commit -m "feat(raman_saab): Sripati bhava cusps (madhya->sandhi->bhava_of)"
```

---

## Task 6: The chart adapter

**Files:**
- Create: `app/raman_saab/chart/adapter.py`
- Test: `tests/raman_saab/test_adapter.py`

Casts a `RamanChart` from `BirthData` at the chosen ayanamsa. Uses **mean node** for Rahu (Raman's hand-computations used the mean node), Ketu = Rahu+180. Porphyry house system (`b'O'`) gives the bhava-madhyas.

- [ ] **Step 1: Write the failing test** (an *adapter-golden*: a known chart, tolerance-banded)
```python
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

# Canonical pin: Bangalore 1990-07-15 12:00 IST (the repo baseline), but asserted in RAMAN ayanamsa.
BANGALORE = BirthData("Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

def test_cast_chart_has_nine_grahas_and_lagna():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    assert set(chart.planets) == {"Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"}
    assert 1 <= chart.asc_sign <= 12
    assert len(chart.bhava_madhyas) == 12 and len(chart.bhava_sandhis) == 12

def test_ketu_opposes_rahu():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    diff = abs((chart.planets["Ketu"].lon - chart.planets["Rahu"].lon) % 360 - 180)
    assert diff < 1e-6

def test_every_planet_has_a_bhava_in_range():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    for p in chart.planets.values():
        assert 1 <= p.bhava <= 12 and 1 <= p.rasi_house <= 12
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
import logging
import swisseph as swe
from app.raman_saab.chart import cusps, varga
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SWE_PLANETS, SIGN_LORDS
from app.raman_saab.chart.model import BirthData, PlanetPos, RamanChart

logger = logging.getLogger(__name__)
swe.set_ephe_path(None)  # built-in Moshier ephemeris (mirrors app/core)
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

def _jd_ut(b: BirthData) -> float:
    utc_hour = (b.hour + b.minute / 60.0) - b.tz_offset
    return swe.julday(b.year, b.month, b.day, utc_hour, swe.GREG_CAL)

def cast_chart(birth: BirthData, *, ayanamsa: str = "raman") -> RamanChart:
    """Birth data -> RamanChart. ONLY place that touches swisseph; ayanamsa isolated."""
    jd = _jd_ut(birth)
    with sidereal_mode(ayanamsa):
        # 1. Lagna + Porphyry cusps (reinterpreted as Vedic bhava-madhyas).
        cusp_arr, ascmc = swe.houses_ex(jd, birth.latitude, birth.longitude, b"O", swe.FLG_SIDEREAL)
        madhyas = tuple(float(x) for x in cusp_arr[:12])       # house 1..12 madhyas
        sandhis = cusps.sandhis_from_madhyas(madhyas)
        asc_lon = float(ascmc[0]); asc_sign = int(asc_lon // 30) + 1

        # 2. Planets.
        raw: dict[str, tuple[float, bool]] = {}
        for name, pid in SWE_PLANETS.items():
            res, _ = swe.calc_ut(jd, pid, _FLAGS)
            raw[name] = (float(res[0]) % 360.0, res[3] < 0)     # lon, retrograde
        node, _ = swe.calc_ut(jd, swe.MEAN_NODE, _FLAGS)        # Raman used the MEAN node
        raw["Rahu"] = (float(node[0]) % 360.0, True)
        raw["Ketu"] = ((float(node[0]) + 180.0) % 360.0, True)

    planets: dict[str, PlanetPos] = {}
    for name, (lon, retro) in raw.items():
        sign = int(lon // 30) + 1
        nak, pada = varga.nakshatra_pada(lon)
        nav = varga.navamsa_sign(lon)
        planets[name] = PlanetPos(
            name=name, lon=lon, sign=sign,
            rasi_house=((sign - asc_sign) % 12) + 1,
            bhava=cusps.bhava_of(lon, sandhis),
            bhava_sandhi=cusps.is_on_sandhi(lon, sandhis),
            nakshatra=nak, pada=pada, retrograde=retro,
            navamsa_sign=nav, vargottama=(nav == sign),
            dispositor=SIGN_LORDS[sign])
    return RamanChart(ayanamsa=ayanamsa, jd_ut=jd, asc_sign=asc_sign, asc_lon=asc_lon,
                      bhava_madhyas=madhyas, bhava_sandhis=sandhis, planets=planets, birth=birth)
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/chart/adapter.py tests/raman_saab/test_adapter.py
git commit -m "feat(raman_saab): chart adapter (ayanamsa-isolated; Sripati bhavas; mean node)"
```

---

## Task 7: CLI

**Files:**
- Create: `app/raman_saab/cli.py`, `app/raman_saab/__main__.py`
- Test: `tests/raman_saab/test_cli.py`

- [ ] **Step 1: Write the failing test**
```python
import json, subprocess, sys

def test_cli_prints_json_chart():
    out = subprocess.run(
        [sys.executable, "-m", "app.raman_saab", "--name", "T", "--date", "1990-07-15",
         "--time", "12:00", "--tz", "5.5", "--lat", "12.97", "--lon", "77.59", "--format", "json"],
        capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    assert data["ayanamsa"] == "raman"
    assert len(data["planets"]) == 9
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

`app/raman_saab/cli.py`:
```python
from __future__ import annotations
import argparse, dataclasses, json, sys
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

def _parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="app.raman_saab", description="Raman Saab chart")
    ap.add_argument("--name", required=True); ap.add_argument("--date", required=True)   # YYYY-MM-DD
    ap.add_argument("--time", required=True)                                              # HH:MM
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True); ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--ayanamsa", default="raman", choices=["raman", "lahiri"])
    ap.add_argument("--format", default="json", choices=["json", "text"])
    return ap.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    a = _parse(argv)
    y, mo, d = (int(x) for x in a.date.split("-")); hh, mm = (int(x) for x in a.time.split(":"))
    birth = BirthData(a.name, y, mo, d, hh, mm, a.tz, a.lat, a.lon)
    chart = cast_chart(birth, ayanamsa=a.ayanamsa)
    payload = {
        "ayanamsa": chart.ayanamsa, "asc_sign": chart.asc_sign, "asc_lon": round(chart.asc_lon, 4),
        "planets": {n: {"lon": round(p.lon, 4), "sign": p.sign, "rasi_house": p.rasi_house,
                        "bhava": p.bhava, "navamsa_sign": p.navamsa_sign,
                        "retrograde": p.retrograde} for n, p in chart.planets.items()},
    }
    if a.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Lagna: sign {chart.asc_sign} ({chart.asc_lon:.2f}°)  [ayanamsa={chart.ayanamsa}]")
        for n, p in chart.planets.items():
            print(f"  {n:8} {p.lon:7.2f}°  sign {p.sign:2}  bhava {p.bhava:2}  "
                  f"{'(R)' if p.retrograde else '   '}")
    return 0
```
`app/raman_saab/__main__.py`:
```python
from __future__ import annotations
import sys
from app.raman_saab.cli import main
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**
```bash
git add app/raman_saab/cli.py app/raman_saab/__main__.py tests/raman_saab/test_cli.py
git commit -m "feat(raman_saab): CLI prints the cast chart (json/text)"
```

---

## Task 8: Doctrine-lock guard — no forbidden `app/core` imports

**Files:**
- Test: `tests/raman_saab/test_import_guard.py`

Enforces spec §4.6: the package must not import the repo's blended-doctrine modules.

- [ ] **Step 1: Write the failing test**
```python
import ast, pathlib

FORBIDDEN = {"app.core.bhava_judge","app.core.reading_composer","app.core.drishti_argala",
             "app.core.yogas","app.core.shadbala"}
PKG = pathlib.Path("app/raman_saab")

def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {n.name for n in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            if node.module.startswith("app.core.dkp"):  # dkp_* family
                mods.add("app.core.dkp_*")
    return mods

def test_no_forbidden_core_imports():
    offenders = {}
    for f in PKG.rglob("*.py"):
        bad = _imports(f) & FORBIDDEN | {m for m in _imports(f) if m.startswith("app.core.dkp")}
        if bad:
            offenders[str(f)] = bad
    assert not offenders, f"forbidden app/core imports: {offenders}"
```

- [ ] **Step 2: Run** `py -3.12 -m pytest tests/raman_saab/test_import_guard.py -v`
Expected: PASS immediately (no offenders yet) — this guard *prevents regressions* in later phases.

- [ ] **Step 3: (no implementation needed — guard only)**

- [ ] **Step 4: Run the whole package suite**
Run: `py -3.12 -m pytest tests/raman_saab/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**
```bash
git add tests/raman_saab/test_import_guard.py
git commit -m "test(raman_saab): import guard against forbidden app/core modules"
```

---

## Phase 0 done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` is green.
- `py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59 --format text` prints a chart with Chalita bhavas.
- The ayanamsa-restore and import guards pass.

**Next plan:** Phase 1 — primitives (`chalita_bhava` refinement, real GBB Shadbala, dignity, dispositor chains, maraka, balarishta, combustion, sphutas) that fill the `Optional` chart fields and add the GBB ±1-rupa fixture.
