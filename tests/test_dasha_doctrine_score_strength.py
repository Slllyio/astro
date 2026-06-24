"""Unit tests for app.medini.ml.dasha_doctrine_score_strength.

Pins the §6 dignity-strength multiplier semantics so a future calibration
edit can't silently flip the doctrine ranks (e.g. accidentally making
debilitated > exalted).
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_score_strength import (
    _NODE_DEFAULT_STRENGTH,
    _annotate_with_strength,
    dignity_strength,
)


class TestDignityStrength:
    def test_exalted_sun_in_aries_full_strength(self) -> None:
        """Sun exalted in Aries → 1.0."""
        assert dignity_strength("Sun", 1) == 1.00

    def test_debilitated_planet_minimal_strength(self) -> None:
        """Jupiter debilitated in Capricorn → 0.10."""
        assert dignity_strength("Jupiter", 10) == 0.10

    def test_own_sign_high_strength(self) -> None:
        """Sun in Leo (own) → 0.75 (above friend, below exalted)."""
        assert dignity_strength("Sun", 5) == 0.75

    def test_unknown_planet_returns_neutral(self) -> None:
        """An unrecognised planet must NOT return 0 (would zero out the
        relevance product); fall back to neutral 0.40."""
        assert dignity_strength("Pluto", 5) == 0.40

    def test_unknown_sign_returns_neutral(self) -> None:
        """Sign outside 1-12 or None → neutral, not zero."""
        assert dignity_strength("Sun", None) == 0.40
        assert dignity_strength("Sun", 0) == 0.40
        assert dignity_strength("Sun", 13) == 0.40

    def test_nodes_use_default_strength_regardless_of_sign(self) -> None:
        """Rahu/Ketu have no classical exaltation — same value for any sign."""
        for sign in range(1, 13):
            assert dignity_strength("Rahu", sign) == _NODE_DEFAULT_STRENGTH
            assert dignity_strength("Ketu", sign) == _NODE_DEFAULT_STRENGTH

    def test_dignity_ranks_monotonic(self) -> None:
        """exalted > own > friend > neutral > enemy > debilitated.
        Lock this so any future calibration edit can't accidentally flip
        a rank (e.g. debilitated > enemy by mistake)."""
        # Sun's dignity progression by sign:
        # Aries=exalted, Leo=own, Sagittarius=friend (Jupiter rules),
        # Capricorn=enemy (Saturn rules), Libra=debilitated.
        exalted = dignity_strength("Sun", 1)
        own = dignity_strength("Sun", 5)
        debilitated = dignity_strength("Sun", 7)  # Libra
        assert exalted > own > debilitated


class TestAnnotation:
    def test_annotate_adds_three_columns(self) -> None:
        """Output has md_relevance (§5), md_strength (§6), and
        md_relevance_strong = product."""
        dasha = pd.DataFrame([{
            "name_norm": "test",
            "dasha_lord": "Jupiter",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0,
            "event_fame": 0,
        }])
        # Jupiter exalted in Cancer (sign 4).
        natal = pd.DataFrame([{
            "name_norm": "test",
            "rules_jupiter": [10], "occ_jupiter": -1, "aspects_jupiter": [],
            "rules_venus": [], "occ_venus": -1, "aspects_venus": [],
            "rules_moon": [], "occ_moon": -1, "aspects_moon": [],
            "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
            "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
            "rules_saturn": [], "occ_saturn": -1, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
            "sign_jupiter": 4, "sign_venus": 1, "sign_moon": 1,
            "sign_sun": 1, "sign_mars": 1, "sign_mercury": 1,
            "sign_saturn": 1, "sign_rahu": 1, "sign_ketu": 1,
        }])
        out = _annotate_with_strength(dasha, natal, "fame")
        assert set(["md_relevance", "md_strength", "md_relevance_strong"]) <= set(out.columns)
        # Jupiter is exalted → strength = 1.0
        assert out["md_strength"].iloc[0] == 1.00
        # md_relevance_strong = md_relevance × md_strength
        assert out["md_relevance_strong"].iloc[0] == pytest.approx(
            out["md_relevance"].iloc[0] * out["md_strength"].iloc[0]
        )

    def test_debilitated_lord_gets_penalty(self) -> None:
        """Same lord with the same house relevance but debilitated dignity
        should produce a 10x smaller modulated score than exalted."""
        dasha = pd.DataFrame([{
            "name_norm": "test",
            "dasha_lord": "Jupiter",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0,
            "event_fame": 0,
        }])
        # Two natal rows: Jupiter exalted (sign 4) vs debilitated (sign 10).
        # Both rule 10H (fame primary house) so the bare relevance is the same.
        natal_template = {
            "rules_jupiter": [10], "occ_jupiter": -1, "aspects_jupiter": [],
            "rules_venus": [], "occ_venus": -1, "aspects_venus": [],
            "rules_moon": [], "occ_moon": -1, "aspects_moon": [],
            "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
            "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
            "rules_saturn": [], "occ_saturn": -1, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
            "sign_venus": 1, "sign_moon": 1, "sign_sun": 1,
            "sign_mars": 1, "sign_mercury": 1, "sign_saturn": 1,
            "sign_rahu": 1, "sign_ketu": 1,
        }
        natal_ex = pd.DataFrame([{**natal_template,
                                  "name_norm": "exalted", "sign_jupiter": 4}])
        natal_de = pd.DataFrame([{**natal_template,
                                  "name_norm": "debilitated", "sign_jupiter": 10}])

        dasha_ex = dasha.assign(name_norm="exalted")
        dasha_de = dasha.assign(name_norm="debilitated")

        out_ex = _annotate_with_strength(dasha_ex, natal_ex, "fame")
        out_de = _annotate_with_strength(dasha_de, natal_de, "fame")

        # Same bare relevance (both rule the fame primary house + are karaka)
        assert out_ex["md_relevance"].iloc[0] == pytest.approx(
            out_de["md_relevance"].iloc[0]
        )
        # But strength-modulated: exalted 1.0 vs debilitated 0.1 → 10× ratio
        assert out_ex["md_relevance_strong"].iloc[0] == pytest.approx(
            out_de["md_relevance_strong"].iloc[0] * 10
        )
