"""Evaluate the later-author rules on a chart, each labelled with its author and cited verbatim.

These are NOT Krishnamurti's rules. They come from authors who wrote after him
(:mod:`app.kp.later.sources`), and the result says so on every row. Each
:class:`~app.kp.later.registry.LaterRule` reads one cusp sub-lord (CSL) and
fires when every condition holds. Condition kinds (``groups`` = tuple of house
tuples, each group needing one hit; "signifies" = ladder levels A-D unless named):

* ``is`` / ``star_is`` / ``is_or_star_is``  the CSL / its star lord / either is a named planet.
* ``signifies`` / ``star_signifies``  the CSL / its star lord signifies the groups.
* ``signifies_ac``  the CSL signifies the groups through its star lord only (levels A and C),
  the E-zine authors' "significator (in the star of the occupant or owner)" (ruling LR4).
* ``signifies_ss`` / ``not_signifies_ss``  houses carried "through its Starlord or Sublord": the
  CSL's levels A and C plus the houses its own sub-lord occupies or owns (ruling LR4).
* ``signifies_ab``  ... at levels A or B, the occupant levels: a "strong" signification (LR6).
* ``signifies_e``   ... at levels A-E, E = conjunction or drishti (ruling R8a), for an author who
  counts "being conjoined with the significators".
* ``not_signifies`` / ``not_signifies_ac`` / ``not_signifies_e``  the CSL signifies none of the houses.
* ``cusp_signifies``  another cusp's CSL signifies groups: ``arg = (cusp, groups)``.
* ``occupies`` / ``star_occupies``  the CSL / its star lord is in one of the bhavas.
* ``sign_in`` / ``star_sign_in`` / ``either_sign_in``  ... is in one of the signs (0 = Aries).
* ``direct`` / ``retro``  the CSL is / is not retrograde (nodes never are).
* ``both_direct`` / ``both_retro``  the CSL and its star lord both are direct / retrograde.
* ``star_retro`` / ``not_star_retro``  the CSL's star lord is / is not retrograde.
* ``dual_or_mercury``  the CSL is Mercury or sits in a dual sign.
* ``aspected_by``  a named planet casts a Hindu sign aspect (drishti, R8a) on the CSL.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.later.rules import later_indications
    for f in later_indications(cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))):
        print(f.to_dict())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import NODES, KPChart, sign_index
from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.registry import LATER_RULES, LaterRule
from app.kp.later.sources import SOURCES
from app.kp.significators import DRISHTI, Signification, planet_significations

DUAL_SIGNS: Final = frozenset({2, 5, 8, 11})
FRAMING: Final[str] = ("A later author's rule, not Krishnamurti's; what the author says this "
                       "configuration shows, not a validated prediction.")
_LEVELS: Final[dict[str, frozenset[str]]] = {
    "": frozenset("ABCD"), "_ac": frozenset("AC"), "_ab": frozenset("AB"), "_e": frozenset("ABCDE"),
}
KINDS: Final = (
    "is", "star_is", "is_or_star_is", "signifies", "star_signifies", "signifies_ac", "signifies_ab",
    "signifies_e", "signifies_ss", "not_signifies", "not_signifies_ss", "not_signifies_ac", "not_signifies_e", "cusp_signifies",
    "occupies", "star_occupies", "sign_in", "star_sign_in", "either_sign_in", "direct", "retro",
    "both_direct", "both_retro", "star_retro", "not_star_retro", "dual_or_mercury", "aspected_by",
)


@dataclass(frozen=True, slots=True)
class LaterFired:
    """A later-author rule that holds, with the CSL and star lord it was read from."""

    rule: LaterRule
    csl: str
    star_lord: str

    def to_dict(self) -> dict:
        r = self.rule
        c = LATER_CITATIONS[r.citation]
        src = SOURCES[c.source]
        return {
            "key": r.key, "cusp": r.cusp, "context": r.context, "sex": r.sex, "indicates": r.indicates,
            "csl": self.csl, "csl_star_lord": self.star_lord,
            "author": src.author, "book": src.title, "citation": f'{c.ref()} "{c.quote}"',
            "note": c.note, "framing": FRAMING,
        }


def _retro(chart: KPChart, p: str) -> bool:
    return p not in NODES and chart.planets[p].retrograde


def _houses(sigs: dict[str, tuple[Signification, ...]], planet: str, levels: frozenset[str]) -> frozenset[int]:
    return frozenset(s.house for s in sigs[planet] if s.level in levels)


def _meets(houses: frozenset[int], groups) -> bool:
    return all(houses & frozenset(g) for g in groups)


def _aspects(chart: KPChart, a: str, b: str) -> bool:
    if a not in DRISHTI:
        return False
    d = (sign_index(chart.planets[b].longitude) - sign_index(chart.planets[a].longitude)) % 12 + 1
    return d in DRISHTI[a]


def _ss(chart: KPChart, sigs, csl: str) -> frozenset[int]:
    """Houses through the CSL's star lord (A, C) or its sub-lord's own occupation/ownership (B, D)."""
    return _houses(sigs, csl, _LEVELS["_ac"]) | _houses(sigs, chart.planets[csl].sub_lord, frozenset("BD"))


def holds(chart: KPChart, kind: str, arg, csl: str, star: str, sigs) -> bool:
    """Evaluate one condition for the CSL ``csl`` (star lord ``star``); ``sigs`` includes level E."""
    sign = lambda p: sign_index(chart.planets[p].longitude)
    if kind == "is":
        return csl in arg
    if kind == "star_is":
        return star in arg
    if kind == "is_or_star_is":
        return csl in arg or star in arg
    if kind == "signifies_ss":
        return _meets(_ss(chart, sigs, csl), arg)
    if kind == "not_signifies_ss":
        return not _ss(chart, sigs, csl) & frozenset(arg)
    if kind.startswith("signifies") or kind == "star_signifies":
        planet = star if kind == "star_signifies" else csl
        suffix = "" if kind == "star_signifies" else kind.removeprefix("signifies")
        return _meets(_houses(sigs, planet, _LEVELS[suffix]), arg)
    if kind.startswith("not_signifies"):
        return not _houses(sigs, csl, _LEVELS[kind.removeprefix("not_signifies")]) & frozenset(arg)
    if kind == "cusp_signifies":
        other, groups = arg
        return _meets(_houses(sigs, chart.cusp(other).sub_lord, _LEVELS[""]), groups)
    if kind == "occupies":
        return chart.planets[csl].bhava in arg
    if kind == "star_occupies":
        return chart.planets[star].bhava in arg
    if kind == "sign_in":
        return sign(csl) in arg
    if kind == "star_sign_in":
        return sign(star) in arg
    if kind == "either_sign_in":
        return sign(csl) in arg or sign(star) in arg
    if kind == "direct":
        return not _retro(chart, csl)
    if kind == "retro":
        return _retro(chart, csl)
    if kind == "both_direct":
        return not (_retro(chart, csl) or _retro(chart, star))
    if kind == "both_retro":
        return _retro(chart, csl) and _retro(chart, star)
    if kind == "star_retro":
        return _retro(chart, star)
    if kind == "not_star_retro":
        return not _retro(chart, star)
    if kind == "dual_or_mercury":
        return csl == "Mercury" or sign(csl) in DUAL_SIGNS
    if kind == "aspected_by":
        return any(p != csl and _aspects(chart, p, csl) for p in arg)
    raise ValueError(f"unknown condition kind {kind!r}")


def later_indications(chart: KPChart, *, context: str | None = None,
                      sex: str | None = None) -> tuple[LaterFired, ...]:
    """Every later-author rule that holds in ``chart``.

    ``context`` keeps only ``"natal"`` or ``"horary"`` rules. ``sex`` (``"male"`` /
    ``"female"``) drops rules the author tied to the other sex; with ``sex=None`` those
    rules are kept and carry their ``sex`` in :meth:`LaterFired.to_dict`.
    """
    sigs = planet_significations(chart, level_e=True)
    out = []
    for r in LATER_RULES.values():
        if context and r.context != context:
            continue
        if sex and r.sex and r.sex != sex:
            continue
        csl = chart.cusp(r.cusp).sub_lord
        star = chart.planets[csl].star_lord
        if all(holds(chart, k, a, csl, star, sigs) for k, a in r.conds):
            out.append(LaterFired(r, csl, star))
    return tuple(out)


__all__ = ["FRAMING", "KINDS", "LaterFired", "holds", "later_indications"]
