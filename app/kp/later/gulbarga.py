"""The "Gulbarga theory" for horary yes/no questions (a later rule, not Krishnamurti's).

Astro Secrets Part 6 (K. Subramaniam) reports it three times, crediting the
Gulbarga Astrological Research Centre; the KP E-zine repeats it:

  "if the sub lord of the Horary Number furnished happens to be either the Moon
  star lord or the lagna star-lord among the ruling planets also, then the query
  is to be answered in the affirmative; otherwise, not." (AS6:p.1603)

The sub-lord is that of the KP horary number (1-249). The ruling planets are
those of the moment and place of judgment, with the ascendant actually rising
then: the worked examples take "the Moon star lord of the day" (AS6:p.1603) and
"the ruling planets at the moment" (AS6:p.1613) (ruling LR5).

Usage:
    from app.kp.chart import Birth
    from app.kp.later.gulbarga import gulbarga
    gulbarga(245, Birth(1981, 1, 8, 18, 25, tz=5.5, lat=13.08, lon=80.27)).yes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import Birth, cast
from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.rules import FRAMING
from app.kp.ruling import ruling_planets
from app.kp.subs import divisions

CITATION: Final[str] = "AS6-gulbarga"


@dataclass(frozen=True, slots=True)
class GulbargaAnswer:
    """The number's sub-lord, the two ruling planets compared with it, and the answer."""

    number: int
    sub_lord: str
    moon_star_lord: str
    lagna_star_lord: str

    @property
    def yes(self) -> bool:
        return self.sub_lord in (self.moon_star_lord, self.lagna_star_lord)

    def to_dict(self) -> dict:
        c = LATER_CITATIONS[CITATION]
        return {
            "number": self.number, "sub_lord": self.sub_lord, "moon_star_lord": self.moon_star_lord,
            "lagna_star_lord": self.lagna_star_lord, "answer": "yes" if self.yes else "no",
            "author": "Gulbarga Astrological Research Centre, as reported by K. Subramaniam",
            "citation": f'{c.ref()} "{c.quote}"', "framing": FRAMING,
        }


def gulbarga(number: int, judged: Birth, *, node_mode: str = "mean") -> GulbargaAnswer:
    """Answer a yes/no horary question by the Gulbarga rule."""
    if not 1 <= number <= 249:
        raise ValueError("horary number must be between 1 and 249")
    rp = ruling_planets(cast(judged, node_mode=node_mode))
    return GulbargaAnswer(number, divisions()[number - 1].sub_lord, rp.moon_star_lord, rp.lagna_star_lord)


__all__ = ["GulbargaAnswer", "gulbarga"]
