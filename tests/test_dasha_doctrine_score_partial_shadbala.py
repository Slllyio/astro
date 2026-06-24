"""Unit tests for app.medini.ml.dasha_doctrine_score_partial_shadbala.

Pins the partial-Shadbala composition: sum of 4 balas (sthana via
dignity, dig, naisargika, drik) normalized into a [0.05, 1.5] multiplier.

Key invariants tested:
  * Sum-in-virupa shape matches expectations from app.core.shadbala.
  * Strength multiplier is clipped to a sane range (no zeroing-out).
  * Exalted-in-best-house planet >> debilitated-in-worst-house planet.
  * Nodes get a neutral default (no Dig/Drik defined classically).
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_score_partial_shadbala import (
    _NODE_VIRUPA,
    _PARTIAL_SHADBALA_SCALE,
    _annotate_with_shadbala,
    partial_shadbala_strength,
    partial_shadbala_virupa,
)


def _make_natal_row(
    sign_jupiter: int, house_jupiter: int,
    *, other_planets_friendly: bool = True,
) -> dict:
    """Construct a synthetic natal_row for testing.

    Other planets default to neutral positions so the focal Jupiter
    measurements aren't perturbed by accidental drik aspects.
    """
    base = {
        "name_norm": "test",
        # Default all other planets to sign 5 (Leo), unaspecting position
        "sign_sun":      5,  "occ_sun":      11,
        "sign_moon":     5,  "occ_moon":     11,
        "sign_mars":     5,  "occ_mars":     11,
        "sign_mercury":  5,  "occ_mercury":  11,
        "sign_jupiter":  sign_jupiter,
        "occ_jupiter":   house_jupiter,
        "sign_venus":    5,  "occ_venus":    11,
        "sign_saturn":   5,  "occ_saturn":   11,
        "sign_rahu":     5,  "occ_rahu":     11,
        "sign_ketu":     5,  "occ_ketu":     11,
    }
    return base


class TestPartialShadbalaVirupa:
    def test_exalted_jupiter_in_strongest_house(self) -> None:
        """Jupiter exalted (Cancer=4) AND in 1st house (its dig=max for
        Jupiter). Expected: high partial-shadbala virupa.

        Components: sthana=60 (exalted) + dig=60 (Jupiter's dig is 1H)
        + naisargika ~38.6 + drik=0 (no aspects from default chart)
        = ~158 virupa."""
        natal = _make_natal_row(sign_jupiter=4, house_jupiter=1)
        v = partial_shadbala_virupa("Jupiter", natal)
        assert v > 130
        assert v < 200

    def test_debilitated_jupiter_in_weakest_house(self) -> None:
        """Jupiter debilitated (Capricorn=10) in 7H (opposite of Jupiter's
        dig=1H). Expected: low partial-shadbala virupa.

        Components: sthana=6 (debilitated) + dig=0 + naisargika ~38.6
        + drik=0 = ~45 virupa."""
        natal = _make_natal_row(sign_jupiter=10, house_jupiter=7)
        v = partial_shadbala_virupa("Jupiter", natal)
        assert v < 60

    def test_exalted_outranks_debilitated(self) -> None:
        """Same chart structure except Jupiter sign+house: exalted+1H must
        produce strictly higher partial-shadbala than debilitated+7H."""
        natal_strong = _make_natal_row(sign_jupiter=4, house_jupiter=1)
        natal_weak = _make_natal_row(sign_jupiter=10, house_jupiter=7)
        v_strong = partial_shadbala_virupa("Jupiter", natal_strong)
        v_weak = partial_shadbala_virupa("Jupiter", natal_weak)
        assert v_strong > v_weak + 30  # at least one bala-worth gap

    def test_nodes_return_neutral_default(self) -> None:
        """Rahu/Ketu have no classical Dig/Drik bala — return _NODE_VIRUPA
        regardless of sign/house input."""
        natal = _make_natal_row(sign_jupiter=4, house_jupiter=1)
        assert partial_shadbala_virupa("Rahu", natal) == _NODE_VIRUPA
        assert partial_shadbala_virupa("Ketu", natal) == _NODE_VIRUPA


class TestPartialShadbalaStrength:
    def test_multiplier_in_clipped_range(self) -> None:
        """Normalized strength must land in [0.05, 1.5] regardless of
        input — the clip prevents degenerate-multiplier rows from killing
        the §5 relevance product."""
        natal_strong = _make_natal_row(sign_jupiter=4, house_jupiter=1)
        natal_weak = _make_natal_row(sign_jupiter=10, house_jupiter=7)
        for natal in (natal_strong, natal_weak):
            for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                           "Venus", "Saturn", "Rahu", "Ketu"):
                s = partial_shadbala_strength(planet, natal)
                assert 0.05 <= s <= 1.5

    def test_normalization_scale(self) -> None:
        """Strength = virupa / 240 (clipped). Verify the ratio."""
        natal = _make_natal_row(sign_jupiter=4, house_jupiter=1)
        v = partial_shadbala_virupa("Jupiter", natal)
        s = partial_shadbala_strength("Jupiter", natal)
        # Exalted-strong Jupiter is well above 60 virupa so the clip
        # doesn't fire; ratio should match.
        assert s == pytest.approx(v / _PARTIAL_SHADBALA_SCALE, abs=1e-9)

    def test_floor_prevents_zero_multiplier(self) -> None:
        """A row with very low virupa (drik very negative) must still
        produce a positive multiplier so §5 relevance ranking is preserved
        when binning. Floor is 0.05."""
        # Construct a chart where all benefics are far from Jupiter and
        # all malefics aspect it. Saturn in 1H gives Saturn aspecting 10H
        # (Saturn special aspect from 1H: signs 3, 7, 10 → 4H, 8H, 11H from
        # Saturn). Put Saturn in same sign as Jupiter for direct conjunction.
        natal = _make_natal_row(sign_jupiter=10, house_jupiter=7)
        natal["sign_saturn"] = 10  # Saturn conjunct Jupiter
        natal["sign_sun"] = 10      # Sun conjunct Jupiter (malefic)
        natal["sign_mars"] = 10     # Mars conjunct Jupiter (malefic)
        s = partial_shadbala_strength("Jupiter", natal)
        assert s >= 0.05


class TestAnnotation:
    """End-to-end: annotate a dasha frame with partial-shadbala columns."""

    def test_annotate_adds_three_columns(self) -> None:
        dasha = pd.DataFrame([{
            "name_norm": "test",
            "dasha_lord": "Jupiter",
            "dasha_start_jd": 0.0, "dasha_end_jd": 10.0,
            "event_fame": 0,
        }])
        # Jupiter rules 10H + is fame karaka + exalted + dig=1H
        natal = pd.DataFrame([{
            **_make_natal_row(sign_jupiter=4, house_jupiter=1),
            "rules_jupiter": [10], "occ_jupiter": 1, "aspects_jupiter": [],
            "rules_sun": [], "occ_sun": 11, "aspects_sun": [],
            "rules_moon": [], "occ_moon": 11, "aspects_moon": [],
            "rules_mars": [], "occ_mars": 11, "aspects_mars": [],
            "rules_mercury": [], "occ_mercury": 11, "aspects_mercury": [],
            "rules_venus": [], "occ_venus": 11, "aspects_venus": [],
            "rules_saturn": [], "occ_saturn": 11, "aspects_saturn": [],
            "rules_rahu": [], "occ_rahu": 11, "aspects_rahu": [],
            "rules_ketu": [], "occ_ketu": 11, "aspects_ketu": [],
        }])
        out = _annotate_with_shadbala(dasha, natal, "fame")
        assert set(["md_relevance", "md_shadbala",
                    "md_relevance_shadbala"]) <= set(out.columns)
        # md_relevance_shadbala = md_relevance × md_shadbala
        assert out["md_relevance_shadbala"].iloc[0] == pytest.approx(
            out["md_relevance"].iloc[0] * out["md_shadbala"].iloc[0]
        )
