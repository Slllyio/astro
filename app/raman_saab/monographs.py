"""Wave A monographs (v25-v27 + v33): Marriage, Children, the Psychological profile,
and Aptitude/intelligence/work-style.

All PURE RE-READS (PREC-10) + Raman VERBATIM by frozen line range (the graha_chapters
method). Composed prose is guard-safe; Raman's own sentences render as labeled quotes.

v25 Marriage — HTJAH-II's Seventh-House chapter mined: what the 7th covers (198-231),
the 7th lord's placement results in his periods (710-852, ordinal sub-extraction for the
native's placement), marriage timing by the navamsa signs (853-886), and Raman's own
statements on loss of the partner (887-940 — rendered ONLY as a labeled verbatim block
with the method-not-prediction frame; the engine composes nothing atop them). Plus: the
FIRED kalatra rules from the H7 proforma ledgers (the 50-rule set, chart-specific), the
7th lord's sign paragraph (HPA-22 via graha_chapters), the D-9 reader core (existing
divisional), the upapada (synthesis), H7 timing activations, and children-after (H5).

v26 Children — HTJAH-I's fifth-house combination block (5179-5297: fertility, many
issues, loss — Raman verbatim), the H5 proforma significations, the D-7 Saptamsa core,
and H5 timing activations.

v27 Psychological profile — the computed mind stack woven into one profile: the HPA-18
lagna block QUOTED verbatim (per-lagna frozen anchors), the Moon's manas state (the D-30
health core), the strongest planet's temperament (ruler card, HTJAH-I:6248), the
navamsa-lagna stamp, and the Atmakaraka.

v33 Aptitude, intelligence & work style — the three trait axes the report never had as
output fields, assembled ENTIRELY from already-judged material: the H5 intellect verdict
and its fired combos (karaka Jupiter, HTJAH-I:5012), Mercury's HPA-21/HPA-22 paragraphs
(graha_chapters, frozen ranges), the fired H1.M.* Moon-mind rule (per-sign, cited), the
H3 courage verdict (HTJAH-I:3324), the navamsa-dispositor trade + 10th-sign profile
(HTJAH-II:10249 / 10340), the H10 profession-mode split, and the computed conditions of
the 10th lord, Saturn and Mars. Saturn=discipline / Mars=drive keyword glosses are
NON_RAMAN_THEMES and render ONLY under MODERN_BANNER (the v20 precedent). The profession
synthesis (v23) governs trade wherever the two overlap. A verbatim block of Raman's
master Moon-mind instruction (HTJAH-I ~1231) is a corpus-machine follow-up: its range
must be pinned against the vendored file, never from memory, so it is deliberately
absent here rather than guessed.

Usage:
    from app.raman_saab.monographs import (build_aptitude_profile,
                                           build_children_chapter,
                                           build_marriage_monograph,
                                           build_psych_profile)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.doctrine.sources import Citation, passage

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_H2: Final[str] = "HTJAH-II"
_H1: Final[str] = "HTJAH-I"

#: HTJAH-II ch.XI "Concerning the Seventh House" — frozen ranges (mined 2026-08-04).
MARRIAGE_INTRO: Final[tuple[int, int]] = (198, 231)
MARRIAGE_LORD_DASA: Final[tuple[int, int]] = (710, 852)
MARRIAGE_TIMING_NAVAMSA: Final[tuple[int, int]] = (853, 886)
MARRIAGE_SEPARATION: Final[tuple[int, int]] = (887, 940)

#: HTJAH-I fifth-house combination block ("culled out from important classical works").
CHILDREN_COMBOS: Final[tuple[int, int]] = (5179, 5297)

#: HPA-18 "Results of Ascending Signs" — per-lagna block anchors (mined 2026-08-04).
LAGNA_BLOCKS: Final[dict[int, tuple[int, int]]] = {
    1: (40, 67), 2: (68, 93), 3: (94, 113), 4: (114, 128), 5: (129, 147), 6: (148, 166),
    7: (167, 194), 8: (195, 222), 9: (223, 246), 10: (247, 266), 11: (267, 307),
    12: (308, 327),
}

CITED_ANCHORS: Final[tuple[Citation, ...]] = tuple(
    [Citation(_H2, s) for s, _ in (MARRIAGE_INTRO, MARRIAGE_LORD_DASA,
                                   MARRIAGE_TIMING_NAVAMSA, MARRIAGE_SEPARATION)]
    + [Citation(_H1, CHILDREN_COMBOS[0])]
    + [Citation("HPA-18", s) for s, _ in LAGNA_BLOCKS.values()])

_ORDINALS: Final[dict[int, tuple[str, ...]]] = {
    1: ("Lagna", "first house", "1st"), 2: ("2nd",), 3: ("3rd",), 4: ("4th",),
    5: ("5th",), 6: ("6th",), 7: ("7th house with", "7th house is"), 8: ("8th",),
    9: ("9th",), 10: ("10th",), 11: ("11th",), 12: ("12th",),
}


def _clean(text: str) -> str:
    text = re.sub(r"[¬­-]\s*\n\s*", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _pull(work: str, rng: tuple[int, int]) -> Optional[str]:
    p = passage(f"{work}:{rng[0]}-{rng[1]}")
    return _clean(p.get("text", "")) or None if isinstance(p, dict) else None


def _lord_dasa_extract(house: int) -> Optional[str]:
    """The '7th lord in the Nth' sentence-run for the native's placement house."""
    p = passage(f"{_H2}:{MARRIAGE_LORD_DASA[0]}-{MARRIAGE_LORD_DASA[1]}")
    if not isinstance(p, dict):
        return None
    text = _clean(p.get("text", ""))
    anchor = None
    for w in _ORDINALS.get(house, ()):
        i = text.find(f"7th lord in the {w}")
        if i < 0:
            i = text.find(f"7th lord joins") if house == 2 else -1
        if i >= 0:
            anchor = i
            break
    if anchor is None:
        return None
    nxt = len(text)
    for h2, words in _ORDINALS.items():
        if h2 == house:
            continue
        for w in words:
            j = text.find(f"7th lord in the {w}", anchor + 10)
            if 0 < j < nxt:
                nxt = j
    return text[anchor:nxt].strip() or None


# ── v25 Marriage ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MarriageMonograph:
    seventh_covers: str                     # verbatim intro
    lord_placement_house: int
    lord_period_text: Optional[str]         # verbatim, the native's placement
    spouse_sign_text: Optional[tuple[str, str]]  # 7th lord in its sign (HPA-22)
    fired_kalatra: tuple[tuple[str, str, str], ...]  # (branch, text, cite)
    upapada: str
    timing_navamsa: str                     # verbatim timing doctrine
    timing_windows: tuple[str, ...]         # H7 activations from the timeline
    children_after: Optional[str]           # H5 verdict
    separation_quote: str                   # Raman verbatim, labeled
    verdict: str                            # the UNCHANGED H7 rollup


def build_marriage_monograph(r: "DetailedReport") -> Optional[MarriageMonograph]:
    from app.raman_saab.doctrine.lookups import graha_chapters as gc
    from app.raman_saab.render import _jd_to_date

    if len(r.proformas) < 7:
        return None
    pf7 = r.proformas[6]
    lord7 = pf7.lord
    p7 = r.chart.planets.get(lord7)
    lord_house = p7.rasi_house if p7 is not None else 0
    sign7 = int(p7.lon % 360.0 // 30.0) + 1 if p7 is not None else 0
    fired: list[tuple[str, str, str]] = []
    for sv in pf7.significations:
        for led in (sv.ledger, *sv.alt_ledgers):
            for fr in (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral):
                cite = f"{fr.rule.source.work}:{fr.rule.source.line}"
                row = (fr.branch, fr.text, cite)
                if row not in fired:
                    fired.append(row)
    windows = tuple(
        f"{ch.maha} MD ({_jd_to_date(ch.start_jd)} to {_jd_to_date(ch.end_jd)}): "
        f"H7 {tier}"
        for ch in r.life_chapters.chapters
        for h, tier, _v in ch.houses_lit if h == 7)
    h5 = next((s for s in r.proformas[4].significations
               if s.signification == "children"), None) if len(r.proformas) >= 5 else None
    return MarriageMonograph(
        seventh_covers=_pull(_H2, MARRIAGE_INTRO) or "",
        lord_placement_house=lord_house,
        lord_period_text=_lord_dasa_extract(lord_house) if lord_house else None,
        spouse_sign_text=gc.sign_result(lord7, sign7) if sign7 else None,
        fired_kalatra=tuple(fired),
        upapada=getattr(r.synthesis, "upapada", "") or "",
        timing_navamsa=_pull(_H2, MARRIAGE_TIMING_NAVAMSA) or "",
        timing_windows=windows,
        children_after=f"{h5.verdict} ({h5.degree})" if h5 is not None else None,
        separation_quote=_pull(_H2, MARRIAGE_SEPARATION) or "",
        verdict=pf7.rollup)


# ── v26 Children ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChildrenChapter:
    combos_quote: str                       # HTJAH-I verbatim combination block
    significations: tuple[tuple[str, str], ...]  # (key, verdict+degree) from H5
    fired_rules: tuple[tuple[str, str, str], ...]
    timing_windows: tuple[str, ...]
    verdict: str


def build_children_chapter(r: "DetailedReport") -> Optional[ChildrenChapter]:
    from app.raman_saab.render import _jd_to_date
    if len(r.proformas) < 5:
        return None
    pf5 = r.proformas[4]
    fired: list[tuple[str, str, str]] = []
    for sv in pf5.significations:
        for led in (sv.ledger, *sv.alt_ledgers):
            for fr in (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral):
                cite = f"{fr.rule.source.work}:{fr.rule.source.line}"
                row = (fr.branch, fr.text, cite)
                if row not in fired:
                    fired.append(row)
    windows = tuple(
        f"{ch.maha} MD ({_jd_to_date(ch.start_jd)} to {_jd_to_date(ch.end_jd)}): "
        f"H5 {tier}"
        for ch in r.life_chapters.chapters
        for h, tier, _v in ch.houses_lit if h == 5)
    return ChildrenChapter(
        combos_quote=_pull(_H1, CHILDREN_COMBOS) or "",
        significations=tuple((sv.signification, f"{sv.verdict} ({sv.degree})")
                             for sv in pf5.significations),
        fired_rules=tuple(fired), timing_windows=windows, verdict=pf5.rollup)


# ── v27 Psychological profile ───────────────────────────────────────────────────


@dataclass(frozen=True)
class PsychProfile:
    lagna_quote: tuple[str, str]            # HPA-18 verbatim + cite
    moon_state: str                         # manas karaka (dignity + afflictions)
    temperament: Optional[str]              # strongest-planet line (ruler card)
    nature_stamp: Optional[str]             # who stamps nature/appearance
    atmakaraka: Optional[str]
    woven: str                              # the composed profile (guard-safe)


def build_psych_profile(r: "DetailedReport") -> Optional[PsychProfile]:
    from app.raman_saab.judges.trimsamsa_health_reading import (
        build_trimsamsa_health_reading)
    from app.raman_saab.primitives.chara_karakas import chara_karakas
    from app.raman_saab.raman_style import conclusion, weighed

    asc = r.chart.asc_sign
    rng = LAGNA_BLOCKS.get(asc)
    if rng is None:
        return None
    quote = _pull("HPA-18", rng)
    if not quote:
        return None
    try:
        core = build_trimsamsa_health_reading(r.chart).core
        moon = (f"the Moon (manas) in house {core.moon_house}, {core.moon_dignity}"
                + (", afflicted by " + ", ".join(core.moon_afflictions)
                   if core.moon_afflictions else ", free of natural-malefic affliction"))
    except Exception:  # noqa: BLE001
        moon = ""
    try:
        ak = chara_karakas(r.chart).get("AK")
    except Exception:  # noqa: BLE001
        ak = None
    woven = weighed(
        "the rising sign's own portrait, the Moon's state, the strongest planet's "
        "temperament and the Atmakaraka together",
        "the profile below describes the method's reading of the mind — tendencies in "
        "Raman's descriptive idiom, never a diagnosis")
    woven += " " + conclusion(
        "each thread is quoted or re-read from its own section; nothing here is a new "
        "judgment")
    return PsychProfile(
        lagna_quote=(quote, f"HPA-18:{rng[0]}"),
        moon_state=moon,
        temperament=r.ruler.temperament,
        nature_stamp=r.ruler.stamps_nature,
        atmakaraka=ak,
        woven=woven)


# ── v33 Aptitude, intelligence & work style ─────────────────────────────────────


@dataclass(frozen=True)
class AptitudeProfile:
    """Pure re-read (PREC-10). Every Optional is an honest absence — a sparse
    chart, a nodal dispositor, or a machine without the corpus — never a guess."""

    # intelligence (buddhi)
    intellect_verdict: Optional[str]                    # H5 "intellect" verdict (degree)
    intellect_fired: tuple[tuple[str, str, str], ...]   # (branch, text, cite) — H5 intellect ledger
    mercury_state: str                                  # computed: house/dignity/avastha
    mercury_house_text: Optional[tuple[str, str]]       # HPA-21 verbatim (text, cite)
    mercury_sign_text: Optional[tuple[str, str]]        # HPA-22 verbatim (text, cite)
    moon_mind_fired: tuple[tuple[str, str, str], ...]   # fired H1.M.* rules (per-sign, cited)
    jupiter_state: Optional[str]                        # H5 intellect-karaka condition
    # aptitude
    courage_verdict: Optional[str]                      # H3 "courage" verdict (degree)
    trade_indication: Optional[tuple[str, str, str]]    # (10th lord, nav-dispositor, trade)
    tenth_sign_profile: Optional[tuple[int, str]]       # (sign, CAREER_BY_SIGN text)
    strongest_affinity: Optional[tuple[str, str]]       # (strongest planet, vocation row)
    # work style
    mode_split: tuple[tuple[str, str], ...]             # H10 profession_* key -> verdict
    tenth_lord_state: Optional[str]                     # computed condition line
    saturn_state: Optional[str]                         # computed condition line
    mars_state: Optional[str]                           # computed condition line
    style_modern: tuple[str, ...]                       # NON_RAMAN_THEMES words — MODERN_BANNER at render
    woven: str                                          # composed prose (guard-safe)


def _condition(planet: str, r: "DetailedReport") -> Optional[str]:
    """A computed condition line — engine facts (house, dignity, avastha), no gloss."""
    from app.raman_saab.primitives.deeptadi import state
    from app.raman_saab.primitives.dignity import dignity
    p = r.chart.planets.get(planet)
    if p is None:
        return None
    return (f"in house {p.rasi_house}, dignity {dignity(planet, r.chart)}, "
            f"avastha {state(planet, r.chart)}")


def _fired_for_key(pf, key: str) -> tuple[tuple[str, str, str], ...]:
    """The fired-rule ledger rows of one signification, deduplicated, with cites."""
    fired: list[tuple[str, str, str]] = []
    for sv in pf.significations:
        if sv.signification != key:
            continue
        for led in (sv.ledger, *sv.alt_ledgers):
            for fr in (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral):
                cite = f"{fr.rule.source.work}:{fr.rule.source.line}"
                row = (fr.branch, fr.text, cite)
                if row not in fired:
                    fired.append(row)
    return tuple(fired)


def _fired_moon_mind(pf1) -> tuple[tuple[str, str, str], ...]:
    """The chart's fired H1.M.* Moon-mind rules from the H1 proforma —
    per-Moon-sign mental-tendency doctrine, each row already cited."""
    fired: list[tuple[str, str, str]] = []
    for sv in pf1.significations:
        for led in (sv.ledger, *sv.alt_ledgers):
            for fr in (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral):
                if not fr.rule.id.startswith("H1.M."):
                    continue
                cite = f"{fr.rule.source.work}:{fr.rule.source.line}"
                row = (fr.rule.id, fr.text, cite)
                if row not in fired:
                    fired.append(row)
    return tuple(fired)


def _sig_line(r: "DetailedReport", house: int, key: str) -> Optional[str]:
    if len(r.proformas) < house:
        return None
    sv = next((s for s in r.proformas[house - 1].significations
               if s.signification == key), None)
    return f"{sv.verdict} ({sv.degree})" if sv is not None else None


def build_aptitude_profile(r: "DetailedReport") -> Optional[AptitudeProfile]:
    from app.raman_saab.doctrine.lookups import graha_chapters as gc
    from app.raman_saab.planet_biographies import NON_RAMAN_THEMES
    from app.raman_saab.primitives.career import (CAREER_BY_SIGN,
                                                  TRADE_BY_NAVAMSA_DISPOSITOR,
                                                  career_indication, tenth_lord,
                                                  tenth_sign)
    from app.raman_saab.raman_style import conclusion, weighed

    if len(r.proformas) < 10:
        return None

    # intelligence: H5 verdict + fired intellect combos + Mercury + Moon-mind + Jupiter
    intellect = _sig_line(r, 5, "intellect")
    intellect_fired = _fired_for_key(r.proformas[4], "intellect")
    mercury = _condition("Mercury", r) or "not placed (sparse chart)"
    p_mer = r.chart.planets.get("Mercury")
    try:
        mer_house = gc.house_result("Mercury", p_mer.rasi_house) if p_mer is not None else None
    except Exception:  # noqa: BLE001 — corpus absent on this machine
        mer_house = None
    try:
        mer_sign = gc.sign_result("Mercury", p_mer.sign) if p_mer is not None else None
    except Exception:  # noqa: BLE001
        mer_sign = None
    moon_mind = _fired_moon_mind(r.proformas[0])

    # aptitude: H3 courage + the three vocational angles
    courage = _sig_line(r, 3, "courage")
    try:
        trade = career_indication(r.chart)
    except Exception:  # noqa: BLE001
        trade = None
    try:
        t_sign = tenth_sign(r.chart)
        tenth_profile = (t_sign, CAREER_BY_SIGN[t_sign])
    except Exception:  # noqa: BLE001
        tenth_profile = None
    strongest = r.ruler.strongest
    affinity = ((strongest, TRADE_BY_NAVAMSA_DISPOSITOR[strongest])
                if strongest in TRADE_BY_NAVAMSA_DISPOSITOR else None)

    # work style: H10 modes + computed conditions + bannered modern glosses
    mode_keys = ("profession_authority", "profession_trade",
                 "profession_learned", "profession_labour")
    modes = tuple((k, v) for k in mode_keys
                  if (v := _sig_line(r, 10, k)) is not None)
    try:
        t_lord_state = _condition(tenth_lord(r.chart), r)
    except Exception:  # noqa: BLE001
        t_lord_state = None
    style_modern = tuple(
        f"{planet}: {', '.join(NON_RAMAN_THEMES[planet])}"
        for planet in ("Saturn", "Mars") if planet in NON_RAMAN_THEMES)

    woven = weighed(
        "the 5th house with Jupiter its karaka, Mercury's own placement, the Moon's "
        "mental disposition, the 3rd house's initiative, and the 10th house's modes "
        "with the navamsa-dispositor of its lord together",
        "the profile below re-reads aptitude, intelligence and the manner of work from "
        "sections already judged — tendencies in Raman's descriptive idiom, never a "
        "measurement of ability")
    woven += " " + conclusion(
        "where this overlaps the Profession synthesis, that synthesis governs; nothing "
        "here is a new judgment")

    return AptitudeProfile(
        intellect_verdict=intellect,
        intellect_fired=intellect_fired,
        mercury_state=mercury,
        mercury_house_text=mer_house,
        mercury_sign_text=mer_sign,
        moon_mind_fired=moon_mind,
        jupiter_state=_condition("Jupiter", r),
        courage_verdict=courage,
        trade_indication=trade,
        tenth_sign_profile=tenth_profile,
        strongest_affinity=affinity,
        mode_split=modes,
        tenth_lord_state=t_lord_state,
        saturn_state=_condition("Saturn", r),
        mars_state=_condition("Mars", r),
        style_modern=style_modern,
        woven=woven)
