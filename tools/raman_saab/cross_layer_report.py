"""Cross-layer convergence report (Layer 4) — do the D1 verdict and the divisional charts agree?

The golden ratchet guards the D1 (Rāśi) verdict in isolation. This measures whether the INDEPENDENT
divisional signal corroborates it. For every golden chart it builds the shodasavarga report
(`varga_judge.build_shodasavarga_report`) — whose per-varga `status` (confirms/weakens/neutral) is
derived from the DIVISIONAL chart's own dignities, NOT from `judge_house` — and compares each varga's
status to the D1 rollup verdict of the house(s) that varga governs (`related_houses`):

  * AGREE           — confirms ↔ favourable, or weakens ↔ afflicted
  * HARD-CONTRADICT — confirms ↔ afflicted, or weakens ↔ favourable  (the polar disagreement)
  * SOFT            — either side is 'mixed' (partial)

An agreement rate well above chance AND below 100% is the healthy signal: the layers are independent
(they differ) yet corroborating (they lean the same way more often than not). REPORT-ONLY / read-only.

Usage:
    py -3.12 -m tools.raman_saab.cross_layer_report
"""
from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import house_template as ht
from app.raman_saab.judges.varga_judge import build_shodasavarga_report

from tools.raman_saab.rule_liveness import golden_charts

_SIGNAL = ("confirms", "weakens")


def _classify(status: str, rollup: str | None) -> str | None:
    """agree / hard / soft, or None when there is no signal on either side."""
    if rollup is None or rollup == "insufficient-evidence":
        return None
    if status == "confirms":
        return "agree" if rollup == "favourable" else "hard" if rollup == "afflicted" else "soft"
    if status == "weakens":
        return "agree" if rollup == "afflicted" else "hard" if rollup == "favourable" else "soft"
    return None


@dataclass(frozen=True)
class Convergence:
    agree: int
    hard: int
    soft: int
    per_varga: dict[str, tuple[int, int, int]]   # "Dn name" -> (agree, hard, soft)

    @property
    def total(self) -> int:
        return self.agree + self.hard + self.soft

    @property
    def agreement_rate(self) -> float:
        return self.agree / self.total if self.total else 0.0

    @property
    def hard_rate(self) -> float:
        return self.hard / self.total if self.total else 0.0


def convergence_stats(charts: list[tuple[str, RamanChart]] | None = None) -> Convergence:
    charts = charts if charts is not None else golden_charts()
    agree = hard = soft = 0
    per: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for _cid, chart in charts:
        try:
            report = build_shodasavarga_report(chart)
        except Exception:  # noqa: BLE001 - a varga build failure is not a convergence signal
            continue
        for r in report.readings:
            if r.status not in _SIGNAL:
                continue
            for house in r.related_houses:
                try:
                    rollup = ht.judge_house(chart, house).rollup
                except Exception:  # noqa: BLE001
                    continue
                c = _classify(r.status, rollup)
                if c is None:
                    continue
                idx = {"agree": 0, "hard": 1, "soft": 2}[c]
                per[f"D{r.n} {r.name}"][idx] += 1
                agree += c == "agree"
                hard += c == "hard"
                soft += c == "soft"
    return Convergence(agree=agree, hard=hard, soft=soft,
                       per_varga={k: (v[0], v[1], v[2]) for k, v in per.items()})


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    charts = golden_charts()
    s = convergence_stats(charts)
    print(f"[cross-layer] golden charts: {len(charts)}   signalled (varga,house) pairs: {s.total}")
    print(f"[cross-layer] AGREE={s.agree} ({s.agreement_rate:.1%})  "
          f"HARD-CONTRADICT={s.hard} ({s.hard_rate:.1%})  SOFT/mixed={s.soft}")
    print("\n  varga                        agree  hard  soft")
    print("  " + "-" * 46)
    for k in sorted(s.per_varga, key=lambda k: int(k.split()[0][1:])):
        a, h, so = s.per_varga[k]
        print(f"  {k:<28} {a:>5} {h:>5} {so:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
