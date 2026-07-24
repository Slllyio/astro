"""Stage 0a — profile the AstroDatabank corpus BEFORE any extraction (the decision gate).

Measures the unknowns the plan gates on:
  * Rodden-rating distribution within raw_holos_full.csv (the master taxonomy corpus), overall AND
    cross-tabbed against each Tier-1 label cohort (childless / prolific / long-life / short-life /
    prison) x time-precision — the gate is >=60% of each cohort surviving quality tier B
    ({AA,A} + minute/quarter time); if a cohort fails, the relaxed gate must be consciously
    documented in METHODOLOGY.md BEFORE Stage 2.
  * Time-precision tiers per source; tz/lat/lon sanity; event-join yield.

REPORT-ONLY. Writes data/astro_databank/derived/raman/corpus_profile.json + prints the report.
Usage: py -3.12 -m tools.raman_saab.astrobank.profile_corpus
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools.raman_saab.astrobank._names import normalize_name, quality_tier, time_precision

_DIR = Path("data/astro_databank")
_OUT = _DIR / "derived" / "raman" / "corpus_profile.json"

#: Tier-1 (+key Tier-2) cohort detectors: lowercase substring on the hierarchical categories field.
COHORTS = {
    "H5_CHILDLESS": "kids none",
    "H5_PROLIFIC": "kids more than 3",
    "H8_LONGLIFE": "long life",
    "H8_SHORTLIFE": "short life",
    "H12_PRISON": "prison sentence",
    "H7_DIVORCED": "number of divorces",
    "H7_LONGMARRIAGE": "marriage more than 15",
    "H7_WIDOWED": "widowed",
    "H2_BANKRUPT": "bankruptcy",
    "H2_WEALTHY": "wealthy",
}

csv.field_size_limit(10_000_000)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    holos = _read(_DIR / "raw_holos_full.csv")
    print(f"[profile] raw_holos_full rows: {len(holos)}")

    # ── overall rating x precision ───────────────────────────────────────────
    ratings = Counter((r.get("rodden_rating") or "?").strip().upper() for r in holos)
    precisions = Counter(time_precision(r.get("time_of_birth", "")) for r in holos)
    tiers = Counter(quality_tier(r.get("rodden_rating", ""), time_precision(r.get("time_of_birth", "")))
                    for r in holos)
    print(f"[profile] ratings: {dict(ratings.most_common(8))}")
    print(f"[profile] time precision: {dict(precisions)}")
    print(f"[profile] best quality tier: {dict(tiers)}   (None = excluded outright)")

    # ── per-cohort cross-tab + tier survival (THE GATE) ──────────────────────
    cohort_stats: dict[str, dict] = {}
    print(f"\n{'cohort':16} {'n':>6} {'tierA':>6} {'tierB':>6} {'tierC':>6} {'excl':>6}  B-survival")
    for key, pat in COHORTS.items():
        rows = [r for r in holos if pat in (r.get("categories") or "").lower()]
        tc = Counter(quality_tier(r.get("rodden_rating", ""),
                                  time_precision(r.get("time_of_birth", ""))) for r in rows)
        n = len(rows)
        n_a, n_b, n_c = tc.get("A", 0), tc.get("B", 0), tc.get("C", 0)
        surv_b = (n_a + n_b) / n if n else 0.0
        cohort_stats[key] = {"n": n, "tier_A": n_a, "tier_B": n_b, "tier_C": n_c,
                             "excluded": tc.get(None, 0), "tierB_survival": round(surv_b, 4)}
        flag = "OK" if surv_b >= 0.6 else "<-- BELOW 60% GATE"
        print(f"{key:16} {n:>6} {n_a:>6} {n_b:>6} {n_c:>6} {tc.get(None,0):>6}  {surv_b:.1%} {flag}")

    # ── tz / coordinate sanity ───────────────────────────────────────────────
    bad_tz = bad_coord = lmt_frac = 0
    for r in holos:
        try:
            tz = float(r.get("tz_offset") or "nan")
            if not (-12.0 <= tz <= 14.0):
                bad_tz += 1
            elif abs(tz * 60) % 5 > 1e-6:
                lmt_frac += 1
        except ValueError:
            bad_tz += 1
        try:
            la, lo = float(r.get("latitude") or "nan"), float(r.get("longitude") or "nan")
            if not (-90 <= la <= 90 and -180 <= lo <= 180):
                bad_coord += 1
        except ValueError:
            bad_coord += 1
    print(f"\n[profile] tz out-of-range/bad: {bad_tz}   LMT-fractional tz: {lmt_frac}   bad coords: {bad_coord}")

    # ── event-join yield (holos names ∩ events names, normalized) ────────────
    holos_names = {normalize_name(r["name"]) for r in holos}
    ev_names = Counter()
    with (_DIR / "events_all.csv").open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            ev_names[normalize_name(r["name"])] += 1
    joined = holos_names & set(ev_names)
    # names that are corpus-unique in holos (safe for event joins)
    holos_name_counts = Counter(normalize_name(r["name"]) for r in holos)
    unique_joined = {n for n in joined if holos_name_counts[n] == 1}
    print(f"[profile] holos∩events people: {len(joined)}   corpus-unique (safe joins): {len(unique_joined)}")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps({
        "holos_rows": len(holos), "ratings": dict(ratings), "precisions": dict(precisions),
        "tiers": {str(k): v for k, v in tiers.items()},
        "cohorts": cohort_stats,
        "tz_bad": bad_tz, "tz_lmt_fractional": lmt_frac, "coords_bad": bad_coord,
        "event_join_people": len(joined), "event_join_unique": len(unique_joined),
    }, indent=2), encoding="utf-8")
    print(f"\n[profile] wrote {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
