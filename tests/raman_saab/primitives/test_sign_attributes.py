from __future__ import annotations
from app.raman_saab.primitives import sign_attributes as s


def test_element_modality_parity():
    assert s.element(1) == "fire" and s.element(4) == "water"      # Aries fire, Cancer water
    assert s.modality(1) == "movable" and s.modality(2) == "fixed" and s.modality(3) == "common"
    assert s.parity(1) == "odd" and s.parity(2) == "even"


def test_sign_gender_matches_parity():
    assert s.sign_gender(1) == "masculine" and s.sign_gender(2) == "feminine"


def test_planet_gender_and_keeta():
    assert s.planet_gender("Jupiter") == "masculine"
    assert s.planet_gender("Venus") == "feminine"
    assert s.planet_gender("Mercury") == "neuter"
    assert s.is_keeta(8) is True and s.is_keeta(1) is False       # Scorpio is keeta


def test_rise_type():
    assert s.rise_type(1) == "prushtodaya"     # Aries
    assert s.rise_type(3) == "seershodaya"     # Gemini
    assert s.rise_type(12) == "ubhayodaya"     # Pisces


def test_is_sushka():
    assert s.is_sushka("Sun") is True and s.is_sushka("Mars") is True
    assert s.is_sushka("Jupiter") is False
