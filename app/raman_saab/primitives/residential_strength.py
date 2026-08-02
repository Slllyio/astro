"""Residential strength (Bhavavastha) — how much of a Bhava's effect a planet in it gives.

Raman, *Graha & Bhava Balas* ch.1 §§12-17. A planet does not deliver its Bhava's results
uniformly: "While some are found very near the middle of the Bhava, others reside at the
beginning, or at the end. In all these three circumstances ... the effects of the respective
Bhavas, produced by the different planets in them, cannot be the same" (GBB-1:25-32). At a
Bhava Sandhi the planet "is utterly powerless and the results it produces are practically
nothing" (GBB-1:38-42); at the Bhava Madhya it gives the full effect.

The method (GBB-1:72-112), quoted rather than paraphrased because the arc is measured FROM
the sandhi, not from the madhya — the easy mistake is to invert it:

    If a planet is in Poorvabhaga of a House:
      (a) Planet's long - long of Arambhasandhi (starting point of a House) = Arc of
          residential strength
      (b) Arc of residential strength / Poorvabhaga of the Bhava = Residential strength
    If a planet is in Uttarabhaga of a Bhava:
      (a) Longitude of Viramasandhi (closing point of a House) - Planet's Long. = Arc ...

Both branches therefore give 0.0 at either sandhi and 1.0 at the madhya, rising linearly.
Raman's own worked example (GBB-1, Standard Horoscope) reports e.g. Jupiter 0.64 units of the
6th Bhava's effects, restated at GBB-1:203 — "Jupiter gives 0.64 units of the total effects of
the 6th Bhava. This effect will materialise during his Dasa or Bhukthi."

Scope notes:
  - This is a POSITIONAL quantity, not a Shadbala component. Raman's own table lists Rahu and
    Kethu alongside the seven grahas here, unlike Shadbala (7 visible grahas only, GBB-3) —
    so this primitive deliberately accepts any body.
  - It scales a planet's HOUSE-specific output only. It is not a verdict input and must not be
    used to re-grade a Bhava; Raman calls it "a general statement standing to be modified in
    the light of other important factors" (GBB-1:207-211).

Usage:
    from app.raman_saab.primitives.residential_strength import residential_strength
    bhava, strength = residential_strength(planet_lon, chart.bhava_madhyas, chart.bhava_sandhis)
"""
from __future__ import annotations

from typing import Sequence

from app.raman_saab.chart import cusps

#: Below this arc (degrees) a half-Bhava is treated as degenerate. Real Sripati/equal cusps
#: never produce it; a malformed or empty cusp set would otherwise divide by zero.
_MIN_HALF_ARC = 1e-9


def residential_strength(
    lon: float,
    madhyas: Sequence[float],
    sandhis: Sequence[float],
) -> tuple[int, float]:
    """The Bhava a longitude falls in, and its residential strength there (0.0-1.0).

    0.0 at either Bhava Sandhi ("utterly powerless", GBB-1:38-42), 1.0 at the Bhava Madhya,
    linear between — measured as the arc FROM the bounding sandhi over the half-Bhava that
    contains the planet (GBB-1:72-112).

    Returns `(bhava, strength)` with bhava in 1..12. Raises ValueError on a cusp set that is
    not 12 madhyas + 12 sandhis, rather than silently scoring against a broken chart.
    """
    if len(madhyas) != 12 or len(sandhis) != 12:
        raise ValueError(
            f"need 12 madhyas and 12 sandhis, got {len(madhyas)} and {len(sandhis)}")

    bhava = cusps.bhava_of(lon, tuple(sandhis))
    i = bhava - 1
    arambha = sandhis[i]                    # sandhi[i] STARTS bhava i+1 (cusps.py:11)
    virama = sandhis[(i + 1) % 12]
    madhya = madhyas[i]

    into_bhava = (lon - arambha) % 360.0
    poorva_len = (madhya - arambha) % 360.0
    uttara_len = (virama - madhya) % 360.0

    if into_bhava <= poorva_len:            # Poorvabhaga — arc from the ARAMBHA sandhi
        arc, half = into_bhava, poorva_len
    else:                                   # Uttarabhaga — arc back from the VIRAMA sandhi
        arc, half = (virama - lon) % 360.0, uttara_len

    if half < _MIN_HALF_ARC:
        return bhava, 0.0
    # clamp: a longitude exactly on a sandhi can land a hair outside its half by float error.
    return bhava, max(0.0, min(1.0, arc / half))


def residential_strengths(chart) -> dict[str, tuple[int, float]]:
    """`{planet: (bhava, residential strength)}` for every body on a cast chart.

    Skips nothing: Raman's own table scores Rahu and Kethu here (see the module docstring)."""
    return {
        name: residential_strength(p.lon, chart.bhava_madhyas, chart.bhava_sandhis)
        for name, p in chart.planets.items()
    }
