"""Corroboration — does the birth-chart promise hold up in the divisions and the ashtakavarga?

A promise read in D1 is corroborated (or weakened) by the finer lenses. That the divisions CONFIRM
rather than overturn is this layer's architectural convention (see `evidence.py` — the commentarial
"tree and its fruit" maxim is NOT in the BPHS corpus, and BPHS-7:62-66 in fact lets a lord's D60/D16
placement diminish/flourish a bhava directly). So every atom here is CORROBORATION-tier (weight 1):
it nudges the convergence, it cannot outvote the birth chart.

The lenses, each cited to the sloka that assigns the division its use (BPHS-7:48, "use of the 16
divisions"):

  * **Navamsa (D9)** — the house lord's and karaka's dignity in their navamsa. Own/exaltation
    corroborates the promise; debilitation/enemy weakens it. Reading D9 for EVERY house is
    practice-convention, disclosed: BPHS-7's own table assigns the Navamsa to the spouse.
  * **Dasamsa (D10)** — the career lens, added for the 10th house: the karaka's D10 dignity.
  * **Sarvashtakavarga** — the house sign's bindus (BPHS-72:53 bands): a favourable band corroborates,
    an adverse band weakens.
  * **Matter-specific BPHS methods**, where Parashara gives one: the Upapada spouse-reading for
    marriage (BPHS-30:7-12) and the Arudha-pada finance-reading for wealth (BPHS-29:8-15). These are
    already-cited BPHS conclusions the reading computes; here they corroborate their matter.

Deferred honestly: a *general* Arudha-Lagna corroboration for every house. BPHS gives the Arudha
method matter-by-matter (marriage, finance — wired above), not as a uniform per-house lens; a
general "kendra/kona from the Arudha Lagna" rule is Jaimini idiom, so it is not forced into this
BPHS-root layer. Reopen if a BPHS per-house arudha rule is located.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.arudha import FINANCE_SOURCE, UPAPADA_SPOUSE_SOURCE
from app.parashara.doctrine.bhava_karaka import karaka_of
from app.parashara.doctrine.sources import Citation
from app.parashara.doctrine.vargottama import SOURCE as VARGOTTAMA_SOURCE
from app.parashara.chart.sudarshana import SOURCE as SUDARSHANA_SOURCE
from app.parashara.primitives.ashtakavarga import SAV_BAND_SOURCE
from app.parashara.primitives.relationships import SIGN_LORDS, dignity_in_sign
from app.parashara.chart.shodasavarga import DOMAINS_SOURCE
from app.parashara.synthesis.chart_facts import functioning_malefics, occupants, planet_signs

#: "The bhava whose lord is in a malefic Shashtiamsa will diminish ... The bhava whose lord is in
#: a benefic Shodasamsa (or Kalamsa) flourish." — BPHS's own per-bhava divisional rule, the
#: strongest cited warrant for divisional corroboration in ch.7.
VARGA_DECIDES_SOURCE: Final[Citation] = Citation("BPHS-7", 62)

#: BPHS-7's own matter-varga table (sl.1-8, lines 49-62): the division each house's matter is read
#: from, cited to the line the assignment lands on. D24 (learning) is skipped — no single house
#: carries it cleanly. The universal D9 lens (above) remains practice-convention.
_MATTER_VARGA: Final[dict[int, tuple[tuple[str, str, int], ...]]] = {
    2: (("D2", "Hora — wealth", 50),),
    4: (("D4", "Chaturthamsa — fortunes", 54), ("D12", "Dvadasamsa — parents", 56)),
    5: (("D7", "Saptamsa — sons and grandsons", 54),),
    6: (("D30", "Trimsamsa — evil effects", 59),),
    8: (("D30", "Trimsamsa — evil effects", 59),),
    9: (("D12", "Dvadasamsa — parents", 56),),
    12: (("D30", "Trimsamsa — evil effects", 59),),
}

#: Sign-lord nature for the D16/D60 amsa rule — a labeled convention (benefic lords Jupiter/Venus/
#: Mercury/Moon vs malefic lords Sun/Mars/Saturn).
# ponytail: amsa nature by sign-lord; upgrade path = the ch.3 Shashtiamsa deity table (benevolent
# vs cruel amsas by name) if a chart ever turns on the difference.
_BENEFIC_LORDS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.chart_facts import house_lord, house_sign
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier


def gather_corroboration(reading: ParasharaReading, house: int) -> list[Evidence]:
    """The divisional / ashtakavarga / matter-specific corroboration for the bhava (all CORROB-tier)."""
    out: list[Evidence] = []
    lord = house_lord(reading.chart.asc_sign, house)
    karaka = karaka_of(house)

    # D9 — the fruit lens, for the lord and the karaka.
    for planet, role in _distinct((lord, "lord"), (karaka, "karaka")):
        out += _varga_evidence(reading, house, planet, role, "D9", "Navamsa")
    # D10 — career lens, added for the 10th house.
    if house == 10:
        out += _varga_evidence(reading, house, karaka, "karaka", "D10", "Dasamsa")

    # Sarvashtakavarga — the house sign's bindus (BPHS-72 bands; same cutoffs as richer_bhava).
    bindus = reading.sav.get(house_sign(reading.chart.asc_sign, house))
    if bindus is not None and (bindus > 30 or bindus < 25):
        favourable = bindus > 30
        out.append(Evidence(
            topic=house, tier=Tier.CORROBORATION, category="corroboration",
            polarity=Polarity.SUPPORTS if favourable else Polarity.CONTRADICTS,
            rule=f"the house holds {bindus} Sarvashtakavarga bindus "
                 f"({'a favourable' if favourable else 'an adverse'} band)",
            condition="sav_band", observed=f"{bindus} SAV bindus in the house sign",
            source=SAV_BAND_SOURCE))

    # BPHS-7's own matter-vargas for this house (the table the chapter itself gives).
    for tag, gloss, line in _MATTER_VARGA.get(house, ()):
        for planet, role in _distinct((lord, "lord"), (karaka, "karaka")):
            out += _varga_evidence(reading, house, planet, role, tag, gloss.split(" — ")[0],
                                   source=Citation("BPHS-7", line))

    # BPHS-7:62-66 — the per-bhava D60/D16 rule (the lord's amsa decides diminish/flourish).
    out += _d60_d16_evidence(reading, house, lord)

    # Vargottama lord/karaka — same sign in D1 and D9 (Saravali, allied — marked in the rule).
    for planet, role in _distinct((lord, "lord"), (karaka, "karaka")):
        if planet in reading.vargottama:
            out.append(Evidence(
                topic=house, tier=Tier.CORROBORATION, category="corroboration",
                polarity=Polarity.SUPPORTS,
                rule=f"the {role} {planet} is Vargottama (Saravali — allied source)",
                condition="vargottama",
                observed=f"{planet} holds the same sign in D1 and D9", source=VARGOTTAMA_SOURCE))

    # Sudarshana — an occupant confirmed in the SAME house from Lagna, Moon and Sun (ch.74).
    out += _sudarshana_evidence(reading, house)

    # Matter-specific BPHS corroborations.
    if house == 7:
        out += _upapada_evidence(reading)
    if house in (2, 11):
        out += _finance_evidence(reading, house)
    return out


def _d60_d16_evidence(reading: ParasharaReading, house: int, lord: str) -> list[Evidence]:
    """BPHS-7:62-66: lord in a malefic-lorded Shashtiamsa -> the bhava diminishes; in a
    benefic-lorded Shodasamsa -> it flourishes. Asymmetric by the sloka's own wording."""
    varga = reading.shodasavarga.get(lord)
    if not varga:
        return []
    out: list[Evidence] = []
    d16 = varga.get("D16")
    if d16 is not None and SIGN_LORDS[d16] in _BENEFIC_LORDS:
        out.append(Evidence(
            topic=house, tier=Tier.CORROBORATION, category="corroboration",
            polarity=Polarity.SUPPORTS,
            rule=f"the lord {lord} sits in a benefic Shodasamsa — 'the bhava ... flourish' "
                 "(amsa nature by sign-lord, a labeled convention)",
            condition="d16_flourish",
            observed=f"{lord} D16 sign {d16} (lord {SIGN_LORDS[d16]})",
            source=VARGA_DECIDES_SOURCE))
    d60 = varga.get("D60")
    if d60 is not None and SIGN_LORDS[d60] not in _BENEFIC_LORDS:
        out.append(Evidence(
            topic=house, tier=Tier.CORROBORATION, category="corroboration",
            polarity=Polarity.CONTRADICTS,
            rule=f"the lord {lord} sits in a malefic Shashtiamsa — 'the bhava ... will diminish' "
                 "(amsa nature by sign-lord, a labeled convention)",
            condition="d60_diminish",
            observed=f"{lord} D60 sign {d60} (lord {SIGN_LORDS[d60]})",
            source=VARGA_DECIDES_SOURCE))
    return out


def _sudarshana_evidence(reading: ParasharaReading, house: int) -> list[Evidence]:
    """One atom when occupants of `house` read as the SAME house from all three lagnas (ch.74):
    benefic-majority confirmation supports, malefic-majority weighs against."""
    chart = reading.chart
    signs = planet_signs(chart)
    confirmed = [b for b in occupants(chart, house, signs=signs)
                 if (p := reading.sudarshana.get(b)) is not None
                 and p.from_lagna == p.from_moon == p.from_sun == house]
    if not confirmed:
        return []
    malefics = functioning_malefics(chart, signs=signs)
    n_mal = sum(1 for b in confirmed if b in malefics)
    n_ben = len(confirmed) - n_mal
    polarity = (Polarity.SUPPORTS if n_ben > n_mal
                else Polarity.CONTRADICTS if n_mal > n_ben else Polarity.NEUTRAL)
    kind = "benefic" if n_ben > n_mal else "malefic" if n_mal > n_ben else "mixed"
    return [Evidence(
        topic=house, tier=Tier.CORROBORATION, category="corroboration", polarity=polarity,
        rule=f"the Sudarshana confirms {kind} occupancy — the same house from Lagna, Moon and Sun",
        condition="sudarshana_confirmed",
        observed=", ".join(confirmed), source=SUDARSHANA_SOURCE)]


def _varga_evidence(reading: ParasharaReading, house: int, planet: str, role: str,
                    tag: str, name: str, *, source: Citation = DOMAINS_SOURCE) -> list[Evidence]:
    varga = reading.shodasavarga.get(planet)
    if not varga or tag not in varga:
        return []
    dig = dignity_in_sign(planet, varga[tag])
    if dig == 0:
        return []
    return [Evidence(
        topic=house, tier=Tier.CORROBORATION, category="corroboration",
        polarity=Polarity.SUPPORTS if dig > 0 else Polarity.CONTRADICTS,
        rule=f"the {role} {planet} is {'dignified' if dig > 0 else 'weak'} in the {name} ({tag})",
        condition=f"{tag.lower()}_dignity",
        observed=f"{planet} in {tag} sign {varga[tag]} "
                 f"({'own/exalted' if dig > 0 else 'debilitated/enemy'})",
        source=source)]


def _upapada_evidence(reading: ParasharaReading) -> list[Evidence]:
    s = reading.spouse_from_upapada
    if s.afflicted and not s.excellent:
        pol, adj = Polarity.CONTRADICTS, "afflicted"
    elif s.excellent or s.benefic_related:
        pol, adj = Polarity.SUPPORTS, "well-supported"
    else:
        return []
    return [Evidence(
        topic=7, tier=Tier.CORROBORATION, category="corroboration", polarity=pol,
        rule=f"the Upapada spouse-reading is {adj}", condition="upapada",
        observed=s.verdict, source=UPAPADA_SPOUSE_SOURCE)]


def _finance_evidence(reading: ParasharaReading, house: int) -> list[Evidence]:
    f = reading.pada_finance
    if not (f.amplified or f.uninterrupted):
        return []
    return [Evidence(
        topic=house, tier=Tier.CORROBORATION, category="corroboration", polarity=Polarity.SUPPORTS,
        rule="the Arudha-pada finance-reading is strong "
             f"({'amplified' if f.amplified else 'uninterrupted'})",
        condition="pada_finance",
        observed=f"wealth {f.nature} (quantum {f.quantum})",
        source=FINANCE_SOURCE)]


def _distinct(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    """De-duplicate (planet, role) pairs by planet, keeping the first role."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for planet, role in pairs:
        if planet not in seen:
            seen.add(planet)
            out.append((planet, role))
    return out
