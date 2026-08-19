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

#: Sign names for narration (ASCII; index = rashi 1..12).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

#: Maintainer/encoding-scope markers that belong in fine print, not client bullets
#: (2026-08-18 report-critique: "v1-OOS" / "owned by H7.C.60" leaked into readings).
_MAINTAINER_MARKERS: Final[tuple[str, ...]] = (
    "v1-OOS", "owned by H7", "kept in text", "TODO(predicate")


def split_maintainer_notes(text: str) -> tuple[str, str]:
    """Split a fired-rule text into (client_text, maintainer_notes).

    ADD-ONLY routing, not removal: the notes are still rendered, in a trailing
    fine-print line, and the raw rule text is unchanged in the data. A note is a
    parenthetical or a whole sentence carrying one of `_MAINTAINER_MARKERS`."""
    notes: list[str] = []
    out = text
    for m in re.finditer(r"\([^()]*\)", out):
        if any(mk in m.group(0) for mk in _MAINTAINER_MARKERS):
            notes.append(m.group(0)[1:-1])
    for n in notes:
        out = out.replace(f"({n})", "")
    kept: list[str] = []
    for sent in re.split(r"(?<=\.)\s+", out):
        if any(mk in sent for mk in _MAINTAINER_MARKERS):
            notes.append(sent.strip())
        else:
            kept.append(sent)
    out = re.sub(r"\s{2,}", " ", " ".join(kept)).strip().rstrip(";").strip()
    return out, "; ".join(notes)


def _ordinal(n: int) -> str:
    from app.raman_saab.ordinals import ordinal
    return ordinal(n)


def _kuja_narration(chart) -> tuple[str, ...]:
    """Narrate _KujaDosha's own per-frame evaluation (HTJAH-II:2579-2622) — which
    reference point(s) place Mars in a dosha house, each exemption checked and its
    result. A pure re-read of the rule's evaluation path via its append-only
    accessor; composes no new judgment and never re-decides the firing."""
    from app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations import (
        evaluate_kuja_dosha)
    kd = evaluate_kuja_dosha(chart)
    if not kd.mars_present:
        return ()
    lines: list[str] = []
    sign = _SIGN_NAMES[kd.mars_sign]
    for fr in kd.frames:
        if fr.house == 0:
            lines.append(f"from {fr.origin}, Mars falls in none of the dosha "
                         f"houses (2/4/7/8/12)")
        elif fr.sign_exempt:
            lines.append(f"from {fr.origin}, Mars falls in the "
                         f"{_ordinal(fr.house)}, but {sign} is an exempt sign "
                         f"for the {_ordinal(fr.house)} - the frame is spared")
        else:
            lines.append(f"from {fr.origin}, Mars falls in the "
                         f"{_ordinal(fr.house)}; {sign} is not an exempt sign "
                         f"for the {_ordinal(fr.house)} - the frame stands")
    if kd.universal_exempt:
        lines.append(f"Mars stands in {sign} - wholly exempt "
                     f"(the Leo/Aquarius exemption)")
    else:
        lines.append(f"Mars in {sign} is not in the wholly-exempt Leo/Aquarius")
    if kd.conjunct_jupiter or kd.conjunct_moon:
        with_whom = " and ".join(p for p, c in (("Jupiter", kd.conjunct_jupiter),
                                                ("the Moon", kd.conjunct_moon)) if c)
        lines.append(f"Mars conjoins {with_whom} - the dosha is neutralised")
    else:
        lines.append("Mars conjoins neither Jupiter nor the Moon")
    lines.append("the dosha stands" if kd.fires else "the dosha does not arise")
    return tuple(lines)


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
    # ── Wave-2 completions (2026-08-18 report-critique, append-only): the shipped
    # B3 happiness-vs-coverture split surfaced where the client looks, the
    # _KujaDosha per-frame narration (via the rule's own append-only accessor,
    # HTJAH-II:2579-2622), and the already-computed favourable Jupiter transit
    # windows touching the 7th from the Moon. Defaults keep every existing
    # construction unchanged. ────────────────────────────────────────────────────
    marital_happiness: Optional[str] = None      # H7 'marital_happiness' verdict (degree)
    coverture: Optional[str] = None              # H7 'coverture' verdict (degree)
    kuja_narration: tuple[str, ...] = ()         # per-frame dosha narration lines
    jupiter_h7_windows: tuple[str, ...] = ()     # favourable Jupiter windows, 7th from Moon
    # v36 (2026-08-19, corpus-unblocked): the COMPUTED timing layer. `timing_navamsa`
    # above prints Raman's timing paragraph verbatim and computes none of it; this is the
    # marriage-giving roster (HTJAH-II:852-867), his two delay screens (HTJAH-II:875-881)
    # and the Jupiter-transit sphutas (HTJAH-II:869-873), applied to this chart.
    timing: object = None


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
    # Wave-2 (2026-08-18): the B3 happiness/coverture split — pure re-read of the
    # same H7 significations the proforma already judged.
    def _sig7(key: str) -> Optional[str]:
        sv = next((s for s in pf7.significations if s.signification == key), None)
        return f"{sv.verdict} ({sv.degree})" if sv is not None else None
    # the _KujaDosha per-frame narration (append-only accessor; HTJAH-II:2579-2622)
    try:
        kuja = _kuja_narration(r.chart)
    except Exception:  # noqa: BLE001 — Track-B sparse
        kuja = ()
    # the method's own favourable Jupiter windows touching the 7th (from the Moon) —
    # a FILTER of the already-computed Gochara outlook rows, no new doctrine claim.
    jup7 = tuple(
        f"{_jd_to_date(seg.start_jd)} to {_jd_to_date(seg.end_jd)}"
        for seg in r.gochara_outlook.get("Jupiter", ())
        if seg.gochara_good and (seg.end_jd - seg.start_jd) >= 25
        and seg.house_from_moon == 7)
    # v36: the computed timing layer. Its own try — a failure here must never silence the
    # rest of the monograph — and report-only: imported by nothing in the verdict path.
    try:
        from app.raman_saab.judges.marriage_timing import build_marriage_timing
        _marriage_timing = build_marriage_timing(r)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        _marriage_timing = None
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
        verdict=pf7.rollup,
        marital_happiness=_sig7("marital_happiness"),
        coverture=_sig7("coverture"),
        kuja_narration=kuja,
        jupiter_h7_windows=jup7,
        timing=_marriage_timing)


# ── v26 Children ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChildrenChapter:
    combos_quote: str                       # HTJAH-I verbatim combination block
    significations: tuple[tuple[str, str], ...]  # (key, verdict+degree) from H5
    fired_rules: tuple[tuple[str, str, str], ...]
    timing_windows: tuple[str, ...]
    verdict: str
    # ── Wave-2 completions (2026-08-18 report-critique, append-only): the D-7
    # corroboration the preamble already promises (a re-read of the Saptamsa
    # section's own computed structures), the Jupiter (putrakaraka) condition,
    # and the doctrine-reviewed classical-shorthand reframe note copied VERBATIM
    # from the D-7 section's notes so it renders BEFORE the fired rules here.
    # Defaults keep every existing construction unchanged. ──────────────────────
    d7_corroboration: str = ""              # beeja/kshetra + D-7 seat + gender lean
    putrakaraka_line: str = ""              # Jupiter's computed condition
    reframe_note: str = ""                  # the D-7 section's shorthand reframe, verbatim


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
    # Wave-2 (2026-08-18): the D-7 corroboration row + Jupiter condition + reframe
    # note — pure re-reads of the Saptamsa reading's own computed structures.
    d7_row, jup_line, reframe = "", "", ""
    try:
        from app.raman_saab.judges.saptamsa_reading import (
            build_saptamsa_children_reading)
        sr = build_saptamsa_children_reading(r.chart)
        core, ov = sr.raman_core, sr.d7_overlay
        yn = {True: "yes", False: "no", None: "not computed"}
        lean = ("; ".join(g.text for g in ov.gender_indicators)
                if ov.gender_indicators else "no gender rule fires")
        d7_row = (
            f"Beeja (male fertility point) strong: {yn[core.beeja_strong]}; "
            f"Kshetra (female): {yn[core.kshetra_strong]}; the D-7 seat: lagna "
            f"{_SIGN_NAMES[ov.lagna_sign]} under {ov.lagna_lord}, Jupiter in the "
            f"D-7 {_ordinal(ov.jupiter_house) if ov.jupiter_house else 'chart'} "
            f"in {_SIGN_NAMES[ov.jupiter_sign]} ({ov.jupiter_dignity}); gender "
            f"lean: {lean} (re-read from the D-7 Children section, which decides "
            f"by Raman's Rasi method; the D-7 corroborates)")
        jup_line = (
            f"Jupiter (putrakaraka) - {_condition('Jupiter', r) or 'not placed'}; "
            f"navamsa dignity {core.putrakaraka_navamsa_dignity} (the "
            f"redemptive/annihilation signal the D-7 section reads)")
        reframe = next((n.text for n in sr.notes
                        if "classical shorthand" in n.text), "")
    except Exception:  # noqa: BLE001 — Track-B sparse
        pass
    return ChildrenChapter(
        combos_quote=_pull(_H1, CHILDREN_COMBOS) or "",
        significations=tuple((sv.signification, f"{sv.verdict} ({sv.degree})")
                             for sv in pf5.significations),
        fired_rules=tuple(fired), timing_windows=windows, verdict=pf5.rollup,
        d7_corroboration=d7_row, putrakaraka_line=jup_line, reframe_note=reframe)


# ── v27 Psychological profile ───────────────────────────────────────────────────


@dataclass(frozen=True)
class PsychProfile:
    lagna_quote: tuple[str, str]            # HPA-18 verbatim + cite
    moon_state: str                         # manas karaka (dignity + afflictions)
    temperament: Optional[str]              # strongest-planet line (ruler card)
    nature_stamp: Optional[str]             # who stamps nature/appearance
    atmakaraka: Optional[str]
    woven: str                              # the composed profile (guard-safe)
    # ── mind-stack completions (2026-08-18 report-critique, append-only): the Moon's
    # per-sign mental disposition (the SAME fired H1.M.* rule the Aptitude chapter
    # re-reads, HTJAH-I:1452), a Mercury (buddhi) condition line composed from its
    # computed state, and the cross-reference to Deeptadi's Moon row. Defaults keep
    # every existing construction unchanged. ─────────────────────────────────────────
    moon_mind: tuple[tuple[str, str, str], ...] = ()   # fired H1.M.* (id, text, cite)
    mercury_line: str = ""                             # buddhi condition (computed)
    deeptadi_moon: str = ""                            # Moon's avastha cross-reference
    # v36 (2026-08-19, corpus-unblocked): Raman's affliction-to-the-mind screen. The
    # audit marked this FOR CORPUS VERIFICATION and it was never implemented; the
    # anchors are now verified. Reported in the classical indication register with his
    # own caution attached — never as a diagnosis, and never in the decree voice.
    mind_screen: tuple[tuple[str, str, str], ...] = ()   # (name, finding, cite)
    mind_caution: str = ""                               # Raman's own hedge, verbatim


def build_psych_profile(r: "DetailedReport") -> Optional[PsychProfile]:
    from app.raman_saab.judges.trimsamsa_health_reading import (
        build_trimsamsa_health_reading)
    from app.raman_saab.primitives.chara_karakas import chara_karakas
    from app.raman_saab.raman_style import conclusion, weighed

    asc = r.chart.asc_sign
    rng = LAGNA_BLOCKS.get(asc)
    if rng is None:
        return None
    cite = f"HPA-18:{rng[0]}"
    # REPORT COMPLETENESS: the Moon state, temperament, nature stamp and AK below are
    # COMPUTED — a missing verbatim pull (corpus not vendored on this machine) must never
    # hide them. The honest-absence line flows through the existing quote field, so every
    # renderer shows the chapter unchanged.
    quote = _pull("HPA-18", rng) or (
        f"lagna portrait at {cite} - corpus not mounted on this machine")
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
    # the Moon's per-sign mental disposition — a RE-READ of the same fired H1.M.* rule
    # (HTJAH-I:1452) the Aptitude chapter shows; the psych chapter is its natural home
    try:
        moon_mind = _fired_moon_mind(r.proformas[0]) if r.proformas else ()
    except Exception:  # noqa: BLE001
        moon_mind = ()
    # Mercury (buddhi) — Raman's mind is Moon (manas) AND Mercury (buddhi); composed
    # from Mercury's computed condition + the drishti it receives, no new judgment
    mercury_line = ""
    merc_cond = _condition("Mercury", r)
    if merc_cond is not None:
        from app.raman_saab.doctrine.drishti import aspecting_planets
        asp = aspecting_planets("Mercury", r.chart)
        mercury_line = (f"the Moon carries the manas (mind) and Mercury the buddhi "
                        f"(intellect): Mercury stands {merc_cond}, "
                        + (f"aspected by {', '.join(asp)}" if asp
                           else "aspected by no planet"))
    # cross-reference to the Deeptadi section's Moon row (state + Raman's result phrase)
    deeptadi_moon = ""
    try:
        from app.raman_saab.primitives.deeptadi import RESULTS as _DR
        from app.raman_saab.primitives.deeptadi import state as _dstate
        _ms = _dstate("Moon", r.chart)
        deeptadi_moon = (f"Moon {_ms} — {_DR[_ms][1]} (HPA Ch.7:46-83; full per-planet "
                         f"table in the Deeptadi avasthas section)")
    except Exception:  # noqa: BLE001
        pass
    woven = weighed(
        "the rising sign's own portrait, the Moon's state, the strongest planet's "
        "temperament and the Atmakaraka together",
        "the profile below describes the method's reading of the mind — tendencies in "
        "Raman's descriptive idiom, never a diagnosis")
    woven += " " + conclusion(
        "each thread is quoted or re-read from its own section; nothing here is a new "
        "judgment")
    # ── v36: Raman's affliction-to-the-mind screen (corpus-verified 2026-08-19) ──
    # Two anchors, both mechanical, reported as SCREENS — present or absent — in the
    # classical indication register. Raman's own hedge on this material travels with
    # them and is not droppable: "In all these cases, a careful weighing of the pros and
    # cons of the affliction or fortification is absolutely necessary. No slip-shod
    # interpretation should be made and a premature conclusion arrived at."
    # (HTJAH-I:4297-4299). His wording for the first is "the native WILL SUFFER FROM
    # mental disorders"; that is his voice for a combination, and this engine does not
    # repeat it as a claim about the reader — the screen states that the configuration is
    # present, names it, and stops. Nothing here diagnoses.
    _mind: list[tuple[str, str, str]] = []
    try:
        _ch = r.chart
        _moon = _ch.planets.get("Moon")
        _rahu = _ch.planets.get("Rahu")
        if _moon is not None and _rahu is not None:
            from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS
            _moon_h = int(getattr(_moon, "rasi_house", 0) or 0)
            _with_malefic = sorted(
                n for n, pl in _ch.planets.items()
                if n in NATURAL_MALEFICS and n != "Moon"
                and int(getattr(pl, "rasi_house", 0) or 0) == _moon_h)
            _rahu_h = int(getattr(_rahu, "rasi_house", 0) or 0)
            if _with_malefic and _rahu_h in (5, 8, 12):
                _mind.append((
                    "Moon with a malefic, Rahu in the 5th/8th/12th",
                    f"present: the Moon shares house {_moon_h} with "
                    f"{', '.join(_with_malefic)}, and Rahu stands in house {_rahu_h}. "
                    f"Raman gives this combination for disturbance of mind; it is a "
                    f"classical configuration, not a finding about this reader.",
                    "HTJAH-I:10077-10078"))
            else:
                _mind.append((
                    "Moon with a malefic, Rahu in the 5th/8th/12th",
                    "absent: the configuration does not form on this chart. Reported "
                    "either way, so a silent screen is not mistaken for one not run.",
                    "HTJAH-I:10077-10078"))
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        _mind = []
    _mind_caution = (
        "In all these cases, a careful weighing of the pros and cons of the affliction "
        "or fortification is absolutely necessary. No slip-shod interpretation should be "
        "made and a premature conclusion arrived at. (HTJAH-I:4297-4299 — Raman's own "
        "caution on affliction readings of this kind.) These are classical combinations "
        "reported as present or absent; nothing here is a diagnosis or a statement about "
        "this reader's health." if _mind else "")
    return PsychProfile(
        mind_screen=tuple(_mind),
        mind_caution=_mind_caution,
        lagna_quote=(quote, cite),
        moon_state=moon,
        temperament=r.ruler.temperament,
        nature_stamp=r.ruler.stamps_nature,
        atmakaraka=ak,
        woven=woven,
        moon_mind=moon_mind,
        mercury_line=mercury_line,
        deeptadi_moon=deeptadi_moon)


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
