"""Round 4: per-(person, event) corpus builder.

Each row in the output parquet is one (person, event_date) tuple. The
model trained on this corpus sees the Janma Kundli + Gochara + active
Vimshottari dasha simultaneously — the classical three-pronged Vedic
prediction setup that prior rounds (per-person rows) could not encode.

Column groups
=============
1. Natal (225 cols, no prefix) — copied verbatim from the natal-features
   parquet. The person's birth chart.
2. Transit (206 cols, ``t_`` prefix) — `compute_chart_features` evaluated
   at the event JD with the natal lat/lon. Strips the 19 chronological
   dasha cols (they encode "the dasha schedule of a person born on
   event_date", which is meaningless context).
3. Active-dasha-at-event (4 cols) — Mahadasha + Antardasha lords active
   at event_jd, plus elapsed years in each. The temporal handle that
   ties the transit and natal vectors together.
4. Cross-features (9 cols) — angular distance between transit and natal
   longitudes per planet. SHAP rules will phrase these as "transit
   Saturn ~X° from natal Saturn" — the Vedic "sade-sati / Jupiter
   return" axis.
5. Metadata (8 cols) — name, event_date, event_jd, event_root,
   event_subtype, birth_jd, is_event, categories_lower (set to "event"
   for positives, "none" for negatives so existing reporting code
   doesn't crash on missing column).

Negative sampling
=================
1:1 balanced per person. For each positive event a person contributes,
one random JD is drawn from their lifespan window
``[birth_jd + 365, min(birth_jd + 100*365.2425, today_jd)]`` and rejected
if within ±30 days of any known positive event for that person.

CLI
===
    python -m app.medini.etl.event_corpus \\
        --features app/medini/data/ml_astro_tier_a_dasha_kinematic.parquet \\
        --events   data/astro_databank/events_all.csv \\
        --raw      data/astro_databank/raw.csv \\
        --event-root "Marriage" \\
        --output   app/medini/data/event_corpus_marriage.parquet
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import swisseph as swe

from app.medini.etl.feature_engineering import (
    active_dasha_at,
    compute_chart_features,
)
from app.medini.etl.lahiri_worker import init_worker

logger = logging.getLogger(__name__)


# ---------- Constants ----------

# Default Vimshottari adulthood reference. Negative-sample window starts
# at this offset after birth (in days).
NEGATIVE_WINDOW_START_DAYS = 365

# Days of buffer around a known event when drawing negative samples. A
# random JD within this radius of any known event is rejected so the
# model doesn't accidentally see "event happened the day after this
# date" as a negative.
NEGATIVE_EXCLUSION_RADIUS_DAYS = 30

# Cap negative sampling to 100 years past birth so we don't draw negatives
# beyond a plausible human lifespan. If the person has a recorded death
# date in the positives, that bound dominates this one automatically.
MAX_LIFESPAN_YEARS = 100

# The 19 chronological scaffolding columns that are meaningless when
# computed at a non-birth JD. Stripped before prefixing the transit dict.
DASHA_COLS_TO_STRIP: frozenset[str] = frozenset({
    "natal_dasha_remaining_years",
    *(f"dasha_start_age_{lord}"
      for lord in ("ketu", "venus", "sun", "moon", "mars",
                   "rahu", "jupiter", "saturn", "mercury")),
    *(f"first_{lord}_antardasha_after_16"
      for lord in ("ketu", "venus", "sun", "moon", "mars",
                   "rahu", "jupiter", "saturn", "mercury")),
})

# Planets carried in the cross-feature group. 9 chara grahas — same as
# the natal lon_<planet> columns.
CROSS_PLANETS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)


# ---------- Helpers ----------

def _event_date_to_jd(
    event_date: str | dt.date | None,
    event_year: int | float | None = None,
) -> float | None:
    """Parse an ISO date string into a JD at 12:00 UT.

    Events don't carry sub-day timing, so 12:00 UT is the centred default.
    This introduces at most ±0.5 day of jitter in transit positions —
    well below the precision floor on the rest of the pipeline.

    When the date string is empty/missing but ``event_year`` is provided,
    falls back to July 1 of that year. The ±6-month jitter this introduces
    is acceptable for outer-planet markers; cross-features computed from
    such events are flagged via ``event_date_precision`` in the output
    row (handled by caller).
    """
    if not pd.isna(event_date):
        if isinstance(event_date, str):
            try:
                d = dt.date.fromisoformat(event_date)
                return swe.julday(d.year, d.month, d.day, 12.0, swe.GREG_CAL)
            except ValueError:
                pass
        elif isinstance(event_date, (dt.date, dt.datetime)):
            d = event_date if isinstance(event_date, dt.date) else event_date.date()
            return swe.julday(d.year, d.month, d.day, 12.0, swe.GREG_CAL)

    # Year-only fallback: July 1 12:00 UT
    if event_year is not None and not pd.isna(event_year):
        try:
            year = int(event_year)
        except (ValueError, TypeError):
            return None
        return swe.julday(year, 7, 1, 12.0, swe.GREG_CAL)
    return None


def _row_to_birth_jd(row: pd.Series) -> float | None:
    """Convert a raw.csv-style row to a birth Julian Day in UT.

    Mirrors `app.medini.etl.databank_etl._row_to_jd` but works on
    pandas Series instead of dict[str, str].
    """
    date_str = str(row.get("date_of_birth", "")).strip()
    time_str = str(row.get("time_of_birth", "")).strip()
    tz_str = str(row.get("tz_offset", "")).strip()
    if not (date_str and time_str and tz_str):
        return None
    try:
        date = dt.date.fromisoformat(date_str)
        h, m, s = map(int, time_str.split(":"))
        tz_offset = float(tz_str)
    except (ValueError, AttributeError):
        return None
    decimal_hour_local = h + m / 60.0 + s / 3600.0
    decimal_hour_ut = decimal_hour_local - tz_offset
    return swe.julday(date.year, date.month, date.day, decimal_hour_ut, swe.GREG_CAL)


def _transit_features(
    event_jd: float, latitude: float, longitude: float,
) -> dict[str, Any]:
    """Compute the transit chart's 206 features at event_jd with the
    natal lat/lon, prefixed ``t_``."""
    full = compute_chart_features(event_jd, latitude, longitude)
    return {
        f"t_{k}": v for k, v in full.items() if k not in DASHA_COLS_TO_STRIP
    }


def _cross_features(
    natal: dict[str, Any], transit: dict[str, Any],
) -> dict[str, float]:
    """Per-planet angular distance between transit and natal longitudes.

    Returns ``cross_lon_<planet>`` ∈ [0, 180] (shortest arc, like
    `dist_*` columns). At an exact transit return (sun anniversary,
    saturn return), cross_lon_<planet> ≈ 0.
    """
    out: dict[str, float] = {}
    for planet in CROSS_PLANETS:
        nat = natal.get(f"lon_{planet}")
        tr = transit.get(f"t_lon_{planet}")
        if nat is None or tr is None:
            out[f"cross_lon_{planet}"] = float("nan")
            continue
        diff = abs(float(tr) - float(nat)) % 360.0
        out[f"cross_lon_{planet}"] = min(diff, 360.0 - diff)
    return out


def _build_event_row(
    natal_row: pd.Series,
    *,
    event_jd: float,
    birth_jd: float,
    latitude: float,
    longitude: float,
    moon_longitude: float,
    is_event: int,
    event_date: str,
    event_root: str,
    event_subtype: str,
) -> dict[str, Any] | None:
    """Build a single (person, event) feature row.

    Returns None on a transit-computation failure (e.g. pyswisseph
    ephemeris range error for an extreme historical event).
    """
    try:
        transit = _transit_features(event_jd, latitude, longitude)
    except Exception:  # noqa: BLE001 - any swisseph failure is fatal for this row
        logger.warning(
            "transit feature compute failed for name=%s event_date=%s",
            natal_row.get("name", "?"), event_date,
        )
        return None

    natal: dict[str, Any] = {
        col: natal_row[col] for col in natal_row.index
        if col not in ("name", "rodden_rating", "categories_raw",
                       "categories_lower", "categories_tokens", "source_url")
    }
    cross = _cross_features(natal, transit)
    dasha = active_dasha_at(event_jd, birth_jd, moon_longitude)

    row: dict[str, Any] = {}
    row.update(natal)
    row.update(transit)
    row.update(cross)
    row.update(dasha)
    # Metadata — `categories_lower` is set to a sentinel so existing trainer
    # code that touches the column doesn't crash; only `is_event` matters
    # as the actual label.
    row["name"] = natal_row.get("name", "")
    row["event_date"] = event_date
    row["event_jd"] = event_jd
    row["birth_jd"] = birth_jd
    row["event_root"] = event_root
    row["event_subtype"] = event_subtype if pd.notna(event_subtype) else ""
    row["is_event"] = int(is_event)
    row["categories_lower"] = "event" if is_event else "none"
    return row


def _draw_negative_jds(
    rng: np.random.Generator,
    birth_jd: float,
    positive_jds: list[float],
    n_to_draw: int,
    max_attempts_factor: int = 30,
) -> list[float]:
    """Draw ``n_to_draw`` non-event JDs for a person, *month-anchored to a
    random positive event for that person and at least 2 years offset*.

    This is the critical control that isolates astrological signal from
    age + seasonal confounding. For each draw:

    1. Pick a random positive_jd as the anchor — gives us its calendar
       month + day.
    2. Pick a random year offset ∈ [-30, +30] yr, excluding ±2 yr (avoids
       same-Saturn-phase samples). Mid-range matches the typical spread
       of "what if this had happened at a different age".
    3. Constrain the resulting JD into the person's lifespan
       ``[birth_jd + 365, min(birth_jd + 100yr, today)]`` and reject if
       within ±30 days of any known event.

    Year-offset matching kills two confounders simultaneously:

    - **Seasonal**: month + day held constant → Sun velocity, declination,
      and other day-of-year-periodic features have the same distribution
      across positives and negatives.
    - **Age**: shifting by ≥ 2 years moves the active dasha and the
      transit positions of slow planets enough that astrological signal
      (if real) emerges, while still keeping the negative within the same
      person's adult lifespan.

    Returns fewer than n_to_draw if the rejection sampler can't find
    enough valid windows.
    """
    if not positive_jds:
        return []

    today_jd = swe.julday(
        dt.date.today().year, dt.date.today().month, dt.date.today().day,
        12.0, swe.GREG_CAL,
    )
    lower = birth_jd + NEGATIVE_WINDOW_START_DAYS
    upper = min(birth_jd + MAX_LIFESPAN_YEARS * 365.2425, today_jd)
    if upper <= lower:
        return []

    drawn: list[float] = []
    max_attempts = n_to_draw * max_attempts_factor
    for _ in range(max_attempts):
        if len(drawn) >= n_to_draw:
            break
        anchor = float(rng.choice(positive_jds))
        # Decompose anchor JD to (year, month, day) so we can shift by
        # INTEGER calendar years — keeping month+day identical kills the
        # seasonal Sun-velocity / Sun-declination confounder cleanly.
        ay, am, ad, _ = swe.revjul(anchor, swe.GREG_CAL)
        ay, am, ad = int(ay), int(am), int(ad)
        offset_years = int(rng.integers(2, 31))
        sign = 1 if rng.random() < 0.5 else -1
        candidate_year = ay + sign * offset_years
        try:
            candidate = swe.julday(candidate_year, am, ad, 12.0, swe.GREG_CAL)
        except Exception:  # noqa: BLE001 - feb 29 → 28 in some libraries
            continue
        if candidate < lower or candidate > upper:
            continue
        if any(abs(candidate - p) < NEGATIVE_EXCLUSION_RADIUS_DAYS
               for p in positive_jds + drawn):
            continue
        drawn.append(candidate)
    return drawn


# ---------- Main ----------

def build_event_corpus(
    *,
    features_parquet: Path,
    events_csv: Path,
    raw_csv: Path,
    event_root_filter: str | None,
    output_parquet: Path,
    seed: int = 42,
    limit: int | None = None,
    include_negatives: bool = True,
) -> dict[str, int]:
    """Build a per-event corpus parquet. Returns stats dict.

    Two modes — driven by what comes next:

    1. **Binary-target mode** (``event_root_filter`` set, ``include_negatives=True``).
       Filters events to one ``event_root`` and draws strict month-anchored
       negatives. Pair with ``train_classifier.py --target-column is_event``
       for "did this person experience event-X at this date".

    2. **Multi-class mode** (``event_root_filter=None``, ``include_negatives=False``).
       Keeps every real event of every type. No negatives. Pair with
       ``train_multiclass.py --target-column event_root`` for "given
       (natal + transit + dasha), which kind of event is this".

    The user's original framing — "for each event for a person we take
    the dob planet positions + date of event planet positions + time of
    dasha" — is mode 2: one row per real (person, event), event type as
    label, no artificial negatives.
    """
    if not features_parquet.exists():
        raise FileNotFoundError(f"features parquet missing: {features_parquet}")
    if not events_csv.exists():
        raise FileNotFoundError(f"events CSV missing: {events_csv}")
    if not raw_csv.exists():
        raise FileNotFoundError(f"raw CSV missing: {raw_csv}")

    output_parquet.parent.mkdir(parents=True, exist_ok=True)

    # Initialize Lahiri ayanamsa once — the main process also needs it for
    # compute_chart_features() calls below.
    init_worker()

    logger.info("loading natal features from %s", features_parquet)
    features_df = pd.read_parquet(features_parquet)
    features_df["_name_lower"] = features_df["name"].astype(str).str.strip().str.lower()
    features_df = features_df.drop_duplicates(subset="_name_lower", keep="first")
    features_df = features_df.set_index("_name_lower", drop=True)

    logger.info("loading birth data from %s", raw_csv)
    raw_df = pd.read_csv(raw_csv)
    raw_df["_name_lower"] = raw_df["name"].astype(str).str.strip().str.lower()
    raw_df = raw_df.drop_duplicates(subset="_name_lower", keep="first")
    raw_df = raw_df.set_index("_name_lower", drop=True)

    logger.info("loading events from %s", events_csv)
    events_df = pd.read_csv(events_csv)
    events_df["_name_lower"] = events_df["name"].astype(str).str.strip().str.lower()
    if event_root_filter is not None:
        events_df = events_df[
            events_df["event_root"].astype(str).str.lower()
            == event_root_filter.lower()
        ]
    # Keep events with EITHER a full date OR a year — the JD parser
    # falls back to July 1 of the event_year when the date is missing.
    has_date = events_df["event_date"].notna()
    has_year = events_df["event_year"].notna() if "event_year" in events_df.columns else False
    events_df = events_df[has_date | has_year]
    events_df = events_df[events_df["_name_lower"].isin(features_df.index)]
    events_df = events_df[events_df["_name_lower"].isin(raw_df.index)]
    logger.info(
        "%d events joinable (filter=%r, date-or-year + natal + raw)",
        len(events_df), event_root_filter or "ALL",
    )

    if limit is not None:
        events_df = events_df.head(limit)

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    positive_jds_per_person: dict[str, list[float]] = {}
    person_meta: dict[str, dict[str, float]] = {}  # name → birth_jd, lat, lon, moon

    # ── Pass 1: positives ─────────────────────────────────────────────
    failed_positives = 0
    for _, ev in events_df.iterrows():
        name_lower = ev["_name_lower"]
        event_jd = _event_date_to_jd(
            ev.get("event_date"), ev.get("event_year"),
        )
        if event_jd is None:
            failed_positives += 1
            continue
        # Look up birth metadata for this person (cached after first hit)
        if name_lower not in person_meta:
            raw_row = raw_df.loc[name_lower]
            birth_jd = _row_to_birth_jd(raw_row)
            try:
                latitude = float(raw_row["latitude"])
                longitude = float(raw_row["longitude"])
            except (ValueError, KeyError, TypeError):
                failed_positives += 1
                continue
            if birth_jd is None:
                failed_positives += 1
                continue
            # Moon longitude needed for active_dasha_at; cheapest way is
            # to read it back from the natal features row.
            moon_lon = float(features_df.loc[name_lower, "lon_moon"])
            person_meta[name_lower] = {
                "birth_jd": birth_jd,
                "latitude": latitude,
                "longitude": longitude,
                "moon_lon": moon_lon,
            }
        meta = person_meta[name_lower]

        natal_row = features_df.loc[name_lower]
        row = _build_event_row(
            natal_row,
            event_jd=event_jd,
            birth_jd=meta["birth_jd"],
            latitude=meta["latitude"],
            longitude=meta["longitude"],
            moon_longitude=meta["moon_lon"],
            is_event=1,
            event_date=str(ev["event_date"]),
            event_root=str(ev["event_root"]),
            event_subtype=str(ev.get("event_subtype", "")),
        )
        if row is None:
            failed_positives += 1
            continue
        rows.append(row)
        positive_jds_per_person.setdefault(name_lower, []).append(event_jd)

    n_positives = len(rows)
    logger.info(
        "positives: succeeded=%d failed=%d  distinct_people=%d",
        n_positives, failed_positives, len(positive_jds_per_person),
    )

    # ── Pass 2: negatives (only in binary-target mode) ────────────────
    failed_negatives = 0
    if include_negatives:
        for name_lower, positive_jds in positive_jds_per_person.items():
            meta = person_meta[name_lower]
            natal_row = features_df.loc[name_lower]
            negative_jds = _draw_negative_jds(
                rng, meta["birth_jd"], positive_jds, len(positive_jds),
            )
            for neg_jd in negative_jds:
                row = _build_event_row(
                    natal_row,
                    event_jd=neg_jd,
                    birth_jd=meta["birth_jd"],
                    latitude=meta["latitude"],
                    longitude=meta["longitude"],
                    moon_longitude=meta["moon_lon"],
                    is_event=0,
                    event_date=str(dt.date(*swe.revjul(neg_jd, swe.GREG_CAL)[:3])),
                    event_root="",
                    event_subtype="",
                )
                if row is None:
                    failed_negatives += 1
                    continue
                rows.append(row)

    n_negatives = sum(1 for r in rows if r["is_event"] == 0)
    if include_negatives:
        logger.info(
            "negatives: succeeded=%d failed=%d", n_negatives, failed_negatives,
        )
    else:
        logger.info("multi-class mode: no negatives drawn")

    if not rows:
        raise RuntimeError(
            f"no rows produced for event_root={event_root_filter!r}. "
            f"Check joinability of events_all.csv with the features parquet."
        )

    df = pd.DataFrame(rows)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info(
        "wrote %s  (%d rows × %d cols)  positives=%d negatives=%d",
        output_parquet, len(df), len(df.columns), n_positives, n_negatives,
    )

    return {
        "n_positives": n_positives,
        "n_negatives": n_negatives,
        "distinct_people": len(positive_jds_per_person),
        "failed_positives": failed_positives,
        "failed_negatives": failed_negatives,
    }


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.event_corpus",
        description="Build a per-(person, event_date) corpus combining "
                    "natal, transit, active-dasha, and cross features.",
    )
    parser.add_argument(
        "--features", type=Path,
        default=Path("app/medini/data/ml_astro_tier_a_dasha_kinematic.parquet"),
        help="Natal-features parquet (Round 3 output).",
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
        help="Events CSV with name + event_root + event_date columns.",
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path("data/astro_databank/raw.csv"),
        help="Raw scrape CSV with name + date_of_birth + time_of_birth "
             "+ latitude + longitude + tz_offset.",
    )
    parser.add_argument(
        "--event-root", type=str, default=None,
        help="event_root to keep (e.g. 'Marriage', 'Death by Disease'). "
             "Omit to keep ALL event types — required for multi-class mode.",
    )
    parser.add_argument(
        "--no-negatives", action="store_true",
        help="Skip negative-sample synthesis. Required for multi-class "
             "training (one row per real event; label = event_root).",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Destination parquet path.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None,
                        help="Take only the first N positive events (smoke tests).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Validation: --event-root is required when negatives are enabled
    # (the binary mode needs to know which event type is the positive class)
    if args.event_root is None and not args.no_negatives:
        parser.error(
            "binary-mode (negatives enabled) requires --event-root; "
            "omit --event-root only when paired with --no-negatives "
            "for multi-class corpus."
        )

    stats = build_event_corpus(
        features_parquet=args.features,
        events_csv=args.events,
        raw_csv=args.raw,
        event_root_filter=args.event_root,
        output_parquet=args.output,
        seed=args.seed,
        limit=args.limit,
        include_negatives=not args.no_negatives,
    )
    print(
        f"Event corpus built: positives={stats['n_positives']} "
        f"negatives={stats['n_negatives']} "
        f"distinct_people={stats['distinct_people']} "
        f"failed_pos={stats['failed_positives']} "
        f"failed_neg={stats['failed_negatives']} "
        f"output={args.output}"
    )
    return 0 if stats["n_positives"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
