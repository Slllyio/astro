"""Plainspoken — say the finding about the PERSON, not about the chart.

The digest is the most-read thing in the report and it speaks in the engine's own bookkeeping:

    "House 10 (career & status) is the most contested area. Its headline reads afflicted, yet
     its own witnesses are divided (7 favourable, 0 adverse, 2 neutral — contested)."

Every word of that is true and none of it is addressed to a human being. An astrologer with the
same facts says: *your working life is the unresolved thing in this chart — nearly everything in
it points up, and one thread drags.* Same information, different act.

This module writes that sentence. It invents no vocabulary: `_PLAIN_MATTER` in
`detailed_report` already holds hand-written, warm, jargon-free prose for each of the twelve
matters at each verdict — written for "Your Reading" and never applied to the digest. This is
that phrasebook, pointed at the findings the reader meets first.

Three rules, all of which follow from the rest of this project:

* **It ADDS, never replaces** (REPORT COMPLETENESS). The technical detail stays exactly as it
  is; the plain sentence sits above it. A reader who wants the witness counts still has them.
* **It never claims more than the finding.** The strength of the phrasing tracks the engine's
  own standing — a well-corroborated house is spoken plainly, a contested one is spoken as
  contested. `restraint` decided which is which; this only reads it.
* **It may say nothing.** An item with no person-facing translation returns "" rather than
  being padded into significance.

PREC-10: no verdict is recomputed. Every sentence is a re-voicing of a value already decided.

Usage:
    from app.raman_saab.plainspoken import plain_for_item
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport
    from app.raman_saab.insight_digest import DigestItem

#: house -> the dashboard matter whose plain prose speaks for it. Mirrors the mapping
#: `tension_narrator` already uses, so the two agree about which reader judges which house.
HOUSE_MATTER: Final[dict[int, str]] = {
    1: "health", 2: "wealth", 3: "siblings", 4: "mother", 5: "children", 6: "health",
    7: "marriage", 8: "spiritual", 9: "father", 10: "career", 11: "wealth",
    12: "spiritual",
}

#: How firmly to speak, from the engine's own standing for that house. The engine decided this
#: in `restraint`; the wording only reflects it.
_FIRMNESS: Final[dict[str, str]] = {
    "concordant": "The chart is unusually consistent about this.",
    "governed": "One factor decides it rather than a balance of them.",
    "concentrated": "It all rests on a single planet here.",
    "unsettled": "The chart does not speak with one voice about it.",
}


def _matter_line(r: "DetailedReport", house: int) -> str:
    """The hand-written plain line for this house's matter at its own verdict."""
    from app.raman_saab.detailed_report import _PLAIN_MATTER

    matter = HOUSE_MATTER.get(house)
    if not matter:
        return ""
    entry = next((e for e in getattr(r.dashboard, "entries", ()) if e.matter == matter), None)
    verdict = str(getattr(entry, "verdict", "") or "").split(" ")[0].lower()
    options = (_PLAIN_MATTER.get(matter) or {}).get(verdict)
    if not options:
        return ""
    if not isinstance(options, tuple):
        return str(options)
    # The phrasebook offers variants precisely so two people do not receive word-identical
    # prose. Always taking options[0] threw that away and made every chart with the same
    # verdict read the same. Select by a value STABLE for this chart — house plus the
    # ascendant — so a report reads identically on every run but differently between charts.
    seed = (house * 7 + int(getattr(r.chart, "asc_sign", 1) or 1)) % len(options)
    return options[seed]


def plain_for_item(r: "DetailedReport", item: "DigestItem") -> str:
    """One sentence about the person for this finding, or "" when there is nothing to say."""
    houses = [h for h in (item.houses or ()) if 1 <= h <= 12]
    # An item spanning most of the chart is about the whole life, not one area of it.
    house = houses[0] if len(houses) == 1 else None

    if item.kind == "first_impression":
        ru = getattr(r, "ruler", None)
        temperament = str(getattr(ru, "temperament", "") or "").rstrip(". ")
        if temperament:
            return f"In plain terms: {temperament[0].lower()}{temperament[1:]}."
        return ""

    if item.kind == "timing" and getattr(r, "synthesis", None):
        md = getattr(r.synthesis, "running_md", None)
        if md:
            from app.raman_saab.detailed_report import _PLANET_THEME
            theme = _PLAIN_THEME_OVERRIDE.get(md) or _PLANET_THEME.get(md)
            if theme:
                # "brings" is on the guard's denylist (promises/brings/foretells). Write
                # around it — the rule this project has followed since the movement passages.
                return (f"You are living a {md} chapter — classically a stretch in which "
                        f"{theme} come to the front of life.")
        return ""

    if house is None:
        return ""

    line = _matter_line(r, house)
    if not line:
        return ""

    # A TENSION must name both sides. The plain phrasebook speaks for the matter's own
    # dedicated reader, while a tension item is about the HOUSE rollup disagreeing with it —
    # so voicing only the matter produced "career reads strongly" above a finding that the
    # house reads afflicted, which is the exact incoherence this layer exists to remove.
    if item.kind == "tension":
        pf = next((p for p in r.proformas if p.house == house), None)
        rollup = str(getattr(pf, "rollup", "") or "")
        if rollup:
            return (f"{line[0].upper()}{line[1:]} — yet taken as a whole this area of life "
                    f"reads {rollup}. That gap is the unresolved thing in your chart, and the "
                    f"engine leaves it standing rather than choosing a side.")
        return f"{line[0].upper()}{line[1:]}."

    firmness = ""
    standing = getattr((getattr(r, "restraint", None) or {}).get(house), "standing", None)
    if item.kind == "convergence" and standing in _FIRMNESS:
        firmness = " " + _FIRMNESS[standing]

    if item.kind == "distinctive":
        return (f"{line[0].upper()}{line[1:]} — and this is one of the readings that most "
                f"sets your chart apart from other people's.")
    return f"{line[0].upper()}{line[1:]}.{firmness}"


#: A few grahas whose `_PLANET_THEME` phrasing does not sit well after "brings".
_PLAIN_THEME_OVERRIDE: Final[dict[str, str]] = {
    "Rahu": "ambition, disruption and appetite for the unfamiliar",
    "Ketu": "detachment, inwardness and a loosening of old holds",
}


# ─── section leads — the six matters a reader opens the report for ──────────────────────────
# Measured before writing these: 12 of 54 sections addressed the reader at all, and the 42 that
# never said "you" included career, wealth, marriage, children and health. The digest had been
# given a human voice and every room behind it was still a database report. Each lead below is
# built from that section's OWN computed data, so it is specific to the chart rather than a
# generic warm sentence — and each says nothing when the data is absent.

def _count_bands(rows, band: str) -> int:
    return sum(1 for row in rows if str(row[0]).lower() == band)


def _career_lead(r: "DetailedReport") -> str:
    pf = getattr(r, "profession", None)
    conv = tuple(getattr(pf, "convergent", ()) or ()) if pf else ()
    n_src = len(getattr(pf, "sources", ()) or ()) if pf else 0
    if not n_src:
        return ""
    if conv:
        words = ", ".join(str(c[0]) for c in conv)
        return (f"{n_src} independent methods were applied to your chart to read vocation, and "
                f"only {words} was named by more than one of them. Where they disagree the "
                f"reading below shows each derivation separately rather than averaging them "
                f"into a single answer.")
    return (f"{n_src} independent methods were applied to your chart to read vocation and no "
            f"trade was named by more than one of them — which is itself the finding: this "
            f"chart does not point at one occupation.")


def _wealth_lead(r: "DetailedReport") -> str:
    w = getattr(r, "wealth", None)
    rows = list(getattr(w, "rows", ()) or []) if w else []
    if not rows:
        return ""
    good = [x.channel.split("(")[0].strip().lower() for x in rows
            if str(x.reading).startswith("favourable")]
    weak = [x.channel.split("(")[0].strip().lower() for x in rows
            if str(x.reading).startswith("afflicted")]
    if not good and not weak:
        return ""
    parts = []
    if good:
        parts.append(f"money reaches you through {', '.join(good[:3])}")
    if weak:
        parts.append(f"while {', '.join(weak[:3])} read as the weak channels")
    return (f"Read as channels rather than one verdict: {'; '.join(parts)}. Wealth is not one "
            f"thing in this method — it matters which route it takes.")


def _marriage_lead(r: "DetailedReport") -> str:
    m = getattr(r, "marriage", None)
    fired = list(getattr(m, "fired_kalatra", ()) or []) if m else []
    if not fired:
        return ""
    forts = _count_bands(fired, "fortified")
    affl = _count_bands(fired, "afflicted")
    if forts and affl:
        return (f"{forts} of Raman's classical testimonies favour this marriage and {affl} warn "
                f"about it. That is a genuinely two-sided reading, not a soft one — both sets "
                f"are quoted below in his own words so you can weigh them yourself.")
    if forts:
        return (f"{forts} of Raman's classical testimonies favour this marriage and none warn "
                f"about it — an unusually one-sided reading for this house.")
    return (f"{affl} of Raman's classical testimonies warn about this marriage and none favour "
            f"it. They are quoted below in his own words rather than summarised.")


def _children_lead(r: "DetailedReport") -> str:
    c = getattr(r, "children", None)
    sigs = tuple(getattr(c, "significations", ()) or ()) if c else ()
    if not sigs:
        return ""
    bits = [f"{str(name).replace('_', ' ')} reads {str(v).split(' ')[0]}"
            for name, v in sigs]
    return (f"This part of your chart covers more than children — {', '.join(bits)}. Each is "
            f"judged separately below, because in this method one of them reading difficult "
            f"does not make the others so.")


def _health_lead(r: "DetailedReport") -> str:
    h = getattr(r, "health_readout", None)
    rows = list(getattr(h, "rows", ()) or []) if h else []
    if not rows:
        return ""
    affl = [x for x in rows if str(x.verdict) == "afflicted"]
    if len(affl) >= 2:
        areas = ", ".join(x.area.split("—")[-1].strip().lower() for x in affl[:3])
        return (f"{len(affl)} of the {len(rows)} indicators checked read afflicted for you — "
                f"{areas}. Where several independent indicators agree, this method treats the "
                f"area as one to attend to rather than to worry over. It describes your chart, "
                f"never your body, and it is not a medical opinion.")
    return (f"Of the {len(rows)} indicators checked, {len(affl)} reads afflicted for you — no "
            f"pattern of agreement, which this method treats as the quieter finding. It "
            f"describes your chart, never your body, and it is not a medical opinion.")


SECTION_LEADS: Final[dict[str, object]] = {
    "profession": _career_lead,
    "wealth": _wealth_lead,
    "marriage": _marriage_lead,
    "children": _children_lead,
    "health_readout": _health_lead,
}


def plain_for_section(r: "DetailedReport", section_id: str) -> str:
    """A person-facing lead for one report section, or "" when there is nothing plain to say."""
    fn = SECTION_LEADS.get(section_id)
    if fn is None:
        return ""
    try:
        return fn(r) or ""                                         # type: ignore[operator]
    except Exception:                                              # noqa: BLE001
        return ""
