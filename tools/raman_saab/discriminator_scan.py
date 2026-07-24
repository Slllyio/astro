"""Discriminator-scan triage — systematize the "thin house" meta-finding.

The NH corpus expansion showed the engine's misses concentrate on a few significations, and that
those gaps split into TWO kinds: (a) a rare CLEAN placement discriminator exists (harvest it as a
cited rule, e.g. H10.C.61 'benefic-fortified malefic-free 10th -> favourable career'); (b) no clean
placement rule exists and the gap is karaka-frame / B1 comparative-weighing (defer, don't force).

This tool makes that triage reproducible. For every signification with >=1 engine-miss, it tests a
fixed panel of house-based candidate discriminators against Raman's verdicts across the WHOLE golden
corpus and reports, per candidate: purity (does it fire on only ONE verdict class?), support (how
many charts), and how many CURRENT engine-misses it would close. A candidate with purity==1.0,
support>=2, and >=1 miss-closed is HARVESTABLE (a clean cited rule is buildable). Otherwise the
signification is flagged karaka-frame/B1.

REPORT-ONLY / read-only. Usage: py -3.12 -m tools.raman_saab.discriminator_scan
"""
from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS

from tools.raman_saab.rule_liveness import golden_charts  # reuses the harness loader

# ── house-based candidate discriminators: (name, predicted_verdict, fires(chart, house)) ──────────

def _influenced(ch: RamanChart, group: frozenset[str], house: int) -> bool:
    return any((p.rasi_house == house) or drishti.aspects_house(n, house, ch)
               for n, p in ch.planets.items() if n in group)


def _papakartari(ch: RamanChart, house: int) -> bool:
    prev, nxt = ((house - 2) % 12) + 1, (house % 12) + 1
    m = NATURAL_MALEFICS
    return (any(p.rasi_house == prev and n in m for n, p in ch.planets.items())
            and any(p.rasi_house == nxt and n in m for n, p in ch.planets.items()))


def _lord_house(ch: RamanChart, house: int) -> int | None:
    p = ch.planets.get(SIGN_LORDS[((ch.asc_sign - 1) + (house - 1)) % 12 + 1])
    return p.rasi_house if p else None


_CANDIDATES = {
    "benefic_fortified_malefic_free": ("favourable", lambda ch, h: (
        _influenced(ch, NATURAL_BENEFICS, h) and not _influenced(ch, NATURAL_MALEFICS, h))),
    "malefic_afflicted_benefic_free": ("afflicted", lambda ch, h: (
        _influenced(ch, NATURAL_MALEFICS, h) and not _influenced(ch, NATURAL_BENEFICS, h))),
    "papakartari_on_house": ("afflicted", lambda ch, h: _papakartari(ch, h)),
    "lord_in_dusthana": ("afflicted", lambda ch, h: _lord_house(ch, h) in (6, 8, 12)),
}


@dataclass
class _Cell:
    fires_by_verdict: dict[str, int]      # raman verdict -> count among charts the candidate fires
    misses_closed: int                    # engine-miss charts it fires on with the predicted verdict

    @property
    def support(self) -> int:
        return sum(self.fires_by_verdict.values())


def scan(charts: list[tuple[str, RamanChart]]) -> dict:
    """sig -> {n_verdicts, n_misses, candidate -> _Cell}. Reuses the golden harness for verdicts."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tg_ds", str(__import__("pathlib").Path(__file__).resolve().parents[2]
                     / "tests" / "raman_saab" / "test_goldens.py"))
    tg = importlib.util.module_from_spec(spec); spec.loader.exec_module(tg)

    chart_by_id = dict(charts)
    per_sig: dict[str, dict] = {}
    for rec in tg.load_goldens():
        cid = str(rec.get("id", ""))
        ch = chart_by_id.get(cid)
        if ch is None:
            continue
        for htag, c in rec.get("expected_verdicts", {}).items():
            sig, raman = c.get("signification"), c.get("verdict")
            if raman not in ("favourable", "mixed", "afflicted"):
                continue
            house = int(htag[1:])
            got = tg._signification_verdict(ch, house, sig)
            is_miss = got != raman
            d = per_sig.setdefault(sig, {"n": 0, "misses": 0, "house": house,
                                         "cells": {k: _Cell(defaultdict(int), 0) for k in _CANDIDATES}})
            d["n"] += 1
            d["misses"] += is_miss
            for name, (pred, fires) in _CANDIDATES.items():
                if fires(ch, house):
                    cell = d["cells"][name]
                    cell.fires_by_verdict[raman] += 1
                    if raman == pred and is_miss:
                        cell.misses_closed += 1
    return per_sig


def _purity(cell: _Cell, predicted: str) -> float:
    return cell.fires_by_verdict.get(predicted, 0) / cell.support if cell.support else 0.0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    per_sig = scan(golden_charts())
    harvest, defer = [], []
    print(f"{'signification':22} {'H':>2} {'n':>3} {'miss':>4}  best clean discriminator (purity/support/closes)")
    print("-" * 96)
    for sig in sorted(per_sig, key=lambda s: -per_sig[s]["misses"]):
        d = per_sig[sig]
        if d["misses"] == 0:
            continue
        best = None
        for name, (pred, _f) in _CANDIDATES.items():
            cell = d["cells"][name]
            pur = _purity(cell, pred)
            if pur == 1.0 and cell.support >= 2 and cell.misses_closed >= 1:
                if best is None or cell.misses_closed > best[3]:
                    best = (name, pred, cell.support, cell.misses_closed)
        tag = (f"{best[0]} -> {best[1]} (1.00/{best[2]}/{best[3]})" if best
               else "-- none (karaka-frame / B1) --")
        (harvest if best else defer).append((sig, d["house"], d["misses"], best))
        print(f"{sig:22} {d['house']:>2} {d['n']:>3} {d['misses']:>4}  {tag}")
    print("-" * 96)
    print(f"HARVESTABLE (clean discriminator): {len(harvest)}   karaka-frame/B1 (defer): {len(defer)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
