"""Grading one factor of Raman's template: the house, its lord, the karaka, the view from the Moon.

Inside each factor the sub-order is Raman's (spec 3.3): house position -> sign dignity ->
associates -> aspecters -> kartari -> Navamsa last; the star lord is read where he says it
decides (longevity, the father; spec 4.8). Every testimony is an ``Item`` with its weight and
citation, so the reading shows every contributing fact.

Functional nature over natural nature (spec 4.3): the house's own lord and a yogakaraka are
defused; a natural benefic that is a functional malefic does not help; a natural malefic that
is a functional benefic is named both ways and balanced to nothing. Cancellation devices
(spec 4.6): neechabhanga, own sign, an exalted benefic's aspect on a debility, the malefic
being the dispositor, Bhava position and bhava sandhi.

CONVENTIONS (Raman gives no mechanical rule; each is marked ``convention`` in the output):

* Each testimony counts one step (+1 good, -1 bad, 0 named but not counted). The Rasi grade is
  the net count on Raman's five-step scale: <= -2 afflicted, -1 blemished, 0 moderate,
  +1 fairly strong, >= +2 strong.
* The Navamsa moves the Rasi grade by at most one step (HTJAH:4688-4689; the engine's
  ``NAVAMSA_ONE_STEP``). For a planet: exalted, own sign or vargottama in the Navamsa lifts it
  one step; debilitated there lowers it one step. For a house: the net of natural benefics and
  malefics occupying the same house counted from the Navamsa Lagna (HTJAH:5690-5691).
* The star lord (longevity and father only): the planet's own star, or a star ruled by the Lagna
  lord, a yogakaraka or a functional benefic, counts good; a node's star or that of the
  6th/8th/12th lord counts bad. Raman gives examples (HTJAH:11796-11798, 13344), not a table.
* Round 2 (2026-10-25, from the mismatch review; each rule cites its passage in the code):
  neechabhanga uses only Raman's printed conditions (HTJAH:16178-16181); "friendly" and
  "inimical" sign follow the natural relation, as Raman's words do (HTJAH:2930-2931, 3811-3812,
  3779); an unoccupied, unaspected house is fairly strong (HTJAH:3669-3670, 2809-2810); a lord in
  the 8th from its own house is weakened (HTJAH:3826-3828); a natural benefic owning the 6th
  afflicts what it touches (HTJAH:4405-4406, 4471-4472).
* Deliberately NOT modelled: the degree-distance device ("nearly 20 degrees behind Rahu",
  HTJAH:2196-2197), because Raman prints no orb; the waning Moon as a malefic (the project's
  locked avastha table counts the Moon a benefic).

Usage:
    from app.raman_saab.procedure.grading import grade_house, grade_planet, grade_from_moon
"""
from __future__ import annotations

import logging
from typing import Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti, hemming
from app.raman_saab.ordinals import ordinal
from app.raman_saab.primitives import relationships as rel
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS, functional_nature)
from app.raman_saab.primitives.vimshottari import nakshatra_lord_of
from app.raman_saab.procedure.citations import cite
from app.raman_saab.procedure.model import GRADES, Factor, Item

logger = logging.getLogger(__name__)

SIGNS: tuple[str, ...] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_KENDRA = frozenset({1, 4, 7, 10})
_TRIKONA = frozenset({5, 9})
_DUSTHANA = frozenset({6, 8, 12})
_NODES = frozenset({"Rahu", "Ketu"})


def sign_from(base_sign: int, n: int) -> int:
    """The sign ``n`` places from ``base_sign`` (whole sign, 1-indexed)."""
    return (base_sign - 1 + n - 1) % 12 + 1


def count(from_sign: int, to_sign: int) -> int:
    """How many signs ``to_sign`` is from ``from_sign`` (1..12)."""
    return (to_sign - from_sign) % 12 + 1


def house_sign(chart: RamanChart, house: int) -> int:
    """The sign on rasi-house ``house`` from the Lagna."""
    return sign_from(chart.asc_sign, house)


def lord_of(chart: RamanChart, house: int) -> str:
    """Lord of rasi-house ``house`` from the Lagna."""
    return SIGN_LORDS[house_sign(chart, house)]


def lord_of_sign_from(base_sign: int, n: int) -> str:
    """Lord of the ``n``th sign from ``base_sign``."""
    return SIGN_LORDS[sign_from(base_sign, n)]


def grade_of(net: int) -> str:
    """Net testimony -> Raman's five-step grade (convention, see module docstring)."""
    return GRADES[max(0, min(4, net + 2))]


def shift(grade: str, steps: int) -> str:
    """Move ``grade`` by ``steps`` (clamped to -1..+1, and to the scale)."""
    steps = max(-1, min(1, steps))
    return GRADES[max(0, min(4, GRADES.index(grade) + steps))]


def _house_label(n: int) -> str:
    return f"the {ordinal(n)}"


def influence(chart: RamanChart, planet: str, own_lord: Optional[str], graded: Optional[str],
              how: str) -> Item:
    """Classify one influence (an occupant, an associate or an aspecter) as Raman does.

    ``own_lord`` is the lord of the house under judgment (his own aspect or presence protects
    it); ``graded`` is the planet being graded, if any (its dispositor's malefic aspect causes
    little mischief)."""
    nature = functional_nature(planet, chart)
    lords = "/".join(ordinal(h) for h in _houses_owned(chart, planet))
    who = f"{planet}" + (f" (lord of the {lords})" if lords else "")
    sub = {"occupies": "occupants", "joins": "associates", "aspects": "aspecters"}[how]
    if own_lord is not None and planet == own_lord:
        return Item(sub, f"{who} {how}: the house's own lord, so it protects rather than "
                         "afflicts", 1, cite("own_lord_defused"))
    if nature == "yogakaraka":
        return Item(sub, f"{who} {how}: a yogakaraka, so not harmful", 1,
                    cite("yogakaraka_defused"))
    if _benefic_sixth_lord(chart, planet):
        # Round 2 (B2): "The affliction is heavy because of association with the Moon lord of
        # the sixth" (HTJAH:4405-4406); "The fourth lord Moon is in the seventh with Mercury
        # lord of the third and sixth and hence blemished" (HTJAH:4472-4473).
        return Item(sub, f"{who} {how}: a natural benefic, but lord of the 6th, so it "
                         "afflicts", -1, cite("benefic_sixth_lord_blemish"))
    if planet in NATURAL_BENEFICS:
        if nature == "malefic":
            return Item(sub, f"{who} {how}: a natural benefic but a functional malefic for this "
                             "Lagna, so not helpful", 0, cite("functional_malefic_no_help"))
        return Item(sub, f"{who} {how}: a benefic influence", 1, cite("benefic_fortifies"))
    # natural malefic
    if nature == "benefic":
        return Item(sub, f"{who} {how}: good as a functional benefic and bad as a natural "
                         "malefic; the two are balanced", 0, cite("dual_nature_named"))
    if graded is not None and planet == SIGN_LORDS.get(_sign_of(chart, graded), "") \
            and how == "aspects":
        return Item(sub, f"{who} {how}: a malefic, but it is the dispositor of {graded}, so "
                         "its aspect causes little mischief", 0,
                    cite("dispositor_aspect_harmless"))
    return Item(sub, f"{who} {how}: a malefic influence", -1, cite("malefic_afflicts"))


def _benefic_sixth_lord(chart: RamanChart, planet: str) -> bool:
    """A natural benefic owning the 6th from the Lagna and none of the Lagna, 5th or 9th
    (Round 2, B2). The Lagna and trine lords are excluded because Raman holds the 9th lord
    "decidedly more benefice" (HTJAH:575-578) and the Lagna lord protective; the house's own
    lord is handled before this test."""
    if planet not in NATURAL_BENEFICS:
        return False
    owned = set(_houses_owned(chart, planet))
    return 6 in owned and not (owned & {1, 5, 9})


def raman_neecha_bhanga(planet: str, chart: RamanChart) -> bool:
    """Cancellation of debility on Raman's printed conditions only (Round 2, A2).

    HTJAH:16178-16181: "If a planet is in debility and the lord of this sign or the planet who
    gets exalted there is in Kendra from the Moon or Lagna" and "If a planet is neecha
    (debilitated) in Rashi but gets exalted in Amsa". Every reason Raman gives in a worked chart
    is one of these (HTJAH:2037-2038, 8858-8859, 8888-8889, 8966-8967, 9133-9134). The engine's
    primitive also cancels when the dispositor joins or aspects the planet; Raman prints no such
    condition, so the reader does not use it. A kendra from the Moon counts the Moon's own sign.
    """
    p = chart.planets.get(planet)
    if p is None or planet in _NODES or dignity(planet, chart) != "debil":
        return False
    moon = chart.planets.get("Moon")
    refs = [chart.asc_sign] + ([moon.sign] if moon is not None else [])
    exalted_here = next((q for q, (s, _d) in rel.EXALTATION.items() if s == p.sign
                         and q not in _NODES), None)
    for q in (SIGN_LORDS[p.sign], exalted_here):
        qp = chart.planets.get(q) if q else None
        if qp is not None and any(count(r, qp.sign) in _KENDRA for r in refs):
            return True
    return p.navamsa_sign == rel.EXALTATION[planet][0]


def sign_relation(planet: str, sign: int) -> str:
    """Raman's "friendly" / "inimical" sign: the natural relation to the sign's lord (Round 2,
    A3). Chart 48, Jupiter in Libra, "placed in an inimical sign" (HTJAH:2930-2931); Chart 60,
    Mars in Gemini, "in the sign of an enemy" (HTJAH:3811-3812); Chart 59, Venus "occupies
    Gemini, a friendly sign" (HTJAH:3779). The compound relation reads all three neutral."""
    return rel.naisargika(planet, SIGN_LORDS[sign])


def _sign_of(chart: RamanChart, planet: str) -> int:
    p = chart.planets.get(planet)
    return p.sign if p is not None else 0


def _houses_owned(chart: RamanChart, planet: str) -> list[int]:
    return sorted(count(chart.asc_sign, s) for s, lord in SIGN_LORDS.items() if lord == planet)


def _finish(step: str, subject: str, items: list[Item], nav_shift: int, nav_note: str,
            merged_with: Optional[str] = None, note: str = "") -> Factor:
    net = sum(i.weight for i in items)
    rasi = grade_of(net)
    final = shift(rasi, nav_shift)
    redeeming = any(i.weight > 0 for i in items)
    return Factor(step, subject, tuple(items), rasi, max(-1, min(1, nav_shift)), nav_note,
                  final, redeeming, merged_with, note)


def _kartari_items(chart: RamanChart, house: int, subject: str) -> list[Item]:
    out: list[Item] = []
    if hemming.hemmed_house(chart, house, "malefic"):
        out.append(Item("kartari", f"{subject} is hemmed between malefics (papakartari)", -1,
                        cite("kartari")))
    if hemming.hemmed_house(chart, house, "benefic"):
        out.append(Item("kartari", f"{subject} is hemmed between benefics (subhakartari)", 1,
                        cite("subhakartari")))
    return out


def grade_house(chart: RamanChart, house: int) -> Factor:
    """The house itself: sign, occupants, aspecters, kartari, then the Navamsa (spec 3.2)."""
    sign = house_sign(chart, house)
    own_lord = SIGN_LORDS[sign]
    subject = f"the {ordinal(house)} house ({SIGNS[sign]})"
    items: list[Item] = [Item("sign", f"{subject}, owned by {own_lord}", 0,
                              cite("house_lord_karaka_order"))]
    # The Bhava decides occupancy both ways (HTJAH:1945-1946, "Ketu is actually in the 12th
    # Bhava. Thus Lagna is free"): a planet in the sign but another Bhava leaves the house, and
    # a planet in the neighbouring sign but this Bhava sits in it. (Post-run bug fix 1: the first
    # version applied only the first half, so such a planet occupied no house at all.)
    occupants = [n for n, p in chart.planets.items() if p.rasi_house == house]
    occupants += [n for n, p in chart.planets.items()
                  if p.bhava == house and p.rasi_house != house]
    aspecters = drishti.aspecting_house(house, chart)
    for name in occupants:
        p = chart.planets[name]
        if p.rasi_house != house:
            if p.bhava_sandhi:
                items.append(Item("occupants", f"{name} is in a Bhava-sandhi and cannot give "
                                               "the house's results", 0,
                                  cite("bhava_sandhi_disqualifies")))
                continue
            it = influence(chart, name, own_lord, None, "occupies")
            where = ordinal(p.rasi_house)
            items.append(Item("occupants", f"{name} is in the sign of the {where} house but "
                                           f"actually in this Bhava. " + it.text,
                              it.weight, cite("bhava_frees_house")))
            continue
        if p.bhava and p.bhava != house:
            items.append(Item("occupants", f"{name} is in the sign but actually in the "
                                           f"{ordinal(p.bhava)} Bhava, so the house is free of it",
                              0, cite("bhava_frees_house")))
            continue
        if p.bhava_sandhi:
            items.append(Item("occupants", f"{name} is in a Bhava-sandhi and cannot give the "
                                           "house's results", 0, cite("bhava_sandhi_disqualifies")))
            continue
        it = influence(chart, name, own_lord, None, "occupies")
        if it.weight < 0 and dignity(name, chart) in ("own", "moolatrikona"):
            it = Item("occupants", f"{name} occupies: a malefic, but in its own sign, so the "
                                   "blemish is cancelled", 0, cite("own_sign_cancels"))
        items.append(it)
    for name in aspecters:
        items.append(influence(chart, name, own_lord, None, "aspects"))
    if not occupants and not aspecters:
        # Round 2 (A8): "not occupied or aspected by any planets, benefice or malefic. Hence it
        # is fairly strong" (HTJAH:3669-3670; again HTJAH:2809-2810).
        items.append(Item("occupants", f"{subject} is neither occupied nor aspected, which is "
                                       "good", 1, cite("empty_house_fairly_strong")))
    items += _kartari_items(chart, house, subject)
    nav_shift, nav_note = _navamsa_house(chart, house)
    return _finish("house", subject, items, nav_shift, nav_note)


def _navamsa_house(chart: RamanChart, house: int) -> tuple[int, str]:
    from app.raman_saab.chart import varga
    nl = varga.navamsa_sign(chart.asc_lon)
    target = sign_from(nl, house)
    ben = [n for n, p in chart.planets.items() if p.navamsa_sign == target
           and n in NATURAL_BENEFICS]
    mal = [n for n, p in chart.planets.items() if p.navamsa_sign == target
           and n in NATURAL_MALEFICS]
    net = len(ben) - len(mal)
    if net == 0:
        return 0, (f"In the Navamsa the {ordinal(house)} from the Navamsa Lagna "
                   f"({SIGNS[target]}) holds " + (", ".join(ben + mal) or "no planet")
                   + ": no change")
    word = "lifts the grade one step" if net > 0 else "lowers the grade one step"
    return (1 if net > 0 else -1), (
        f"In the Navamsa the {ordinal(house)} from the Navamsa Lagna ({SIGNS[target]}) holds "
        + ", ".join(ben + mal) + f": {word}")


def grade_planet(chart: RamanChart, planet: str, *, step: str, house: int, role: str,
                 star_lord: bool = False, karaka_bhava: tuple[int, ...] = (),
                 karaka_bhava_cite: str = "") -> Factor:
    """Grade a lord or a karaka in Raman's sub-order. ``house`` is the house under judgment
    (for the "12th from" test and its own lord's protection); ``karaka_bhava`` lists houses
    where this karaka sitting harms its own matter (karako bhava nashaya, applied by Raman)."""
    p = chart.planets.get(planet)
    subject = f"{role} {planet}"
    if p is None:
        return _finish(step, subject, [Item("position", f"{planet} is not in the printed chart",
                                            0, cite("lord_first_printed"), "convention")], 0,
                       "no Navamsa data")
    items: list[Item] = []
    h = p.rasi_house
    own_lord = lord_of(chart, house)
    dig = dignity(planet, chart)
    own_sign = dig in ("own", "moolatrikona")
    # 1. house position
    if house == 12 and planet == own_lord and h in (6, 8):
        items.append(Item("position", f"{planet} in the {ordinal(h)}: the 12th lord in a "
                                      "dusthana reads well", 1, cite("twelfth_lord_dusthana")))
    elif h in _DUSTHANA:
        if own_sign:
            items.append(Item("position", f"{planet} in the {ordinal(h)}, a dusthana, but in its "
                                          "own sign, so the blemish is cancelled", 0,
                              cite("own_sign_cancels")))
        else:
            items.append(Item("position", f"{planet} in the {ordinal(h)}, a dusthana", -1,
                              cite("lord_first_printed")))
    elif h in _KENDRA or h in _TRIKONA:
        kind = "a kendra" if h in _KENDRA else "a trikona"
        items.append(Item("position", f"{planet} in the {ordinal(h)}, {kind}", 1,
                          cite("lord_first_printed")))
    else:
        items.append(Item("position", f"{planet} in the {ordinal(h)}", 0,
                          cite("lord_first_printed")))
    if count(house, h) == 12 and h not in _DUSTHANA and not own_sign:
        items.append(Item("position", f"{planet} is in the 12th from the {ordinal(house)} house",
                          -1, cite("spouse_death_loss_house")))
    if planet == own_lord and count(house, h) == 8 and h not in _DUSTHANA:
        # Round 2 (B1): "posited in a Kendra and own sign but his situation in the 8th from the
        # 3rd ... renders him weak" (HTJAH:3826-3828); own sign does not cancel it there.
        items.append(Item("position", f"{planet} is in the 8th from the {ordinal(house)} house, "
                                      "its own house", -1, cite("eighth_from_own_house")))
    if h in karaka_bhava:
        items.append(Item("position", f"{planet}, the karaka, sits in its own Bhava (the "
                                      f"{ordinal(h)}), which harms its matter", -1,
                          cite(karaka_bhava_cite)))
    # 2. sign dignity (and combustion)
    if dig == "exalt":
        items.append(Item("dignity", f"{planet} is exalted in {SIGNS[p.sign]}", 1,
                          cite("lord_first_printed")))
    elif own_sign:
        items.append(Item("dignity", f"{planet} is in its own sign {SIGNS[p.sign]}", 1,
                          cite("lord_first_printed")))
    elif dig == "debil":
        exalted_benefic = [a for a in drishti.aspecting_planets(planet, chart)
                           if a in NATURAL_BENEFICS and dignity(a, chart) == "exalt"]
        if raman_neecha_bhanga(planet, chart):
            items.append(Item("dignity", f"{planet} is debilitated, but gets neechabhanga", 0,
                              cite("neechabhanga_conditions")))
        elif exalted_benefic:
            items.append(Item("dignity", f"{planet} is debilitated, but the exalted "
                                         f"{exalted_benefic[0]} aspects it, which cancels the "
                                         "evil", 0, cite("exalted_benefic_cancels")))
        else:
            items.append(Item("dignity", f"{planet} is debilitated in {SIGNS[p.sign]}", -1,
                              cite("debility_combustion_destroys")))
    elif planet in _NODES:
        items.append(Item("dignity", f"{planet} is in {SIGNS[p.sign]}; a node is read by its "
                                     "sign lord, not by dignity", 0, cite("node_sign_lord")))
    elif sign_relation(planet, p.sign) == "enemy":
        items.append(Item("dignity", f"{planet} is in an inimical sign {SIGNS[p.sign]}", -1,
                          cite("inimical_sign_natural")))
    else:
        word = "friendly" if sign_relation(planet, p.sign) == "friend" else "neutral"
        items.append(Item("dignity", f"{planet} is in a {word} sign {SIGNS[p.sign]}", 0,
                          cite("friendly_sign_natural") if word == "friendly"
                          else cite("lord_first_printed")))
    if p.combust_fraction > 0.0:
        items.append(Item("dignity", f"{planet} is combust", -1, cite("combust_powerless")))
    # 3. associates
    for name, q in chart.planets.items():
        if name != planet and q.rasi_house == h:
            items.append(influence(chart, name, own_lord if name == own_lord else None,
                                   planet, "joins"))
    # 4. aspecters
    for name in drishti.aspecting_planets(planet, chart):
        items.append(influence(chart, name, own_lord if name == own_lord else None,
                               planet, "aspects"))
    # 5. kartari (planet form)
    items += _kartari_items(chart, h, planet)
    # star lord, where Raman says it decides
    if star_lord:
        items.append(_star_lord_item(chart, planet))
    # 6. Navamsa last
    nav_shift, nav_note = _navamsa_planet(chart, planet)
    return _finish(step, subject, items, nav_shift, nav_note)


def _star_lord_item(chart: RamanChart, planet: str) -> Item:
    sl = nakshatra_lord_of(chart, planet)
    bad_lords = {lord_of(chart, h) for h in (6, 8, 12)}
    if sl == planet:
        return Item("star lord", f"{planet} occupies its own constellation", 1,
                    cite("star_lord_longevity"), "convention")
    if sl in _NODES:
        return Item("star lord", f"{planet} occupies the constellation of {sl}, a node", -1,
                    cite("star_lord_matters"), "convention")
    good = sl == SIGN_LORDS[chart.asc_sign] or functional_nature(sl, chart) in (
        "benefic", "yogakaraka")
    if good and sl not in bad_lords:
        return Item("star lord", f"{planet} occupies the constellation of {sl}, a benefic lord "
                                 "for this Lagna", 1, cite("star_lord_father"), "convention")
    if sl in bad_lords:
        which = "/".join(ordinal(h) for h in (6, 8, 12) if lord_of(chart, h) == sl)
        return Item("star lord", f"{planet} occupies the constellation of {sl}, lord of the "
                                 f"{which}", -1, cite("star_lord_matters"), "convention")
    return Item("star lord", f"{planet} occupies the constellation of {sl}", 0,
                cite("star_lord_matters"), "convention")


def _navamsa_planet(chart: RamanChart, planet: str) -> tuple[int, str]:
    p = chart.planets[planet]
    if planet in _NODES:
        return 0, "a node: no Navamsa dignity is read"
    nav = p.navamsa_sign
    if p.vargottama:
        return 1, f"In the Navamsa {planet} is vargottama ({SIGNS[nav]}): lifts the grade one step"
    if nav == rel.EXALTATION[planet][0]:
        return 1, f"In the Navamsa {planet} is exalted ({SIGNS[nav]}): lifts the grade one step"
    if SIGN_LORDS[nav] == planet:
        return 1, f"In the Navamsa {planet} is in its own sign ({SIGNS[nav]}): lifts one step"
    if nav == rel.DEBILITATION[planet][0]:
        return -1, (f"In the Navamsa {planet} is debilitated ({SIGNS[nav]}): lowers the grade "
                    "one step")
    return 0, f"In the Navamsa {planet} is in {SIGNS[nav]}: no change"


def grade_from_moon(chart: RamanChart, house: int) -> Factor:
    """The same house and its lord counted from the Moon, briefly (spec 1, step 7)."""
    moon = chart.planets.get("Moon")
    subject = f"the {ordinal(house)} from the Moon"
    if moon is None:
        return _finish("moon", subject, [Item("position", "the Moon is not in the printed chart",
                                              0, cite("from_moon"), "convention")], 0, "")
    target = sign_from(moon.sign, house)
    target_h = count(chart.asc_sign, target)
    lord = SIGN_LORDS[target]
    subject = f"the {ordinal(house)} from the Moon ({SIGNS[target]})"
    items: list[Item] = []
    occ = [n for n, p in chart.planets.items() if p.sign == target]
    for name in occ:
        items.append(influence(chart, name, lord, None, "occupies"))
    for name in drishti.aspecting_house(target_h, chart):
        items.append(influence(chart, name, lord, None, "aspects"))
    if not items:
        # Round 2 (A8), as for the house itself (HTJAH:3669-3670).
        items.append(Item("occupants", f"{subject} is neither occupied nor aspected, which is "
                                       "good", 1, cite("empty_house_fairly_strong")))
    items += _kartari_items(chart, target_h, subject)
    lp = chart.planets.get(lord)
    if lp is not None:
        from_moon = count(moon.sign, lp.sign)
        if from_moon in _DUSTHANA:
            items.append(Item("position", f"its lord {lord} is in the {ordinal(from_moon)} from "
                                          "the Moon, a dusthana", -1, cite("from_moon")))
        elif from_moon in _KENDRA or from_moon in _TRIKONA:
            items.append(Item("position", f"its lord {lord} is in the {ordinal(from_moon)} from "
                                          "the Moon", 1, cite("from_moon")))
        dig = dignity(lord, chart)
        if dig in ("exalt", "own", "moolatrikona"):
            items.append(Item("dignity", f"{lord} is {'exalted' if dig == 'exalt' else 'in its own sign'}",
                              1, cite("lord_first_printed")))
        elif dig == "debil" and not raman_neecha_bhanga(lord, chart):
            items.append(Item("dignity", f"{lord} is debilitated", -1,
                              cite("debility_combustion_destroys")))
    return _finish("moon", subject, items, 0, "the view from the Moon is read briefly, without "
                                              "the Navamsa (Raman's practice)")
