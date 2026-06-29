"""Jaimini Karakamsa reading (Jaimini Sutras 1.2 Su.14-22) — additive, parallel to the Parashari
verdicts. The Karakamsa is the Atmakaraka's navamsa sign; a planet occupying it (navamsa-conjunct
the AK) colours the soul's profession/inclination."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import jaimini_reading as jr
from app.raman_saab.primitives.special_points import atmakaraka

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_karakamsa_sign_is_the_ak_navamsa():
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    assert jr.karakamsa_sign(ch) == ch.planets[atmakaraka(ch)].navamsa_sign


def test_ak_occupies_its_own_karakamsa_and_all_indications_cited():
    """The Atmakaraka occupies the Karakamsa by definition; every indication cites the sutra."""
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    inds = dict(jr.karakamsa_indications(ch))
    assert atmakaraka(ch) in inds                       # Mainpuri AK=Sun -> in its own Karakamsa
    assert all("JS 1.2" in v for v in inds.values())


def test_table_covers_all_nine_grahas_including_nodes():
    """Rahu/Ketu CAN occupy the Karakamsa (Su.21-22) even though they can never BE the AK."""
    assert set(jr._ORDER) == set(jr._KARAKAMSA_PROFESSION)
    assert {"Rahu", "Ketu"} <= set(jr._KARAKAMSA_PROFESSION)


def test_indication_planets_actually_occupy_the_karakamsa():
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    ks = jr.karakamsa_sign(ch)
    for planet, _ in jr.karakamsa_indications(ch):
        assert ch.planets[planet].navamsa_sign == ks
