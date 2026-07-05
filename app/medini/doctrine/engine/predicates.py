"""The compendium DSL interpreter — one hard-tested code path.

Rule antecedents are JSON predicate trees: combinators ``all | any | not |
count_gte`` over ~25 leaf operations mirroring what ``RamanChart`` exposes.
Every house-valued leaf takes an optional ``frame`` (``lagna`` default,
``moon``, ``navamsa``, ``arudha``, ``karakamsa``) so a rule states the
reference frame Raman used, not a hard-coded lookup.

Contracts:

* **Unknown ops fail at load** — ``validate_predicate`` walks the tree and
  rejects anything the interpreter doesn't implement, so a compendium with
  an unevaluable ``full`` rule can never ship.
* **Missing inputs are not False** — a leaf that needs data the chart
  cannot supply (dasha context in static mode, strengths absent) raises
  ``MissingInput``; the evaluator records the rule as *not evaluable* for
  that chart, which is different from *did not fire*.
* Planets/signs are canonical repo spellings ("Jupiter", sign ints 1..12);
  sign names are accepted lowercase for readability in rule files.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping

from app.core.arishta_yogas import NATURAL_BENEFICS, NATURAL_MALEFICS
from app.core.dignity import dignity_state, is_debilitated, is_exalted, is_own_sign
from app.core.drishti_argala import aspects_from_planet
from app.core.nakshatra import nakshatra_for_longitude
from app.core.varga_points import occupies_point
from app.medini.doctrine.raman_chart import RamanChart

SIGN_NAMES = {
    "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4, "leo": 5, "virgo": 6,
    "libra": 7, "scorpio": 8, "sagittarius": 9, "capricorn": 10,
    "aquarius": 11, "pisces": 12,
}
HOUSE_GROUPS = {
    "kendra": (1, 4, 7, 10),
    "trikona": (1, 5, 9),
    "dusthana": (6, 8, 12),
    "upachaya": (3, 6, 10, 11),
    "maraka": (2, 7),
}


class MissingInput(Exception):
    """The chart/context cannot supply an input this leaf requires."""


class UnknownOp(ValueError):
    """Predicate references an op the interpreter does not implement."""


@dataclasses.dataclass(frozen=True)
class EvalContext:
    chart: RamanChart
    # timeline context; None in static mode (dasha leaves raise MissingInput)
    dasha: Mapping[str, str] | None = None       # e.g. {"md": "Saturn", "ad": "Venus"}
    # gochara context; None in static mode (transit leaves raise MissingInput).
    # Maps a graha to the sign (1..12) it is transiting at the moment judged.
    transit: Mapping[str, int] | None = None
    strength_threshold: float = 0.5              # "if strong" compiles against this


def _sign(node_value) -> int:
    if isinstance(node_value, str):
        try:
            return SIGN_NAMES[node_value.lower()]
        except KeyError:
            raise UnknownOp(f"unknown sign name {node_value!r}") from None
    sign = int(node_value)
    if not 1 <= sign <= 12:
        raise UnknownOp(f"sign must be 1..12, got {node_value!r}")
    return sign


def _houses(node) -> tuple[int, ...]:
    spec = node.get("house", node.get("houses"))
    if isinstance(spec, str):
        try:
            return HOUSE_GROUPS[spec]
        except KeyError:
            raise UnknownOp(f"unknown house group {spec!r}") from None
    if isinstance(spec, int):
        return (spec,)
    return tuple(int(h) for h in spec)


def _planets(ctx: EvalContext, spec) -> tuple[str, ...]:
    if spec == "malefic":
        return tuple(sorted(NATURAL_MALEFICS))
    if spec == "benefic":
        return tuple(sorted(NATURAL_BENEFICS))
    if isinstance(spec, str):
        return (spec,)
    return tuple(spec)


def _frame(node) -> str:
    return node.get("frame", "lagna")


def _lord_of_house(ctx: EvalContext, house: int, frame: str) -> str:
    from_moon = frame == "moon"
    if frame not in ("lagna", "moon"):
        raise UnknownOp(f"lordship frame must be lagna|moon, got {frame!r}")
    return ctx.chart.bundle.sign_lord_of_house(house, from_moon=from_moon)


def _strength(ctx: EvalContext, planet: str) -> float:
    val = ctx.chart.bundle.strength.get(planet)
    if val is None:
        raise MissingInput(f"strength unavailable for {planet}")
    return float(val)


# ---------------------------------------------------------------- leaves

def _op_lagna_sign_is(ctx, node):
    return ctx.chart.lagna_sign(_frame(node)) == _sign(node["sign"])


def _op_planet_in_house(ctx, node):
    houses = _houses(node)
    frame = _frame(node)
    return any(ctx.chart.house_of(p, frame) in houses
               for p in _planets(ctx, node["planet"]))


def _op_planet_in_sign(ctx, node):
    target = _sign(node["sign"])
    return any(ctx.chart.bundle.chart.planet_signs[p] == target
               for p in _planets(ctx, node["planet"]))


def _op_planets_conjunct(ctx, node):
    frame = _frame(node)
    houses = {ctx.chart.house_of(p, frame) for p in _planets(ctx, node["planets"])}
    return len(houses) == 1


def _op_lord_of_house_in_house(ctx, node):
    lord = _lord_of_house(ctx, int(node["of_house"]), _frame(node))
    return ctx.chart.house_of(lord, _frame(node)) in _houses({"house": node["in_house"]})


def _op_planet_is_lord_of(ctx, node):
    return _lord_of_house(ctx, int(node["house"]), _frame(node)) == node["planet"]


def _op_planet_aspects_house(ctx, node):
    ph = ctx.chart.bundle.kundali.planet_house
    houses = _houses(node)
    return any(
        any(h in aspects_from_planet(p, ph[p]) for h in houses)
        for p in _planets(ctx, node["planet"]) if p in ph
    )


def _op_planet_aspects_planet(ctx, node):
    ph = ctx.chart.bundle.kundali.planet_house
    targets = _planets(ctx, node["target"])
    return any(
        ph.get(t) in aspects_from_planet(p, ph[p])
        for p in _planets(ctx, node["planet"]) if p in ph
        for t in targets if t in ph and t != p
    )


def _op_varga_sign_is(ctx, node):
    return (ctx.chart.varga_sign(node["planet"], int(node["divisor"]))
            == _sign(node["sign"]))


def _op_varga_lord_is(ctx, node):
    from app.core.dignity import SIGN_RULERS
    sign = ctx.chart.varga_sign(node["planet"], int(node["divisor"]))
    return SIGN_RULERS[sign] in _planets(ctx, node["lord"])


def _op_vargottama(ctx, node):
    p = node["planet"]
    return ctx.chart.varga_sign(p, 1) == ctx.chart.varga_sign(p, 9)


def _op_dignity_is(ctx, node):
    p = node["planet"]
    sign = ctx.chart.bundle.chart.planet_signs[p]
    states = node["state"] if isinstance(node["state"], list) else [node["state"]]
    if p in ("Rahu", "Ketu"):
        raise MissingInput("nodal dignity is doctrine-specific; use an escape hatch")
    return dignity_state(p, sign) in states


def _op_exalted(ctx, node):
    p = node["planet"]
    return is_exalted(p, ctx.chart.bundle.chart.planet_signs[p])


def _op_debilitated(ctx, node):
    p = node["planet"]
    return is_debilitated(p, ctx.chart.bundle.chart.planet_signs[p])


def _op_own_sign(ctx, node):
    p = node["planet"]
    return is_own_sign(p, ctx.chart.bundle.chart.planet_signs[p])


def _op_strength_gte(ctx, node):
    return _strength(ctx, node["planet"]) >= float(node["value"])


def _op_strong(ctx, node):
    return _strength(ctx, node["planet"]) >= ctx.strength_threshold


def _op_combust(ctx, node):
    return bool(ctx.chart.bundle.combust.get(node["planet"], False))


def _op_retrograde(ctx, node):
    raise MissingInput("retrograde flags are not carried by printed positions")


def _op_waxing_moon(ctx, node):
    return bool(ctx.chart.bundle.moon_waxing)


def _op_yoga_present(ctx, node):
    from app.reading.computations.yogas_extended import detect_yogas
    chart = ctx.chart.bundle.chart
    d1 = {p: {"sign": chart.planet_signs[p], "longitude": chart.planet_lons[p]}
          for p in chart.planet_signs}
    findings = detect_yogas(d1, chart.asc_sign, chart.planet_signs["Moon"])
    prefix = f"practitioner.yogas_extended.{node['yoga']}"
    return any(f.id.startswith(prefix) for f in findings)


def _bav(ctx: EvalContext):
    from app.core.ashtakavarga import compute_ashtakavarga
    chart = ctx.chart.bundle.chart
    d1 = {p: {"sign": s} for p, s in chart.planet_signs.items()}
    return compute_ashtakavarga(d1, {"sign": chart.asc_sign})


def _op_av_bindus_gte(ctx, node):
    matrix = _bav(ctx)
    planet = node["planet"]
    sign = (_sign(node["sign"]) if "sign" in node
            else ctx.chart.bundle.chart.planet_signs[planet])
    return matrix["bav_per_planet"][planet][sign - 1] >= int(node["value"])


def _op_sav_bindus_gte(ctx, node):
    matrix = _bav(ctx)
    house = int(node["house"])
    sign = ((ctx.chart.bundle.kundali.lagna_sign - 1 + house - 1) % 12) + 1
    return matrix["sav"][sign - 1] >= int(node["value"])


def _op_reduced_av_total_cmp(ctx, node):
    from app.core.ashtakavarga_sodhana import sodhana
    matrix = _bav(ctx)
    chart = ctx.chart.bundle.chart
    occupied = {chart.planet_signs[p] for p in chart.planet_signs
                if p not in ("Rahu", "Ketu")}
    total = sodhana(matrix["bav_per_planet"][node["planet"]], occupied).total
    op = node.get("cmp", "gte")
    value = int(node["value"])
    return {"gte": total >= value, "lte": total <= value, "eq": total == value}[op]


def _op_tara_class(ctx, node):
    """Count from the Moon's nakshatra to the planet's, 1..9 cycle."""
    lons = ctx.chart.bundle.chart.planet_lons
    moon_n = int(nakshatra_for_longitude(lons["Moon"])["index"])
    planet_n = int(nakshatra_for_longitude(lons[node["planet"]])["index"])
    tara = ((planet_n - moon_n) % 27) % 9 + 1
    wanted = node["tara"] if isinstance(node["tara"], list) else [node["tara"]]
    return tara in [int(t) for t in wanted]


def _op_dasha_lord_is(ctx, node):
    if ctx.dasha is None:
        raise MissingInput("dasha context absent (static evaluation)")
    level = node.get("level", "md")
    lord = ctx.dasha.get(level)
    if lord is None:
        raise MissingInput(f"dasha level {level!r} absent")
    if "house" in node:
        # "dasa of the lord of house N" — the running lord is that house's lord
        return lord == _lord_of_house(ctx, int(node["house"]), _frame(node))
    return lord in _planets(ctx, node["planet"])


def _op_karaka_is(ctx, node):
    if node.get("karaka", "atmakaraka") != "atmakaraka":
        raise MissingInput("only atmakaraka is wired; others via escape hatch")
    return ctx.chart.atmakaraka in _planets(ctx, node["planet"])


def _op_transit_in_house(ctx, node):
    """Gochara: a transiting graha reckoned as a house from a natal reference.

    ``from`` is ``moon`` (classical Gochara, default) or ``lagna``. Fires when
    any named transiting graha stands in one of the target houses counted from
    that reference sign. Raises MissingInput in static mode (no transit ctx),
    so the rule is simply non-evaluable rather than an error."""
    if ctx.transit is None:
        raise MissingInput("transit context absent (static evaluation)")
    frm = node.get("from", "moon")
    if frm == "moon":
        ref = ctx.chart.bundle.chart.planet_signs["Moon"]
    elif frm == "lagna":
        ref = ctx.chart.lagna_sign("lagna")
    else:
        raise UnknownOp(f"transit 'from' must be moon|lagna, got {frm!r}")
    houses = _houses(node)
    for p in _planets(ctx, node["planet"]):
        sign = ctx.transit.get(p)
        if sign is None:
            continue
        house = ((int(sign) - int(ref)) % 12) + 1
        if house in houses:
            return True
    return False


def _op_occupies_khara(ctx, node):
    lon = ctx.chart.bundle.chart.planet_lons[node["planet"]]
    return occupies_point(lon, ctx.chart.khara, float(node.get("orb", 5.0)))


def _op_occupies_chidra(ctx, node):
    lon = ctx.chart.bundle.chart.planet_lons[node["planet"]]
    return occupies_point(lon, ctx.chart.chidra, float(node.get("orb", 5.0)))


LEAF_OPS: dict[str, Callable[[EvalContext, Mapping], bool]] = {
    "lagna_sign_is": _op_lagna_sign_is,
    "planet_in_house": _op_planet_in_house,
    "planet_in_sign": _op_planet_in_sign,
    "planets_conjunct": _op_planets_conjunct,
    "lord_of_house_in_house": _op_lord_of_house_in_house,
    "planet_is_lord_of": _op_planet_is_lord_of,
    "planet_aspects_house": _op_planet_aspects_house,
    "planet_aspects_planet": _op_planet_aspects_planet,
    "varga_sign_is": _op_varga_sign_is,
    "varga_lord_is": _op_varga_lord_is,
    "vargottama": _op_vargottama,
    "dignity_is": _op_dignity_is,
    "exalted": _op_exalted,
    "debilitated": _op_debilitated,
    "own_sign": _op_own_sign,
    "strength_gte": _op_strength_gte,
    "strong": _op_strong,
    "combust": _op_combust,
    "retrograde": _op_retrograde,
    "waxing_moon": _op_waxing_moon,
    "yoga_present": _op_yoga_present,
    "av_bindus_gte": _op_av_bindus_gte,
    "sav_bindus_gte": _op_sav_bindus_gte,
    "reduced_av_total_cmp": _op_reduced_av_total_cmp,
    "tara_class": _op_tara_class,
    "dasha_lord_is": _op_dasha_lord_is,
    "karaka_is": _op_karaka_is,
    "transit_in_house": _op_transit_in_house,
    "occupies_khara": _op_occupies_khara,
    "occupies_chidra": _op_occupies_chidra,
}

COMBINATORS = ("all", "any", "not", "count_gte")


def validate_predicate(node: Mapping) -> set[str]:
    """Load-time walk: return the set of ops used; raise UnknownOp on any
    op the interpreter does not implement (the fail-at-load contract)."""
    if not isinstance(node, Mapping) or "op" not in node:
        raise UnknownOp(f"predicate node must be an object with 'op': {node!r}")
    op = node["op"]
    used = {op}
    if op in ("all", "any"):
        args = node.get("args", [])
        if not args:
            raise UnknownOp(f"{op} needs non-empty args")
        for child in args:
            used |= validate_predicate(child)
    elif op == "not":
        used |= validate_predicate(node["arg"])
    elif op == "count_gte":
        if "n" not in node:
            raise UnknownOp("count_gte needs n")
        for child in node.get("args", []):
            used |= validate_predicate(child)
    elif op not in LEAF_OPS:
        raise UnknownOp(f"unknown op {op!r}")
    return used


def evaluate_predicate(node: Mapping, ctx: EvalContext) -> bool:
    """Evaluate a validated tree. Raises MissingInput when the chart/context
    cannot answer; combinators only short-circuit on definitive values."""
    op = node["op"]
    if op == "all":
        return all(evaluate_predicate(c, ctx) for c in node["args"])
    if op == "any":
        return any(evaluate_predicate(c, ctx) for c in node["args"])
    if op == "not":
        return not evaluate_predicate(node["arg"], ctx)
    if op == "count_gte":
        hits = sum(1 for c in node["args"] if evaluate_predicate(c, ctx))
        return hits >= int(node["n"])
    leaf = LEAF_OPS.get(op)
    if leaf is None:
        raise UnknownOp(f"unknown op {op!r}")
    return bool(leaf(ctx, node))
