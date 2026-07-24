"""Gochara Vedha (transit obstruction) — `primitives/transits.py`.

Pins the Vedha cancellation logic (pure, no swisseph): the paired obstruction house, the exempt
pairs (Sun↔Saturn, Moon↔Mercury), and the table-completeness invariant (every benefic Gochara
house has a Vedha pair). Plus a public-baseline integration smoke.
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import transits as tr


class TestVedhaLogic:
    def test_vedha_obstructs_when_paired_house_occupied(self) -> None:
        """The Sun's benefic transit in the 3rd (from Moon) is obstructed by a graha in the 9th."""
        vh, obstr = tr._vedha("Sun", 3, {"Sun": 3, "Mars": 9})
        assert vh == 9 and "Mars" in obstr

    def test_no_vedha_when_paired_house_empty(self) -> None:
        """No graha in the Vedha house → the benefic result stands."""
        vh, obstr = tr._vedha("Sun", 3, {"Sun": 3})
        assert vh == 9 and obstr == ()

    def test_sun_saturn_are_mutually_exempt(self) -> None:
        """Sun & Saturn cause no Vedha to each other (Raman's exception)."""
        _vh, obstr = tr._vedha("Sun", 3, {"Sun": 3, "Saturn": 9})
        assert obstr == ()

    def test_moon_mercury_are_mutually_exempt(self) -> None:
        """Moon & Mercury cause no Vedha to each other (Raman's exception)."""
        _vh, obstr = tr._vedha("Moon", 3, {"Moon": 3, "Mercury": 9})
        assert obstr == ()

    def test_vedha_table_covers_every_benefic_gochara_house(self) -> None:
        """Raman's Vedha table is complete: every benefic Gochara house has a Vedha pair."""
        for planet, good in tr._GOCHARA_GOOD.items():
            assert set(good) == set(tr._VEDHA[planet]), planet


class TestGocharaIntegration:
    def test_gochara_rows_carry_vedha_and_net_good(self) -> None:
        """gochara() on the public baseline returns rows with the Vedha fields wired."""
        natal = cast_chart(BirthData(name="b", year=1990, month=7, day=15, hour=12, minute=0,
                                     tz_offset=5.5, latitude=12.97, longitude=77.59),
                           ayanamsa="raman")
        rows = tr.gochara(natal, 2026, 7, 24)
        assert rows
        for r in rows:
            assert isinstance(r.net_good, bool)
            # net_good can only be True on a benefic house that is un-obstructed
            assert r.net_good == (r.gochara_good and not r.vedha_by)
            if not r.gochara_good:
                assert r.vedha_house is None and r.vedha_by == ()
