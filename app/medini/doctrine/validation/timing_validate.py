"""Held-out TIMING validation: does the engine's Vimshottari period arithmetic place
Raman's stated events in the mahadasha / bhukti he names?

The strength harness (``worked_chart_validate``) scores bhava/lord/karaka *strength*;
this is its timing counterpart. Raman prints, per worked chart, a **balance of dasa at
birth** ("Balance of Ketu Dasa at birth: 2-1-25") and states **when events fell** ("the
mother died when the native was aged 3 in Venus Dasa, Venus Bhukti"). We seed the MD/AD
timeline from his *printed balance* (Route 2 -- no degrees, ephemeris, or timezone
needed: the balance line alone fixes the whole timeline) and check whether each event's
age lands in the mahadasha (MD) and bhukti (AD) he names.

It reuses the LIVE engine's own period builder ``_antardasha_spans``
(``house_judgment``) and the locked ``DASHA_LORDS`` order + ``DAYS_PER_VEDIC_YEAR`` -- so
the test judges the engine's arithmetic, not a re-implementation. MD match is robust to
Raman's ~+/-1yr age phrasing ("about 32"); AD match is stricter, so we also report
AD-adjacent (the stated bhukti borders the computed one -- within the age rounding).

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.timing_validate \
      docs/raman_doctrine/validation/corpora/heldout_timing.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR
from app.medini.doctrine.domains.house_judgment import _DASHA_YEARS, _antardasha_spans

_LORDS = [l for l, _ in DASHA_LORDS]
_DAYS_PER_MONTH = DAYS_PER_VEDIC_YEAR / 12.0


def balance_years(bal: dict) -> float:
    """Raman's 'Y-M-D' balance line -> remaining years of the birth mahadasha."""
    return (bal["years"] + bal["months"] * _DAYS_PER_MONTH / DAYS_PER_VEDIC_YEAR
            + bal["days"] / DAYS_PER_VEDIC_YEAR)


def maha_sequence_from_balance(lord0: str, remaining: float
                               ) -> list[tuple[str, float, float]]:
    """MD windows (lord, start_age, end_age) from birth, seeded by the printed balance
    -- mirrors ``house_judgment._maha_sequence`` but from (lord0, remaining) instead of
    the Moon longitude, so no ephemeris is needed."""
    idx0 = _LORDS.index(lord0)
    seq = [(lord0, 0.0, remaining)]
    cursor = remaining
    for step in range(1, 9):
        lord, years = DASHA_LORDS[(idx0 + step) % 9]
        seq.append((lord, cursor, cursor + years))
        cursor += years
    return seq


def _span_at(age: float, spans: list[tuple[str, float, float]]) -> tuple[str, float, float] | None:
    for lord, s, e in spans:
        if s <= age < e:
            return lord, s, e
    return None


def locate(age: float, lord0: str, remaining: float) -> dict[str, Any]:
    """Which MD and AD covers ``age``, seeded from the printed balance. The balance MD
    (lord0) carries ``elapsed_into_md = total - remaining`` so its bhukti windows are
    birth-clipped exactly as the live engine does; later MDs start fresh."""
    seq = maha_sequence_from_balance(lord0, remaining)
    md = _span_at(age, seq)
    if md is None:
        return {"md": None, "ad": None, "ad_neighbours": []}
    md_lord, md_s, md_e = md
    elapsed = (_DASHA_YEARS[lord0] - remaining) if md_lord == lord0 else 0.0
    ads = _antardasha_spans(md_lord, md_s, md_e, elapsed)
    hit = _span_at(age, ads)
    ad = hit[0] if hit else None
    # the bhukti immediately before/after (for the age-rounding tolerance report)
    neigh = []
    for i, (lord, s, e) in enumerate(ads):
        if hit and lord == hit[0]:
            if i > 0:
                neigh.append(ads[i - 1][0])
            if i + 1 < len(ads):
                neigh.append(ads[i + 1][0])
    return {"md": md_lord, "ad": ad, "ad_neighbours": neigh}


def validate_record(rec: dict) -> dict[str, Any]:
    bal = rec.get("balance_of_dasa")
    if not bal:
        return {"chart": rec.get("chart_no"), "excluded": "no_balance"}
    lord0, remaining = bal["lord"], balance_years(bal)
    rows = []
    for ev in rec.get("events", []):
        age = ev.get("age_years")
        if age is None:
            rows.append({"desc": ev.get("desc", ""), "excluded": "no_age"})
            continue
        got = locate(float(age), lord0, remaining)
        md_ok = got["md"] == ev.get("md")
        ad_ok = got["ad"] == ev.get("ad") if ev.get("ad") else None
        ad_adj = (ev.get("ad") in got["ad_neighbours"]) if ev.get("ad") else None
        rows.append({"desc": ev.get("desc", ""), "age": age,
                     "raman_md": ev.get("md"), "engine_md": got["md"], "md_ok": md_ok,
                     "raman_ad": ev.get("ad"), "engine_ad": got["ad"],
                     "ad_ok": ad_ok, "ad_adjacent": ad_adj})
    return {"chart": rec.get("chart_no"), "balance": f"{lord0} {remaining:.3f}y", "rows": rows}


def run(corpus_path: str | list[str]) -> dict[str, Any]:
    paths = [corpus_path] if isinstance(corpus_path, str) else list(corpus_path)
    records: list[dict] = []
    for p in paths:
        corpus = json.loads(Path(p).read_text())
        records += corpus["charts"] if isinstance(corpus, dict) else corpus
    scored, excluded = [], []
    for rec in records:
        res = validate_record(rec)
        if res.get("excluded"):
            excluded.append(res)
            continue
        for row in res["rows"]:
            if row.get("excluded"):
                excluded.append({"chart": res["chart"], **row})
            else:
                scored.append({"chart": res["chart"], **row})
    n = len(scored)
    md_hit = sum(1 for r in scored if r["md_ok"])
    ad_scored = [r for r in scored if r["ad_ok"] is not None]
    ad_hit = sum(1 for r in ad_scored if r["ad_ok"])
    ad_adj = sum(1 for r in ad_scored if r["ad_ok"] or r["ad_adjacent"])
    return {
        "n_events": n,
        "md_exact": md_hit, "md_pct": round(100 * md_hit / n, 1) if n else 0.0,
        "ad_n": len(ad_scored),
        "ad_exact": ad_hit, "ad_pct": round(100 * ad_hit / len(ad_scored), 1) if ad_scored else 0.0,
        "ad_within_one_bhukti": ad_adj,
        "ad_adj_pct": round(100 * ad_adj / len(ad_scored), 1) if ad_scored else 0.0,
        "rows": scored, "n_excluded": len(excluded), "excluded": excluded,
    }


def _print(s: dict) -> None:
    print(f"events={s['n_events']}  MD exact={s['md_exact']} ({s['md_pct']}%)  "
          f"AD exact={s['ad_exact']}/{s['ad_n']} ({s['ad_pct']}%)  "
          f"AD +/-1 bhukti={s['ad_within_one_bhukti']}/{s['ad_n']} ({s['ad_adj_pct']}%)")
    for r in s["rows"]:
        md = "OK " if r["md_ok"] else "XX "
        ad = "--" if r["ad_ok"] is None else ("OK" if r["ad_ok"] else ("~adj" if r["ad_adjacent"] else "XX"))
        print(f"  ch{r['chart']} age {r['age']:>4}  MD {md} raman={r['raman_md']:<8} eng={r['engine_md']:<8} "
              f"| AD {ad:<4} raman={r['raman_ad']} eng={r['engine_ad']}   \"{r['desc'][:34]}\"")
    if s["excluded"]:
        print(f"excluded={s['n_excluded']}: " + ", ".join(
            f"ch{e.get('chart')}:{e.get('excluded')}" for e in s["excluded"]))


def main() -> None:
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not paths:
        print(__doc__)
        raise SystemExit(2)
    s = run(paths if len(paths) > 1 else paths[0])
    _print(s)
    if "--json" in sys.argv:
        print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
