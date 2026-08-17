"""Wave B (v28-v29): the decade indication timeline and the full life synthesis.

PURE RE-READS (PREC-10). Two recorded deviations from the user's naming (Measured-Truth):
the proposal's "event probability timeline" renders as the DECADE INDICATION TIMELINE —
the method's indications per decade, never probabilities of life events (this project's
real-outcome validation measured no predictive power, so probability language would be a
false claim) — and every sentence stays inside the guard's descriptive idiom.

v28 — decades from birth, sliced over the ALREADY-BUILT windowed timeline: the MD lords
running, the life-areas activated (education H4/H5, family H2/H4, health H6/H8, wealth
H2/H11 — the same house->area names the report uses), the yogas ripening, the leans, and
the tension notes. Decades outside the displayed window say so — nothing is invented.

v29 — the biography-closing chapter: temperament, destiny, career, wealth, marriage,
children, spiritual thread, reputation, health, turning points, dominant themes — every
paragraph WEAVES values the report already computed (a defect test asserts each claim's
key value appears in its source field; a synthesis contradicting its source is a defect,
never a reading).

Usage:
    from app.raman_saab.life_arc import build_decade_timeline, build_life_synthesis
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_DAYS_PER_YEAR: Final[float] = 365.2425

#: house -> the life-area word the report already uses (the dashboard vocabulary).
_AREA: Final[dict[int, str]] = {
    1: "self & health", 2: "family & wealth", 3: "courage & siblings", 4: "home, mother "
    "& education", 5: "children & intellect", 6: "health & rivals", 7: "marriage & "
    "partnerships", 8: "longevity matters", 9: "fortune & dharma", 10: "career & "
    "status", 11: "gains & friends", 12: "expenditure & foreign",
}


@dataclass(frozen=True)
class DecadeReading:
    label: str                              # e.g. "1989-1999 (ages 0-10)"
    inside_window: bool
    md_lords: tuple[str, ...]
    areas_favourable: tuple[str, ...]       # area (house, tier) — natal-favourable, lit
    areas_challenged: tuple[str, ...]       # natal-afflicted houses lit in the decade
    yogas_ripening: tuple[str, ...]
    leans: tuple[str, ...]                  # MD Ishta/Kashta leans present
    note: str


@dataclass(frozen=True)
class DecadeTimeline:
    decades: tuple[DecadeReading, ...]
    frame: str                              # the honesty frame, rendered with the section


_FRAME: Final[str] = (
    "Indications per decade — how the method reads each stretch, sliced from the same "
    "windowed timeline shown above; never a probability of any life event (the project's "
    "own validation measured no real-outcome signal). Decades outside the displayed "
    "window are labeled, not guessed.")


def build_decade_timeline(r: "DetailedReport") -> Optional[DecadeTimeline]:
    from app.raman_saab.render import _jd_to_date
    b = r.birth
    try:
        import swisseph as swe
        birth_jd = swe.julday(b.year, b.month, b.day,
                              b.hour + b.minute / 60.0 - b.tz_offset, swe.GREG_CAL)
    except Exception:  # noqa: BLE001
        return None
    if not r.life_chapters.chapters:
        return None
    win_lo = min(ch.start_jd for ch in r.life_chapters.chapters)
    win_hi = max(ch.end_jd for ch in r.life_chapters.chapters)
    out: list[DecadeReading] = []
    for k in range(0, 9):                                   # ages 0..90
        lo = birth_jd + k * 10 * _DAYS_PER_YEAR
        hi = birth_jd + (k + 1) * 10 * _DAYS_PER_YEAR
        label = f"{b.year + k * 10}-{b.year + (k + 1) * 10} (ages {k * 10}-{(k + 1) * 10})"
        if hi <= win_lo or lo >= win_hi:
            out.append(DecadeReading(label, False, (), (), (), (), (),
                                     "outside the displayed timeline window — not read"))
            continue
        mds: list[str] = []
        leans: list[str] = []
        # ONE chip per area per decade (2026-08-17 fix): the old key included the tier, so a
        # house lit in two Mahadashas at different tiers rendered twice ("(H1, limited)" AND
        # "(H1, par excellence)") unexplained. Aggregate per house, keeping EVERY per-MD tier
        # attribution (completeness: nothing dropped, only merged into one chip).
        fav_by_house: dict[int, list[tuple[str, str]]] = {}   # house -> [(tier, maha)]
        chal_by_house: dict[int, list[tuple[str, str]]] = {}
        for ch in r.life_chapters.chapters:
            if ch.end_jd <= lo or ch.start_jd >= hi:
                continue
            if ch.maha not in mds:
                mds.append(ch.maha)
            if ch.lean and ch.lean not in leans:
                leans.append(str(ch.lean))
            for h, tier, natal in ch.houses_lit:
                bucket = (fav_by_house if natal == "favourable"
                          else chal_by_house if natal == "afflicted" else None)
                if bucket is None:
                    continue
                if (tier, ch.maha) not in bucket.setdefault(h, []):
                    bucket[h].append((tier, ch.maha))

        def _chip(h: int, attributions: list[tuple[str, str]]) -> str:
            area = _AREA.get(h, f"house {h}")
            detail = "; ".join(f"{tier} in {maha} MD" for tier, maha in attributions)
            return f"{area} (H{h} - {detail})"

        fav = [_chip(h, attrs) for h, attrs in fav_by_house.items()]
        chal = [_chip(h, attrs) for h, attrs in chal_by_house.items()]
        yogas = []
        for t in r.yoga_timing:
            if t.period_end_jd > lo and t.period_start_jd < hi:
                tag = f"{t.yoga_name} ({t.planet} {t.role})"
                if tag not in yogas:
                    yogas.append(tag)
        partial = " (decade partially inside the window)" if lo < win_lo or hi > win_hi \
            else ""
        out.append(DecadeReading(label, True, tuple(mds), tuple(fav), tuple(chal),
                                 tuple(yogas), tuple(leans),
                                 f"read from the windowed timeline{partial}"))
    return DecadeTimeline(decades=tuple(out), frame=_FRAME)


# ── v29 Full life synthesis ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class LifeSynthesis:
    paragraphs: tuple[tuple[str, str], ...]     # (theme, woven paragraph)
    closing: str


def build_life_synthesis(r: "DetailedReport") -> Optional[LifeSynthesis]:
    from app.raman_saab.raman_style import conclusion

    paras: list[tuple[str, str]] = []

    def _add(theme: str, text: str) -> None:
        if text.strip():
            paras.append((theme, text.strip()))

    ps = r.psych
    if ps is not None:
        _add("Temperament",
             f"The rising sign's portrait opens the story (quoted in full in the "
             f"Psychological profile), with {ps.moon_state or 'the Moon as manas'}"
             + (f"; the strongest planet's temperament reads: {ps.temperament}"
                if ps.temperament else "") + ".")
    if r.nichod.essence:
        _add("Destiny", f"The Nichod's own distillation stands as the destiny line: "
                        f"{r.nichod.essence}")
    pf = r.profession
    if pf is not None and pf.convergent:
        conv = ", ".join(w for w, _n in pf.convergent[:4])
        _add("Career", f"Across every derivation the profession synthesis runs, the "
                       f"convergent trades are {conv} — the method's occupational "
                       f"emphasis, counted, not judged anew.")
    w = r.wealth
    if w is not None and w.rows:
        first = w.rows[0]
        _add("Wealth", f"The wealth chapter reads the channels rather than one verdict; "
                       f"its leading channel: {first.channel} — {first.reading}.")
    m = r.marriage
    if m is not None:
        _add("Marriage", f"The seventh house's headline stands {m.verdict}, with "
                         f"{len(m.fired_kalatra)} kalatra rule(s) firing; the monograph "
                         f"carries Raman's own words for the placement.")
    c = r.children
    if c is not None:
        _add("Children", f"The fifth house reads {c.verdict}; the chapter quotes the "
                         f"classical combination block whole.")
    a = r.arishta
    if a is not None:
        _add("Protections", f"On the arishta side: {a.kemadruma_note}; the band is "
                            f"{a.band}.")
    if len(r.proformas) >= 10:
        sh = next((sv for sv in r.proformas[9].significations
                   if sv.signification == "status_honour"), None)
        if sh is not None:
            _add("Reputation", f"Status and honour (H10) read {sh.verdict} "
                               f"({sh.degree}).")
    h = r.health_readout
    if h is not None and h.rows:
        _add("Health", f"The health read-out's headline rows: "
             + "; ".join(f"{row.area} {row.verdict}" for row in h.rows[:3]) + ".")
    if r.nichod.turning_points:
        _add("Turning points", "Where the period lean changes: "
             + "; ".join(f"{when} — {what}" for when, what in r.nichod.turning_points)
             + ".")
    if r.planet_bios:
        dom = r.planet_bios[0]
        _add("Dominant themes", f"{dom.planet} drives more of this chart's computed "
                                f"readings than any other ({dom.census_count} "
                                f"connections); its themes run through every chapter "
                                f"above.")
    if not paras:
        return None
    closing = conclusion(
        "this synthesis introduces no judgment of its own — every line re-reads a "
        "chapter above, and where two chapters pull differently the How-to-read rules "
        "govern; a synthesis contradicting its source would be a defect, never a reading")
    return LifeSynthesis(paragraphs=tuple(paras), closing=closing)
