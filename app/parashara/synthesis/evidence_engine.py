"""Gather the birth-chart evidence for a bhava — PROMISE, STRENGTH, AFFLICTION.

These are the three "evidence engines" of the architecture, over the birth chart (D1). They reuse
what the reading already computed and cited, re-expressed as `Evidence` atoms so the convergence and
audit layers have a uniform, traceable substrate:

  * **PROMISE / AFFLICTION (the birth-chart verdict)** come straight from ch.11's own
    prosperity/annihilation judgment (`reading.bhavas`): each fired prosperity condition is a
    SUPPORTS testimony, each fired annihilation condition a CONTRADICTS one — carrying its
    `antidoted` flag verbatim, so ch.11's cancellation logic (the lord's aspect, a dusthana-lord's
    relief) flows through untouched. These are PROMISE-tier: ch.11 IS Parashara's weighed house
    verdict, so it — and it alone — settles denied-vs-granted.
  * **STRENGTH (delivery & obstruction)** reads what modulates that promise: the significators'
    delivery capacity — the house lord's and karaka's Shadbala against Parashara's required minimum
    (ch.27) and their Vimsopaka band (ch.7) — AND the plain affliction ch.11 does not enumerate, a
    natural malefic occupying or aspecting the house. These are STRENGTH-tier by deliberate design:
    malefic drishti is ubiquitous (three malefics each aspect several houses) and non-differential,
    so counting it as PROMISE-tier would deny almost every house — exactly the "abundant affliction"
    trap. As delivery-tier evidence it makes a promised matter *difficult*, never *denied*.

Every atom keeps the citation its source primitive already held, so nothing here transcribes doctrine
text — it only re-keys already-cited facts into evidence.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.judges.richer_bhava import REQUIRED_SHADBALA, SHADBALA_SOURCE
from app.parashara.primitives.functional_nature import SOURCE as MALEFIC_SOURCE
from app.parashara.primitives.graha_drishti import SOURCE as DRISHTI_SOURCE
from app.parashara.primitives.deeptadi_avastha import SOURCE as DEEPTADI_SOURCE
from app.parashara.primitives.lajjitadi_avastha import DESTROYED_SOURCE
from app.parashara.doctrine.functional_by_lagna import YOGAKARAKA_SOURCE
from app.parashara.doctrine.bhava_karaka import karaka_of
from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.chart_facts import (
    aspectors, functioning_malefics, house_lord, occupants, planet_signs)
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier

#: BPHS-11 (notes to sl.16): "If a malefic relation is there for a bhava, its lord's aspect on it
#: is an antidote." The lord's own aspect is PROTECTION — it must never vote as affliction.
LORD_ANTIDOTE_SOURCE: Final[Citation] = Citation("BPHS-11", 208)

#: Upachaya bhavas — malefics grow strong here rather than afflict (classical; a deliberate softening
#: so a malefic in the 3rd/6th/10th/11th is disclosed but does not vote as an affliction).
# ponytail: upachaya softening is coarse (NEUTRAL, not a favourable vote); refine to a graded
# malefic-benefit reading if a chart ever needs it.
_UPACHAYA: Final[frozenset[int]] = frozenset({3, 6, 10, 11})

_ORD: Final[dict[int, str]] = {
    1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
    7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}


def gather_promise(reading: ParasharaReading, house: int) -> list[Evidence]:
    """The ch.11 prosperity (SUPPORTS) and annihilation (CONTRADICTS) testimonies for the bhava."""
    bv = reading.bhavas[house]
    out: list[Evidence] = []
    for c in bv.prosperity:
        if c.fired:
            out.append(Evidence(
                topic=house, tier=Tier.PROMISE, category="promise", polarity=Polarity.SUPPORTS,
                rule=c.note, condition=c.key, observed=c.note, source=c.source))
    for c in bv.annihilation:
        if c.fired:
            out.append(Evidence(
                topic=house, tier=Tier.PROMISE, category="affliction", polarity=Polarity.CONTRADICTS,
                rule=c.note, condition=c.key, observed=c.note, source=c.source,
                antidoted=c.antidoted))
    return out


def gather_affliction(reading: ParasharaReading, house: int) -> list[Evidence]:
    """Plain affliction ch.11 does not enumerate: a malefic ON or ASPECTING the bhava.

    The malefic set is the CHART's (BPHS-3:187 makes the waning Moon and malefic-joined Mercury
    malefic — `functioning_malefics`), and the bhava's OWN LORD is exempt: its occupancy is ch.11's
    Prabuddha prosperity condition, and its aspect is ch.11's antidote (BPHS-11:208) — counting
    either as affliction would contradict the very doctrine this layer cites.
    """
    chart = reading.chart
    signs = planet_signs(chart)
    malefics = functioning_malefics(chart, signs=signs)
    lord = house_lord(chart.asc_sign, house)
    ordinal = _ORD[house]
    out: list[Evidence] = []

    yogakarakas = frozenset(reading.yogakarakas)

    for m in occupants(chart, house, signs=signs):
        if m not in malefics or m == lord:
            continue                    # own lord occupying = ch.11 prosperity, never affliction
        if m in yogakarakas:
            # A yogakaraka (kendra + trikona lord, BPHS-34:90) does not afflict — disclosed, no vote.
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="affliction", polarity=Polarity.NEUTRAL,
                rule=f"{m}, though a natural malefic, is this lagna's yogakaraka — "
                     "its presence is not counted as affliction",
                condition="yogakaraka_exempt",
                observed=f"{m} (yogakaraka) occupies the {ordinal} bhava",
                source=YOGAKARAKA_SOURCE))
            continue
        # A malefic thrives in an upachaya — disclose it, but do not count it against the promise.
        neutral = house in _UPACHAYA
        out.append(Evidence(
            topic=house, tier=Tier.STRENGTH, category="affliction",
            polarity=Polarity.NEUTRAL if neutral else Polarity.CONTRADICTS,
            rule=f"the malefic {m} occupies the house"
                 + (" (an upachaya — tolerated)" if neutral else ""),
            condition="malefic_occupant",
            observed=f"{m} occupies the {ordinal} bhava", source=MALEFIC_SOURCE))

    for g in aspectors(chart, house, signs=signs):
        if g not in malefics:
            continue
        if g == lord:
            # The lord's aspect on its own bhava is the ANTIDOTE (BPHS-11:208): disclosed, no vote.
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="affliction", polarity=Polarity.NEUTRAL,
                rule=f"{g}, though a malefic, is the house's own lord — "
                     "its aspect is the antidote, not an affliction",
                condition="own_lord_aspect",
                observed=f"{g} (lord of the {ordinal}) aspects its own bhava",
                source=LORD_ANTIDOTE_SOURCE))
            continue
        if g in yogakarakas:
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="affliction", polarity=Polarity.NEUTRAL,
                rule=f"{g}, though a natural malefic, is this lagna's yogakaraka — "
                     "its aspect is not counted as affliction",
                condition="yogakaraka_exempt",
                observed=f"{g} (yogakaraka) aspects the {ordinal} bhava",
                source=YOGAKARAKA_SOURCE))
            continue
        out.append(Evidence(
            topic=house, tier=Tier.STRENGTH, category="affliction", polarity=Polarity.CONTRADICTS,
            rule=f"the malefic {g} aspects the house", condition="malefic_aspect",
            observed=f"{g} casts a full aspect on the {ordinal} bhava", source=DRISHTI_SOURCE))
    return out


def gather_avastha(reading: ParasharaReading, house: int) -> list[Evidence]:
    """Occupant avastha testimony (ch.45): the destroyed-house clause and the Deeptadi state.

    Two distinct doctrines about an occupant, so up to two atoms per occupant (the double-count
    rule permits distinct doctrines; each FAMILY stays one atom per occupant):
      * Kshudita/Kshobhita — "the houses occupied by a planet in Kshuditavastha or Kshobhitavastha
        are destroyed" (BPHS-45:165). STRENGTH-tier by the same frequency guard that demoted
        malefic drishti (Kshudita fires on any Saturn conjunction); the sloka's word is kept
        verbatim in the rule text.
      * Deeptadi — a bright occupant (Deepta/Swastha) strengthens the bhava it sits in; a spoiled
        one (Khala, or Vikala/Kopa) weakens it (BPHS-45:113).
    """
    chart = reading.chart
    signs = planet_signs(chart)
    ordinal = _ORD[house]
    out: list[Evidence] = []
    for occ in occupants(chart, house, signs=signs):
        av = reading.avasthas.get(occ)
        if av is None:
            continue
        if av.lajjitadi_destroys_house:
            states = [s for s in av.lajjitadi if s in ("Kshudita", "Kshobhita")]
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="affliction",
                polarity=Polarity.CONTRADICTS,
                rule=f"{occ} occupies in {'/'.join(states)}avastha — 'the houses occupied ... "
                     "are destroyed'",
                condition="lajjitadi_destroys",
                observed=f"{occ} in the {ordinal} bhava holds {', '.join(states)}",
                source=DESTROYED_SOURCE))
        if av.deeptadi in ("Deepta", "Swastha"):
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="strength", polarity=Polarity.SUPPORTS,
                rule=f"{occ} occupies in {av.deeptadi}avastha (a bright state)",
                condition="deeptadi_state",
                observed=f"{occ} {av.deeptadi} in the {ordinal} bhava", source=DEEPTADI_SOURCE))
        elif av.deeptadi == "Khala" or av.deeptadi_vikala or av.deeptadi_kopa:
            spoil = ("Khala" if av.deeptadi == "Khala"
                     else "Vikala" if av.deeptadi_vikala else "Kopa")
            out.append(Evidence(
                topic=house, tier=Tier.STRENGTH, category="affliction",
                polarity=Polarity.CONTRADICTS,
                rule=f"{occ} occupies in {spoil}avastha (a spoiled state)",
                condition="deeptadi_state",
                observed=f"{occ} {spoil} in the {ordinal} bhava", source=DEEPTADI_SOURCE))
    return out


def gather_strength(reading: ParasharaReading, house: int) -> list[Evidence]:
    """The significators' delivery strength — the lord's and karaka's Shadbala + Vimsopaka."""
    lord = house_lord(reading.chart.asc_sign, house)
    karaka = karaka_of(house)
    out = _strength_for(reading, house, lord, "lord")
    if karaka != lord:
        out += _strength_for(reading, house, karaka, "karaka")
    return out


def _strength_for(reading: ParasharaReading, house: int, planet: str, role: str) -> list[Evidence]:
    out: list[Evidence] = []
    ps = reading.shadbala.get(planet)
    req = REQUIRED_SHADBALA.get(planet)
    if ps is not None and req is not None:
        strong = ps.rupas >= req
        out.append(Evidence(
            topic=house, tier=Tier.STRENGTH, category="strength",
            polarity=Polarity.SUPPORTS if strong else Polarity.CONTRADICTS,
            rule=(f"the {role} {planet} has its required Shadbala" if strong
                  else f"the {role} {planet} is short of its required Shadbala"),
            condition="shadbala_vs_required",
            observed=f"{planet} {ps.rupas:.2f} rupas vs {req} required",
            source=SHADBALA_SOURCE))
    vs = reading.vimsopaka.get(planet)
    if vs is not None and vs.band in ("wholly-favourable", "inauspicious"):
        supports = vs.band == "wholly-favourable"
        out.append(Evidence(
            topic=house, tier=Tier.STRENGTH, category="strength",
            polarity=Polarity.SUPPORTS if supports else Polarity.CONTRADICTS,
            rule=f"the {role} {planet}'s Vimsopaka is {vs.band}", condition="vimsopaka_band",
            observed=f"{planet} Vimsopaka {vs.score:.1f}/20 ({vs.band})",
            source=vs.source))
    return out
