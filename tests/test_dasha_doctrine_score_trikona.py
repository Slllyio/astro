"""Unit tests for app.medini.ml.dasha_doctrine_score_trikona.

Pins the §8.3 triple-witness semantics: min over (bhavesha, karaka,
md_lord) strength-modulated relevances. Critical invariant: any single
weak witness collapses the composite (the doctrine's "weakest link"
encoding of B.V. Raman's classical claim).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_score_trikona import (
    _annotate_trikona,
    _bhavesha_planet,
    _primary_house_for,
)


class TestPrimaryHouse:
    def test_fame_primary_is_10h(self) -> None:
        """Fame's primary house per BPHS Ch.27 is the 10H (career/honour)."""
        assert _primary_house_for("fame") == 10

    def test_marriage_primary_is_7h(self) -> None:
        assert _primary_house_for("marriage") == 7

    def test_personal_primary_is_1h(self) -> None:
        assert _primary_house_for("personal") == 1

    def test_unknown_class_returns_none(self) -> None:
        assert _primary_house_for("nonsense") is None


class TestBhaveshaLookup:
    def test_finds_lord_of_house(self) -> None:
        """Jupiter rules 10H → Jupiter is the bhavesha of 10H (fame)."""
        natal = {
            "rules_sun": [], "rules_moon": [],
            "rules_mars": [], "rules_mercury": [],
            "rules_jupiter": [10], "rules_venus": [],
            "rules_saturn": [], "rules_rahu": [], "rules_ketu": [],
        }
        assert _bhavesha_planet(10, natal) == "Jupiter"

    def test_no_lord_returns_none(self) -> None:
        """Chart with no planet ruling that house → None (graceful)."""
        natal = {
            "rules_sun": [], "rules_moon": [],
            "rules_mars": [], "rules_mercury": [],
            "rules_jupiter": [], "rules_venus": [],
            "rules_saturn": [], "rules_rahu": [], "rules_ketu": [],
        }
        assert _bhavesha_planet(10, natal) is None


class TestTrikonaWitness:
    """End-to-end triwit_strength = min(bh, kr, md_lord)."""

    def _make_natal(self, sign_jupiter: int) -> pd.DataFrame:
        """Synthetic natal row with Jupiter ruling 10H (fame bhavesha)
        and given Jupiter sign. All other planets dignity-neutral."""
        return pd.DataFrame([{
            "name_norm": "test",
            "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
            "rules_moon": [], "occ_moon": -1, "aspects_moon": [],
            "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
            "rules_jupiter": [10], "occ_jupiter": -1, "aspects_jupiter": [],
            "rules_venus": [], "occ_venus": -1, "aspects_venus": [],
            "rules_saturn": [], "occ_saturn": -1, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
            "sign_sun": 5, "sign_moon": 5, "sign_mars": 5,
            "sign_mercury": 5, "sign_jupiter": sign_jupiter,
            "sign_venus": 5, "sign_saturn": 5,
            "sign_rahu": 5, "sign_ketu": 5,
        }])

    def test_weak_md_lord_collapses_composite(self) -> None:
        """Jupiter rules 10H (strong bhavesha) AND is fame karaka → both
        witnesses high. But if a non-fame-related lord (e.g. Saturn here,
        with no relation to fame) runs the MD, triwit = md_witness ≈ 0.
        The triple-witness rule should collapse the composite."""
        natal = self._make_natal(sign_jupiter=4)  # Jupiter exalted in Cancer
        dasha = pd.DataFrame([{
            "name_norm": "test",
            "dasha_lord": "Saturn",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0,
            "event_fame": 0,
        }])
        out = _annotate_trikona(dasha, natal, "fame")
        # bhavesha = Jupiter exalted, strong; karaka = max(Sun, Jupiter)
        # → Jupiter; md_lord = Saturn (no fame relation in this chart).
        assert out["bhavesha_witness"].iloc[0] > 0
        assert out["karaka_witness"].iloc[0] > 0
        assert out["md_witness"].iloc[0] == pytest.approx(0.0)
        # Triwit collapses to the min = 0
        assert out["triwit_strength"].iloc[0] == 0.0

    def test_all_three_witnesses_strong_composite_high(self) -> None:
        """Jupiter exalted, rules 10H, MD = Jupiter → all three witnesses
        identical (Jupiter strong) → triwit = full Jupiter strength."""
        natal = self._make_natal(sign_jupiter=4)  # exalted
        dasha = pd.DataFrame([{
            "name_norm": "test",
            "dasha_lord": "Jupiter",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0,
            "event_fame": 0,
        }])
        out = _annotate_trikona(dasha, natal, "fame")
        # All three witnesses are the same Jupiter strength
        assert out["bhavesha_witness"].iloc[0] == out["karaka_witness"].iloc[0]
        assert out["md_witness"].iloc[0] == out["karaka_witness"].iloc[0]
        # Triwit = that strength (min == max here)
        assert out["triwit_strength"].iloc[0] == pytest.approx(
            out["bhavesha_witness"].iloc[0]
        )
        assert out["triwit_strength"].iloc[0] > 0

    def test_negative_witnesses_clipped_to_zero(self) -> None:
        """If any witness is negative (compound dusthana penalty), clip
        to 0 — keeps quintile binning well-behaved (negative-rich bottom
        bin wouldn't degenerate)."""
        natal = pd.DataFrame([{
            "name_norm": "test",
            # Jupiter rules 6+8+12 → triple dusthana, fc_mod=-0.5
            "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
            "rules_moon": [], "occ_moon": -1, "aspects_moon": [],
            "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
            "rules_jupiter": [6, 8, 12], "occ_jupiter": -1, "aspects_jupiter": [],
            "rules_venus": [], "occ_venus": -1, "aspects_venus": [],
            "rules_saturn": [10], "occ_saturn": -1, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
            "sign_sun": 5, "sign_moon": 5, "sign_mars": 5,
            "sign_mercury": 5, "sign_jupiter": 5, "sign_venus": 5,
            "sign_saturn": 5, "sign_rahu": 5, "sign_ketu": 5,
        }])
        # bhavesha for fame (10H) = Saturn here. Jupiter karaka → strongly
        # negative (-0.5 func_mod and no fame house relation).
        dasha = pd.DataFrame([{
            "name_norm": "test", "dasha_lord": "Jupiter",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0, "event_fame": 0,
        }])
        out = _annotate_trikona(dasha, natal, "fame")
        # Triwit must be non-negative (clipped before min)
        assert out["triwit_strength"].iloc[0] >= 0
