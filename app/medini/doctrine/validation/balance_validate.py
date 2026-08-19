"""Validate the engine's Vimśottarī START BALANCE against Raman's PRINTED balance lines.

The HTJAH timing report deferred one thing: the balance-of-daśā *itself* (the engine computing
the balance from the Moon) was validated only indirectly (via the 94% MD-placement result).
*Notable Horoscopes* prints, per chart, a verbatim "Balance of <lord> Dasa at birth : Years
Y-M-D" line — the exact ground truth. This harness computes the balance from each chart's stored
Moon longitude with the LIVE engine (`calculate_vimshottari_mahadasha`) and compares the lord
(exact) and the remaining duration (years) to Raman's printed line.

Corpus: ``docs/raman_doctrine/validation/corpora/nh_balance.json`` (self-contained: Moon longitude
+ Raman's printed balance, 30 golden cases matched by name). Measurement only — no engine change.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.balance_validate
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.ephemeris_engine import calculate_vimshottari_mahadasha

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "docs/raman_doctrine/validation/corpora/nh_balance.json"
_FIXED_JD = 2451545.0          # Vimśottarī balance depends only on the Moon; JD is date-format only


def _printed_years(b: dict) -> float:
    return b["years"] + b["months"] / 12.0 + b["days"] / 365.25


def run(corpus_path: str | Path = _CORPUS, dur_tol: float = 0.5) -> dict[str, Any]:
    rows = json.loads(Path(corpus_path).read_text())["rows"]
    out, lord_ok, dur_ok = [], 0, 0
    for r in rows:
        eng = calculate_vimshottari_mahadasha(r["moon_lon"], _FIXED_JD)
        raman_lord = r["printed_balance"]["lord"]
        raman_y = _printed_years(r["printed_balance"])
        lok = eng["mahadasha_lord"] == raman_lord
        dok = lok and abs(eng["years_remaining"] - raman_y) <= dur_tol
        lord_ok += lok
        dur_ok += dok
        out.append({"name": r["name"], "raman_lord": raman_lord, "engine_lord": eng["mahadasha_lord"],
                    "raman_years": round(raman_y, 2), "engine_years": round(eng["years_remaining"], 2),
                    "lord_ok": lok, "dur_ok": dok})
    n = len(out)
    return {"n": n, "lord_exact": lord_ok, "lord_pct": round(100 * lord_ok / n, 1) if n else 0.0,
            "dur_within_tol": dur_ok, "dur_pct": round(100 * dur_ok / n, 1) if n else 0.0,
            "mismatches": [r for r in out if not r["lord_ok"]], "rows": out}


def main() -> None:
    s = run()
    print(f"NH printed-balance validation (N={s['n']}):")
    print(f"  MD-lord exact:        {s['lord_exact']}/{s['n']} ({s['lord_pct']}%)")
    print(f"  duration within 0.5y: {s['dur_within_tol']}/{s['n']} ({s['dur_pct']}%)")
    for m in s["mismatches"]:
        print(f"  MISMATCH  {m['name'][:26]:26s} raman {m['raman_lord']:<8}{m['raman_years']:>6}y "
              f" eng {m['engine_lord']:<8}{m['engine_years']:>6}y  (likely Moon-longitude OCR)")


if __name__ == "__main__":
    main()
