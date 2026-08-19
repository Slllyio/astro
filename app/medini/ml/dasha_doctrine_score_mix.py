"""Per-class "mix" scorer — the locked scorer assignment used in Round-11.

Reconstructed from its contract (imported by ``dasha_doctrine_pooled.py``,
``dasha_doctrine_structural.py``, ``dasha_doctrine_stratified.py``,
``dasha_doctrine_personal_disambiguation.py``). The original module was never
committed; this restores the documented behaviour.

Round-11 found that different event classes are best served by different
scorer variants:

- **s5** — bare doctrine relevance (HR + KR + func_mod).
- **s6** — relevance × dignity-strength (weights a lord by its natal dignity).
- **s8_3** — a triple-witness variant; here it falls back to s6 (the
  karaka-stripped structural module documents the same fallback).

``_PER_CLASS_SCORER`` pins which variant each class uses; ``_scorer_for``
looks it up (default s6); ``_annotate_mix`` materialises a per-row
``mix_score`` column on a dasha corpus, exactly mirroring
``dasha_doctrine_structural._annotate_structural`` but with the karaka term
retained.
"""
from __future__ import annotations

import logging
from typing import Final

import numpy as np
import pandas as pd

from app.medini.ml.dasha_doctrine_score import doctrine_relevance
from app.medini.ml.dasha_doctrine_score_strength import dignity_strength

logger = logging.getLogger(__name__)

_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)

# Locked per-class scorer assignment (Round-11). Classes not listed default
# to s6 via ``_scorer_for``.
_PER_CLASS_SCORER: Final[dict[str, str]] = {
    "marriage":                "s6",
    "relationships":           "s6",
    "career":                  "s6",
    "fame":                    "s5",
    "death":                   "s6",
    "death_cause_unspecified": "s6",
    "personal":                "s5",
    "family":                  "s6",
}

_DEFAULT_SCORER: Final[str] = "s6"


def _scorer_for(event_class: str) -> str:
    """Return the locked scorer id ({s5, s6, s8_3}) for an event class."""
    return _PER_CLASS_SCORER.get(event_class, _DEFAULT_SCORER)


def _s5_score(lord: str, event_class: str, natal_row: dict) -> float:
    """Bare relevance."""
    return doctrine_relevance(lord, event_class, natal_row)


def _s6_score(lord: str, event_class: str, natal_row: dict) -> float:
    """Relevance × dignity strength."""
    rel = doctrine_relevance(lord, event_class, natal_row)
    sign = natal_row.get(f"sign_{lord.lower()}")
    return rel * dignity_strength(lord, sign)


def mix_score(lord: str, event_class: str, natal_row: dict) -> float:
    """Dispatch on the locked per-class scorer assignment."""
    scorer = _scorer_for(event_class)
    if scorer == "s5":
        return _s5_score(lord, event_class, natal_row)
    if scorer in ("s6", "s8_3"):  # s8_3 falls back to s6 (see module docstring)
        return _s6_score(lord, event_class, natal_row)
    raise ValueError(f"unknown scorer {scorer!r}")


def _annotate_mix(
    dasha_df: pd.DataFrame, natal_df: pd.DataFrame, event_class: str,
) -> pd.DataFrame:
    """Attach a per-row ``mix_score`` column to a dasha corpus.

    For each person (keyed by ``name_norm``) pre-computes the mix score of all
    nine lords, then maps each dasha row's ``dasha_lord`` onto that person's
    score. Rows with no matching natal chart score 0.0.
    """
    natal_lookup = natal_df.set_index("name_norm").to_dict("index")
    per_person: dict[str, dict[str, float]] = {}
    for name, row in natal_lookup.items():
        per_person[name] = {
            lord: mix_score(lord, event_class, row) for lord in _LORDS
        }
    names = dasha_df["name_norm"].to_numpy()
    ds_lords = dasha_df["dasha_lord"].to_numpy()
    score = np.zeros(len(dasha_df), dtype=float)
    missing = 0
    for i in range(len(dasha_df)):
        per = per_person.get(names[i])
        if per is None:
            missing += 1
            continue
        score[i] = per.get(ds_lords[i], 0.0)
    if missing:
        logger.warning("%d rows had no matching natal_lord_houses", missing)
    out = dasha_df.copy()
    out["mix_score"] = score
    out["scorer_used"] = _scorer_for(event_class)
    return out
