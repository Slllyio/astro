"""Unit tests for app.medini.ml.dasha_doctrine_score_mix.

Pins the doctrine-informed per-class scorer assignment so a future edit
can't quietly remap (say) `fame` from §6 strength to §5 bare without a
test failing.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_score_mix import (
    _PER_CLASS_SCORER,
    _annotate_mix,
    _scorer_for,
    mix_score,
)


class TestPerClassAssignment:
    """The locked classical mapping. Edits must come with a doctrine
    citation, not data-fishing."""

    def test_fame_uses_strength_scorer(self) -> None:
        """BPHS 27.62 + Phaladeepika: honour follows planetary strength."""
        assert _scorer_for("fame") == "s6"

    def test_personal_uses_strength_scorer(self) -> None:
        """Phaladeepika Ch.4: personal events tied to lord strength."""
        assert _scorer_for("personal") == "s6"

    def test_relationships_uses_triple_witness(self) -> None:
        """Raman/Rao: yoga-style partnerships need triple-witness rule."""
        assert _scorer_for("relationships") == "s8_3"

    def test_marriage_defaults_to_s5(self) -> None:
        """Marriage is timing-driven (dasha+transit), not strength-driven."""
        assert _scorer_for("marriage") == "s5"

    def test_unknown_class_defaults_to_s5(self) -> None:
        """Anything not in the locked mapping uses bare §5."""
        assert _scorer_for("nonsense") == "s5"

    def test_locked_mapping_has_exactly_three_entries(self) -> None:
        """Sanity: only three classes get non-default scorers. Adding a
        fourth requires intentional doctrinal justification."""
        assert set(_PER_CLASS_SCORER.keys()) == {
            "fame", "personal", "relationships",
        }


def _full_natal_row(name: str, jupiter_sign: int = 5) -> dict:
    """Synthetic natal row with all required columns. Jupiter rules 10H,
    other planets neutralised."""
    base = {
        "name_norm": name,
        "rules_sun": [], "occ_sun": -1, "aspects_sun": [],
        "rules_moon": [], "occ_moon": -1, "aspects_moon": [],
        "rules_mars": [], "occ_mars": -1, "aspects_mars": [],
        "rules_mercury": [], "occ_mercury": -1, "aspects_mercury": [],
        "rules_jupiter": [10], "occ_jupiter": -1, "aspects_jupiter": [],
        "rules_venus": [], "occ_venus": -1, "aspects_venus": [],
        "rules_saturn": [], "occ_saturn": -1, "aspects_saturn": [],
        "rules_rahu": [], "occ_rahu": -1, "aspects_rahu": [],
        "rules_ketu": [], "occ_ketu": -1, "aspects_ketu": [],
        "sign_sun": 1, "sign_moon": 1, "sign_mars": 1,
        "sign_mercury": 1, "sign_jupiter": jupiter_sign,
        "sign_venus": 1, "sign_saturn": 1, "sign_rahu": 1, "sign_ketu": 1,
    }
    return base


class TestMixScoreDispatch:
    """Verify mix_score routes to the right per-class scorer."""

    def test_fame_route_picks_strength_scorer(self) -> None:
        """Same Jupiter, two different signs (dignity differs):
        the fame scorer must produce different results because it's §6
        (strength-modulated)."""
        natal_ex = _full_natal_row("t", jupiter_sign=4)  # exalted
        natal_de = _full_natal_row("t", jupiter_sign=10)  # debilitated
        s_ex = mix_score("Jupiter", "fame", natal_ex)
        s_de = mix_score("Jupiter", "fame", natal_de)
        assert s_ex > s_de  # strength differentiates exalted vs debilitated

    def test_marriage_route_picks_bare_s5(self) -> None:
        """Marriage uses bare §5: same dignity differences should NOT
        change the score, because §5 doesn't read planetary strength."""
        natal_ex = _full_natal_row("t", jupiter_sign=4)
        natal_de = _full_natal_row("t", jupiter_sign=10)
        s_ex = mix_score("Jupiter", "marriage", natal_ex)
        s_de = mix_score("Jupiter", "marriage", natal_de)
        # Jupiter rules 10H in both — house map for marriage is
        # {7:1.0, 2:0.5, 11:0.5, 4:0.25, 5:0.25}. Jupiter doesn't rule any
        # of those, isn't a marriage karaka in our table? Actually it IS
        # (karaka_map["marriage"] = {Venus, Jupiter}). So KR contributes.
        # The KR is the same regardless of dignity (it's a fixed lookup).
        # HR is also the same (Jupiter doesn't rule marriage houses).
        # → s5 produces IDENTICAL score regardless of sign.
        assert s_ex == s_de

    def test_relationships_route_uses_triwit(self) -> None:
        """Relationships → §8.3 triple-witness. Min(bh, kr, md). If any
        witness drops to 0 (lord with no relation), composite drops."""
        # Use Saturn as the MD lord — Saturn isn't related to Venus
        # (the relationships karaka) or 7H (no rulership). So:
        # - bhavesha = lord of 7H (unknown in this synthetic row → 0)
        # - karaka = max Venus s6 strength
        # - md_lord = Saturn s6 strength → 0 (not karaka, no 7H rules)
        # min(0, ..., 0) = 0
        natal = _full_natal_row("t", jupiter_sign=4)
        score = mix_score("Saturn", "relationships", natal)
        # Triwit collapses to 0 when MD lord is unrelated
        assert score == 0.0


class TestAnnotationEndToEnd:
    def test_mix_score_column_added(self) -> None:
        """Annotation adds mix_score + scorer_used columns."""
        dasha = pd.DataFrame([
            {"name_norm": "p1", "dasha_lord": "Jupiter",
             "dasha_start_jd": 0.0, "dasha_end_jd": 10.0, "event_fame": 0},
            {"name_norm": "p2", "dasha_lord": "Jupiter",
             "dasha_start_jd": 0.0, "dasha_end_jd": 10.0, "event_fame": 0},
        ])
        natal = pd.DataFrame([
            _full_natal_row("p1", jupiter_sign=4),  # exalted
            _full_natal_row("p2", jupiter_sign=10),  # debilitated
        ])
        out = _annotate_mix(dasha, natal, "fame")
        assert "mix_score" in out.columns
        assert "scorer_used" in out.columns
        assert (out["scorer_used"] == "s6").all()
        # Exalted person should score higher than debilitated
        assert out.iloc[0]["mix_score"] > out.iloc[1]["mix_score"]
