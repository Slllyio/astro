from __future__ import annotations
from app.raman_saab.primitives import varga_lords as v


def test_hora_lord():
    assert v.hora_lord_of(5.0) == "Sun"     # Aries 5° (odd sign, 1st half) -> Sun
    assert v.hora_lord_of(20.0) == "Moon"   # Aries 20° (odd sign, 2nd half) -> Moon
    assert v.hora_lord_of(35.0) == "Moon"   # Taurus 5° (even sign, 1st half) -> Moon
    assert v.hora_lord_of(50.0) == "Sun"    # Taurus 20° (even sign, 2nd half) -> Sun


def test_saptamsa_lord():
    assert v.saptamsa_lord_of(2.0) == "Mars"        # Aries 2° -> Aries -> Mars
    assert v.saptamsa_lord_of(32.0) == "Mars"       # Taurus 2° (even) -> Scorpio -> Mars


def test_dwadasamsa_lord():
    assert v.dwadasamsa_lord_of(2.0) == "Mars"      # Aries 2° -> Aries
    assert v.dwadasamsa_lord_of(6.0) == "Mercury"   # Aries 6° (part 2) -> Gemini -> Mercury


def test_thrimsamsa_lord():
    assert v.thrimsamsa_lord_of(3.0) == "Mars"      # Aries 3° (odd, 0-5) -> Mars
    assert v.thrimsamsa_lord_of(27.0) == "Venus"    # Aries 27° (odd, 25-30) -> Venus
    assert v.thrimsamsa_lord_of(33.0) == "Venus"    # Taurus 3° (even, 0-5) -> Venus
