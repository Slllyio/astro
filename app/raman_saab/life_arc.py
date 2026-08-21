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
class DecadeAreaRow:
    """One life-area's reading in one decade, laid out as a grid row.

    The same facts as the matching entry in `areas_favourable` / `areas_challenged`,
    but taken apart so a renderer can put ONE AREA ON ONE ROW and each running
    Mahadasha in its own column. The chip form chains every area into a single
    semicolon-run — measured at 338 words per "sentence", the densest line in the
    whole report — which is a shape problem, not a wording one.
    """
    house: int
    area: str
    #: one entry per lord in `DecadeReading.md_lords`, SAME ORDER; "" where that
    #: Mahadasha does not light this house. Several tiers in one Mahadasha join
    #: with " / " rather than being dropped.
    grades: tuple[str, ...]


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
    #: the same two chip lists as a grid (area x Mahadasha). Append-only, defaulted
    #: so the two positional constructions above stay valid.
    favourable_grid: tuple[DecadeAreaRow, ...] = ()
    challenged_grid: tuple[DecadeAreaRow, ...] = ()


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

        def _grid(by_house: dict[int, list[tuple[str, str]]]) -> tuple[DecadeAreaRow, ...]:
            """The chips' own data, one row per area and one column per running MD."""
            rows: list[DecadeAreaRow] = []
            for h, attrs in by_house.items():
                per_md: dict[str, list[str]] = {}
                for tier, maha in attrs:
                    per_md.setdefault(maha, []).append(tier)
                rows.append(DecadeAreaRow(
                    house=h, area=_AREA.get(h, f"house {h}"),
                    grades=tuple(" / ".join(per_md.get(m, ())) for m in mds)))
            return tuple(rows)

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
                                 f"read from the windowed timeline{partial}",
                                 favourable_grid=_grid(fav_by_house),
                                 challenged_grid=_grid(chal_by_house)))
    return DecadeTimeline(decades=tuple(out), frame=_FRAME)


# ── v29 Full life synthesis ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class LifeSynthesis:
    paragraphs: tuple[tuple[str, str], ...]     # (theme, woven paragraph)
    closing: str


def build_life_synthesis(r: "DetailedReport") -> Optional[LifeSynthesis]:
    from app.raman_saab.detailed_report import _joined_names, period_pairing
    from app.raman_saab.raman_style import conclusion

    paras: list[tuple[str, str]] = []

    def _add(theme: str, text: str) -> None:
        if text.strip():
            paras.append((theme, text.strip()))

    def _ripens(houses: tuple[int, ...]) -> str:
        """Raman's pair-indication-with-period discipline (HTJAH-I:1586-1596, the locked
        timer doctrine): the MD lords whose chapters most light the theme's houses — a
        pure re-read of the graded life-chapters; '' when nothing in the window lights
        them. Timed-indication idiom only."""
        lords, span = period_pairing(r, houses)
        if not lords:
            return ""
        word = "chapter" if len(lords) == 1 else "chapters"
        return (f" These matters ripen most fully under the {_joined_names(lords)} "
                f"{word} ({span}; HTJAH-I:1586-1596).")

    ps = r.psych
    if ps is not None:
        # Wave-2: the dual-frame clause — when the Moon's frame is the stronger, the
        # psychological read says so (HTJAH-I:645-646, the Chart-signature re-read).
        frame_bit = ("; the psychological read is weighed from the Moon's sign, the "
                     "stronger frame in this chart (HTJAH-I:645-646)"
                     if r.overview.stronger_frame == "moon" else "")
        _add("Temperament",
             f"The rising sign's portrait opens the story (quoted in full in the "
             f"Psychological profile), with {ps.moon_state or 'the Moon as manas'}"
             + (f"; the strongest planet's temperament reads: {ps.temperament}"
                if ps.temperament else "") + frame_bit + ".")
    # Wave-2 rebuild: Destiny carries its own distinct clause — identity + longevity band
    # + governing factor — instead of pasting the whole Nichod essence (which stays
    # complete in the Nichod itself, so nothing computed is hidden).
    if r.nichod.identity:
        gov = f"the ruler of the nativity is {r.ruler.lagna_lord}"
        if r.ruler.strongest is not None:
            gov += (" - itself the strongest planet" if r.ruler.coincide
                    else f"; the strongest planet by Shadbala is {r.ruler.strongest}")
        _add("Destiny",
             f"{r.nichod.identity}. Longevity reads at the {r.longevity_class} band, and "
             f"{gov} (HTJAH-I:16001-16002). The full distillation stands complete in the "
             f"Nichod below.")
    pf = r.profession
    if pf is not None and pf.convergent:
        conv = ", ".join(w for w, _n in pf.convergent[:4])
        _add("Career", f"Across every derivation the profession synthesis runs, the "
                       f"convergent trades are {conv} — the method's occupational "
                       f"emphasis, counted, not judged anew.{_ripens((10,))}")
    w = r.wealth
    if w is not None and w.rows:
        first = w.rows[0]
        _add("Wealth", f"The wealth chapter reads the channels rather than one verdict; "
                       f"its leading channel: {first.channel} — {first.reading}."
                       f"{_ripens((2, 11))}")
    m = r.marriage
    if m is not None:
        # Wave-2 rebuild: re-read the CONTENT (lord placement + fired kalatra count),
        # not the fact that a monograph exists.
        lord_bit = (f"; the seventh lord sits in house {m.lord_placement_house}"
                    if m.lord_placement_house else "")
        _add("Marriage", f"The seventh house's headline stands {m.verdict}{lord_bit}, "
                         f"with {len(m.fired_kalatra)} kalatra rule(s) firing on the "
                         f"placement.{_ripens((7,))}")
    c = r.children
    if c is not None:
        # Wave-2 rebuild: name the fifth house's own decided matters instead of pointing
        # at the chapter's quotation block.
        sig_bits = "; ".join(f"{k} {v}" for k, v in c.significations[:3])
        _add("Children", f"The fifth house reads {c.verdict}"
                         + (f" — its decided matters: {sig_bits}" if sig_bits else "")
                         + f".{_ripens((5,))}")
    a = r.arishta
    if a is not None:
        _add("Protections", f"On the arishta side: {a.kemadruma_note}; the band is "
                            f"{a.band}.")
    if len(r.proformas) >= 10:
        sh = next((sv for sv in r.proformas[9].significations
                   if sv.signification == "status_honour"), None)
        if sh is not None:
            _add("Reputation", f"Status and honour (H10) read {sh.verdict} "
                               f"({sh.degree}).{_ripens((10,))}")
    h = r.health_readout
    if h is not None and h.rows:
        _add("Health", f"The health read-out's headline rows: "
             + "; ".join(f"{row.area} {row.verdict}" for row in h.rows[:3]) + "."
             + _ripens((6, 8)))
    if r.nichod.turning_points:
        _add("Turning points", "Where the period lean changes: "
             + "; ".join(f"{when} — {what}" for when, what in r.nichod.turning_points)
             + ".")
    # Wave-2: the Present chapter — the running MD/AD, its tier and the houses it lights
    # (a re-read of the Nichod's current_period line), the one thing a biography-shaped
    # closing pass must never omit.
    cur_period = r.nichod.current_period
    if cur_period and not cur_period.startswith("no running period"):
        cur = next((ch for ch in r.life_chapters.chapters if ch.is_current), None)
        lean_bit = (f", on a {cur.lean} Ishta/Kashta lean" if cur is not None and cur.lean
                    else "")
        _add("Present chapter",
             f"The chapter running now: {cur_period}{lean_bit} — re-read from the "
             f"Life-narrative's own four-tier grading (HTJAH-I:1592-1596), a timing "
             f"lens, never an event.")
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
