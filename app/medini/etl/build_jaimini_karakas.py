"""Build the Jaimini-karakas table (strict 7-karaka scheme — Jaimini Sutras).

For each person, rank ONLY the 7 visible planets by degree-within-sign to
derive the 7 karaka assignments:

  AK   Atmakaraka       self / soul
  AmK  Amatyakaraka     mind / advisor
  BK   Bhratrukaraka    siblings
  MK   Matrukaraka      mother
  PK   Putrakaraka      children
  GK   Gnatikaraka      relatives
  DK   Darakaraka       spouse

**Rahu and Ketu are EXCLUDED** — they are chayagrahas (shadow grahas) and
per strict Jaimini doctrine (BV Raman, Sanjay Rath, the dominant traditional
pandit consensus, and the Jaimini Sutras strict reading) they cannot
signify the soul or any karaka role. AK can NEVER be Rahu or Ketu.

The earlier 8-karaka extension (adding Rahu with longitude-inverted as
"PK2_PutraKaraka2") was a Narasimha-Rao-modern-minority interpretation
and is doctrinally rejected by the project as of 2026-06-01 — see the
`feedback_chara_karakas_7_not_8.md` memory note + CLAUDE.md doctrinal lock.

## Output schema (jaimini_karakas.parquet)

  person_id        TEXT (FK → persons)
  karaka           TEXT one of the 7 labels above
  planet           TEXT  Sun..Saturn (never Rahu/Ketu)
  sign             INT   1..12
  sign_name        TEXT  zodiac sign name
  degree_in_sign   FLOAT 0..30
  natal_house      INT   1..12 from person's natal Lagna
  natal_houses_ruled  TEXT  comma-separated houses this planet rules natally
  ranking_score    FLOAT degree_in_sign; the value used to rank

## Scale

75,149 persons × 7 karakas = 526,043 rows. Tiny parquet (~9-18 MB).

Usage:
    python -m app.medini.etl.build_jaimini_karakas
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final, Any

import pandas as pd

from app.core.ephemeris_engine import ZODIAC_SIGNS
from app.medini.ml.person_profile import (
    _GRAHAS, _houses_ruled_by_planet,
    _JAIMINI_KARAKA_LABELS,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
# Strict 7-karaka Jaimini scheme — 7 visible planets only.
# Rahu/Ketu are excluded as chayagrahas (shadow grahas cannot signify soul).
# See CLAUDE.md locked decision + feedback_chara_karakas_7_not_8.md memory.
_KARAKA_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


def _karakas_for_chart_row(row: pd.Series) -> list[dict[str, Any]]:
    """Compute the 7 karaka assignments for one charts.parquet row."""
    asc_sign = int(row["asc_sign"])
    candidates: list[tuple[str, float, int, float]] = []
    for graha in _KARAKA_PLANETS:
        lon = float(row[f"{graha.lower()}_lon"])
        sign = int(row[f"{graha.lower()}_sign"])
        deg = lon - (sign - 1) * 30.0
        candidates.append((graha, deg, sign, deg))
    # Descending by degree-in-sign; highest gets AK.
    candidates.sort(key=lambda t: t[1], reverse=True)
    out: list[dict[str, Any]] = []
    for i, (planet, score, sign, deg) in enumerate(candidates):
        if i >= len(_JAIMINI_KARAKA_LABELS):
            break
        natal_house = ((sign - asc_sign) % 12) + 1
        houses = _houses_ruled_by_planet(planet, asc_sign)
        out.append({
            "person_id": str(row["person_id"]),
            "karaka": _JAIMINI_KARAKA_LABELS[i],
            "planet": planet,
            "sign": sign,
            "sign_name": ZODIAC_SIGNS[sign - 1],
            "degree_in_sign": deg,
            "natal_house": natal_house,
            "natal_houses_ruled": ",".join(str(h) for h in houses),
            "ranking_score": score,
        })
    return out


def build_jaimini_karakas(charts: pd.DataFrame) -> pd.DataFrame:
    """Vectorisable per-row computation; no multiprocessing needed at this size."""
    rows: list[dict[str, Any]] = []
    for _, row in charts.iterrows():
        rows.extend(_karakas_for_chart_row(row))
    logger.info("Built %d karaka rows for %d persons (7 per person)",
                len(rows), len(charts))
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    charts = pd.read_parquet(args.data_dir / "charts.parquet")
    if args.limit is not None:
        charts = charts.head(args.limit)
    logger.info("Loaded %d charts", len(charts))

    result = build_jaimini_karakas(charts)
    out_path = args.data_dir / "jaimini_karakas.parquet"
    result.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows to %s", len(result), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
