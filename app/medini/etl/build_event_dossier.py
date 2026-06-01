"""Build the wide-format event dossier (one row per event).

For every dated event, denormalise its full doctrinal context into a
single ~110-column row: event metadata, active MD/AD/PD dasha lords
with their natal house lordships, and the 9-planet transit state at
event_jd with each transit's sign / degree / natal-house / nakshatra /
houses-ruled / classical flags.

This pre-joins the Silver tables ``events_with_dasha``, ``persons``,
``charts``, ``event_transits`` and ``dasha_pd_windows`` into a single
queryable view — the natural unit of analysis for event-trigger ML and
the doctrine reading layer.

## Output schema (event_dossier.parquet)

Event block (~8 cols):
  event_id, person_id, person_name, event_class, event_date, event_jd,
  age_at_event_years, source

Dasha block (~12 cols): MD/AD/PD lord + their natal houses ruled +
elapsed/window timing.

Transit block (9 grahas × 10 attrs = 90 cols):
  t_{graha}_lon, t_{graha}_sign, t_{graha}_sign_name,
  t_{graha}_degree_in_sign, t_{graha}_natal_house, t_{graha}_nakshatra,
  t_{graha}_nakshatra_pada, t_{graha}_nakshatra_lord,
  t_{graha}_houses_ruled, t_{graha}_in_own_lord_house,
  t_{graha}_is_slow_mover, t_{graha}_is_retrograde

Self-trigger summary (2 cols):
  has_self_trigger_slow_mover, n_self_trigger_slow_movers

## Why recompute natal_house here

The transit's natal-house value depends on the chart's ``asc_sign``.
``event_transits.parquet`` already stores transit_natal_house computed
against the event's tagged person_id. Re-deriving from the canonical
chart here is defensive — if cross-corpus dedup ever changes which
person_id holds the canonical chart, transits stay aligned.

## Scale

Events with non-null event_jd (~62k) × ~110 cols ≈ 25 MB parquet.

Usage:
    python -m app.medini.etl.build_event_dossier
    python -m app.medini.etl.build_event_dossier --limit 1000
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
    _GRAHAS, _houses_ruled_by_planet,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


def _nakshatra_attrs(lon: float) -> tuple[str, int, str]:
    info = nakshatra_for_longitude(lon)
    return NAKSHATRAS[info["index"]], int(info["pada"]), str(info["lord"])


def _transit_block_empty() -> dict[str, Any]:
    """Empty transit block for events with no transit data."""
    out: dict[str, Any] = {}
    for graha in _GRAHAS:
        prefix = "t_" + graha.lower()
        out[f"{prefix}_lon"] = float("nan")
        out[f"{prefix}_sign"] = pd.NA
        out[f"{prefix}_sign_name"] = None
        out[f"{prefix}_degree_in_sign"] = float("nan")
        out[f"{prefix}_natal_house"] = pd.NA
        out[f"{prefix}_nakshatra"] = None
        out[f"{prefix}_nakshatra_pada"] = pd.NA
        out[f"{prefix}_nakshatra_lord"] = None
        out[f"{prefix}_houses_ruled"] = None
        out[f"{prefix}_in_own_lord_house"] = False
        out[f"{prefix}_is_slow_mover"] = False
        out[f"{prefix}_is_retrograde"] = False
    out["has_self_trigger_slow_mover"] = False
    out["n_self_trigger_slow_movers"] = 0
    return out


def _transit_block(
    transits_for_event: pd.DataFrame, asc_sign: int,
) -> dict[str, Any]:
    """Wide transit block for one event — recomputes natal_house against
    the canonical chart's asc_sign.
    """
    out: dict[str, Any] = {}
    has_self_trigger = False
    n_self_trigger_slow = 0
    by_planet = {
        str(r["transit_planet"]): r for _, r in transits_for_event.iterrows()
    }
    for graha in _GRAHAS:
        prefix = "t_" + graha.lower()
        r = by_planet.get(graha)
        if r is None:
            out[f"{prefix}_lon"] = float("nan")
            out[f"{prefix}_sign"] = pd.NA
            out[f"{prefix}_sign_name"] = None
            out[f"{prefix}_degree_in_sign"] = float("nan")
            out[f"{prefix}_natal_house"] = pd.NA
            out[f"{prefix}_nakshatra"] = None
            out[f"{prefix}_nakshatra_pada"] = pd.NA
            out[f"{prefix}_nakshatra_lord"] = None
            out[f"{prefix}_houses_ruled"] = None
            out[f"{prefix}_in_own_lord_house"] = False
            out[f"{prefix}_is_slow_mover"] = False
            out[f"{prefix}_is_retrograde"] = False
            continue
        lon = float(r["transit_lon"])
        sign = int(r["transit_sign"])
        natal_house = ((sign - asc_sign) % 12) + 1
        houses_ruled = _houses_ruled_by_planet(graha, asc_sign)
        in_own = natal_house in houses_ruled
        nak_name, pada, naklord = _nakshatra_attrs(lon)
        is_slow = bool(r["is_slow_mover"])

        out[f"{prefix}_lon"] = lon
        out[f"{prefix}_sign"] = sign
        out[f"{prefix}_sign_name"] = ZODIAC_SIGNS[sign - 1]
        out[f"{prefix}_degree_in_sign"] = lon - (sign - 1) * 30.0
        out[f"{prefix}_natal_house"] = natal_house
        out[f"{prefix}_nakshatra"] = nak_name
        out[f"{prefix}_nakshatra_pada"] = pada
        out[f"{prefix}_nakshatra_lord"] = naklord
        out[f"{prefix}_houses_ruled"] = (
            ",".join(str(h) for h in houses_ruled) if houses_ruled else ""
        )
        out[f"{prefix}_in_own_lord_house"] = in_own
        out[f"{prefix}_is_slow_mover"] = is_slow
        out[f"{prefix}_is_retrograde"] = bool(r["is_retrograde"])

        if in_own and is_slow:
            n_self_trigger_slow += 1
            has_self_trigger = True

    out["has_self_trigger_slow_mover"] = has_self_trigger
    out["n_self_trigger_slow_movers"] = n_self_trigger_slow
    return out


def _build_active_pd_lookup(
    events_with_jd: pd.DataFrame, pd_windows: pd.DataFrame,
) -> dict[int, dict[str, Any]]:
    """Find each event's active PD via merge_asof on (person_id, jd).

    Vimshottari PD windows tile time without gaps within the natal cycle;
    the right PD window is the latest one starting on/before event_jd.
    Events past the 120-year natal cycle have no row — they fall out.
    """
    # pandas.merge_asof requires the merge key (left_on / right_on) to be
    # MONOTONICALLY sorted across the whole frame — `by=person_id` only
    # pre-groups, it doesn't relax the global sort requirement. So sort by
    # event_jd / start_jd primary, not by person_id.
    ev = (
        events_with_jd[events_with_jd["event_jd"].notna()]
        [["event_id", "person_id", "event_jd"]]
        .sort_values("event_jd")
        .reset_index(drop=True)
    )
    pdw = (
        pd_windows[["person_id", "pd_lord", "start_jd", "end_jd"]]
        .sort_values("start_jd")
        .reset_index(drop=True)
    )
    merged = pd.merge_asof(
        ev, pdw,
        by="person_id",
        left_on="event_jd", right_on="start_jd",
        direction="backward",
    )
    merged = merged[merged["end_jd"].notna() & (merged["event_jd"] < merged["end_jd"])]
    lookup: dict[int, dict[str, Any]] = {}
    for _, m in merged.iterrows():
        lookup[int(m["event_id"])] = {
            "active_pd_lord": str(m["pd_lord"]),
            "pd_start_jd": float(m["start_jd"]),
            "pd_end_jd": float(m["end_jd"]),
        }
    return lookup


def _event_columns(
    event_row: pd.Series, person_name: str | None, asc_sign: int,
    pd_info: dict[str, Any] | None,
) -> dict[str, Any]:
    """Event-meta + dasha block for one events_with_dasha row."""
    md_lord = event_row.get("md_lord_at_event")
    ad_lord = event_row.get("ad_lord_at_event")
    md_houses = (
        _houses_ruled_by_planet(str(md_lord), asc_sign)
        if pd.notna(md_lord) else ()
    )
    ad_houses = (
        _houses_ruled_by_planet(str(ad_lord), asc_sign)
        if pd.notna(ad_lord) else ()
    )
    pd_lord = pd_info.get("active_pd_lord") if pd_info else None
    pd_houses = (
        _houses_ruled_by_planet(pd_lord, asc_sign) if pd_lord else ()
    )
    return {
        "event_id": int(event_row["event_id"]),
        "person_id": str(event_row["person_id"]),
        "person_name": person_name,
        "event_class": str(event_row["event_class"]),
        "event_date": (
            str(event_row["event_date"])
            if pd.notna(event_row["event_date"]) else None
        ),
        "event_jd": (
            float(event_row["event_jd"])
            if pd.notna(event_row["event_jd"]) else None
        ),
        "age_at_event_years": (
            float(event_row["age_at_event_years"])
            if pd.notna(event_row["age_at_event_years"]) else None
        ),
        "source": (
            str(event_row["source"])
            if pd.notna(event_row["source"]) else None
        ),
        # Dasha block.
        "active_md_lord": str(md_lord) if pd.notna(md_lord) else None,
        "active_md_natal_houses_ruled": (
            ",".join(str(h) for h in md_houses) if md_houses else ""
        ),
        "md_elapsed_years": (
            float(event_row["md_elapsed_years"])
            if pd.notna(event_row["md_elapsed_years"]) else None
        ),
        "active_ad_lord": str(ad_lord) if pd.notna(ad_lord) else None,
        "active_ad_natal_houses_ruled": (
            ",".join(str(h) for h in ad_houses) if ad_houses else ""
        ),
        "ad_elapsed_years": (
            float(event_row["ad_elapsed_years"])
            if pd.notna(event_row["ad_elapsed_years"]) else None
        ),
        "active_pd_lord": pd_lord,
        "active_pd_natal_houses_ruled": (
            ",".join(str(h) for h in pd_houses) if pd_houses else ""
        ),
        "pd_start_jd": pd_info["pd_start_jd"] if pd_info else None,
        "pd_end_jd": pd_info["pd_end_jd"] if pd_info else None,
    }


def build_event_dossier(
    events_wd: pd.DataFrame, persons: pd.DataFrame, charts: pd.DataFrame,
    transits: pd.DataFrame, pd_windows: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the wide per-event dossier."""
    name_lookup = persons.set_index("person_id")["name"].to_dict()
    asc_lookup = charts.set_index("person_id")["asc_sign"].to_dict()
    pd_lookup = _build_active_pd_lookup(events_wd, pd_windows)
    transits_grouped = transits.groupby("event_id", sort=False)

    rows: list[dict[str, Any]] = []
    n_skipped_no_chart = 0
    for _, e in events_wd.iterrows():
        pid = str(e["person_id"])
        asc_sign = asc_lookup.get(pid)
        if asc_sign is None:
            n_skipped_no_chart += 1
            continue
        asc_sign = int(asc_sign)

        e_id = int(e["event_id"])
        ev_meta = _event_columns(
            e,
            person_name=(
                str(name_lookup[pid]) if pid in name_lookup else None
            ),
            asc_sign=asc_sign,
            pd_info=pd_lookup.get(e_id),
        )
        if e_id in transits_grouped.groups:
            tr_block = _transit_block(transits_grouped.get_group(e_id), asc_sign)
        else:
            tr_block = _transit_block_empty()
        rows.append({**ev_meta, **tr_block})

    logger.info(
        "Assembled %d event dossier rows (from %d events; skipped %d w/o chart)",
        len(rows), len(events_wd), n_skipped_no_chart,
    )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    events_wd = pd.read_parquet(args.data_dir / "events_with_dasha.parquet")
    persons = pd.read_parquet(
        args.data_dir / "persons.parquet",
        columns=["person_id", "name"],
    )
    charts = pd.read_parquet(
        args.data_dir / "charts.parquet",
        columns=["person_id", "asc_sign"],
    )
    transits = pd.read_parquet(args.data_dir / "event_transits.parquet")
    pd_windows = pd.read_parquet(
        args.data_dir / "dasha_pd_windows.parquet",
        columns=["person_id", "pd_lord", "start_jd", "end_jd"],
    )
    logger.info("Loaded events=%d transits=%d pd_windows=%d",
                len(events_wd), len(transits), len(pd_windows))
    if args.limit is not None:
        events_wd = events_wd.head(args.limit)
        # also filter transits/pd_windows to keep merge_asof tractable
        event_ids = set(events_wd["event_id"].tolist())
        transits = transits[transits["event_id"].isin(event_ids)]

    result = build_event_dossier(events_wd, persons, charts, transits, pd_windows)
    out_path = args.data_dir / "event_dossier.parquet"
    result.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows × %d cols to %s",
                len(result), len(result.columns), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
