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


def _matter_line(r: "DetailedReport", house: int, verdict: str = "") -> str:
    """The hand-written plain line for this house's matter.

    `verdict` overrides the dashboard's. House sections must pass their own rollup: the heading
    beside the lead already shows it, and voicing the dashboard verdict there would print
    "reads strongly" under a heading saying AFFLICTED — the same incoherence the tension item
    produced before it was made to name both sides.
    """
    from app.raman_saab.detailed_report import _PLAIN_MATTER

    matter = HOUSE_MATTER.get(house)
    if not matter:
        return ""
    if not verdict:
        entry = next((e for e in getattr(r.dashboard, "entries", ()) if e.matter == matter),
                     None)
        verdict = str(getattr(entry, "verdict", "") or "")
    verdict = verdict.split(" ")[0].lower()
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


def plain_for_house(r: "DetailedReport", house: int) -> str:
    """A person-facing lead for one bhava, or "" when there is nothing plain to say.

    Built from the house's OWN significations rather than a shared dashboard matter. Mapping
    houses onto the twelve matters collided — houses 1 and 6 both became "health", 2 and 11
    both "wealth", 8 and 12 both "spiritual" — so a reader met the identical sentence twice.
    Each house carries a distinct set (H1 self/body/health; H6 enemies/accidents/debts), and
    `_SIGNIFICATION_PLAIN` already holds a person-facing phrase for all 56 of them.
    """
    from app.raman_saab.detailed_report import _SIGNIFICATION_PLAIN

    pf = next((p for p in getattr(r, "proformas", ()) or () if p.house == house), None)
    if pf is None or not getattr(pf, "significations", None):
        return ""

    good, bad = [], []
    for sv in pf.significations:
        phrase = _SIGNIFICATION_PLAIN.get(sv.signification)
        if not phrase:
            continue
        verdict = str(sv.verdict).split(" ")[0].lower()
        if verdict == "favourable":
            good.append(phrase)
        elif verdict == "afflicted":
            bad.append(phrase)
    if not good and not bad:
        return ""

    if good and bad:
        out = (f"Of what this part of your life covers, {_join(good)} read well, "
               f"while {_join(bad)} {'do' if len(bad) > 1 else 'does'} not.")
    elif good:
        verb = "all read" if len(good) > 1 else "reads"
        out = f"{_join(good).capitalize()} {verb} well here."
    else:
        out = (f"{_join(bad).capitalize()} {'are' if len(bad) > 1 else 'is'} the difficult "
               f"part of this house.")

    standing = getattr((getattr(r, "restraint", None) or {}).get(house), "standing", None)
    if standing in _FIRMNESS:
        out += " " + _FIRMNESS[standing]

    dom = (getattr(r, "dominance", None) or {}).get(house)
    if dom is not None:
        out += (f" {dom.governing} carries this house — stronger here than {dom.yielding}, so "
                f"the reading follows {dom.governing} rather than splitting the difference.")
    return out


def _join(items: list) -> str:
    """Oxford-free list join, capped so a lead never becomes an inventory."""
    items = items[:3]
    if len(items) == 1:
        return items[0]
    # Several phrases already contain "and" ("courage and drive"), so a conjunction join reads
    # as a stutter — "siblings, courage and drive and short journeys". If ANY item carries one,
    # comma-join the whole list. (Checking only the last item missed this exact case.)
    if any(" and " in i for i in items):
        return ", ".join(items)
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{items[0]}, {items[1]} and {items[2]}"


# ─── who-you-are leads ──────────────────────────────────────────────────────────────────────
# These three sections are the ones a reader most expects to be about them, and all three
# addressed the chart instead. Each lead below is built from that section's own already-computed
# fields, so it is specific rather than a warm generic opener.

def _ruler_lead(r: "DetailedReport") -> str:
    ru = getattr(r, "ruler", None)
    lord = getattr(ru, "lagna_lord", None)
    strongest = getattr(ru, "strongest", None)
    if not lord:
        return ""
    house = getattr(ru, "lagna_lord_house", None)
    # "rules your rising sign, WHICH sits in house 1" made the relative pronoun point at the
    # sign rather than at the planet — and house 1 IS the rising sign, so it read as nonsense.
    where = f" and stands in house {house}," if house else ","
    if strongest and strongest != lord:
        return (f"Two planets shape you here and they are not the same one. {lord} rules your "
                f"rising sign{where} so it sets the manner you meet the world in; {strongest} "
                f"is simply the strongest thing in your chart. Where those two differ, this "
                f"method reads the first for temperament and the second for force.")
    if strongest:
        return (f"{lord} both rules your rising sign{where} and is the strongest planet in "
                f"your chart. That concentration is unusual — the manner you meet the world "
                f"in and the force behind it come from one place rather than two.")
    return f"{lord} rules your rising sign{where} and sets the manner you meet the world in."


def _psych_lead(r: "DetailedReport") -> str:
    ps = getattr(r, "psych", None)
    moon = str(getattr(ps, "moon_state", "") or "")
    if not moon:
        return ""
    ak = getattr(ps, "atmakaraka", None)
    # `moon_state` reads "the Moon (manas) in house 7, exalt, afflicted by Sun, Mars" — strip
    # the label and give it a verb, or the sentence is a fragment.
    state = moon.replace("the Moon (manas) ", "it stands ")
    lead = (f"Your mind is read from the Moon, and here {state}. That is the instrument every "
            f"other judgement in this chart is taken with.")
    if ak:
        lead += (f" {ak} stands as your Atmakaraka — in this method the planet carrying what "
                 f"the life is FOR, as distinct from what it contains.")
    return lead


def _planet_bios_lead(r: "DetailedReport") -> str:
    bios = tuple(getattr(r, "planet_bios", ()) or ())
    if not bios:
        return ""
    top = bios[0]
    count = getattr(top, "census_count", None)
    if not count:
        return ""
    return (f"{top.planet} runs more of your chart than any other planet — it is involved in "
            f"{count} of the readings above, by ruling, sitting in or aspecting the houses "
            f"they judge. Whatever else this chart says, it says it largely in "
            f"{top.planet}'s voice.")


SECTION_LEADS.update({                                             # type: ignore[union-attr]
    "ruler": _ruler_lead,
    "psych": _psych_lead,
    "planet_bios": _planet_bios_lead,
})


# ─── timing leads ───────────────────────────────────────────────────────────────────────────
# The timing sections spoke in bhukti tiers, Julian-day windows and "par excellence" grades.
# Each lead below says what the section is doing, in the reader's terms, and keeps the
# Measured-Truth frame these sections carry: a period is read as which areas of life come
# forward, never as a forecast of events.

def _timeline_lead(r: "DetailedReport") -> str:
    syn = getattr(r, "synthesis", None)
    md, ad = getattr(syn, "running_md", None), getattr(syn, "running_ad", None)
    if not md:
        return ""
    lit = 0
    for tp in getattr(getattr(r, "timeline", None), "periods", ()) or ():
        if getattr(tp.period, "maha", None) == md and getattr(tp.period, "antar", None) == ad:
            lit = sum(1 for a in tp.activated if str(a.grade) == "par_excellence")
            break
    sub = f" with {ad} as the sub-period" if ad else ""
    tail = (f" Between them they light {lit} of your houses at the method's top tier — those "
            f"are the areas it reads as live for you now." if lit else "")
    return (f"You are in a {md} chapter{sub}.{tail} A period is read here as which areas of "
            f"life come forward, not as fortune arriving or leaving.")


def _life_chapters_lead(r: "DetailedReport") -> str:
    chapters = getattr(getattr(r, "life_chapters", None), "chapters", ()) or ()
    cur = next((c for c in chapters if getattr(c, "is_current", False)), None)
    if cur is None:
        return ""
    lit = [h for h, tier, _v in (getattr(cur, "houses_lit", ()) or ())
           if tier == "par excellence"]
    # Name the matters, not the house numbers — a reader knows "marriage", not "the 7th".
    # HOUSE_MATTER is many-to-one (1 and 6 both read health), so dedupe while keeping order.
    matters: list[str] = []
    for h in lit:
        m = HOUSE_MATTER.get(h, "")
        if m and m not in matters:
            matters.append(m)
    where = f" It bears most strongly on {_join(matters)}." if matters else ""
    return (f"Your life is told below as one chapter per major period, and you are inside "
            f"{cur.maha}'s.{where} Each chapter is woven from readings already made above — "
            f"nothing new is judged in them.")


def _decades_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(getattr(r, "decades", None), "decades", ()) or ())
    if not rows:
        return ""
    inside = sum(1 for d in rows if getattr(d, "inside_window", False))
    return (f"{inside} of the {len(rows)} decades below fall inside the window this report "
            f"actually reads; the rest are listed and left unread rather than quietly filled "
            f"in. A decade here is the same periods above, sliced differently — an indication "
            f"of what the method emphasises in a stretch, never a forecast of your years.")


def _gochara_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "gochara", ()) or ())
    if not rows:
        return ""
    good = sum(1 for g in rows if getattr(g, "net_good", False))
    # "0 read net favourable" is arithmetic, not English; say it the way a person would.
    count = "none" if good == 0 else ("all" if good == len(rows) else str(good))
    return (f"Of the {len(rows)} slow transits now running over your chart, {count} read net "
            f"favourable once Vedha and the Ashtakavarga support are applied. In this method "
            f"transits are secondary to the period you are in — they colour the chapter, they "
            f"do not replace it.")


def _synthesis_lead(r: "DetailedReport") -> str:
    """The `synthesis` SECTION is Integrated insights (cross-feature rules that fired) — NOT
    the `Synthesis` dataclass, whose house matters belong to the `houses` section. Two
    different objects with the same word on them; describe the one actually rendered here."""
    fired = tuple(getattr(r, "insights", ()) or ())
    if not fired:
        return ""
    own = sum(1 for i in fired
              if str(getattr(getattr(i, "rule", None), "band", "")) == "raman")
    whose = (f" {own} of them are Raman's own combination doctrine; the rest are classical "
             f"corroboration, which never overrides him." if own else "")
    return (f"Most of this report reads one thing at a time — a house, a planet, a period. "
            f"These {len(fired)} readings are what appear only when several of them are put "
            f"side by side.{whose} They combine findings already made above; none of them "
            f"judges anything new about you.")


def _life_synthesis_lead(r: "DetailedReport") -> str:
    paras = tuple(getattr(getattr(r, "life_synthesis", None), "paragraphs", ()) or ())
    if not paras:
        return ""
    return (f"Told now as continuous prose rather than as tables — {len(paras)} passages, each "
            f"one drawing together what the sections above found about a single side of your "
            f"life. Where two of those sections lean different ways, the passage says so rather "
            f"than picking a winner.")


def _nichod_lead(r: "DetailedReport") -> str:
    n = getattr(r, "nichod", None)
    if n is None or not getattr(n, "essence", ""):
        return ""
    turns = len(tuple(getattr(n, "turning_points", ()) or ()))
    tail = (f" It also marks {turns} point{'s' if turns != 1 else ''} where the lean of the "
            f"periods changes." if turns else "")
    return (f"Nichod is the distillation — the shortest honest account of what this chart says "
            f"about you, in the method's own terms.{tail} It states the caution alongside the "
            f"reading, because the two are equally part of the answer.")


SECTION_LEADS.update({                                             # type: ignore[union-attr]
    "timeline": _timeline_lead,
    "life_chapters": _life_chapters_lead,
    "decades": _decades_lead,
    "gochara": _gochara_lead,
    "synthesis": _synthesis_lead,
    "life_synthesis": _life_synthesis_lead,
    "nichod": _nichod_lead,
})
