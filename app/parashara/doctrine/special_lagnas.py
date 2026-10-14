"""Special ascendants — Bhava, Hora and Ghatika Lagna (BPHS ch.5).

Three time-based ascendants that advance from the Sun's sunrise longitude at a fixed rate per ghati
(1 ghati = 24 min; 1 day = 60 ghatis). Each is used as its own lagna — "keeping the planets at
birth as they are, prepare bhava charts with respect to each and analyse as the natal ascendant"
(BPHS-5:9):

    Bhava Lagna   — one sign every 5 ghatis   (BPHS-5:2-3)
    Hora Lagna    — one sign every 2.5 ghatis  (BPHS-5:4-5)
    Ghatika Lagna — one sign every 1 ghati     (BPHS-5:6-8)

So each = Sun-at-sunrise + (ghatis-since-sunrise / period) x 30deg. Verified against Parashara's own
worked example (Sun at sunrise 132deg, birth 12gh30vi -> Bhava Libra 27, Hora Capricorn 12, Ghati
Leo 27). The pure arithmetic lives here; `chart.ephemeris.special_lagnas` supplies the two inputs.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-5", 35)     # sl.2-3, "BHAVA LAGNA : From Sunrise ..."

#: lagna name -> ghatis the ascendant takes to traverse one sign.
PERIODS: Final[Mapping[str, float]] = {"Bhava": 5.0, "Hora": 2.5, "Ghati": 1.0}


def special_lagna_longitudes(sun_at_sunrise: float, ghatis_since_sunrise: float) -> dict[str, float]:
    """The three special-ascendant longitudes (0..360) from the Sun's sunrise longitude and the
    ghatis elapsed since sunrise (BPHS-5). Pure arithmetic — no ephemeris."""
    sun = sun_at_sunrise % 360.0
    return {name: (sun + (ghatis_since_sunrise / period) * 30.0) % 360.0
            for name, period in PERIODS.items()}
