"""Timed-birth VOCATION corpus from the ASTROCRM mirror — the Track-B
non-death outcome axis.

Joins two ASTROCRM CSVs (fetched by ``fetch_astrocrm.py`` into ``data/holos/``):

* ``holos_clean.csv``            — Rodden-rated **timed** births with birth
  date/time, UTC offset, coordinates, gender (the castable chart).
* ``astro_analytics_quality.csv``— the Astro-Databank **category** taxonomy
  per person (``vocation : GROUP : detail``, ``notable : famous : top 5% …``).

The two are joined on a normalised name key ("Last, First" → "first last",
punctuation stripped). Output: one row per person with a castable timed birth
AND boolean vocation/eminence labels, written to
``data/holos/vocation_corpus.parquet``.

The vocation GROUP flags are the *pre-registered* classes the karaka battery
tests (see docs/raman_saab/VOCATION_PREREG.md). We deliberately roll the noisy
level-3 detail up to the AstroDatabank level-2 group and keep only Rodden
AA/A/B (accurate birth time → real lagna/houses).

CLI:
    python -m app.medini.etl.astrocrm_vocation_corpus \
        --holos data/holos --out data/holos/vocation_corpus.parquet
"""
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Pre-registered vocation GROUPS (AstroDatabank level-2) → boolean columns.
# Chosen because each has a large N and an unambiguous classical significator.
_VOCATION_GROUPS: dict[str, tuple[str, ...]] = {
    # column            AstroDatabank level-2 group substrings (lower-case)
    "voc_sports":       ("sports",),               # excludes "sports business"
    "voc_military":     ("military",),
    "voc_writers":      ("writers",),
    "voc_entertainment":("entertainment", "entertain/music", "entertain/business"),
    "voc_art":          ("art",),                  # "fine art"
    "voc_politics":     ("politics",),
    "voc_education":    ("education",),
    "voc_law":          ("law",),
    "voc_religion":     ("religion",),
    "voc_science":      ("science",),
    "voc_business":     ("business",),
    "voc_medical":      ("medical",),
}

_EMINENCE_TOKEN = "notable : famous : top 5%"


def _norm_name(n: object) -> str:
    s = str(n).strip().lower()
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        if len(parts) == 2:
            s = f"{parts[1]} {parts[0]}"
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", s)).strip()


def _tokens(cat: object) -> list[str]:
    if not isinstance(cat, str):
        return []
    return [t.strip().lower() for t in cat.replace("|", ";").split(";") if t.strip()]


def _group_of(token: str) -> str | None:
    """Return the level-2 vocation group of a 'vocation : GROUP : detail' token."""
    if not token.startswith("vocation"):
        return None
    parts = [p.strip() for p in token.split(":")]
    return parts[1] if len(parts) >= 2 else None


def build(holos_dir: Path, out_path: Path) -> pd.DataFrame:
    holos = pd.read_csv(holos_dir / "holos_clean.csv")
    analytics = pd.read_csv(holos_dir / "astro_analytics_quality.csv", low_memory=False)

    holos["k"] = holos["name"].map(_norm_name)
    analytics["k"] = analytics["name"].map(_norm_name)

    # one category string per person (first non-null on the join key)
    cats = (
        analytics.dropna(subset=["categories"])
        .drop_duplicates("k")
        .set_index("k")["categories"]
    )

    rows: list[dict] = []
    seen: set[str] = set()
    for _, r in holos.iterrows():
        k = r["k"]
        if not k or k in seen:
            continue
        rodden = str(r.get("rodden_rating") or "").strip().upper()
        if rodden not in ("AA", "A", "B"):
            continue
        cat = cats.get(k)
        toks = _tokens(cat)
        if not toks:
            continue
        try:
            lat = float(r["latitude"]); lon = float(r["longitude"])
            tz = float(r["utc_dst_corrected"] if pd.notna(r.get("utc_dst_corrected"))
                       else r["utc_offset"])
            y = int(r["birth_year"]); mo = int(r["birth_month"]); d = int(r["birth_day"])
            hh = int(r["birth_hour"]); mi = int(r["birth_min"])
        except (TypeError, ValueError):
            continue
        if not (1 <= mo <= 12 and 1 <= d <= 31 and 0 <= hh <= 23 and 0 <= mi <= 59):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and abs(tz) <= 14):
            continue

        groups = {g for g in (_group_of(t) for t in toks) if g}
        row = {
            "name": r["name"], "k": k,
            "birth_year": y, "birth_month": mo, "birth_day": d,
            "birth_hour": hh, "birth_min": mi,
            "tz_offset": tz, "lat": lat, "lon": lon,
            "rodden": rodden, "gender": str(r.get("gender") or "").strip(),
            "is_julian": int(r.get("is_julian") or 0),
            "eminent": int(any(_EMINENCE_TOKEN in t for t in toks)),
        }
        for col, needles in _VOCATION_GROUPS.items():
            # a group matches only if the token's level-2 group is exactly one of
            # the needles (so "sports" excludes "sports business", etc.)
            row[col] = int(any(g in needles for g in groups))
        rows.append(row)
        seen.add(k)

    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info("vocation corpus -> %s (%d persons)", out_path, len(df))
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--holos", type=Path, default=Path("data/holos"))
    p.add_argument("--out", type=Path, default=Path("data/holos/vocation_corpus.parquet"))
    args = p.parse_args()
    df = build(args.holos, args.out)
    print(f"persons: {len(df)}")
    print("eminent:", int(df["eminent"].sum()))
    for col in _VOCATION_GROUPS:
        print(f"  {col:20s} {int(df[col].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
