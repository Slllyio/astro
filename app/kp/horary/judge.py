"""Judge a KP horary question (KPR6): cusp sub-lord verdict + ruling-planet timing.

The verdict uses the same cusp sub-lord rules and tie-break as the natal
engine (:mod:`app.kp.judgment`, rulings R12/R18) on the horary chart. Two
horary-only facts are added:

* ``star_lord_retrograde``: the CSL sits in the star of a retrograde planet.
  Krishnamurti: "If the lord of the constellation in which third cusp
  sub-lord is deposited is retrograde, the call will not materialise"
  (KPR6-CSL-RETRO), and the same for the child's return (KPR6-CHILD-RETRO).
  He states it for those questions; the engine reports it on every horary
  verdict as a flag and does not change the verdict (ruling RH5).
* ``fruitful``: ruling planets that also signify the matter's favourable
  houses, and the next moment the chosen body reaches a position they govern
  (:mod:`app.kp.horary.timing`).

Usage:
    from app.kp.chart import Birth
    from app.kp.horary.judge import judge_horary
    h = judge_horary(48, Birth(1969, 12, 11, 10, 0, tz=5.5, lat=13.08, lon=80.27), "marriage")
    print(h.to_dict())
"""

from __future__ import annotations

from dataclasses import dataclass

from app.kp.chart import NODES, Birth
from app.kp.horary.cast import cast_horary
from app.kp.horary.timing import Rising, fruitful_planets, next_rising, usable_ruling_planets
from app.kp.judgment import Matter, _core_full, _matter
from app.kp.ruling import ruling_planets

#: Questions the engine refuses to time (matches the project's walled prasna rule).
EXCLUDED = ("death", "longevity", "lifespan", "suicide", "murder")


@dataclass(frozen=True, slots=True)
class HoraryVerdict:
    number: int
    matter: Matter
    verdict: str
    raw_verdict: str
    resolution: str
    csl: str
    csl_houses: frozenset[int]
    csl_star_lord: str
    star_lord_retrograde: bool
    ruling_planets: tuple[str, ...]
    usable_ruling_planets: tuple[str, ...]
    fruitful: tuple[str, ...]
    rising: Rising | None
    tz: float

    def to_dict(self) -> dict:
        return {
            "number": self.number, "matter": self.matter.key, "cusp": self.matter.cusp,
            "verdict": self.verdict, "raw_verdict": self.raw_verdict, "resolution": self.resolution,
            "csl": self.csl, "csl_houses": sorted(self.csl_houses), "csl_star_lord": self.csl_star_lord,
            "star_lord_retrograde": self.star_lord_retrograde,
            "ruling_planets": list(self.ruling_planets),
            "usable_ruling_planets": list(self.usable_ruling_planets),
            "fruitful": list(self.fruitful),
            "timing": None if self.rising is None else {
                "body": self.rising.body, "at": self.rising.local(self.tz),
                "sign_lord": self.rising.position.sign_lord, "star_lord": self.rising.position.star_lord,
                "sub_lord": self.rising.position.sub_lord, "sub_sub_lord": self.rising.position.sub_sub_lord,
            },
            "framing": "What Krishnamurti's horary rules say; not a validated prediction.",
        }


def judge_horary(number: int, judged: Birth, matter: str | Matter, *, body: str | None = "lagna",
                 node_mode: str = "mean") -> HoraryVerdict:
    """Judge ``matter`` from horary ``number`` at the moment and place ``judged``.

    ``body`` picks the timing body (``lagna`` for hours, ``Moon`` for days,
    ``Sun`` for months, ``Jupiter`` for years, KPR6-RP-BODY) or ``None`` to skip timing.
    """
    m = _matter(matter)
    if any(w in m.key for w in EXCLUDED):
        raise ValueError("death, lifespan and self-harm questions are not judged")
    chart = cast_horary(number, judged, node_mode=node_mode)
    verdict, raw, how, csl, houses, _ = _core_full(chart, m)
    star = chart.planets[csl].star_lord
    retro = chart.planets[star].retrograde and star not in NODES
    rp = ruling_planets(chart)
    fr = fruitful_planets(chart, m.favourable)
    rising = None
    if body is not None and fr:
        rising = next_rising(judged, fr, body=body, lagna_lord=chart.cusp(1).sign_lord)
    return HoraryVerdict(number, m, verdict, raw, how, csl, houses, star, retro,
                         (*rp.planets, *rp.node_agents), usable_ruling_planets(chart), fr, rising, judged.tz)


__all__ = ["HoraryVerdict", "judge_horary", "EXCLUDED"]
