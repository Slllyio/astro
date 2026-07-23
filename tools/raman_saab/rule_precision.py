"""Rule-precision ledger — mine confirmed real outcomes for MISFIRING rules.

The real-outcome corpus (the committed ``field_case_01`` + the private
``data/private/real_outcomes.json``) is normally consumed as a single aggregate scalar
(``static_within1 >= floor``, ``real_outcome_validate.py``). That discards the richest signal
the engine already computes: for EVERY signification verdict, ``sv.ledger.fired_malefic /
fired_benefic`` records exactly WHICH doctrine rules produced it. This tool joins each
owner-confirmed verdict to that per-rule ledger and ranks the rules by how often they fire
AGAINST the confirmed life:

  * a MALEFIC rule that fires on a matter the owner confirms ``favourable`` = a false positive;
  * a BENEFIC rule that fires on a matter the owner confirms ``afflicted`` = a false positive.

This turns the manual "find over-affliction -> propose a narrow gate -> prove zero Raman-golden
regression" craft into a repeatable, auditable pipeline (the discipline the catastrophic gate
and H4.C.18a were held to). Two guardrails are BAKED INTO THE REPORT, not optional:

  * ANTI-OVERFIT: a rule is only flagged SAFE-TO-INVESTIGATE once it misfires on >=2 INDEPENDENT
    confirmed charts. A single-chart misfire is "n=1 — grow the corpus first", never a fix
    licence (fitting a gate to one family chart is textbook overfitting).
  * DOCTRINE-FIRST: this tool only POINTS. Any actual gate change must carry a Raman citation and
    pass ``tests/raman_saab/test_goldens.py`` with ZERO regression — the tool never edits rules.

REPORT-ONLY / read-only: casts charts and reads verdicts; changes no engine state.

Usage:
    py -3.12 -m tools.raman_saab.rule_precision
    py -3.12 -m tools.raman_saab.rule_precision --private data/private/real_outcomes.json
    py -3.12 -m tools.raman_saab.rule_precision --min-charts 1   # show n=1 leads too (default)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import house_template as ht

_FIELD_CASE = Path("tests/fixtures/field_case_01.json")
_PRIVATE = Path("data/private/real_outcomes.json")
_POS = {"afflicted": 0, "mixed": 1, "favourable": 2}


@dataclass
class _Firing:
    case_id: str
    house: int
    sig: str
    polarity: str          # "malefic" | "benefic" (which branch the rule fired in)
    truth: str
    engine: Optional[str]


def _distance(a: Optional[str], b: str) -> int:
    if a in _POS and b in _POS:
        return abs(_POS[a] - _POS[b])
    return 2


@dataclass
class _RuleStat:
    rule_id: str
    citation: str
    firings: list[_Firing] = field(default_factory=list)

    def _is_misfire(self, f: _Firing) -> bool:
        """The rule fired AGAINST the confirmed life (malefic on a good matter, or vice-versa)."""
        if f.polarity == "malefic":
            return f.truth == "favourable"
        return f.truth == "afflicted"

    def _is_consequential(self, f: _Firing) -> bool:
        """A misfire that MATTERS: the engine's final verdict is also on the wrong side of the
        confirmed life. A misfire where the engine still verdicts correctly means the synthesis
        already outweighed the errant rule — benign, not a gap."""
        return self._is_misfire(f) and f.engine != f.truth

    @property
    def consequential(self) -> list[_Firing]:
        return [f for f in self.firings if self._is_consequential(f)]

    @property
    def benign_misfires(self) -> list[_Firing]:
        return [f for f in self.firings if self._is_misfire(f) and not self._is_consequential(f)]

    @property
    def consequential_charts(self) -> set[str]:
        return {f.case_id for f in self.consequential}

    @property
    def worst_distance(self) -> int:
        return max((_distance(f.engine, f.truth) for f in self.consequential), default=0)


def _normalize_cases(field_case: Optional[dict], private: Optional[dict]) -> list[dict]:
    """Both sources -> a flat list of {id, birth, ayanamsa, confirmed_verdicts}."""
    cases: list[dict] = []
    if field_case is not None:
        cases.append({"id": "field_case_01", "birth": field_case["birth"],
                      "ayanamsa": field_case.get("ayanamsa", "raman"),
                      "confirmed_verdicts": field_case.get("confirmed_verdicts", {})})
    for c in (private or {}).get("cases", []):
        cases.append({"id": c.get("id", "case"), "birth": c["birth"],
                      "ayanamsa": c.get("ayanamsa", "raman"),
                      "confirmed_verdicts": c.get("confirmed_verdicts", {})})
    return cases


def _chart(case: dict):
    b = case["birth"]
    return cast_chart(BirthData(name=case["id"], year=b["year"], month=b["month"], day=b["day"],
                                hour=b["hour"], minute=b["minute"], tz_offset=b["tz_offset"],
                                latitude=b["latitude"], longitude=b["longitude"]),
                      ayanamsa=case["ayanamsa"])


def _collect(cases: list[dict]) -> tuple[dict[str, _RuleStat], int, int]:
    """Cast every case, join each confirmed verdict to its fired-rule ledger."""
    stats: dict[str, _RuleStat] = {}
    within1 = total = 0
    for case in cases:
        chart = _chart(case)
        for hstr, sigs in case["confirmed_verdicts"].items():
            proforma = ht.judge_house(chart, int(hstr))
            by_sig = {sv.signification: sv for sv in proforma.significations}
            for sig, truth in sigs.items():
                sv = by_sig.get(sig)
                total += 1
                engine = sv.verdict if sv else None
                if engine in _POS and truth in _POS and abs(_POS[engine] - _POS[truth]) <= 1:
                    within1 += 1
                if sv is None:
                    continue
                for polarity, fired in (("benefic", sv.ledger.fired_benefic),
                                        ("malefic", sv.ledger.fired_malefic)):
                    for fr in fired:
                        rid = fr.rule.id
                        st = stats.get(rid)
                        if st is None:
                            src = fr.rule.source
                            st = stats[rid] = _RuleStat(
                                rule_id=rid, citation=f"{src.work}:{src.line}")
                        st.firings.append(_Firing(case["id"], int(hstr), sig, polarity,
                                                  truth, engine))
    return stats, within1, total


def _load(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Rank doctrine rules by misfire vs confirmed lives.")
    ap.add_argument("--field-case", type=Path, default=_FIELD_CASE)
    ap.add_argument("--private", type=Path, default=_PRIVATE)
    ap.add_argument("--min-charts", type=int, default=1,
                    help="only flag SAFE-TO-INVESTIGATE at >= this many independent charts (2 = "
                         "the anti-overfit threshold); leads below it are shown as n=1.")
    args = ap.parse_args(argv)

    cases = _normalize_cases(_load(args.field_case), _load(args.private))
    if not cases:
        print("[rule-precision] no confirmed cases found — nothing to mine.")
        return 0

    stats, within1, total = _collect(cases)
    consequential = sorted((s for s in stats.values() if s.consequential),
                           key=lambda s: (s.worst_distance, len(s.consequential_charts),
                                          len(s.consequential)), reverse=True)
    benign_rules = sum(1 for s in stats.values() if s.benign_misfires and not s.consequential)

    print(f"[rule-precision] {len(cases)} confirmed chart(s), {total} verdicts, "
          f"engine within-1 = {within1}/{total}")
    print(f"[rule-precision] {len(stats)} distinct rules fired.\n")
    print("A CONSEQUENTIAL misfire = a rule fired against the confirmed life (malefic on a good "
          "matter, or\nbenefic on an afflicted one) AND the engine's final verdict is also wrong. "
          "Those are the real gaps.\nDoctrine-first: a lead is never a licence to edit — any fix "
          "needs a Raman citation + ZERO golden\nregression, and >=2 INDEPENDENT charts before a "
          "gate is touched (n=1 = grow the corpus first).\n")

    thresh = max(2, args.min_charts)
    safe = [s for s in consequential if len(s.consequential_charts) >= thresh]
    leads = [s for s in consequential if s not in safe]

    if safe:
        print("== SAFE-TO-INVESTIGATE (consequential on >=2 independent charts) ==")
        for s in safe:
            _print_rule(s)
        print()
    print("== LEADS (consequential, n=1 chart — GROW THE CORPUS before treating as a gap) ==")
    for s in leads:
        _print_rule(s)
    if not consequential:
        print("  (no rule drove a wrong verdict against a confirmed life)")
    print(f"\n[benign] {benign_rules} further rule(s) fired against a confirmed matter but the "
          f"engine\n         still verdicted correctly (synthesis outweighed them) — not gaps.")
    return 0


def _print_rule(s: _RuleStat) -> None:
    cf = s.consequential
    charts = ", ".join(sorted(s.consequential_charts))
    print(f"  {s.rule_id:<12} ({s.citation})  dist={s.worst_distance}  "
          f"drove {len(cf)}/{len(s.firings)} fires wrong  on chart(s): {charts}")
    for f in cf:
        print(f"        H{f.house}.{f.sig}: fired {f.polarity}, life={f.truth}, "
              f"engine={f.engine} (dist {_distance(f.engine, f.truth)})  [{f.case_id}]")


if __name__ == "__main__":
    raise SystemExit(main())
