"""Phase 3 instrument store: Raman's activation tier for every Vimshottari (MD, AD) period x 12 houses.

Map-agnostic on purpose: it stores the tier for ALL houses, so the event->house map
(PHASE3_TIMING_PREREG.md) can be fixed or reviewed without re-casting. Reads no outcomes.

Tier of an (MD, AD) period for house H (HTJAH-I:1592-1596; locked dasha-activation convention):
  4 both lords influence H and are associated (same sign or mutual aspect)   par excellence
  3 both influence, not associated                                         ordinary
  2 only the AD lord influences                                            limited
  1 only the MD lord influences                                            feeble
  0 neither
"Influence" = activation.influences (own / occupy / aspect H or its lord: Raman's factors a-e,
HTJAH-I:1586-1588) PLUS factor (f), being the lord of the H-th house counted from the Moon
(HTJAH-I:2586; locked convention "the lord-from-the-Moon"), added here because the engine's
influences() omits it. MD-level exposure: the MD lord influences H  <=>  tier in {1, 3, 4}.
`t_mk` = the same tier scheme with "influence" replaced by PRIMARY MARAKA (death; HTJAH-II:4494-4509):
lord of the 2nd or 7th, an occupant of the 2nd or 7th, or conjunct the 2nd/7th lord.
`conj` = the two lords are conjunct (Raman's textual "association"); `assoc` used in the tiers also
admits mutual aspect (project lock), so conj-only tier 4 is a sensitivity arm.

Variants: "real" = the engine's own dashas (reading._dashas); "placebo" = the dasha seeded ONE
nakshatra ahead (same elapsed fraction): right chart, wrong dasha sequence.

Usage:
    py -3.12 -m tools.validation.activation_store --derived E:/astro/data/astro_databank/derived --tiers A,B --ayanamsa lahiri --out E:/astro/data/validation/activation_lahiri_AB.parquet
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import multiprocessing as mp
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import swisseph as swe

HOUSES = tuple(range(1, 13))
_SIDM = {"lahiri": None, "raman": swe.SIDM_RAMAN}


def _init(ayanamsa: str) -> None:
    from tools.validation import reliability
    reliability.install_ayanamsa_patch()
    reliability._TARGET[0] = _SIDM[ayanamsa]


def associated(md: str, ad: str, signs: dict[str, int]) -> bool:
    """Raman's 'associated': conjunct (same sign) or in mutual aspect."""
    from app.parashara.primitives.graha_drishti import aspects_sign
    from app.parashara.synthesis.chart_facts import ASPECTING_GRAHAS
    a, b = signs.get(md), signs.get(ad)
    if a is None or b is None:
        return False
    if a == b:
        return True
    return (md in ASPECTING_GRAHAS and ad in ASPECTING_GRAHAS
            and aspects_sign(md, a, b) and aspects_sign(ad, b, a))


def tier(md_inf: bool, ad_inf: bool, assoc: bool) -> int:
    if md_inf and ad_inf:
        return 4 if assoc else 3
    return 2 if ad_inf else 1 if md_inf else 0


def primary_maraka(planet: str, chart, signs: dict[str, int]) -> bool:
    """Raman's primary marakas (HTJAH-II:4494-4509): lord of 2/7, occupant of 2/7, conjunct their lords."""
    from app.parashara.primitives.relationships import SIGN_LORDS
    from app.parashara.synthesis.chart_facts import house_sign
    s = signs.get(planet)
    for h in (2, 7):
        hs = house_sign(chart.asc_sign, h)
        lord = SIGN_LORDS[hs]
        if planet == lord or s == hs or (s is not None and s == signs.get(lord)):
            return True
    return False


def influence(planet: str, house: int, chart, signs: dict[str, int]) -> bool:
    """Raman factors a-e (engine `influences`) + f: lord of the house counted from the Moon."""
    from app.parashara.primitives.relationships import SIGN_LORDS
    from app.parashara.synthesis.activation import influences
    if influences(chart, planet, house, signs=signs):
        return True
    moon_house_sign = (signs["Moon"] - 1 + house - 1) % 12 + 1
    return planet == SIGN_LORDS[moon_house_sign]


def periods(chart, dashas) -> list[tuple]:
    from app.parashara.synthesis.chart_facts import planet_signs
    signs = planet_signs(chart)
    vim = next(d for d in dashas if d.system == "vimshottari")
    inf: dict[str, list[bool]] = {}
    mk: dict[str, bool] = {}
    out = []
    for maha, bhuktis in vim.bhuktis:
        for b in bhuktis:
            if b.end_year <= 0:
                continue
            for p in (maha, b.lord):
                if p not in inf:
                    inf[p] = [influence(p, h, chart, signs) for h in HOUSES]
                    mk[p] = primary_maraka(p, chart, signs)
            assoc = associated(maha, b.lord, signs)
            conj = signs.get(maha) is not None and signs.get(maha) == signs.get(b.lord)
            out.append((maha, b.lord, max(0.0, b.start_year), b.end_year,
                        *(tier(inf[maha][i], inf[b.lord][i], assoc) for i in range(12)),
                        tier(mk[maha], mk[b.lord], assoc), conj))
    return out


def process(row: dict[str, Any]) -> list[tuple] | None:
    try:
        from app.parashara.chart.cast import cast
        from app.parashara.reading import _dashas
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        chart = cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]),
                     tz_offset=float(row["tz_offset"]), latitude=float(row["latitude"]),
                     longitude=float(row["longitude"]))
        placebo = dataclasses.replace(chart, janma_nakshatra=chart.janma_nakshatra % 27 + 1)
        return ([(row["person_id"], "real", *p) for p in periods(chart, _dashas(chart))]
                + [(row["person_id"], "placebo", *p) for p in periods(chart, _dashas(placebo))])
    except Exception:  # noqa: BLE001 - per-row failure counted, never fatal
        return None


COLUMNS = ["person_id", "variant", "md", "ad", "start_age", "end_age", *(f"t{h}" for h in HOUSES),
           "t_mk", "conj"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--tiers", default="A,B")
    ap.add_argument("--ayanamsa", choices=tuple(_SIDM), default="lahiri")
    ap.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) - 2))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    master = pd.read_parquet(a.derived / "raman" / "person_master.parquet")
    sel = master[master.quality_tier.isin(a.tiers.split(","))
                 & master.birth_time.str.match(r"^\d\d:\d\d")
                 & master.birth_date.str.match(r"^\d{4}-\d\d-\d\d$")]
    rows = sel[["person_id", "birth_date", "birth_time", "tz_offset", "latitude", "longitude"]] \
        .dropna().to_dict("records")[: a.limit]
    t0, recs, fails = time.perf_counter(), [], 0
    with mp.Pool(a.workers, initializer=_init, initargs=(a.ayanamsa,)) as pool:
        for i, r in enumerate(pool.imap_unordered(process, rows, chunksize=50)):
            if r is None:
                fails += 1
            else:
                recs.extend(r)
            if i % 5000 == 0:
                print(f"[activation] {i}/{len(rows)} ({(time.perf_counter()-t0)/60:.1f} min)")
    df = pd.DataFrame.from_records(recs, columns=COLUMNS)
    df[[*(f"t{h}" for h in HOUSES), "t_mk"]] = df[[*(f"t{h}" for h in HOUSES), "t_mk"]].astype(np.int8)
    df[["start_age", "end_age"]] = df[["start_age", "end_age"]].astype(np.float32)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(a.out, compression="zstd", index=False)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
    a.out.with_suffix(".manifest.json").write_text(json.dumps({
        "n_selected": len(rows), "n_failures": fails, "tiers": a.tiers, "ayanamsa": a.ayanamsa,
        "engine_sha": sha, "built": time.strftime("%Y-%m-%d %H:%M")}, indent=2), encoding="utf-8")
    print(f"[activation] DONE {len(rows)-fails}/{len(rows)} people, {len(df)} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
