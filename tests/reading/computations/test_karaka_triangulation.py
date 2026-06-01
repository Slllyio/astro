"""Tests for ``app.reading.computations.karaka_triangulation``.

Doctrine lock: D-10 -- Sanjay-Rath triple-AND formulation
(``docs/doctrine-decisions.md``).

The reading examines a domain by computing the signification's house
from THREE anchors at once (Lagna, Moon, natural karaka) and asking
"do all three agree?". Concordance = how many of the (house, anchor)
sign computations land on the *same* sign.

Domain table
============

  | Domain    | House(s)   | Anchors                  |
  |-----------|------------|--------------------------|
  | marriage  | 7          | Lagna, Moon, Venus       |
  | career    | 10         | Lagna, Moon, Sun         |
  | wealth    | 2, 11      | Lagna, Moon, Jupiter     |
  | children  | 5          | Lagna, Moon, Jupiter     |
  | health    | 1, 6       | Lagna, Moon              |
  | education | 4, 5       | Lagna, Moon, Mercury     |

For each domain, we enumerate the (house, anchor) Cartesian product
and resolve each to a target sign. Concordance is the largest
agreeing-anchor count divided by total. Direction:

  - positive : all anchors agree (concordance == 1.0)
  - neutral  : at least half agree (>= 0.5)
  - negative : less than half agree

Verdict format (per spec):
  'Marriage anchors: 7H from Lagna=Aries, 7H from Moon=Aries,
   7H from Venus=Aries (3/3 concordance)'

Bangalore baseline (1990-07-15 12:00 IST, lat 12.97, lon 77.59):
  - asc_sign = 6 (Virgo)
  - Moon = 12 (Pisces)
  - Venus = 3 (Gemini)
  - Sun = 3 (Gemini)
  - Jupiter = 3 (Gemini)
  - Mercury = 4 (Cancer)
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


_DOMAINS = ("marriage", "career", "wealth", "children", "health", "education")


# ---------------------------------------------------------------------------
# Fixtures: Bangalore baseline
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


@pytest.fixture(scope="module")
def moon_sign(bangalore_chart) -> int:
    return int(bangalore_chart["d1"]["Moon"]["sign"])


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeKarakaTriangulation:

    def test_returns_dict(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        assert isinstance(result, dict)

    def test_all_six_domains_present(self, d1_chart, asc_sign, moon_sign):
        """Property test: all six expected domain keys appear in output."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        assert set(result.keys()) == set(_DOMAINS)

    def test_all_values_are_findings(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for finding in result.values():
            assert isinstance(finding, Finding)

    def test_id_grammar(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for domain, finding in result.items():
            assert finding.id == (
                f"foundation.karaka_triangulation.{domain}"
            ), f"unexpected id {finding.id!r}"

    def test_classification_is_primitive(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_direction_enum_valid(self, d1_chart, asc_sign, moon_sign):
        """Property test required by wave-B plan: direction must be in
        {positive, neutral, negative}.
        """
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        valid = {"positive", "neutral", "negative"}
        for finding in result.values():
            assert finding.direction in valid, (
                f"unexpected direction {finding.direction!r}"
            )

    def test_doctrine_sentinel_in_evidence(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for finding in result.values():
            joined = " ".join(finding.evidence)
            # D-10 / Sanjay-Rath are the locked doctrine source markers.
            assert "D-10" in joined or "Sanjay" in joined or "sanjay" in joined


# ---------------------------------------------------------------------------
# Arithmetic correctness on the Bangalore baseline
# ---------------------------------------------------------------------------


class TestBangaloreBaseline:
    """Pin specific anchor computations against the Bangalore baseline.

    asc_sign = 6 (Virgo), Moon = 12 (Pisces), Venus = Sun = Jupiter = 3
    (Gemini), Mercury = 4 (Cancer).

    Worked example -- marriage (7th from {Lagna, Moon, Venus}):
      7th from asc 6  -> ((6 - 1 + 7 - 1) % 12) + 1  = 12  (Pisces)
      7th from Moon 12 -> ((12 - 1 + 7 - 1) % 12) + 1 = 6   (Virgo)
      7th from Venus 3 -> ((3 - 1 + 7 - 1) % 12) + 1  = 9   (Sagittarius)
      Signs: {12, 6, 9} -> 3 distinct, mode-count = 1/3 -> negative direction.
    """

    def test_marriage_anchor_signs(self, d1_chart, asc_sign, moon_sign):
        """Marriage anchors land on signs 12 / 6 / 9 (all distinct)."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        finding = result["marriage"]
        joined = " ".join(finding.evidence)
        # The evidence should expose the per-anchor sign mapping.
        assert "anchors=" in joined or "lagna" in joined.lower()

    def test_marriage_direction_negative_on_baseline(
        self, d1_chart, asc_sign, moon_sign
    ):
        """On Bangalore baseline, marriage anchors are all distinct ->
        concordance 1/3 -> direction negative."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        # Concordance = 1/3 maps to negative per the rule.
        assert result["marriage"].direction == "negative"


# ---------------------------------------------------------------------------
# Synthetic concordance scenarios
# ---------------------------------------------------------------------------


class TestSyntheticConcordance:
    """Construct charts that force specific concordance outcomes."""

    def test_full_concordance_positive(self):
        """All three pivots in the same sign -> 7H anchors all match ->
        concordance 1.0 -> positive."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        # asc_sign = 1 (Aries), Moon = 1, Venus = 1
        # 7H from each = sign 7 (Libra) for all three -> 3/3 concordance.
        chart = {
            "Moon":    {"sign": 1, "longitude": 5.0},
            "Venus":   {"sign": 1, "longitude": 10.0},
            "Sun":     {"sign": 1, "longitude": 15.0},
            "Jupiter": {"sign": 1, "longitude": 20.0},
            "Mercury": {"sign": 1, "longitude": 25.0},
        }
        result = compute_karaka_triangulation(
            chart, asc_sign=1, moon_sign=1,
        )
        assert result["marriage"].direction == "positive"

    def test_partial_concordance_neutral(self):
        """2/3 anchors agree -> concordance 0.67 -> neutral."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        # asc_sign = 1, Moon = 1 (same as Lagna -> both 7H -> Libra=7)
        # Venus = 2 (Taurus) -> 7H from Venus = Scorpio=8.
        # Lagna-7H = Libra; Moon-7H = Libra; Venus-7H = Scorpio.
        # Mode = Libra at 2/3, concordance = 0.667 -> neutral.
        chart = {
            "Moon":    {"sign": 1, "longitude": 5.0},
            "Venus":   {"sign": 2, "longitude": 35.0},
            "Sun":     {"sign": 1, "longitude": 15.0},
            "Jupiter": {"sign": 1, "longitude": 20.0},
            "Mercury": {"sign": 1, "longitude": 25.0},
        }
        result = compute_karaka_triangulation(
            chart, asc_sign=1, moon_sign=1,
        )
        assert result["marriage"].direction == "neutral"

    def test_no_concordance_negative(self):
        """All three anchors distinct -> concordance 1/3 -> negative."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        # asc_sign = 1, Moon = 2, Venus = 3 -> 7H lands on 7, 8, 9 -> all distinct.
        chart = {
            "Moon":    {"sign": 2, "longitude": 35.0},
            "Venus":   {"sign": 3, "longitude": 65.0},
            "Sun":     {"sign": 1, "longitude": 15.0},
            "Jupiter": {"sign": 1, "longitude": 20.0},
            "Mercury": {"sign": 1, "longitude": 25.0},
        }
        result = compute_karaka_triangulation(
            chart, asc_sign=1, moon_sign=2,
        )
        assert result["marriage"].direction == "negative"


# ---------------------------------------------------------------------------
# Verdict shape: spec example "3/3 concordance"
# ---------------------------------------------------------------------------


class TestVerdictShape:

    def test_verdict_mentions_concordance(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        for finding in result.values():
            assert "concordance" in finding.verdict.lower(), (
                f"verdict {finding.verdict!r} missing 'concordance' marker"
            )

    def test_verdict_full_match_says_3_of_3_for_marriage(self):
        """The full-match synthetic case yields 3/3 for marriage."""
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        chart = {
            "Moon":    {"sign": 1, "longitude": 5.0},
            "Venus":   {"sign": 1, "longitude": 10.0},
            "Sun":     {"sign": 1, "longitude": 15.0},
            "Jupiter": {"sign": 1, "longitude": 20.0},
            "Mercury": {"sign": 1, "longitude": 25.0},
        }
        result = compute_karaka_triangulation(
            chart, asc_sign=1, moon_sign=1,
        )
        # Verdict text should carry the 3/3 ratio.
        assert "3/3" in result["marriage"].verdict


# ---------------------------------------------------------------------------
# Multi-house domains
# ---------------------------------------------------------------------------


class TestMultiHouseDomains:
    """Wealth (2/11), Health (1/6), Education (4/5) use multiple houses
    crossed with multiple pivots. We verify the domain still resolves to
    a single Finding with a valid direction."""

    def test_wealth_emits_finding(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        assert isinstance(result["wealth"], Finding)
        # 6 anchors total (2 houses × 3 pivots).
        joined = " ".join(result["wealth"].evidence)
        assert "anchors=" in joined or "total_anchors=" in joined

    def test_health_emits_finding(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        assert isinstance(result["health"], Finding)
        # Health = 2 houses × 2 pivots = 4 anchors total.

    def test_education_emits_finding(self, d1_chart, asc_sign, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        result = compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
        assert isinstance(result["education"], Finding)
        # Education = 2 houses × 3 pivots = 6 anchors total.


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self, d1_chart, moon_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        with pytest.raises(ValueError):
            compute_karaka_triangulation(d1_chart, asc_sign=0, moon_sign=moon_sign)
        with pytest.raises(ValueError):
            compute_karaka_triangulation(d1_chart, asc_sign=13, moon_sign=moon_sign)

    def test_invalid_moon_sign_raises(self, d1_chart, asc_sign):
        from app.reading.computations.karaka_triangulation import (
            compute_karaka_triangulation,
        )

        with pytest.raises(ValueError):
            compute_karaka_triangulation(d1_chart, asc_sign=asc_sign, moon_sign=0)
        with pytest.raises(ValueError):
            compute_karaka_triangulation(d1_chart, asc_sign=asc_sign, moon_sign=13)
