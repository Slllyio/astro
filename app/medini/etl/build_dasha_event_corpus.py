"""Fork-A ETL: build a (person, mahadasha-window, event-or-censor) corpus.

Reframes the prediction problem from "did this person ever have a career
event" (the binary screening framing that FAILed across 5 substrates in
Phase 3C) to "during a specific dasha period in this person's life, did
an event of class X happen?" — astrology's native predictive shape.

For each Astro-Databank person with valid birth data AND ≥1 timestamped
event, this script:

  1. Computes the natal chart's Moon longitude and birth JD.
  2. Walks the Vimshottari mahadasha sequence forward from birth for
     `--observation-years` (default 100 years) to cover lifetime.
  3. For each (person, mahadasha) tuple, attributes events from
     ``events_all.csv`` to the window they fall within.
  4. Emits one row per (person × mahadasha) with per-event-class binary
     labels indicating whether any event of that class fired in this
     dasha window.

The output is the substrate for:
  - Stage B: stratified hazard diagnostic (chi-square on
    yoga-active-vs-inactive × event-vs-not 2x2 table per event class).
  - Stage C (conditional): Cox PH with yoga-active flags as
    time-varying covariates per dasha window.
  - Stage D (conditional): Dynamic-DeepHit.

Usage:
    python -m app.medini.etl.build_dasha_event_corpus \\
        --merged data/astro_databank/merged_all.csv \\
        --events data/astro_databank/events_all.csv \\
        --output app/medini/data/dasha_event_corpus.parquet \\
        [--observation-years 100] [--workers N] [--limit N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import multiprocessing as mp
import sys
import traceback
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import (
    DASHA_LORDS, DAYS_PER_VEDIC_YEAR,
    calculate_d1_position, calculate_jd, PLANETS,
)
from app.medini.etl.lahiri_worker import init_worker

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Mahadasha sequence helper                                                   #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class DashaWindow:
    """One mahadasha window in a person's life."""
    seq_idx: int          # 0-indexed sequence number from birth
    lord: str             # mahadasha lord (Ketu, Venus, ..., Mercury)
    start_jd: float       # Julian Day of window start
    end_jd: float         # Julian Day of window end
    duration_years: float # Vimshottari years (not 365.25 calendar years)


@dataclass(frozen=True, slots=True)
class ThreeLevelWindow:
    """A single (MD, AD, PD) window — leaf node of the 3-level Vimshottari cycle."""
    md_seq_idx: int
    ad_seq_idx: int       # 0-8 within the MD
    pd_seq_idx: int       # 0-8 within the AD
    md_lord: str
    ad_lord: str
    pd_lord: str
    start_jd: float
    end_jd: float
    duration_days: float

    @property
    def duration_years(self) -> float:
        return self.duration_days / DAYS_PER_VEDIC_YEAR


def mahadasha_sequence(
    moon_longitude: float,
    birth_jd: float,
    observation_years: float = 100.0,
) -> list[DashaWindow]:
    """Return the full mahadasha sequence from birth covering ``observation_years``.

    Uses the Vimshottari 120-year cycle. The first window is the dasha
    active at birth (typically partial — it started before birth); we
    truncate its start to birth_jd so events can only be attributed
    after birth.

    The walk continues through subsequent dasha lords in the DASHA_LORDS
    cycle until the cumulative duration exceeds ``observation_years``.
    """
    if observation_years <= 0:
        return []

    nakshatra_span = 360.0 / 27.0
    nakshatra_index = int(moon_longitude // nakshatra_span)
    degree_elapsed = moon_longitude % nakshatra_span
    fraction_elapsed = degree_elapsed / nakshatra_span

    lord_index = nakshatra_index % 9
    current_lord, current_total = DASHA_LORDS[lord_index]
    years_remaining = current_total * (1.0 - fraction_elapsed)

    end_obs_jd = birth_jd + observation_years * DAYS_PER_VEDIC_YEAR
    windows: list[DashaWindow] = []

    # Window 0: partial first dasha (truncated to start at birth).
    end_jd = birth_jd + years_remaining * DAYS_PER_VEDIC_YEAR
    windows.append(DashaWindow(
        seq_idx=0,
        lord=current_lord,
        start_jd=birth_jd,
        end_jd=end_jd,
        duration_years=years_remaining,
    ))

    seq = 1
    next_lord_idx = (lord_index + 1) % 9
    cursor = end_jd
    while cursor < end_obs_jd and seq < 50:  # safety bound
        next_lord, next_total = DASHA_LORDS[next_lord_idx]
        dur_days = next_total * DAYS_PER_VEDIC_YEAR
        windows.append(DashaWindow(
            seq_idx=seq,
            lord=next_lord,
            start_jd=cursor,
            end_jd=cursor + dur_days,
            duration_years=float(next_total),
        ))
        cursor += dur_days
        next_lord_idx = (next_lord_idx + 1) % 9
        seq += 1

    return windows


# --------------------------------------------------------------------------- #
# 3-level Vimshottari (MD × AD × PD) sequence                                 #
# --------------------------------------------------------------------------- #
#
# Within each MD of total T_md years:
#   The AD sequence walks the 9 dasha lords starting from the MD lord
#   (so Venus MD starts with Venus AD). AD duration:
#       T_ad(L_ad) = T_md(L_md) × T_total(L_ad) / 120
#   E.g. Venus MD (20y), Sun AD = 20 × 6 / 120 = 1.0 years.
#
# Within each AD of total T_ad years:
#   The PD sequence walks the 9 dasha lords starting from the AD lord
#   (so Sun AD starts with Sun PD). PD duration:
#       T_pd(L_pd) = T_ad(L_ad) × T_total(L_pd) / 120
#
# Both sub-cycles sum exactly to their parent's duration:
#   sum_{L_ad} T_ad(L_ad) = T_md(L_md) × sum_L T_total(L) / 120 = T_md × 1 = T_md
#
# Partial first MD (birth mid-dasha): we also need to identify which AD
# and PD are active at birth, and truncate the first AD/PD windows
# accordingly so events can only attribute after birth.

_LORD_INDEX = {lord: i for i, (lord, _) in enumerate(DASHA_LORDS)}
_LORD_YEARS = {lord: years for lord, years in DASHA_LORDS}
_VIMSHOTTARI_CYCLE_YEARS = sum(years for _, years in DASHA_LORDS)  # 120


def _ad_durations_within_md(md_lord: str) -> list[tuple[str, float]]:
    """Return [(ad_lord, ad_years), ...] in AD order starting from ``md_lord``."""
    start = _LORD_INDEX[md_lord]
    md_years = _LORD_YEARS[md_lord]
    out: list[tuple[str, float]] = []
    for i in range(9):
        ad_lord, ad_total = DASHA_LORDS[(start + i) % 9]
        ad_years = md_years * ad_total / _VIMSHOTTARI_CYCLE_YEARS
        out.append((ad_lord, ad_years))
    return out


def _pd_durations_within_ad(ad_lord: str, ad_years: float) -> list[tuple[str, float]]:
    """Return [(pd_lord, pd_years), ...] in PD order starting from ``ad_lord``."""
    start = _LORD_INDEX[ad_lord]
    out: list[tuple[str, float]] = []
    for i in range(9):
        pd_lord, pd_total = DASHA_LORDS[(start + i) % 9]
        pd_years = ad_years * pd_total / _VIMSHOTTARI_CYCLE_YEARS
        out.append((pd_lord, pd_years))
    return out


def vimshottari_3_level_sequence(
    moon_longitude: float,
    birth_jd: float,
    observation_years: float = 100.0,
) -> list[ThreeLevelWindow]:
    """Return the full (MD × AD × PD) sequence from birth covering observation_years.

    The first MD is truncated to start at birth_jd; its AD/PD sub-cycles
    are run forward (so we don't slice them — the first AD/PD just starts
    at the elapsed offset). Events before the active AD/PD-at-birth
    cannot be attributed to the corpus anyway (they predate birth).

    Each leaf is one ThreeLevelWindow representing a PD-grained window.
    For a 100-year observation: ~9 MDs × 9 ADs × 9 PDs = ~729 windows
    per person; some are very short (a Ketu-Sun-Sun PD is < 13 days).
    """
    if observation_years <= 0:
        return []

    nakshatra_span = 360.0 / 27.0
    nakshatra_index = int(moon_longitude // nakshatra_span)
    fraction_elapsed = (moon_longitude % nakshatra_span) / nakshatra_span
    lord_index = nakshatra_index % 9
    md_lord_birth, md_total_birth = DASHA_LORDS[lord_index]
    years_elapsed_in_md = fraction_elapsed * md_total_birth
    md_start_jd_unbounded = birth_jd - years_elapsed_in_md * DAYS_PER_VEDIC_YEAR

    end_obs_jd = birth_jd + observation_years * DAYS_PER_VEDIC_YEAR
    leaves: list[ThreeLevelWindow] = []

    # Walk forward through MDs.
    md_seq = 0
    md_lord_idx = lord_index
    cursor_md = md_start_jd_unbounded
    while cursor_md < end_obs_jd and md_seq < 50:
        md_lord, md_total_years = DASHA_LORDS[md_lord_idx]
        md_end = cursor_md + md_total_years * DAYS_PER_VEDIC_YEAR

        # Walk ADs within this MD.
        cursor_ad = cursor_md
        for ad_seq, (ad_lord, ad_years) in enumerate(_ad_durations_within_md(md_lord)):
            ad_end = cursor_ad + ad_years * DAYS_PER_VEDIC_YEAR

            # Walk PDs within this AD.
            cursor_pd = cursor_ad
            for pd_seq, (pd_lord, pd_years) in enumerate(
                _pd_durations_within_ad(ad_lord, ad_years)
            ):
                pd_dur_days = pd_years * DAYS_PER_VEDIC_YEAR
                pd_end = cursor_pd + pd_dur_days

                # Truncation: leaf window must be at least partially within
                # [birth_jd, end_obs_jd) to be useful for event attribution.
                leaf_start = max(cursor_pd, birth_jd)
                leaf_end = min(pd_end, end_obs_jd)
                if leaf_start < leaf_end:
                    leaves.append(ThreeLevelWindow(
                        md_seq_idx=md_seq,
                        ad_seq_idx=ad_seq,
                        pd_seq_idx=pd_seq,
                        md_lord=md_lord,
                        ad_lord=ad_lord,
                        pd_lord=pd_lord,
                        start_jd=leaf_start,
                        end_jd=leaf_end,
                        duration_days=leaf_end - leaf_start,
                    ))
                cursor_pd = pd_end
            cursor_ad = ad_end

        cursor_md = md_end
        md_lord_idx = (md_lord_idx + 1) % 9
        md_seq += 1

    return leaves


# --------------------------------------------------------------------------- #
# Date / JD parsers (mirrors databank_etl)                                    #
# --------------------------------------------------------------------------- #

def _birth_jd_from_row(row: dict) -> float | None:
    """Compute birth Julian Day from a merged_all.csv row."""
    try:
        date = dt.date.fromisoformat(row["date_of_birth"])
        h, m, s = map(int, row["time_of_birth"].split(":"))
        tz = float(row["tz_offset"])
    except (ValueError, AttributeError, KeyError, TypeError):
        return None
    decimal_hour = h + m / 60.0 + s / 3600.0
    return calculate_jd(date.year, date.month, date.day, decimal_hour, tz)


def _moon_longitude_at(jd: float) -> float:
    """Sidereal Moon longitude at the given JD."""
    return calculate_d1_position(jd, PLANETS["Moon"])["longitude"]


def _event_jd(event_date_str: str) -> float | None:
    """Parse 'YYYY-MM-DD' → noon JD for event-window attribution."""
    if not event_date_str:
        return None
    try:
        date = dt.date.fromisoformat(event_date_str)
    except (ValueError, TypeError):
        return None
    return swe.julday(date.year, date.month, date.day, 12.0, swe.GREG_CAL)


# --------------------------------------------------------------------------- #
# Per-person worker                                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _PersonInput:
    """Pre-aggregated per-person input for the multiprocessing worker."""
    name: str
    birth_row: dict
    events: tuple[tuple[str, float], ...]  # (event_root, event_jd)
    observation_years: float
    level: str  # 'md' (1-level legacy) or 'mdadpd' (3-level)


def _process_person(p: _PersonInput) -> list[dict[str, Any]] | None:
    """Worker: build all dasha rows for one person at the requested ``level``."""
    try:
        birth_jd = _birth_jd_from_row(p.birth_row)
        if birth_jd is None:
            return None
        moon_lon = _moon_longitude_at(birth_jd)

        event_roots = sorted({e[0] for e in p.events})
        rows: list[dict[str, Any]] = []

        if p.level == "md":
            windows = mahadasha_sequence(moon_lon, birth_jd, p.observation_years)
            for w in windows:
                events_in_window = [
                    root for (root, jd) in p.events
                    if jd is not None and w.start_jd <= jd < w.end_jd
                ]
                row: dict[str, Any] = {
                    "name": p.name,
                    "name_norm": p.name.strip().lower(),
                    "birth_jd": birth_jd,
                    "moon_longitude": moon_lon,
                    "seq_idx": w.seq_idx,
                    "dasha_lord": w.lord,
                    "dasha_start_jd": w.start_jd,
                    "dasha_end_jd": w.end_jd,
                    "dasha_duration_years": w.duration_years,
                    "n_events_in_window": len(events_in_window),
                }
                for root in event_roots:
                    row[f"event_{_slug(root)}"] = int(root in events_in_window)
                rows.append(row)
        elif p.level == "mdadpd":
            leaves = vimshottari_3_level_sequence(
                moon_lon, birth_jd, p.observation_years
            )
            for w in leaves:
                events_in_window = [
                    root for (root, jd) in p.events
                    if jd is not None and w.start_jd <= jd < w.end_jd
                ]
                row = {
                    "name": p.name,
                    "name_norm": p.name.strip().lower(),
                    "birth_jd": birth_jd,
                    "moon_longitude": moon_lon,
                    "md_seq_idx": w.md_seq_idx,
                    "ad_seq_idx": w.ad_seq_idx,
                    "pd_seq_idx": w.pd_seq_idx,
                    "md_lord": w.md_lord,
                    "ad_lord": w.ad_lord,
                    "pd_lord": w.pd_lord,
                    "window_start_jd": w.start_jd,
                    "window_end_jd": w.end_jd,
                    "window_duration_days": w.duration_days,
                    "window_duration_years": w.duration_years,
                    "n_events_in_window": len(events_in_window),
                }
                for root in event_roots:
                    row[f"event_{_slug(root)}"] = int(root in events_in_window)
                rows.append(row)
        else:
            raise ValueError(f"unknown level {p.level!r}")
        return rows
    except Exception:
        logger.warning(
            "person failed (name=%s): %s",
            p.name, traceback.format_exc(limit=2),
        )
        return None


def _slug(s: str) -> str:
    """Stable column-name slug for an event_root."""
    return (
        s.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(",", "")
        .replace(":", "")
        .replace("__", "_")
        .strip("_")
    )


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def _join_inputs(
    merged_path: Path,
    events_path: Path,
    observation_years: float,
    *,
    level: str = "md",
    event_roots: Iterable[str] | None = None,
    limit: int | None = None,
) -> list[_PersonInput]:
    """Load CSVs, filter to viable rows, and pre-aggregate per-person inputs."""
    merged = pd.read_csv(merged_path, low_memory=False)
    events = pd.read_csv(events_path, low_memory=False)
    logger.info("loaded merged=%d rows events=%d rows", len(merged), len(events))

    if event_roots is not None:
        roots_set = set(event_roots)
        events = events[events["event_root"].isin(roots_set)]
        logger.info("filtered events to %d rows for roots=%s",
                    len(events), sorted(roots_set))

    events = events.dropna(subset=["event_date", "name", "event_root"]).copy()
    events["event_jd"] = events["event_date"].apply(_event_jd)
    events = events.dropna(subset=["event_jd"])

    # Validity filter on birth data.
    merged = merged.dropna(
        subset=["date_of_birth", "time_of_birth", "tz_offset", "name"]
    ).copy()
    merged["name"] = merged["name"].astype(str).str.strip()
    merged = merged.drop_duplicates(subset=["name"], keep="first")

    # Join: keep only people with events AND birth data.
    people_with_events = set(events["name"].astype(str).str.strip())
    merged = merged[merged["name"].isin(people_with_events)]
    logger.info("after join: %d people with both birth data + dated events", len(merged))

    if limit is not None:
        merged = merged.iloc[:limit]

    # Group events by person.
    events["name"] = events["name"].astype(str).str.strip()
    events_by_person: dict[str, list[tuple[str, float]]] = {}
    for _, row in events.iterrows():
        events_by_person.setdefault(row["name"], []).append(
            (row["event_root"], float(row["event_jd"]))
        )

    inputs: list[_PersonInput] = []
    for _, row in merged.iterrows():
        evs = events_by_person.get(row["name"], [])
        if not evs:
            continue
        inputs.append(_PersonInput(
            name=row["name"],
            birth_row=row.to_dict(),
            events=tuple(evs),
            observation_years=observation_years,
            level=level,
        ))
    return inputs


def run_etl(
    merged_path: Path,
    events_path: Path,
    output_parquet: Path,
    *,
    observation_years: float,
    level: str = "md",
    event_roots: list[str] | None = None,
    n_workers: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    if level not in {"md", "mdadpd"}:
        raise ValueError(f"--level must be 'md' or 'mdadpd', got {level!r}")
    inputs = _join_inputs(
        merged_path, events_path, observation_years,
        level=level, event_roots=event_roots, limit=limit,
    )
    logger.info("processing %d people level=%s obs=%dy",
                len(inputs), level, observation_years)

    n_workers = n_workers or max(1, mp.cpu_count() - 1)
    if n_workers == 1:
        init_worker()
        all_rows = [_process_person(p) for p in inputs]
    else:
        with mp.Pool(processes=n_workers, initializer=init_worker) as pool:
            all_rows = pool.map(_process_person, inputs)

    flat_rows: list[dict] = []
    n_failed = 0
    for r in all_rows:
        if r is None:
            n_failed += 1
            continue
        flat_rows.extend(r)
    logger.info("dasha-window rows=%d people_failed=%d", len(flat_rows), n_failed)

    if not flat_rows:
        raise RuntimeError("no dasha-event rows produced; check inputs")

    df = pd.DataFrame(flat_rows)
    # Fill missing per-class label columns with 0 (a person didn't have
    # that event class in this particular dasha — pandas leaves NaN when
    # the row didn't carry that column).
    label_cols = [c for c in df.columns if c.startswith("event_")]
    for c in label_cols:
        df[c] = df[c].fillna(0).astype(int)

    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info("wrote %s (rows=%d cols=%d)", output_parquet, len(df), df.shape[1])

    return {
        "input_people": len(inputs),
        "people_failed": n_failed,
        "rows": len(df),
        "n_event_classes": len(label_cols),
        "unique_people_in_output": int(df["name_norm"].nunique()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.build_dasha_event_corpus",
        description="Build (person, mahadasha-window, event-class) corpus.",
    )
    parser.add_argument(
        "--merged", type=Path,
        default=Path("data/astro_databank/merged_all.csv"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/dasha_event_corpus.parquet"),
    )
    parser.add_argument("--observation-years", type=float, default=100.0)
    parser.add_argument(
        "--level", choices=["md", "mdadpd"], default="md",
        help="'md' = one row per mahadasha (~9 per person); "
             "'mdadpd' = one row per pratyantar (~729 per person).",
    )
    parser.add_argument("--event-roots", nargs="+", default=None,
                        help="Restrict to these event_root values (default: all).")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run_etl(
        args.merged, args.events, args.output,
        observation_years=args.observation_years,
        level=args.level,
        event_roots=args.event_roots,
        n_workers=args.workers, limit=args.limit,
    )
    print(
        f"ETL complete: input_people={stats['input_people']} "
        f"failed={stats['people_failed']} "
        f"output_rows={stats['rows']} "
        f"unique_people={stats['unique_people_in_output']} "
        f"event_classes={stats['n_event_classes']} "
        f"-> {args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
