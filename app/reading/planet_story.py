"""Planet Story Engine + Interaction Matrix.

Two reducers over blocks the engine already computed:

- **planet_stories** — one short narrative per graha: what it signifies, the
  houses it owns, the house it sits in, its real strength and dignity, its
  functional role, and whether it expresses its higher nature. The chart's
  dominant planet (from the Master layer) is flagged as the central thread.

- **interactions** — the pairwise relationships among the significant grahas
  (conjunction, mutual/one-way aspect, sign-exchange/parivartana, planetary
  war), each reduced to a combined effect read from the two planets' functional
  natures. This is what `master.dominant_challenge` draws its fault-lines from.

Pure and deterministic over `extras.planet_strength` + `extras.classical_factors`
+ `extras.master`, reusing the engine's own aspect primitive
(`drishti_argala.aspects_from_planet`) and rulerships (`dignity.SIGN_RULERS`) —
no chart re-cast, no probability. Fail-soft → {} / [].
"""
from __future__ import annotations

from typing import Any, Mapping

from app.reading._planet_lexicon import (
    PLANET_QUALITY,
    PLANET_SIG,
    strength_index,
    well_placed,
)

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu")
_TARA = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_NATURAL_BENEFIC = {"Jupiter", "Venus", "Mercury", "Moon"}
_ORD = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
        7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}

_DIGNITY_CLAUSE = {
    "exalted": "exalted and hence very powerful",
    "moolatrikona": "in its moolatrikona and strong",
    "own": "in its own sign, well established",
    "friendly": "in a friendly sign",
    "neutral": "in a neutral sign",
    "inimical": "in an inimical sign and somewhat weakened",
    "enemy": "in an inimical sign and somewhat weakened",
    "debilitated": "in its sign of debilitation",
}


def _functional_nature(cf: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for f in (cf.get("functional") or []):
        if isinstance(f, dict) and f.get("planet"):
            out[f["planet"]] = f
    return out


def build_planet_stories(reading: Mapping[str, Any],
                        extras: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One narrative per graha, strongest-first, dominant flagged. → []."""
    try:
        idx = strength_index(extras.get("planet_strength"))
        if not idx:
            return []
        fx = _functional_nature(extras.get("classical_factors") or {})
        master = extras.get("master") or {}
        dominant = ((master.get("dominant_planet") or {}) or {}).get("planet")

        stories: list[dict[str, Any]] = []
        for p in _GRAHAS:
            row = idx.get(p)
            if not row:
                continue
            house = row.get("house")
            dig = str(row.get("dignity") or "").lower()
            combust = bool(row.get("combust"))
            comp = row.get("composite")
            w = well_placed(row.get("dignity"), comp, combust)
            role = fx.get(p) or {}
            ruled = sorted(role.get("houses_ruled") or [])
            good, shadow = PLANET_QUALITY.get(p, ("", ""))

            # --- assemble the narrative.
            bits: list[str] = []
            sig = PLANET_SIG.get(p, "")
            lead = f"{p}, signifying {sig}," if sig else f"{p}"
            if ruled:
                owns = ", ".join(_ordinal(h) for h in ruled)
                lead += f" owns your {owns} house{'s' if len(ruled) > 1 else ''}"
            if house:
                lead += f"{' and' if ruled else ''} sits in the {_ordinal(house)} house"
            bits.append(lead.rstrip() + ".")
            if dig in _DIGNITY_CLAUSE:
                bits.append(f"It is {_DIGNITY_CLAUSE[dig]}"
                            + (", and combust — weakened by the Sun's proximity" if combust
                               else "") + ".")
            elif combust:
                bits.append("It is combust — weakened by the Sun's proximity.")
            if role.get("is_yogakaraka"):
                bits.append("As a yogakāraka it is among the chart's most valuable planets.")
            elif role.get("nature") == "malefic":
                bits.append("It functions as a malefic for your ascendant, so its "
                            "results ask for care.")
            elif role.get("nature") == "benefic":
                bits.append("It functions as a benefic for your ascendant.")
            if good:
                if w is True:
                    bits.append(f"Well placed, it lends {good}.")
                elif w is False:
                    bits.append(f"Under strain, it inclines to {shadow}.")
                else:
                    bits.append(f"It gives a moderate share of {good}.")

            stories.append({
                "planet": p,
                "house": house,
                "house_ord": _ORD.get(house) if house else None,
                "sign": row.get("sign"),
                "houses_ruled": ruled,
                "dignity": row.get("dignity"),
                "composite": comp,
                "combust": combust,
                "nature": role.get("nature", ""),
                "is_yogakaraka": bool(role.get("is_yogakaraka")),
                "condition": ("well placed" if w is True else "under strain"
                              if w is False else "mixed"),
                "is_dominant": (p == dominant),
                "text": " ".join(bits),
            })
        # strongest-first, but keep the dominant planet at the head.
        stories.sort(key=lambda s: (not s["is_dominant"],
                                    -(s["composite"] or 0)))
        return stories
    except Exception:  # noqa: BLE001
        return []


def _nature(p: str, fx: Mapping[str, dict[str, Any]]) -> str:
    """functional nature if known, else natural benefic/malefic."""
    n = (fx.get(p) or {}).get("nature")
    if n in ("benefic", "malefic"):
        return n
    return "benefic" if p in _NATURAL_BENEFIC else "malefic"


def _pair_effect(a: str, b: str, relation: str,
                 fx: Mapping[str, dict[str, Any]]) -> str:
    """Reduce a relation between two grahas into one combined-effect line, from
    their functional natures and the nature of the tie."""
    na, nb = _nature(a, fx), _nature(b, fx)
    both_ben = na == "benefic" and nb == "benefic"
    both_mal = na == "malefic" and nb == "malefic"
    if relation == "war":
        return (f"A planetary war between {a} and {b} — the weaker yields; "
                f"expect strain between their significations until it resolves.")
    if relation == "exchange":
        return (f"{a} and {b} exchange signs (parivartana) — a strong mutual "
                f"bond that ties their affairs together for better and worse.")
    tie = ("conjoined" if relation == "conjunct"
           else "in mutual aspect" if relation == "mutual"
           else "in aspect")
    if both_ben:
        return f"{a} and {b} {tie} — two benefics reinforcing each other's good."
    if both_mal:
        return (f"{a} and {b} {tie} — compounded pressure; friction that can "
                f"mature into resilience under discipline.")
    # benefic + malefic
    ben, mal = (a, b) if na == "benefic" else (b, a)
    return (f"{a} and {b} {tie} — {ben} tempers {mal}; a productive tension "
            f"rather than a plain affliction.")


def build_interactions(reading: Mapping[str, Any],
                      extras: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The pairwise relationships among the significant grahas → []."""
    try:
        from app.core.dignity import SIGN_RULERS
        from app.core.drishti_argala import aspects_from_planet

        idx = strength_index(extras.get("planet_strength"))
        if not idx:
            return []
        cf = extras.get("classical_factors") or {}
        fx = _functional_nature(cf)
        # graha-yuddha pairs already computed by classical_factors.
        wars = {frozenset((w.get("a"), w.get("b")))
                for w in (cf.get("graha_yuddha") or []) if isinstance(w, dict)}

        houses = {p: idx[p]["house"] for p in _TARA
                  if p in idx and idx[p].get("house")}
        signs = {p: idx[p]["sign"] for p in _TARA
                 if p in idx and idx[p].get("sign") is not None}

        out: list[dict[str, Any]] = []
        for i, a in enumerate(_TARA):
            for b in _TARA[i + 1:]:
                if a not in houses or b not in houses:
                    continue
                pair = frozenset((a, b))
                ha, hb = houses[a], houses[b]
                sa, sb = signs.get(a), signs.get(b)
                # --- classify the tie (priority order).
                relation: str | None = None
                if pair in wars:
                    relation = "war"
                elif sa is not None and sb is not None and \
                        SIGN_RULERS[sa] == b and SIGN_RULERS[sb] == a:
                    relation = "exchange"
                elif sa is not None and sa == sb:
                    relation = "conjunct"
                else:
                    a_sees_b = hb in aspects_from_planet(a, ha)
                    b_sees_a = ha in aspects_from_planet(b, hb)
                    if a_sees_b and b_sees_a:
                        relation = "mutual"
                    elif a_sees_b or b_sees_a:
                        relation = "aspect"
                if relation is None:
                    continue
                out.append({
                    "a": a, "b": b,
                    "relation": relation,
                    "effect": _pair_effect(a, b, relation, fx),
                })
        # wars and exchanges are the sharpest — surface them first.
        _RANK = {"war": 0, "exchange": 1, "conjunct": 2, "mutual": 3, "aspect": 4}
        out.sort(key=lambda r: _RANK.get(r["relation"], 9))
        return out
    except Exception:  # noqa: BLE001
        return []


def _ordinal(n: int) -> str:
    if 10 <= (int(n) % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(int(n) % 10, "th")
    return f"{n}{suffix}"
