"""Pins against Krishnamurti's own worked chart and tables in KP Reader 5 (Transits)."""

from __future__ import annotations

from app.kp.chart import Birth, cast
from app.kp.significators import houses_signified, planet_significations
from app.kp.transit import read_transits, sensitive_points

#: Alibag 18°39'N 72°55'E, 9-00 P.M. I.S.T., Tuesday 23-12-1924 (KPR5 p.151).
ALIBAG = Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18 + 39 / 60, lon=72 + 55 / 60)

#: His significator table (KPR5 p.154).
PRINTED = {
    "Sun": {2, 7, 5}, "Moon": {4, 1, 5, 6, 9}, "Mars": {4, 8, 7, 5, 10},
    "Mercury": {11, 4, 5, 3, 12}, "Jupiter": {7, 5, 6, 9}, "Venus": {4, 11, 7, 8},
    "Saturn": {1, 4, 8, 7}, "Rahu": {3, 12, 5, 1, 4}, "Ketu": {8, 10, 5, 7, 4},
}


class TestAlibagChart:
    def test_cusps_match_print(self) -> None:
        """Cusps I-VI print as Cancer 18°22', Leo 15°01', Virgo 15°01', Libra 17°01', Scorpio 19°01', Sag 19°01'."""
        c = cast(ALIBAG)
        printed = [90 + 18 + 22 / 60, 120 + 15 + 1 / 60, 150 + 15 + 1 / 60,
                   180 + 17 + 1 / 60, 210 + 19 + 1 / 60, 240 + 19 + 1 / 60]
        for h, p in enumerate(printed, start=1):
            assert abs(c.cusp(h).longitude - p) < 0.3, h

    def test_every_planets_houses_match_his_table(self) -> None:
        """All nine planets signify exactly the houses Krishnamurti tabulates (ladder + R6a)."""
        c = cast(ALIBAG)
        sigs = planet_significations(c)
        for planet, houses in PRINTED.items():
            assert set(houses_signified(c, planet, sigs)) == houses, planet


class TestSensitivePoints:
    def test_mars_saturn_mercury_four_points(self) -> None:
        """KPR5 p.160: four points for Mars, Saturn, Mercury, at the printed degrees."""
        got = [(round(float(d.start) * 3600), round(float(d.end) * 3600))
               for d in sensitive_points(("Mars", "Saturn", "Mercury"))]
        deg = lambda d, m=0, s=0: d * 3600 + m * 60 + s  # noqa: E731
        assert got == [(deg(177, 53, 20), deg(180)), (deg(215, 26, 40), deg(217, 20)),
                       (deg(237, 53, 20), deg(240)), (deg(300), deg(301, 53, 20))]

    def test_mars_venus_venus_two_points(self) -> None:
        """Mars sign Venus star Venus sub 13°20'-15°33'20"; Venus sign Mars star Venus sub 182°40'-184°53'20"."""
        got = [(round(float(d.start), 4), round(float(d.end), 4)) for d in sensitive_points(("Mars", "Venus", "Venus"))]
        assert got == [(13.3333, 15.5556), (182.6667, 184.8889)]

    def test_mars_venus_sun_three_points(self) -> None:
        """Three points for Mars, Venus, Sun, as printed."""
        got = [round(float(d.start), 4) for d in sensitive_points(("Mars", "Venus", "Sun"))]
        assert got == [15.5556, 137.3333, 184.8889]


class TestTransitReading:
    def test_reading_uses_star_lord_planet_and_sub_lord(self) -> None:
        """what = star lord's houses, source = the planet's, whether = sub lord's (KPR5-SOURCE)."""
        c = cast(ALIBAG)
        sigs = planet_significations(c)
        for r in read_transits(c, c.jd_ut + 400):
            assert r.what_houses == houses_signified(c, r.star_lord, sigs)
            assert r.source_houses == houses_signified(c, r.planet, sigs)
            assert r.whether_houses == houses_signified(c, r.sub_lord, sigs)
