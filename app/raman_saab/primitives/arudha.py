"""Arudha padas — the "image / manifestation" of a bhava, as B. V. Raman computes them.

The Arudha pada of a house is found by counting from the house to its lord, then the same count
again from the lord; the resulting sign is the Arudha. **No 1st/7th exception.** Strict Jaimini
(Jaimini Sutras / later tradition) redirects an Arudha landing in the house itself or its 7th to
the 10th therefrom — Raman does not: his definition (HTJAH-I:2519-2521, "the sign arrived at by
counting as many signs from lord of Lagna as lord of Lagna is removed from Lagna") states no
exception, and his worked examples cover BOTH exception arms: the 7th-landing AL is kept
(Aquarius Lagna, Saturn in Taurus → "the 4th from Taurus, viz., Leo becomes Arudha Lagna" — Leo
IS the 7th from Aquarius, HTJAH-I:2521-2522), and the SELF-landing AL is kept in his own Jaimini
book (Studies in Jaimini Ex. 48, Hitler: "lord of Lagna Sukra is in the 7th, and the 7th from
the 7th, viz., Lagna itself will be Arudha Lagna" — Thula, where the exception would force
Capricorn). The exception's actual home is BPHS 29.4-5 (Parasara / later Rath school), which on
the identical Aquarius configuration yields Taurus — exactly what the old code returned: a BPHS
behavior wearing a Raman label. Per the Prime Directive, Raman's printed arithmetic wins.
(2026-08-23 audit-ticket fix, reviewer VALIDATED/HIGH.)

The Arudha of the Lagna is the **Arudha Lagna (AL)** — how the native is perceived by the world
(status, wealth, public image), as distinct from the Lagna (the actual self). Raman uses it for
image/affluence.

Usage:
    from app.raman_saab.primitives import arudha
    al = arudha.arudha_lagna(chart)        # AL sign (1..12)
    a7 = arudha.arudha_pada(chart, 7)      # Upapada-adjacent partner image, etc.
"""
from __future__ import annotations

from typing import Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart


def arudha_pada(chart: RamanChart, house: int) -> Optional[int]:
    """Arudha pada sign (1..12) of the whole-sign `house` (counted from the Lagna). None if the
    house lord is absent (sparse Track-B)."""
    house_sign = ((chart.asc_sign - 1) + (house - 1)) % 12 + 1
    lord = SIGN_LORDS[house_sign]
    p = chart.planets.get(lord)
    if p is None:
        return None
    lord_sign = p.sign
    # count house->lord, then the same count lord-> : arudha = 2*lord - house (1-based, mod 12).
    # Deliberately NO 1st/7th->10th exception — Raman's formula and worked example
    # (HTJAH-I:2519-2522) apply the plain count; see the module docstring.
    return ((2 * lord_sign - house_sign - 1) % 12) + 1


def arudha_lagna(chart: RamanChart) -> Optional[int]:
    """Arudha Lagna (AL) — the Arudha pada of the 1st house; the native's worldly image/status."""
    return arudha_pada(chart, 1)


def upapada_lagna(chart: RamanChart) -> Optional[int]:
    """Upapada Lagna (UL) — the Arudha pada of the 12th house; the marriage/spouse image (Jaimini)."""
    return arudha_pada(chart, 12)
