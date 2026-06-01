"""Build the event-transits table — captures the transit STATE of each
planet at every documented event, with classical natal house lordship.

For each dated event in ``events_with_dasha.parquet``, computes for all
9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu):

  - **Transit sign** at the event moment (sidereal Lahiri)
  - **Transit natal house**: which house in the PERSON'S natal chart
    that transit sign represents (whole-sign from Lagna)
  - **Natal houses ruled** by this planet, given the person's lagna
    (e.g., for someone with Virgo lagna, Saturn rules signs Capricorn
    and Aquarius which are houses 5 and 6)
  - **Speed class** (slow_mover / fast_mover) for classical "powerful
    transit" filtering
  - **Retrograde** flag at the event moment

This encodes the doctrine claim from BPHS Ch.31 + Phaladeepika Ch.26:

  > Event timing is triggered by the transit of slow planets through
  > houses that those planets are natal lords of.

Example query that becomes possible:
  > "Find all marriage events that happened while Venus, the natal lord
  > of the 7th house, was transiting the natal 7th house."

```sql
SELECT * FROM event_transits t
JOIN events e USING (event_id)
WHERE e.event_class = 'marriage'
  AND t.transit_planet = 'Venus'
  AND t.transit_natal_house = 7
  AND list_contains(t.natal_houses_ruled, 7);
```

## Output schema (event_transits.parquet)

  event_id              INT     -- FK → events_with_dasha
  person_id             TEXT    -- FK → persons
  event_jd              FLOAT64 -- duplicated from events_with_dasha for convenience
  transit_planet        TEXT    -- one of 9 grahas
  transit_lon           FLOAT64 -- sidereal longitude at event_jd
  transit_sign          INT     -- 1..12
  transit_natal_house   INT     -- 1..12 (from person's Lagna)
  natal_houses_ruled    TEXT    -- comma-separated, e.g. "5,6"; empty for Rahu/Ketu
  is_slow_mover         BOOL    -- True for Saturn, Jupiter, Rahu, Ketu, Mars
  is_retrograde         BOOL
  has_natal_house_lordship  BOOL  -- False for Rahu/Ketu only

## Powerful-transit filter

Downstream Gold view ``v_event_transits_powerful`` restricts to:
  - Slow movers only (Saturn, Jupiter, Rahu, Ketu, Mars)
  - Transit landing in a house the planet is natal lord of, OR
  - Transit landing in the natal 1st/5th/9th (trikona) or 10th (success)

Usage:
    python -m app.medini.etl.build_event_transits
    python -m app.medini.etl.build_event_transits --workers 6
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Final, Any

import pandas as pd
import swisseph as swe

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
OUTPUT_FILE: Final = "event_transits.parquet"

# Canonical sign rulership per BPHS Ch.3 (1-indexed for clarity).
_SIGN_RULERS: Final[dict[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Planets (Title-case) → swisseph IDs. Rahu uses TRUE_NODE; Ketu derived.
_PLANETS: Final[dict[str, int]] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

# Slow movers per classical doctrine: their transits carry weight because
# they last long enough to dwell in a single house for months/years.
_SLOW_MOVERS: Final[frozenset[str]] = frozenset({
    "Saturn", "Jupiter", "Rahu", "Ketu", "Mars",
})

# Rahu/Ketu are nodes — they don't have sign rulership in classical Vedic.
_HAS_LORDSHIP: Final[frozenset[str]] = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
})


def _planet_lon_sidereal(jd: float, planet_id: int) -> tuple[float, bool]:
    """Sidereal longitude + retrograde flag for one planet at JD."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    res, _ = swe.calc_ut(jd, planet_id, flags)
    return float(res[0]), bool(res[3] < 0)


def _houses_ruled_by_planet(
    planet: str, lagna_sign: int,
) -> tuple[int, ...]:
    """Return the natal houses this planet rules, given the person's Lagna.

    For each sign in the zodiac, derive its natal-house position from
    Lagna via whole-sign counting; collect those where this planet is
    the sign-ruler.
    """
    if planet not in _HAS_LORDSHIP:
        return ()
    houses = []
    for sign in range(1, 13):
        if _SIGN_RULERS[sign] == planet:
            # House number for this sign = (sign - lagna_sign) mod 12 + 1
            house = ((sign - lagna_sign) % 12) + 1
            houses.append(house)
    return tuple(sorted(houses))


def _compute_event_transits_one(
    event_id: int, person_id: str, event_jd: float, lagna_sign: int,
) -> list[dict[str, Any]]:
    """For one event, compute the transit row for each of 9 planets."""
    rows: list[dict[str, Any]] = []

    # Rahu position via swisseph TRUE_NODE; Ketu = Rahu + 180.
    rahu_lon, rahu_rx = _planet_lon_sidereal(event_jd, swe.TRUE_NODE)

    for planet, swe_id in _PLANETS.items():
        lon, retrograde = _planet_lon_sidereal(event_jd, swe_id)
        rows.append(_make_row(
            event_id, person_id, event_jd, planet, lon, retrograde, lagna_sign,
        ))

    # Rahu uses precomputed value.
    rows.append(_make_row(
        event_id, person_id, event_jd, "Rahu", rahu_lon, rahu_rx, lagna_sign,
    ))
    # Ketu is 180° opposite Rahu.
    ketu_lon = (rahu_lon + 180.0) % 360.0
    rows.append(_make_row(
        event_id, person_id, event_jd, "Ketu", ketu_lon, rahu_rx, lagna_sign,
    ))

    return rows


def _make_row(
    event_id: int, person_id: str, event_jd: float,
    planet: str, lon: float, retrograde: bool, lagna_sign: int,
) -> dict[str, Any]:
    """Compose one transit-state row for a planet at an event moment."""
    transit_sign = int(lon // 30) + 1  # 1..12
    transit_natal_house = ((transit_sign - lagna_sign) % 12) + 1  # 1..12
    houses_ruled = _houses_ruled_by_planet(planet, lagna_sign)
    return {
        "event_id": event_id,
        "person_id": person_id,
        "event_jd": event_jd,
        "transit_planet": planet,
        "transit_lon": lon,
        "transit_sign": transit_sign,
        "transit_natal_house": transit_natal_house,
        "natal_houses_ruled": (
            ",".join(str(h) for h in houses_ruled) if houses_ruled else ""
        ),
        "is_slow_mover": planet in _SLOW_MOVERS,
        "is_retrograde": retrograde,
        "has_natal_house_lordship": planet in _HAS_LORDSHIP,
    }


def _worker(args: tuple[int, str, float, int]) -> list[dict[str, Any]] | None:
    """Multiprocessing worker. Returns None on swisseph errors."""
    event_id, person_id, event_jd, lagna_sign = args
    try:
        return _compute_event_transits_one(
            event_id, person_id, event_jd, lagna_sign,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Transit calc failed for event %d: %s", event_id, exc)
        return None


def build_event_transits(
    events_with_dasha: pd.DataFrame,
    charts: pd.DataFrame,
    workers: int = 1,
) -> pd.DataFrame:
    """For each event with a valid event_jd, compute its 9-planet transit state."""
    # Need lagna_sign from charts for each person — join in.
    merged = events_with_dasha.merge(
        charts[["person_id", "asc_sign"]], on="person_id", how="left",
    )
    valid = merged[merged["event_jd"].notna() & merged["asc_sign"].notna()].copy()

    inputs = list(zip(
        valid["event_id"].astype(int).tolist(),
        valid["person_id"].tolist(),
        valid["event_jd"].astype(float).tolist(),
        valid["asc_sign"].astype(int).tolist(),
    ))
    logger.info("Computing transits for %d events x 9 planets = %d rows...",
                len(inputs), len(inputs) * 9)

    if workers > 1:
        with mp.Pool(workers) as pool:
            chunks = list(pool.imap_unordered(_worker, inputs, chunksize=64))
    else:
        chunks = [_worker(t) for t in inputs]

    flat = [row for chunk in chunks if chunk is not None for row in chunk]
    logger.info("Built %d transit rows (%d events × 9 planets, expected %d)",
                len(flat), len(inputs), len(inputs) * 9)
    return pd.DataFrame(flat)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N events (smoke test).")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    events = pd.read_parquet(
        args.data_dir / "events_with_dasha.parquet",
        columns=["event_id", "person_id", "event_jd"],
    )
    charts = pd.read_parquet(
        args.data_dir / "charts.parquet",
        columns=["person_id", "asc_sign"],
    )
    if args.limit is not None:
        events = events.head(args.limit)
    logger.info("Loaded %d events / %d charts", len(events), len(charts))

    transits = build_event_transits(events, charts, workers=args.workers)
    out_path = args.data_dir / OUTPUT_FILE
    transits.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows to %s", len(transits), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
