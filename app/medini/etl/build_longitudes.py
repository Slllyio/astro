"""Recompute D1 planetary longitudes from the stored birth Julian Day.

`charts.parquet` kept only signs; the confluence model needs **degrees** for the
degree-based classical factors — combustion (a graha within the Sun's orb),
exact conjunction / planetary war (two grahas within ~1°), and moolatrikona
dignity. The sidereal ephemeris is JD-only for planetary longitudes, and
`birth_jd_used` is persisted, so we simply recompute (same proven path as
`build_d9_charts`; recomputed signs reproduce the stored parquet exactly).

Output `charts_lon.parquet`: `person_id` + `{planet}_lon` (sidereal, 0–360°).

Usage::

    python -m app.medini.etl.build_longitudes \\
        --charts app/medini/data/lunarastro_run/charts.parquet \\
        --out app/medini/data/lunarastro_run/charts_lon.parquet
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

logger = logging.getLogger(__name__)
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def longitudes_for(jd: float) -> dict[str, float]:
    """All 9 grahas' sidereal D1 longitudes for one birth JD."""
    lons = {name: float(calculate_d1_position(jd, pid)["longitude"])
            for name, pid in PLANETS.items()}                # 8 grahas (no Ketu)
    rahu_pos = calculate_d1_position(jd, PLANETS["Rahu"])
    lons["Ketu"] = float(calculate_ketu_d1(rahu_pos)["longitude"])
    return {f"{g.lower()}_lon": lons[g] for g in _GRAHAS}


def build(charts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in charts.iterrows():
        jd = r.get("birth_jd_used")
        if pd.isna(jd):
            continue
        rows.append({"person_id": r["person_id"], **longitudes_for(float(jd))})
    return pd.DataFrame(rows)


def run(charts_path: Path, out_path: Path) -> dict[str, object]:
    charts = pd.read_parquet(charts_path)
    lon = build(charts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lon.to_parquet(out_path, index=False)
    logger.info("built longitudes for %d/%d natives -> %s",
                len(lon), len(charts), out_path)
    return {"natives": len(lon), "of": len(charts)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--charts", type=Path,
                        default=Path("app/medini/data/lunarastro_run/charts.parquet"))
    parser.add_argument("--out", type=Path,
                        default=Path("app/medini/data/lunarastro_run/charts_lon.parquet"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.charts, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
