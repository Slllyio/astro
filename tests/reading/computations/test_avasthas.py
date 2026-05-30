"""Tests for ``app.reading.computations.avasthas``.

Deeptadi 9-state classification per planet — distinct from the
Baladi (degree-based) and Jagradadi (drishti-based) states already
covered by ``app.core.avastha``. The 9 Deeptadi states are:

| # | State        | Trigger                                                 |
|---|--------------|---------------------------------------------------------|
| 1 | Deepta       | Planet in its exaltation sign.                          |
| 2 | Susvastha    | Planet in its own sign (sva-rashi).                     |
| 3 | Pramudita    | Planet in a friend's sign.                              |
| 4 | Shanta       | Planet in its Moolatrikona range.                       |
| 5 | Dukhita      | Planet in an enemy's sign.                              |
| 6 | Sudukhita    | Planet in its debilitation sign.                        |
| 7 | Kshobita     | Planet within 1° of another non-luminary (Graha Yuddha).|
| 8 | Atra         | Planet combust by the Sun.                              |
| 9 | Khala        | Planet afflicted by a malefic aspect.                   |

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59) is used as the
canonical fixture.
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
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


# ---------------------------------------------------------------------------
# Construction / shape
# ---------------------------------------------------------------------------


_NINE_STATES = frozenset({
    "Deepta", "Susvastha", "Pramudita", "Shanta",
    "Dukhita", "Sudukhita", "Kshobita", "Atra", "Khala",
})


class TestComputeDeeptadiAvasthas:

    def test_returns_mapping_per_planet(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1_chart)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(d1_chart.keys())

    def test_emits_findings(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )
        from app.reading.schema import Finding

        result = compute_deeptadi_avasthas(d1_chart)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), f"{planet} is not a Finding"

    def test_id_grammar(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1_chart)
        for planet, finding in result.items():
            assert finding.id == f"primitive.avasthas.{planet.lower()}"

    def test_classification_is_primitive(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1_chart)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1_chart)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_state_is_one_of_nine(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1_chart)
        for planet, finding in result.items():
            state = _parse_state(finding)
            assert state in _NINE_STATES, (
                f"{planet} has invalid state {state!r}"
            )

    def test_direction_matches_state_polarity(self, d1_chart):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        positive_states = {"Deepta", "Susvastha", "Pramudita", "Shanta"}
        negative_states = {
            "Dukhita", "Sudukhita", "Kshobita", "Atra", "Khala",
        }
        result = compute_deeptadi_avasthas(d1_chart)
        for planet, finding in result.items():
            state = _parse_state(finding)
            if state in positive_states:
                assert finding.direction == "positive", (
                    f"{planet} in {state} expected positive direction, "
                    f"got {finding.direction}"
                )
            elif state in negative_states:
                assert finding.direction == "negative", (
                    f"{planet} in {state} expected negative direction, "
                    f"got {finding.direction}"
                )


class TestStateAssignment:
    """Hand-crafted chart vectors for each of the 9 states."""

    # 1=Aries .. 12=Pisces.

    def test_exalted_jupiter_is_deepta(self):
        """Jupiter exalted in Cancer (sign 4)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Jupiter"] = {
            "longitude": 95.0, "degree_in_sign": 5.0,
            "sign": 4, "sign_name": "Cancer", "is_retrograde": False,
        }
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Jupiter"]) == "Deepta"

    def test_own_sign_sun_is_susvastha(self):
        """Sun in Leo OUTSIDE Moolatrikona range -> Susvastha.

        Sun's Moolatrikona range is 120-140° (Leo 0-20°). A Sun at
        Leo 25° (longitude 145°) is in own-sign but NOT Moolatrikona,
        which yields plain Susvastha rather than the higher-tier Shanta.
        """
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 145.0, "degree_in_sign": 25.0,
            "sign": 5, "sign_name": "Leo", "is_retrograde": False,
        }
        # Move Moon and Mercury away from the Sun to avoid combustion.
        chart["Moon"] = {**chart["Moon"], "longitude": 30.0, "sign": 2}
        chart["Mercury"] = {**chart["Mercury"], "longitude": 200.0, "sign": 7}
        chart["Venus"] = {**chart["Venus"], "longitude": 250.0, "sign": 9}
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Sun"]) == "Susvastha"

    def test_debilitated_sun_is_sudukhita(self):
        """Sun in Libra (sign 7, debilitation)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 190.0, "degree_in_sign": 10.0,
            "sign": 7, "sign_name": "Libra", "is_retrograde": False,
        }
        # Spread out other planets so the Sun itself isn't affected by
        # combustion from a neighbour.
        chart["Moon"] = {**chart["Moon"], "longitude": 30.0, "sign": 2}
        chart["Mercury"] = {**chart["Mercury"], "longitude": 30.0, "sign": 2}
        chart["Venus"] = {**chart["Venus"], "longitude": 30.0, "sign": 2}
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Sun"]) == "Sudukhita"

    def test_moolatrikona_sun_is_shanta(self):
        """Sun at 10° Leo — within its Moolatrikona range (120-140°)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 130.0, "degree_in_sign": 10.0,
            "sign": 5, "sign_name": "Leo", "is_retrograde": False,
        }
        chart["Moon"] = {**chart["Moon"], "longitude": 30.0, "sign": 2}
        chart["Mercury"] = {**chart["Mercury"], "longitude": 200.0, "sign": 7}
        chart["Venus"] = {**chart["Venus"], "longitude": 250.0, "sign": 9}
        result = compute_deeptadi_avasthas(chart)
        # Moolatrikona Shanta is HIGHER priority than own Susvastha in our
        # ordering (priority: Deepta > Shanta > Susvastha > Pramudita > ...).
        assert _parse_state(result["Sun"]) == "Shanta"

    def test_friend_sign_is_pramudita(self):
        """Sun in Sagittarius (Jupiter's sign — friend)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 250.0, "degree_in_sign": 10.0,
            "sign": 9, "sign_name": "Sagittarius", "is_retrograde": False,
        }
        chart["Moon"] = {**chart["Moon"], "longitude": 30.0, "sign": 2}
        chart["Mercury"] = {**chart["Mercury"], "longitude": 30.0, "sign": 2}
        chart["Venus"] = {**chart["Venus"], "longitude": 60.0, "sign": 3}
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Sun"]) == "Pramudita"

    def test_enemy_sign_is_dukhita(self):
        """Sun in Taurus (Venus's sign — enemy)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 40.0, "degree_in_sign": 10.0,
            "sign": 2, "sign_name": "Taurus", "is_retrograde": False,
        }
        chart["Moon"] = {**chart["Moon"], "longitude": 180.0, "sign": 7}
        chart["Mercury"] = {**chart["Mercury"], "longitude": 180.0, "sign": 7}
        chart["Venus"] = {**chart["Venus"], "longitude": 200.0, "sign": 7}
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Sun"]) == "Dukhita"

    def test_combust_planet_is_atra(self):
        """Mercury at 0.5° from Sun (well within 14° combustion orb)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {
            "longitude": 100.0, "degree_in_sign": 10.0,
            "sign": 4, "sign_name": "Cancer", "is_retrograde": False,
        }
        chart["Mercury"] = {
            "longitude": 100.5, "degree_in_sign": 10.5,
            "sign": 4, "sign_name": "Cancer", "is_retrograde": False,
        }
        # Push other planets far away to avoid planetary war.
        chart["Venus"] = {**chart["Venus"], "longitude": 200.0, "sign": 7}
        result = compute_deeptadi_avasthas(chart)
        # Mercury is combust -> Atra (combust beats sign-based state).
        # NOTE: It's also a friend of the Sun, but Atra takes priority.
        assert _parse_state(result["Mercury"]) == "Atra"

    def test_planetary_war_is_kshobita(self):
        """Mars at 0.3° from Jupiter -> Kshobita (Graha Yuddha)."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        chart = _baseline_chart()
        chart["Sun"] = {**chart["Sun"], "longitude": 0.0, "sign": 1}
        chart["Mars"] = {
            "longitude": 200.0, "degree_in_sign": 20.0,
            "sign": 7, "sign_name": "Libra", "is_retrograde": False,
        }
        chart["Jupiter"] = {
            "longitude": 200.3, "degree_in_sign": 20.3,
            "sign": 7, "sign_name": "Libra", "is_retrograde": False,
        }
        result = compute_deeptadi_avasthas(chart)
        assert _parse_state(result["Mars"]) == "Kshobita"
        assert _parse_state(result["Jupiter"]) == "Kshobita"


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@st.composite
def _synthetic_d1(draw):
    out = {}
    for name in _PLANET_NAMES:
        lon = draw(st.floats(min_value=0.0, max_value=359.999))
        sign = int(lon // 30) + 1
        out[name] = {
            "longitude": lon,
            "degree_in_sign": lon % 30,
            "sign": sign,
            "sign_name": _SIGN_NAMES[sign - 1],
            "is_retrograde": False,
        }
    return out


_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


class TestPropertyInvariants:

    @given(d1=_synthetic_d1())
    def test_state_in_nine_enum(self, d1):
        """For arbitrary input, the state is always one of the 9 enum values."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1)
        for finding in result.values():
            state = _parse_state(finding)
            assert state in _NINE_STATES, (
                f"invalid state {state!r}"
            )

    @given(d1=_synthetic_d1())
    def test_ids_unique(self, d1):
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1)
        ids = [f.id for f in result.values()]
        assert len(ids) == len(set(ids))

    @given(d1=_synthetic_d1())
    def test_direction_never_neutral_or_mixed(self, d1):
        """Deeptadi states partition into positive vs negative; no neutral."""
        from app.reading.computations.avasthas import (
            compute_deeptadi_avasthas,
        )

        result = compute_deeptadi_avasthas(d1)
        for finding in result.values():
            assert finding.direction in {"positive", "negative"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_state(finding) -> str:
    """Extract the ``state=`` value from a Finding's evidence."""
    for line in finding.evidence:
        if line.startswith("state="):
            return line.split("=", 1)[1]
    raise AssertionError(
        f"finding {finding.id!r} missing 'state=' evidence line"
    )


def _baseline_chart() -> dict:
    """Construct a sparse-but-complete D1 chart for hand-crafted state tests.

    Each entry carries the minimum fields the implementation reads:
    ``longitude``, ``degree_in_sign``, ``sign`` (1..12), ``sign_name``,
    ``is_retrograde``.
    """
    base = {
        "Sun":     (0.0,  1),
        "Moon":    (30.0, 2),
        "Mars":    (60.0, 3),
        "Mercury": (90.0, 4),
        "Jupiter": (120.0, 5),
        "Venus":   (150.0, 6),
        "Saturn":  (180.0, 7),
        "Rahu":    (210.0, 8),
        "Ketu":    (30.0, 2),
    }
    return {
        name: {
            "longitude": lon,
            "degree_in_sign": lon % 30,
            "sign": sign,
            "sign_name": _SIGN_NAMES[sign - 1],
            "is_retrograde": False,
        }
        for name, (lon, sign) in base.items()
    }
