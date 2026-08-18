"""Stage-9 v1 completion scorecard — measure the never-reported gates honestly.

EXECUTION_PLAN.md Stage 9 defines "done (v1)" as: >=90% Track-B accuracy over
>=150 user-CONFIRMED verdicts, a per-house minimum of >=8 confirmed verdicts,
an abstain ceiling (engine insufficient-evidence on <=10% of decisive goldens),
a separately-reported holdout (gated on >=20), rule corpus >= ~900 evaluable
cited rules, and every remaining mismatch documented. The accuracy figure is
reported at every run; the OTHER gates had never been measured. This tool
measures them and prints the scorecard; docs/raman_saab/STAGE9_SCORECARD.md
records a dated snapshot.

Usage:
    python -m tools.raman_saab.stage9_scorecard
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    from app.raman_saab.doctrine.rule_sets import ALL_RULES
    from app.raman_saab.doctrine.yogas import YOGAS
    from tests.raman_saab.test_goldens import (
        _TRACK_B_RATCHET, _id, build_chart, confirmed_verdicts,
        _signification_verdict, track_b_scoreboard)

    correct, total, mismatches = track_b_scoreboard()
    print(f"== Stage-9 v1 scorecard ==")
    print(f"[1] Accuracy bar (>=90% over >=150 confirmed):"
          f"  {correct}/{total} = {correct/total:.3f}"
          f"  -> volume {'MET' if total >= 150 else 'NOT MET'},"
          f" accuracy {'MET' if correct/total >= 0.90 else 'NOT MET'}")

    # [2] per-house confirmed minimums (>=8 each)
    per_house: Counter[int] = Counter()
    abstain_decisive = 0
    decisive_total = 0
    per_house_correct: Counter[int] = Counter()
    for rec in _TRACK_B_RATCHET:
        chart = build_chart(rec)
        for house, entry in confirmed_verdicts(rec):
            per_house[house] += 1
            got = _signification_verdict(chart, house, entry["signification"])
            if got == entry["verdict"]:
                per_house_correct[house] += 1
            if entry["verdict"] != "insufficient-evidence":
                decisive_total += 1
                if got == "insufficient-evidence":
                    abstain_decisive += 1
    print("[2] Per-house minimum (>=8 confirmed each):")
    short = []
    for h in range(1, 13):
        n = per_house.get(h, 0)
        ok = "OK " if n >= 8 else "LOW"
        if n < 8:
            short.append(h)
        acc = per_house_correct.get(h, 0) / n if n else 0.0
        print(f"      H{h:<2} {n:>3} confirmed  [{ok}]  accuracy {acc:.3f}")
    print(f"      -> {'MET' if not short else 'NOT MET (houses ' + str(short) + ')'}")

    # [3] abstain ceiling (<=10% of decisive goldens)
    rate = abstain_decisive / decisive_total if decisive_total else 0.0
    print(f"[3] Abstain ceiling: engine insufficient-evidence on "
          f"{abstain_decisive}/{decisive_total} decisive goldens = {rate:.3f}"
          f"  -> {'MET' if rate <= 0.10 else 'NOT MET'} (ceiling 0.10)")

    # [4] holdout
    print("[4] Holdout (report separately, within 10 pts of fit, gated >=20):"
          "  NOT OPERATIONALIZED — no fit/holdout split exists in the golden"
          " harness; every confirmed verdict participates in the ratchet.")

    # [5] rule corpus (>= ~900 evaluable cited rules)
    evaluable = [r for r in ALL_RULES if getattr(r, "kind", None) == "evaluable"]
    cited = [r for r in ALL_RULES if getattr(r, "source", None) is not None]
    print(f"[5] Rule corpus: {len(ALL_RULES)} placement/combination rules"
          f" ({len(evaluable)} evaluable, {len(cited)} cited) + {len(YOGAS)} yogas"
          f"  -> {'MET' if len(evaluable) >= 900 else 'NOT MET'} (bar ~900 evaluable)")

    # [6] mismatch documentation coverage
    backlog = (_REPO / "docs" / "raman_saab" / "DOCTRINE_BACKLOG.md").read_text(
        encoding="utf-8", errors="replace")
    undocumented = []
    for m in mismatches:
        cid = m.strip().split(" ", 1)[0]                      # e.g. HTJAH-I.chart_09
        short_id = cid.split(".")[-1]                          # chart_09 / h9_02 ...
        if not re.search(re.escape(short_id), backlog):
            undocumented.append(cid)
    print(f"[6] Mismatch documentation: {len(mismatches) - len(undocumented)}/"
          f"{len(mismatches)} mismatches appear in DOCTRINE_BACKLOG.md"
          f"  -> {'MET' if not undocumented else 'NOT MET'}")
    for cid in undocumented:
        print(f"      undocumented: {cid}")


if __name__ == "__main__":
    main()
