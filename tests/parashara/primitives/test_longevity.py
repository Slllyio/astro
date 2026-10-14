"""Nisargayu — natural longevity (BPHS ch.43 sl.16-17 + ch.3 sl.49-50).

Load-bearing: the seven allotments sum to exactly 120 (the canonical full lifespan), and the scale
runs 1.0 at deep exaltation to 0.5 at deep debilitation — both Parashara's own numbers, not chosen.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import longevity as L


class TestAllotments:
    def test_the_seven_allotments_sum_to_120(self):
        """BPHS-43:551 — 1+2+9+20+18+20+50 = 120, the full human lifespan."""
        assert sum(L.NISARGAYU_YEARS.values()) == 120 == L.FULL_SPAN

    def test_allotments_are_the_sloka_verbatim(self):
        """'1, 2, 9, 20, 18, 20 and 50 ... to the Moon, Mars, Mercury, Venus, Jupiter, the Sun and
        Saturn' — in the sloka's own (non-Sun-first) order."""
        assert [L.NISARGAYU_YEARS[p] for p in
                ("Moon", "Mars", "Mercury", "Venus", "Jupiter", "Sun", "Saturn")] == \
            [1, 2, 9, 20, 18, 20, 50]

    def test_nodes_have_no_allotment(self):
        assert "Rahu" not in L.NISARGAYU_YEARS and "Ketu" not in L.NISARGAYU_YEARS


class TestExaltationPoints:
    def test_deep_exaltation_points(self):
        """ch.3 sl.49-50 — signs Aries/Taurus/Capricorn/Virgo/Cancer/Pisces/Libra at degrees
        10/3/28/15/5/27/20."""
        assert L.deep_exaltation_point("Sun") == 10.0        # Aries 10
        assert L.deep_exaltation_point("Moon") == 33.0       # Taurus 3
        assert L.deep_exaltation_point("Mars") == 298.0      # Capricorn 28
        assert L.deep_exaltation_point("Saturn") == 200.0    # Libra 20
        assert L.deep_exaltation_point("Venus") == 357.0     # Pisces 27


class TestScaling:
    def test_full_at_deep_exaltation(self):
        for p in L.NISARGAYU_YEARS:
            assert L.exaltation_scale(p, L.deep_exaltation_point(p)) == pytest.approx(1.0), p

    def test_half_at_deep_debilitation(self):
        """Debilitation is 180 deg from exaltation (7th sign, same degree) -> scale 0.5."""
        for p in L.NISARGAYU_YEARS:
            debil = (L.deep_exaltation_point(p) + 180.0) % 360.0
            assert L.exaltation_scale(p, debil) == pytest.approx(0.5), p

    def test_ninety_degrees_is_three_quarters(self):
        """Linear: a quarter-circle from exaltation is halfway between full and half = 0.75."""
        exalt = L.deep_exaltation_point("Sun")
        assert L.exaltation_scale("Sun", (exalt + 90) % 360) == pytest.approx(0.75)

    def test_scale_is_symmetric_around_the_exaltation(self):
        exalt = L.deep_exaltation_point("Jupiter")
        assert L.exaltation_scale("Jupiter", (exalt + 40) % 360) == \
            pytest.approx(L.exaltation_scale("Jupiter", (exalt - 40) % 360))


class TestContributionAndSpan:
    def test_contribution_is_full_times_scale(self):
        c = L.contribution("Saturn", L.deep_exaltation_point("Saturn"))
        assert c.full_years == 50 and c.scale == pytest.approx(1.0)
        assert c.years == pytest.approx(50.0)

    def test_all_planets_deeply_exalted_gives_the_full_120(self):
        lons = {p: L.deep_exaltation_point(p) for p in L.NISARGAYU_YEARS}
        span = L.nisargayu_span(lons)
        assert span.natural_years == pytest.approx(120.0)

    def test_all_planets_deeply_debilitated_gives_half(self):
        lons = {p: (L.deep_exaltation_point(p) + 180) % 360 for p in L.NISARGAYU_YEARS}
        assert L.nisargayu_span(lons).natural_years == pytest.approx(60.0)

    def test_span_flags_reductions_not_applied(self):
        """The pre-reduction figure must never masquerade as the final longevity."""
        span = L.nisargayu_span({p: 0.0 for p in L.NISARGAYU_YEARS})
        assert span.reductions_applied is False

    def test_nodes_rejected(self):
        with pytest.raises(ValueError):
            L.contribution("Rahu", 100.0)


class TestCitations:
    def test_sources_resolve(self):
        assert verify(L.YEARS_SOURCE) and verify(L.EXALT_SOURCE)

    def test_citations_point_at_the_right_slokas(self):
        assert "Nisargayu" in passage("BPHS-43:551")["text"] or \
               "NISARGA" in passage("BPHS-43:551")["text"].upper()
        assert "exalt" in passage("BPHS-3:894")["text"].lower()
