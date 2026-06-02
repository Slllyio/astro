# Raman Saab — Phase 1b: Functional Nature, Bhangas, Special Points, Maraka & Balarishta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add the chart-relative "judgment-fact" primitives the Raman Saab condition predicates need beyond Phase 1a — per-Lagna **functional nature** (benefic/malefic/yogakaraka/kendradhipati-dosha), the **bhangas** (neecha-bhanga, parivartana/exchange, kemadruma + cancellations), the **special points** (Atmakaraka, Karakamsa, Arudha Lagna, Gulika/Mandi), the **maraka** point set, and the **balarishta** gate — then wire the new `RamanChart` fields (`upagrahas`, `arudha_lagna`, `karakamsa`, `maraka_points`, `balarishta`) into the adapter.

**Architecture:** Extends `app/raman_saab/primitives/` with five new pure-function modules (each a fact-computer over a `RamanChart`, no verdicts, no ephemeris) plus one ephemeris-touching `app/raman_saab/chart/upagrahas.py` (Gulika/Mandi need sunrise/sunset + ascendant-at-time, so they live in the `chart/` layer where `swisseph` is allowed). The adapter gains a third/fourth `dataclasses.replace` pass that fills the Phase-0 `Optional=None` fields. Everything stays inside the package — the Phase-0 import guard (no `app/core`, no global-ayanamsa mutation) must continue to pass.

**Tech Stack:** Python 3.12, frozen dataclasses, pytest (`py -3.12 -m pytest`). `swisseph` only in `chart/upagrahas.py`. No new dependencies.

**Scope:** Plan 1b of the Phase-1 group. **In scope:** `functional_nature`, `bhangas`, `special_points` (Atmakaraka/Karakamsa/Arudha), `chart/upagrahas` (Gulika/Mandi), `maraka`, `balarishta`, and adapter wiring. **Out of scope (Phase 1c):** GBB Shadbala, bhava-bala, ishta/kashta, sphutas (beeja/kshetra/special-dhana/sahams). Because Shadbala is 1c, anything needing planetary *strength* — `MarakaUnit.strength_rank`, the "weakest planet" tertiary maraka, and strength-based bhanga ranking — is **stubbed with a documented placeholder here and finalized in 1c**. Because the drishti engine (`doctrine/drishti.py`, nodes=7th) is Phase 2, bhanga/balarishta conditions that classically use *aspect* are implemented with the computable **conjunction** subset in this phase and explicitly flagged for aspect-refinement in Phase 2.

**Spec:** `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` (§4 model, §5.5 bhangas, §7 longevity/maraka) · **Predicate set:** `docs/raman_saab/predicate_audit.md` §7 (C4 functional, C5 neecha-bhanga, C6 parivartana, H11 Atmakaraka/Karakamsa) · **Doctrine + citations:** `docs/raman_saab/methodology/00_method_overview.md` §4 (functional table HTJAH-I:523-566), §5 (yoga karakas HTJAH-I:606-644), §8.1 (balarishta HPA-14), §8.2 (maraka HTJAH-I:776-814).

---

## Citation discipline (applies to every task)

Every doctrine constant (the functional table, the maraka per-Lagna list, each balarishta yoga/antidote, the neecha-bhanga conditions) carries an inline comment citing the **on-disk** source line in `data/knowledge_library/sources/...` using the `TAG:line` convention from the methodology overview §0 (e.g. `# HTJAH-I:523`). Where this plan supplies a starting value, the implementer **verifies it against the on-disk corpus** (grep the relevant chapter file) before committing, and corrects the citation to the real line number. If a supplied doctrine value cannot be located in the corpus, **STOP and surface it** (status `BLOCKED` / `DONE_WITH_CONCERNS`) rather than committing an uncited constant. This mirrors the spec §5.4 lock: *every doctrine assertion cites a real on-disk line.*

The canonical test chart for any "does it run end-to-end" adapter check is the repo baseline: **Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59, tz +5.5** (`BirthData("X",1990,7,15,12,0,5.5,12.97,77.59)`).

---

## File structure (created/modified in this plan)

| File | Responsibility | Ephemeris? |
|---|---|---|
| `app/raman_saab/primitives/functional_nature.py` | per-Lagna functional table (verbatim Raman) + `functional_nature`, `is_yogakaraka`, `kendradhipati_dosha`, `houses_owned` | no |
| `app/raman_saab/primitives/bhangas.py` | `neecha_bhanga`, `effective_dignity`, `exchange`, `parivartana`, `kemadruma`, `kemadruma_bhanga` | no |
| `app/raman_saab/primitives/special_points.py` | `atmakaraka`, `karakamsa`, `arudha_lagna` (pure) | no |
| `app/raman_saab/chart/upagrahas.py` | `gulika`, `mandi` (sunrise/sunset segment + ascendant-at-time) | **yes** |
| `app/raman_saab/primitives/maraka.py` | `maraka_points` (tiered lords/occupants/associates + 22nd-drekkana + 64th-navamsa) | no |
| `app/raman_saab/primitives/balarishta.py` | `balarishta` (infant-mortality yoga gate + antidotes) | no |
| `app/raman_saab/chart/adapter.py` | wire the 5 `Optional` fields (modify) | yes (existing) |
| `tests/raman_saab/primitives/test_functional_nature.py` … `test_balarishta.py` | paired tests | — |
| `tests/raman_saab/chart/test_upagrahas.py` | Gulika/Mandi unit + external pin | — |
| `tests/raman_saab/test_adapter.py` | add wiring assertions (modify) | — |

**Natural benefic/malefic sets (used across maraka & balarishta), per CLAUDE.md + overview:**
`NATURAL_BENEFICS = {"Jupiter","Venus","Mercury","Moon"}`, `NATURAL_MALEFICS = {"Sun","Mars","Saturn","Rahu","Ketu"}`. Define these once in `functional_nature.py` and import where needed (DRY).

---

## Task 1: Functional nature (per-Lagna benefic/malefic, yogakaraka, kendradhipati-dosha)

**Files:** Create `app/raman_saab/primitives/functional_nature.py`; Test `tests/raman_saab/primitives/test_functional_nature.py`

**Doctrine:** overview §4 (HTJAH-I:523-566 printed table + HTJAH-I:573-604 generating rules) and §5 (HTJAH-I:606-644 yoga karakas). The **printed table is the authority** (it embeds Raman's hand-tuned calls like Libra-Mars "feeble benefic" = neutral, which pure generating rules would miss). Raman printed all 7 visible planets for 9 of the 12 Lagnas; **3 cells are holes** (Aries-Moon, Gemini-Saturn, Aquarius-Saturn) — fill them via the generating rules and **flag for reviewer scrutiny** (see comments below). `is_yogakaraka`/`kendradhipati_dosha` are computed structurally from lordship (unambiguous) and cross-checked against the printed "best" markers.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import functional_nature as fn
from app.raman_saab.chart.model import RamanChart

def _chart(asc_lon: float) -> RamanChart:
    # one dummy planet so the chart is valid; functional_nature only needs asc_sign
    return RamanChart.from_stated_positions({"Sun": {"lon": 0.0, "bhava": 1}},
                                            asc_lon=asc_lon, ayanamsa="raman")

def test_printed_table_cells_verbatim():
    # Aries (asc_sign 1): Jupiter best benefic; Mercury worst malefic. HTJAH-I:523
    c = _chart(5.0)
    assert fn.functional_nature("Jupiter", c) == "benefic"
    assert fn.functional_nature("Mercury", c) == "malefic"
    # Libra (asc_sign 7): Mars is the printed NEUTRAL ("feeble benefic"). HTJAH-I:548
    c7 = _chart(7 * 30 + 5.0)
    assert fn.functional_nature("Saturn", c7) == "yogakaraka"   # Saturn is Libra's YK (overlay)
    assert fn.functional_nature("Sun", c7) == "malefic"

def test_yoga_karakas_only_mars_saturn_venus():
    # owns a kendra (other than 1st) AND a trikona (other than 1st) from the Lagna.
    assert fn.is_yogakaraka("Mars", 4) and fn.is_yogakaraka("Mars", 5)       # Cancer, Leo
    assert fn.is_yogakaraka("Saturn", 7) and fn.is_yogakaraka("Saturn", 2)   # Libra, Taurus
    assert fn.is_yogakaraka("Venus", 10) and fn.is_yogakaraka("Venus", 11)   # Cap, Aqu
    assert not fn.is_yogakaraka("Jupiter", 1)
    assert not fn.is_yogakaraka("Mars", 1)

def test_kendradhipati_dosha_for_benefic_kendra_lords():
    # Jupiter for Gemini (asc 3) owns the 7th & 10th (both kendras) -> dosha.
    assert fn.kendradhipati_dosha("Jupiter", 3) is True
    # Mars for Aries (asc 1) is a natural malefic -> no kendradhipati dosha.
    assert fn.kendradhipati_dosha("Mars", 1) is False

def test_houses_owned_from_lagna():
    assert fn.houses_owned("Saturn", 11) == [1, 12]   # Aquarius lagna: Saturn owns 1 & 12
    assert fn.houses_owned("Sun", 5) == [1]           # Leo lagna: Sun owns the 1st only
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from typing import Final, Literal
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS

Nature = Literal["benefic", "malefic", "neutral", "yogakaraka"]

NATURAL_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
NATURAL_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

_VISIBLE: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})

# B.V. Raman's per-Lagna functional classification — PRINTED TABLE is authoritative.
# Source: How to Judge a Horoscope Vol I, HTJAH-I:523-566 (overview §4).
# asc_sign 1..12 (Aries..Pisces) -> planet -> "benefic" | "malefic" | "neutral".
# 9 Lagnas print all 7 visible planets; 3 cells are HOLES Raman did not print
# (Aries-Moon, Gemini-Saturn, Aquarius-Saturn) — filled below via the generating
# rules (HTJAH-I:573-604) and MARKED for doctrine-reviewer scrutiny.
_FUNCTIONAL_TABLE: Final[dict[int, dict[str, str]]] = {
    1:  {"Jupiter": "benefic", "Mars": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Saturn": "malefic", "Venus": "malefic",
         "Moon": "neutral"},   # HOLE: Aries-Moon (4th lord, luminary) — REVIEW
    2:  {"Saturn": "benefic", "Mercury": "benefic", "Mars": "benefic", "Sun": "benefic",
         "Jupiter": "malefic", "Moon": "malefic", "Venus": "neutral"},
    3:  {"Venus": "benefic",
         "Mars": "malefic", "Jupiter": "malefic", "Sun": "malefic",
         "Moon": "neutral", "Mercury": "neutral",
         "Saturn": "neutral"},   # HOLE: Gemini-Saturn owns 8th(dusthana)+9th(trikona);
                                 # the 8th taint tempers the 9th -> neutral (Raman omitted). REVIEW.
    4:  {"Mars": "benefic", "Jupiter": "benefic",
         "Venus": "malefic", "Mercury": "malefic",
         "Saturn": "neutral", "Moon": "neutral", "Sun": "neutral"},
    5:  {"Mars": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Venus": "malefic",
         "Jupiter": "neutral", "Moon": "neutral", "Saturn": "neutral"},
    6:  {"Venus": "benefic",
         "Moon": "malefic", "Mars": "malefic", "Jupiter": "malefic",
         "Saturn": "neutral", "Sun": "neutral", "Mercury": "neutral"},
    7:  {"Saturn": "benefic", "Mercury": "benefic", "Venus": "benefic",
         "Sun": "malefic", "Jupiter": "malefic", "Moon": "malefic",
         "Mars": "neutral"},   # Libra-Mars "feeble benefic" -> NEUTRAL (HTJAH-I:548)
    8:  {"Moon": "benefic", "Jupiter": "benefic", "Sun": "benefic",
         "Mercury": "malefic", "Venus": "malefic",
         "Mars": "neutral", "Saturn": "neutral"},
    9:  {"Mars": "benefic", "Sun": "benefic",
         "Venus": "malefic", "Saturn": "malefic", "Mercury": "malefic",
         "Jupiter": "neutral", "Moon": "neutral"},
    10: {"Venus": "benefic", "Mercury": "benefic", "Saturn": "benefic",
         "Mars": "malefic", "Jupiter": "malefic", "Moon": "malefic",
         "Sun": "neutral"},
    11: {"Venus": "benefic", "Sun": "benefic", "Mars": "benefic",
         "Jupiter": "malefic", "Moon": "malefic", "Mercury": "neutral",
         "Saturn": "benefic"},  # HOLE: Aquarius-Saturn (lagna lord, owns 1st+12th) — REVIEW
    12: {"Moon": "benefic", "Mars": "benefic",
         "Saturn": "malefic", "Sun": "malefic", "Venus": "malefic", "Mercury": "malefic",
         "Jupiter": "neutral"},
}


def houses_owned(planet: str, asc_sign: int) -> list[int]:
    """Rasi-houses (1..12 from the Lagna) lorded by `planet`. Empty for Rahu/Ketu."""
    return sorted(((sign - asc_sign) % 12) + 1
                  for sign, lord in SIGN_LORDS.items() if lord == planet)


def is_yogakaraka(planet: str, asc_sign: int) -> bool:
    """A Raja-Yoga Karaka owns BOTH a kendra and a trikona other than the 1st
    (only Mars/Saturn/Venus can, for specific Lagnas). HTJAH-I:606."""
    hs = set(houses_owned(planet, asc_sign))
    return bool((hs & (_KENDRA - {1})) and (hs & (_TRIKONA - {1})))


def kendradhipati_dosha(planet: str, asc_sign: int) -> bool:
    """A NATURAL BENEFIC owning a kendra (4/7/10, not the 1st) acquires malefic
    tendency — Kendradhipati Dosha. HTJAH-I:582."""
    if planet not in NATURAL_BENEFICS:
        return False
    return bool(set(houses_owned(planet, asc_sign)) & {4, 7, 10})


def functional_nature(planet: str, chart: RamanChart) -> Nature:
    """Per-Lagna functional nature ∈ {benefic, malefic, neutral, yogakaraka}.
    Yoga-karaka overlays the printed table. Rahu/Ketu have no functional ownership
    nature (they act per dispositor/conjunction) -> 'neutral'."""
    if planet in ("Rahu", "Ketu"):
        return "neutral"
    if is_yogakaraka(planet, chart.asc_sign):
        return "yogakaraka"
    return _FUNCTIONAL_TABLE[chart.asc_sign][planet]  # type: ignore[return-value]
```
> **Hole values supplied** (flag in your completion summary for the doctrine reviewer): Aries-Moon=`neutral` (sole kendra-lord luminary; Raman's omission ⇒ unemphatic), Gemini-Saturn=`neutral` (owns 8th+9th — trikona benefic tempered by dusthana taint), Aquarius-Saturn=`benefic` (lagna-lord owning 1st+12th; 1st-lord-not-Moon ⇒ benefic). Each is the generating-rule result (HTJAH-I:573-604) for a cell Raman left unprinted; a doctrine reviewer confirmed Aries-Moon and Aquarius-Saturn and flagged Gemini-Saturn (now set to `neutral`). Re-verify against HTJAH-I:573-604 before committing.

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Verify the 84 printed cells against the on-disk `how_to_judge_a_horoscope_raman/` chapter (grep for the Lagna sections HTJAH-I:523-566); correct any cell that misreads Raman. Then commit: `feat(raman_saab): per-Lagna functional nature (table + yogakaraka + kendradhipati)`

---

## Task 2: Bhangas (neecha-bhanga, parivartana/exchange, kemadruma + cancellations)

**Files:** Create `app/raman_saab/primitives/bhangas.py`; Test `tests/raman_saab/primitives/test_bhangas.py`

**Doctrine:** spec §5.5; predicate audit C5 (`NeechaBhanga`/`EffectiveDignity`), C6 (`Parivartana`/`Exchange`). Neecha-bhanga conditions are the standard Raman/HPA "cancellation of debilitation" set; **aspect-based** conditions (dispositor aspecting the debilitated planet) are **deferred to Phase 2** (drishti engine) — this phase implements the kendra-, navamsa-, and conjunction-based conditions, which are computable now. Mark the deferral in a comment.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import bhangas as b
from app.raman_saab.chart.model import RamanChart

def _c(lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")

def test_exchange_and_parivartana():
    # Mars in Taurus(Venus-owned) + Venus in Aries(Mars-owned) -> exchange.
    c = _c({"Mars": 35.0, "Venus": 5.0})
    assert b.exchange("Mars", "Venus", c) is True
    # Aries lagna: 1st lord Mars in 2nd (Taurus), 2nd lord Venus in 1st (Aries) -> parivartana(1,2).
    assert b.parivartana(1, 2, c) is True
    assert b.parivartana(1, 3, c) is False

def test_neecha_bhanga_dispositor_in_kendra():
    # Sun debilitated in Libra (190). Dispositor Venus in Capricorn (280) = the 10th
    # house (a kendra) from Aries lagna (asc_lon 0) -> cancellation.
    c = _c({"Sun": 190.0, "Venus": 280.0})
    assert b.neecha_bhanga("Sun", c) is True
    assert b.effective_dignity("Sun", c) == "neecha_bhanga"

def test_no_neecha_bhanga_when_not_debilitated():
    c = _c({"Sun": 10.0})            # exalted, not debilitated
    assert b.neecha_bhanga("Sun", c) is False
    assert b.effective_dignity("Sun", c) == "exalt"

def test_kemadruma_moon_isolated():
    # Moon alone, nothing in 2nd/12th from Moon, nothing with it (Sun excluded) -> kemadruma.
    c = _c({"Moon": 100.0})
    assert b.kemadruma(c) is True
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives.dignity import dignity

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
# Planet exalted in each sign (inverse of relationships.EXALTATION), for neecha-bhanga cond 2.
_EXALTED_IN_SIGN: Final[dict[int, str]] = {sign: p for p, (sign, _deg) in r.EXALTATION.items()}


def _in_kendra_from(planet: str, ref_house: int, chart: RamanChart) -> bool:
    """Is `planet` in a kendra (1/4/7/10) counted from rasi-house `ref_house`?"""
    if planet not in chart.planets:
        return False
    dist = ((chart.planets[planet].rasi_house - ref_house) % 12) + 1
    return dist in _KENDRA


def exchange(a: str, b_: str, chart: RamanChart) -> bool:
    """Parivartana between two planets: each occupies a sign owned by the other."""
    if a not in chart.planets or b_ not in chart.planets:
        return False
    return (SIGN_LORDS[chart.planets[a].sign] == b_ and
            SIGN_LORDS[chart.planets[b_].sign] == a)


def parivartana(h1: int, h2: int, chart: RamanChart) -> bool:
    """Exchange between the LORDS of houses h1 and h2 (rasi-house lords from the Lagna)."""
    lord1 = SIGN_LORDS[((chart.asc_sign - 1) + (h1 - 1)) % 12 + 1]
    lord2 = SIGN_LORDS[((chart.asc_sign - 1) + (h2 - 1)) % 12 + 1]
    if lord1 == lord2 or lord1 not in chart.planets or lord2 not in chart.planets:
        return False
    return (chart.planets[lord1].rasi_house == h2 and
            chart.planets[lord2].rasi_house == h1)


def neecha_bhanga(planet: str, chart: RamanChart) -> bool:
    """Cancellation of debilitation. Computable Raman/HPA conditions (cite HPA
    cancellation passage). Aspect-by-dispositor is DEFERRED to Phase 2 (drishti)."""
    if planet in ("Rahu", "Ketu") or planet not in chart.planets:
        return False
    if dignity(planet, chart) != "debil":
        return False
    p = chart.planets[planet]
    lagna_h, moon_h = 1, chart.planets["Moon"].rasi_house if "Moon" in chart.planets else 1
    dispositor = SIGN_LORDS[p.sign]                      # lord of the debilitation sign
    exalted_here = _EXALTED_IN_SIGN.get(p.sign)          # planet exalted in that sign
    # (1) dispositor in a kendra from Lagna or Moon
    if _in_kendra_from(dispositor, lagna_h, chart) or _in_kendra_from(dispositor, moon_h, chart):
        return True
    # (2) the planet exalted in this sign is in a kendra from Lagna or Moon
    if exalted_here and (_in_kendra_from(exalted_here, lagna_h, chart)
                         or _in_kendra_from(exalted_here, moon_h, chart)):
        return True
    # (3) conjunct its dispositor (same rasi-house)  [aspect variant -> Phase 2]
    if dispositor in chart.planets and chart.planets[dispositor].rasi_house == p.rasi_house:
        return True
    # (4) exalted in navamsa, or vargottama
    if p.vargottama or p.navamsa_sign == r.EXALTATION[planet][0]:
        return True
    return False


def effective_dignity(planet: str, chart: RamanChart) -> str:
    """Dignity with neecha-bhanga applied: a cancelled debilitation reports
    'neecha_bhanga' rather than 'debil'."""
    d = dignity(planet, chart)
    if d == "debil" and neecha_bhanga(planet, chart):
        return "neecha_bhanga"
    return d


def kemadruma(chart: RamanChart) -> bool:
    """Kemadruma: the Moon has no planet (excluding Sun & nodes) in the 2nd or 12th
    from it and none conjunct it. HPA (cite). NOTE: refine with aspect in Phase 2."""
    if "Moon" not in chart.planets:
        return False
    mh = chart.planets["Moon"].rasi_house
    neighbours = {(mh % 12) + 1, ((mh - 2) % 12) + 1, mh}   # 2nd, 12th, conjunct
    for name, pl in chart.planets.items():
        if name in ("Moon", "Sun", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in neighbours:
            return False
    return True


def kemadruma_bhanga(chart: RamanChart) -> bool:
    """Kemadruma cancellation (computable subset): a planet other than the Moon in a
    kendra from the Lagna, or the Moon itself in a kendra from the Lagna. HPA (cite)."""
    if "Moon" not in chart.planets:
        return False
    if chart.planets["Moon"].rasi_house in _KENDRA:
        return True
    for name, pl in chart.planets.items():
        if name in ("Moon", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in _KENDRA:
            return True
    return False
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Grep the on-disk corpus for the neecha-bhanga / kemadruma passages (HPA + HTJAH) and replace the `(cite ...)` placeholders with real `TAG:line` citations. Commit: `feat(raman_saab): bhangas — neecha-bhanga, parivartana/exchange, kemadruma`

---

## Task 3: Special points (Atmakaraka, Karakamsa, Arudha Lagna — pure)

**Files:** Create `app/raman_saab/primitives/special_points.py`; Test `tests/raman_saab/primitives/test_special_points.py`

**Doctrine:** CLAUDE.md (**strict 7-karaka Atmakaraka, NO Rahu/Ketu** — AK = highest degree-within-sign among Sun..Saturn); Karakamsa = the AK's navamsa sign treated as a point (predicate audit H11); Arudha Lagna = Jaimini pada of the Lagna with the 1st/7th → 10th exception. All three are **degree/lordship arithmetic — no ephemeris**. Returns `SpecialPoint(name, lon, sign, bhava, navamsa_sign)` for Karakamsa/Arudha; `atmakaraka` returns the planet name.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives import special_points as sp
from app.raman_saab.chart.model import RamanChart

def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")

def test_atmakaraka_highest_degree_in_sign_seven_planets_only():
    # Saturn at 28° in sign beats all; Rahu at 29° must be IGNORED (chayagraha).
    c = _c({"Sun": 5.0, "Moon": 12.0, "Mars": 20.0, "Mercury": 3.0,
            "Jupiter": 18.0, "Venus": 25.0, "Saturn": 28.0, "Rahu": 29.0, "Ketu": 209.0})
    assert sp.atmakaraka(c) == "Saturn"

def test_karakamsa_is_ak_navamsa_sign():
    c = _c({"Sun": 5.0, "Moon": 12.0, "Mars": 20.0, "Mercury": 3.0,
            "Jupiter": 18.0, "Venus": 25.0, "Saturn": 28.0})
    ak = sp.atmakaraka(c)
    km = sp.karakamsa(c)
    assert km.name == "Karakamsa"
    assert km.sign == c.planets[ak].navamsa_sign

def test_arudha_lagna_exception_to_tenth():
    # Aries lagna, lagna-lord Mars in the 1st -> raw Arudha = 1st -> exception -> 10th (Capricorn=10).
    c = _c({"Mars": 5.0}, asc_lon=0.0)
    assert sp.arudha_lagna(c).sign == 10
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.model import RamanChart, SpecialPoint
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart import varga

_SEVEN: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def atmakaraka(chart: RamanChart) -> str:
    """Strict 7-karaka Jaimini Atmakaraka: the planet with the highest degree-within-sign
    among the 7 visible planets. Rahu/Ketu are chayagrahas and CANNOT be AK (CLAUDE.md)."""
    present = [p for p in _SEVEN if p in chart.planets]
    return max(present, key=lambda p: chart.planets[p].lon % 30.0)


def karakamsa(chart: RamanChart) -> SpecialPoint:
    """Karakamsa = the Atmakaraka's navamsa sign, as a point (judged as a lagna in D9)."""
    ak = chart.planets[atmakaraka(chart)]
    sign = ak.navamsa_sign
    bhava = ((sign - chart.asc_sign) % 12) + 1     # rasi-house of the karakamsa sign
    return SpecialPoint(name="Karakamsa", lon=ak.lon, sign=sign, bhava=bhava,
                        navamsa_sign=sign)


def arudha_lagna(chart: RamanChart) -> SpecialPoint:
    """Jaimini Arudha (Pada) Lagna: count from the lagna-lord as many signs as it is
    from the Lagna; if the result falls in the 1st or 7th, take the 10th from there."""
    asc = chart.asc_sign
    lord = SIGN_LORDS[asc]
    lord_house = chart.planets[lord].rasi_house if lord in chart.planets else 1
    lord_sign = ((asc - 1) + (lord_house - 1)) % 12 + 1
    a = ((lord_sign - 1) + (lord_house - 1)) % 12 + 1
    rel = ((a - asc) % 12) + 1
    if rel in (1, 7):                               # Jaimini exception
        a = ((a - 1) + 9) % 12 + 1
    bhava = ((a - asc) % 12) + 1
    return SpecialPoint(name="ArudhaLagna", lon=float((a - 1) * 30), sign=a, bhava=bhava,
                        navamsa_sign=varga.navamsa_sign(float((a - 1) * 30)))
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): special points — Atmakaraka (7-karaka), Karakamsa, Arudha Lagna`

---

## Task 4: Gulika & Mandi (upagrahas — ephemeris layer)

**Files:** Create `app/raman_saab/chart/upagrahas.py`; Test `tests/raman_saab/chart/test_upagrahas.py` (+ `tests/raman_saab/chart/__init__.py` if absent)

**Doctrine:** HPA (Gulika/Mandi computation). The day (sunrise→sunset) and night (sunset→next sunrise) are each divided into **8 parts**; parts are ruled cyclically by the weekday lords; **Gulika = the ascendant rising at the START of Saturn's part**. **Mandi = the ascendant at the END of Saturn's part** (= start of the next part) — *traditions differ on start/end; this is the convention to pin against an external source and adjust if it fails.* This is the **only ephemeris-touching module in this plan** — it lives in `chart/` (where `swisseph` is allowed) and is computed **inside the `sidereal_mode(ayanamsa)` context**, never mutating the global ayanamsa. `from_stated_positions` charts have no ephemeris → upagrahas are `None` there.

> **Risk note (read before coding):** this is the highest-risk task. Sunrise/sunset (`swe.rise_trans`) signature and the weekday→part ordering have convention pitfalls. Verify the Gulika SIGN for the canonical Bangalore chart against **drikpanchang.com / Jagannatha Hora** (test-pinning policy) before committing. If the external value disagrees, adjust (a) start-vs-end convention, (b) day-vs-night sequence offset, in that order, and re-pin. If you cannot reconcile within reason, commit the computation **with the pin test `xfail`-marked and a written note**, and surface `DONE_WITH_CONCERNS` — do NOT silently ship an unpinned upagraha.

- [ ] **Step 1: Write the failing test**
```python
import pytest
from app.raman_saab.chart.adapter import cast_chart   # only to get a real jd/birth
from app.raman_saab.chart.model import BirthData
from app.raman_saab.chart import upagrahas as u

_BLR = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

def test_gulika_mandi_return_points_in_valid_signs():
    g = u.gulika(_BLR, ayanamsa="raman")
    m = u.mandi(_BLR, ayanamsa="raman")
    assert g.name == "Gulika" and 1 <= g.sign <= 12 and 0.0 <= g.lon < 360.0
    assert m.name == "Mandi" and 1 <= m.sign <= 12

@pytest.mark.external_pin
def test_gulika_sign_matches_reference():
    # PIN: replace EXPECTED with drikpanchang/JH Gulika sign for the Bangalore baseline.
    g = u.gulika(_BLR, ayanamsa="raman")
    EXPECTED_SIGN = None   # <-- implementer fills from external source, then asserts
    if EXPECTED_SIGN is not None:
        assert g.sign == EXPECTED_SIGN
```

- [ ] **Step 2:** Run → FAIL (module missing).

- [ ] **Step 3: Implement** (verify the `rise_trans` return shape live for the installed pyswisseph before trusting it)
```python
from __future__ import annotations
import swisseph as swe
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.model import BirthData, SpecialPoint
from app.raman_saab.chart import varga

# Weekday lord order, index 0=Sunday .. 6=Saturday.
_WEEKDAY_LORDS: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_SAT_IDX = 6   # Saturn's index in _WEEKDAY_LORDS


def _jd_ut(b: BirthData) -> float:
    return swe.julday(b.year, b.month, b.day, (b.hour + b.minute / 60.0) - b.tz_offset, swe.GREG_CAL)


def _weekday(jd_local_noon: float) -> int:
    """0=Sunday..6=Saturday for the civil date (use local noon JD to avoid edge slips)."""
    return int((jd_local_noon + 1.5) % 7)   # JD 0 = Monday noon convention -> calibrate in test


def _rise_set(jd: float, b: BirthData, rsmi: int) -> float:
    # VERIFIED LIVE (pyswisseph 2.10.03): signature is
    #   rise_trans(tjd_ut, body, rsmi, geopos, atpress=0.0, attemp=0.0, flags=...)
    # i.e. rsmi comes BEFORE geopos (both positional); returns (retflag, tret) with tret[0]=JD.
    geopos = (b.longitude, b.latitude, 0.0)
    ret, tret = swe.rise_trans(jd - 1.0, swe.SUN, rsmi, geopos, 0.0, 0.0, swe.FLG_SWIEPH)
    return float(tret[0])


def _ascendant(jd: float, b: BirthData) -> float:
    cusp, ascmc = swe.houses_ex(jd, b.latitude, b.longitude, b"O", swe.FLG_SIDEREAL)
    return float(ascmc[0]) % 360.0


def _saturn_part_bounds(b: BirthData, ayanamsa: str) -> tuple[float, float]:
    """Return (start_jd, end_jd) of Saturn's 1/8 part of the relevant day/night span."""
    jd = _jd_ut(b)
    with sidereal_mode(ayanamsa):
        sunrise = _rise_set(jd, b, swe.CALC_RISE | swe.BIT_DISC_CENTER)
        sunset = _rise_set(jd, b, swe.CALC_SET | swe.BIT_DISC_CENTER)
        is_day = sunrise <= jd < sunset
        wd = _weekday(jd)
        if is_day:
            span0, span1 = sunrise, sunset
            seq_start = wd                                 # day: parts start from weekday lord
        else:
            next_sunrise = _rise_set(jd + 1.0, b, swe.CALC_RISE | swe.BIT_DISC_CENTER)
            span0 = sunset if jd >= sunset else _rise_set(jd - 1.0, b, swe.CALC_SET | swe.BIT_DISC_CENTER)
            span1 = next_sunrise if jd >= sunset else sunrise
            seq_start = (wd + 5) % 7                       # night: start from lord of the 5th weekday
        part = (span1 - span0) / 8.0
        # index i where Saturn rules: lord[(seq_start + i) % 7] == Saturn
        i = (_SAT_IDX - seq_start) % 7
        return span0 + i * part, span0 + (i + 1) * part


def _point(name: str, jd: float, b: BirthData, ayanamsa: str) -> SpecialPoint:
    with sidereal_mode(ayanamsa):
        lon = _ascendant(jd, b)
    sign = int(lon // 30) + 1
    return SpecialPoint(name=name, lon=lon, sign=sign, bhava=sign,
                        navamsa_sign=varga.navamsa_sign(lon))


def gulika(birth: BirthData, *, ayanamsa: str = "raman") -> SpecialPoint:
    """Ascendant at the START of Saturn's eighth-part (Gulika Kala)."""
    start, _end = _saturn_part_bounds(birth, ayanamsa)
    return _point("Gulika", start, birth, ayanamsa)


def mandi(birth: BirthData, *, ayanamsa: str = "raman") -> SpecialPoint:
    """Ascendant at the END of Saturn's eighth-part (convention: pin & adjust)."""
    _start, end = _saturn_part_bounds(birth, ayanamsa)
    return _point("Mandi", end, birth, ayanamsa)
```
> The `rise_trans` signature above was confirmed live on the installed pyswisseph 2.10.03: `rise_trans(tjd_ut, body, rsmi, geopos, atpress=0.0, attemp=0.0, flags=...)` returning `(retflag, tret)` with `tret[0]` = JD. Still **calibrate `_weekday`** so the Bangalore baseline (1990-07-15 = a **Sunday**) returns `0` (adjust the `+1.5` constant / use `swe.day_of_week` if needed), and remember `rsmi` flags are `swe.CALC_RISE`/`swe.CALC_SET` OR'd with `swe.BIT_DISC_CENTER`.

- [ ] **Step 4:** Run → PASS (the structural test). Then do the external pin (Step in the risk note).
- [ ] **Step 5:** Commit: `feat(raman_saab): Gulika & Mandi upagrahas (sunrise-segment, ayanamsa-isolated)`

---

## Task 5: Maraka points (tiered + 22nd-drekkana + 64th-navamsa)

**Files:** Create `app/raman_saab/primitives/maraka.py`; Test `tests/raman_saab/primitives/test_maraka.py`

**Doctrine:** overview §8.2 (HTJAH-I:776-814). Death houses = **2nd & 7th**. Tiers: **primary** = lords of 2/7 + malefic occupants of 2/7 + malefic associates of those lords; **secondary** = benefics with 2/7 lords + lords of 3/8 + 3rd/8th lord associated with a 2/7 lord; **tertiary** = Saturn touching any maraka + lord of 6/8 + the weakest planet. `MarakaUnit.strength_rank` and the **weakest-planet** tertiary need Shadbala → **deferred to Phase 1c** (rank stubbed `0`; weakest-planet omitted with a comment). "Associate" = **conjunct** (same rasi-house) here; aspect-association → Phase 2. **The two named death-points (HTJAH-II:4540,:4544):** the **22nd drekkana from the LAGNA** (offset **+22**, pinned live to Raman's printed example 27° Aquarius → 1st-of-Libra → Venus, HTJAH-II:3692-3695) and the **64th navamsa from the MOON** (HTJAH-II:4544 — *not* the Lagna; offset +63, external-pin to confirm). Both formulae were verified live before this plan was written.

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives.maraka import maraka_points
from app.raman_saab.chart.model import RamanChart

def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")

def test_22nd_drekkana_lord_pins_ramans_printed_example():
    # Raman HTJAH-II:3692-3695: Lagna 27° Aquarius -> lagna drekkana = 3rd of Aquarius;
    # the 22nd drekkana from this = 1st drekkana of Libra -> lord Venus.
    c = _c({"Moon": 0.0}, asc_lon=10 * 30 + 27.0)   # 27° Aquarius
    assert maraka_points(c).drekkana22_lord == "Venus"

def test_64th_navamsa_lord_is_reckoned_from_the_moon():
    # HTJAH-II:4544: "the lord of the 64th Navamsa occupied by the Moon" -> from the MOON.
    # Structural: a valid sign-lord; and it MUST change when only the Moon moves.
    c1 = _c({"Moon": 5.0}, asc_lon=0.0)
    c2 = _c({"Moon": 100.0}, asc_lon=0.0)           # same lagna, different Moon
    from app.raman_saab.chart.constants import SIGN_LORDS
    assert maraka_points(c1).navamsa64_lord in SIGN_LORDS.values()
    assert maraka_points(c1).navamsa64_lord != maraka_points(c2).navamsa64_lord

def test_second_and_seventh_lords_are_primary_marakas():
    # Aries lagna: 2nd lord = Venus (Taurus), 7th lord = Venus (Libra) -> Venus primary.
    c = _c({"Venus": 35.0, "Moon": 0.0}, asc_lon=0.0)
    mp = maraka_points(c)
    grahas = {u.graha for u in mp.units if u.tier == "primary"}
    assert "Venus" in grahas
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from app.raman_saab.chart.model import RamanChart, MarakaUnit, MarakaPoints
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS, NATURAL_BENEFICS


def _lord_of(house: int, asc_sign: int) -> str:
    return SIGN_LORDS[((asc_sign - 1) + (house - 1)) % 12 + 1]


def _occupants(house: int, chart: RamanChart) -> list[str]:
    return [n for n, p in chart.planets.items() if p.rasi_house == house]


def _drekkana22_lord(asc_lon: float) -> str:
    """Lord of the 22nd drekkana reckoned from the LAGNA drekkana (HTJAH-II:3692-3695).
    Offset is +22 in the 36-decanate cycle, PINNED to Raman's printed worked example:
    Lagna 27° Aquarius (3rd of Aquarius) -> 22nd drekkana = 1st of Libra -> Venus.
    (The textbook '8th-house decanate' derivation gives +21; Raman's printed example is
    +22 and is the authority here — see the pin test. His example's LORD is Venus under
    BOTH offsets, so the pin is robust.)"""
    g = (int(asc_lon // 30) * 3 + int((asc_lon % 30) // 10) + 22) % 36
    sign = ((g // 3 + (g % 3) * 4) % 12) + 1
    return SIGN_LORDS[sign]


def _navamsa64_lord(chart: RamanChart) -> str:
    """Lord of the 64th Navamsa reckoned from the MOON (HTJAH-II:4544: 'the lord of the
    64th Navamsa occupied by the Moon'). Offset +63 (Moon's navamsa counted as the 1st)
    is the textbook default; no Raman worked example disambiguates +63 vs +64, so an
    EXTERNAL PIN (Jagannatha Hora / drikpanchang for the canonical chart) must confirm it
    before this maraka point is trusted at Phase-4 death-timing. Falls back to the Lagna
    only if the Moon is absent (sparse Track-B charts)."""
    ref_lon = chart.planets["Moon"].lon if "Moon" in chart.planets else chart.asc_lon
    g = (int(ref_lon // (30 / 9)) + 63) % 108
    return SIGN_LORDS[(g % 12) + 1]


def maraka_points(chart: RamanChart) -> MarakaPoints:
    """Tiered maraka set per HTJAH-I:776-814 (overview §8.2). strength_rank and the
    weakest-planet tertiary are filled in Phase 1c (Shadbala); associate=conjunct here."""
    asc = chart.asc_sign
    seen: dict[str, str] = {}                      # graha -> first (strongest) tier assigned

    def add(graha: str, tier: str) -> None:
        if graha in ("Rahu", "Ketu"):
            return
        seen.setdefault(graha, tier)

    l2, l7 = _lord_of(2, asc), _lord_of(7, asc)
    l3, l8, l6 = _lord_of(3, asc), _lord_of(8, asc), _lord_of(6, asc)
    death_lords = {l2, l7}
    death_lord_houses = {chart.planets[l].rasi_house for l in death_lords if l in chart.planets}

    # primary
    add(l2, "primary"); add(l7, "primary")
    for h in (2, 7):
        for occ in _occupants(h, chart):
            if occ in NATURAL_MALEFICS:
                add(occ, "primary")
    for n, p in chart.planets.items():             # malefic associates (conjunct) of 2/7 lords
        if n in NATURAL_MALEFICS and p.rasi_house in death_lord_houses:
            add(n, "primary")

    # secondary
    for n, p in chart.planets.items():
        if n in NATURAL_BENEFICS and p.rasi_house in death_lord_houses:
            add(n, "secondary")
    add(l3, "secondary"); add(l8, "secondary")

    # tertiary
    if "Saturn" in chart.planets and chart.planets["Saturn"].rasi_house in death_lord_houses:
        add("Saturn", "tertiary")
    add(l6, "tertiary"); add(l8, "tertiary")
    # NOTE: "weakest planet in the chart" tertiary maraka -> Phase 1c (needs Shadbala).

    units = tuple(MarakaUnit(graha=g, tier=t, strength_rank=0)   # rank -> Phase 1c
                  for g, t in seen.items())
    return MarakaPoints(units=units,
                        drekkana22_lord=_drekkana22_lord(chart.asc_lon),
                        navamsa64_lord=_navamsa64_lord(chart))
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): maraka points — tiered marakas + 22nd-drekkana + 64th-navamsa`

---

## Task 6: Balarishta gate (infant-mortality yogas + antidotes)

**Files:** Create `app/raman_saab/primitives/balarishta.py`; Test `tests/raman_saab/primitives/test_balarishta.py`

**Doctrine:** overview §8.1 + **Raman's verbatim HPA-14 lists** (read into this plan). The 8 balarishta yogas are at HPA-14:90-115; the 10 antidotes at HPA-14:232-266. Implement a **faithful CITED subset** of the cleanly-computable yogas + antidotes, returning `BalarishtaState(applies, cancelled, reasons)`. Aspect-based yogas use the **conjunction** subset now (drishti → Phase 2); the full set is validated by the Phase-4 longevity goldens. **Every yoga/antidote below is a real HPA-14 line — keep the citations exact.** Note the corrected facts from the corpus: Raman's Moon-affliction balarishta house set is **7/8/12** (HPA-14:96-98), NOT 6/8/12; and there is **NO "malefics in upachaya" antidote** in Raman's list (it was dropped after a doctrine audit).

- [ ] **Step 1: Write the failing test**
```python
from app.raman_saab.primitives.balarishta import balarishta
from app.raman_saab.chart.model import RamanChart

def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")

def test_moon_in_7_8_12_with_malefic_triggers_balarishta():
    # Raman HPA-14:96-98: Moon in the 7th/8th/12th with malefics. Moon in 8th (Scorpio 220)
    # conjoined Saturn, no benefic with the Moon -> applies, not cancelled.
    c = _c({"Moon": 220.0, "Saturn": 225.0}, asc_lon=0.0)
    st = balarishta(c)
    assert st.applies is True
    assert any("moon_7_8_12_malefic" in r for r in st.reasons)

def test_jupiter_in_lagna_cancels():
    # Raman HPA-14:232: Jupiter in the ascendant removes Balarishta.
    c = _c({"Moon": 220.0, "Saturn": 225.0, "Jupiter": 5.0}, asc_lon=0.0)   # Jupiter in 1st
    st = balarishta(c)
    assert st.applies is True and st.cancelled is True
    assert any("jupiter_in_lagna" in r for r in st.reasons)

def test_clean_chart_no_balarishta():
    c = _c({"Moon": 100.0, "Jupiter": 100.0}, asc_lon=0.0)   # Moon in 4th, no malefic with it
    assert balarishta(c).applies is False
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement**
```python
from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart, BalarishtaState
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS
from app.raman_saab.primitives.dignity import dignity

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})
# Raman's Moon-affliction balarishta house set is the 7th/8th/12th (HPA-14:96-98) — NOT 6/8/12.
_BALA_MOON_HOUSES: Final[frozenset[int]] = frozenset({7, 8, 12})


def _conjunct_malefic(house: int, chart: RamanChart) -> bool:
    return any(n in NATURAL_MALEFICS and p.rasi_house == house
               for n, p in chart.planets.items())


def _has_benefic_with_moon(chart: RamanChart) -> bool:
    mh = chart.planets["Moon"].rasi_house
    return any(n in NATURAL_BENEFICS and n != "Moon" and p.rasi_house == mh
               for n, p in chart.planets.items())


def balarishta(chart: RamanChart) -> BalarishtaState:
    """Infant-mortality gate. Verbatim Raman HPA-14 yogas (:90-115) + antidotes (:232-266),
    conjunction-based v1 (aspect refines in Phase 2). Returns which yogas/antidotes fired
    so the longevity judge (Phase 4) can gate the houses."""
    if "Moon" not in chart.planets:
        return BalarishtaState(applies=False, cancelled=False, reasons=())
    moon = chart.planets["Moon"]
    reasons: list[str] = []

    # --- balarishta yogas (Raman HPA-14) ---
    # (2) Moon in a kendra (quadrant) with malefics.                       HPA-14:93
    if moon.rasi_house in _KENDRA and _conjunct_malefic(moon.rasi_house, chart):
        reasons.append("moon_kendra_malefic")
    # (3) Moon in the 7th/8th/12th with malefics, no benefic with it.      HPA-14:96
    if moon.rasi_house in _BALA_MOON_HOUSES and _conjunct_malefic(moon.rasi_house, chart) \
            and not _has_benefic_with_moon(chart):
        reasons.append("moon_7_8_12_malefic")
    # (7) Moon in the ascendant, Mars in the 8th, Sun in the 9th,
    #     Saturn in the 12th (a precise low-false-positive yoga).          HPA-14:111
    if (moon.rasi_house == 1
            and any(n == "Mars" and p.rasi_house == 8 for n, p in chart.planets.items())
            and any(n == "Sun" and p.rasi_house == 9 for n, p in chart.planets.items())
            and any(n == "Saturn" and p.rasi_house == 12 for n, p in chart.planets.items())):
        reasons.append("moon_lagna_mars8_sun9_sat12")

    applies = bool(reasons)

    # --- antidotes / bhangas (Raman HPA-14) ---
    cancel_reasons: list[str] = []
    if applies:
        # (1) Jupiter powerfully posited in the ascendant.                 HPA-14:232
        if "Jupiter" in chart.planets and chart.planets["Jupiter"].rasi_house == 1:
            cancel_reasons.append("jupiter_in_lagna")
        # (2) the lord of the lagna powerfully situated.                   HPA-14:235
        #     ("powerfully" = full Shadbala -> Phase 1c; v1 proxy: lagna lord in a
        #      kendra/trikona, or in exalt/own/moolatrikona dignity.)
        lagna_lord = SIGN_LORDS[chart.asc_sign]
        if lagna_lord in chart.planets:
            ll = chart.planets[lagna_lord]
            if ll.rasi_house in (_KENDRA | _TRIKONA) or \
                    dignity(lagna_lord, chart) in ("exalt", "own", "moolatrikona"):
                cancel_reasons.append("strong_lagna_lord")
        # (9) Full Moon aspects lagna with Jupiter in quadrants -> v1 proxy:
        #     a natural benefic (esp. Jupiter) in a kendra from the lagna. HPA-14:263
        if any(n in NATURAL_BENEFICS and n != "Moon" and p.rasi_house in _KENDRA
               for n, p in chart.planets.items()):
            cancel_reasons.append("benefic_in_kendra")

    return BalarishtaState(applies=applies, cancelled=bool(cancel_reasons),
                           reasons=tuple(reasons + cancel_reasons))
```

- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Confirm each cited HPA-14 line still matches the on-disk corpus (the line numbers in the comments were read directly from `hindu_predictive_astrology_raman/chapter_014_ayurdaya-or-longevity.md`; re-grep to be safe). Commit: `feat(raman_saab): balarishta gate (infant-mortality yogas + antidotes)`

---

## Task 7: Wire the pure special points / maraka / balarishta into the adapter

**Files:** Modify `app/raman_saab/chart/adapter.py`; Test `tests/raman_saab/test_adapter.py` (add cases)

These five fields are all **pure functions of the finished chart** (no extra ephemeris): `karakamsa`, `arudha_lagna`, `maraka_points`, `balarishta`. Compute them after the combustion pass via a final `dataclasses.replace`. (`upagrahas` is wired in Task 8 because it needs the ephemeris.)

- [ ] **Step 1: Write the failing test** (append to `test_adapter.py`)
```python
def test_adapter_populates_pure_special_fields():
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.primitives.special_points import atmakaraka
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    assert chart.karakamsa is not None and chart.karakamsa.name == "Karakamsa"
    assert chart.karakamsa.sign == chart.planets[atmakaraka(chart)].navamsa_sign
    assert chart.arudha_lagna is not None and chart.arudha_lagna.name == "ArudhaLagna"
    assert chart.maraka_points is not None and len(chart.maraka_points.units) >= 1
    assert chart.balarishta is not None and isinstance(chart.balarishta.applies, bool)
```

- [ ] **Step 2:** Run → FAIL (fields are `None`).

- [ ] **Step 3: Implement** — in `adapter.py`, after the combustion `replace`, add the special-field pass. Add imports `from app.raman_saab.primitives import special_points, maraka, balarishta as balarishta_mod`. Replace the final `return`:
```python
    chart = dataclasses.replace(chart, planets=planets)   # (existing combustion result)
    return dataclasses.replace(
        chart,
        karakamsa=special_points.karakamsa(chart),
        arudha_lagna=special_points.arudha_lagna(chart),
        maraka_points=maraka.maraka_points(chart),
        balarishta=balarishta_mod.balarishta(chart),
    )
```
> No import cycle: adapter→primitives only; primitives never import adapter. The Phase-0 import guard still passes (no `app/core`).

- [ ] **Step 4:** Run `py -3.12 -m pytest tests/raman_saab/ -q` → all PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): adapter wires karakamsa, arudha, maraka, balarishta`

---

## Task 8: Wire Gulika/Mandi (upagrahas) into the adapter

**Files:** Modify `app/raman_saab/chart/adapter.py`; Test `tests/raman_saab/test_adapter.py`

`upagrahas` need the ephemeris (sunrise/ascendant-at-time), so they are computed from `birth` via `chart/upagrahas.py` and attached only for ephemeris-cast charts (`from_stated_positions` leaves them `None`).

- [ ] **Step 1: Write the failing test** (append)
```python
def test_adapter_populates_upagrahas():
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    assert chart.upagrahas is not None
    assert set(chart.upagrahas) == {"Gulika", "Mandi"}
    assert 1 <= chart.upagrahas["Gulika"].sign <= 12
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: Implement** — add `from app.raman_saab.chart import upagrahas as upagrahas_mod`; compute before the final `replace` and include in it:
```python
    ug = {"Gulika": upagrahas_mod.gulika(birth, ayanamsa=ayanamsa),
          "Mandi": upagrahas_mod.mandi(birth, ayanamsa=ayanamsa)}
    return dataclasses.replace(
        chart,
        upagrahas=ug,
        karakamsa=special_points.karakamsa(chart),
        arudha_lagna=special_points.arudha_lagna(chart),
        maraka_points=maraka.maraka_points(chart),
        balarishta=balarishta_mod.balarishta(chart),
    )
```

- [ ] **Step 4:** Run the full suite → all PASS.
- [ ] **Step 5:** Commit: `feat(raman_saab): adapter wires Gulika/Mandi upagrahas`

---

## Phase 1b done-when

- `py -3.12 -m pytest tests/raman_saab/ -q` green (Phase-0 + Phase-1a + the new Phase-1b tests).
- New importable, unit-tested primitives: `functional_nature`, `bhangas`, `special_points`, `maraka`, `balarishta`, and `chart/upagrahas`.
- `cast_chart` fills **all five** previously-`Optional=None` fields: `upagrahas`, `arudha_lagna`, `karakamsa`, `maraka_points`, `balarishta`.
- Import guard (`tests/raman_saab/test_import_guard.py`) still passes — no `app/core`, no global-ayanamsa mutation.
- Every doctrine constant cites a real on-disk corpus line (functional table, maraka list, balarishta yogas, neecha-bhanga/kemadruma).
- **Documented deferrals (carry to 1c):** `MarakaUnit.strength_rank` (=0 stub), weakest-planet tertiary maraka, and any aspect-based bhanga/balarishta condition (conjunction-only in 1b).

**Update** `docs/raman_saab/BUILD_STATUS.md`: mark Phase 1b done (modules + test count), and set the resume pointer to **Phase 1c** (GBB Shadbala — 6 components in Rupas, ±1-rupa fixture from `graha_bhava_balas_raman/` Ch.3–10; bhava-bala; ishta/kashta; sphutas; then backfill `strength_rank` + weakest-planet maraka).

**Next plan:** Phase 1c — GBB Shadbala & sphutas. Then Phase 2 — `doctrine/conditions.py` + the evaluable/descriptive RuleRecord encoding (predicate audit §7 is the finalized algebra).
