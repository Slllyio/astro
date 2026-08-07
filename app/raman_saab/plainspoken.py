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

import logging
from typing import TYPE_CHECKING, Final

logger = logging.getLogger(__name__)

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
        from app.raman_saab.synthesis import running_period
        # NOT `if md:` — the out-of-sequence sentinel is a non-empty string and would produce
        # "You are living a (beyond computed sequence) chapter".
        _rp = running_period(r.synthesis)
        md = _rp[0] if _rp else None
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
    # The channel labels arrive as raw data ("inheritance / legacies"), and a slash mid-prose
    # reads as a field separator, not English. Also dedupe: "gains" appeared in both lists on
    # one chart, which reads as the reading contradicting itself.
    def _clean(names: list[str]) -> list[str]:
        seen: list[str] = []
        for n in names:
            n = n.replace(" / ", " and ").replace("/", " and ")
            if n not in seen:
                seen.append(n)
        return seen

    good, weak = _clean(good), _clean(weak)
    weak = [w for w in weak if w not in good]
    # 13 channels is too many to name, so this one SELECTS — and says so. The count carries the
    # completeness; `_join` then shows a few without implying they are all of them.
    parts = []
    if good:
        parts.append(f"{len(good)} of your {len(rows)} channels read favourable, money reaching "
                     f"you through {_join(good)} among others")
    if weak:
        parts.append(f"{len(weak)} read weaker, including {_join(weak)}")
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
    # Gloss the Sanskrit inline. A plain-language lead that prints "poorvapunya" untranslated
    # has handed the reader the same jargon the layer exists to remove.
    _GLOSS = {"poorvapunya": "poorvapunya (merit carried in)"}
    bits = [f"{_GLOSS.get(str(name), str(name).replace('_', ' '))} "
            f"reads {str(v).split(' ')[0]}"
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
        # Swallowing is right — a phrasing failure must never cost the reader the section. But
        # swallowing SILENTLY is how a lead that crashes on every chart looks identical to a
        # lead that has nothing to say: `_SIGN_NAME` is a tuple, one `.get()` call turned the
        # whole Ashtakavarga lead into "", and only printing every lead by hand caught it.
        logger.warning("plain lead for section %r raised; section renders without it",
                       section_id, exc_info=True)
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
        out = (f"Of what this part of your life covers, {_join_all(good)} read well, "
               f"while {_join_all(bad)} {'do' if len(bad) > 1 else 'does'} not.")
    elif good:
        out = (f"Everything this part of your life covers reads well — "
               f"{_join_all(good)}.")
    else:
        out = (f"This part of your life is the difficult one, across all of what it covers — "
               f"{_join_all(bad)}.")

    standing = getattr((getattr(r, "restraint", None) or {}).get(house), "standing", None)
    if standing in _FIRMNESS:
        out += " " + _FIRMNESS[standing]

    dom = (getattr(r, "dominance", None) or {}).get(house)
    if dom is not None:
        out += (f" {dom.governing} carries this house — stronger here than {dom.yielding}, so "
                f"the reading follows {dom.governing} rather than splitting the difference.")
    return out


def _v(n: int, singular: str, plural: str) -> str:
    """The verb form for a count, because four leads shipped assuming plurality.

    "1 are neutralised", "1 fired yoga touch it", "1 of the 10 pillars are unshaken",
    "Travel abroad all read well" — every one only appears at a cardinality the canonical chart
    never produced, which is why they survived hand-checking. Templates must not assume n > 1.
    """
    return singular if n == 1 else plural


def _join_all(items: list) -> str:
    """Every item, same grammar as `_join` but with NO cap.

    Use this wherever the sentence reads as the complete set. `_join` truncates at three so a
    lead never becomes an inventory, which is right when the phrasing signals a selection
    ("among them", "most strongly") and a silent lie when it does not. It had already dropped
    Mars from a maraka list of four and arishta from a yoga breakdown of four kinds — in both
    cases the reader saw a sentence that read as exhaustive and was not.
    """
    items = [str(i) for i in items]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if any(" and " in i for i in items):
        return ", ".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


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
    # The raw state ends in a comma-list of afflicting grahas ("afflicted by Sun, Mars"), which
    # reads as a data dump mid-sentence. Give the last pair a conjunction.
    if ", " in state.rsplit("by ", 1)[-1] and "by " in state:
        head, tail = state.rsplit("by ", 1)
        names = [n.strip() for n in tail.split(",") if n.strip()]
        if len(names) > 1:
            state = f"{head}by {', '.join(names[:-1])} and {names[-1]}"
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
    from app.raman_saab.synthesis import running_period
    _rp = running_period(syn)
    if _rp is None:
        return ("The date this reading is cast for falls outside your chart's Vimshottari "
                "sequence, so no period is named as running below. The periods themselves are "
                "listed in full; only the marker for 'now' is missing.")
    md, ad = _rp
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
    whose = (f" {own} of them {_v(own, 'is', 'are')} Raman's own combination doctrine; the rest "
             f"are classical "
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


# ─── reference-section leads ────────────────────────────────────────────────────────────────
# The sections a reader reaches for by name (the twelve matters, the yogas, the birth-time
# check) but which spoke only in the engine's register. Each lead is computed from that
# section's OWN data, so it cannot drift from the table it introduces.

def _dashboard_lead(r: "DetailedReport") -> str:
    entries = tuple(getattr(getattr(r, "dashboard", None), "entries", ()) or ())
    if not entries:
        return ""
    tally: dict[str, int] = {}
    for e in entries:
        v = str(getattr(e, "verdict", "") or "")
        if v:
            tally[v] = tally.get(v, 0) + 1
    parts = [f"{n} read {v}" if i == 0 else f"{n} {v}"
             for i, (v, n) in enumerate(sorted(tally.items(), key=lambda kv: -kv[1]))]
    return (f"The whole report on one line each. Of the {len(entries)} matters this method "
            f"weighs, {_join(parts)}. No verdict here is its own — each is the conclusion "
            f"of that matter's full chapter below, carried up so you can see the shape at once.")


def _stands_out_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "distinctive", ()) or ())
    if not rows:
        return ""
    # Count and rarity only. The significations themselves include tokens the LLM guard
    # refuses outright (H8 reads "death"), and a lead must never be the thing that trips it.
    rarest = min((getattr(e, "band_share", 1.0) for _h, e in rows), default=1.0)
    return (f"Almost everything a chart says is also true of almost everyone. These "
            f"{len(rows)} readings are the exceptions — the ones sitting furthest from "
            f"what the comparison population shows, the rarest shared by about {rarest:.0%} of "
            f"charts. They are what distinguishes your chart, not what is strongest in it.")


def _chart_signature_lead(r: "DetailedReport") -> str:
    syn = getattr(r, "synthesis", None)
    lagna = str(getattr(syn, "lagna", "") or "")
    if not lagna:
        return ""
    ak = str(getattr(syn, "atmakaraka", "") or "")
    soul = f", with {ak} carrying the role of soul-significator" if ak else ""
    return (f"These are the frames the whole of your reading is read against: a {lagna} rising "
            f"sign{soul}. Nothing here is a judgment yet — it is the ground the judgments stand "
            f"on, given first so everything that follows has somewhere to attach.")


def _yogas_lead(r: "DetailedReport") -> str:
    fired = tuple(getattr(r, "yogas", ()) or ())
    if not fired:
        return ""
    names = [str(getattr(y, "name", "")) for y in fired if getattr(y, "name", "")]
    named = f" Among them {_join(names)}." if names else ""
    return (f"A yoga is a configuration the classical texts already noticed, named and wrote "
            f"about. {len(fired)} of them are present in your chart.{named} What you read under "
            f"each is those texts' own language for the pattern, quoted — not a fresh "
            f"claim about your life.")


def _analogy_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "analogy", ()) or ())
    if not rows:
        return ""
    who = str(getattr(rows[0], "name", "") or "")
    if len(rows) == 1:
        head = (f"One of the nativities Raman worked through in print sits close enough to "
                f"yours to be worth naming{f' — {who}' if who else ''}.")
    else:
        head = (f"Of the nativities Raman worked through in print, {len(rows)} sit close enough "
                f"to yours to be worth naming{f' — nearest is {who}' if who else ''}.")
    return (f"{head} What they share is itemised below so you can check the resemblance rather "
            f"than take it. The likeness is in the configuration, never in the life that was "
            f"lived from it.")


def _karmic_lead(r: "DetailedReport") -> str:
    ak = str(getattr(getattr(r, "karmic", None), "atmakaraka", "") or "")
    if not ak:
        return ""
    return (f"This layer reads the chart for the direction of the inner life rather than for "
            f"circumstances, through {ak} as your soul-significator and the sign it falls in. "
            f"It is walled off from everything above: it draws on the same chart, and it "
            f"changes no verdict already given.")


def _rect_confidence_lead(r: "DetailedReport") -> str:
    rc = getattr(r, "rect_confidence", None)
    total = int(getattr(rc, "total_count", 0) or 0)
    if not total:
        return ""
    stable = int(getattr(rc, "stable_count", 0) or 0)
    lo, hi = getattr(rc, "overall_stable_minus", None), getattr(rc, "overall_stable_plus", None)
    # LEAD WITH THE WINDOW, not with `stable_count`. That count is pillars surviving the FULL
    # +-60 scan, a deliberately brutal bar — 1 of 10 is normal and says nothing alarming. Printed
    # first it reads as a fragile chart directly above this section's own label, which for this
    # nativity says "firm". Same incoherence as a plain line saying "reads strongly" under a
    # heading saying AFFLICTED: the lead must agree with what sits beside it.
    if lo is not None and hi is not None:
        head = (f"Every pillar of your reading holds from {lo} minutes before your stated time "
                f"to {hi} after, and {stable} of the {total} "
                f"{'survives' if stable == 1 else 'survive'} the full hour scanned either way.")
    else:
        head = (f"{stable} of the {total} pillars of your reading "
                f"{'survives' if stable == 1 else 'survive'} the full scan either way.")
    return (f"A birth time is rarely exact, so the chart is re-cast minute by minute in both "
            f"directions to see what would survive being wrong. {head} This is the honest "
            f"measure of how much weight your recorded time can carry.")


def _restraint_lead(r: "DetailedReport") -> str:
    st = getattr(r, "restraint", None) or {}
    if not st:
        return ""
    unsettled = sum(1 for v in st.values() if str(getattr(v, "standing", "")) == "unsettled")
    firm = len(st) - unsettled
    tail = (f" For {unsettled} the witnesses genuinely disagree, and the reading says so rather "
            f"than picking a side to sound certain." if unsettled
            else " Every one of them holds together.")
    return (f"How firmly the chart speaks, area by area — which is a separate question "
            f"from what it says. {firm} of your {len(st)} houses stand on testimony that agrees "
            f"with itself.{tail}")


def _dominance_lead(r: "DetailedReport") -> str:
    dm = getattr(r, "dominance", None) or {}
    if not dm:
        return ""
    return (f"When two planets pull an area of life in opposite directions, Raman does not "
            f"average them — he says which one prevails, and why. In {len(dm)} of your "
            f"houses that contest is settled below, with the planet that governs it named and "
            f"the rule of precedence that decided it quoted.")


SECTION_LEADS.update({                                             # type: ignore[union-attr]
    "dashboard": _dashboard_lead,
    "stands_out": _stands_out_lead,
    "chart_signature": _chart_signature_lead,
    "yogas": _yogas_lead,
    "analogy": _analogy_lead,
    "karmic": _karmic_lead,
    "rect_confidence": _rect_confidence_lead,
    "restraint": _restraint_lead,
    "dominance": _dominance_lead,
})


# ─── measurement-section leads ──────────────────────────────────────────────────────────────
# The sections that report an instrument reading rather than a verdict. A reader meets a table
# of rupas or bindus with no idea what the number is FOR; each lead says what the measure means
# for them and, where Raman qualified the method himself, carries his qualification.

def _shadbala_lead(r: "DetailedReport") -> str:
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED

    rows = [(n, p.shadbala_rupas.total / 60.0) for n, p in r.chart.planets.items()
            if getattr(p, "shadbala_rupas", None) is not None]
    if not rows:
        return ""
    meets = sum(1 for n, v in rows if MIN_REQUIRED.get(n) is not None and v >= MIN_REQUIRED[n])
    strongest = max(rows, key=lambda t: t[1])
    weakest = min(rows, key=lambda t: t[1])
    return (f"Strength here means capacity, not luck — how fully a planet can deliver what it "
            f"already signifies. {meets} of your {len(rows)} planets meet the minimum Raman "
            f"himself requires (GBB-8:303). {strongest[0]} is your strongest at "
            f"{strongest[1]:.1f} rupas and {weakest[0]} your weakest at {weakest[1]:.1f}, which "
            f"matters most during their own periods.")


def _ashtakavarga_lead(r: "DetailedReport") -> str:
    sav = getattr(r, "sav", None) or {}
    if not sav:
        return ""
    above = sum(1 for v in sav.values() if v > 28)
    best = max(sav.items(), key=lambda kv: kv[1])
    from app.raman_saab.detailed_report import _SIGN_NAME
    return (f"Each sign is scored out of an average of 28 — a rough measure of how much support "
            f"a planet finds when it travels there. {above} of your 12 signs sit above that "
            f"average, {_SIGN_NAME[best[0]]} highest at {best[1]}. Raman rates this "
            f"method corroborative rather than decisive and says so plainly: “it does not "
            f"seem to be quite reliable\u201d (HTJAH-II:4453-4456).")


def _divisional_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "divisional", ()) or ())
    if not rows:
        return ""
    return (f"Your main chart shows the whole of a life at once. These {len(rows)} divisional "
            f"charts each magnify a single part of it — one for your marriage, one for your "
            f"career, one for children — by dividing every sign again. Where a divisional "
            f"reading and the "
            f"main chart disagree, the main chart governs; the division refines the picture, it "
            f"never overturns it.")


def _preponderance_lead(r: "DetailedReport") -> str:
    p = getattr(r, "preponderance", None)
    if p is None:
        return ""
    fav, aff = getattr(p, "most_corroborated_favourable", None), \
        getattr(p, "most_corroborated_afflicted", None)
    con = getattr(p, "most_contested", None)
    bits = []
    if fav:
        bits.append(f"house {fav} is where it most agrees in your favour")
    if aff:
        bits.append(f"house {aff} where it most agrees against")
    if con:
        bits.append(f"house {con} is the one it argues with itself about most")
    return (f"Raman weighs a house by counting how many independent testimonies point the same "
            f"way. Across your chart, {_join(bits)}. Where the testimonies genuinely split, the "
            f"count is shown rather than resolved — a divided house is a fact about the chart, "
            f"not a gap in the reading.")


def _yoga_deep_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "yoga_deep", ()) or ())
    if not rows:
        return ""
    kinds: dict[str, int] = {}
    for y in rows:
        k = str(getattr(y, "kind", "") or "")
        if k:
            kinds[k] = kinds.get(k, 0) + 1
    named = _join_all([f"{n} {k}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])])
    return (f"Each of the {len(rows)} yogas in your chart is read out in full here rather than "
            f"just named — what forms it, what the texts say it does, and how strongly it sits. "
            f"By kind: {named}. What you read under each is the classical description of the "
            f"pattern, not a claim about how it turned out for you.")


def _deeptadi_lead(r: "DetailedReport") -> str:
    states = tuple(getattr(getattr(r, "synthesis", None), "deeptadi", ()) or ())
    if not states:
        return ""
    distinct = {x.split(" ", 1)[1] for x in states if " " in x}
    return (f"An avastha is the state a planet is acting FROM — the same planet, signifying the "
            f"same things, can be radiant or exhausted while it does so. Your {len(states)} "
            f"grahas occupy {len(distinct)} different states between them. This colours HOW a "
            f"planet delivers what it already indicates; it does not change what it indicates.")


def _karakamsa_lead(r: "DetailedReport") -> str:
    syn = getattr(r, "synthesis", None)
    ak, ks = str(getattr(syn, "atmakaraka", "") or ""), str(getattr(syn, "karakamsa", "") or "")
    if not (ak and ks):
        return ""
    return (f"In Jaimini's method the planet at the highest degree becomes the Atmakaraka, the "
            f"significator of the soul — yours is {ak} — and the sign it occupies in the navamsa "
            f"is your karakamsa, {ks}. What that sign holds is read as the direction of your "
            f"inner inclination rather than your circumstances.")


def _ishta_kashta_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "ishta_kashta", ()) or ())
    if not rows:
        return ""
    decided = sum(1 for x in rows if getattr(x, "prevails", None))
    return (f"Ishta is a planet's capacity for good, Kashta its capacity for difficulty; every "
            f"planet carries both at once. Of the {len(rows)} periods listed, {decided} "
            f"{_v(decided, 'has', 'have')} one "
            f"of the two clearly prevailing and the rest are left undecided rather than forced. "
            f"This is a lean, not a forecast of what happens to you.")


def _md_condition_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "md_condition", ()) or ())
    if not rows:
        return ""
    strong = sum(1 for x in rows if getattr(x, "strong", None) is True)
    return (f"A chapter of your life is only as capable as the planet ruling it. Of the "
            f"{len(rows)} major periods this report covers for you, {strong} "
            f"{'is' if strong == 1 else 'are'} ruled by a planet the chart reads as strong. "
            f"A weak period-lord does not make a hard chapter — it means whatever "
            f"that chapter indicates arrives with less force behind it.")


def _av_dasha_seat_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "av_dasha_seats", ()) or ())
    if not rows:
        return ""
    graded = sum(1 for x in rows if str(getattr(x, "read", "")) not in ("", "no data"))
    missing = len(rows) - graded
    tail = (f" {missing} could not be graded and {'is' if missing == 1 else 'are'} left unread "
            f"rather than filled in." if missing else "")
    return (f"This grades each major period by how much Ashtakavarga support sits in the sign "
            f"its lord occupies, and {graded} of your {len(rows)} {_v(graded, 'carries', 'carry')} "
            f"enough data to "
            f"score.{tail} Raman's "
            f"own caveat governs the whole section, which is why it sits last among the "
            f"period companions.")


def _dasa_kakshya_lead(r: "DetailedReport") -> str:
    rows = tuple(getattr(r, "dasa_kakshya", ()) or ())
    if not rows:
        return ""
    donated = sum(1 for x in rows if getattr(x, "donated", False))
    neutral = sum(1 for x in rows if getattr(x, "neutralised", False))
    return (f"The same periods again, cut finer: each is divided into intervals ruled by one "
            f"planet's contribution to the Ashtakavarga of the sign involved. Of your "
            f"{len(rows)} intervals, {donated} {_v(donated, 'carries', 'carry')} a donated point "
            f"and {neutral} {_v(neutral, 'is', 'are')} "
            f"neutralised. Like everything Ashtakavarga, this corroborates the reading above; "
            f"it never overrides it.")


SECTION_LEADS.update({                                             # type: ignore[union-attr]
    "shadbala": _shadbala_lead,
    "ashtakavarga": _ashtakavarga_lead,
    "divisional": _divisional_lead,
    "preponderance": _preponderance_lead,
    "yoga_deep": _yoga_deep_lead,
    "deeptadi": _deeptadi_lead,
    "karakamsa": _karakamsa_lead,
    "ishta_kashta": _ishta_kashta_lead,
    "md_condition": _md_condition_lead,
    "av_dasha_seat": _av_dasha_seat_lead,
    "dasa_kakshya": _dasa_kakshya_lead,
})


# ─── the three sections whose subject IS the guard's subject ────────────────────────────────
# longevity, arishta and maraka are where a plain-language layer can do the most harm. The
# guard's actual line is narrower than "never mention it": it refuses a life event attached to
# a TIME — `death (around|at|by|near)`, `die (around|at|by|before|after)`, `end of life`,
# `will/shall die` — and any dated or age-attached indication. Naming the subject is allowed;
# putting a clock on it is not.
#
# So these leads do three things and no more: say what the method is DOING, say what the
# engine's own measurement found about it, and refuse the clock. Two of the project's own
# findings belong in the plain sentence rather than the small print, because a reader meeting
# "about 101 years" needs both at the moment they read it:
#   - Raman's own order is band-then-period, and the number is a cross-check (HTJAH-II:4465).
#   - The real-outcome programme measured NO chart-specific timing signal here
#     (REAL_OUTCOME_GENERALIZATION.md). That is the engine's own verdict on itself.

def _longevity_lead(r: "DetailedReport") -> str:
    band = str(getattr(r, "longevity_class", "") or "")
    if not band:
        return ""
    years = getattr(r, "longevity_years", None)
    span = (f" The arithmetic cross-check lands near {float(years):.0f} years."
            if isinstance(years, (int, float)) else "")
    return (f"Raman's method sorts a nativity into one of four broad bands rather than naming a "
            f"span, and yours classifies as {band}.{span} Read the band, not the number: he "
            f"establishes the band by combination FIRST and only then looks at periods "
            f"(HTJAH-II:4465-4472), and this engine's own validation found no chart-specific "
            f"timing signal anywhere in this material. It is a classification the method makes, "
            f"and it is not a statement about your life.")


def _arishta_lead(r: "DetailedReport") -> str:
    a = getattr(r, "arishta", None)
    if a is None:
        return ""
    applies = bool(getattr(a, "balarishta_applies", False))
    cancelled = bool(getattr(a, "balarishta_cancelled", False))
    if not applies:
        state = ("Balarishta — the classical combination for danger in infancy — does not form "
                 "in your chart at all")
    elif cancelled:
        state = ("Balarishta forms in your chart and is cancelled; the texts treat a cancelled "
                 "combination as answered, not as a lingering one")
    else:
        state = "Balarishta forms in your chart and the antidotes below are the doctrine's reply"
    protections = len(tuple(getattr(a, "protections", ()) or ()))
    tail = (f" The chart also carries {protections} protective "
            f"combination{'s' if protections != 1 else ''}." if protections else "")
    return (f"This section reads the classical afflictions and, just as carefully, their "
            f"cancellations — Raman treats the two as one question, never quoting an affliction "
            f"without its antidote. {state}.{tail} You are reading how the method tests itself, "
            f"not a finding about what happens to you.")


def _maraka_lead(r: "DetailedReport") -> str:
    mp = getattr(getattr(r, "chart", None), "maraka_points", None)
    units = tuple(getattr(mp, "units", ()) or ())
    if not units:
        return ""
    primary = [str(u.graha) for u in units if str(getattr(u, "tier", "")) == "primary"]
    # NOT `_join` here. It caps at three so a lead never becomes an inventory, which is right
    # everywhere else and wrong in a sentence that reads as the complete list — it printed
    # "Jupiter, Venus and Saturn" for a chart with four, silently dropping Mars. The set is
    # small and closed; name all of it.
    who = ""
    if primary:
        named = (primary[0] if len(primary) == 1
                 else f"{', '.join(primary[:-1])} and {primary[-1]}")
        who = f" In your chart that marks {named}."
    return (f"Having placed the band, Raman's method names which planets carry the relevant "
            f"authority — the lords, occupants and associates of the 2nd and 7th houses, which "
            f"the tradition assigns this role.{who} This is a disclosure of how the method "
            f"works, offered so you can see the machinery rather than be handed a conclusion "
            f"from it. The engine's own outcome study found no chart-specific signal in this "
            f"scheme, and nothing here is timed against your life.")


SECTION_LEADS.update({                                             # type: ignore[union-attr]
    "longevity": _longevity_lead,
    "arishta": _arishta_lead,
    "maraka": _maraka_lead,
})
