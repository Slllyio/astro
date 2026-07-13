"""Increment 34 — yoga-engine COVERAGE audit against Raman's 'Three Hundred Important Combinations'.

A fresh, non-strength axis (the strength-verdict vein is exhausted across all Raman's books). This
book catalogues yogas with a Definition (antecedent), Results (stated outcome), and example charts.
Two honest, NON-circular questions it answers — and one it deliberately does NOT:

  COVERAGE (answered here): of the yogas Raman names, how many does our engine's yoga library know?
    A concrete gap map — it says which of Raman's combinations the detector (and the increment-30
    yoga-token feature) is blind to.
  OUTCOME PREDICTION (NOT answered): Raman's yoga→outcome is DOCTRINE (his stated effect), not
    observed ground truth, so scoring a model that predicts his outcome from his combination would be
    circular. A genuine test needs real-birth people with known life outcomes — the deferred Track B
    (population data), out of scope here.

Corpus: docs/raman_doctrine/validation/corpora/three_hundred_yogas.json (extracted rows only; the
book text is never committed). Engine names: derived live from app/core/{yoga_library,yogas,
arishta_yogas}.py so the coverage number tracks the engine.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.yoga_coverage [--json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "docs/raman_doctrine/validation/corpora/three_hundred_yogas.json"
_CORE = [_ROOT / "app/core" / f for f in ("yoga_library.py", "yogas.py", "arishta_yogas.py")]

# OCR/spelling variants → a canonical stem, so a name match isn't defeated by transliteration noise.
# NOTE the five Pancha-Mahapurusha members (Bhadra/Hamsa/Malavya/Ruchaka/Sasa) show as MISSING: the
# engine references "Mahapurusha" only as a family, not each member by name — a real detection gap by
# the member names Raman uses (documented in REPORT_yoga_coverage.md, not aliased away).
_ALIAS = {"neechabhanga": "neecha bhanga", "vipareeta": "vipareeta raja", "akhanda": "akhanda samrajya",
          "veshi": "vesi", "vosi": "vasi", "parijatha": "parijata"}


def _stem(name: str) -> str:
    s = re.sub(r"[^a-z ]", "", name.lower()).replace(" yoga", "").replace("yoga", "").strip()
    s = re.sub(r"\s+", " ", s)
    return _ALIAS.get(s, s)


def engine_yoga_stems() -> set[str]:
    names: set[str] = set()
    for f in _CORE:
        t = f.read_text(errors="ignore")
        for m in re.findall(r"\"([A-Za-z][A-Za-z ]+?) ?[Yy]oga\"", t):
            names.add(_stem(m))
        for m in re.findall(r"([A-Z][a-z]+(?:kesari|sari|pha|druma))", t):
            names.add(_stem(m))
        for m in re.findall(r"name\s*=\s*[\"']([A-Za-z ]+)", t):
            names.add(_stem(m))
    return {n for n in names if len(n) > 2}


def run() -> dict[str, Any]:
    corpus = json.loads(_CORPUS.read_text())
    rows = corpus["rows"]
    known = engine_yoga_stems()

    def is_known(name: str) -> bool:
        st = _stem(name)
        return any(st == k or st in k or k in st for k in known)

    covered = [r["name"] for r in rows if is_known(r["name"])]
    missing = [r["name"] for r in rows if not is_known(r["name"])]
    from collections import Counter
    oc = Counter(c for r in rows for c in r["outcome_classes"])
    return {
        "n_yogas": len(rows), "n_example_charts": corpus["n_example_charts"],
        "n_engine_known": len(known),
        "covered": len(covered), "missing": len(missing),
        "coverage_pct": round(100 * len(covered) / len(rows), 1) if rows else 0.0,
        "covered_names": sorted(covered), "missing_names": sorted(missing),
        "outcome_distribution": dict(oc.most_common()),
        "n_with_outcome_class": sum(1 for r in rows if r["outcome_classes"]),
    }


def main() -> None:
    o = run()
    print(f"Three Hundred Important Combinations — yoga-engine coverage audit\n")
    print(f"  corpus: {o['n_yogas']} yogas, {o['n_example_charts']} example charts, "
          f"{o['n_with_outcome_class']} with a coarse outcome class")
    print(f"  engine yoga library knows {o['n_engine_known']} distinct stems")
    print(f"  COVERAGE: {o['covered']}/{o['n_yogas']} = {o['coverage_pct']}% of Raman's named yogas\n")
    print("  covered :", ", ".join(o["covered_names"]))
    print("\n  MISSING (engine blind to these — the gap):")
    for n in o["missing_names"]:
        print("     ", n)
    print("\n  outcome-class distribution (doctrine, not observed):", o["outcome_distribution"])
    if "--json" in sys.argv:
        print("\n" + json.dumps(o, indent=1))


if __name__ == "__main__":
    main()
