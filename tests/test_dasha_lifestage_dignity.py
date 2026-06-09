"""Tests for app.medini.ml.dasha_lifestage_dignity.

Pin the composite MD-lord quality (composed from app.core.dignity +
app.core.functional_roles), the life-stage bucketing, the valence
resolution, and the stage×quality benefit-lift / gradient maths.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.dasha_lifestage_dignity import (
    annotate,
    dignity_gradient,
    event_valence,
    life_stage,
    md_lord_quality,
    pair_cross_table,
    stage_quality_table,
)

# sign integers
ARIES, TAURUS, CANCER, LEO, LIBRA, PISCES = 1, 2, 4, 5, 7, 12


# ---------- md_lord_quality (composition of canonical layers) ----------

def test_exalted_yogakaraka_is_strong() -> None:
    # Saturn exalted in Libra AND yogakaraka for Taurus lagna.
    q = md_lord_quality("Saturn", LIBRA, TAURUS)
    assert q["dignity"] == "exalted"
    assert q["yogakaraka"] is True
    assert q["quality"] == "strong"
    assert q["quality_score"] > 0.33


def test_debilitated_is_weak() -> None:
    # Saturn debilitated in Aries; natural malefic.
    q = md_lord_quality("Saturn", ARIES, CANCER)
    assert q["dignity"] == "debilitated"
    assert q["quality"] == "weak"


def test_node_has_no_functional_role_but_scores() -> None:
    q = md_lord_quality("Rahu", TAURUS, LEO)
    assert q["functional"] == "neutral"   # nodes rule no house
    assert q["quality"] in {"strong", "mixed", "weak"}


def test_quality_safe_on_missing_signs() -> None:
    q = md_lord_quality("Jupiter", None, None)
    assert q["quality"] in {"strong", "mixed", "weak"}


# ---------- life stage ----------

@pytest.mark.parametrize("age,expected", [
    (5, "childhood"), (20, "youth"), (33, "prime"),
    (50, "maturity"), (75, "elder"),
])
def test_life_stage_bands(age, expected) -> None:
    assert life_stage(age) == expected


def test_life_stage_invalid() -> None:
    assert life_stage(None) is None
    assert life_stage(-3) is None


# ---------- valence ----------

def test_valence_from_class_map() -> None:
    assert event_valence("marriage", None) == 1
    assert event_valence("death_by_disease", None) == -1
    assert event_valence("relationship", None) == 0  # deliberately neutral


def test_explicit_polarity_overrides_class() -> None:
    # class would map to +1, but explicit Adverse subtype wins.
    assert event_valence("marriage", "Adverse") == -1
    assert event_valence("anything", "Beneficial") == 1


# ---------- annotate + tables ----------

def _charts() -> pd.DataFrame:
    # p1: Saturn exalted (Libra) for Taurus lagna -> strong.
    # p2: Saturn debilitated (Aries) for Cancer lagna -> weak.
    return pd.DataFrame([
        {"person_id": "p1", "asc_sign": TAURUS, "saturn_sign": LIBRA},
        {"person_id": "p2", "asc_sign": CANCER, "saturn_sign": ARIES},
    ])


def test_annotate_attaches_columns() -> None:
    events = pd.DataFrame({
        "person_id": ["p1", "p2"],
        "event_class": ["marriage", "death"],
        "md_lord_at_event": ["Saturn", "Saturn"],
        "age_at_event_years": [33.0, 70.0],
    })
    out = annotate(events, _charts())
    assert list(out["md_quality"]) == ["strong", "weak"]
    assert list(out["life_stage"]) == ["prime", "elder"]
    assert list(out["valence"]) == [1, -1]


def test_unknown_person_gets_unknown_quality() -> None:
    events = pd.DataFrame({
        "person_id": ["ghost"],
        "event_class": ["marriage"],
        "md_lord_at_event": ["Saturn"],
        "age_at_event_years": [30.0],
    })
    out = annotate(events, _charts())
    assert out["md_quality"].iloc[0] == "unknown"


def test_stage_quality_lift_and_gradient() -> None:
    # Within 'prime': strong MD -> mostly beneficial; weak MD -> mostly adverse.
    rows = []
    for _ in range(10):
        rows.append(("strong", 1))   # beneficial under strong MD
    for _ in range(10):
        rows.append(("weak", -1))    # adverse under weak MD
    ann = pd.DataFrame({
        "md_quality": [r[0] for r in rows],
        "valence": [r[1] for r in rows],
        "life_stage": ["prime"] * len(rows),
        "md_lord_at_event": ["Saturn"] * len(rows),
    })
    tbl = stage_quality_table(ann, min_support=5)
    strong = tbl[(tbl.life_stage == "prime") & (tbl.md_quality == "strong")].iloc[0]
    weak = tbl[(tbl.life_stage == "prime") & (tbl.md_quality == "weak")].iloc[0]
    assert strong["benefit_share"] == 1.0
    assert weak["benefit_share"] == 0.0
    assert strong["benefit_lift"] > 1.0   # above the prime base rate (0.5)

    grad = dignity_gradient(tbl)
    g = grad[grad.life_stage == "prime"].iloc[0]
    assert g["gradient"] == pytest.approx(1.0)  # 1.0 - 0.0


def test_stage_quality_min_support_drops_sparse() -> None:
    ann = pd.DataFrame({
        "md_quality": ["strong"] * 3,
        "valence": [1, 1, -1],
        "life_stage": ["prime"] * 3,
        "md_lord_at_event": ["Venus"] * 3,
    })
    assert stage_quality_table(ann, min_support=5).empty


# ---------- AD lord + MD/AD pair ----------

def _charts_ad() -> pd.DataFrame:
    # Saturn strong (Libra/Taurus-lagna), Mars weak as AD (debilitated Cancer).
    return pd.DataFrame([
        {"person_id": "p1", "asc_sign": TAURUS, "saturn_sign": LIBRA, "mars_sign": CANCER},
    ])


def test_annotate_scores_ad_and_pair() -> None:
    events = pd.DataFrame({
        "person_id": ["p1"],
        "event_class": ["marriage"],
        "md_lord_at_event": ["Saturn"],
        "ad_lord_at_event": ["Mars"],
        "age_at_event_years": [33.0],
    })
    out = annotate(events, _charts_ad())
    assert out["md_quality"].iloc[0] == "strong"      # exalted+YK Saturn
    assert out["ad_quality"].iloc[0] == "weak"        # debilitated Mars
    # pair = mean of a strong (>0) and weak (<0) score → mixed/weak, not strong.
    assert out["pair_quality"].iloc[0] in {"mixed", "weak"}
    assert out["pair_label"].iloc[0] == "strong/weak"


def test_stage_quality_table_accepts_ad_column() -> None:
    ann = pd.DataFrame({
        "md_quality": ["strong"] * 10,
        "ad_quality": ["weak"] * 6 + ["strong"] * 4,
        "valence": [-1] * 6 + [1] * 4,
        "life_stage": ["prime"] * 10,
        "md_lord_at_event": ["Saturn"] * 10,
    })
    tbl = stage_quality_table(ann, quality_col="ad_quality", min_support=3)
    weak = tbl[tbl.md_quality == "weak"].iloc[0]   # generic 'md_quality' = the split col
    strong = tbl[tbl.md_quality == "strong"].iloc[0]
    assert weak["benefit_share"] == 0.0
    assert strong["benefit_share"] == 1.0


def test_pair_cross_table_grid() -> None:
    ann = pd.DataFrame({
        "md_quality": ["strong"] * 10 + ["weak"] * 10,
        "ad_quality": ["strong"] * 10 + ["weak"] * 10,
        "valence": [1] * 10 + [-1] * 10,
    })
    cross = pair_cross_table(ann, min_support=5)
    ss = cross[(cross.md_quality == "strong") & (cross.ad_quality == "strong")].iloc[0]
    ww = cross[(cross.md_quality == "weak") & (cross.ad_quality == "weak")].iloc[0]
    assert ss["benefit_share"] == 1.0 and ss["benefit_lift"] > 1.0
    assert ww["benefit_share"] == 0.0
