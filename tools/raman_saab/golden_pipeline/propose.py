"""Proposal for user sign-off. The ONLY stage that imports the engine (lazily)."""
from __future__ import annotations

from typing import Any, Callable

_ORD = {"afflicted": 0, "mixed": 1, "favourable": 2}


def _dist(got: str | None, want: str) -> int:
    if got == want:
        return 0
    return abs(_ORD[got] - _ORD[want]) if got in _ORD and want in _ORD else 2


def engine_lookup(goldens: list[dict[str, Any]]) -> Callable[[dict[str, Any]], str | None]:
    import sys
    from tools.raman_saab.golden_pipeline.apply import ROOT
    tests_dir = str(ROOT / "tests")
    if tests_dir not in sys.path:               # no tests/__init__.py; import as pytest does
        sys.path.insert(0, tests_dir)
    import raman_saab.test_goldens as G         # engine import happens here and only here
    by_id = {r["id"]: r for r in goldens}

    def lookup(d: dict[str, Any]) -> str | None:
        return G._signification_verdict(G.build_chart(by_id[d["record_id"]]), d["house"],
                                        d["signification"])
    return lookup


def render(decisions: list[dict[str, Any]], engine: Callable[[dict[str, Any]], str | None],
           current: tuple[tuple[int, int], tuple[int, int]]) -> str:
    (c, t), (w, _wt) = current
    rows = []
    for d in decisions:
        got = engine(d) if d["outcome"] == "CONFIRMED" else None
        if d["outcome"] == "CONFIRMED":
            t += 1
            c += got == d["verdict"]
            w += _dist(got, d["verdict"]) <= 1
        q = "; ".join(f"{r}: \"{q}\" (l.{ln})" for r, (q, ln) in d.get("quotes", {}).items())
        rows.append(f"| {d['item_id']} | {d['outcome']}{' (REVISE)' if d.get('revised') else ''}"
                    f" | {d.get('verdict', '')} | {got or ''} | {q} |")
    return ("# Golden pipeline proposal\n\n"
            f"Projected if all CONFIRMED rows are applied — exact **{c}/{t}**, "
            f"within-1 **{w}/{t}** (reported side by side, never averaged).\n\n"
            "| item | outcome | Raman verdict | engine | decisive quotes |\n"
            "|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
