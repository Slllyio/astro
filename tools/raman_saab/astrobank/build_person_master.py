"""Stage 0b — build the deduplicated person master + events join (the corpus foundation).

Sources (by design): raw_holos_full.csv (master taxonomy corpus, all AA/A), raw_wayback.csv
(+~3k AstroDatabank people; snapshot-deduplicated per (name,date) keeping the richest categories),
raw_lunarastro_aa.csv (population='app_user', excluded from all cohorts/controls; its ONLY role is
the strict time-upgrade rule). raw_lapaas/raw.csv are EXCLUDED (no ratings, no usable labels —
documented in METHODOLOGY.md).

Rules (pre-registered in the plan):
  * pid = sha1(name_norm | birth_date)[:16] — same name+date = same person; different date =
    different person (namesake-safe).
  * Conflict ranking: Rodden AA>A>B>C>DD>X -> time precision minute>quarter>round_hour -> source
    holos>wayback>lunarastro. All candidates archived to person_birth_candidates.parquet.
  * Lunarastro time-upgrade: only on exact-date pid match + lat/lon within 0.5 deg + chosen record
    round_hour/missing + lunarastro minute-precision. Logged.
  * Events joined ONLY on names that are corpus-unique in the master; long/short-life category vs
    own-death-age contradictions -> quarantine (dropped from longevity cohorts).

Usage: py -3.12 -m tools.raman_saab.astrobank.build_person_master
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from tools.raman_saab.astrobank._names import (
    normalize_name, person_id, quality_tier, repair_mojibake, time_precision)

_DIR = Path("data/astro_databank")
_OUT = _DIR / "derived" / "raman"

_RATING_RANK = {"AA": 0, "A": 1, "B": 2, "C": 3, "DD": 4, "X": 5, "XX": 6}
_PRECISION_RANK = {"minute": 0, "quarter": 1, "round_hour": 2, "noon_default": 3, "missing": 4}
_SOURCE_RANK = {"holos": 0, "wayback": 1, "lunarastro": 2}

csv.field_size_limit(10_000_000)


def _rows(path: Path, source: str) -> list[dict]:
    out = []
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("name") or "").strip()
            date = (r.get("date_of_birth") or "").strip()
            if not name or not date or name.startswith("Animal") or "astro-databank" in name:
                continue
            if not (len(date) >= 4 and date[:4].isdigit() and 1700 <= int(date[:4]) <= 2015):
                continue  # birth-year sanity (drops e.g. the 'Indira Gandhi 2017' bad row)
            try:
                la, lo = float(r.get("latitude") or "nan"), float(r.get("longitude") or "nan")
                tz = float(r.get("tz_offset") or "nan")
            except ValueError:
                continue
            if not (-90 <= la <= 90 and -180 <= lo <= 180 and -12 <= tz <= 14):
                continue
            out.append({
                "name_display": repair_mojibake(name), "name_norm": normalize_name(name),
                "birth_date": date, "birth_time": (r.get("time_of_birth") or "").strip(),
                "rodden_rating": (r.get("rodden_rating") or "").strip().upper(),
                "latitude": la, "longitude": lo, "tz_offset": tz,
                "categories_raw": (r.get("categories") or "").strip(),
                "source": source, "source_url": (r.get("source_url") or "").strip(),
            })
    return out


def _dedupe_wayback(rows: list[dict]) -> list[dict]:
    """One record per (name_norm, birth_date): keep the RICHEST categories (snapshot proxy)."""
    best: dict[tuple[str, str], dict] = {}
    for r in rows:
        k = (r["name_norm"], r["birth_date"])
        if k not in best or len(r["categories_raw"]) > len(best[k]["categories_raw"]):
            best[k] = r
    return list(best.values())


def _rank(r: dict) -> tuple[int, int, int]:
    return (_RATING_RANK.get(r["rodden_rating"], 9),
            _PRECISION_RANK.get(time_precision(r["birth_time"]), 9),
            _SOURCE_RANK.get(r["source"], 9))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    holos = _rows(_DIR / "raw_holos_full.csv", "holos")
    wayback = _dedupe_wayback(_rows(_DIR / "raw_wayback.csv", "wayback"))
    lunar = _rows(_DIR / "raw_lunarastro_aa.csv", "lunarastro")
    print(f"[master] holos={len(holos)}  wayback(deduped)={len(wayback)}  lunarastro_aa={len(lunar)}")

    # ── group all candidates by pid ──────────────────────────────────────────
    cands: dict[str, list[dict]] = defaultdict(list)
    for r in holos + wayback + lunar:
        pid = person_id(r["name_norm"], r["birth_date"])
        r["person_id"] = pid
        cands[pid].append(r)

    upgrades = 0
    chosen_rows: list[dict] = []
    for pid, rs in cands.items():
        rs.sort(key=_rank)
        srcs = {r["source"] for r in rs}
        # PLAN RULE: lunarastro NEVER supplies the chosen birth record for a celebrity pid — its
        # only role is the strict time-upgrade below. (The spot-check gate caught lunarastro's
        # minute-precision but WRONG times outranking AstroDatabank records — e.g. Einstein 09:23
        # vs the canonical 11:30.) The chosen record is the best-ranked holos/wayback candidate;
        # lunarastro-only pids become population='app_user'.
        db = [r for r in rs if r["source"] != "lunarastro"]
        best = dict(db[0] if db else rs[0])
        best["population"] = "celebrity_databank" if srcs & {"holos", "wayback"} else "app_user"
        # categories: prefer the richest holos/wayback categories (lunarastro's are flattened).
        cat = max((r for r in rs if r["source"] != "lunarastro"),
                  key=lambda r: len(r["categories_raw"]), default=None)
        if cat is not None:
            best["categories_raw"] = cat["categories_raw"]
        # Lunarastro time-upgrade: DISABLED by Stage-0 spot-check evidence. The pre-registered rule
        # allowed a minute-precision lunarastro time to upgrade a round-hour holos record — but the
        # spot-check showed lunarastro times can be flatly WRONG while claiming AA and matching
        # coords (Einstein 09:23:00 vs the canonical 11:30). A wrong minute-precision time is worse
        # than an honest round-hour one, so lunarastro contributes nothing to celebrity records.
        # (Kept as a counted no-op so the manifest records how many upgrades WOULD have fired.)
        if time_precision(best["birth_time"]) in ("round_hour", "missing"):
            for r in rs:
                if (r["source"] == "lunarastro"
                        and time_precision(r["birth_time"]) == "minute"
                        and abs(r["latitude"] - best["latitude"]) <= 0.5
                        and abs(r["longitude"] - best["longitude"]) <= 0.5):
                    upgrades += 1  # counted, NOT applied
                    break
        prec = time_precision(best["birth_time"])
        best["time_precision"] = prec
        best["quality_tier"] = quality_tier(best["rodden_rating"], prec) or ""
        best["tz_lmt_flag"] = abs(best["tz_offset"] * 60) % 5 > 1e-6
        best["n_candidates"] = len(rs)
        best["conflict_flag"] = len({(r["birth_time"], round(r["latitude"], 1)) for r in rs}) > 1
        best.setdefault("time_upgraded", False)
        chosen_rows.append(best)

    master = pd.DataFrame(chosen_rows).drop(columns=["source_url"])
    master = master.rename(columns={"source": "source_chosen"})
    _OUT.mkdir(parents=True, exist_ok=True)
    master.to_parquet(_OUT / "person_master.parquet", engine="pyarrow",
                      compression="zstd", index=False)
    all_cands = pd.DataFrame([r for rs in cands.values() for r in rs])
    all_cands.to_parquet(_OUT / "person_birth_candidates.parquet", engine="pyarrow",
                         compression="zstd", index=False)
    celeb = master[master.population == "celebrity_databank"]
    print(f"[master] persons={len(master)}  celebrity={len(celeb)}  app_user={(master.population=='app_user').sum()}")
    print(f"[master] tiers: {celeb.quality_tier.value_counts().to_dict()}  time-upgrades={upgrades}")

    # ── events join (corpus-unique names only) ───────────────────────────────
    name_counts = master.name_norm.value_counts()
    unique_names = set(name_counts[name_counts == 1].index)
    pid_by_name = {r.name_norm: r.person_id for r in
                   master[master.name_norm.isin(unique_names)].itertuples()}
    ev_rows = []
    with (_DIR / "events_all.csv").open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            pid = pid_by_name.get(normalize_name(r.get("name", "")))
            if pid is None or not (r.get("event_year") or "").strip().isdigit():
                continue
            date = (r.get("event_date") or "").strip()
            full = len(date) == 10 and date[4] == "-"
            ev_rows.append({
                "person_id": pid, "event_root": (r.get("event_root") or "").strip(),
                "event_subtype": (r.get("event_subtype") or "").strip(),
                "event_year": int(r["event_year"]),
                "event_month": int(date[5:7]) if full else 0,
                "event_day": int(date[8:10]) if full else 0,
                "date_precision": "day" if full else "year",
            })
    events = pd.DataFrame(ev_rows)
    events.to_parquet(_OUT / "person_events.parquet", engine="pyarrow",
                      compression="zstd", index=False)
    print(f"[master] events joined: {len(events)} rows, {events.person_id.nunique()} people")

    # ── longevity contradiction quarantine ───────────────────────────────────
    birth_year = {r.person_id: int(r.birth_date[:4]) for r in master.itertuples()
                  if len(r.birth_date) >= 4 and r.birth_date[:4].isdigit()}
    own_death = {}
    for r in events.itertuples():
        low = f"{r.event_root} {r.event_subtype}".lower()
        if r.event_root.startswith("Death") and "death of" not in low:
            age = r.event_year - birth_year.get(r.person_id, 0)
            if 0 < age < 115:
                own_death[r.person_id] = age
    cats = {r.person_id: r.categories_raw.lower() for r in master.itertuples()}
    quarantine = []
    for pid, age in own_death.items():
        c = cats.get(pid, "")
        if ("long life" in c and age < 75) or ("short life" in c and age > 33):
            quarantine.append({"person_id": pid, "death_age": age,
                               "reason": "category-vs-event age contradiction"})
    (_OUT / "quarantine.json").write_text(json.dumps(quarantine, indent=2), encoding="utf-8")
    print(f"[master] longevity contradictions quarantined: {len(quarantine)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
