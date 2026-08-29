"""Yoga, argala and eighth-house evidence — the reading's detected combinations, wired as testimony.

The engine detects BPHS's named combinations (ch.35-42 yogas, ch.31 argala, ch.44 marakas) but v1's
synthesis never heard them. This module turns each into CORROBORATION- or STRENGTH-tier `Evidence`
on the house(s) the combination classically bears on, under the double-count rule: **one atom per
doctrine family per house** (all fired Dhana yogas are ONE testimony whose `observed` enumerates
them), and a fact never votes twice across families for the same claim.

House attributions, and where each is cited:
  * Pancha Mahapurusha  -> the kendra the yoga occupies (the dataclass carries it).
  * Dhana (ch.41) / Daridra (ch.42) -> houses 2 and 11 as SUPPORTS / CONTRADICTS. NOTE the mapping:
    ch.41's combinations are 5th/9th-lord constructions — the 2/11 attachment rides on ch.11's own
    house significations (wealth at the 2nd, BPHS-11:53; income at the 11th, BPHS-11:131), so each
    atom cites the yoga's own ch.41/42 line and this docstring carries the house-mapping ground.
  * Royal association (ch.40) -> the 10th.
  * Chandra yogas (ch.37): Sunapha/Anapha/Duradhara -> the 1st and 4th (the Moon's own matters);
    Adhi -> the 10th; Kemadruma -> the 1st, CONTRADICTS (the whole-chart negative). The Moon-Dhana
    yoga is NOT wired (the wealth topic already hears ch.41); it stays visible in the yoga section.
  * Special (ch.36): Subha -> the 1st SUPPORTS, Asubha -> the 1st CONTRADICTS. The rest of ch.36
    (Gaja-Kesari, Amala, Parvata, Chamara, Srinatha) stays un-wired for now — visible in the yoga
    section, not yet testimony. Solar yogas (ch.38) are skipped outright: they fire in most charts
    and would be non-differential testimony.
  * Argala (ch.31): a PREVAILING intervention is one atom whose polarity follows the intervening
    planets' nature (argala amplifies what the planet signifies — BPHS never calls it intrinsically
    benefic, cf. the Subhargala note at BPHS-31:110), magnitude worded by Parashara's own 1/2/3+
    scale (BPHS-31:79); an OBSTRUCTED set is one NEUTRAL disclosure ("duly obstructed will go
    astray", BPHS-31:82).
  * The 8th house additionally hears: a maraka planet on/aspecting it (BPHS-44:51) — only marakas
    NOT already voting as functioning malefics (the double-count guard) — and a NEUTRAL disclosure
    of the computed Nisargayu span beside the longevity judgment.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.longevity import ASCENDANT_SOURCE
from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.chart_facts import (
    aspectors, functioning_malefics, occupants, planet_signs)
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier

#: "The Argala unobstructed will be fruitful while the one duly obstructed will go astray."
ARGALA_JUDGMENT_SOURCE: Final[Citation] = Citation("BPHS-31", 82)
#: "the Argala caused by one planet will yield limited effects, by two medium and more than two
#: excellent effects."
ARGALA_MAGNITUDE_SOURCE: Final[Citation] = Citation("BPHS-31", 79)

#: The Sunapha family — benefic lunar support (ch.37 sl.7).
_CHANDRA_GOOD: Final[frozenset[str]] = frozenset({"Sunapha", "Anapha", "Duradhara", "Durudhara"})


def _magnitude(count: int) -> str:
    """Parashara's own argala scale: one planet limited, two medium, more than two excellent."""
    return "limited" if count == 1 else "medium" if count == 2 else "excellent"


def _one_atom(house: int, tier: Tier, polarity: Polarity, family: str, rule: str,
              names: list[str], source: Citation) -> Evidence:
    return Evidence(topic=house, tier=tier, category="corroboration" if tier is Tier.CORROBORATION
                    else "affliction" if polarity is Polarity.CONTRADICTS else "strength",
                    polarity=polarity, rule=rule, condition=family,
                    observed=", ".join(names), source=source)


def gather_yogas(reading: ParasharaReading, house: int) -> list[Evidence]:
    """The detected yogas bearing on `house`, one aggregated atom per family (see module doc)."""
    out: list[Evidence] = []

    maha = [y for y in reading.mahapurusha if y.house == house]
    if maha:
        out.append(_one_atom(
            house, Tier.CORROBORATION, Polarity.SUPPORTS, "mahapurusha",
            "a Pancha Mahapurusha yoga occupies this kendra",
            [f"{y.name} ({y.planet}, {y.dignity})" for y in maha], maha[0].source))

    if house in (2, 11):
        if reading.dhana_yogas:
            out.append(_one_atom(
                house, Tier.CORROBORATION, Polarity.SUPPORTS, "dhana_yogas",
                "wealth combinations fire (ch.41) — attached to the wealth houses per ch.11",
                [y.name for y in reading.dhana_yogas], reading.dhana_yogas[0].source))
        if reading.daridra_yogas:
            out.append(_one_atom(
                house, Tier.CORROBORATION, Polarity.CONTRADICTS, "daridra_yogas",
                "penury combinations fire (ch.42) — the wealth houses' cited negative",
                [y.name for y in reading.daridra_yogas], reading.daridra_yogas[0].source))

    if house == 10 and reading.royal_yogas:
        out.append(_one_atom(
            house, Tier.CORROBORATION, Polarity.SUPPORTS, "royal_yogas",
            "royal-association combinations fire (ch.40)",
            [y.name for y in reading.royal_yogas], reading.royal_yogas[0].source))

    good = [y for y in reading.chandra_yogas if y.name in _CHANDRA_GOOD]
    if house in (1, 4) and good:
        out.append(_one_atom(
            house, Tier.CORROBORATION, Polarity.SUPPORTS, "chandra_support",
            "benefic lunar yogas support the Moon's matters (ch.37)",
            [y.name for y in good], good[0].source))
    adhi = [y for y in reading.chandra_yogas if y.name.startswith("Adhi")]
    if house == 10 and adhi:
        out.append(_one_atom(
            house, Tier.CORROBORATION, Polarity.SUPPORTS, "adhi_yoga",
            "Adhi yoga — benefics in the 6th/7th/8th from the Moon confer status (ch.37)",
            [y.name for y in adhi], adhi[0].source))
    kema = [y for y in reading.chandra_yogas if y.name == "Kemadruma"]
    if house == 1 and kema:
        out.append(_one_atom(
            house, Tier.CORROBORATION, Polarity.CONTRADICTS, "kemadruma",
            "Kemadruma — the Moon left bare of company (ch.37), the lunar negative",
            [y.name for y in kema], kema[0].source))

    if house == 1:
        subha = [y for y in reading.special_yogas if y.name == "Subha"]
        asubha = [y for y in reading.special_yogas if y.name == "Asubha"]
        if subha:
            out.append(_one_atom(house, Tier.CORROBORATION, Polarity.SUPPORTS, "subha",
                                 "Subha — benefic support around the ascendant (ch.36)",
                                 [y.reason for y in subha], subha[0].source))
        if asubha:
            out.append(_one_atom(house, Tier.CORROBORATION, Polarity.CONTRADICTS, "asubha",
                                 "Asubha — malefic presence around the ascendant (ch.36)",
                                 [y.reason for y in asubha], asubha[0].source))
    return out


def gather_argala(reading: ParasharaReading, house: int) -> list[Evidence]:
    """The ch.31 interventions on `house`: one atom for the prevailing set, one disclosure for the
    obstructed set. Polarity follows the intervening planets' nature (argala amplifies)."""
    argalas = reading.argala.get(house, ())
    if not argalas:
        return []
    malefics = functioning_malefics(reading.chart)
    out: list[Evidence] = []

    prevailing = [a for a in argalas if a.prevails]
    if prevailing:
        planets = [p for a in prevailing for p in a.argala_planets]
        n_mal = sum(1 for p in planets if p in malefics)
        n_ben = len(planets) - n_mal
        polarity = (Polarity.SUPPORTS if n_ben > n_mal
                    else Polarity.CONTRADICTS if n_mal > n_ben else Polarity.NEUTRAL)
        vip = any(a.vipareeta for a in prevailing)
        out.append(Evidence(
            topic=house, tier=Tier.CORROBORATION, category="corroboration", polarity=polarity,
            rule=f"unobstructed argala intervenes ({_magnitude(len(planets))} — "
                 f"{len(planets)} planet{'s' if len(planets) != 1 else ''}, BPHS-31:79)"
                 + ("; a vipareeta argala among them is itself favourable" if vip else ""),
            condition="argala_prevails",
            observed="; ".join(f"from the {a.argala_house}th: {', '.join(a.argala_planets)}"
                               for a in prevailing),
            source=ARGALA_JUDGMENT_SOURCE))

    obstructed = [a for a in argalas if not a.prevails]
    if obstructed:
        out.append(Evidence(
            topic=house, tier=Tier.CORROBORATION, category="corroboration",
            polarity=Polarity.NEUTRAL,
            rule="argala duly obstructed — 'will go astray' (disclosed, no vote)",
            condition="argala_obstructed",
            observed="; ".join(
                f"from the {a.argala_house}th ({', '.join(a.argala_planets)}) obstructed by "
                f"{', '.join(a.obstructor_planets)}" for a in obstructed),
            source=ARGALA_JUDGMENT_SOURCE))
    return out


def gather_eighth_extras(reading: ParasharaReading) -> list[Evidence]:
    """The 8th house's own extras: maraka touch (double-count-guarded) + the span disclosure."""
    chart = reading.chart
    signs = planet_signs(chart)
    malefics = functioning_malefics(chart, signs=signs)
    out: list[Evidence] = []

    on_eighth = set(occupants(chart, 8, signs=signs)) | set(aspectors(chart, 8, signs=signs))
    touching = [m for m in reading.maraka_planets
                if m.planet in on_eighth and m.planet not in malefics]
    if touching:
        out.append(Evidence(
            topic=8, tier=Tier.STRENGTH, category="affliction", polarity=Polarity.CONTRADICTS,
            rule="a maraka planet touches the house of longevity (its periods are the classically "
                 "sensitive ones)",
            condition="maraka_touch",
            observed="; ".join(f"{m.planet} — {m.reason}" for m in touching),
            source=touching[0].source))

    nf = reading.nisargayu_full
    out.append(Evidence(
        topic=8, tier=Tier.CORROBORATION, category="corroboration", polarity=Polarity.NEUTRAL,
        rule="the computed natural span, disclosed beside the longevity judgment (BPHS's own "
             "band-to-period rule is nakshatra-tara based — Vipat/Pratyak/Vadha, BPHS-44:182 — "
             "not maraka-lord based)",
        condition="nisargayu_span",
        observed=f"complete Nisargayu {nf.total_years:.1f} years "
                 f"(planetary {nf.planetary_years:.1f} + ascendant {nf.ascendant_years:.1f})",
        source=ASCENDANT_SOURCE))
    return out
