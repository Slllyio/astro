"""Build the wide-format person dossier (one row per person).

Materialises the comprehensive Agatha-style profile into a flat queryable
parquet — each person becomes a single ~140-column row that bundles
identity, full natal D1 chart with nakshatras, and Jaimini 7-karaka
assignments. The atomic Silver tables (persons, charts, jaimini_karakas,
divisional_charts) remain the source of truth; this dossier is a denormalised
Gold-equivalent for fast single-table reads.

Why wide-format here: the natural query is "give me everything about person
X" — a 4-way JOIN over Silver every time is wasteful for browse/UI/ML
feature extraction. Parquet's column projection means readers that only
want identity pay nothing for the karaka block.

The 15 divisional charts (D1..D60) remain long-format in
``divisional_charts.parquet`` — a single wide row including all vargas
would be ~700 columns, past the point of practical querying. Join on
``person_id`` when you need vargas.

## Output schema (person_dossier.parquet)

Identity block (~10 cols):
  person_id, name, corpus, source, birth_date, birth_time,
  birth_time_confidence, birth_lat, birth_lon, tz_offset, birth_jd

Ascendant block (~8 cols):
  asc_lon, asc_sign, asc_sign_name, asc_degree_in_sign,
  asc_nakshatra, asc_nakshatra_pada, asc_nakshatra_lord, asc_lord

Natal planet block (9 grahas × 9 attrs ≈ 81 cols):
  {graha}_lon, {graha}_sign, {graha}_sign_name, {graha}_degree_in_sign,
  {graha}_natal_house, {graha}_nakshatra, {graha}_nakshatra_pada,
  {graha}_nakshatra_lord, {graha}_houses_ruled

Jaimini karaka block (7 karakas × 6 attrs = 42 cols):
  {prefix}_planet, {prefix}_sign, {prefix}_sign_name,
  {prefix}_degree_in_sign, {prefix}_natal_house, {prefix}_houses_ruled
  where {prefix} ∈ {ak, amk, bk, mk, pk, gk, dk}  (strict 7-karaka Jaimini)

## Scale

~70-75k persons (those with a chart) × ~140 cols ≈ 30 MB parquet.

Usage:
    python -m app.medini.etl.build_person_dossier
    python -m app.medini.etl.build_person_dossier --limit 100
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final, Any

import pandas as pd

from app.core.ephemeris_engine import ZODIAC_SIGNS
from app.core.nakshatra import NAKSHATRAS, nakshatra_for_longitude
from app.medini.ml.person_profile import (
    _GRAHAS, _SIGN_RULERS, _JAIMINI_KARAKA_LABELS, _houses_ruled_by_planet,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


def _corpus_from_person_id(person_id: str) -> str:
    """ADB:..., WD:..., LA:... → 'ADB' / 'WD' / 'LA'."""
    if ":" in person_id:
        return person_id.split(":", 1)[0]
    return ""


def _nakshatra_attrs(lon: float) -> tuple[str, int, str]:
    """Return (nakshatra_name, pada, nakshatra_lord) for a sidereal longitude."""
    info = nakshatra_for_longitude(lon)
    return NAKSHATRAS[info["index"]], int(info["pada"]), str(info["lord"])


def _natal_columns(chart_row: pd.Series) -> dict[str, Any]:
    """Wide natal columns derived from one charts.parquet row.

    Includes ascendant block + per-graha block (9 attrs each). Nakshatra
    pada/lord and houses-ruled aren't stored in charts.parquet — those
    are computed here from longitude and asc_sign.
    """
    asc_lon = float(chart_row["asc_lon"])
    asc_sign = int(chart_row["asc_sign"])
    asc_nak_name, asc_pada, asc_naklord = _nakshatra_attrs(asc_lon)

    out: dict[str, Any] = {
        "asc_lon": asc_lon,
        "asc_sign": asc_sign,
        "asc_sign_name": ZODIAC_SIGNS[asc_sign - 1],
        "asc_degree_in_sign": asc_lon - (asc_sign - 1) * 30.0,
        "asc_nakshatra": asc_nak_name,
        "asc_nakshatra_pada": asc_pada,
        "asc_nakshatra_lord": asc_naklord,
        "asc_lord": _SIGN_RULERS[asc_sign],
    }

    for graha in _GRAHAS:
        prefix = graha.lower()
        lon = float(chart_row[f"{prefix}_lon"])
        sign = int(chart_row[f"{prefix}_sign"])
        house = int(chart_row[f"{prefix}_house"])
        nak_name, pada, naklord = _nakshatra_attrs(lon)
        houses_ruled = _houses_ruled_by_planet(graha, asc_sign)
        out[f"{prefix}_lon"] = lon
        out[f"{prefix}_sign"] = sign
        out[f"{prefix}_sign_name"] = ZODIAC_SIGNS[sign - 1]
        out[f"{prefix}_degree_in_sign"] = lon - (sign - 1) * 30.0
        out[f"{prefix}_natal_house"] = house
        out[f"{prefix}_nakshatra"] = nak_name
        out[f"{prefix}_nakshatra_pada"] = pada
        out[f"{prefix}_nakshatra_lord"] = naklord
        out[f"{prefix}_houses_ruled"] = (
            ",".join(str(h) for h in houses_ruled) if houses_ruled else ""
        )
    return out


def _karaka_columns(karaka_rows: pd.DataFrame) -> dict[str, Any]:
    """Pivot the 7 karaka rows for one person into a wide column block."""
    out: dict[str, Any] = {}
    by_label = {str(r["karaka"]): r for _, r in karaka_rows.iterrows()}
    for label in _JAIMINI_KARAKA_LABELS:
        prefix = label.split("_", 1)[0].lower()  # "ak", "amk", ..., "dk"
        r = by_label.get(label)
        if r is None:
            out[f"{prefix}_planet"] = None
            out[f"{prefix}_sign"] = pd.NA
            out[f"{prefix}_sign_name"] = None
            out[f"{prefix}_degree_in_sign"] = float("nan")
            out[f"{prefix}_natal_house"] = pd.NA
            out[f"{prefix}_houses_ruled"] = None
            continue
        out[f"{prefix}_planet"] = str(r["planet"])
        out[f"{prefix}_sign"] = int(r["sign"])
        out[f"{prefix}_sign_name"] = str(r["sign_name"])
        out[f"{prefix}_degree_in_sign"] = float(r["degree_in_sign"])
        out[f"{prefix}_natal_house"] = int(r["natal_house"])
        out[f"{prefix}_houses_ruled"] = (
            str(r["natal_houses_ruled"])
            if pd.notna(r["natal_houses_ruled"]) else ""
        )
    return out


def _identity_columns(person_row: pd.Series) -> dict[str, Any]:
    """Identity block — denormalises persons.parquet, derives corpus tag."""
    pid = str(person_row["person_id"])
    return {
        "person_id": pid,
        "name": str(person_row["name"]) if pd.notna(person_row["name"]) else None,
        "corpus": _corpus_from_person_id(pid),
        "source": str(person_row["source"]) if pd.notna(person_row["source"]) else None,
        "birth_date": (
            str(person_row["birth_date"])
            if pd.notna(person_row["birth_date"]) else None
        ),
        "birth_time": (
            str(person_row["birth_time"])
            if pd.notna(person_row["birth_time"]) else None
        ),
        "birth_time_confidence": (
            float(person_row["birth_time_confidence"])
            if pd.notna(person_row["birth_time_confidence"]) else None
        ),
        "birth_lat": (
            float(person_row["birth_lat"])
            if pd.notna(person_row["birth_lat"]) else None
        ),
        "birth_lon": (
            float(person_row["birth_lon"])
            if pd.notna(person_row["birth_lon"]) else None
        ),
        "tz_offset": (
            float(person_row["tz_offset"])
            if pd.notna(person_row["tz_offset"]) else None
        ),
        "birth_jd": (
            float(person_row["birth_jd"])
            if pd.notna(person_row["birth_jd"]) else None
        ),
    }


def build_person_dossier(
    persons: pd.DataFrame, charts: pd.DataFrame, karakas: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the wide per-person dossier.

    Only persons with a row in ``charts`` are included — without a chart
    there's no natal block to wide-format. Persons missing karaka rows
    keep null karaka columns rather than being dropped.
    """
    chart_lookup = charts.set_index("person_id")
    karakas_by_pid = dict(tuple(karakas.groupby("person_id", sort=False)))

    rows: list[dict[str, Any]] = []
    for _, p in persons.iterrows():
        pid = str(p["person_id"])
        if pid not in chart_lookup.index:
            continue
        chart_row = chart_lookup.loc[pid]
        if isinstance(chart_row, pd.DataFrame):
            # Defensive: shouldn't happen given charts is one-per-person.
            chart_row = chart_row.iloc[0]
        identity = _identity_columns(p)
        natal = _natal_columns(chart_row)
        karaka_block = _karaka_columns(
            karakas_by_pid.get(pid, karakas.iloc[0:0])
        )
        rows.append({**identity, **natal, **karaka_block})

    logger.info(
        "Assembled %d dossier rows (from %d persons, %d had charts)",
        len(rows), len(persons), len(rows),
    )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap persons (smoke test)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    persons = pd.read_parquet(args.data_dir / "persons.parquet")
    charts = pd.read_parquet(args.data_dir / "charts.parquet")
    karakas = pd.read_parquet(args.data_dir / "jaimini_karakas.parquet")
    logger.info("Loaded persons=%d charts=%d karaka_rows=%d",
                len(persons), len(charts), len(karakas))
    if args.limit is not None:
        persons = persons.head(args.limit)

    result = build_person_dossier(persons, charts, karakas)
    out_path = args.data_dir / "person_dossier.parquet"
    result.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows × %d cols to %s",
                len(result), len(result.columns), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
