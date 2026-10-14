"""The Sitting — the reading as one continuous piece, in Raman's own compositional arc.

The report has 54 sections and, until now, no single place where the chart is READ the way an
astrologer reads it: as one story with a thesis, characters, and a close that answers the
opening. The gap was measured before this was written (one generated reading): the honesty
hedge restated 26 times, "Jupiter" named 211 times with no accumulated identity, zero backward
references, and timing prose that puts the mechanism before the life.

The arc here is hand-derived from Raman's own worked readings in *Notable Horoscopes* — his
compositional practice, observed and imitated, never claimed as doctrine:

1. he opens on who this is and what the chart rests on;
2. he names the striking feature early (his "Special Features" openings; "Mark the fact"
   itself recurs THROUGHOUT his readings, mostly inside Important Events — the early-feature
   move is carried by the openings, per the doctrine review's reading of NH);
3. his planets are characters with earned epithets ("Gnanakaraka Jupiter", "the philosophical
   planet Saturn"), and he refers back to them ("both together again constituting another…");
4. he tells the life forward, event first, chart cause second;
5. he closes with a character sketch that answers the opening.

PREC-10 absolutely: every sentence re-voices a value already decided elsewhere in the report.
Nothing here judges, ranks, or predicts; the composition is deterministic; every paragraph is
guard-checked by test. The Measured-Truth frame is stated ONCE, in the section preamble — this
section speaks freely inside that frame rather than re-hedging every sentence (user decision,
2026-08-07).

Usage:
    from app.raman_saab.sitting import build_sitting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Optional

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

#: The matter each house speaks for in this telling — mirrors plainspoken.HOUSE_MATTER's
#: intent but phrased for narrative, not dashboard lookup.
_HOUSE_STORY: Final[dict[int, str]] = {
    1: "the person themselves", 2: "money and family", 3: "siblings and courage",
    4: "home and mother", 5: "children", 6: "health and rivals", 7: "marriage",
    8: "the hidden and inherited", 9: "father and fortune", 10: "career and standing",
    11: "gains", 12: "expense and retreat",
}


@dataclass(frozen=True)
class CastMember:
    """A graha as a character: the epithet is EARNED — every clause of it is a computed fact,
    listed in `basis` so a reader (or a test) can check the earning."""

    planet: str
    epithet: str
    basis: tuple[str, ...]
    #: the epithet's individual clauses, so a callback can use the ones that are not circular
    #: for its own context (Jupiter "strongest AND deciding voice in house 8" must still be
    #: callable-back in house 8 — by its strength, not by the clause house 8 earned).
    clauses: tuple[str, ...] = ()


@dataclass(frozen=True)
class Sitting:
    grip: str
    cast: tuple[CastMember, ...]
    paragraphs: tuple[tuple[str, str], ...]      # (heading, text)
    closing: str
    #: the Grip's key phrase, repeated by the closing — tests pin the callback on this
    grip_key: str = ""


# ─── the cast ───────────────────────────────────────────────────────────────────────────────

def _epithet(r: "DetailedReport", planet: str) -> CastMember:
    """Compose one planet's epithet from the roles the report already computed."""
    basis: list[str] = []
    clauses: list[str] = []

    ru = getattr(r, "ruler", None)
    if ru is not None and getattr(ru, "lagna_lord", None) == planet:
        lagna = _SIGNS[r.chart.asc_sign - 1]
        clauses.append(f"lord of the {lagna} Lagna")
        basis.append(f"lagna_lord={planet}")
    if ru is not None and getattr(ru, "strongest", None) == planet:
        rupas = float(getattr(ru, "strongest_rupas", 0.0) or 0.0)
        clauses.append(f"the strongest planet in the chart ({rupas:.1f} rupas)")
        basis.append(f"strongest_by_shadbala={rupas:.2f}")
    ak = getattr(getattr(r, "synthesis", None), "atmakaraka", None)
    if ak == planet:
        # NH's own word with a different referent: Raman's NH prose uses "Atmakaraka" for the
        # NATURAL karaka (the Sun, NH:2556); this reads the engine's locked CHARA AK
        # (strict 7-karaka Jaimini). Named per the doctrine review so nobody takes it as NH
        # usage (PASS-WITH-NOTES finding 4).
        clauses.append("the Atmakaraka, significator of the soul")
        basis.append("atmakaraka")
    governed = [h for h, d in (getattr(r, "dominance", None) or {}).items()
                if getattr(d, "governing", None) == planet]
    if governed:
        houses = " and ".join(f"house {h}" for h in sorted(governed)[:2])
        clauses.append(f"the deciding voice in {houses}")
        basis.append(f"governs={sorted(governed)}")

    bio = next((b for b in getattr(r, "planet_bios", ()) or ()
                if getattr(b, "planet", None) == planet), None)
    census = int(getattr(bio, "census_count", 0) or 0)
    if census:
        basis.append(f"census={census}")

    if not clauses and bio is not None:
        # No headline role — earn the epithet from lordship instead, so two supporting cast
        # members never share the same anonymous line (Victoria's Jupiter and Saturn did).
        lords = tuple(getattr(bio, "lord_of", ()) or ())
        if lords:
            houses = " and ".join(_HOUSE_STORY.get(h, f"house {h}") for h in lords[:2])
            clauses.append(f"lord of {houses}")
            basis.append(f"lord_of={lords}")
    if not clauses and census:
        # tied to the census, which IS in `basis` — the review flagged the earlier
        # "a steady presence" fallback as the one sentence in this module not re-reading a
        # computed value (bphs-doctrine-reviewer, 2026-08-07, PASS-WITH-NOTES finding 2)
        clauses.append(f"named through {census} of the readings below")
    if not clauses:
        clauses.append("one of the grahas this chart keeps returning to")
    return CastMember(planet=planet, epithet=f"{planet}, {clauses[0]}"
                      + ("".join(f" and {c}" for c in clauses[1:2])),
                      basis=tuple(basis), clauses=tuple(clauses[:2]))


def _cast(r: "DetailedReport") -> tuple[CastMember, ...]:
    """The 2-3 grahas that dominate the judgment-graph census. Bios arrive census-ranked;
    the nodes are excluded from the cast — they may dominate a census without being able to
    carry a Raman epithet (no lordship, no Atmakaraka role: the Chara-Karaka lock)."""
    bios = [b for b in (getattr(r, "planet_bios", ()) or ())
            if getattr(b, "planet", "") not in ("Rahu", "Ketu")]
    return tuple(_epithet(r, b.planet) for b in bios[:3])


# ─── the paragraphs ─────────────────────────────────────────────────────────────────────────

def _grip(r: "DetailedReport") -> tuple[str, str]:
    """The thesis: what this chart IS. Returns (text, key_phrase) — the closing repeats the
    key phrase, which is how the callback is made testable rather than asserted."""
    ru = r.ruler
    lagna = _SIGNS[r.chart.asc_sign - 1]
    if getattr(ru, "coincide", False):
        frame = (f"its manner and its force both rest on {ru.lagna_lord}, which rules the "
                 f"rising sign and is also the strongest planet here")
        key = f"{ru.lagna_lord} carrying both the manner and the force"
    else:
        frame = (f"its manner is set by {ru.lagna_lord}, lord of the rising sign, while its "
                 f"force gathers in {ru.strongest}")
        key = f"the manner in {ru.lagna_lord} and the force in {ru.strongest}"

    tail = ""
    if r.distinctive:
        h, e = r.distinctive[0]
        from app.raman_saab.detailed_report import _plain_signification
        tail = (f" What most sets it apart from other charts is "
                f"{_plain_signification(e.signification)} (house {h}) — {e.note}.")
    unsettled = [h for h, v in (r.restraint or {}).items()
                 if getattr(v, "standing", "") == "unsettled"]
    settle = (f" On {_HOUSE_STORY.get(unsettled[0], 'one area')} the chart does not speak "
              f"with one voice, and this reading keeps that open rather than forcing it."
              if unsettled else
              " The chart is unusually consistent with itself — its testimonies agree.")
    return (f"This is a {lagna}-rising chart, and {frame}.{tail}{settle}", key)


def _strikes_first(r: "DetailedReport") -> str:
    if not r.distinctive:
        return ""
    from app.raman_saab.detailed_report import _plain_signification

    # Group by house: three distinctive readings often share one, and three identically-shaped
    # clauses in a row read as a table wearing prose. Rarity is stated once per group.
    by_house: dict[int, list] = {}
    for h, e in list(r.distinctive)[:4]:
        by_house.setdefault(h, []).append(e)
    lines = []
    for h, es in by_house.items():
        plain = [_plain_signification(e.signification) for e in es[:3]]
        names = plain[0] if len(plain) == 1 else f"{', '.join(plain[:-1])} and {plain[-1]}"
        verdicts = {str(e.verdict) for e in es}
        v = verdicts.pop() if len(verdicts) == 1 else "each in its own direction"
        rar = min(e.band_share for e in es)
        lines.append(f"{names} — house {h} — read{'s' if len(es) == 1 else ''} {v}, at a "
                     f"level as few as {rar:.0%} of charts share")
    return (f"Mark first what is rare here, because the common readings say little: "
            f"{'; '.join(lines)}. These readings belong to this chart, not to everyone's.")


def _cast_paragraph(cast: tuple[CastMember, ...]) -> str:
    if not cast:
        return ""
    intros = ". ".join(m.epithet for m in cast)
    lead = cast[0].planet
    count = {1: "One planet carries", 2: "Two planets carry", 3: "Three planets carry"}.get(
        len(cast), f"{len(cast)} planets carry")
    them = "it" if len(cast) == 1 else "them"
    return (f"{count} most of this reading, and it is worth meeting {them} once, properly, "
            f"because everything below returns to {them}. {intros}. When a section below "
            f"turns on one of these, it is the same {lead} or its companions — the same few "
            f"characters in different rooms of the same house.")


def _life_forward(r: "DetailedReport", cast: tuple[CastMember, ...]) -> str:
    """The matters told in the shipped doctrinal order, favourable gathered, difficult named,
    each tied to its governing character where dominance decided one."""
    entries = {e.matter: str(e.verdict).split(" ")[0] for e in r.dashboard.entries}
    # A matter whose house the chart is UNSETTLED on may not be counted plainly either way —
    # the grip has just told the reader the chart does not speak with one voice there, and two
    # paragraphs later listing it among the supported reads as the report contradicting
    # itself. Verdict and firmness are different axes; one continuous reading must honour
    # both at once.
    from app.raman_saab.plainspoken import HOUSE_MATTER
    unsettled_h = {h for h, v in (getattr(r, "restraint", None) or {}).items()
                   if getattr(v, "standing", "") == "unsettled"}
    unsettled_m = {HOUSE_MATTER[h] for h in unsettled_h if h in HOUSE_MATTER}
    good = [m for m, v in entries.items() if v == "favourable" and m not in unsettled_m]
    hard = [m for m, v in entries.items() if v == "afflicted" and m not in unsettled_m]
    held = sorted(unsettled_m & set(entries))
    names = {m.planet for m in cast}
    dom_bits = []
    for h, d in sorted((getattr(r, "dominance", None) or {}).items()):
        if getattr(d, "governing", None) in names:
            dom_bits.append(f"in {_HOUSE_STORY.get(h, f'house {h}')} it is "
                            f"{d.governing} that decides, {d.yielding} that yields")
    weave = (" Where two pulls meet, one prevails: " + "; ".join(dom_bits[:2]) + "."
             if dom_bits else "")
    good_s = (f"Read in the method's own order, the life leans this way: "
              f"{', '.join(good[:5])} carry the chart's support" if good else
              "Few matters here read plainly favourable")
    hard_s = (f", while {', '.join(hard[:4])} ask more of the native" if hard else "")
    _GLOSS = {"spiritual": "spiritual life", "mother": "home and mother"}
    held_names = [_GLOSS.get(m, m) for m in held]
    held_j = (held_names[0] if len(held_names) == 1
              else f"{', '.join(held_names[:-1])} and {held_names[-1]}")
    held_s = ((f" {held_j.capitalize()} the reading holds apart — "
               f"{'that is the area' if len(held_names) == 1 else 'those are the areas'} the "
               f"chart is least settled on, weighed out below rather than counted either way.")
              if held else "")
    return f"{good_s}{hard_s}.{weave}{held_s}"


def _in_time(r: "DetailedReport") -> str:
    """Event-first: the window opens the sentence, the mechanism follows. Degrades honestly
    when the reference date is outside the Vimshottari span (the Victoria case)."""
    from app.raman_saab.synthesis import running_period
    rp = running_period(r.synthesis)
    if rp is None:
        return ("This chart's Vimshottari span does not reach the date the reading is cast "
                "for, so no chapter is named as running; the life above stands as the chart "
                "gives it, without a marker for now.")
    md, ad = rp
    lit: list[int] = []
    for tp in getattr(getattr(r, "timeline", None), "periods", ()) or ():
        if getattr(tp.period, "maha", None) == md and getattr(tp.period, "antar", None) == ad:
            lit = sorted({a.house for a in tp.activated
                          if str(getattr(a, "grade", "")) == "par_excellence"})
            break
    areas = ", ".join(_HOUSE_STORY.get(h, f"house {h}") for h in lit[:4])
    now = (f"Now, in the {md} years with {ad} beneath them, "
           f"{areas or 'no single area'} come forward — these are the rooms the period "
           f"lights, not events it delivers.")
    turn = ""
    tps = getattr(getattr(r, "nichod", None), "turning_points", ()) or ()
    if tps:
        when, what = tps[0]
        turn = f" The next change of lean is {when}: {what.rstrip('.')}."
    return now + turn


def _closing(r: "DetailedReport", grip_key: str) -> str:
    unsettled = [h for h, v in (r.restraint or {}).items()
                 if getattr(v, "standing", "") == "unsettled"]
    holds = (f" What it declines to resolve — {', '.join(_HOUSE_STORY.get(h, f'house {h}') for h in unsettled[:2])} — "
             f"it declines honestly, and that is part of the reading too." if unsettled else "")
    return (f"Step back and the chart says one thing more than it says anything else: "
            f"{grip_key}. Every section of the full report below is that sentence examined "
            f"from a different side.{holds}")


def build_sitting(r: "DetailedReport") -> Sitting:
    """Compose the sitting. Pure re-read; any failure inside a paragraph costs that paragraph,
    never the section, and never the report."""
    cast = _cast(r)
    grip, key = _grip(r)

    paras: list[tuple[str, str]] = []
    for heading, fn in (("What strikes first", lambda: _strikes_first(r)),
                        ("The cast", lambda: _cast_paragraph(cast)),
                        ("The life, told forward", lambda: _life_forward(r, cast)),
                        ("In time", lambda: _in_time(r))):
        try:
            text = fn()
        except Exception:                                          # noqa: BLE001
            text = ""
        if text:
            paras.append((heading, text))

    try:
        closing = _closing(r, key)
    except Exception:                                              # noqa: BLE001
        closing = ""
    return Sitting(grip=grip, cast=cast, paragraphs=tuple(paras),
                   closing=closing, grip_key=key)
