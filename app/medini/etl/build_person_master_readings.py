"""Bulk-materialise MASTER 13-layer readings for every dossier person.

Sibling of ``build_person_readings.py`` — that script materialises the
9-phase base reading. THIS script runs the **full master toolkit**
(Phases 1-9 + Gaps A-M) via :func:`compose_master_reading` and writes a
wider ``master_readings.parquet`` enriched with:

  * Ashtakavarga SAV per bhava (12 cols)
  * Arudha Lagna, Upapada Lagna, Dara Pada signs (3 cols)
  * Karakamsa sign + soul reading (when Atmakaraka derivable)
  * Per-planet Vimsopaka composite rupas (7 cols — visible grahas only)
  * Per-planet composite Avastha multiplier (7 cols — visible grahas only;
    Rahu/Ketu are shadow grahas, classical Avastha doesn't apply)
  * Sensitive points: Bhrigu Bindu sign + Pranapada sign + Upagrahas blob
  * Bhāvāt Bhāvam common chains (JSON blob)
  * Prescribed remedies — count + planet list + caveat counts

We do **not** pass dasha-dependent inputs (Yogini/Ashtottari/Tara) — the
dossier row has no Moon nakshatra or transit JD. Those layers degrade to
``None`` cleanly per the composer's contract.

## Why JSON-encode some columns

`varga_confirmations` (12 × VargaConfirmation), `all_arudhas` (12 × ArudhaPada),
`vimsopaka` per scheme (9 × 7), and `triple_lagna_per_bhava` (12 × 3) are
dense nested mappings. Encoding them as JSON strings keeps the parquet
schema flat while preserving full fidelity for downstream readers (any
consumer can ``json.loads`` to get the original dict back).

## Scale

~120 ms per person × 75,149 persons ≈ 2.5 hours single-process; with
``--workers 4`` ≈ 40 minutes. Output parquet ≈ 80-120 MB.

Usage:
    python -m app.medini.etl.build_person_master_readings --limit 100
    python -m app.medini.etl.build_person_master_readings --workers 4
"""
from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final

import pandas as pd

from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.master_reading import MasterReading, compose_master_reading

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


# ─── Worker helpers (module-level — must be picklable) ──────────────


def _safe_asdict(obj: Any) -> Any:
    """Convert a frozen dataclass to a plain dict, recursively.

    Falls back to ``str(obj)`` for non-dataclass values so JSON encoding
    never blows up on numpy scalars or enums.
    """
    if obj is None:
        return None
    try:
        return asdict(obj)
    except TypeError:
        return obj


def _row_to_master_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one dossier row to one master_readings.parquet row.

    Worker function — must be picklable for multiprocessing.
    """
    try:
        chart = Chart.from_dossier_row(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chart build failed for %s: %s", row.get("person_id"), exc)
        return _empty_master_row(row)
    try:
        mr = compose_master_reading(
            chart, DKPContext(),
            birth_jd=row.get("birth_jd"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Master compose failed for %s: %s", row.get("person_id"), exc)
        return _empty_master_row(row)

    return _master_reading_to_row(chart, row, mr)


def _master_reading_to_row(
    chart: Chart, row: dict[str, Any], mr: MasterReading,
) -> dict[str, Any]:
    """Flatten MasterReading into parquet-friendly scalar/list/JSON columns."""
    base = mr.base_reading
    n_strong = sum(1 for c in base.bhava_claims.values() if c.verdict_label == "strong")
    n_afflicted = sum(1 for c in base.bhava_claims.values() if c.verdict_label == "afflicted")

    out: dict[str, Any] = {
        # Identity
        "person_id": chart.person_id,
        "corpus": row.get("corpus"),
        "name": row.get("name"),
        "asc_sign": base.asc_sign,

        # Base summary
        "asc_lagna_lord": base.asc_lagna_lord,
        "yogakaraka_planets": list(base.yogakarakas),
        "badhakesh": base.badhakesh,
        "strongest_planet": base.strongest_planet,
        "weakest_planet": base.weakest_planet,
        "n_active_yogas": len(base.active_yogas),
        "n_strong_bhavas": n_strong,
        "n_afflicted_bhavas": n_afflicted,
        "active_yoga_names": [y.name for y in base.active_yogas],

        # Arudha triplet (Jaimini)
        "arudha_lagna_sign": mr.arudha_lagna.bhava,
        "upapada_lagna_sign": mr.upapada_lagna.bhava,
        "dara_pada_sign": mr.dara_pada.bhava,

        # Karakamsa (None when no AK provided — composer returns None)
        "karakamsa_present": mr.karakamsa is not None,
        "karakamsa_sign": mr.karakamsa.karakamsa_sign if mr.karakamsa else None,
        "atmakaraka": mr.karakamsa.atmakaraka if mr.karakamsa else None,

        # Sensitive points
        "bhrigu_bindu_sign": mr.sensitive_points.bhrigu_bindu.sign,
        "bhrigu_bindu_lon": round(mr.sensitive_points.bhrigu_bindu.longitude, 3),
        "pranapada_sign": mr.sensitive_points.pranapada.sign,
        "maandi_sign": (
            mr.sensitive_points.maandi.sign if mr.sensitive_points.maandi else None
        ),

        # Per-bhava verdicts (base) — 12 × 2 lite cols
    }
    for b in range(1, 13):
        claim = base.bhava_claims[b]
        out[f"b{b}_label"] = claim.verdict_label
        out[f"b{b}_composite"] = round(claim.composite_score, 3)

    # Ashtakavarga SAV per bhava (12 cols) — unwrap BhavaSAVReport to int
    for b in range(1, 13):
        report = mr.ashtakavarga.sav_per_bhava.get(b)
        out[f"sav_b{b}"] = report.sav_points if report is not None else pd.NA
        out[f"sav_b{b}_label"] = report.strength_label if report is not None else None

    # Per-planet Vimsopaka composite rupas (9 cols)
    for planet, report in mr.vimsopaka.items():
        out[f"vimsopaka_{planet.lower()}"] = round(report.composite_rupas, 3)

    # Per-planet composite Avastha multiplier (9 cols)
    for planet, mult in mr.avastha_multipliers.items():
        out[f"avastha_mult_{planet.lower()}"] = round(mult, 3)

    # Remedies summary
    out["n_prescribed_remedies"] = len(mr.prescribed_remedies)
    out["remedy_planets"] = [rx.planet for rx in mr.prescribed_remedies]
    out["remedy_caveats"] = [rx.gemstone_caveat for rx in mr.prescribed_remedies]

    # JSON blobs for dense nested layers — preserves full fidelity
    out["upagrahas_json"] = json.dumps({
        name: {"sign": pt.sign, "longitude": round(pt.longitude, 3)}
        for name, pt in mr.sensitive_points.upagrahas.items()
    })
    out["all_arudhas_json"] = json.dumps({
        str(bhava): arudha.bhava for bhava, arudha in mr.all_arudhas.items()
    })
    out["varga_confirmations_json"] = json.dumps({
        str(bhava): vc.confirmation_label
        for bhava, vc in mr.varga_confirmations.items()
    })
    out["bhavat_chains_json"] = json.dumps([
        {"base": ch.base_bhava, "distance": ch.distance,
         "derived": ch.derived_bhava,
         "karaka": ch.natural_karaka_of_derived,
         "hint": ch.interpretation_hint}
        for ch in mr.bhavat_chains
    ])
    out["triple_lagna_json"] = json.dumps({
        str(b): {"from_lagna": m["from_lagna"],
                 "from_moon": m["from_moon"],
                 "from_sun": m["from_sun"]}
        for b, m in mr.triple_lagna_per_bhava.items()
    })
    return out


def _empty_master_row(row: dict[str, Any]) -> dict[str, Any]:
    """Stub row when chart build / master compose fails.

    Preserves identity columns; all framework columns are NA / [] / None
    so downstream consumers can filter cleanly via ``isna(asc_sign)``.
    """
    out: dict[str, Any] = {
        "person_id": row.get("person_id"),
        "corpus": row.get("corpus"),
        "name": row.get("name"),
        "asc_sign": pd.NA,
        "asc_lagna_lord": None,
        "yogakaraka_planets": [],
        "badhakesh": None,
        "strongest_planet": None,
        "weakest_planet": None,
        "n_active_yogas": 0,
        "n_strong_bhavas": 0,
        "n_afflicted_bhavas": 0,
        "active_yoga_names": [],
        "arudha_lagna_sign": pd.NA,
        "upapada_lagna_sign": pd.NA,
        "dara_pada_sign": pd.NA,
        "karakamsa_present": False,
        "karakamsa_sign": None,
        "atmakaraka": None,
        "bhrigu_bindu_sign": pd.NA,
        "bhrigu_bindu_lon": pd.NA,
        "pranapada_sign": pd.NA,
        "maandi_sign": None,
        "n_prescribed_remedies": 0,
        "remedy_planets": [],
        "remedy_caveats": [],
        "upagrahas_json": "{}",
        "all_arudhas_json": "{}",
        "varga_confirmations_json": "{}",
        "bhavat_chains_json": "[]",
        "triple_lagna_json": "{}",
    }
    for b in range(1, 13):
        out[f"b{b}_label"] = None
        out[f"b{b}_composite"] = pd.NA
        out[f"sav_b{b}"] = pd.NA
        out[f"sav_b{b}_label"] = None
    for planet in ("sun", "moon", "mars", "mercury", "jupiter",
                   "venus", "saturn"):
        out[f"vimsopaka_{planet}"] = pd.NA
        out[f"avastha_mult_{planet}"] = pd.NA
    return out


def build_master_readings(
    dossier: pd.DataFrame, workers: int = 1,
) -> pd.DataFrame:
    """Materialise master readings for every row of ``dossier``."""
    records = dossier.to_dict(orient="records")
    if workers > 1:
        with mp.Pool(workers) as pool:
            results = list(pool.imap_unordered(
                _row_to_master_dict, records, chunksize=64,
            ))
    else:
        results = [_row_to_master_dict(r) for r in records]
    built = sum(1 for r in results if r["asc_sign"] is not pd.NA)
    skipped = len(records) - built
    logger.info(
        "Built %d master readings (%d input rows, %d skipped)",
        built, len(records), skipped,
    )
    return pd.DataFrame(results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N dossier rows (smoke).")
    parser.add_argument("--workers", type=int, default=1,
                        help="Multiprocessing pool size (default 1).")
    parser.add_argument(
        "--output", type=str, default="master_readings.parquet",
        help="Output parquet filename (under data-dir).",
    )
    parser.add_argument("--force", action="store_true",
                        help="Rebuild even if output is fresh vs inputs.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    from app.medini.etl._freshness import skip_if_fresh

    dossier_path = args.data_dir / "person_dossier.parquet"
    out_path = args.data_dir / args.output
    if args.limit is None and skip_if_fresh(
        out_path, [dossier_path], force=args.force,
    ):
        return 0

    dossier = pd.read_parquet(dossier_path)
    logger.info("Loaded %d dossier rows from %s", len(dossier), dossier_path)
    if args.limit is not None:
        dossier = dossier.head(args.limit)

    start = time.time()
    result = build_master_readings(dossier, workers=args.workers)
    elapsed = time.time() - start
    rate = len(result) / elapsed if elapsed else 0
    logger.info(
        "Built %d master readings in %.1fs (%.1f rows/sec)",
        len(result), elapsed, rate,
    )

    result.to_parquet(out_path, index=False)
    logger.info(
        "Wrote %d rows x %d cols to %s",
        len(result), len(result.columns), out_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
