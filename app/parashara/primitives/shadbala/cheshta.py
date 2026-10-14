"""Cheshta bala — motional strength (BPHS ch.27, slokas 18, 21-25).

    "The Sun's Ayana bala is his Cheshta bala; the Moon's Paksha bala is her Cheshta bala. For the
     other 5 planets ... eight kinds of motions: Vakra, Anuvakra, Vikala, Manda, Mandatara, Sama,
     Chara, Atichara. The strengths allotted are 60, 30, 15, 30, 15, 7.5, 45 and 30." (BPHS-27:3596,
     BPHS-27:21-23)

The eight motion-types and their virupa values are Parashara's, verbatim. What the sloka states
QUALITATIVELY is which motion a given speed belongs to ("Manda = somewhat slower than usual",
"Chara = faster than Sama"). Turning a measured speed into one of the eight therefore requires
explicit thresholds; those below are the ENGINE's stated interpretation, anchored on the two
unambiguous cases (retrograde -> Vakra; near-zero -> Vikala) and the planet's mean daily motion.
Documented here so the interpretive layer is visible, not hidden. The precise alternative — the
Seeghra-kendra method (sl.24-25) — needs mean longitudes + seeghrochchas (a heliocentric-mean
computation) this engine does not yet carry; that is the faithful upgrade path.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-27", 3596)
MOTIONS_SOURCE: Final[Citation] = Citation("BPHS-27", 3618)   # the 8 motions + their virupa values

#: Motion -> virupas, BPHS-27:21-23 (verbatim).
MOTION_VIRUPAS: Final[dict[str, float]] = {
    "vakra": 60.0, "anuvakra": 30.0, "vikala": 15.0, "manda": 30.0,
    "mandatara": 15.0, "sama": 7.5, "chara": 45.0, "atichara": 30.0,
}

#: Mean geocentric daily motion (deg/day) for the five star-planets — standard values, used to band
#: the measured speed. Sun/Moon use Ayana/Paksha instead, so they are not here.
_MEAN_MOTION: Final[dict[str, float]] = {
    "Mars": 0.524, "Mercury": 1.383, "Jupiter": 0.083, "Venus": 1.602, "Saturn": 0.034,
}


def _classify(speed: float, mean: float) -> str:
    """Map a longitudinal speed to one of the eight motions (engine's documented bands)."""
    if speed < 0:
        return "vakra"                       # retrograde (Anuvakra needs multi-epoch detection)
    ratio = speed / mean if mean else 0.0
    if ratio < 0.10:
        return "vikala"                      # near-stationary
    if ratio < 0.5:
        return "mandatara"                   # much slower than mean
    if ratio < 0.9:
        return "manda"                       # somewhat slower
    if ratio <= 1.1:
        return "sama"                        # about mean
    if ratio <= 1.5:
        return "chara"                       # faster
    return "atichara"                        # much faster


def cheshta_bala(planet: str, *, speed: float,
                 sun_ayana: float | None = None, moon_paksha: float | None = None) -> float:
    """Motional strength of `planet` in virupas.

    Sun's Cheshta == its Ayana bala; Moon's == its Paksha bala (pass them in). The five star-planets
    are classified from `speed` against their mean motion.
    """
    if planet == "Sun":
        if sun_ayana is None:
            raise ValueError("Sun's Cheshta bala is its Ayana bala; pass sun_ayana")
        return sun_ayana
    if planet == "Moon":
        if moon_paksha is None:
            raise ValueError("Moon's Cheshta bala is its Paksha bala; pass moon_paksha")
        return moon_paksha
    if planet not in _MEAN_MOTION:
        raise ValueError(f"Cheshta bala is for the 7 grahas, not {planet!r}")
    return MOTION_VIRUPAS[_classify(speed, _MEAN_MOTION[planet])]
