"""B1 research — extract the (FrameLedger features -> Raman verdict) dataset.

For every CONFIRMED Track-B verdict, cast the chart, judge the house, and record the LEAD frame's
FrameLedger features (the same inputs `house_template._decide` consumes) alongside Raman's verdict
and the engine's own verdict. This is the supervised dataset for testing whether a LEARNED decision
function can beat the hand-tuned `_decide` on held-out data.

REPORT-ONLY. Usage: py -3.12 -m tools.raman_saab.b1_decide_dataset  (prints shape + baseline)
"""
from __future__ import annotations

import importlib.util as _ilu
import zlib
from dataclasses import dataclass
from pathlib import Path as _Path

from app.raman_saab.judges import house_template as ht

_HARN = _Path(__file__).resolve().parents[2] / "tests" / "raman_saab" / "test_goldens.py"
_spec = _ilu.spec_from_file_location("_h_b1", _HARN)
_tg = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_tg)

_VERDICTS = {"afflicted": 0, "mixed": 1, "favourable": 2}
_DUSTHANA, _KENDRA, _TRIKONA, _UPACHAYA = {6, 8, 12}, {1, 4, 7, 10}, {1, 5, 9}, {3, 6, 10, 11}
_NAV = {"confirms": 1, "weakens": -1, "neutral": 0, "unknown": 0}
_DEG = {"strong": 2, "moderate": 1, "mild": 0}
_FRAME = {"lagna": 0, "moon": 1, "karaka": 2}

FEATURES = [
    "house", "dusthana", "kendra", "trikona", "upachaya",
    "lord_strong", "karaka_strong", "bhava_bala_strong", "has_shadbala",
    "nav", "karaka_intact", "maraka_active", "parivartana_resilient", "lord_karaka_identical",
    "n_benefic", "n_malefic", "n_neutral", "lead_frame", "degree",
]


def _tri(b) -> int:      # True->1, False->0, None->-1
    return -1 if b is None else (1 if b else 0)


@dataclass
class Row:
    features: list[float]
    raman: int            # 0/1/2
    engine: int           # 0/1/2 (or -1 if insufficient-evidence/absent)
    holdout: bool
    key: str              # id:H<n>:sig


def _row(cid: str, house: int, sig: str, sv, raman: int, holdout: bool) -> Row:
    L = sv.ledger
    feats = [
        float(house), float(house in _DUSTHANA), float(house in _KENDRA),
        float(house in _TRIKONA), float(house in _UPACHAYA),
        float(_tri(L.lord_strong)), float(_tri(L.karaka_strong)), float(_tri(L.bhava_bala_strong)),
        float(L.lord_strong is not None),
        float(_NAV.get(str(L.navamsa_status), 0)),
        float(L.karaka_intact), float(L.maraka_active), float(L.parivartana_resilient),
        float(L.lord_karaka_identical),
        float(len(L.fired_benefic)), float(len(L.fired_malefic)), float(len(L.fired_neutral)),
        float(_FRAME.get(str(sv.lead_frame), 0)), float(_DEG.get(str(sv.degree), 1)),
    ]
    eng = _VERDICTS.get(sv.verdict, -1)
    return Row(feats, raman, eng, holdout, f"{cid}:H{house}:{sig}")


_HOLDOUT_IDS = frozenset({"HTJAH-II.chart_73", "HTJAH-II.chart_74",
                          "HTJAH-II.chart_75", "HTJAH-II.chart_78"})


def _is_holdout(rid: str) -> bool:
    return rid in _HOLDOUT_IDS or zlib.crc32(rid.encode()) % 5 == 0


def build_rows() -> list[Row]:
    rows: list[Row] = []
    for rec in _tg.load_goldens():
        if "B" not in rec.get("track_eligibility", []):
            continue
        cid = str(rec.get("id", ""))
        chart = None
        for htag, c in rec.get("expected_verdicts", {}).items():
            if c.get("verdict_review") != "CONFIRMED" or c.get("verdict") not in _VERDICTS:
                continue
            if chart is None:
                try:
                    chart = _tg.build_chart(rec)
                except Exception:  # noqa: BLE001
                    break
            house = int(htag[1:])
            pf = ht.judge_house(chart, house)
            sv = next((s for s in pf.significations if s.signification == c["signification"]), None)
            if sv is None:
                continue
            rows.append(_row(cid, house, c["signification"], sv,
                             _VERDICTS[c["verdict"]], _is_holdout(cid)))
    return rows


def main() -> int:
    rows = build_rows()
    fit = [r for r in rows if not r.holdout]
    hold = [r for r in rows if r.holdout]
    print(f"rows={len(rows)}  fit={len(fit)}  holdout={len(hold)}  features={len(FEATURES)}")
    from collections import Counter
    print("raman class dist:", dict(Counter(r.raman for r in rows)))
    # engine (current _decide) baseline
    eng_fit = sum(1 for r in fit if r.engine == r.raman) / max(1, len(fit))
    eng_hold = sum(1 for r in hold if r.engine == r.raman) / max(1, len(hold))
    print(f"current _decide accuracy:  fit={eng_fit:.3f}  holdout={eng_hold:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
