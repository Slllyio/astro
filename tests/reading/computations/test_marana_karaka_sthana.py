"""Tests for ``app.reading.computations.marana_karaka_sthana``.

Doctrine lock D-9 (``docs/doctrine-decisions.md``):

    Marana Karaka Sthana (MKS) — house where each planet "loses
    effectiveness." The canonical BPHS Vol.I Ch.46 table:

        Sun     -> 12
        Moon    -> 8
        Mars    -> 7
        Mercury -> 7
        Jupiter -> 3
        Venus   -> 6
        Saturn  -> 1
        Rahu    -> 9
        Ketu    -> not applicable (sentinel None)

A planet placed in its MKS house emits a negative ``affliction`` Finding.
Ketu carries no MKS finding regardless of placement (sentinel-aware).

Algorithm summary
=================

For each of the 9 planets:
  - Look up the canonical MKS house.
  - Compute the planet's whole-sign house from the ascendant.
  - Emit a Finding only when the planet sits in its MKS house.
Ketu is skipped (sentinel None) — its non-emission is part of the contract.
"""
from __future__ import annotations

import pytest


_PLANETS_WITH_MKS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu",
)


# Canonical MKS table per D-9 (BPHS Vol.I Ch.46).
_EXPECTED_MKS_HOUSES: dict[str, int] = {
    "Sun": 12,
    "Moon": 8,
    "Mars": 7,
    "Mercury": 7,
    "Jupiter": 3,
    "Venus": 6,
    "Saturn": 1,
    "Rahu": 9,
}


# ---------------------------------------------------------------------------
# Helpers — build d1_chart fixtures programmatically.
# ---------------------------------------------------------------------------


def _planet_in_house(asc_sign: int, target_house: int) -> int:
    """Return the 1..12 sign that places a planet in ``target_house`` from
    the given ``asc_sign`` using whole-sign math.

    house = ((sign - asc_sign) % 12) + 1
    ⇒ sign = ((asc_sign + house - 2) % 12) + 1
    """
    return ((asc_sign + target_house - 2) % 12) + 1


def _planet_dict(sign: int) -> dict:
    """Minimal planet record consumed by the MKS detector (only ``sign``)."""
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart_with(asc_sign: int, placements: dict[str, int]) -> dict:
    """Build a d1_chart dict where each named planet sits in the requested
    HOUSE (1..12) from ``asc_sign``. Planets not specified get a benign
    placement (1st house — out of every MKS slot, since 1 is Saturn's MKS
    only, and Saturn is included only when explicitly specified)."""
    chart: dict[str, dict] = {}
    benign_sign = asc_sign  # 1st-house placement
    for planet in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        if planet in placements:
            chart[planet] = _planet_dict(_planet_in_house(asc_sign, placements[planet]))
        elif planet == "Saturn":
            # Place Saturn somewhere innocuous (2nd house — not MKS for Saturn).
            chart[planet] = _planet_dict(_planet_in_house(asc_sign, 2))
        else:
            chart[planet] = _planet_dict(benign_sign)
    return chart


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestDetectMksShape:

    def test_returns_dict(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        chart = _chart_with(asc_sign=1, placements={})
        result = detect_mks(chart, asc_sign=1)
        assert isinstance(result, dict)

    def test_only_emits_for_afflicted_planets(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        # No planet in its MKS slot → empty dict.
        chart = _chart_with(asc_sign=1, placements={})
        result = detect_mks(chart, asc_sign=1)
        assert result == {}

    def test_emits_finding_when_planet_in_mks(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks
        from app.reading.schema import Finding

        # Saturn in 1st house (its MKS) for Aries lagna.
        chart = _chart_with(asc_sign=1, placements={"Saturn": 1})
        result = detect_mks(chart, asc_sign=1)
        assert "Saturn" in result
        assert isinstance(result["Saturn"], Finding)

    def test_ketu_never_emits(self):
        """D-9 sentinel: Ketu is N/A. Even when in house 1, no Finding."""
        from app.reading.computations.marana_karaka_sthana import detect_mks

        # Try Ketu in every house — never emit.
        for house in range(1, 13):
            chart = _chart_with(asc_sign=1, placements={"Ketu": house})
            result = detect_mks(chart, asc_sign=1)
            assert "Ketu" not in result, (
                f"Ketu MKS finding emitted at house {house} — D-9 violation"
            )


# ---------------------------------------------------------------------------
# Canonical D-9 table — one test per planet.
# ---------------------------------------------------------------------------


class TestMksTablePin:

    @pytest.mark.parametrize(
        ("planet", "mks_house"),
        list(_EXPECTED_MKS_HOUSES.items()),
    )
    def test_planet_in_its_mks_house_fires(self, planet, mks_house):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        chart = _chart_with(asc_sign=1, placements={planet: mks_house})
        result = detect_mks(chart, asc_sign=1)
        assert planet in result, (
            f"{planet} in house {mks_house} (its MKS per D-9) did not emit"
        )

    @pytest.mark.parametrize(
        ("planet", "mks_house"),
        list(_EXPECTED_MKS_HOUSES.items()),
    )
    def test_planet_outside_mks_does_not_fire(self, planet, mks_house):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        # Place in house mks_house + 1 (or mks_house - 1 if at edge).
        other_house = (mks_house % 12) + 1
        chart = _chart_with(asc_sign=1, placements={planet: other_house})
        result = detect_mks(chart, asc_sign=1)
        assert planet not in result, (
            f"{planet} in house {other_house} (NOT its MKS={mks_house}) "
            f"falsely emitted"
        )


# ---------------------------------------------------------------------------
# Finding contract conformance.
# ---------------------------------------------------------------------------


class TestFindingContract:

    def _saturn_in_mks_chart(self) -> dict:
        return _chart_with(asc_sign=1, placements={"Saturn": 1})

    def test_id_grammar(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        assert result["Saturn"].id == "practitioner.mks.saturn"

    def test_classification_is_affliction(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        assert result["Saturn"].classification == "affliction"

    def test_direction_is_negative(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        assert result["Saturn"].direction == "negative"

    def test_verdict_under_140_chars(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        assert len(result["Saturn"].verdict) <= 140

    def test_verdict_mentions_mks(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        assert "MKS" in result["Saturn"].verdict

    def test_evidence_cites_d9(self):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        result = detect_mks(self._saturn_in_mks_chart(), asc_sign=1)
        evidence_blob = " ".join(result["Saturn"].evidence)
        assert "D-9" in evidence_blob


# ---------------------------------------------------------------------------
# Property: works across all lagnas (whole-sign invariance).
# ---------------------------------------------------------------------------


class TestPropertyAllLagnas:

    @pytest.mark.parametrize("asc_sign", list(range(1, 13)))
    def test_saturn_in_1st_house_fires_for_every_lagna(self, asc_sign):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        chart = _chart_with(asc_sign=asc_sign, placements={"Saturn": 1})
        result = detect_mks(chart, asc_sign=asc_sign)
        assert "Saturn" in result, (
            f"Saturn 1st-house MKS missed at asc_sign={asc_sign}"
        )

    @pytest.mark.parametrize("asc_sign", list(range(1, 13)))
    def test_sun_in_12th_house_fires_for_every_lagna(self, asc_sign):
        from app.reading.computations.marana_karaka_sthana import detect_mks

        chart = _chart_with(asc_sign=asc_sign, placements={"Sun": 12})
        result = detect_mks(chart, asc_sign=asc_sign)
        assert "Sun" in result, (
            f"Sun 12th-house MKS missed at asc_sign={asc_sign}"
        )
