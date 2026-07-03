"""Vectorized gochara (transit) death-trigger indicators — Leg 2.

The pre-registered, frozen trigger menu (RUN3_PREREG.md pins T1–T4):

- **T1 Sade Sati** — transit Saturn in 12th/1st/2nd from the natal Moon sign.
  Semantics identical to ``gochara_engine._check_sade_sati``. ⚑ Saturn on the
  janma-rashi axis as the classical hardship/mortality window.
- **T2 Saturn in natal 8H** — transit Saturn occupying the 8th whole-sign
  house from the lagna. ⚑ Saturn (ayushkaraka) transiting the ayus-sthana.
- **T3 Jupiter–Saturn double transit on 8H** — Saturn touches the 8th bhava
  (occupies, or casts its 3/7/10 graha drishti onto it) AND Jupiter touches it
  (occupies, or casts 5/7/9). Same semantics as ``compute_gochara``'s
  ``is_double_transit_bhava`` restricted to bhava 8 (BPHS Ch.31 activation);
  the parity test in ``tests/test_gochara_death.py`` pins this equivalence.
- **T4 no protective Jupiter** — transit Jupiter absent from all kendras
  (1/4/7/10) from the natal Moon. Base rate ~2/3, so it is an **aggravator
  only** (secondary conjunction row), never part of the primary OR.

Primary Leg-2 indicator: ``I2 = T1 | T2 | T3``.

All functions take transit *sign* arrays (from ``transit_table.sign_at``) and
natal ``asc_sign`` / ``moon_sign`` scalars, and return boolean arrays — pure
numpy, no ephemeris calls in the hot loop.

House convention: whole-sign; ``house_of(sign) = ((sign - asc) % 12) + 1``.
Drishti: special aspects counted house-to-house from the planet's occupied
house (Saturn 3/7/10, Jupiter 5/7/9), matching ``drishti_argala``/gochara.
"""
from __future__ import annotations

from typing import Final

import numpy as np

_SATURN_DRISHTI: Final = (3, 7, 10)
_JUPITER_DRISHTI: Final = (5, 7, 9)
_KENDRA: Final = (1, 4, 7, 10)


def _house_from(ref_sign: int, sign_arr: np.ndarray) -> np.ndarray:
    """Whole-sign house (1..12) of each sign in ``sign_arr`` from ref_sign."""
    return ((sign_arr - ref_sign) % 12) + 1


def _touches(house_arr: np.ndarray, target_house: int,
             drishti: tuple[int, ...]) -> np.ndarray:
    """Planet in house_arr occupies target_house or aspects it via drishti.

    A planet in house h casts a drishti of length d onto house
    ((h - 1 + d - 1) % 12) + 1 (counting inclusively, so d=7 is opposition).
    """
    hit = house_arr == target_house
    for d in drishti:
        hit = hit | ((((house_arr - 1) + (d - 1)) % 12) + 1 == target_house)
    return hit


def t1_sade_sati(sat_sign: np.ndarray, moon_sign: int) -> np.ndarray:
    """Transit Saturn in 12/1/2 from natal Moon."""
    h = _house_from(moon_sign, sat_sign)
    return (h == 12) | (h == 1) | (h == 2)


def t2_saturn_in_8h(sat_sign: np.ndarray, asc_sign: int) -> np.ndarray:
    """Transit Saturn occupying the natal 8th house."""
    return _house_from(asc_sign, sat_sign) == 8


def t3_double_transit_8h(sat_sign: np.ndarray, jup_sign: np.ndarray,
                         asc_sign: int) -> np.ndarray:
    """Saturn AND Jupiter each occupy-or-aspect the natal 8th house."""
    sat_h = _house_from(asc_sign, sat_sign)
    jup_h = _house_from(asc_sign, jup_sign)
    return (_touches(sat_h, 8, _SATURN_DRISHTI)
            & _touches(jup_h, 8, _JUPITER_DRISHTI))


def t4_no_protective_jupiter(jup_sign: np.ndarray,
                             moon_sign: int) -> np.ndarray:
    """Transit Jupiter NOT in any kendra (1/4/7/10) from the natal Moon."""
    h = _house_from(moon_sign, jup_sign)
    protected = np.zeros_like(h, dtype=bool)
    for k in _KENDRA:
        protected |= h == k
    return ~protected


def leg2_trigger(sat_sign: np.ndarray, jup_sign: np.ndarray,
                 asc_sign: int, moon_sign: int) -> np.ndarray:
    """The primary Leg-2 OR: T1 | T2 | T3."""
    return (t1_sade_sati(sat_sign, moon_sign)
            | t2_saturn_in_8h(sat_sign, asc_sign)
            | t3_double_transit_8h(sat_sign, jup_sign, asc_sign))
