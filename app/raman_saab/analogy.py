"""Analogy — "this chart resembles Raman's reading of X, in these respects".

An experienced astrologer recognises a chart. Not vaguely: he says *which* chart it recalls and
*what* about it is the same. Raman does this himself, comparing one worked example against
another — "the papakartari yoga in Chart No. 91 is comparatively much stronger than in Chart No.
90" — and he names the axis every time.

So the resemblance here is **itemised, never scored alone**. A bare "87% similar to Chart 42" is
unfalsifiable and unusable; "the same ascendant, its lord in the same house and equally
dignified" is something a reader can check and disagree with.

The axes are the ones he compares on:

  * the ascendant and its lord's situation — "ascendant lord in situations SIMILAR TO the above
    illustration will confer a weak constitution"
  * which planets bear on the Lagna — "saturnine influences on Lagna"
  * each graha's house and dignity

Reference set: the 190 worked charts in `analogy_index.json`, each carrying the house Raman
pronounced on and his citation, so a match points at something he actually wrote.

**It is allowed to find nothing.** Below the floor, no analogy is offered — the same restraint
`restraint.py` applies to houses. A resemblance engine that always produces a match is a
coincidence generator, and the tests pin that it does not.

PREC-10: comparison only. No verdict is read from the neighbour and none is transferred to the
query chart. A resemblance is an invitation to go and read what Raman wrote, never a conclusion.

Usage:
    from app.raman_saab.analogy import resembles
    for m in resembles(chart):
        print(m.name, m.shared)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

INDEX_PATH: Final[Path] = (Path(__file__).resolve().parents[2]
                           / "tests" / "fixtures" / "analogy_index.json")

#: Weights follow Raman's own emphasis: the ascendant and its lord dominate every comparison he
#: makes, what sits in the Lagna is next, and the rest of the grahas are corroboration.
W_ASC: Final[float] = 3.0
W_LORD_HOUSE: Final[float] = 3.0
W_LORD_DIGNITY: Final[float] = 1.5
W_IN_LAGNA: Final[float] = 2.0
W_PLANET_HOUSE: Final[float] = 0.4
W_PLANET_DIGNITY: Final[float] = 0.3

#: Below this, say nothing. A chart sharing only its ascendant with a worked example is not
#: "resembling" it in any sense a reader would accept.
FLOOR: Final[float] = 6.0


@dataclass(frozen=True)
class Resemblance:
    """One of Raman's charts this one recalls, and exactly what is shared."""

    chart_id: str
    name: str
    book: str
    score: float
    shared: tuple[str, ...]          # the itemised respects — the whole point
    pronounced_houses: tuple[int, ...]
    citations: tuple[str, ...]


@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, Any], ...]:
    if not INDEX_PATH.is_file():
        return ()
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    return tuple(data.get("charts") or ())


def _compare(q: dict, ref: dict) -> tuple[float, list[str]]:
    """Score one pair and, more importantly, say what they actually share."""
    score, shared = 0.0, []

    if q["asc_sign"] == ref["asc_sign"] and q["lagna_lord"] == ref["lagna_lord"]:
        score += W_ASC
        shared.append(f"the same ascendant, ruled by {q['lagna_lord']}")

        if q["lagna_lord_house"] and q["lagna_lord_house"] == ref["lagna_lord_house"]:
            score += W_LORD_HOUSE
            shared.append(f"its lord {q['lagna_lord']} in house {q['lagna_lord_house']} in both")
        if q["lagna_lord_dignity"] and q["lagna_lord_dignity"] == ref["lagna_lord_dignity"]:
            score += W_LORD_DIGNITY
            shared.append(f"{q['lagna_lord']} equally {q['lagna_lord_dignity']}")

    common_lagna = sorted(set(q["in_lagna"]) & set(ref["in_lagna"]))
    if common_lagna:
        score += W_IN_LAGNA * len(common_lagna)
        shared.append(f"{', '.join(common_lagna)} rising in both")

    qp, rp = q.get("planets") or {}, ref.get("planets") or {}
    same_house = [n for n in qp if n in rp and qp[n]["house"] and qp[n]["house"] == rp[n]["house"]]
    if len(same_house) >= 3:
        score += W_PLANET_HOUSE * len(same_house)
        shared.append(f"{len(same_house)} grahas in the same houses "
                      f"({', '.join(sorted(same_house)[:4])}"
                      f"{'…' if len(same_house) > 4 else ''})")

    notable = [n for n in qp if n in rp and qp[n]["dignity"] and
               qp[n]["dignity"] == rp[n]["dignity"] and
               qp[n]["dignity"] in ("exalted", "debilitated", "own")]
    if len(notable) >= 2:
        score += W_PLANET_DIGNITY * len(notable)
        shared.append(f"{len(notable)} grahas in matching dignity "
                      f"({', '.join(f'{n} {qp[n]['dignity']}' for n in sorted(notable)[:3])})")

    return score, shared


def resembles(chart, *, limit: int = 3) -> tuple[Resemblance, ...]:
    """Raman's worked charts this one recalls, strongest first — possibly none.

    `chart` is a cast RamanChart. Returns an empty tuple when nothing clears the floor, which
    is a real and common answer, not a failure.
    """
    from tools.raman_saab.build_analogy_index import chart_features

    index = _index()
    if not index:
        return ()
    try:
        q = chart_features(chart)
    except Exception:                                              # noqa: BLE001
        return ()

    scored: list[Resemblance] = []
    for ref in index:
        score, shared = _compare(q, ref.get("features") or {})
        if score < FLOOR or not shared:
            continue
        scored.append(Resemblance(
            chart_id=str(ref.get("id")), name=str(ref.get("name")), book=str(ref.get("book")),
            score=round(score, 2), shared=tuple(shared),
            pronounced_houses=tuple(ref.get("pronounced_houses") or ()),
            citations=tuple(ref.get("citations") or ())))

    scored.sort(key=lambda m: (-m.score, m.chart_id))
    return tuple(scored[:limit])
