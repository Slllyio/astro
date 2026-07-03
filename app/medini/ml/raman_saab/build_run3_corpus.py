"""Build the run-3 Triple-Lock corpus: timed + Rodden-rated + death-dated persons.

Joins the two ASTROCRM files fetched by ``app.medini.etl.fetch_astrocrm``:

- ``holos_clean.csv``  — birth date + time + lat/lon + utc offset + Rodden
  (61,583 rows, all AA/A). Effective UTC offset = ``utc_dst_corrected``
  (falls back to ``utc_offset``); the ``is_julian`` calendar flag is carried
  through so natal computation can use the right Swiss Ephemeris calendar.
- ``astro_people.csv`` — {{ASTRODATABANK_evn}} wikitext events, extracted via
  the existing ``events_extractor``; filtered to **own-death** events with a
  full ISO date. "Death of Mate/Child/…" (family loss) is explicitly excluded
  — an own-death root is ``Death*`` but NOT ``Death of *`` (mirrors the
  medini taxonomy's own-death vs family_loss split).

Join key: normalized name (casefold, whitespace-collapsed). Per the
pre-registration: names duplicated within EITHER source are dropped entirely
(ambiguous joins are worse than lost N), and a person with conflicting
own-death dates is dropped. Every exclusion is counted and reported.

Output: ``data/raman_saab/death_corpus_run3.parquet`` with columns
``person_id, name, dob, tob, lat, lon, tz_offset, is_julian, rodden,
dod, age_years`` plus an ``exclusions.json`` accounting file.

Usage:
    python -m app.medini.ml.raman_saab.build_run3_corpus \
        --holos data/holos/holos_clean.csv \
        --astro-people data/holos/astro_people.csv \
        --out data/raman_saab/death_corpus_run3.parquet
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import pandas as pd

from app.medini.etl.events_extractor import extract_events

logger = logging.getLogger(__name__)

_MAX_ABS_LAT = 60.0   # P9: circumpolar sunrise risk
_MIN_AGE = 1.0
_MAX_AGE = 120.0


def _norm_name(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.casefold().str.strip()
            .str.replace(r"\s+", " ", regex=True))


def _is_own_death_root(root: pd.Series) -> pd.Series:
    """Own death = root starts with 'Death' but not 'Death of' (family loss)."""
    r = root.astype(str)
    return r.str.startswith("Death") & ~r.str.startswith("Death of")


def load_death_events(astro_people_csv: Path, work_dir: Path) -> pd.DataFrame:
    """Extract events and reduce to one own-death full-date row per person.

    Returns columns ``name_norm, dod`` and drops persons with conflicting
    death dates (counted by the caller via the ``n_conflicting`` attr).
    """
    events_csv = work_dir / "events_extracted.csv"
    extract_events(astro_people_csv, events_csv)
    ev = pd.read_csv(events_csv)
    ev = ev[_is_own_death_root(ev["event_root"])]
    ev = ev[ev["event_date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
    ev = ev.assign(name_norm=_norm_name(ev["name"]))[["name_norm", "event_date"]]
    ev = ev.drop_duplicates()  # exact (person, date) dupes are harmless
    counts = ev.groupby("name_norm")["event_date"].nunique()
    conflicting = set(counts[counts > 1].index)
    out = (ev[~ev["name_norm"].isin(conflicting)]
           .rename(columns={"event_date": "dod"})
           .reset_index(drop=True))
    out.attrs["n_conflicting_death_dates"] = len(conflicting)
    return out


def build_corpus(
    holos_csv: Path, astro_people_csv: Path, out_parquet: Path,
) -> dict:
    """Build and write the run-3 corpus; return the exclusion accounting."""
    acc: dict[str, int] = {}
    h = pd.read_csv(holos_csv, low_memory=False)
    acc["holos_rows"] = len(h)

    # Rodden AA/A only (holos is already AA/A, but assert rather than assume).
    h = h[h["rodden_rating"].isin(["AA", "A"])]
    acc["after_rodden_filter"] = len(h)

    h = h.assign(name_norm=_norm_name(h["name"]))

    # Drop names duplicated within holos (ambiguous join).
    dup_h = h["name_norm"].duplicated(keep=False)
    acc["dropped_dup_names_holos"] = int(dup_h.sum())
    h = h[~dup_h]

    deaths = load_death_events(astro_people_csv, out_parquet.parent)
    acc["death_events_persons"] = len(deaths)
    acc["dropped_conflicting_death_dates"] = deaths.attrs["n_conflicting_death_dates"]
    # (deaths already one-row-per-person after conflict drop)
    dup_d = deaths["name_norm"].duplicated(keep=False)
    acc["dropped_dup_names_deaths"] = int(dup_d.sum())
    deaths = deaths[~dup_d]

    m = h.merge(deaths, on="name_norm", how="inner")
    acc["joined"] = len(m)

    # Assemble typed columns.
    dob = pd.to_datetime(dict(year=m["birth_year"], month=m["birth_month"],
                              day=m["birth_day"]), errors="coerce")
    tob = (m["birth_hour"].astype(float)
           + m["birth_min"].astype(float) / 60.0
           + m["birth_sec"].fillna(0).astype(float) / 3600.0)
    tz = m["utc_dst_corrected"].where(m["utc_dst_corrected"].notna(),
                                      m["utc_offset"])
    tob_str = (m["birth_hour"].astype(int).map("{:02d}".format) + ":"
               + m["birth_min"].astype(int).map("{:02d}".format))
    out = pd.DataFrame({
        "person_id": "ADB:" + m["name_norm"].str.replace(r"[^a-z0-9]+", "_",
                                                         regex=True),
        "name": m["name"],
        "dob": dob.dt.strftime("%Y-%m-%d"),
        "tob": tob_str,          # "HH:MM" — the schema maraka_validate expects
        "tob_hours": tob,
        "lat": m["latitude"].astype(float),
        "lon": m["longitude"].astype(float),
        "tz_offset": tz.astype(float),
        "is_julian": m["is_julian"].fillna(0).astype(int),
        "rodden": m["rodden_rating"],
        "dod": m["dod"],
    })

    # Exclusions (each counted separately, applied in order).
    bad_dob = out["dob"].isna() | out["tz_offset"].isna() | out["tob_hours"].isna()
    acc["dropped_missing_birth_fields"] = int(bad_dob.sum())
    out = out[~bad_dob]

    polar = out["lat"].abs() > _MAX_ABS_LAT
    acc["dropped_circumpolar_lat"] = int(polar.sum())
    out = out[~polar]

    age = ((pd.to_datetime(out["dod"]) - pd.to_datetime(out["dob"])).dt.days
           / 365.2425)
    out = out.assign(age_years=age)
    bad_age = ~((age >= _MIN_AGE) & (age <= _MAX_AGE))
    acc["dropped_age_out_of_range"] = int(bad_age.sum())
    out = out[~bad_age].reset_index(drop=True)

    acc["final_n"] = len(out)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_parquet, index=False)
    (out_parquet.parent / "exclusions.json").write_text(json.dumps(acc, indent=2))
    logger.info("corpus: %d persons -> %s", len(out), out_parquet)
    return acc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--holos", type=Path, default=Path("data/holos/holos_clean.csv"))
    p.add_argument("--astro-people", type=Path,
                   default=Path("data/holos/astro_people.csv"))
    p.add_argument("--out", type=Path,
                   default=Path("data/raman_saab/death_corpus_run3.parquet"))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    acc = build_corpus(args.holos, args.astro_people, args.out)
    print(json.dumps(acc, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
