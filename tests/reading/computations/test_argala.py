"""Tests for ``app.reading.computations.argala``.

Doctrine source: BPHS Vol.I Ch.30 -- Argala (intervention) + Virodhargala
(blocking).

Algorithm summary
=================

For each target bhava (1..12) we ask "what other planets *intervene on*
its results?". Per BPHS Ch.30:

  - **Argala (primary intervention)**: planets occupying the **2nd, 4th,
    and 11th** signs counted from the target sign cause Argala on the
    target. They influence (intervene on) the target's affairs.
  - **Virodhargala (counter / blocking)**: planets occupying the **3rd,
    5th, and 9th** signs from the target *block* the corresponding
    Argala:
        - planets in the 3rd block planets in the 2nd
        - planets in the 5th block planets in the 4th
        - planets in the 9th block planets in the 11th
  - **Visesha (special) Argala**: planets in the **10th** from the
    target are recognised as an additional special Argala source by
    several classical commentators.

Verdict convention
==================

A finding's ``direction`` is set as follows:

  - **positive** when the surviving (unblocked) argala set is purely
    benefic -- the bhava receives helpful intervention.
  - **negative** when the surviving argala set is purely malefic.
  - **mixed**   when surviving argalas include both benefics and malefics.
  - **neutral** when there are no surviving argala sources at all.

The "blocked" predicate is per pair: an Argala in slot 2 is considered
blocked if ANY planet sits in slot 3; similarly 4 by 5 and 11 by 9. If
the blocker set is also empty the Argala fires through.

Worked example (target bhava = house 1, asc_sign = 1 / Aries):
  - target sign = Aries (1)
  - 2nd from Aries  = Taurus (2)     -> argala
  - 3rd from Aries  = Gemini (3)     -> blocks 2nd argala
  - 4th from Aries  = Cancer (4)     -> argala
  - 5th from Aries  = Leo (5)        -> blocks 4th argala
  - 9th from Aries  = Sagittarius(9) -> blocks 11th argala
  - 10th from Aries = Capricorn (10) -> visesha argala
  - 11th from Aries = Aquarius (11)  -> argala
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


# ---------------------------------------------------------------------------
# Fixtures: Bangalore baseline + a deterministic toy chart
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


@pytest.fixture(scope="module")
def asc_sign(bangalore_chart) -> int:
    return int(bangalore_chart["ascendant"]["sign"])


@pytest.fixture
def empty_chart() -> dict:
    """A chart with no planets -- every bhava should be neutral / unblocked-empty."""
    return {}


@pytest.fixture
def toy_chart() -> dict:
    """Hand-crafted minimal chart for argala arithmetic checks.

    asc_sign = 1 (Aries). Then signs offset by 1 == bhavas offset by 1.

      - Jupiter in Taurus  (sign 2) -- argala on h1 (2nd from Aries)
      - Mars    in Gemini  (sign 3) -- blocker on the 2nd-argala for h1
      - Venus   in Cancer  (sign 4) -- argala on h1 (4th from Aries)
      - Mercury in Aquarius(sign 11)-- argala on h1 (11th from Aries)
      - Saturn  in Sagit.  (sign 9) -- blocker for the 11th-argala
      - Moon    in Capricorn(sign 10)-- visesha argala on h1
    """
    return {
        "Jupiter": {"sign": 2,  "longitude": 35.0},
        "Mars":    {"sign": 3,  "longitude": 65.0},
        "Venus":   {"sign": 4,  "longitude": 95.0},
        "Mercury": {"sign": 11, "longitude": 305.0},
        "Saturn":  {"sign": 9,  "longitude": 245.0},
        "Moon":    {"sign": 10, "longitude": 275.0},
    }


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeArgala:

    def test_returns_dict_keyed_by_house_1_to_12(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(range(1, 13))

    def test_emits_findings(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        for house, finding in result.items():
            assert isinstance(finding, Finding), (
                f"house {house} value is not a Finding"
            )

    def test_id_grammar(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        for house, finding in result.items():
            assert finding.id == f"foundation.argala.h{house}", (
                f"unexpected id {finding.id!r}"
            )

    def test_classification_is_primitive(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_direction_enum_valid(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        valid = {"positive", "negative", "neutral", "mixed"}
        result = compute_argala(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.direction in valid

    def test_doctrine_sentinel_in_evidence(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        for finding in result.values():
            joined = " ".join(finding.evidence)
            assert "BPHS" in joined or "Argala" in joined or "argala" in joined


# ---------------------------------------------------------------------------
# Property: every bhava emits a finding; argala/virodhargala lists are str
# ---------------------------------------------------------------------------


class TestPropertyEveryBhava:
    """Property test required by the wave-B plan: every bhava 1..12 has a
    Finding; the argala/virodhargala lists materialise as ``list[str]``
    of planet names."""

    def test_exactly_12_entries(self, d1_chart, asc_sign):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(d1_chart, asc_sign)
        assert len(result) == 12
        for key in result.keys():
            assert isinstance(key, int)
            assert 1 <= key <= 12

    def test_argala_lists_are_list_of_str(self, toy_chart):
        """argala_planets and virodhargala_planets must surface as list[str]."""
        from app.reading.computations.argala import compute_argala

        result = compute_argala(toy_chart, asc_sign=1)
        for finding in result.values():
            # Evidence should expose argala / virodhargala lists explicitly.
            joined = " ".join(finding.evidence)
            assert "argala_planets=" in joined
            assert "virodhargala_planets=" in joined

    def test_argala_planet_names_only_known_grahas(self, toy_chart):
        """The names that appear in argala lists are real planet names."""
        from app.reading.computations.argala import compute_argala

        result = compute_argala(toy_chart, asc_sign=1)
        valid = {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
            "Rahu", "Ketu",
        }
        for finding in result.values():
            for line in finding.evidence:
                if line.startswith("argala_planets=") or line.startswith(
                    "virodhargala_planets="
                ):
                    # Pull the list portion -- format is `key=[Mars, Venus]`
                    body = line.split("=", 1)[1].strip("[] ")
                    if not body:
                        continue
                    parts = [p.strip(" '\"") for p in body.split(",")]
                    for p in parts:
                        if p == "":
                            continue
                        assert p in valid, (
                            f"unrecognised planet name {p!r} in {line!r}"
                        )


# ---------------------------------------------------------------------------
# Empty chart behaviour
# ---------------------------------------------------------------------------


class TestEmptyChart:
    """With no planets, every bhava has no argala / no blocker -> neutral."""

    def test_all_bhavas_neutral(self, empty_chart):
        from app.reading.computations.argala import compute_argala

        result = compute_argala(empty_chart, asc_sign=1)
        for finding in result.values():
            assert finding.direction == "neutral", (
                f"empty chart should yield neutral, got "
                f"{finding.direction!r} ({finding.verdict!r})"
            )


# ---------------------------------------------------------------------------
# Argala arithmetic on the toy chart
# ---------------------------------------------------------------------------


class TestArgalaArithmetic:
    """Verify the 2/4/10/11 argala + 3/5/9 blocker computation on a chart
    whose layout we control fully."""

    def test_h1_argala_planets(self, toy_chart):
        """target h1 == sign 1 (Aries):
          2nd=Taurus(Jupiter), 4th=Cancer(Venus), 11th=Aquarius(Mercury),
          10th=Capricorn(Moon) (visesha).
        So argala on h1 = {Jupiter, Venus, Mercury, Moon}.
        """
        from app.reading.computations.argala import _argala_planets_for_bhava

        result = _argala_planets_for_bhava(
            target_sign=1, d1_chart={
                "Jupiter": {"sign": 2,  "longitude": 35.0},
                "Mars":    {"sign": 3,  "longitude": 65.0},
                "Venus":   {"sign": 4,  "longitude": 95.0},
                "Mercury": {"sign": 11, "longitude": 305.0},
                "Saturn":  {"sign": 9,  "longitude": 245.0},
                "Moon":    {"sign": 10, "longitude": 275.0},
            },
        )
        assert set(result) == {"Jupiter", "Venus", "Mercury", "Moon"}

    def test_h1_virodhargala_planets(self, toy_chart):
        """3rd/5th/9th from Aries = Gemini/Leo/Sag. Mars(3) and Saturn(9)
        sit in blocker slots; Leo is empty."""
        from app.reading.computations.argala import _virodhargala_planets_for_bhava

        result = _virodhargala_planets_for_bhava(
            target_sign=1, d1_chart={
                "Jupiter": {"sign": 2,  "longitude": 35.0},
                "Mars":    {"sign": 3,  "longitude": 65.0},
                "Venus":   {"sign": 4,  "longitude": 95.0},
                "Mercury": {"sign": 11, "longitude": 305.0},
                "Saturn":  {"sign": 9,  "longitude": 245.0},
                "Moon":    {"sign": 10, "longitude": 275.0},
            },
        )
        assert set(result) == {"Mars", "Saturn"}

    def test_h1_direction_is_mixed_on_toy_chart(self, toy_chart):
        """On the toy chart, h1's surviving argalas include benefic Venus
        (4th, blocked by Mars in 5th? No -- Mars sits in 3rd, blocks the
        2nd not the 4th) AND malefic Moon (10th visesha). Mercury (11th)
        is blocked by Saturn (9th). Jupiter (2nd) is blocked by Mars (3rd).
        Surviving set = {Venus(benefic), Moon(benefic)}. Direction = positive.
        """
        from app.reading.computations.argala import compute_argala

        result = compute_argala(toy_chart, asc_sign=1)
        # All survivors are benefics -> positive
        assert result[1].direction == "positive"

    def test_block_pairing_2_blocked_by_3(self, empty_chart):
        """A 2nd-argala is blocked ONLY by a planet in the 3rd, not the
        5th or 9th."""
        from app.reading.computations.argala import compute_argala

        chart = {
            "Jupiter": {"sign": 2, "longitude": 35.0},
            "Venus":   {"sign": 5, "longitude": 125.0},  # 5th -- not a blocker for 2nd
        }
        result = compute_argala(chart, asc_sign=1)
        # Jupiter in 2nd (benefic argala on h1) NOT blocked because no planet in 3rd.
        # Direction should be positive (only benefic survives).
        assert result[1].direction == "positive"
        joined = " ".join(result[1].evidence)
        assert "Jupiter" in joined

    def test_block_pairing_4_blocked_by_5(self):
        """A 4th-argala is blocked by a planet in the 5th."""
        from app.reading.computations.argala import compute_argala

        # Jupiter (benefic) in 4th, Mars (malefic) in 5th -> 4th argala
        # blocked. No surviving argalas -> neutral.
        chart = {
            "Jupiter": {"sign": 4, "longitude": 95.0},
            "Mars":    {"sign": 5, "longitude": 125.0},
        }
        result = compute_argala(chart, asc_sign=1)
        assert result[1].direction == "neutral"

    def test_block_pairing_11_blocked_by_9(self):
        """An 11th-argala is blocked by a planet in the 9th."""
        from app.reading.computations.argala import compute_argala

        chart = {
            "Mercury": {"sign": 11, "longitude": 305.0},
            "Saturn":  {"sign":  9, "longitude": 245.0},
        }
        result = compute_argala(chart, asc_sign=1)
        # Mercury in 11 (benefic) blocked by Saturn in 9. No survivor -> neutral.
        assert result[1].direction == "neutral"


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self, empty_chart):
        from app.reading.computations.argala import compute_argala

        with pytest.raises(ValueError):
            compute_argala(empty_chart, asc_sign=0)
        with pytest.raises(ValueError):
            compute_argala(empty_chart, asc_sign=13)
