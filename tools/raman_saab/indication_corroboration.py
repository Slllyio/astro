"""Indication-corroboration harness — do Raman's own words echo the indications we emit?

WHAT THIS IS NOT. This is **not** an accuracy measure, and it must never be reported as one.
The golden ratchet scores VERDICTS against Raman's graded conclusions on his worked charts.
The non-graded lane (`detailed_report.collected_indications` — the cause-of-end decanate, the
source of gains, the organ, the manner, the count, the profession) has no ordinal to score
against, so it would otherwise ship with **no check at all**. That is the gap this closes.

WHAT IT MEASURES. Each golden verdict row carries `verdict_prose`, Raman's own commentary on
that chart and house. For every indication the engine emits for that house, this asks a narrow
question: do distinctive terms from the indication appear in Raman's prose for the same chart
and the same house? If the engine says the 10th indicates ``judiciary`` and Raman's prose for
that chart says "a Judge", that is CORROBORATION — evidence the lane is surfacing things he
actually talked about.

WHY THE NULL ARM IS NOT OPTIONAL. A corroboration rate alone is uninterpretable: astrological
prose is full of shared vocabulary, so a generous matcher will "corroborate" anything. So the
same measurement is re-run with indications deliberately **misassigned to the wrong charts**.
If the real rate does not clearly exceed the shuffled rate, the matcher is measuring vocabulary
overlap and nothing else, and the honest report is NULL. This mirrors the sham-gate discipline
`astrobank/METHODOLOGY.md` already requires of every real-outcome claim, and it is the whole
reason this tool can be trusted to report a low number.

EXPECT A LOW RATE, AND REPORT IT HONESTLY. Raman's prose states the TYPE of a thing only
sometimes; most of his commentary argues the grade, not the kind. A low corroborated fraction
is the expected, correct result and is not a defect in the engine.

REPORT-ONLY / read-only: builds reports and reads golden prose; changes no engine state and
feeds no verdict.

Usage:
    py -3.12 -m tools.raman_saab.indication_corroboration
    py -3.12 -m tools.raman_saab.indication_corroboration --limit 40
    py -3.12 -m tools.raman_saab.indication_corroboration --show-hits 25
"""
from __future__ import annotations

import argparse
import importlib.util as _ilu
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path as _Path

from app.raman_saab.detailed_report import build_detailed_report, collected_indications

# Load the golden harness by file path (tests/ is deliberately not an importable package) —
# the same device `rule_liveness.py` uses.
_HARNESS_PATH = _Path(__file__).resolve().parents[2] / "tests" / "raman_saab" / "test_goldens.py"
_spec = _ilu.spec_from_file_location("_raman_golden_harness_corroboration", _HARNESS_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS_PATH}")
_harness = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_harness)
load_goldens = _harness.load_goldens

_WORD = re.compile(r"[a-z]{4,}")

#: Records that would not cast, with the reason. Reported at the end rather than
#: dropped — a harness that silently skips inputs reports a rate over an unknown
#: denominator, which is exactly the failure this tool exists to avoid.
_SKIPPED: list[tuple[str, str]] = []

#: Terms too common in astrological prose to evidence anything. Dropped before matching, so a
#: "hit" cannot be carried by shared jargon alone. Deliberately generous — over-pruning costs
#: recall (a lower reported rate), while under-pruning would inflate the number, and this tool
#: exists to avoid inflating it.
_STOP: frozenset[str] = frozenset({
    "house", "houses", "lord", "lords", "native", "planet", "planets", "sign", "signs",
    "malefic", "malefics", "benefic", "benefics", "afflicted", "affliction", "afflictions",
    "favourable", "favorable", "unfavourable", "strong", "strength", "weak", "weakness",
    "aspect", "aspects", "aspected", "conjunction", "conjoined", "with", "will", "have",
    "this", "that", "these", "those", "there", "their", "them", "from", "into", "also",
    "very", "much", "many", "some", "such", "than", "then", "when", "which", "while",
    "results", "result", "indicates", "indicated", "indication", "reading", "chart",
    "raman", "engine", "verdict", "prose", "dasha", "bhukti", "period", "periods",
    "good", "evil", "bad", "well", "give", "gives", "given", "make", "makes", "made",
    "life", "lagna", "karaka", "occupies", "occupied", "placed", "position", "positions",
    "here", "same", "other", "others", "both", "each", "over", "under", "about", "being",
    "because", "however", "though", "although", "should", "would", "could", "must",
    "note", "noted", "case", "chapter", "example", "combination", "combinations",
})


def _terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


@dataclass(frozen=True)
class Corroboration:
    """One indication weighed against Raman's prose for the same chart and house."""
    chart_id: str
    house: int
    category: str
    kind: str
    text: str
    matched: tuple[str, ...]


def _prose_by_house(record: dict) -> dict[int, str]:
    """{house number: Raman's prose for that house} for one golden record."""
    out: dict[int, str] = {}
    for hkey, row in (record.get("expected_verdicts") or {}).items():
        if not isinstance(row, dict):
            continue
        prose = row.get("verdict_prose") or ""
        m = re.fullmatch(r"H(\d{1,2})", str(hkey))
        if m and prose:
            out[int(m.group(1))] = prose
    return out


def _document_frequency(prose_docs: list[str]) -> Counter:
    """How many charts' prose each term appears in — the basis for calling a term
    DISTINCTIVE. A term present in most charts evidences nothing."""
    df: Counter = Counter()
    for doc in prose_docs:
        df.update(_terms(doc))
    return df


def corroborate(limit: int | None = None) -> tuple[list[Corroboration], int, list[Corroboration], int]:
    """(real hits, real total, shuffled hits, shuffled total).

    The shuffled arm pairs each chart's indications with the NEXT chart's prose — a
    deterministic misassignment, so the null is reproducible rather than seeded."""
    records = [g for g in load_goldens() if g.get("expected_verdicts") and g.get("birth")]
    if limit:
        records = records[:limit]

    built: list[tuple[str, dict[int, str], tuple]] = []
    for rec in records:
        prose = _prose_by_house(rec)
        if not prose:
            continue
        try:
            report = build_detailed_report(_birth_of(rec))
        except Exception as exc:               # a record that will not cast is test_goldens'
            _SKIPPED.append((str(rec.get("id")), f"{type(exc).__name__}: {exc}"))
            continue                           # business — but it is COUNTED, never silent
        built.append((str(rec.get("id")), prose, collected_indications(report)))

    if not built:
        return [], 0, [], 0

    df = _document_frequency([p for _i, prose, _g in built for p in prose.values()])
    n_docs = sum(len(prose) for _i, prose, _g in built)
    #: DISTINCTIVE = appears in at most a tenth of the prose documents. Two distinctive terms
    #: must co-occur, or one rare term (<=2%), before a row counts as corroborated. Set once,
    #: before looking at any result, and reported alongside the number it produced.
    common_cut = max(2, n_docs // 10)
    rare_cut = max(1, n_docs // 50)

    def _score(prose: dict[int, str], groups: tuple) -> tuple[list[Corroboration], int]:
        hits: list[Corroboration] = []
        total = 0
        for label, rows in groups:
            for house, kind, _sig, text, _cite in rows:
                doc = prose.get(house)
                if not doc:
                    continue
                total += 1
                shared = _terms(text) & _terms(doc)
                distinctive = tuple(sorted(t for t in shared if df[t] <= common_cut))
                rare = [t for t in distinctive if df[t] <= rare_cut]
                if len(distinctive) >= 2 or rare:
                    hits.append(Corroboration(_id_of(prose), house, label, kind, text,
                                              distinctive))
        return hits, total

    real_hits: list[Corroboration] = []
    real_total = 0
    sham_hits: list[Corroboration] = []
    sham_total = 0
    for i, (cid, prose, groups) in enumerate(built):
        globals()["_CURRENT_ID"] = cid
        h, t = _score(prose, groups)
        real_hits += h
        real_total += t
        # the null arm: this chart's indications against the NEXT chart's prose
        other_prose = built[(i + 1) % len(built)][1]
        globals()["_CURRENT_ID"] = f"{cid}~sham"
        h2, t2 = _score(other_prose, groups)
        sham_hits += h2
        sham_total += t2
    return real_hits, real_total, sham_hits, sham_total


def _id_of(_prose: dict) -> str:
    return str(globals().get("_CURRENT_ID", "?"))


def _birth_of(rec: dict):
    """`BirthData` from a golden record's `birth` block, whose schema is
    {dt: "YYYY-MM-DDTHH:MM:SS", tz, lat, lon} — the shape `test_goldens.build_chart` reads."""
    from datetime import datetime

    from app.raman_saab.chart.model import BirthData
    b = rec["birth"]
    dt = datetime.fromisoformat(str(b["dt"]))
    return BirthData(str(rec.get("name") or rec.get("id")), dt.year, dt.month, dt.day,
                     dt.hour, dt.minute, float(b["tz"]), float(b["lat"]), float(b["lon"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None,
                    help="cast only the first N golden records (a fast smoke run)")
    ap.add_argument("--show-hits", type=int, default=15,
                    help="print this many corroborated rows as evidence")
    args = ap.parse_args()

    real, real_n, sham, sham_n = corroborate(args.limit)
    if _SKIPPED:
        print(f"[corroboration] {len(_SKIPPED)} record(s) would not cast and are EXCLUDED "
              f"from the denominator:")
        for rid, why in _SKIPPED[:8]:
            print(f"    {rid}: {why}")
        print()
    if not real_n:
        print("[corroboration] no golden record produced both prose and indications")
        return

    r_rate = len(real) / real_n
    s_rate = (len(sham) / sham_n) if sham_n else 0.0
    print("[corroboration] Raman's own prose vs the engine's non-graded indications")
    print(f"  corroborated : {len(real)}/{real_n} = {r_rate:.1%}")
    print(f"  SHAM (wrong chart's prose) : {len(sham)}/{sham_n} = {s_rate:.1%}")
    lift = r_rate - s_rate
    print(f"  lift over sham : {lift:+.1%}")
    print()
    if lift <= 0.02:
        print("  VERDICT: NULL. The real rate does not clearly exceed the misassigned-prose")
        print("  baseline, so this is measuring shared astrological vocabulary, not")
        print("  corroboration. Report it as null; do NOT quote the raw rate as a result.")
    else:
        print("  VERDICT: the real rate exceeds the misassigned baseline. This is")
        print("  CORROBORATION -- evidence that the lane surfaces things Raman discussed on")
        print("  the same chart. It is NOT accuracy: nothing here scores a prediction, and it")
        print("  must never be averaged with the golden ratchet or quoted beside it as if it")
        print("  were a second fidelity figure.")
    print()
    by_cat = Counter(h.category for h in real)
    print("  corroborated by category:")
    for cat, n in by_cat.most_common():
        print(f"    {n:4d}  {cat}")
    if args.show_hits and real:
        print(f"\n  first {min(args.show_hits, len(real))} corroborated rows:")
        for h in real[: args.show_hits]:
            print(f"    H{h.house:<2d} [{h.kind}] {h.text[:78]}")
            print(f"         shared distinctive terms: {', '.join(h.matched) or '-'}")


if __name__ == "__main__":
    main()
