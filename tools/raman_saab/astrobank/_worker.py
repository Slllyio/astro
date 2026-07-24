"""Stage 2 pool worker — per-person chart cast + full verdict/window extraction (raman track).

The initializer sets ONLY the ephemeris path: `cast_chart` sets its own sidereal mode per call
(`sidereal_mode(ayanamsa)`), so no ayanamsa state needs to cross the process boundary. Do NOT reuse
medini's `lahiri_worker` (it pins SIDM_LAHIRI — wrong track).

`process_person(row) -> dict[str, list[dict]] | None`: all six table row-sets for one person, or
None on any failure (logged upstream by count). Every downstream stage reads the parquet store —
nothing ever re-casts a chart.
"""
from __future__ import annotations

from typing import Any

import swisseph as swe


def init_worker() -> None:
    swe.set_ephe_path(None)   # built-in Moshier, mirrors the engine


def process_person(row: dict[str, Any]) -> dict[str, list[dict]] | None:
    try:
        return _process(row)
    except Exception:  # noqa: BLE001 - per-row failure -> None (counted, never fatal)
        return None


def _process(row: dict[str, Any]) -> dict[str, list[dict]]:
    # imports inside the worker so Windows spawn re-imports cleanly
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.judges import house_template as ht
    from app.raman_saab.primitives import ayurdaya
    from app.raman_saab.primitives import vimshottari as vim

    pid = row["person_id"]
    y, mo, d = (int(x) for x in row["birth_date"].split("-"))
    t = row["birth_time"]
    birth = BirthData(name=pid, year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]),
                      tz_offset=float(row["tz_offset"]), latitude=float(row["latitude"]),
                      longitude=float(row["longitude"]))
    chart = cast_chart(birth, ayanamsa="raman")

    verdicts, rollups = [], []
    for h in range(1, 13):
        pf = ht.judge_house(chart, h)
        rollups.append({"person_id": pid, "house": h, "rollup": pf.rollup})
        for sv in pf.significations:
            verdicts.append({"person_id": pid, "house": h, "signification": sv.signification,
                             "verdict": sv.verdict, "degree": str(sv.degree)})

    res = ayurdaya.longevity(chart)
    ayur = [{"person_id": pid, "method": res.method, "total_years": float(res.total_years),
             "longevity_class": res.longevity_class}]

    # dasha timeline: MD + AD periods over 110y
    timeline = []
    for md in vim.mahadasha_timeline(chart, span_years=110.0):
        timeline.append({"person_id": pid, "level": "MD", "md_lord": md.maha, "antar_lord": "",
                        "jd_start": md.start_jd, "jd_end": md.end_jd})
        for bh in vim.bhuktis(md):
            timeline.append({"person_id": pid, "level": "AD", "md_lord": bh.maha,
                             "antar_lord": bh.antar or "", "jd_start": bh.start_jd,
                             "jd_end": bh.end_jd})
    mds = [r for r in timeline if r["level"] == "MD"]
    ads = [r for r in timeline if r["level"] == "AD"]

    # significator windows per house. Pre-registered instruments:
    #   MD level  = the MD lord belongs to timer_set(house)
    #   AD level  = BOTH the MD and antar lords belong (the tight 'par excellence' instrument,
    #               HTJAH-II:680-694 both-period-lords convergence)
    sig_windows = []
    for h in range(1, 13):
        timers = vim.timer_set(chart, h)
        for r in mds:
            if r["md_lord"] in timers:
                sig_windows.append({"person_id": pid, "house": h, "level": "MD",
                                    "jd_start": r["jd_start"], "jd_end": r["jd_end"]})
        for r in ads:
            if r["md_lord"] in timers and r["antar_lord"] in timers:
                sig_windows.append({"person_id": pid, "house": h, "level": "AD",
                                    "jd_start": r["jd_start"], "jd_end": r["jd_end"]})

    # maraka windows: every AD period, annotated with maraka membership/weights
    mset = vim.maraka_set(chart)
    maraka_rows = []
    for r in ads:
        aw = mset.weight(r["antar_lord"])
        if aw > 0:
            maraka_rows.append({"person_id": pid, "jd_start": r["jd_start"], "jd_end": r["jd_end"],
                                "md_weight": mset.weight(r["md_lord"]), "antar_weight": aw})

    return {"verdicts": verdicts, "house_rollups": rollups, "ayurdaya": ayur,
            "dasha_timeline": timeline, "significator_windows": sig_windows,
            "maraka_windows": maraka_rows}
