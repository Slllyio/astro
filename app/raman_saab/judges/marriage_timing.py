"""Marriage timing — Raman's marriage-giving lords and his two delay factors.

The marriage monograph already PRINTS this doctrine verbatim (`timing_navamsa`) and then
computes none of it: the reader is handed a paragraph naming eight kinds of marriage-giving
planet and two delay screens, and no statement of which of them this chart actually
carries. The audit logged the computed early/delayed lean as corpus-gated; with the corpus
mounted the passage is in hand and every clause in it is mechanical.

RAMAN'S MARRIAGE-GIVING PLANETS (HTJAH-II:852-867). Each is surfaced as its own row, so a
reader can see which clause produced which planet:

  * the lord of the sign occupied by the 7th lord              (HTJAH-II:852-853)
  * the lord of the sign occupied by the 7th lord IN NAVAMSA   (HTJAH-II:853-854)
  * Venus, "the karaka or natural significator of the 7th"     (HTJAH-II:854-855)
  * the Moon                                                    (HTJAH-II:855-856)
  * the 7th lord itself, IF it associates with Venus            (HTJAH-II:857-858)
  * the 2nd lord, and the navamsa ruler of the 2nd lord's sign  (HTJAH-II:858-864)
  * the 9th and 10th lords, "if the earlier Dasas are fruitless" (HTJAH-II:864-866)
  * a planet conjoined with the 7th lord, or occupying the 7th   (HTJAH-II:866-867)

"The strongest of these lords gives marriage in his Dasa" (HTJAH-II:856) — so the roster is
ranked by shadbala and the strongest is named. The 9th/10th lords carry Raman's own
condition ("if the earlier Dasas are fruitless"), which the engine cannot evaluate for a
life it has not seen; they are listed with that condition attached and are EXCLUDED from
the strongest-of ranking rather than silently promoted.

HIS TWO DELAY FACTORS (HTJAH-II:875-881), both with their conditionals intact:

  * "Saturn's aspect on the 7th house and 7th lord both from Lagna and the Moon and on
    Venus DELAYS marriage IF THE DASA LORD IS NOT VERY STRONG." The trailing condition is
    part of the rule and is reported with every firing, never dropped.
  * "The association or aspect of the lord of the 6th, 8th or 12th on the 7th house, 7th
    lord and karaka also RULES OUT EARLY marriage."

THE JUPITER-TRANSIT METHOD (HTJAH-II:869-873). Two sphutas — Lagna-lord + 7th-lord
longitude, and Moon + 7th-lord longitude. Jupiter transiting the resultant rasi or its
trines is favourable for marriage. Both resultants are computed and their trines named;
this is a transit lens and Raman subordinates it himself one line later: "Primary
importance must be given to the natal positions and Dasas and only secondary consideration
to transiting planets" (HTJAH-II:881-883) — the same subordination PREC-6 already carries.

NOT A PREDICTION. Nothing here says a marriage happens or when. It reports which planets
Raman's own text nominates as capable of giving marriage in their periods, which of his two
delay factors this chart carries, and the transit windows he names — an indication in the
classical voice, never a decree.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path. The H7 verdict
stays Raman's rasi judgment through `house_template`; a test enforces it.

Usage:
    from app.raman_saab.judges.marriage_timing import build_marriage_timing
    mt = build_marriage_timing(report)
    mt.givers        # the marriage-giving roster, strongest first
    mt.delays        # which of Raman's two delay factors fire
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.dispositor import dispositor, navamsa_lord_of

_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_NODES: Final[frozenset[str]] = frozenset({"Rahu", "Ketu"})

CITE_GIVERS: Final[Citation] = Citation("HTJAH-II", 852)
CITE_STRONGEST: Final[Citation] = Citation("HTJAH-II", 856)
CITE_JUPITER_TRANSIT: Final[Citation] = Citation("HTJAH-II", 869)
CITE_DELAY: Final[Citation] = Citation("HTJAH-II", 875)
CITE_SUBORDINATION: Final[Citation] = Citation("HTJAH-II", 881)

#: The strongest-of rule, verbatim.
STRONGEST_RULE: Final[str] = "The strongest of these lords gives marriage in his Dasa."

#: The two delay factors, verbatim, conditionals intact.
DELAY_SATURN: Final[str] = (
    "Saturn's aspect on the 7th house and 7th lord both from Lagna and the Moon and on "
    "Venus delays marriage if the Dasa lord is not very strong.")
DELAY_DUSTHANA: Final[str] = (
    "The association or aspect of the lord of the 6th, 8th or 12th on the 7th house, 7th "
    "lord and karaka also rules out early marriage.")

#: Raman's own subordination of the transit method, verbatim.
SUBORDINATION: Final[str] = (
    "Primary importance must be given to the natal positions and Dasas and only secondary "
    "consideration to transiting planets.")

CAVEAT: Final[str] = (
    "A timing lens in the classical voice, never a forecast: these are the planets Raman's "
    "own text nominates as capable of giving marriage in their periods, and the delay "
    "factors he names. Nothing here states that a marriage occurs, or when.")


@dataclass(frozen=True)
class MarriageGiver:
    """One planet Raman's text nominates, and EVERY clause that nominates it.

    `clauses` is a list because several of his clauses can land on the same planet, and
    that is information: a graha nominated three ways is better supported than one
    nominated once. It does not change the ranking — Raman says "the STRONGEST of these
    lords", not the most-nominated — but hiding the repetition would drop a real reading.
    """
    planet: str
    clauses: tuple[str, ...]
    strength_rupas: float
    ranked: bool                 # False when Raman attaches a condition the engine cannot judge
    condition: str               # his condition, verbatim-ish, when one applies
    citations: tuple[str, ...]


@dataclass(frozen=True)
class DelayFactor:
    """One of Raman's two delay screens, and what made it fire here."""
    name: str
    rule: str                    # his sentence, verbatim
    fired: bool
    because: tuple[str, ...]     # the specific contacts found
    condition: str               # the trailing conditional, kept attached
    citation: str


@dataclass(frozen=True)
class MarriageTiming:
    """The computed timing layer for the marriage monograph."""
    seventh_lord: str
    givers: tuple[MarriageGiver, ...]
    strongest: str
    strongest_rule: str
    delays: tuple[DelayFactor, ...]
    lean: str                    # the plain-language summary of the delay screens
    jupiter_sphutas: tuple[tuple[str, str, str], ...]   # (label, resultant sign, trines)
    subordination: str
    caveat: str
    citation: str


def _sign_name(s: int) -> str:
    return _SIGNS[s - 1] if 1 <= s <= 12 else f"sign {s}"


def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _rupas(chart, planet: str) -> float:
    p = chart.planets.get(planet)
    sb = getattr(p, "shadbala_rupas", None) if p is not None else None
    total = getattr(sb, "total", None)
    return round(float(total) / 60.0, 2) if total else 0.0


def _house_of(chart, planet: str) -> int:
    p = chart.planets.get(planet)
    return int(getattr(p, "rasi_house", 0) or 0) if p is not None else 0


def _associated(chart, a: str, b: str) -> bool:
    """Raman's 'associates with' — conjunction (same bhava) or mutual aspect."""
    if a not in chart.planets or b not in chart.planets:
        return False
    if _house_of(chart, a) and _house_of(chart, a) == _house_of(chart, b):
        return True
    return bool(drishti.mutual_aspect(a, b, chart))


def build_marriage_timing(r) -> Optional[MarriageTiming]:
    """Compute HTJAH-II:852-883 for a chart. None when the 7th cannot be resolved."""
    chart = getattr(r, "chart", None)
    if chart is None:
        return None
    asc = int(getattr(chart, "asc_sign", 0) or 0)
    if not 1 <= asc <= 12:
        return None
    seventh = _house_of_sign(asc, 7)
    lord7 = SIGN_LORDS[seventh]

    givers: list[MarriageGiver] = []
    by_planet: dict[str, int] = {}

    def _add(planet: str, clause: str, cite_line: int, *,
             ranked: bool = True, condition: str = "") -> None:
        if not planet or planet in _NODES:
            return
        cite = f"HTJAH-II:{cite_line}"
        idx = by_planet.get(planet)
        if idx is not None:                      # already nominated — record the extra clause
            g = givers[idx]
            if clause in g.clauses:
                return
            givers[idx] = MarriageGiver(
                planet=g.planet, clauses=g.clauses + (clause,),
                strength_rupas=g.strength_rupas,
                # a clause Raman states unconditionally outranks a conditional one: once a
                # planet qualifies without his caveat it belongs in the ranking.
                ranked=g.ranked or (ranked and planet in chart.planets),
                condition=g.condition if not ranked else "",
                citations=g.citations + (cite,))
            return
        by_planet[planet] = len(givers)
        givers.append(MarriageGiver(
            planet=planet, clauses=(clause,), strength_rupas=_rupas(chart, planet),
            ranked=ranked and planet in chart.planets, condition=condition,
            citations=(cite,)))

    if lord7 in chart.planets:
        _add(dispositor(lord7, chart),
             f"the lord of the sign occupied by the 7th lord ({lord7})", 852)
        _add(navamsa_lord_of(lord7, chart),
             f"the lord of the sign occupied by the 7th lord ({lord7}) in Navamsa", 853)
    _add("Venus", "Venus, the karaka or natural significator of the 7th house", 854)
    _add("Moon", "the Moon", 855)
    if _associated(chart, lord7, "Venus"):
        _add(lord7, "the 7th lord itself, which here associates with Venus", 857)
    second = SIGN_LORDS[_house_of_sign(asc, 2)]
    _add(second, "the 2nd lord", 858)
    if second in chart.planets:
        _add(navamsa_lord_of(second, chart),
             f"the ruler of the sign occupied by the 2nd lord ({second}) in Navamsa", 859)
    for h, name in ((9, "9th"), (10, "10th")):
        # the condition is written INTO the clause text as well as the `condition` field:
        # when this planet is already nominated unconditionally elsewhere the clause merges
        # into that entry, and a condition living only in the field would be lost there.
        _add(SIGN_LORDS[_house_of_sign(asc, h)],
             f"the {name} lord (only \"if the earlier Dasas are fruitless\")", 864,
             ranked=False,
             condition="Raman admits these only 'if the earlier Dasas are fruitless' — a "
                       "condition about a life the engine has not seen, so this planet is "
                       "listed but kept out of the strongest-of ranking")
    if lord7 in chart.planets:
        for p in drishti.aspecting_planets(lord7, chart):
            if _house_of(chart, p) == _house_of(chart, lord7):
                _add(p, f"a planet conjoined with the 7th lord ({lord7})", 866)
    for p, pl in chart.planets.items():
        if int(getattr(pl, "rasi_house", 0) or 0) == 7:
            _add(p, "a planet occupying the 7th house", 867)

    ranked = [g for g in givers if g.ranked]
    strongest = max(ranked, key=lambda g: g.strength_rupas).planet if ranked else ""
    givers.sort(key=lambda g: (not g.ranked, -g.strength_rupas, g.planet))

    # ── the two delay factors ────────────────────────────────────────────────
    moon_seventh = 0
    mp = chart.planets.get("Moon")
    if mp is not None and 1 <= int(getattr(mp, "sign", 0) or 0) <= 12:
        moon_seventh = _house_of_sign(int(mp.sign), 7)

    sat_hits: list[str] = []
    if "Saturn" in chart.planets:
        if "Saturn" in drishti.aspecting_house(7, chart):
            sat_hits.append("Saturn aspects the 7th house from the Lagna")
        if moon_seventh and "Saturn" in drishti.aspecting_house(moon_seventh, chart):
            sat_hits.append(f"Saturn aspects the 7th from the Moon "
                            f"({_sign_name(moon_seventh)})")
        if lord7 in chart.planets and drishti.aspects_planet("Saturn", lord7, chart):
            sat_hits.append(f"Saturn aspects the 7th lord {lord7}")
        if "Venus" in chart.planets and drishti.aspects_planet("Saturn", "Venus", chart):
            sat_hits.append("Saturn aspects Venus, the karaka")

    dus_hits: list[str] = []
    for h in (6, 8, 12):
        dl = SIGN_LORDS[_house_of_sign(asc, h)]
        if dl not in chart.planets or dl in _NODES:
            continue
        if _house_of(chart, dl) == 7:
            dus_hits.append(f"the {h}th lord {dl} occupies the 7th house")
        elif dl in drishti.aspecting_house(7, chart):
            dus_hits.append(f"the {h}th lord {dl} aspects the 7th house")
        if lord7 in chart.planets and dl != lord7 and _associated(chart, dl, lord7):
            dus_hits.append(f"the {h}th lord {dl} is associated with the 7th lord {lord7}")
        if "Venus" in chart.planets and dl != "Venus" and _associated(chart, dl, "Venus"):
            dus_hits.append(f"the {h}th lord {dl} is associated with Venus, the karaka")

    delays = (
        DelayFactor(
            name="Saturn on the 7th, its lord, or the karaka",
            rule=DELAY_SATURN, fired=bool(sat_hits), because=tuple(sat_hits),
            condition="Raman's own qualifier travels with it: this delays marriage ONLY "
                      "'if the Dasa lord is not very strong', which depends on the period "
                      "running, not on the natal chart alone.",
            citation="HTJAH-II:877-879"),
        DelayFactor(
            name="a 6th, 8th or 12th lord on the 7th, its lord, or the karaka",
            rule=DELAY_DUSTHANA, fired=bool(dus_hits), because=tuple(dus_hits),
            condition="Raman's wording is 'rules out early marriage' — a statement about "
                      "timing, not about whether marriage occurs.",
            citation="HTJAH-II:879-881"),
    )
    fired = [d for d in delays if d.fired]
    if not fired:
        lean = ("Neither of Raman's two delay factors is present on this chart — no Saturn "
                "contact on the 7th, its lord or the karaka, and no 6th/8th/12th lord on "
                "them either. He names no positive 'early marriage' rule here, so this is "
                "the absence of a delay indication, not an indication of earliness.")
    else:
        lean = ("Raman's delay screen fires: "
                + "; ".join(d.name for d in fired)
                + ". He treats these as delaying or ruling out EARLY marriage, each with "
                  "the qualifier printed beside it — not as a denial of marriage.")

    # ── the Jupiter-transit sphutas ──────────────────────────────────────────
    sph: list[tuple[str, str, str]] = []
    lagna_lord = SIGN_LORDS[asc]
    lp, sp = chart.planets.get(lagna_lord), chart.planets.get(lord7)
    for label, a, b in (("Lagna lord + 7th lord", lp, sp),
                        ("Moon + 7th lord", chart.planets.get("Moon"), sp)):
        if a is None or b is None:
            continue
        lon = (float(getattr(a, "lon", 0.0)) + float(getattr(b, "lon", 0.0))) % 360.0
        sign = int(lon // 30) + 1
        trines = [_sign_name(((sign - 1) + k) % 12 + 1) for k in (4, 8)]
        sph.append((label, _sign_name(sign), ", ".join(trines)))

    return MarriageTiming(
        seventh_lord=lord7,
        givers=tuple(givers),
        strongest=strongest,
        strongest_rule=STRONGEST_RULE,
        delays=delays,
        lean=lean,
        jupiter_sphutas=tuple(sph),
        subordination=SUBORDINATION,
        caveat=CAVEAT,
        citation="HTJAH-II:852-883")
