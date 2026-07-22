"""Per-varga judge — assess each divisional chart with Raman's GENERAL principles only.

Four principles, each independently citable — NO invented per-varga rules (no
"10th-lord-in-D10" fabrications; none of Raman's texts teach such rules, and the
Prime Directive forbids synthesizing them):

  (a) DIGNITY of the varga lagna lord and the domain karakas in the varga's sign —
      the GBB-3 Saptavargaja pattern (a planet's varga dignity measures its strength
      there, GBB-3:447-543);
  (b) BENEFIC/MALEFIC OCCUPANCY of the varga lagna and its kendras — Raman's general
      judgment doctrine, both directions verbatim: "good planets in Kendras ... great
      happiness" (HTJAH-I:1090-1091), "Jupiter or Venus ... in quadrants or trines ...
      favourable results" (HTJAH-I:1095-1096), "Benefices in Kendras ... confer ...
      longevity" (HTJAH-I:9913-9914), "malefic planets in Kendras [without] benefice
      aspects ..." (HTJAH-I:9849-9850); in-varga application demonstrated by Raman's own
      D9 house-framed readings (HTJAH-I:2856);
  (c) VARGOTTAMA — a graha in the same sign in D1 and D9 is strong, and Raman credits
      that strength wherever the graha testifies as lord, karaka or lagna (a paraphrase,
      gate-corrected anchors): "lord of Lagna ... in Vargottama ... happy all his life"
      (HTJAH-I:1119-1120); "Lagna ... the same both in Rashi and Navamsha ...
      Vargottamamsa. Hence the Lagna is very powerful" (HTJAH-I:1859-1860); the karaka
      usage "The Sun ... occupies a vargottama position ... The Karaka is therefore
      inclining towards good" (HTJAH-I:1810-1811); definition at HPA-20:247-248;
  (d) ``varga_status`` — the confirms/weakens/neutral model GENERALIZED from the proven
      D9 ``house_template._navamsa_status``: a pillar vargottama/exalted/own in the
      varga confirms the matter; debilitated or in a dusthana from the varga lagna
      weakens it.

bphs-doctrine-reviewer (P3 gate): principles (a), (b), (d) VALIDATED (HIGH) as a
report-only surface; (c) doctrine VALIDATED with the citation anchors corrected above
(the prior HPA-11 anchor had no vargottama text). Recorded caveats: the dignity model is
a naisargika-only simplification of GBB's compound relation (note on any future
promotion); re-review is MANDATORY if any non-D9 varga_status ever feeds the verdict path.

VERDICT-AUTHORITY INVARIANT: this module (the report surface) is imported by NOTHING in the
D1 verdict path. The navamsa (D9) modulates all matters, and — since the D-7 promotion
(2026-07-22, this mandatory re-review completed) — the Sapthamsa (D-7) modulates the H5
children matter; BOTH via NATIVE helpers inside house_template (`_navamsa_status`,
`_saptamsa_status`/`_saptamsa_gate`), never by importing this report. All 16 readings here
remain a standalone report; the D-7 children gate is borderline-only and was verified
verdict-invariant on the golden ratchet (209/241 unchanged).

Usage:
    from app.raman_saab.judges.varga_judge import build_shodasavarga_report
    report = build_shodasavarga_report(chart)
    report.readings[6].status        # e.g. the D10 reading's confirms/weakens
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga_chart import VargaChart, cast_all_vargas
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.varga_domains import DOMAINS, VargaDomain
from app.raman_saab.primitives import relationships as rel
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)
from app.raman_saab.primitives.vargavisesha import VargaVisesha, vargavisesha

VargaStatus = Literal["confirms", "weakens", "neutral", "unknown"]
Dignity = Literal["exalt", "debil", "own", "friend", "neutral", "enemy"]

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})


def _varga_dignity(planet: str, sign: int) -> Dignity:
    """Sign-only dignity vs the varga sign's lord (naisargika relation for friend/
    enemy) — mirrors ``conditions._varga_dignity`` semantics for ANY division's sign.
    Nodes are 'neutral' (they own no sign; Raman judges them by association)."""
    if planet in ("Rahu", "Ketu"):
        return "neutral"
    if sign == rel.EXALTATION[planet][0]:
        return "exalt"
    if sign == rel.DEBILITATION[planet][0]:
        return "debil"
    lord = SIGN_LORDS[sign]
    if lord == planet:
        return "own"
    return rel.naisargika(planet, lord)          # friend | neutral | enemy


@dataclass(frozen=True)
class PillarReading:
    """One pillar (varga lagna lord or domain karaka) read inside the varga."""
    planet: str
    role: Literal["varga_lagna_lord", "domain_karaka"]
    varga_sign: int
    varga_house: Optional[int]                   # None in D2 (no house frame)
    dignity: Dignity
    vargottama: bool                             # the D1==D9 flag


@dataclass(frozen=True)
class VargaReading:
    """A divisional chart assessed by the four general principles."""
    n: int
    name: str
    domain: str
    related_houses: tuple[int, ...]
    chart: VargaChart
    lagna_lord: PillarReading
    karakas: tuple[PillarReading, ...]
    benefics_on_lagna: tuple[str, ...]
    malefics_on_lagna: tuple[str, ...]
    benefics_in_kendra: tuple[str, ...]          # houses 1/4/7/10 from the varga lagna
    malefics_in_kendra: tuple[str, ...]
    status: VargaStatus
    notes: tuple[tuple[str, str], ...]
    source: Citation


@dataclass(frozen=True)
class ShodasavargaReport:
    """All sixteen readings (ascending n) + the Parijatadi own-varga standings."""
    readings: tuple[VargaReading, ...]
    vargavisesha: tuple[VargaVisesha, ...]


def _pillar(chart: RamanChart, vc: VargaChart, planet: str,
            role: Literal["varga_lagna_lord", "domain_karaka"]) -> Optional[PillarReading]:
    p = chart.planets.get(planet)
    if p is None:
        return None
    pos = vc.positions[planet]
    return PillarReading(planet=planet, role=role, varga_sign=pos.sign,
                         varga_house=pos.house,
                         dignity=_varga_dignity(planet, pos.sign),
                         vargottama=pos.vargottama)


def _occupants(vc: VargaChart, houses: frozenset[int],
               group: frozenset[str]) -> tuple[str, ...]:
    return tuple(name for name in _PLANET_ORDER
                 if name in vc.positions
                 and vc.positions[name].house in houses
                 and name in group)


def _status(pillars: tuple[PillarReading, ...], has_house_frame: bool) -> VargaStatus:
    """The D9 confirms/weakens model generalized (house_template._navamsa_status):
    confirms — any pillar vargottama, exalted or own in this varga;
    weakens — any pillar debilitated, or (house-framed vargas) in a 6/8/12 from the
    varga lagna; both or neither -> neutral; no pillar resolvable -> unknown."""
    if not pillars:
        return "unknown"
    confirms = any(p.vargottama or p.dignity in ("exalt", "own") for p in pillars)
    weakens = any(
        p.dignity == "debil"
        or (has_house_frame and p.varga_house is not None and p.varga_house in _DUSTHANA)
        for p in pillars)
    if confirms and not weakens:
        return "confirms"
    if weakens and not confirms:
        return "weakens"
    return "neutral"


def assess_varga(chart: RamanChart, vc: VargaChart, dom: VargaDomain) -> VargaReading:
    """One divisional chart through the four general principles."""
    has_frame = vc.positions and next(iter(vc.positions.values())).house is not None
    lagna_lord = _pillar(chart, vc, vc.lagna_lord, "varga_lagna_lord")
    karakas = tuple(pr for k in dom.karakas
                    if (pr := _pillar(chart, vc, k, "domain_karaka")) is not None)
    pillars = tuple(p for p in (lagna_lord, *karakas) if p is not None)

    notes: list[tuple[str, str]] = []
    if vc.n == 2:
        moon_hora = [n for n in _PLANET_ORDER
                     if n in vc.positions and vc.positions[n].sign == 4]
        sun_hora = [n for n in _PLANET_ORDER
                    if n in vc.positions and vc.positions[n].sign == 5]
        notes.append(("hora_distribution",
                      f"Moon-hora: {','.join(moon_hora) or '-'} | "
                      f"Sun-hora: {','.join(sun_hora) or '-'}"))
        ben_lagna = mal_lagna = ben_kendra = mal_kendra = ()
    else:
        ben_lagna = _occupants(vc, frozenset({1}), NATURAL_BENEFICS)
        mal_lagna = _occupants(vc, frozenset({1}), NATURAL_MALEFICS)
        ben_kendra = _occupants(vc, _KENDRA, NATURAL_BENEFICS)
        mal_kendra = _occupants(vc, _KENDRA, NATURAL_MALEFICS)
    if vc.lagna_vargottama and vc.n == 9:
        notes.append(("vargottama_lagna", "the lagna rises in the same sign in D1 and D9"))

    # The lagna lord may be absent on a sparse Track-B chart; fall back to a bare
    # sign-only pillar so the reading still reports the lord's identity.
    if lagna_lord is None:
        lagna_lord = PillarReading(
            planet=vc.lagna_lord, role="varga_lagna_lord",
            varga_sign=vc.lagna_sign, varga_house=None,
            dignity="neutral", vargottama=False)
        pillars = tuple(p for p in karakas)

    return VargaReading(
        n=vc.n, name=dom.name, domain=dom.domain, related_houses=dom.related_houses,
        chart=vc, lagna_lord=lagna_lord, karakas=karakas,
        benefics_on_lagna=ben_lagna, malefics_on_lagna=mal_lagna,
        benefics_in_kendra=ben_kendra, malefics_in_kendra=mal_kendra,
        status=_status(pillars, bool(has_frame)), notes=tuple(notes),
        source=dom.source)


def build_shodasavarga_report(chart: RamanChart) -> ShodasavargaReport:
    """Cast all 16 divisions and assess each; append the Parijatadi standings."""
    charts = cast_all_vargas(chart)
    readings = tuple(assess_varga(chart, charts[dom.n], dom) for dom in DOMAINS)
    return ShodasavargaReport(readings=readings, vargavisesha=vargavisesha(chart))
