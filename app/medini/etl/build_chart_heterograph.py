"""Phase 4 - Build the BPHS-faithful chart heterograph.

The bphs-doctrine-reviewer agent flagged that flat-tabular ML cannot
faithfully test classical doctrine because BPHS predictive logic is a
relational graph-pattern grammar (Ch.4 lordship, Ch.26 drishti, Ch.34
karakas, Ch.46 dasha witness). This module materialises one heterograph
per chart so downstream graph-neural-network ML can consume it directly.

Node types (60 nodes per chart):
  Graha       : 9   (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
  Rasi        : 12  (Aries..Pisces, 0-indexed)
  Bhava       : 12  (1st..12th house, 0-indexed)
  Nakshatra   : 27  (Ashwini..Revati, 0-indexed)

Edge types (chart-dependent, written to chart_edges.parquet):
  occupies         Graha -> Bhava   - per-chart, derived from {graha}_house
  drishti          Graha -> Bhava   - per-chart, BPHS Ch.26 + project drishti table
  dispositor_of    Graha -> Graha   - per-chart, "who rules the sign G is in"
  nakshatra_of     Graha -> Nakshatra - per-chart

Edge types (chart-INDEPENDENT, written to static_graph_edges.parquet):
  rules            Graha -> Rasi    - 12 fixed sign-rulership edges (BPHS Ch.3)
  karaka_for       Graha -> EventClass - fixed BPHS Ch.34 mapping per event domain

Output schema (chart_edges.parquet):
  person_id    TEXT  FK
  edge_type    TEXT  - one of the chart-dependent types
  src_type     TEXT  "Graha"
  src_idx      INT   0..8
  dst_type     TEXT  "Graha" | "Bhava" | "Nakshatra"
  dst_idx      INT   0..max
  attr_value   FLOAT optional aspect-house number (drishti) or 0.0

Output schema (static_graph_edges.parquet):
  edge_type    TEXT  "rules" | "karaka_for"
  src_type     TEXT
  src_idx      INT
  dst_type     TEXT
  dst_idx      INT
  attr_value   FLOAT
  attr_label   TEXT  (e.g., event class name for karaka_for)

Usage:
    python -m app.medini.etl.build_chart_heterograph
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.avastha import _DRISHTI_HOUSES

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
CHART_EDGES_FILE: Final = "chart_edges.parquet"
STATIC_EDGES_FILE: Final = "static_graph_edges.parquet"

# Canonical Graha order. Same as in build_charts_table — must stay in sync.
GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_GRAHA_TO_IDX: Final[dict[str, int]] = {g: i for i, g in enumerate(GRAHAS)}

# Classical sign rulership (BPHS Ch.3) - the 12 fixed Graha->Rasi edges.
# Rasi indices are 0-based (Aries=0, ..., Pisces=11). Note Mars rules both
# Aries (0) and Scorpio (7); Venus rules Taurus (1) and Libra (6); etc.
_SIGN_RULERSHIP: Final[dict[int, str]] = {
    0: "Mars",     1: "Venus",    2: "Mercury",  3: "Moon",
    4: "Sun",      5: "Mercury",  6: "Venus",    7: "Mars",
    8: "Jupiter",  9: "Saturn",  10: "Saturn",  11: "Jupiter",
}

# Karaka assignments per BPHS Ch.34 / Phaladeepika Ch.15. Maps each event
# class we care about to its primary signifying grahas. Multiple karakas
# per class are allowed and intentional (Sun + Mars for career = authority
# + drive). Event classes are kept aligned with the harmonised vocabulary
# used in events.parquet.
_KARAKAS: Final[dict[str, tuple[str, ...]]] = {
    "marriage":                ("Venus", "Jupiter"),  # spouse karakas
    "relationships":           ("Venus", "Moon"),
    "career":                  ("Sun", "Saturn", "Mercury"),
    "fame":                    ("Sun", "Jupiter"),
    "death_cause_unspecified": ("Saturn", "Mars"),
    "family":                  ("Moon", "Jupiter"),
}


# --------------------------------------------------------------------------- #
# Static edges (chart-independent)                                            #
# --------------------------------------------------------------------------- #

def build_static_edges() -> pd.DataFrame:
    """All edges that do NOT depend on a specific chart.

    Lives in static_graph_edges.parquet, loaded once at training time.
    """
    rows: list[dict] = []

    # Rules edges: Graha -> Rasi (12 total, BPHS Ch.3).
    for rasi_idx, ruler_name in _SIGN_RULERSHIP.items():
        rows.append({
            "edge_type": "rules",
            "src_type": "Graha",
            "src_idx": _GRAHA_TO_IDX[ruler_name],
            "dst_type": "Rasi",
            "dst_idx": rasi_idx,
            "attr_value": 1.0,
            "attr_label": ruler_name,
        })

    # Karaka edges: Graha -> EventClass (BPHS Ch.34).
    # EventClass indices are stable (alphabetical sort of dict keys for reproducibility).
    event_classes = sorted(_KARAKAS.keys())
    for ec_idx, ec in enumerate(event_classes):
        for karaka_graha in _KARAKAS[ec]:
            rows.append({
                "edge_type": "karaka_for",
                "src_type": "Graha",
                "src_idx": _GRAHA_TO_IDX[karaka_graha],
                "dst_type": "EventClass",
                "dst_idx": ec_idx,
                "attr_value": 1.0,
                "attr_label": ec,
            })

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Per-chart edges                                                             #
# --------------------------------------------------------------------------- #

def _occupies_edges(chart_row: dict) -> list[dict]:
    """Graha -> Bhava edges. One per planet."""
    out: list[dict] = []
    for graha in GRAHAS:
        house_1based = chart_row[f"{graha.lower()}_house"]
        out.append({
            "person_id": chart_row["person_id"],
            "edge_type": "occupies",
            "src_type": "Graha",
            "src_idx": _GRAHA_TO_IDX[graha],
            "dst_type": "Bhava",
            "dst_idx": house_1based - 1,  # store 0-indexed
            "attr_value": 0.0,
        })
    return out


def _drishti_edges(chart_row: dict) -> list[dict]:
    """Graha -> Bhava drishti edges per BPHS Ch.26 + project locked rules.

    Each graha aspects 1-3 houses computed relative to its own house. The
    house-distance number is stored in attr_value so the model can
    distinguish 4th-aspect (Mars martial) from 7th-aspect (opposition).
    """
    out: list[dict] = []
    for graha in GRAHAS:
        graha_house = chart_row[f"{graha.lower()}_house"]  # 1..12
        for distance in _DRISHTI_HOUSES[graha]:
            # distance counted whole-sign forward from graha's house.
            # distance=1 would be self-aspect (excluded by construction).
            target_house_1based = ((graha_house - 1 + distance - 1) % 12) + 1
            out.append({
                "person_id": chart_row["person_id"],
                "edge_type": "drishti",
                "src_type": "Graha",
                "src_idx": _GRAHA_TO_IDX[graha],
                "dst_type": "Bhava",
                "dst_idx": target_house_1based - 1,
                "attr_value": float(distance),  # 3,4,5,7,8,9,10
            })
    return out


def _dispositor_edges(chart_row: dict) -> list[dict]:
    """Graha -> Graha "is-dispositor-of" edges.

    The dispositor of graha G is the graha that rules the sign G is in.
    Closes the rulership loop on a chart's per-graha sign assignments.
    """
    out: list[dict] = []
    for graha in GRAHAS:
        sign_1based = chart_row[f"{graha.lower()}_sign"]
        ruler = _SIGN_RULERSHIP[sign_1based - 1]
        out.append({
            "person_id": chart_row["person_id"],
            "edge_type": "dispositor_of",
            "src_type": "Graha",
            "src_idx": _GRAHA_TO_IDX[ruler],
            "dst_type": "Graha",
            "dst_idx": _GRAHA_TO_IDX[graha],
            "attr_value": 0.0,
        })
    return out


def _nakshatra_edges(chart_row: dict) -> list[dict]:
    """Graha -> Nakshatra edges. One per planet (BPHS Ch.7)."""
    out: list[dict] = []
    for graha in GRAHAS:
        nak_0based = chart_row[f"{graha.lower()}_nakshatra"]
        out.append({
            "person_id": chart_row["person_id"],
            "edge_type": "nakshatra_of",
            "src_type": "Graha",
            "src_idx": _GRAHA_TO_IDX[graha],
            "dst_type": "Nakshatra",
            "dst_idx": nak_0based,
            "attr_value": 0.0,
        })
    return out


def edges_for_chart(chart_row: dict) -> list[dict]:
    """All chart-dependent edges for one chart."""
    return (
        _occupies_edges(chart_row)
        + _drishti_edges(chart_row)
        + _dispositor_edges(chart_row)
        + _nakshatra_edges(chart_row)
    )


def build_chart_edges(charts: pd.DataFrame) -> pd.DataFrame:
    """Flatten all charts into one long-format edge dataframe."""
    rows: list[dict] = []
    chart_dicts = charts.to_dict(orient="records")
    for chart in chart_dicts:
        rows.extend(edges_for_chart(chart))
    logger.info("Built %d chart-dependent edges across %d charts (~%d edges/chart)",
                len(rows), len(charts), len(rows) // max(1, len(charts)))
    return pd.DataFrame(rows)


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    # Static edges first - tiny, fast.
    static = build_static_edges()
    static.to_parquet(args.data_dir / STATIC_EDGES_FILE, index=False)
    logger.info("Wrote %d static edges to %s",
                len(static), args.data_dir / STATIC_EDGES_FILE)

    # Per-chart edges.
    charts = pd.read_parquet(args.data_dir / "charts.parquet")
    if args.limit is not None:
        charts = charts.head(args.limit)
    chart_edges = build_chart_edges(charts)
    chart_edges.to_parquet(args.data_dir / CHART_EDGES_FILE, index=False)
    logger.info("Wrote %d chart edges to %s",
                len(chart_edges), args.data_dir / CHART_EDGES_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
