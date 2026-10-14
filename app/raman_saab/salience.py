"""Salience — what an experienced astrologer would notice first in THIS chart.

The engine computes roughly fifty true statements per chart and, until now, had no way to say
which three carry it. That gap is not cosmetic. The Capstone measured its cost: the median chart
holds **19 afflicted and 31 favourable significations at once**, so indications are
"non-differential by construction — present in abundance in every chart, they can explain any
life" (`WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md`). Selecting from abundance is the faculty an
expert supplies, and it is what this module scores.

Measured starting point (`docs/raman_saab/SALIENCE_BASELINE.md`): the previous fixed-template
digest ranked houses WORSE than a constant "always say the Lagna, then the 10th, then the 7th"
— p@1 0.321 vs 0.643 against Raman's own emphasis in *Notable Horoscopes*. The cause was
structural: the template led with CORROBORATION, which is population-typical by construction,
and buried DISTINCTIVENESS in its last slots. It sorted by the one quantity the population
study had already proved carries no chart-specific information.

So the score is built the other way round:

* a **doctrinal prior** — Raman judges the Lagna first (HTJAH-I:16001), and kendras and trikonas
  are the pillars of a chart (HPA-6). Derived from doctrine, never from the benchmark's own
  emphasis frequencies; fitting the prior to the measuring stick would be leakage.
* **surprisal** — `-log2(band_share)` from the population overlay. A reading held by 8% of
  charts distinguishes this one; a reading held by 44% does not. This is the calibration layer's
  existing disclosure role, used at last for attention.
* **extremity** — how far the house sits from the population median.
* **centrality** — how many CHART-SPECIFIC judgment-graph edges touch the house. Doctrine-constant
  edges are excluded: they are identical across unrelated charts and carry nothing.
* **yogas** — a house carrying a fired yoga is one Raman reliably discusses.

PREC-10 holds absolutely: nothing here re-judges anything. Every input is already-computed
output, and the golden ratchet must not move.

Usage:
    from app.raman_saab.salience import rank_houses, house_salience
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: Raman's own order of examination, as doctrine — NOT fitted to any benchmark. The Lagna is
#: judged first and colours everything (HTJAH-I:16001-16002); the kendras and trikonas are the
#: chart's pillars, and among the kendras the 10th (karmasthana) is the most consequential,
#: among the trikonas the 9th (bhagya) outranks the 5th (HPA-6).
#:
#: Ties matter. An earlier version gave every kendra and trikona the same 0.75 and broke ties by
#: house NUMBER, which cost 0.10 p@3 outright — the order within a tier is doctrine too.
DOCTRINAL_PRIOR: Final[dict[int, float]] = {
    1: 1.00,                                        # Lagna — the first impression
    10: 0.80, 7: 0.76, 4: 0.72,                     # kendras, strongest first
    9: 0.74, 5: 0.70,                               # trikonas, bhagya before putra
    2: 0.55, 11: 0.53,                              # dhana / labha
    8: 0.45, 12: 0.44, 6: 0.43, 3: 0.42,            # the rest
}

# ─── chart-specific modulation: MEASURED, and it does not help ──────────────────────────────
# Every one of these was ablated on the tune split against Raman's own emphasis. All of them
# made the ranking WORSE than the doctrinal prior alone (p@1, prior alone 0.643):
#
#     + surprisal   0.214      + extremity  0.357      + centrality 0.357
#     + occupancy   0.643 but p@3 0.357 (down from 0.429)      all together 0.286
#
# The honest reading is that Raman's attention is driven by DOCTRINE — which house is
# structurally consequential — and not by how unusual a house is against a modern population.
# The calibration overlay is a 21st-century addition he never had and never used; it earns its
# place by disclosing information content, not by predicting where a master looks.
#
# So the weights are ZERO. The terms are still computed, because they carry the chart-specific
# REASONS a house matters (surfaced in `why`) even though they must not reorder anything. If a
# later variant beats the prior on held-out charts, raise them — and record the measurement.
W_PRIOR: Final[float] = 1.00
W_SURPRISAL: Final[float] = 0.0
W_EXTREMITY: Final[float] = 0.0
W_CENTRALITY: Final[float] = 0.0
W_YOGA: Final[float] = 0.0

#: A band_share below this floor is treated as this rare; guards -log2(0).
_MIN_SHARE: Final[float] = 0.001


@dataclass(frozen=True)
class HouseSalience:
    """Why one house deserves the reader's attention, with the reason kept alongside the score."""

    house: int
    score: float
    doctrinal_prior: float
    surprisal: float
    extremity: float
    centrality: float
    yogas: int
    #: Reasons this house holds the POSITION it holds. A line may appear here only if the weight
    #: behind it is live; otherwise it describes the house without having moved it, and belongs
    #: in `notable`. Today the prior is the whole ranking, so `why` carries the Lagna and nothing
    #: else — which is the honest answer, not a missing feature.
    why: tuple[str, ...] = field(default_factory=tuple)
    #: True, chart-specific observations that did NOT affect the ranking. Kept rather than
    #: dropped (append-only), under a name that claims description instead of causation.
    notable: tuple[str, ...] = field(default_factory=tuple)


def _z(values: dict[int, float]) -> dict[int, float]:
    """Standardise within the chart — salience is comparative, never absolute."""
    vals = list(values.values())
    if not vals:
        return {}
    mu = statistics.mean(vals)
    sd = statistics.pstdev(vals)
    if sd == 0:
        return {k: 0.0 for k in values}
    return {k: (v - mu) / sd for k, v in values.items()}


def _surprisal_and_extremity(r: "DetailedReport") -> tuple[dict[int, float], dict[int, float]]:
    """Per house: mean information content of its readings, and mean distance from typical."""
    surprisal: dict[int, float] = {}
    extremity: dict[int, float] = {}
    for house, reading in (r.calibration or {}).items():
        entries = getattr(reading, "entries", ()) or ()
        bits, ext = [], []
        for e in entries:
            share = getattr(e, "band_share", None)
            if share is not None and share > 0:
                bits.append(-math.log2(max(float(share), _MIN_SHARE)))
            pct = getattr(e, "favourability_percentile", None)
            if pct is not None:
                ext.append(abs(float(pct) - 0.5) * 2.0)
        if bits:
            surprisal[house] = statistics.mean(bits)
        if ext:
            extremity[house] = statistics.mean(ext)
    return surprisal, extremity


def _centrality(r: "DetailedReport") -> dict[int, float] | None:
    """Chart-specific judgment-graph edges touching each house, or None if the graph failed.

    Only `lord_of` / `occupies` / `aspects` count. The doctrine-constant relations were measured
    byte-identical across unrelated charts, so including them would add a constant to every
    house and wash the signal out.

    Returning None on failure rather than a zero-filled dict matters: all-zeros standardises to
    all-zeros, which reads as "centrality is flat across this chart" — indistinguishable from a
    broken graph. The caller must be able to tell "no evidence" from "no variation".
    """
    from app.raman_saab.judgment_graph import CHART_SPECIFIC_ROLES, build_judgment_graph

    roles = {role for role, _label in CHART_SPECIFIC_ROLES}
    counts: dict[int, float] = {h: 0.0 for h in range(1, 13)}
    try:
        graph = build_judgment_graph(r)
    except Exception:                                              # noqa: BLE001
        return None
    for edge in graph.edges:
        if edge.relation not in roles:
            continue
        for nid in (edge.src, edge.dst):
            if isinstance(nid, str) and nid.startswith("house:"):
                try:
                    counts[int(nid.split(":")[1])] += 1.0
                except (ValueError, KeyError):
                    continue
    return counts


def _yoga_counts(r: "DetailedReport") -> dict[int, int]:
    from app.raman_saab.insight_digest import _yogas_on_house

    out: dict[int, int] = {}
    for h in range(1, 13):
        try:
            out[h] = len(_yogas_on_house(r, h) or ())
        except Exception:                                          # noqa: BLE001
            out[h] = 0
    return out


def house_salience(r: "DetailedReport") -> dict[int, HouseSalience]:
    """Score every house. Pure re-read — no verdict is recomputed (PREC-10)."""
    surprisal, extremity = _surprisal_and_extremity(r)
    centrality = _centrality(r) or {}
    yogas = _yoga_counts(r)

    zs, ze, zc = _z(surprisal), _z(extremity), _z(centrality)
    out: dict[int, HouseSalience] = {}

    for h in range(1, 13):
        prior = DOCTRINAL_PRIOR.get(h, 0.45)
        # A term this chart carries no evidence for is ABSENT, not average. `_z` returns only the
        # houses it was actually given, so `.get(h)` is None where there was nothing to
        # standardise — and substituting 0.0 there would score the house as exactly typical,
        # because 0.0 IS the mean of a standardised distribution. Silent while the weights are
        # zero; wrong the moment one is not, which is exactly when it would be trusted.
        s, e, c = zs.get(h), ze.get(h), zc.get(h)
        y = yogas.get(h, 0)
        score = W_PRIOR * prior + W_YOGA * min(y, 3)
        for weight, z in ((W_SURPRISAL, s), (W_EXTREMITY, e), (W_CENTRALITY, c)):
            if z is not None:
                score += weight * z

        # A line earns a place in `why` only if the weight behind it actually moved the score.
        # Everything else is a true observation that explains nothing about the ordering, and
        # goes to `notable` — kept, never dropped.
        why: list[str] = []
        notable: list[str] = []
        if h == 1:
            why.append("the Lagna, judged first (HTJAH-I:16001)")
        observations = (
            (W_SURPRISAL, s, f"readings here are unusually rare in the population "
                             f"({surprisal.get(h, 0):.1f} bits)"),
            (W_EXTREMITY, e, "sits far from the population median"),
            (W_CENTRALITY, c, f"{int(centrality.get(h, 0))} chart-specific factors bear on it"),
        )
        for weight, z, line in observations:
            if z is not None and z > 0.8:
                (why if weight else notable).append(line)
        if y:
            (why if W_YOGA else notable).append(
                f"{y} fired yoga{'s' if y > 1 else ''} touch{'' if y > 1 else 'es'} it")

        out[h] = HouseSalience(house=h, score=score, doctrinal_prior=prior,
                               surprisal=surprisal.get(h, 0.0), extremity=extremity.get(h, 0.0),
                               centrality=centrality.get(h, 0.0), yogas=y,
                               why=tuple(why), notable=tuple(notable))
    return out


def rank_houses(r: "DetailedReport") -> list[int]:
    """Houses most-salient first — the order a reader should meet them in."""
    scored = house_salience(r)
    return [h for h, _ in sorted(scored.items(), key=lambda kv: -kv[1].score)]
