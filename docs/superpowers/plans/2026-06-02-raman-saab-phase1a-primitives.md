# Raman Saab — Phase 1a: Foundational Fact Primitives — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add the pure-function "fact" primitives the Raman Saab condition predicates read — dignity, planetary relationships, graded combustion, sign attributes (element/gender/etc.), the nakshatra layer (star-lord + tara), and dispositor/varga-lord chains — each a small, data-driven, independently-tested module over the Phase-0 `RamanChart`.

**Architecture:** New `app/raman_saab/primitives/` package. Every module is a pure function of a chart/longitude (no ephemeris, no global state). Doctrine data tables (exaltation degrees, naisargika friendships, nakshatra lords) are module-level constants. These primitives produce the facts; the condition algebra (Phase 2) and judges (Phase 3) consume them. This sub-plan covers the *cheap, no-cross-dependency* primitives; GBB Shadbala (1c) and functional-nature/special-points (1b) are separate plans.

**Tech Stack:** Python 3.12, frozen dataclasses, pytest (`py -3.12 -m pytest`). No new dependencies.

**Scope:** Plan 1a of the Phase-1 group. Implements the predicate-audit primitives: relationships, dignity, combustion, sign_attributes, nakshatra, dispositor. Out of scope here: Shadbala/bhava-bala/ishta-kashta (1c), functional-nature/yogakaraka/neecha-bhanga/parivartana (1b), upagrahas/arudha/karakamsa/maraka/balarishta (1b), sphutas (1c).

**Spec:** `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` · **Predicate set:** `docs/raman_saab/predicate_audit.md` §7

---

## File structure (created in this plan)

| File | Responsibility |
|---|---|
| `app/raman_saab/primitives/__init__.py` | package marker |
| `app/raman_saab/primitives/relationships.py` | exalt/debil/moolatrikona tables; naisargika friendship grid; combustion orbs |
| `app/raman_saab/primitives/dignity.py` | `dignity(planet, chart)` → compound 5-fold state |
| `app/raman_saab/primitives/combustion.py` | `combust_fraction(planet, chart)` graded by orb |
| `app/raman_saab/primitives/sign_attributes.py` | element, modality, parity, gender, keeta, sushka/watery, rise-type |
| `app/raman_saab/primitives/nakshatra.py` | `nakshatra_lord`, `tara_of`, `tara_position` |
| `app/raman_saab/primitives/dispositor.py` | `dispositor`, `dispositor_chain`, `navamsa_lord_of`, `drekkana_lord_of` |
| `tests/raman_saab/primitives/test_*.py` | paired tests |

---

## Task 0: Package scaffolding

- [ ] **Step 1:** Create `app/raman_saab/primitives/__init__.py` (empty) and `tests/raman_saab/primitives/__init__.py` (empty).
- [ ] **Step 2:** Run `py -3.12 -c "import app.raman_saab.primitives"` → no error.
- [ ] **Step 3:** Commit: `git add app/raman_saab/primitives/__init__.py tests/raman_saab/primitives/__init__.py && git commit -m "feat(raman_saab): primitives package skeleton"`

---

## Task 1: Relationships & dignity data tables

**Files:** Create `app/raman_saab/primitives/relationships.py`; Test `tests/raman_saab/primitives/test_relationships.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import relationships as r

def test_exaltation_signs_and_degrees():
    # Classical deep-exaltation points (sign, degree).
    assert r.EXALTATION["Sun"] == (1, 10.0)      # Aries 10
    assert r.EXALTATION["Saturn"] == (7, 20.0)   # Libra 20
    assert r.EXALTATION["Venus"] == (12, 27.0)   # Pisces 27

def test_debilitation_is_opposite_sign_same_degree():
    for p, (sign, deg) in r.EXALTATION.items():
        dsign, ddeg = r.DEBILITATION[p]
        assert dsign == ((sign + 6 - 1) % 12) + 1
        assert ddeg == deg

def test_naisargika_friendship_is_consistent():
    # Sun's friends include Moon/Mars/Jupiter; enemies Venus/Saturn; Mercury neutral.
    assert r.naisargika("Sun", "Jupiter") == "friend"
    assert r.naisargika("Sun", "Venus") == "enemy"
    assert r.naisargika("Sun", "Mercury") == "neutral"
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement** (verify these standard values; they are doctrine-critical)
```python
from __future__ import annotations
from typing import Final

# (sign 1..12, degree within sign) of deep exaltation.
EXALTATION: Final[dict[str, tuple[int, float]]] = {
    "Sun": (1, 10.0), "Moon": (2, 3.0), "Mars": (10, 28.0), "Mercury": (6, 15.0),
    "Jupiter": (4, 5.0), "Venus": (12, 27.0), "Saturn": (7, 20.0),
}
DEBILITATION: Final[dict[str, tuple[int, float]]] = {
    p: (((s + 6 - 1) % 12) + 1, d) for p, (s, d) in EXALTATION.items()
}
# Moolatrikona: (sign, start_deg, end_deg).
MOOLATRIKONA: Final[dict[str, tuple[int, float, float]]] = {
    "Sun": (5, 0.0, 20.0), "Moon": (2, 4.0, 30.0), "Mars": (1, 0.0, 12.0),
    "Mercury": (6, 16.0, 20.0), "Jupiter": (9, 0.0, 10.0), "Venus": (7, 0.0, 15.0),
    "Saturn": (11, 0.0, 20.0),
}
# Naisargika (natural) friendship — Parashara. friends/enemies; anything else neutral.
_FRIENDS: Final[dict[str, frozenset[str]]] = {
    "Sun": frozenset({"Moon", "Mars", "Jupiter"}),
    "Moon": frozenset({"Sun", "Mercury"}),
    "Mars": frozenset({"Sun", "Moon", "Jupiter"}),
    "Mercury": frozenset({"Sun", "Venus"}),
    "Jupiter": frozenset({"Sun", "Moon", "Mars"}),
    "Venus": frozenset({"Mercury", "Saturn"}),
    "Saturn": frozenset({"Mercury", "Venus"}),
}
_ENEMIES: Final[dict[str, frozenset[str]]] = {
    "Sun": frozenset({"Venus", "Saturn"}),
    "Moon": frozenset(),
    "Mars": frozenset({"Mercury"}),
    "Mercury": frozenset({"Moon"}),
    "Jupiter": frozenset({"Mercury", "Venus"}),
    "Venus": frozenset({"Sun", "Moon"}),
    "Saturn": frozenset({"Sun", "Moon", "Mars"}),
}
# General combustion orbs (degrees from Sun). Note: the longevity Astangata-harana
# uses its own orbs (doctrine/ayus_tables, Phase 4) — do NOT reuse these there.
COMBUSTION_ORB: Final[dict[str, float]] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
    "Venus": 10.0, "Saturn": 15.0,
}

def naisargika(of: str, towards: str) -> str:
    if towards in _FRIENDS.get(of, frozenset()):
        return "friend"
    if towards in _ENEMIES.get(of, frozenset()):
        return "enemy"
    return "neutral"
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): planetary relationship tables (exalt/debil/moolatrikona/friendship)`

---

## Task 2: Dignity (compound 5-fold)

**Files:** Create `dignity.py`; Test `test_dignity.py`

Raman uses **compound** (panchadha) relation = naisargika + tatkalika (temporal). Temporal friend = the other planet is in the 2/3/4/10/11/12 from this planet (by rasi_house); else temporal enemy. Compound: friend+friend=great-friend→treat as friend; friend+enemy / enemy+friend = neutral; enemy+enemy = great-enemy→enemy; with neutral, the non-neutral side wins (friend→friend, enemy→enemy); neutral+neutral=neutral.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.chart.model import RamanChart

def _chart(planet_lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planet_lons.items()},
        asc_lon=0.0, ayanamsa="raman")

def test_exalted_sun():
    assert dignity("Sun", _chart({"Sun": 10.0})) == "exalt"   # Aries 10

def test_debilitated_sun():
    assert dignity("Sun", _chart({"Sun": 190.0})) == "debil"  # Libra 10

def test_own_sign():
    assert dignity("Mars", _chart({"Mars": 5.0})) == "moolatrikona"  # Aries 5 (MT 0-12)
    assert dignity("Mars", _chart({"Mars": 215.0})) == "own"         # Scorpio (own, not MT)
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives import relationships as r

def _in_range(deg: float, lo: float, hi: float) -> bool:
    return lo <= deg < hi

def dignity(planet: str, chart: RamanChart) -> str:
    """Compound dignity ∈ {exalt, debil, moolatrikona, own, friend, neutral, enemy}.
    exalt/debil/moolatrikona/own are positional; friend/neutral/enemy use compound relation."""
    if planet in ("Rahu", "Ketu"):
        return "neutral"                      # Raman treats nodes by sign/conjunction, not dignity
    p = chart.planets[planet]
    sign, deg = p.sign, p.lon % 30.0
    # Categorical dignity is by SIGN (whole exaltation/debilitation sign). The deep-exaltation
    # DEGREE in the table is used only for the ayus arc (Phase 4) and uchcha-bala (Phase 1c).
    if sign == r.EXALTATION[planet][0]:
        return "exalt"
    if sign == r.DEBILITATION[planet][0]:
        return "debil"
    mt_s, mt_lo, mt_hi = r.MOOLATRIKONA[planet]
    if sign == mt_s and _in_range(deg, mt_lo, mt_hi):
        return "moolatrikona"
    if SIGN_LORDS[sign] == planet:
        return "own"
    return _compound_relation(planet, SIGN_LORDS[sign], chart)

def _temporal(of: str, towards: str, chart: RamanChart) -> str:
    a, b = chart.planets[of].rasi_house, chart.planets[towards].rasi_house
    dist = ((b - a) % 12) + 1
    return "friend" if dist in (2, 3, 4, 10, 11, 12) else "enemy"

_COMPOUND = {
    ("friend", "friend"): "friend", ("friend", "enemy"): "neutral",
    ("enemy", "friend"): "neutral", ("enemy", "enemy"): "enemy",
    ("friend", "neutral"): "friend", ("neutral", "friend"): "friend",
    ("enemy", "neutral"): "enemy", ("neutral", "enemy"): "enemy",
    ("neutral", "neutral"): "neutral",
}

def _compound_relation(of: str, lord: str, chart: RamanChart) -> str:
    if lord in ("Rahu", "Ketu") or of == lord:
        return "neutral"
    nat = r.naisargika(of, lord)
    tmp = _temporal(of, lord, chart)
    return _COMPOUND[(nat, tmp)]
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): compound (panchadha) dignity`

---

## Task 3: Graded combustion

**Files:** Create `combustion.py`; Test `test_combustion.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives.combustion import combust_fraction
from app.raman_saab.chart.model import RamanChart

def _c(sun, other_name, other_lon):
    return RamanChart.from_stated_positions(
        {"Sun": {"lon": sun, "bhava": 1}, other_name: {"lon": other_lon, "bhava": 1}},
        asc_lon=0.0, ayanamsa="raman")

def test_mars_far_from_sun_not_combust():
    assert combust_fraction("Mars", _c(0.0, "Mars", 100.0)) == 0.0

def test_mars_on_sun_fully_combust():
    assert combust_fraction("Mars", _c(50.0, "Mars", 50.0)) == 1.0

def test_partial_combustion_scales_with_orb():
    f = combust_fraction("Mars", _c(0.0, "Mars", 8.5))   # half of Mars' 17° orb
    assert 0.4 < f < 0.6

def test_sun_itself_never_combust():
    assert combust_fraction("Sun", _c(0.0, "Sun", 0.0)) == 0.0
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.relationships import COMBUSTION_ORB

def _circ_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)

def combust_fraction(planet: str, chart: RamanChart) -> float:
    """0.0 (free) .. 1.0 (exact conjunction with Sun), linear within the planet's orb."""
    if planet not in COMBUSTION_ORB or planet not in chart.planets or "Sun" not in chart.planets:
        return 0.0
    orb = COMBUSTION_ORB[planet]
    sep = _circ_sep(chart.planets[planet].lon, chart.planets["Sun"].lon)
    if sep >= orb:
        return 0.0
    return round(1.0 - sep / orb, 6)
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): graded combustion fraction`

---

## Task 4: Sign attributes

**Files:** Create `sign_attributes.py`; Test `test_sign_attributes.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import sign_attributes as s

def test_element_modality_parity():
    assert s.element(1) == "fire" and s.element(4) == "water"      # Aries fire, Cancer water
    assert s.modality(1) == "movable" and s.modality(2) == "fixed" and s.modality(3) == "common"
    assert s.parity(1) == "odd" and s.parity(2) == "even"

def test_sign_gender_matches_parity():
    assert s.sign_gender(1) == "masculine" and s.sign_gender(2) == "feminine"

def test_planet_gender_and_keeta():
    assert s.planet_gender("Jupiter") == "masculine"
    assert s.planet_gender("Venus") == "feminine"
    assert s.planet_gender("Mercury") == "neuter"
    assert s.is_keeta(8) is True and s.is_keeta(1) is False       # Scorpio is keeta
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from typing import Final

# sign 1..12 = Aries..Pisces.
def element(sign: str | int) -> str:
    return ("fire", "earth", "air", "water")[(int(sign) - 1) % 4]

def modality(sign: int) -> str:
    return ("movable", "fixed", "common")[(int(sign) - 1) % 3]

def parity(sign: int) -> str:
    return "odd" if int(sign) % 2 == 1 else "even"

def sign_gender(sign: int) -> str:
    return "masculine" if parity(sign) == "odd" else "feminine"

_PLANET_GENDER: Final[dict[str, str]] = {
    "Sun": "masculine", "Mars": "masculine", "Jupiter": "masculine",
    "Moon": "feminine", "Venus": "feminine",
    "Mercury": "neuter", "Saturn": "neuter", "Rahu": "neuter", "Ketu": "neuter",
}
def planet_gender(planet: str) -> str:
    return _PLANET_GENDER[planet]

_KEETA: Final[frozenset[int]] = frozenset({4, 8, 12})   # Cancer, Scorpio, Pisces
def is_keeta(sign: int) -> bool:
    return int(sign) in _KEETA

_SEERSHODAYA: Final[frozenset[int]] = frozenset({3, 5, 6, 7, 8, 11})  # head-rising
def rise_type(sign: int) -> str:
    if int(sign) == 12:
        return "ubhayodaya"
    return "seershodaya" if int(sign) in _SEERSHODAYA else "prushtodaya"

_SUSHKA: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})  # dry planets
def is_sushka(planet: str) -> bool:
    return planet in _SUSHKA
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): sign attributes (element/modality/parity/gender/keeta/rise-type)`

---

## Task 5: Nakshatra layer

**Files:** Create `nakshatra.py`; Test `test_nakshatra.py`

Nakshatra lord cycles Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury (Vimshottari order), repeating over the 27 stars. Tara = position of a planet's nakshatra counted (1-indexed) from the Janma nakshatra (the Moon's natal nakshatra), mapped into the 9-fold tara cycle.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import nakshatra as nk
from app.raman_saab.chart.model import RamanChart

def test_nakshatra_lords_cycle():
    assert nk.nakshatra_lord(1) == "Ketu"      # Ashwini
    assert nk.nakshatra_lord(2) == "Venus"     # Bharani
    assert nk.nakshatra_lord(10) == "Ketu"     # Magha (cycle repeats every 9)
    assert nk.nakshatra_lord(27) == "Mercury"  # Revati

def test_tara_position_from_janma():
    # Moon at 0° (Ashwini=1). A planet also in Ashwini = tara 1 (janma); 3rd star = vipat (3).
    chart = RamanChart.from_stated_positions(
        {"Moon": {"lon": 0.0, "bhava": 1}, "Mars": {"lon": 2 * (360/27), "bhava": 1}},
        asc_lon=0.0, ayanamsa="raman")
    assert nk.tara_position("Mars", chart) == 3
    assert nk.tara_of("Mars", chart) == "vipat"
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart

_NAK_LORDS: Final[tuple[str, ...]] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
_TARA_NAMES: Final[tuple[str, ...]] = (
    "janma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "naidhana", "mitra", "param_mitra")

def nakshatra_lord(nak: int) -> str:
    return _NAK_LORDS[(int(nak) - 1) % 9]

def tara_position(planet: str, chart: RamanChart) -> int:
    """1..9 tara of `planet`'s nakshatra counted from the Janma (natal Moon) nakshatra."""
    janma = chart.planets["Moon"].nakshatra
    nak = chart.planets[planet].nakshatra
    return ((nak - janma) % 27) % 9 + 1

def tara_of(planet: str, chart: RamanChart) -> str:
    return _TARA_NAMES[tara_position(planet, chart) - 1]
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): nakshatra lord + tara`

---

## Task 6: Dispositor & varga lords

**Files:** Create `dispositor.py`; Test `test_dispositor.py`

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import dispositor as d
from app.raman_saab.chart.model import RamanChart

def _c(lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")

def test_dispositor_is_sign_lord():
    assert d.dispositor("Mars", _c({"Mars": 100.0})) == "Moon"   # Cancer -> Moon

def test_dispositor_chain_terminates_at_own_sign():
    # Mars in Cancer(Moon) -> Moon in Taurus(Venus) -> Venus in Libra(own) STOP.
    chart = _c({"Mars": 100.0, "Moon": 40.0, "Venus": 190.0})
    assert d.dispositor_chain("Mars", chart) == ["Moon", "Venus"]

def test_navamsa_lord_of():
    # planet whose navamsa sign is Aries -> Mars.
    chart = _c({"Sun": 0.0})    # 0° Aries -> first navamsa Aries -> Mars
    assert d.navamsa_lord_of("Sun", chart) == "Mars"
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart import varga

def dispositor(planet: str, chart: RamanChart) -> str:
    return SIGN_LORDS[chart.planets[planet].sign]

def dispositor_chain(planet: str, chart: RamanChart, *, max_hops: int = 12) -> list[str]:
    """Follow lord-of-occupied-sign until a planet in its OWN sign (or a cycle/limit)."""
    chain: list[str] = []
    cur = planet
    seen = {planet}
    for _ in range(max_hops):
        lord = dispositor(cur, chart)
        if lord in ("Rahu", "Ketu") or lord not in chart.planets:
            break
        chain.append(lord)
        if SIGN_LORDS[chart.planets[lord].sign] == lord:   # lord in own sign -> terminus
            break
        if lord in seen:                                   # cycle guard
            break
        seen.add(lord); cur = lord
    return chain

def navamsa_lord_of(planet: str, chart: RamanChart) -> str:
    return SIGN_LORDS[chart.planets[planet].navamsa_sign]

def drekkana_lord_of(planet: str, chart: RamanChart) -> str:
    """Lord of the drekkana (D3) sign of the planet."""
    lon = chart.planets[planet].lon
    sign_idx = int(lon // 30)
    drek = int((lon % 30) // 10)                  # 0,1,2
    d3_sign = ((sign_idx + drek * 4) % 12) + 1     # classical: +0/+4/+8 signs
    return SIGN_LORDS[d3_sign]
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): dispositor chain + navamsa/drekkana lords`

---

## Task 7: Wire combustion into the adapter (fill the Phase-0 stub)

**Files:** Modify `app/raman_saab/chart/adapter.py`; Test `tests/raman_saab/test_adapter.py` (add a case)

- [ ] **Step 1: Write the failing test** (append to test_adapter.py)
```python
def test_adapter_populates_combust_fraction():
    # A planet within the Sun's orb should have combust_fraction > 0.
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    chart = cast_chart(BirthData("X",1990,7,15,12,0,5.5,12.97,77.59), ayanamsa="raman")
    # at least asserts the field is a float in [0,1] for every planet
    for p in chart.planets.values():
        assert 0.0 <= p.combust_fraction <= 1.0
```

- [ ] **Step 2:** Run → it likely PASSES already (stub is 0.0). To make it meaningful, instead assert combustion is actually computed: after wiring, Mercury/Venus near the Sun get >0. Adjust: build the chart, then re-derive expected via `combust_fraction` and assert equality.
```python
    from app.raman_saab.primitives.combustion import combust_fraction
    for name, p in chart.planets.items():
        assert p.combust_fraction == combust_fraction(name, chart)
```
Run → FAIL (adapter still sets 0.0).

- [ ] **Step 3: Implement** — in `adapter.py`, after building `planets` dict, recompute each `PlanetPos` with the real combustion. Since `PlanetPos` is frozen, build the dict in two passes: first with `combust_fraction=0.0`, then a second pass using `dataclasses.replace(p, combust_fraction=combustion.combust_fraction(name, partial_chart))`. Simplest: construct a provisional `RamanChart`, compute combustion per planet, then `dataclasses.replace` the planets. Add `from app.raman_saab.primitives import combustion` and `import dataclasses`.
```python
    chart = RamanChart(ayanamsa=ayanamsa, jd_ut=jd, asc_sign=asc_sign, asc_lon=asc_lon,
                       bhava_madhyas=madhyas, bhava_sandhis=sandhis, planets=planets, birth=birth)
    planets = {n: dataclasses.replace(p, combust_fraction=combustion.combust_fraction(n, chart))
               for n, p in planets.items()}
    return dataclasses.replace(chart, planets=planets)
```
> Guard: `primitives.combustion` imports only `chart.model` + `relationships` — no cycle with `adapter` (adapter imports primitives, primitives do not import adapter).

- [ ] **Step 4:** Run the full suite `py -3.12 -m pytest tests/raman_saab/ -q` → all PASS.

- [ ] **Step 5:** Commit: `feat(raman_saab): adapter populates graded combustion`

---

## Phase 1a done-when
- `py -3.12 -m pytest tests/raman_saab/ -q` green (Phase-0 tests + the new primitives tests).
- `relationships`, `dignity`, `combustion`, `sign_attributes`, `nakshatra`, `dispositor` importable and unit-tested.
- Adapter fills `combust_fraction`.
- No forbidden `app/core` import (the Phase-0 import guard still passes).

**Next plans:** Phase 1b — functional-nature (per-Lagna benefic/malefic, yogakaraka, kendradhipati-dosha), neecha-bhanga, parivartana, and the special points (Gulika/Mandi, Atmakaraka, Karakamsa, maraka points, balarishta). Phase 1c — GBB Shadbala (6 components in Rupas, ±1-rupa fixture), bhava-bala, ishta/kashta, and the sphutas (beeja/kshetra, special-dhana, sahams).
