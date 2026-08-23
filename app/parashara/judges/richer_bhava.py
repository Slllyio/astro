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
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation

from app.parashara.chart.bhava_chart import judge_bhava
from app.parashara.doctrine import mahapurusha
from app.parashara.primitives.deeptadi_avastha import deeptadi
from app.parashara.doctrine.bhava_karaka import karaka_of
from app.parashara.judges.bhava_prosperity import BhavaVerdict, Verdict
from app.parashara.primitives import ashtakavarga as _av
from app.parashara.primitives.relationships import EXALTATION, GRAHAS, SIGN_LORDS, naisargika
from app.parashara.chart.vimsopaka_chart import vimsopaka_for


#: Parashara's minimum required Shadbala per graha, in rupas (BPHS-27:3739-3745). "If a planet has
#: the required shadbala, it will prove favourable" (BPHS-27:3747); below it, the graha is deficient.
REQUIRED_SHADBALA: Final[Mapping[str, float]] = {
    "Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
SHADBALA_SOURCE: Final[Citation] = Citation("BPHS-27", 3747)


@dataclass(frozen=True)
class RicherBhavaVerdict:
    house: int
    verdict: Verdict             # flourishing | ordinary | annihilated
    degree: str                  # strong | moderate | balanced — how decisively the votes fell
    prosperity_votes: int
    annihilation_votes: int
    factors: tuple[str, ...]     # every vote, prosperity then added, each citing its source
    base: BhavaVerdict           # the underlying ch.11 verdict (unchanged)

    @property
    def graded(self) -> str:
        """The verdict qualified by its decisiveness, e.g. 'strongly flourishing', 'ordinary'."""
        if self.verdict == "ordinary":
            return "ordinary"
        return f"{'strongly' if self.degree == 'strong' else 'moderately'} {self.verdict}"


def _degree(margin: int) -> str:
    """How decisively the net vote fell: |prosperity - annihilation|. Transparent from the votes,
    not a separate doctrinal claim — it only surfaces the margin the 3-way verdict discards."""
    if margin == 0:
        return "balanced"
    return "strong" if margin >= 3 else "moderate"


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


def richer_all_bhavas(longitudes: Mapping[str, float], *, asc_sign: int, moon_waxing: bool,
                      shadbala_rupas: Optional[Mapping[str, float]] = None,
                      ) -> dict[int, RicherBhavaVerdict]:
    """The richer verdict for all twelve bhavas (ch.11 + strength + yoga).

    Runs on longitudes alone (book charts + cast charts). When `shadbala_rupas` (the six-fold
    Shadbala in rupas per graha) is supplied — only cast charts can compute it, as it needs
    birth-time speeds + the sunrise/Kala context — a further vote fires: the lord's Shadbala meeting
    its required strength (BPHS-27:3747) adds a prosperity vote, falling short adds an annihilation
    vote. Book charts pass None and simply do not cast that vote.
    """
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
                p += 1; factors.append(f"+ {bindus} SAV bindus, a favourable band (BPHS-72)")
            elif bindus < 25:
                a += 1; factors.append(f"- {bindus} SAV bindus, an adverse band (BPHS-72)")

        if lord in maha_planets or karaka in maha_planets:
            p += 1; factors.append("+ a Pancha Mahapurusha yoga strengthens the lord/karaka (SARAVALI-37)")

        # An occupant's Deeptadi colours the house it sits in (BPHS-45:118): a bright state
        # (Deepta/Swastha) strengthens the bhava, a spoiled one (Khala, or Vikala/Kopa) weakens it.
        for occ, osign in planet_signs.items():
            if occ not in _av.PLANETS or ((osign - asc_sign) % 12) + 1 != house:
                continue
            d = deeptadi(occ, longitudes)
            if d.state in ("Deepta", "Swastha"):
                p += 1; factors.append(f"+ {occ} occupies in {d.state}avastha (BPHS-45)")
            elif d.state == "Khala" or d.vikala or d.kopa:
                a += 1; spoil = "Khala" if d.state == "Khala" else ("Vikala" if d.vikala else "Kopa")
                factors.append(f"- {occ} occupies in {spoil}avastha (BPHS-45)")

        if shadbala_rupas is not None and lord in shadbala_rupas and lord in REQUIRED_SHADBALA:
            rupas = shadbala_rupas[lord]
            if rupas >= REQUIRED_SHADBALA[lord]:
                p += 1; factors.append(
                    f"+ lord {lord} has its required Shadbala ({rupas:.2f} >= "
                    f"{REQUIRED_SHADBALA[lord]} rupas) (BPHS-27)")
            else:
                a += 1; factors.append(
                    f"- lord {lord} short of required Shadbala ({rupas:.2f} < "
                    f"{REQUIRED_SHADBALA[lord]} rupas) (BPHS-27)")

        verdict: Verdict = "flourishing" if p > a else "annihilated" if a > p else "ordinary"
        out[house] = RicherBhavaVerdict(house=house, verdict=verdict, degree=_degree(abs(p - a)),
                                        prosperity_votes=p, annihilation_votes=a,
                                        factors=tuple(factors), base=base)
    return out
