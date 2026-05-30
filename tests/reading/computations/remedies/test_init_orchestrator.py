"""Tests for the unified ``generate_remedies`` entry point on the
``app.reading.computations.remedies`` package.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs). The unified orchestrator returns a dict with
four keys -- ``mantras``, ``gemstones``, ``daan``, ``yantras`` -- each
mapping to a list of Findings. Discipline:

  - ``daan + mantras + yantras`` are returned for ALL afflicted planets.
  - ``gemstones`` are filtered by the lagna-suitability gate (only safe
    planets get a positive gem; functional_malefic planets surface a
    BLOCKED Finding).

This wraps the four sub-modules. The orchestrator does NOT re-validate
inputs -- delegating to the sub-modules -- but it does pin the
``afflicted_planets`` order across the three "per-planet" categories so
downstream consumers can rely on consistent ordering.
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


def _natures_all(label: str) -> dict[str, str]:
    return {p: label for p in _PLANETS}


# ---------------------------------------------------------------------------
# Shape / contract
# ---------------------------------------------------------------------------


class TestGenerateRemediesShape:

    def test_returns_dict_with_four_keys(self):
        from app.reading.computations.remedies import generate_remedies

        out = generate_remedies(
            afflicted_planets=["Saturn"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        assert isinstance(out, dict)
        assert set(out.keys()) == {"mantras", "gemstones", "daan", "yantras"}

    def test_each_value_is_finding_list(self):
        from app.reading.computations.remedies import generate_remedies
        from app.reading.schema import Finding

        out = generate_remedies(
            afflicted_planets=["Saturn", "Mars"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        for key, val in out.items():
            assert isinstance(val, list), f"{key} is not a list"
            for f in val:
                assert isinstance(f, Finding), f"{key} contains non-Finding"

    def test_empty_afflicted_planets(self):
        """Empty afflicted list -> mantras/daan/yantras empty;
        gemstones may still emit blockings for malefic planets."""
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        out = generate_remedies(
            afflicted_planets=[],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=nats,
        )
        assert out["mantras"] == []
        assert out["daan"] == []
        assert out["yantras"] == []
        # Gemstones may also be empty here since no planet is malefic and
        # no eligible benefic exists in nats.
        assert out["gemstones"] == []


# ---------------------------------------------------------------------------
# Three-tier discipline: daan + mantras + yantras for ALL afflicted
# ---------------------------------------------------------------------------


class TestThreeTierDiscipline:
    """For every afflicted planet, daan + mantras + yantras MUST exist
    (independent of lagna/dignity). Gemstones are conditional only."""

    def test_each_afflicted_planet_gets_mantra(self):
        from app.reading.computations.remedies import generate_remedies

        out = generate_remedies(
            afflicted_planets=["Saturn", "Mars", "Rahu"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        ids = {f.id for f in out["mantras"]}
        assert "practitioner.remedies.mantra.saturn" in ids
        assert "practitioner.remedies.mantra.mars" in ids
        assert "practitioner.remedies.mantra.rahu" in ids

    def test_each_afflicted_planet_gets_daan(self):
        from app.reading.computations.remedies import generate_remedies

        out = generate_remedies(
            afflicted_planets=["Saturn", "Mars", "Rahu"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        ids = {f.id for f in out["daan"]}
        assert "practitioner.remedies.daan.saturn" in ids
        assert "practitioner.remedies.daan.mars" in ids
        assert "practitioner.remedies.daan.rahu" in ids

    def test_each_afflicted_planet_gets_yantra(self):
        from app.reading.computations.remedies import generate_remedies

        out = generate_remedies(
            afflicted_planets=["Saturn", "Mars"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        ids = {f.id for f in out["yantras"]}
        assert "practitioner.remedies.yantra.saturn" in ids
        assert "practitioner.remedies.yantra.mars" in ids

    def test_mantras_daan_yantras_have_same_planets(self):
        """Cross-check that all three per-planet categories cover the
        same set of afflicted planets."""
        from app.reading.computations.remedies import generate_remedies

        afflicted = ["Saturn", "Mars", "Rahu"]
        out = generate_remedies(
            afflicted_planets=afflicted,
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        m_planets = {f.id.rsplit(".", 1)[-1] for f in out["mantras"]}
        d_planets = {f.id.rsplit(".", 1)[-1] for f in out["daan"]}
        y_planets = {f.id.rsplit(".", 1)[-1] for f in out["yantras"]}
        assert m_planets == d_planets == y_planets
        assert m_planets == {p.lower() for p in afflicted}


# ---------------------------------------------------------------------------
# Gem-gating discipline: lagna-suitability filter
# ---------------------------------------------------------------------------


class TestGemGatingDiscipline:
    """Gems are emitted ONLY when the eligibility gate passes (positive)
    or when the planet is functional_malefic (BLOCKED). The orchestrator
    must delegate to recommend_gemstones with the full parameter bundle."""

    def test_gems_block_for_aries_lagna_saturn_malefic(self):
        """The critical invariant: Aries lagna + Saturn malefic -> Blue
        Sapphire surfaces as BLOCKED in out['gemstones']."""
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"   # 1L Aries
        nats["Saturn"] = "functional_malefic" # blocked
        out = generate_remedies(
            afflicted_planets=["Saturn"],  # afflicted: Saturn gets daan/mantra/yantra
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=nats,
        )
        blue = [
            f for f in out["gemstones"]
            if f.id == "practitioner.remedies.gemstone.blue_sapphire"
        ]
        assert blue, "Blue sapphire blocking Finding missing"
        assert all(f.direction == "negative" for f in blue)

    def test_gems_recommend_for_eligible_benefic_lagna_lord(self):
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        out = generate_remedies(
            afflicted_planets=["Saturn"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=nats,
        )
        coral_pos = [
            f for f in out["gemstones"]
            if f.id == "practitioner.remedies.gemstone.red_coral"
            and f.direction == "positive"
        ]
        assert coral_pos, "Red Coral positive Finding missing"

    def test_gems_dont_emit_for_unaffected_neutral_planets(self):
        """A neutral planet not in {1L,5L,9L,AK} produces no gem at all."""
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        out = generate_remedies(
            afflicted_planets=["Mars"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=nats,
        )
        assert out["gemstones"] == []

    def test_daan_before_gem_principle(self):
        """For Saturn afflicted, daan/mantra/yantra must EXIST even when
        no gem is recommended (or gem is blocked) — the daan-before-gem
        discipline."""
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"  # gem blocked
        out = generate_remedies(
            afflicted_planets=["Saturn"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1,
            functional_natures=nats,
        )
        # Saturn gets pacification via daan, mantra, yantra.
        assert any(f.id == "practitioner.remedies.daan.saturn" for f in out["daan"])
        assert any(f.id == "practitioner.remedies.mantra.saturn" for f in out["mantras"])
        assert any(f.id == "practitioner.remedies.yantra.saturn" for f in out["yantras"])
        # And the gem is BLOCKED, not silently omitted.
        gem_ids = {f.id for f in out["gemstones"]}
        assert "practitioner.remedies.gemstone.blue_sapphire" in gem_ids


# ---------------------------------------------------------------------------
# Realistic Aries-lagna scenario (end-to-end)
# ---------------------------------------------------------------------------


class TestAriesLagnaScenario:
    """Realistic chart: Aries lagna, Mars 1L benefic, Jupiter 9L benefic,
    Saturn functional_malefic, afflicted planets are [Saturn, Rahu]."""

    def test_aries_lagna_end_to_end(self):
        from app.reading.computations.remedies import generate_remedies

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        nats["Jupiter"] = "functional_benefic"
        nats["Saturn"] = "functional_malefic"
        out = generate_remedies(
            afflicted_planets=["Saturn", "Rahu"],
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Jupiter", asc_sign=1,
            functional_natures=nats,
        )
        # Three per-planet categories: 2 Findings each (Saturn, Rahu).
        assert len(out["mantras"]) == 2
        assert len(out["daan"]) == 2
        assert len(out["yantras"]) == 2
        # Gems: Red Coral (Mars benefic + 1L) positive,
        #       Yellow Sapphire (Jupiter benefic + 9L) positive,
        #       Blue Sapphire (Saturn malefic) negative.
        gem_pos = {
            f.id for f in out["gemstones"] if f.direction == "positive"
        }
        gem_neg = {
            f.id for f in out["gemstones"] if f.direction == "negative"
        }
        assert "practitioner.remedies.gemstone.red_coral" in gem_pos
        assert "practitioner.remedies.gemstone.yellow_sapphire" in gem_pos
        assert "practitioner.remedies.gemstone.blue_sapphire" in gem_neg


# ---------------------------------------------------------------------------
# Re-exports from the package
# ---------------------------------------------------------------------------


class TestPackageReexports:
    """The four sub-module entry points must be re-exported on the
    package namespace so the domains/* layer doesn't need to know about
    individual sub-modules."""

    def test_recommend_mantras_reexported(self):
        from app.reading.computations.remedies import recommend_mantras

        assert callable(recommend_mantras)

    def test_recommend_gemstones_reexported(self):
        from app.reading.computations.remedies import recommend_gemstones

        assert callable(recommend_gemstones)

    def test_recommend_daan_reexported(self):
        from app.reading.computations.remedies import recommend_daan

        assert callable(recommend_daan)

    def test_recommend_yantras_reexported(self):
        from app.reading.computations.remedies import recommend_yantras

        assert callable(recommend_yantras)

    def test_generate_remedies_reexported(self):
        from app.reading.computations.remedies import generate_remedies

        assert callable(generate_remedies)


# ---------------------------------------------------------------------------
# Input validation delegation
# ---------------------------------------------------------------------------


class TestInputValidation:
    """The orchestrator delegates validation to sub-modules but bad
    inputs must still raise ValueError somewhere up the stack."""

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.remedies import generate_remedies

        with pytest.raises(ValueError):
            generate_remedies(
                afflicted_planets=["Saturn"],
                lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
                atmakaraka="Mars", asc_sign=13,
                functional_natures=_natures_all("functional_neutral"),
            )

    def test_invalid_planet_in_afflicted_raises(self):
        from app.reading.computations.remedies import generate_remedies

        with pytest.raises(ValueError):
            generate_remedies(
                afflicted_planets=["Pluto"],
                lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
                atmakaraka="Mars", asc_sign=1,
                functional_natures=_natures_all("functional_neutral"),
            )
