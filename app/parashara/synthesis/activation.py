"""Activation — WHEN a promise fructifies: the dasha windows that light up a topic, graded by
BPHS's own antardasha rule.

Two separable questions, each with its own doctrine:

**Which house does a window activate? (targeting)** A period-lord bears on a house if it owns,
occupies, or aspects the house OR its lord — the conjunct-the-lord factor is Parashara's own idiom
(BPHS-47:108: the Sun's dasha gives wealth "if the Sun be associated with the lord of the 2nd", a
son with the lord of the 5th, and so on). Nodes target by ownership-they-lack, occupancy and
conjunction only — they cast no drishti in this engine (BPHS-26; see `chart_facts`).

**How does the window behave? (quality)** BPHS grades an antardasha by the AD lord's POSITION FROM
THE DASA LORD and its own dignity — the rule recurs across ch.52-60 for every planet:
    auspicious — the AD lord in a kendra or trikona, the 11th or the 2nd from the Dasa lord
                 (BPHS-53:364), or exalted / in own house (BPHS-52:45);
    adverse    — the AD lord in the 6th, the 8th or the 12th from the Dasa lord, or debilitated
                 (BPHS-53:375).
The mahadasha lord's own quality is ch.47's rule (BPHS-47:76): favourable in the Ascendant /
exaltation / own / a friend's sign; unfavourable in the 6th/8th/12th, debilitation or an inimical
sign. (BPHS-47:48 further says the dasha's effects accord with the lord's STRENGTH — noted, not yet
encoded.) This module previously mirrored the Raman engine's four-tier influence grading; replaced
2026-08-29 (user decision) with the rule Parashara himself states.

Two honesty flags ride on every window: `maraka` — the period of a maraka planet, which BPHS-44:51
says "will bring death on the native depending on whether he has a long, medium or short life" —
and `beyond_span` — the window opens past the chart's computed Nisargayu span (annotated, never
clipped: surfaces only add). Windows are dated as AGE (years after birth), in the classical
indication idiom — timing is never a decree.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable, Mapping, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import (
    EXALTATION, MOOLATRIKONA, SIGN_LORDS, naisargika)
from app.parashara.reading import ParasharaReading
from app.parashara.chart.cast import ParasharaChart
from app.parashara.synthesis.chart_facts import ASPECTING_GRAHAS, house_sign, planet_signs
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier

#: Targeting: a period-lord conjunct/aspecting a house's LORD times that house (BPHS-47 sl.7-11).
TARGETING_SOURCE: Final[Citation] = Citation("BPHS-47", 108)
#: "The effects of the Dasas of the planets are in accordance with their strength" (sl.3-4).
MD_STRENGTH_SOURCE: Final[Citation] = Citation("BPHS-47", 48)
#: MD-lord quality: favourable in lagna/exaltation/own/friend's sign; unfavourable in 6/8/12,
#: debilitation or an inimical sign (sl.5-6).
MD_QUALITY_SOURCE: Final[Citation] = Citation("BPHS-47", 76)
#: AD lord in kendra/trikona/11th/2nd FROM the Dasa lord -> auspicious (Mercury's AD, sl.41-43).
AD_QUALITY_SOURCE: Final[Citation] = Citation("BPHS-53", 364)
#: AD lord in 6/8/12 from the Dasa lord, or debilitated -> adverse (sl.44-46).
AD_ADVERSE_SOURCE: Final[Citation] = Citation("BPHS-53", 375)
#: AD lord exalted / in own house -> auspicious (the Sun's AD in his own dasha, sl.1-3).
AD_DIGNITY_SOURCE: Final[Citation] = Citation("BPHS-52", 45)
#: Maraka periods "will bring death ... depending on whether he has a long, medium or short life".
MARAKA_PERIOD_SOURCE: Final[Citation] = Citation("BPHS-44", 51)

#: AD-from-MD houses that are auspicious (kendra 1/4/7/10, trikona 5/9, the 2nd and the 11th) and
#: adverse (the dusthanas) — BPHS-53:364 / :375. The 3rd and 12th-as-counted carry no position vote.
_AUSPICIOUS_FROM_MD: Final[frozenset[int]] = frozenset({1, 2, 4, 5, 7, 9, 10, 11})
_ADVERSE_FROM_MD: Final[frozenset[int]] = frozenset({6, 8, 12})

#: Quality rank for sorting — best first.
QUALITY_RANK: Final[Mapping[str, int]] = {"auspicious": 0, "mixed": 1, "neutral": 2, "adverse": 3}


@dataclass(frozen=True)
class ActiveWindow:
    """A (mahadasha, antardasha) period that bears on the topic, graded by BPHS's own rule."""
    maha_lord: str
    antar_lord: str
    quality: str              # auspicious | mixed | neutral | adverse (the AD rule, ch.52-60)
    md_quality: str           # favourable | unfavourable | neutral (the MD rule, BPHS-47:76)
    ad_from_md: int           # the AD lord's house counted from the MD lord (1..12)
    start_age: float          # years after birth (clipped at 0)
    end_age: float
    maraka: bool              # a maraka planet's period (BPHS-44:51) — classically sensitive
    beyond_span: bool         # opens past the computed Nisargayu span (annotated, not clipped)

    @property
    def label(self) -> str:
        lo, hi = round(self.start_age), round(self.end_age)
        age = f"age {lo}" if lo == hi else f"ages {lo}-{hi}"
        flags = []
        if self.maraka:
            flags.append("a maraka period")
        if self.beyond_span:
            flags.append("beyond the computed Nisargayu span")
        note = f" ({'; '.join(flags)})" if flags else ""
        return (f"{self.antar_lord} periods within the {self.maha_lord} dasha, {age} — "
                f"{self.quality}{note}")


def influences(chart: ParasharaChart, planet: str, house: int, *, signs=None) -> bool:
    """Does `planet` bear on `house` — own / occupy / aspect the house OR its lord (targeting)?"""
    signs = signs or planet_signs(chart)
    sign = signs.get(planet)
    if sign is None:
        return False
    hsign = house_sign(chart.asc_sign, house)
    lord = SIGN_LORDS[hsign]
    lord_sign = signs.get(lord)
    can_aspect = planet in ASPECTING_GRAHAS
    if planet == lord:                                          # owns the house
        return True
    if sign == hsign:                                           # occupies the house
        return True
    if can_aspect and aspects_sign(planet, sign, hsign):        # aspects the house
        return True
    if lord_sign is not None and sign == lord_sign:             # conjoins the lord
        return True
    if lord_sign is not None and can_aspect and aspects_sign(planet, sign, lord_sign):
        return True                                             # aspects the lord
    return False


def influences_any(chart: ParasharaChart, planet: str, houses: Iterable[int], *, signs=None) -> bool:
    signs = signs or planet_signs(chart)
    return any(influences(chart, planet, h, signs=signs) for h in houses)


def _dignity_vote(planet: str, sign: int) -> int:
    """+1 exalted or own house, -1 debilitated, else 0 — exactly the clauses BPHS's antardasha
    chapters name (BPHS-52:45 auspicious; BPHS-53:375 adverse). Deliberately narrower than the full
    ch.3 dignity read: an enemy's sign is NOT in the antardasha rule, so it casts no vote here."""
    if planet not in EXALTATION:
        return 0
    if sign == EXALTATION[planet] or SIGN_LORDS.get(sign) == planet:
        return 1
    if sign == ((EXALTATION[planet] - 1 + 6) % 12) + 1:
        return -1
    return 0


def window_quality(chart: ParasharaChart, md_lord: str, ad_lord: str, *, signs=None
                   ) -> tuple[str, int, int]:
    """(quality, ad_from_md, dignity_vote) for one (MD, AD) pair — BPHS's own antardasha grading.

    Position vote: +1 if the AD lord sits in a kendra/trikona/2nd/11th from the MD lord
    (BPHS-53:364), -1 in the 6th/8th/12th from it (BPHS-53:375). Dignity vote: `_dignity_vote`.
    quality: sum > 0 auspicious; sum < 0 adverse; opposed non-zero votes mixed; else neutral.
    The MD lord's own antardasha (ad == md) counts position 1 (a kendra) — its quality then rides
    on the lord's dignity, matching ch.52's "in his own Dasa" clauses.
    """
    signs = signs or planet_signs(chart)
    md_sign, ad_sign = signs.get(md_lord), signs.get(ad_lord)
    if md_sign is None or ad_sign is None:
        return "neutral", 0, 0
    ad_from_md = ((ad_sign - md_sign) % 12) + 1
    pos = 1 if ad_from_md in _AUSPICIOUS_FROM_MD else -1 if ad_from_md in _ADVERSE_FROM_MD else 0
    dig = _dignity_vote(ad_lord, ad_sign)
    total = pos + dig
    if total > 0:
        quality = "auspicious"
    elif total < 0:
        quality = "adverse"
    elif pos != 0 and dig != 0:
        quality = "mixed"                                       # opposed votes, disclosed as such
    else:
        quality = "neutral"
    return quality, ad_from_md, dig


def md_quality(chart: ParasharaChart, md_lord: str, *, signs=None) -> str:
    """favourable | unfavourable | neutral — the mahadasha lord's own placement (BPHS-47:76).

    Favourable: in the Ascendant, exaltation, own sign or a friend's sign. Unfavourable: in the
    6th/8th/12th house, debilitation or an inimical sign. Nodes (outside ch.3's dignity scheme)
    grade by house alone.
    """
    signs = signs or planet_signs(chart)
    sign = signs.get(md_lord)
    if sign is None:
        return "neutral"
    house = ((sign - chart.asc_sign) % 12) + 1
    if house in (6, 8, 12):
        return "unfavourable"
    if house == 1:
        return "favourable"
    if md_lord not in EXALTATION:                               # a node: house said all it can
        return "neutral"
    if sign == EXALTATION[md_lord] or SIGN_LORDS.get(sign) == md_lord:
        return "favourable"
    if sign == ((EXALTATION[md_lord] - 1 + 6) % 12) + 1:
        return "unfavourable"
    lord = SIGN_LORDS[sign]
    if lord in MOOLATRIKONA:
        rel = naisargika(md_lord, lord)
        if rel == "mitra":
            return "favourable"
        if rel == "shatru":
            return "unfavourable"
    return "neutral"


def active_windows(reading: ParasharaReading, houses: Iterable[int]) -> tuple[ActiveWindow, ...]:
    """Every Vimshottari (MD, AD) window (age >= 0) bearing on any of `houses`, best quality first
    then chronological."""
    houses = tuple(houses)
    chart = reading.chart
    signs = planet_signs(chart)
    vim = next((d for d in reading.dashas if d.system == "vimshottari"), None)
    if vim is None:
        return ()
    maraka_names = {m.planet for m in reading.maraka_planets}
    span = reading.nisargayu_full.total_years
    quality_cache: dict[tuple[str, str], tuple[str, int, int]] = {}
    md_cache: dict[str, str] = {}

    out: list[ActiveWindow] = []
    for maha_lord, bhuktis in vim.bhuktis:
        maha_infl = influences_any(chart, maha_lord, houses, signs=signs)
        if maha_lord not in md_cache:
            md_cache[maha_lord] = md_quality(chart, maha_lord, signs=signs)
        for b in bhuktis:
            if b.end_year <= 0:                                 # entirely before birth
                continue
            if not (maha_infl or influences_any(chart, b.lord, houses, signs=signs)):
                continue                                        # window does not target the topic
            key = (maha_lord, b.lord)
            if key not in quality_cache:
                quality_cache[key] = window_quality(chart, maha_lord, b.lord, signs=signs)
            quality, ad_from_md, _ = quality_cache[key]
            out.append(ActiveWindow(
                maha_lord=maha_lord, antar_lord=b.lord, quality=quality,
                md_quality=md_cache[maha_lord], ad_from_md=ad_from_md,
                start_age=max(0.0, b.start_year), end_age=b.end_year,
                maraka=maha_lord in maraka_names or b.lord in maraka_names,
                beyond_span=b.start_year > span))
    out.sort(key=lambda w: (QUALITY_RANK[w.quality], w.start_age))
    return tuple(out)


def activation_evidence(houses: Iterable[int],
                        windows: tuple[ActiveWindow, ...]) -> list[Evidence]:
    """One ACTIVATION-tier audit note for the strongest timing window (weight 0 — activation times
    a promise, it never votes on whether the promise exists)."""
    houses = tuple(houses)
    if not windows:
        return []
    best = windows[0]                                           # best quality, earliest
    source = (AD_QUALITY_SOURCE if best.quality == "auspicious"
              else AD_ADVERSE_SOURCE if best.quality == "adverse" else TARGETING_SOURCE)
    return [Evidence(
        topic=houses[0], tier=Tier.ACTIVATION, category="activation", polarity=Polarity.NEUTRAL,
        rule=f"the matter's strongest activation is {best.quality}, in the {best.maha_lord} dasha "
             f"(MD lord {best.md_quality})",
        condition="dasha_activation",
        observed=best.label,
        source=source)]
