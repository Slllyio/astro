"""Build D9 (Navamsa) signs for every native from the stored birth Julian Day.

`charts.parquet` persisted only D1 signs, not longitudes, so the Navamsa pada
(which needs the degree within a sign) was lost. But `birth_jd_used` is stored,
and the sidereal ephemeris is JD-only for planetary longitudes — so we recompute
each graha's D1 longitude and fold it into D9 with the project's own varga
formula. (Verified: recomputed D1 signs reproduce the stored parquet exactly.)

The D9 *ascendant* is NOT recoverable (it needs the birth lat/long, which were
not persisted), so this builds **planet** navamsa signs only — enough for the
strongest planet-based marriage significators (Venus's navamsa dispositor, the
7th-lord's navamsa dispositor).

Output `charts_d9.parquet`: `person_id` + `{planet}_d9_sign` for the 9 grahas.

Usage::

    python -m app.medini.etl.build_d9_charts \\
        --charts app/medini/data/lunarastro_run/charts.parquet \\
        --out app/medini/data/lunarastro_run/charts_d9.parquet
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.ephemeris_engine import (
    PLANETS, calculate_d1_position, calculate_ketu_d1,
)
from app.core.shodashavarga import compute_divisional_longitude

logger = logging.getLogger(__name__)

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def d9_sign(longitude: float) -> int:
    """Navamsa sign (1..12) for a sidereal D1 longitude."""
    return int(compute_divisional_longitude(longitude, 9) // 30) + 1


def d9_row(jd: float) -> dict[str, int]:
    """All 9 grahas' D9 signs for one birth JD."""
    lons: dict[str, float] = {}
    for name, pid in PLANETS.items():                 # 8 grahas (no Ketu)
        lons[name] = float(calculate_d1_position(jd, pid)["longitude"])
    rahu_pos = calculate_d1_position(jd, PLANETS["Rahu"])
    lons["Ketu"] = float(calculate_ketu_d1(rahu_pos)["longitude"])
    return {f"{g.lower()}_d9_sign": d9_sign(lons[g]) for g in _GRAHAS}


def build(charts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in charts.iterrows():
        jd = r.get("birth_jd_used")
        if pd.isna(jd):
            continue
        rec = {"person_id": r["person_id"]}
        rec.update(d9_row(float(jd)))
        rows.append(rec)
    return pd.DataFrame(rows)


def run(charts_path: Path, out_path: Path) -> dict[str, object]:
    charts = pd.read_parquet(charts_path)
    d9 = build(charts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    d9.to_parquet(out_path, index=False)
    logger.info("built D9 for %d/%d natives -> %s", len(d9), len(charts), out_path)
    return {"natives": len(d9), "of": len(charts)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--charts", type=Path,
                        default=Path("app/medini/data/lunarastro_run/charts.parquet"))
    parser.add_argument("--out", type=Path,
                        default=Path("app/medini/data/lunarastro_run/charts_d9.parquet"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.charts, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
