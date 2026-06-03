from __future__ import annotations

from app.raman_saab.primitives.shadbala import ishta_kashta as ik

# GBB Standard Horoscope: Ochcha (Sh) and Chesta (Sh, incl. Sun/Moon surrogates).
_OCHCHA = {"Sun": 3.6, "Moon": 32.9, "Mars": 37.2, "Mercury": 54.8, "Jupiter": 56.2, "Venus": 2.3, "Saturn": 34.9}
_CHESTA = {"Sun": 23.2, "Moon": 44.2, "Mars": 22.28, "Mercury": 2.13, "Jupiter": 35.33, "Venus": 5.76, "Saturn": 21.06}
_ISHTA  = {"Sun": 9.14, "Moon": 38.13, "Mars": 28.79, "Mercury": 10.83, "Jupiter": 44.56, "Venus": 3.63, "Saturn": 27.11}
_KASHTA = {"Sun": 45.54, "Moon": 20.66, "Mars": 29.32, "Mercury": 17.34, "Jupiter": 9.73, "Venus": 55.94, "Saturn": 31.26}


def test_ishta_kashta_fixture():
    """All 7 GBB Standard Horoscope Ishta/Kashta values match within 0.1 Sh."""
    for p in _OCHCHA:
        assert abs(ik.ishta_phala(_OCHCHA[p], _CHESTA[p]) - _ISHTA[p]) < 0.1, p
        assert abs(ik.kashta_phala(_OCHCHA[p], _CHESTA[p]) - _KASHTA[p]) < 0.1, p


def test_sun_moon_chesta_surrogates():
    """Sun: (Sayana 200.4 + 90) folded /3 = 23.2 ; Moon: (Moon 311.67 − Sun 179.13)/3 = 44.2"""
    assert abs(ik.sun_chesta_surrogate(200.4) - 23.2) < 0.2
    assert abs(ik.moon_chesta_surrogate(311.67, 179.13) - 44.18) < 0.2
