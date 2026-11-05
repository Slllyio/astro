"""The spread of indications, matter by matter: how many of Raman's rules point for a matter,
how many against, how many are descriptive only, and how often an ordinary chart shows the same.

Requested 2026-11-05 ("make the reader show its own uncertainty"), from the finding in
``HOW_ASTROLOGERS_PREDICT_2026-11-05.md`` section 2.1: when nearly every chart offers indications
both ways, a single verdict hides that the books point in both directions. So for every matter
the reading now says, in plain words, whether both outcomes are indicated, and how common that
is: the same count taken over ``BASELINE_N`` random charts (random date 1920-2010, time and
place), cast and judged by the same engine.

Nothing here changes a verdict. It re-reads the judge's own ledgers (the same rules the
for-and-against count uses) and compares them with a fixed, seeded baseline stored in
``spread_baseline.json`` beside this module.

Usage:
    python -m app.raman_saab.cited spread-baseline            # regenerate the baseline (~2 min)
    python -m app.raman_saab.cited spread-baseline --n 500 --seed 7
"""
from __future__ import annotations

import json
import logging
import random
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from app.raman_saab.judges import house_template as ht

logger = logging.getLogger(__name__)

BASELINE_PATH: Path = Path(__file__).with_name("spread_baseline.json")
BASELINE_N = 2000
BASELINE_SEED = 20261105

BOTH, ONLY_FOR, ONLY_AGAINST, SILENT = ("both outcomes indicated", "indicated for only",
                                         "indicated against only", "no rule speaks")


@dataclass(frozen=True)
class Spread:
    house: int
    matter: str                 # signification key, e.g. "spouse"
    n_for: int
    n_against: int
    n_descriptive: int
    verdict: str                # the judge's verdict, unchanged

    @property
    def kind(self) -> str:
        return kind_of(self.n_for, self.n_against)


def kind_of(n_for: int, n_against: int) -> str:
    if n_for and n_against:
        return BOTH
    if n_for:
        return ONLY_FOR
    if n_against:
        return ONLY_AGAINST
    return SILENT


def spreads_for_house(pf: Any) -> tuple[Spread, ...]:
    """The spread of every matter of one judged house (a ``HouseProforma``)."""
    out = []
    for sv in pf.significations:
        L = sv.ledger
        out.append(Spread(pf.house, sv.signification,
                          len({fr.rule.id for fr in L.fired_benefic}),
                          len({fr.rule.id for fr in L.fired_malefic}),
                          len({fr.rule.id for fr in L.fired_neutral}),
                          str(sv.verdict)))
    return tuple(out)


def spreads(chart: Any) -> tuple[Spread, ...]:
    return tuple(s for h in range(1, 13) for s in spreads_for_house(ht.judge_house(chart, h)))


# -- the baseline -----------------------------------------------------------------------------

def _random_birth(rng: random.Random):
    from app.raman_saab.chart.model import BirthData
    lon = rng.uniform(-125.0, 150.0)
    return BirthData("random", rng.randint(1920, 2010), rng.randint(1, 12), rng.randint(1, 28),
                     rng.randint(0, 23), rng.randint(0, 59), round(lon / 15.0 * 2) / 2,
                     rng.uniform(-40.0, 60.0), lon)


def build_baseline(n: int = BASELINE_N, seed: int = BASELINE_SEED) -> dict[str, Any]:
    """Cast ``n`` seeded random charts and record, per matter, how often both sides fire and the
    median counts. Deterministic for a given (n, seed) and engine version."""
    from app.raman_saab.chart.adapter import cast_chart
    rng = random.Random(seed)
    rows: dict[str, dict[str, list[int]]] = {}
    for _ in range(n):
        chart = cast_chart(_random_birth(rng), ayanamsa="raman")
        for s in spreads(chart):
            r = rows.setdefault(f"{s.house}:{s.matter}", {"for": [], "against": [], "both": []})
            r["for"].append(s.n_for)
            r["against"].append(s.n_against)
            r["both"].append(1 if s.kind == BOTH else 0)
    matters = {}
    for key, r in sorted(rows.items(), key=lambda kv: (int(kv[0].split(":")[0]), kv[0])):
        k = len(r["both"])
        matters[key] = {"charts": k, "both_share": round(sum(r["both"]) / k, 4),
                        "only_for_share": round(sum(1 for f, a in zip(r["for"], r["against"]) if f and not a) / k, 4),
                        "only_against_share": round(sum(1 for f, a in zip(r["for"], r["against"]) if a and not f) / k, 4),
                        "median_for": statistics.median(r["for"]),
                        "median_against": statistics.median(r["against"])}
    per_chart_both = None
    total = sum(m["both_share"] for m in matters.values())
    if matters:
        per_chart_both = round(total / len(matters), 4)
    return {"n": n, "seed": seed, "ayanamsa": "raman",
            "sampling": "date 1920-2010 uniform, time uniform, latitude -40..60, longitude -125..150",
            "mean_both_share": per_chart_both, "matters": matters}


@lru_cache(maxsize=1)
def baseline() -> Optional[dict[str, Any]]:
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning("spread baseline not found at %s", BASELINE_PATH)
        return None


def base_for(house: int, matter: str) -> Optional[dict[str, Any]]:
    b = baseline()
    return None if b is None else b["matters"].get(f"{house}:{matter}")


def _rules(n: int) -> str:
    return f"{n} rule" if n == 1 else f"{n} rules"


def pct(x: float) -> str:
    return f"{round(100 * x)}%"


def sentence(s: Spread) -> str:
    """One plain sentence on this matter's spread and how common it is."""
    b = base_for(s.house, s.matter)
    n = (baseline() or {}).get("n")
    head = {BOTH: (f"Both outcomes are indicated: {_rules(s.n_for)} of Raman's point for it and "
                   f"{s.n_against} against."),
            ONLY_FOR: f"Only favourable indications: {_rules(s.n_for)} for, none against.",
            ONLY_AGAINST: f"Only unfavourable indications: {_rules(s.n_against)} against, none for.",
            SILENT: "No rule of Raman's speaks for or against this matter in this chart."}[s.kind]
    if b is None or not n:
        return head
    share = {BOTH: b["both_share"], ONLY_FOR: b["only_for_share"],
             ONLY_AGAINST: b["only_against_share"]}.get(s.kind)
    if share is None:
        share = max(0.0, 1 - b["both_share"] - b["only_for_share"] - b["only_against_share"])
    return (f"{head} On {n:,} random charts, {pct(share)} show the same for this matter "
            f"(typically {b['median_for']:g} for and {b['median_against']:g} against).")


def summary(all_spreads: tuple[Spread, ...]) -> str:
    """The chart-level line for the top of a reading."""
    both = sum(1 for s in all_spreads if s.kind == BOTH)
    b = baseline()
    line = (f"In this chart, {both} of {len(all_spreads)} matters have Raman's rules pointing both "
            f"ways, so for those the books indicate both outcomes and the verdict is a weighing, "
            f"not a single clear sign.")
    if b and b.get("mean_both_share") is not None:
        line += (f" For comparison, on {b['n']:,} random charts, a matter has rules both ways "
                 f"{pct(b['mean_both_share'])} of the time.")
    line += (" A one-sided count is not certainty either: the engine holds only part of what "
             "Raman weighed (about 29% of the reasons he states in his worked charts), and on real "
             "lives no verdict, one-sided or not, has predicted better than chance.")
    return line
