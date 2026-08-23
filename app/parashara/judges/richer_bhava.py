"""A richer bhava verdict — BPHS ch.11 EXTENDED with strength and yoga, by Parashara's own method.

Ch.11 judges a bhava by counting prosperity conditions against annihilation conditions
(`bhava_prosperity`). This module keeps that exact net-vote method but adds more BPHS-cited votes of
each kind — strength and yoga signals Parashara elsewhere says bear on a bhava's result:

  * the LORD's Vimsopaka band (ch.7): "wholly-favourable" adds a prosperity vote, "inauspicious" an
    annihilation vote — Parashara's own bands, no tuned cutoff;
  * the KARAKA's dignity (ch.32 karaka + ch.3): own/exaltation adds prosperity, debilitation or an
    enemy's sign adds annihilation (the lord's own dignity is already a ch.11 clause, so only the
    karaka is added here — no double counting);
  * the bhava's Sarvashtakavarga bindus (ch.66): clearly above the 28-bindu average adds prosperity,
    clearly below adds annihilation;
  * a Pancha Mahapurusha yoga (Saravali ch.37) whose planet lords or signifies the bhava adds a
    prosperity vote.

The verdict rule is UNCHANGED from ch.11 — more prosperity votes than annihilation -> flourishing,
fewer -> annihilated, equal -> ordinary. It is a faithful elaboration of Parashara's method, NOT a
model tuned toward any target; every added vote cites its own sloka. Inputs are longitudes + sign
only, so it runs identically on book charts and cast charts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from app.parashara.chart.bhava_chart import judge_bhava
from app.parashara.doctrine import mahapurusha
from app.parashara.doctrine.bhava_karaka import karaka_of
from app.parashara.judges.bhava_prosperity import BhavaVerdict, Verdict
from app.parashara.primitives import ashtakavarga as _av
from app.parashara.primitives.relationships import EXALTATION, GRAHAS, SIGN_LORDS, naisargika
from app.parashara.chart.vimsopaka_chart import vimsopaka_for


@dataclass(frozen=True)
class RicherBhavaVerdict:
    house: int
    verdict: Verdict             # flourishing | ordinary | annihilated
    prosperity_votes: int
    annihilation_votes: int
    factors: tuple[str, ...]     # every vote, prosperity then added, each citing its source
    base: BhavaVerdict           # the underlying ch.11 verdict (unchanged)


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def _dignity(planet: str, sign: int) -> int:
    """+1 if `planet` is in own/exaltation, -1 if debilitated or in an enemy's sign, else 0 (ch.3)."""
    if planet not in EXALTATION:
        return 0
    if sign == EXALTATION[planet] or SIGN_LORDS.get(sign) == planet:
        return 1
    if sign == ((EXALTATION[planet] - 1 + 6) % 12) + 1:          # debilitation = 7th from exaltation
        return -1
    if naisargika(planet, SIGN_LORDS[sign]) == "shatru":         # an enemy's sign
        return -1
    return 0


def richer_all_bhavas(longitudes: Mapping[str, float], *, asc_sign: int,
                      moon_waxing: bool) -> dict[int, RicherBhavaVerdict]:
    """The richer verdict for all twelve bhavas (ch.11 + strength + yoga), from longitudes alone."""
    planet_signs = {p: _sign_of(l) for p, l in longitudes.items()}
    sav = _av.sarvashtakavarga({g: planet_signs[g] for g in _av.PLANETS if g in planet_signs},
                               asc_sign=asc_sign) if any(g in planet_signs for g in _av.PLANETS) else {}
    # Vimsopaka per graha, skipping any the chart is too sparse to compute (a dispositor absent) —
    # uncomputable, not faked, so that vote simply does not fire.
    vims = {}
    for g in GRAHAS:
        if g in longitudes:
            try:
                vims[g] = vimsopaka_for(g, longitudes)
            except (ValueError, KeyError):
                pass
    maha_planets = {y.planet for y in mahapurusha.detect(planet_signs, asc_sign=asc_sign)}

    out: dict[int, RicherBhavaVerdict] = {}
    for house in range(1, 13):
        base = judge_bhava(house, longitudes, asc_sign=asc_sign, moon_waxing=moon_waxing)
        p, a = base.net_prosperity, base.net_annihilation
        factors = list(base.reasons)

        house_sign = ((asc_sign - 1 + house - 1) % 12) + 1
        lord = SIGN_LORDS[house_sign]
        karaka = karaka_of(house)

        vs = vims.get(lord)
        if vs is not None and vs.band == "wholly-favourable":
            p += 1; factors.append(f"+ lord {lord} Vimsopaka wholly-favourable (BPHS-7)")
        elif vs is not None and vs.band == "inauspicious":
            a += 1; factors.append(f"- lord {lord} Vimsopaka inauspicious (BPHS-7)")

        if karaka in planet_signs:
            kd = _dignity(karaka, planet_signs[karaka])
            if kd > 0:
                p += 1; factors.append(f"+ karaka {karaka} in own/exaltation (BPHS-32)")
            elif kd < 0:
                a += 1; factors.append(f"- karaka {karaka} debilitated or in an enemy's sign (BPHS-32)")

        bindus = sav.get(house_sign)
        if bindus is not None:
            if bindus > 30:
                p += 1; factors.append(f"+ {bindus} SAV bindus, above the 28 average (BPHS-66)")
            elif bindus < 25:
                a += 1; factors.append(f"- {bindus} SAV bindus, below the 28 average (BPHS-66)")

        if lord in maha_planets or karaka in maha_planets:
            p += 1; factors.append("+ a Pancha Mahapurusha yoga strengthens the lord/karaka (SARAVALI-37)")

        verdict: Verdict = "flourishing" if p > a else "annihilated" if a > p else "ordinary"
        out[house] = RicherBhavaVerdict(house=house, verdict=verdict, prosperity_votes=p,
                                        annihilation_votes=a, factors=tuple(factors), base=base)
    return out
