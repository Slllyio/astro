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

## Nested-layer encoding

The 5 dense nested layers (`upagrahas`, `all_arudhas`, `varga_confirmations`,
`bhavat_chains`, `triple_lagna`) are emitted as list-of-struct columns —
PyArrow infers a `LIST<STRUCT<...>>` schema automatically. DuckDB can push
predicates into struct fields natively (`WHERE varga_confirmations[2].label
= 'CONFIRMED'`), so they remain queryable without deserialization. Earlier
versions of this script emitted these as JSON-encoded strings; the
2026-05-31 storage refactor unnested them per the database-optimizer
agent's recommendation.

## Scale

~120 ms per person × 75,149 persons ≈ 2.5 hours single-process; with
``--workers 4`` ≈ 40 minutes. Output parquet ≈ 80-120 MB.

Usage:
    python -m app.medini.etl.build_person_master_readings --limit 100
    python -m app.medini.etl.build_person_master_readings --workers 4
"""
from __future__ import annotations

import argparse
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

    Reads optional master-toolkit inputs from the row (added by
    ``_enrich_dossier_with_master_inputs`` before workers dispatch):

      * ``moon_nakshatra_index`` (0..26)  — activates Yogini, Ashtottari, Tara
      * ``atmakaraka`` (planet name)      — activates Karakamsa
      * ``atmakaraka_d9_sign`` (1..12)    — activates Karakamsa
      * ``day_of_week`` (0..6)            — activates Maandi
      * ``is_day_birth`` (bool)           — activates Maandi
      * ``target_jd`` (snapshot day)      — activates dasha-snapshot layers

    Any missing input causes the corresponding layer to gracefully
    degrade to ``None`` per the composer's contract.
    """
    try:
        chart = Chart.from_dossier_row(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chart build failed for %s: %s", row.get("person_id"), exc)
        return _empty_master_row(row)
    try:
        ppvs = row.get("per_planet_varga_signs") or None
        if isinstance(ppvs, dict) and not ppvs:
            ppvs = None
        vps = row.get("varga_pillar_scores") or None
        if isinstance(vps, dict) and not vps:
            vps = None
        # birth_jd can be NaN for low-precision births (date-only, no time).
        # When it is, the dasha-snapshot layers (Yogini, Ashtottari) cannot
        # compute and must be skipped — pass target_jd=None so they bail
        # cleanly instead of crashing on float NaN in cycle math.
        birth_jd = _safe_float(row.get("birth_jd"))
        target_jd = _safe_float(row.get("target_jd")) if birth_jd is not None else None
        mr = compose_master_reading(
            chart, DKPContext(),
            birth_jd=birth_jd,
            target_jd=target_jd,
            atmakaraka=row.get("atmakaraka"),
            atmakaraka_d9_sign=_safe_int(row.get("atmakaraka_d9_sign")),
            moon_nakshatra_index=_safe_int(row.get("moon_nakshatra_index")),
            day_of_week=_safe_int(row.get("day_of_week")),
            is_day_birth=_safe_bool(row.get("is_day_birth")),
            per_planet_varga_signs=ppvs,
            varga_pillar_scores=vps,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Master compose failed for %s: %s", row.get("person_id"), exc)
        return _empty_master_row(row)

    return _master_reading_to_row(chart, row, mr)


def _safe_int(v: Any) -> int | None:
    """Coerce pandas NA / NaN / None → None; valid scalar → int."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_bool(v: Any) -> bool | None:
    """Coerce pandas NA / NaN / None → None; valid scalar → bool."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return bool(v)


def _safe_float(v: Any) -> float | None:
    """Coerce pandas NA / NaN / None → None; valid scalar → float."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


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

        # Dasha snapshots at target_jd (today by default for bulk ETL)
        "yogini_active_name": mr.yogini_active.yogini_name if mr.yogini_active else None,
        "yogini_active_lord": mr.yogini_active.presiding_planet if mr.yogini_active else None,
        "yogini_active_years_left": (
            round((mr.yogini_active.end_jd - row.get("target_jd", 0)) / 365.2425, 2)
            if mr.yogini_active else None
        ),
        "ashtottari_active_lord": mr.ashtottari_active.lord if mr.ashtottari_active else None,
        "ashtottari_applicable": bool(mr.ashtottari_applicable_flag),

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

    # Dense nested layers — emitted as native list-of-structs so PyArrow
    # infers a queryable LIST<STRUCT<...>> schema. DuckDB can push
    # predicates into these (`WHERE upagrahas[1].sign = 4`) where JSON
    # strings would be opaque blobs requiring deserialization at scan time.
    out["upagrahas"] = [
        {"name": name, "sign": pt.sign, "longitude": round(pt.longitude, 3)}
        for name, pt in mr.sensitive_points.upagrahas.items()
    ]
    out["all_arudhas"] = [
        {"bhava": int(bhava), "sign": int(arudha.bhava)}
        for bhava, arudha in mr.all_arudhas.items()
    ]
    out["varga_confirmations"] = [
        {"bhava": int(bhava), "label": vc.confirmation_label}
        for bhava, vc in mr.varga_confirmations.items()
    ]
    out["bhavat_chains"] = [
        {"base": int(ch.base_bhava), "distance": int(ch.distance),
         "derived": int(ch.derived_bhava),
         "karaka": ch.natural_karaka_of_derived,
         "hint": ch.interpretation_hint}
        for ch in mr.bhavat_chains
    ]
    out["triple_lagna"] = [
        {"bhava": int(b),
         "from_lagna": int(m["from_lagna"]),
         "from_moon": int(m["from_moon"]),
         "from_sun": int(m["from_sun"])}
        for b, m in mr.triple_lagna_per_bhava.items()
    ]
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
        "yogini_active_name": None,
        "yogini_active_lord": None,
        "yogini_active_years_left": None,
        "ashtottari_active_lord": None,
        "ashtottari_applicable": False,
        "bhrigu_bindu_sign": pd.NA,
        "bhrigu_bindu_lon": pd.NA,
        "pranapada_sign": pd.NA,
        "maandi_sign": None,
        "n_prescribed_remedies": 0,
        "remedy_planets": [],
        "remedy_caveats": [],
        # Empty list-of-struct stubs for the 5 nested layers (matches
        # the success-path schema so PyArrow infers a consistent type).
        "upagrahas": [],
        "all_arudhas": [],
        "varga_confirmations": [],
        "bhavat_chains": [],
        "triple_lagna": [],
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


# Bhava -> assigned varga for pillar confirmation. Subset of
# app.core.varga_confirmation.BHAVA_TO_VARGA — we omit D4 (not loaded)
# and skip D1/D2/D3 here because the BASE reading already covers D1
# pillars (Phase 6 bhava_judge), and D2/D3 add little discrimination
# beyond D1 in practice. Future deepening: wire D4 + D2/D3 pillars too.
_BHAVA_PILLAR_VARGA: Final[Mapping[int, str]] = {
    5: "D9",   # children — Saptamsa (D7) ideal; D9 is acceptable proxy
    6: "D30",  # disease/service — Trimsamsa
    7: "D9",   # marriage — Navamsa
    8: "D30",  # longevity — Trimsamsa
    9: "D9",   # dharma — Navamsa
    10: "D10", # career — Dasamsa
    12: "D30", # loss/moksha — Trimsamsa
}

# Natural karakas per bhava — duplicated from bhavat_bhavam._NATURAL_KARAKAS
# to avoid import cycle. Keep in lockstep.
_BHAVA_NATURAL_KARAKAS: Final[Mapping[int, tuple[str, ...]]] = {
    1:  ("Sun",),
    2:  ("Jupiter",),
    3:  ("Mars",),
    4:  ("Moon", "Mercury"),
    5:  ("Jupiter",),
    6:  ("Mars", "Saturn"),
    7:  ("Venus",),
    8:  ("Saturn",),
    9:  ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Jupiter", "Saturn"),
    11: ("Jupiter",),
    12: ("Saturn", "Ketu"),
}

_KENDRA_TRIKONA: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10})
_DUSHTANA: Final[frozenset[int]] = frozenset({6, 8, 12})


def _compute_varga_pillar_scores(
    per_planet_full: Mapping[str, Mapping[str, int]],
    varga_lagnas: Mapping[str, int],
) -> dict[int, float]:
    """Per-bhava placement-based varga pillar score (-1..+1).

    Simplified scoring — DOCTRINAL CAVEATS:

    For each bhava B with assigned varga V (from _BHAVA_PILLAR_VARGA):
      * Locate each of B's natural karakas in V.
      * Compute the karaka's house from V's Lagna.
      * +0.5 if karaka in kendra/trikona, -0.5 if in dushtana, 0 else.
      * Average across karakas → score in [-0.5, +0.5].

    Returns dict {bhava: score} keyed by 1..12; only bhavas with
    sufficient data are present. Composer's varga_confirmation reads
    this and produces CONFIRMED / PROMISE_NO_DELIVERY / HIDDEN_PROMISE
    / CONSISTENT_AFFLICTION verdicts by combining with the D1 pillar.

    Future deepening (not implemented here): add bhava-lord placement,
    benefic/malefic aspects in the varga chart, dignity-weighting.
    Current simplification scores ONLY the karaka placement; that's
    enough to differentiate CONFIRMED vs CONSISTENT_AFFLICTION but
    misses some PROMISE_NO_DELIVERY nuance.
    """
    from typing import Mapping  # noqa  # for type-narrowing in scopes
    scores: dict[int, float] = {}
    for bhava, varga_short in _BHAVA_PILLAR_VARGA.items():
        if varga_short not in varga_lagnas:
            continue
        varga_lagna = varga_lagnas[varga_short]
        karakas = _BHAVA_NATURAL_KARAKAS.get(bhava, ())
        if not karakas:
            continue
        karaka_scores: list[float] = []
        for k in karakas:
            varga_sign = per_planet_full.get(k, {}).get(varga_short)
            if varga_sign is None:
                continue
            house = ((varga_sign - varga_lagna) % 12) + 1
            if house in _KENDRA_TRIKONA:
                karaka_scores.append(0.5)
            elif house in _DUSHTANA:
                karaka_scores.append(-0.5)
            else:
                karaka_scores.append(0.0)
        if karaka_scores:
            scores[bhava] = sum(karaka_scores) / len(karaka_scores)
    return scores


def _enrich_dossier_with_master_inputs(
    dossier: pd.DataFrame, data_dir: Path, snapshot_jd: float,
) -> pd.DataFrame:
    """Add the 5 optional master-toolkit input columns to the dossier.

    These columns activate previously-null master_readings layers:

      * ``moon_nakshatra_index``  — derived from ``moon_lon`` (always populates).
      * ``atmakaraka``            — looked up from jaimini_karakas.parquet.
      * ``atmakaraka_d9_sign``    — looked up from divisional_charts.parquet (D9 + AK).
      * ``day_of_week``           — derived from ``birth_jd`` (always populates).
      * ``is_day_birth``          — heuristic from local-solar-hour (always populates).
      * ``target_jd``             — constant: snapshot_jd (for Yogini/Ashtottari).

    Pre-computing into the DataFrame keeps the worker function pure
    (no shared lookup tables across multiprocessing workers).
    """
    out = dossier.copy()

    # Always-populated derivations — NaN-safe (some dossier rows have
    # missing birth_jd / moon_lon for low-precision births).
    moon_lon_f = pd.to_numeric(out["moon_lon"], errors="coerce")
    out["moon_nakshatra_index"] = (
        (moon_lon_f // (360.0 / 27.0)).astype("Int64")
    )

    # JD -> day-of-week: int(JD + 1.5) % 7 gives 0=Sunday..6=Saturday (Vedic convention)
    birth_jd_f = pd.to_numeric(out["birth_jd"], errors="coerce")
    dow_raw = (birth_jd_f + 1.5).floordiv(1).mod(7)  # NaN-safe via pandas ops
    out["day_of_week"] = dow_raw.astype("Int64")

    # is_day_birth heuristic: local solar hour 6..18 = day. Caveat: not
    # equation-of-time corrected; near poles this gets wrong. Acceptable
    # for the bulk corpus (mostly mid-latitude births).
    birth_lon_f = pd.to_numeric(out["birth_lon"], errors="coerce").fillna(0.0)
    jd_frac = birth_jd_f.mod(1.0)
    hour_ut = ((jd_frac + 0.5) * 24.0).mod(24.0)
    hour_local = (hour_ut + birth_lon_f / 15.0).mod(24.0)
    is_day = (hour_local >= 6.0) & (hour_local <= 18.0)
    # Preserve NaN for rows where birth_jd was missing
    out["is_day_birth"] = is_day.where(~birth_jd_f.isna(), other=pd.NA).astype("boolean")

    # Atmakaraka lookup from jaimini_karakas.parquet
    jk_path = data_dir / "jaimini_karakas.parquet"
    if jk_path.exists():
        jk = pd.read_parquet(jk_path)
        ak_rows = jk[jk["karaka"] == "AK_Atmakaraka"][["person_id", "planet"]]
        ak_map = dict(zip(ak_rows["person_id"], ak_rows["planet"]))
        out["atmakaraka"] = out["person_id"].map(ak_map)
    else:
        logger.warning("jaimini_karakas.parquet missing — Karakamsa layer stays null")
        out["atmakaraka"] = None

    # Divisional chart lookups for Karakamsa + Vimsopaka + varga pillar scores.
    # divisional_charts.parquet has 15 vargas; we use 8 of them:
    #   D1, D2, D3, D7, D9, D12, D30  — saptavargaja for Vimsopaka
    #   D10                             — added for bhava-10 (career) pillar
    # Plus the varga Lagna per person (graha=='Lagna' row in each varga)
    # for computing house-from-varga-Lagna in the pillar score.
    dc_path = data_dir / "divisional_charts.parquet"
    if dc_path.exists():
        _SAPTA_VARGAS = {
            "D1_Rashi": "D1", "D2_Hora": "D2", "D3_Drekkana": "D3",
            "D7_Saptamsa": "D7", "D9_Navamsa": "D9",
            "D12_Dwadasamsa": "D12", "D30_Trimsamsa": "D30",
        }
        # D10 is loaded for pillar scoring (bhava 10 career) but NOT
        # injected into per_planet_varga_signs (that's saptavargaja only,
        # to keep vimsopaka_for_chart on its 7-varga scheme).
        _PILLAR_VARGAS = {**_SAPTA_VARGAS, "D10_Dasamsa": "D10"}
        _VISIBLE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

        dc = pd.read_parquet(
            dc_path,
            filters=[("varga", "in", list(_PILLAR_VARGAS.keys()))],
        )

        # Build nested lookup: {person_id: {planet: {"D1": s, ..., "D30": s}}}
        per_planet_full: dict[str, dict[str, dict[str, int]]] = {}
        # Varga Lagnas: {person_id: {"D9": sign, "D10": sign, ...}}
        varga_lagnas: dict[str, dict[str, int]] = {}
        for r in dc[["person_id", "varga", "graha", "sign"]].itertuples(index=False):
            short = _PILLAR_VARGAS[r.varga]
            if r.graha == "Lagna":
                varga_lagnas.setdefault(r.person_id, {})[short] = int(r.sign)
                continue
            if r.graha not in _VISIBLE:
                continue
            person_map = per_planet_full.setdefault(r.person_id, {})
            planet_map = person_map.setdefault(r.graha, {})
            planet_map[short] = int(r.sign)

        # Saptavargaja-only view for Vimsopaka (strip D10).
        per_planet_sapta: dict[str, dict[str, dict[str, int]]] = {
            pid: {p: {v: s for v, s in vargas.items() if v != "D10"}
                  for p, vargas in planets.items()}
            for pid, planets in per_planet_full.items()
        }

        # AK D9 sign (for Karakamsa)
        d9_map: dict[tuple[str, str], int] = {}
        for pid, planets in per_planet_full.items():
            for planet, vargas in planets.items():
                if "D9" in vargas:
                    d9_map[(pid, planet)] = vargas["D9"]

        out["atmakaraka_d9_sign"] = [
            d9_map.get((pid, ak)) if ak else None
            for pid, ak in zip(out["person_id"], out["atmakaraka"])
        ]
        out["per_planet_varga_signs"] = [
            per_planet_sapta.get(pid, {}) for pid in out["person_id"]
        ]
        out["varga_pillar_scores"] = [
            _compute_varga_pillar_scores(
                per_planet_full.get(pid, {}),
                varga_lagnas.get(pid, {}),
            )
            for pid in out["person_id"]
        ]
        n_have_varga = sum(1 for v in out["per_planet_varga_signs"] if v)
        n_have_pillar = sum(1 for s in out["varga_pillar_scores"] if s)
        logger.info(
            "Loaded saptavargaja for %d/%d persons; pillar scores for %d/%d",
            n_have_varga, len(out), n_have_pillar, len(out),
        )
    else:
        logger.warning("divisional_charts.parquet missing — Karakamsa + Vimsopaka + varga pillars stay null")
        out["atmakaraka_d9_sign"] = None
        out["per_planet_varga_signs"] = [{}] * len(out)
        out["varga_pillar_scores"] = [{}] * len(out)

    # Constant target_jd snapshot — Yogini + Ashtottari are dasha-state-AT-this-date
    out["target_jd"] = snapshot_jd

    n_ak = int(out["atmakaraka"].notna().sum())
    n_d9 = int(out["atmakaraka_d9_sign"].notna().sum())
    logger.info(
        "Enriched %d rows: %d have AK, %d have AK D9 sign, "
        "Moon nakshatra/DoW/is_day populated for all",
        len(out), n_ak, n_d9,
    )
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
    parser.add_argument(
        "--snapshot-jd", type=float, default=None,
        help=(
            "Julian Day to use as the target for dasha-snapshot layers "
            "(Yogini, Ashtottari). Defaults to today's JD."
        ),
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    from app.medini.etl._freshness import skip_if_fresh

    dossier_path = args.data_dir / "person_dossier.parquet"
    jk_path = args.data_dir / "jaimini_karakas.parquet"
    d9_path = args.data_dir / "divisional_charts.parquet"
    out_path = args.data_dir / args.output
    # Tier B inputs are now dependencies — rebuild if any have changed.
    inputs = [dossier_path] + [p for p in (jk_path, d9_path) if p.exists()]
    if args.limit is None and skip_if_fresh(out_path, inputs, force=args.force):
        return 0

    dossier = pd.read_parquet(dossier_path)
    logger.info("Loaded %d dossier rows from %s", len(dossier), dossier_path)
    if args.limit is not None:
        dossier = dossier.head(args.limit)

    # Tier B enrichment: add the 5 optional master-toolkit inputs so the
    # composer can activate Karakamsa, Yogini, Ashtottari, and Maandi.
    # Default snapshot_jd = today (2026-05-31 = JD 2461191.5).
    snapshot_jd = args.snapshot_jd
    if snapshot_jd is None:
        from datetime import datetime, timezone
        # JD at 00:00 UT today
        epoch = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        snapshot_jd = 2451545.0 + (now - epoch).total_seconds() / 86400.0
    logger.info("Using snapshot_jd=%.4f for dasha-snapshot layers", snapshot_jd)
    dossier = _enrich_dossier_with_master_inputs(
        dossier, args.data_dir, snapshot_jd,
    )

    start = time.time()
    result = build_master_readings(dossier, workers=args.workers)
    elapsed = time.time() - start
    rate = len(result) / elapsed if elapsed else 0
    logger.info(
        "Built %d master readings in %.1fs (%.1f rows/sec)",
        len(result), elapsed, rate,
    )

    from app.medini.etl._parquet_io import write_parquet_zstd
    write_parquet_zstd(result, out_path)
    logger.info(
        "Wrote %d rows x %d cols to %s (ZSTD)",
        len(result), len(result.columns), out_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
