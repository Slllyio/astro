"""HPA ch.12 arithmetic verification rules — the SECONDARY rectification channel.

Raman (Hindu Predictive Astrology, ch.12 "On Birth Verification and Rectification",
lines 65-93) lists three arithmetic consistency rules "generally employed by the
astrologers", while himself subordinating them to event-fitting ("birth times can be
rectified only by men of experience by a consideration of pronounced life incidents").
Accordingly this channel contributes a SMALL capped bonus (<= ``CHANNEL_CAP``) and never
outranks the event channels.

  R1 (verbatim): "Multiply the time of birth in ghaties by 4 and divide the product by 9.
      The remainder must give the ruling constellation when counted from Aswini, Makha
      or Moola."  -> remainder (whole-ghati convention, 0 -> 9) equals the Moon
      nakshatra's position inside its 9-star group.
  R2 (verbatim): "Multiply the number of ghaties from birth by 6 and add the longitude
      of the Sun (the number of degrees passed in the sign). Divide the sum by 30. The
      quotient plus 1 counted from the Sun's sign will give the rising sign."
      -> degrees-IN-SIGN explicitly (Raman's own parenthesis); inclusive counting.
  R3 (verbatim): "The 5th or the 9th sign from the house occupied by the lord of the
      sign in which the Moon is placed becomes the Janma Lagna ... The 7th from the sign
      occupied by the lord of the Moon's sign or the 5th or the 9th ... and in some
      cases the sign where the Moon is at radix itself becomes the ascendant."
      -> the FULL candidate set {5th, 7th, 9th from the Moon-sign-lord's sign;
      the Moon's own sign} (a wide net — weighted lowest).

Ghati convention: 1 ghati = 24 minutes; ghatis = (birth - sunrise) in days x 60. R1's
modular step uses the WHOLE-ghati count (Raman's ch.12 worked usage quotes whole
ghatis); R2 uses the fractional value. Both conventions are documented here and
reviewed by the doctrine gate.

Usage:
    from app.raman_saab.rectification.arithmetic import arithmetic_score
    result = arithmetic_score(chart_light, birth)   # ArithmeticScore(.subtotal <= 0.65)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import swisseph as swe

from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import BirthData, RamanChart

#: Channel weights (R3 is Raman's widest net -> lowest weight); hard cap on the channel.
W_R1: Final[float] = 0.25
W_R2: Final[float] = 0.25
W_R3: Final[float] = 0.15
CHANNEL_CAP: Final[float] = 0.65


@dataclass(frozen=True)
class ArithmeticScore:
    """The three rule outcomes + the ghati count they were computed from."""
    ghatis: float
    r1_nakshatra: bool
    r2_rising_sign: bool
    r3_janma_lagna: bool

    @property
    def subtotal(self) -> float:
        raw = (W_R1 * self.r1_nakshatra + W_R2 * self.r2_rising_sign
               + W_R3 * self.r3_janma_lagna)
        return min(raw, CHANNEL_CAP)


def sunrise_jd(birth: BirthData, ayanamsa: str) -> float:
    """Sunrise (JD UT, disc-centre) on the birth date — replicates the verified
    ``kala_context._sunrise_sunset`` swe.rise_trans pattern (rsmi flags BEFORE geopos;
    search from local civil midnight so it is *this* date's sunrise)."""
    jd_midnight = swe.julday(birth.year, birth.month, birth.day,
                             -birth.tz_offset, swe.GREG_CAL)
    geopos = (birth.longitude, birth.latitude, 0.0)
    with sidereal_mode(ayanamsa):
        _ret, tret = swe.rise_trans(
            jd_midnight, swe.SUN,
            swe.CALC_RISE | swe.BIT_DISC_CENTER,
            geopos, 0.0, 0.0, swe.FLG_SWIEPH)
    return float(tret[0])


def ghatis_from_sunrise(birth_jd_ut: float, sunrise: float) -> float:
    """Elapsed ghatis at birth: (birth - sunrise) in days x 60 (24 min per ghati)."""
    return (birth_jd_ut - sunrise) * 60.0


def rule1_nakshatra(ghatis: float, moon_nakshatra: int) -> bool:
    """R1: (whole-ghatis x 4) mod 9 (0 -> 9) equals the Moon nakshatra's position in its
    9-star group counted from Aswini (1-9), Makha (10-18) or Moola (19-27)."""
    rem = (round(ghatis) * 4) % 9
    rem = 9 if rem == 0 else rem
    position = ((moon_nakshatra - 1) % 9) + 1
    return rem == position


def rule2_rising_sign(ghatis: float, sun_deg_in_sign: float, sun_sign: int,
                      asc_sign: int) -> bool:
    """R2: quotient of (ghatis x 6 + Sun's degrees-in-sign) / 30, plus 1, counted
    INCLUSIVELY from the Sun's sign, equals the rising sign."""
    quotient = int((ghatis * 6.0 + sun_deg_in_sign) // 30.0)
    predicted = ((sun_sign - 1) + quotient) % 12 + 1     # (quotient+1)th from Sun's sign
    return predicted == asc_sign


def rule3_janma_lagna(moon_sign: int, moon_sign_lord_sign: int, asc_sign: int) -> bool:
    """R3: the ascendant lies in {5th, 7th, 9th from the Moon-sign-lord's sign} or is
    the Moon's own sign (the full on-disk candidate set)."""
    candidates = {((moon_sign_lord_sign - 1) + offset) % 12 + 1 for offset in (4, 6, 8)}
    candidates.add(moon_sign)
    return asc_sign in candidates


def arithmetic_score(chart: RamanChart, birth: BirthData) -> ArithmeticScore:
    """Evaluate R1-R3 for one candidate chart (Tier-L suffices — positions only)."""
    sunrise = sunrise_jd(birth, chart.ayanamsa)
    ghatis = ghatis_from_sunrise(chart.jd_ut, sunrise)
    moon = chart.planets["Moon"]
    sun = chart.planets["Sun"]
    lord = SIGN_LORDS[moon.sign]
    lord_pos = chart.planets.get(lord)
    r3 = (rule3_janma_lagna(moon.sign, lord_pos.sign, chart.asc_sign)
          if lord_pos is not None else False)
    return ArithmeticScore(
        ghatis=ghatis,
        r1_nakshatra=rule1_nakshatra(ghatis, moon.nakshatra),
        r2_rising_sign=rule2_rising_sign(ghatis, sun.lon % 30.0, sun.sign,
                                         chart.asc_sign),
        r3_janma_lagna=r3)
