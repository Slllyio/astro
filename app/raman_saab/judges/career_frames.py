"""The 10th house reckoned from all three centres — Lagna, the Moon and the Sun.

`primitives/career.py` reckons the 10th from the LAGNA only, so the profession chapter has
been reading one of Raman's three reference frames and silently dropping the other two.
The audit logged this as corpus-gated because the three-frame rule needed a verified
citation before it could be encoded. With the corpus mounted the passage is in hand and
states the rule plainly:

    "The 10th house should be reckoned not only from Lagna but also from the Moon and the
    Sun. It is also common experience that the reckoning made from the strongest of these
    three centers gives good results in judging occupation."   (HTJAH-I:13960-13962)

Two further clauses of the same passage are encoded with it, because they govern how the
three frames combine and omitting them would leave the rule half-applied:

  * the BLENDING clause — "when the different planets are more or less of equal strength,
    then there will he a blending of influences and more than one occupation may he
    indicated" (HTJAH-I:13957-13959). Near-equal centres do not produce one answer; they
    produce several, and the reading says so instead of forcing a winner.
  * Raman's own caution one line earlier: "These principles are very general and must he
    adapted suitably" (HTJAH-I:13959-13960). It travels with the output.

HOW "STRONGEST" IS MEASURED, and what part of that is ours. Raman's worked example (Chart
115, HTJAH-I:13974-13981) reasons qualitatively — the Lagna holds its own lord Jupiter, the
Sun is exalted with Mercury and Venus, the Moon's sign is aspected by Saturn, and the Lagna
"would emerge the strongest of the three". But five lines later he prints a NUMERIC
comparison of exactly the two quantities this module uses: "the Ascendant (10 2 rupas) is
more powerfully than the Moon (8.8 rupas)" (HTJAH-I:13986) — an ascendant BHAVA BALA set
against a graha SHADBALA, in rupas. Mixing those two measures is therefore his own
precedent, not an invention here; the reading discloses which measure each centre is
carrying so the comparison is never mistaken for like-for-like.

What IS ours and is labelled as ours: the numeric threshold below which two centres count
as "more or less of equal strength". Raman gives no figure. `_BLEND_TOLERANCE` is the
engine's own convention, named and cited to nothing — the same treatment the deeptadi
precedence ordering carries.

WHAT THIS IS NOT. Not a verdict. The H10 career verdict remains Raman's rasi judgment
through `house_template`; this reports the three reckonings, names which centre is
strongest, and shows where they converge. Convergence across frames is the real signal —
in Raman's own worked example Mars recurs from the Lagna, from the Moon and from the Sun
("ruled by Mars again"), and that repetition is what carries the reading.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path. The golden ratchet
is untouched by construction, and a test enforces it.

Usage:
    from app.raman_saab.judges.career_frames import build_career_frames
    cf = build_career_frames(report)
    cf.frames        # one per centre: Lagna, Moon, Sun
    cf.strongest     # the centre Raman would reckon from
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.career import (CAREER_BY_SIGN,
                                              TRADE_BY_NAVAMSA_DISPOSITOR)
from app.raman_saab.primitives.dispositor import navamsa_lord_of

_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_NODES: Final[frozenset[str]] = frozenset({"Rahu", "Ketu"})

CITE_THREE_CENTRES: Final[Citation] = Citation("HTJAH-I", 13960)
CITE_BLENDING: Final[Citation] = Citation("HTJAH-I", 13957)
CITE_WORKED_EXAMPLE: Final[Citation] = Citation("HTJAH-I", 13974)
CITE_RUPAS_PRECEDENT: Final[Citation] = Citation("HTJAH-I", 13986)

#: Raman's rule, verbatim (HTJAH-I:13960-13962).
RULE: Final[str] = (
    "The 10th house should be reckoned not only from Lagna but also from the Moon and the "
    "Sun. It is also common experience that the reckoning made from the strongest of these "
    "three centers gives good results in judging occupation."
)

#: The blending clause, verbatim (HTJAH-I:13957-13959), OCR intact.
BLENDING_RULE: Final[str] = (
    "when the different planets are more or less of equal strength, then there will he a "
    "blending of influences and more than one occupation may he indicated"
)

#: Raman's own caution on the whole passage (HTJAH-I:13959-13960).
CAUTION: Final[str] = (
    "These principles are very general and must he adapted suitably (HTJAH-I:13959) — "
    "Raman's own caution on this passage, carried with its output."
)

#: How close two centres must be in rupas to count as "more or less of equal strength".
#: ENGINE CONVENTION, NOT RAMAN: he states the blending clause but gives no figure, so a
#: threshold had to be chosen and is labelled rather than presented as his. 10% of the
#: strongest centre — wide enough that the near-ties he describes register, narrow enough
#: that a clearly dominant centre still wins outright.
_BLEND_TOLERANCE: Final[float] = 0.10

_STRENGTH_BASIS: Final[dict[str, str]] = {
    "Lagna": "bhava bala of the 1st house",
    "Moon": "shadbala of the Moon",
    "Sun": "shadbala of the Sun",
}


@dataclass(frozen=True)
class CareerFrame:
    """The 10th reckoned from ONE of Raman's three centres."""
    centre: str                      # "Lagna" | "Moon" | "Sun"
    centre_sign: int
    centre_sign_name: str
    tenth_sign: int
    tenth_sign_name: str
    tenth_lord: str
    tenth_lord_house: int
    navamsa_dispositor: str
    trade: str                       # "" when the dispositor carries no trade entry
    sign_career: str
    strength_rupas: float
    strength_basis: str
    is_strongest: bool
    note: str                        # why a field is empty, when one is


@dataclass(frozen=True)
class CareerFrames:
    """All three reckonings, which centre is strongest, and where they agree."""
    frames: tuple[CareerFrame, ...]
    strongest: str
    strongest_why: str
    blended: bool
    blended_note: str
    convergent: tuple[tuple[str, int], ...]   # trade word -> how many centres name it
    convergence_note: str
    leading_indication: str
    rule: str
    blending_rule: str
    caution: str
    citation: str


def _sign_name(sign: int) -> str:
    return _SIGNS[sign - 1] if 1 <= sign <= 12 else f"sign {sign}"


def _tenth_from(sign: int) -> int:
    return ((sign - 1) + 9) % 12 + 1


def _trade_tokens(trade: str) -> set[str]:
    """The comparable words in a trade string — the same tokenisation the profession
    synthesis already uses for its convergence tally, so the two agree by construction."""
    return {w.strip().lower()
            for part in trade.split(",")
            for w in [part.split("&")[0]]
            if len(w.strip()) > 3}


def build_career_frames(r) -> Optional[CareerFrames]:
    """Reckon the 10th from Lagna, Moon and Sun per HTJAH-I:13960-13962.

    None on a chart where no centre resolves (sparse Track-B). A centre whose luminary is
    absent is skipped rather than faked — Raman names three, and reporting a frame the
    chart cannot support would be an invention.
    """
    chart = getattr(r, "chart", None)
    if chart is None:
        return None
    asc = int(getattr(chart, "asc_sign", 0) or 0)
    if not 1 <= asc <= 12:
        return None

    # the strength of each centre, in rupas (virupas / 60), from what the report already
    # computed — a re-read, never a new measurement.
    strengths: dict[str, float] = {}
    for row in getattr(r, "house_strength", ()) or ():
        if getattr(row, "house", None) == 1 and getattr(row, "bhava_bala", None):
            strengths["Lagna"] = float(row.bhava_bala) / 60.0
    for lum in ("Moon", "Sun"):
        p = chart.planets.get(lum)
        sb = getattr(p, "shadbala_rupas", None) if p is not None else None
        total = getattr(sb, "total", None)
        if total:
            strengths[lum] = float(total) / 60.0

    centres: list[tuple[str, int]] = [("Lagna", asc)]
    for lum in ("Moon", "Sun"):
        p = chart.planets.get(lum)
        if p is not None and 1 <= int(getattr(p, "sign", 0) or 0) <= 12:
            centres.append((lum, int(p.sign)))
    if not centres:
        return None

    # `strengths` is empty on a chart that carries neither a bhava bala for the first house
    # nor a shadbala for either luminary. Every centre then scores 0.0, `max` returns whichever
    # was appended first, and the reading prints "Lagna carries 0.0 rupas ..., the highest of
    # the three centres" — a ranking produced by list order and presented as a measurement.
    # This module's own contract is that a centre the chart cannot support would be an
    # invention, so the comparison is withheld instead of decided.
    measured = bool(strengths)
    strongest = max(centres, key=lambda c: strengths.get(c[0], 0.0))[0] if measured else ""
    top = strengths.get(strongest, 0.0)

    frames: list[CareerFrame] = []
    for centre, csign in centres:
        tenth = _tenth_from(csign)
        lord = SIGN_LORDS[tenth]
        lp = chart.planets.get(lord)
        nav = navamsa_lord_of(lord, chart) if lp is not None else ""
        trade = TRADE_BY_NAVAMSA_DISPOSITOR.get(nav, "")
        note = ""
        if lp is None:
            note = (f"the 10th lord {lord} is not present on this chart, so the "
                    f"navamsa-dispositor technique cannot run from this centre")
        elif nav in _NODES:
            note = (f"the navamsa dispositor is {nav}; Raman's vocation table covers the "
                    f"seven visible grahas and gives the nodes no trade, so this centre "
                    f"names no occupation. Reported rather than skipped.")
        frames.append(CareerFrame(
            centre=centre,
            centre_sign=csign,
            centre_sign_name=_sign_name(csign),
            tenth_sign=tenth,
            tenth_sign_name=_sign_name(tenth),
            tenth_lord=lord,
            tenth_lord_house=int(getattr(lp, "rasi_house", 0) or 0) if lp is not None else 0,
            navamsa_dispositor=nav,
            trade=trade,
            sign_career=CAREER_BY_SIGN.get(tenth, ""),
            strength_rupas=round(strengths.get(centre, 0.0), 2),
            strength_basis=_STRENGTH_BASIS.get(centre, ""),
            is_strongest=(measured and centre == strongest),
            note=note))

    # the blending clause: centres within the tolerance of the top are "more or less of
    # equal strength", so the reading reports several occupations rather than one.
    near = [f.centre for f in frames
            if top > 0 and abs(top - strengths.get(f.centre, 0.0)) <= top * _BLEND_TOLERANCE]
    blended = len(near) > 1
    blended_note = ""
    if blended:
        blended_note = (
            f"{' and '.join(near)} are within {int(_BLEND_TOLERANCE * 100)}% of one another "
            f"in rupas, which is Raman's \"more or less of equal strength\" case: he expects "
            f"a blending of influences and more than one occupation to be indicated "
            f"(HTJAH-I:13957-13959), so the frames below are read together rather than "
            f"resolved to a single answer. The 10% figure is the ENGINE's convention — "
            f"Raman states the clause but gives no number.")

    counts: dict[str, int] = {}
    for f in frames:
        for tok in _trade_tokens(f.trade):
            counts[tok] = counts.get(tok, 0) + 1
    convergent = tuple(sorted(((w, n) for w, n in counts.items() if n >= 2),
                              key=lambda x: (-x[1], x[0])))
    if convergent:
        convergence_note = (
            f"{len(convergent)} trade word(s) are named from more than one centre. In "
            f"Raman's own worked example the convergence IS the reading — the dispositor "
            f"resolves to Mars from the Lagna, from the Moon and from the Sun alike "
            f"(\"ruled by Mars again\", HTJAH-I:13974-13976).")
    else:
        convergence_note = ("No trade word is named from more than one centre — the three "
                           "reckonings point in different directions, which is itself a "
                           "finding and is reported rather than resolved.")

    lead = next((f for f in frames if f.is_strongest), frames[0])
    leading = (lead.trade or lead.sign_career
               or "no occupation is named from this centre")
    return CareerFrames(
        frames=tuple(frames),
        strongest=strongest,
        strongest_why=(
            f"{strongest} carries {round(top, 2)} rupas ({_STRENGTH_BASIS.get(strongest, '')}), "
            f"the highest of the three centres. Raman compares an ascendant bhava bala "
            f"against a graha shadbala in exactly this way at HTJAH-I:13986, so the mixed "
            f"basis is his precedent; each centre's own measure is named beside it."
            if measured else
            "This chart carries no strength measure for any of the three centres, so no centre "
            "can be ranked. All three reckonings are reported side by side and none is "
            "preferred — Raman ranks by strength, and without a strength there is no ranking "
            "to report."),
        blended=blended,
        blended_note=blended_note,
        convergent=convergent,
        convergence_note=convergence_note,
        leading_indication=leading,
        rule=RULE,
        blending_rule=BLENDING_RULE,
        caution=CAUTION,
        citation=f"{CITE_THREE_CENTRES.work}:{CITE_THREE_CENTRES.line}-13962")
