"""ASP ch.XV transit-band elections — the nine uniform bindu-band rules (ASP-15:21-183).

Released to this subsystem by the 2026-08-03 firewall lift (they were mined and deliberately
NOT encoded under the natal scope — DOCTRINE_BACKLOG "ASP ch.XV mining record"). The nine
rules share one shape: *graha X transiting a sign whose bindu count in X's OWN
Bhinnashtakavarga falls in band B -> verdict V for activity set A.*

Encoded (rule -> lines): Sun 5-8 bindus auspicious for long journeys/marriages/good actions
(ASP-15:21-24); Sun 1-3 poor, 0 absolutely forbidden, 4 mixed (ASP-15:25-30); Moon 6-8 for
marriage/assistants/studies/friendships (ASP-15:55-58); Moon 1-3 fruitless (ASP-15:59-62);
Mars max-bindu rasi for land/houses/litigation (ASP-15:82-96); Mercury max-bindu rasi for
education/literary work/debates (ASP-15:101-109); Jupiter max-bindu sign for initiation/
Veda study/earning/ceremonies/children (ASP-15:116-128); Venus max-bindu sign for music/
marriage/clothes (ASP-15:145-150); Saturn max-bindu rasi for factories/agriculture
(ASP-15:155-159).

DEFERRED, recorded not dropped: the direction-map rules (3, 10, 14, 18, 20 — siting by the
max-bindu sign's compass direction) and the rising-sign-of-the-moment rules (12, 15, 16,
21, 22 — daily windows when a given sign/SAV band rises) need a sign->direction table and a
time-scan respectively; encode them when an election surface actually asks for them.

Usage:
    from app.raman_saab.electional.asp_transit_elections import transit_election
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga


@dataclass(frozen=True)
class TransitElection:
    graha: str
    transit_sign: int
    bindus: int
    verdict: str               # auspicious | mixed | poor | forbidden | (max-bindu) best
    activities: tuple[str, ...]
    source: Citation


#: The max-bindu family: graha -> (activities, citation line). ASP-15 as cited above.
_MAX_BINDU_RULES: Final[dict[str, tuple[tuple[str, ...], int]]] = {
    "Mars": (("buying_land", "buying_houses", "litigation"), 82),
    "Mercury": (("education", "literary_work", "debates", "litigation_success"), 101),
    "Jupiter": (("spiritual_initiation", "veda_study", "earning_money", "ceremonies",
                 "begetting_children"), 116),
    "Venus": (("learning_music", "marriage", "purchase_of_clothes"), 145),
    "Saturn": (("acquiring_factories", "agriculture"), 155),
}

_SUN_ACTS: Final[tuple[str, ...]] = ("long_journeys", "marriages", "good_actions")
_MOON_ACTS: Final[tuple[str, ...]] = ("marriage", "hiring_assistants", "beginning_studies",
                                      "forming_friendships")


def transit_election(chart: RamanChart, graha: str, transit_sign: int) -> Optional[TransitElection]:
    """Judge `graha` transiting `transit_sign` (1..12) against its own BAV in the NATIVE's
    chart, per the ASP-15 band rules. Returns None for grahas ASP-15 states no rule for."""
    bav = bhinnashtakavarga(chart, graha) if graha in (
        "Sun", "Moon", *_MAX_BINDU_RULES) else None
    if bav is None:
        return None
    bindus = bav[transit_sign]

    if graha == "Sun":
        if bindus == 0:
            verdict = "forbidden"          # "absolutely forbidden" (ASP-15:25-30)
        elif bindus <= 3:
            verdict = "poor"
        elif bindus == 4:
            verdict = "mixed"
        else:
            verdict = "auspicious"          # 5..8 (ASP-15:21-24)
        return TransitElection(graha, transit_sign, bindus, verdict, _SUN_ACTS,
                               Citation("ASP-15", 21))

    if graha == "Moon":
        if bindus >= 6:
            verdict = "auspicious"          # ASP-15:55-58
        elif bindus <= 3:
            verdict = "poor"                # "fruitless" (ASP-15:59-62)
        else:
            verdict = "mixed"
        return TransitElection(graha, transit_sign, bindus, verdict, _MOON_ACTS,
                               Citation("ASP-15", 55))

    acts, line = _MAX_BINDU_RULES[graha]
    best = max(bav.values())
    verdict = "auspicious" if bindus == best else "mixed" if bindus >= best - 1 else "poor"
    return TransitElection(graha, transit_sign, bindus, verdict, acts,
                           Citation("ASP-15", line))
