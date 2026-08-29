"""Corroboration — does the birth-chart promise hold up in the divisions and the ashtakavarga?

"The Rasi is the tree, the divisional charts its fruit." A promise read in D1 is corroborated (or
weakened) by the finer lenses, which — per BPHS's precedence — CONFIRM, they never overturn. So every
atom here is CORROBORATION-tier (weight 1): it nudges the convergence, it cannot outvote the birth
chart.

The lenses, each cited to the sloka that assigns the division its use (BPHS-7:48, "use of the 16
divisions"):

  * **Navamsa (D9)** — the universal fruit/sustained lens: the house lord's and karaka's dignity in
    their navamsa. Own/exaltation corroborates the promise; debilitation/enemy weakens it.
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

from app.parashara.doctrine.arudha import FINANCE_SOURCE, UPAPADA_SPOUSE_SOURCE
from app.parashara.doctrine.bhava_karaka import karaka_of
from app.parashara.primitives.ashtakavarga import SAV_BAND_SOURCE
from app.parashara.primitives.relationships import EXALTATION, MOOLATRIKONA, SIGN_LORDS, naisargika
from app.parashara.chart.shodasavarga import DOMAINS_SOURCE
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

    # Matter-specific BPHS corroborations.
    if house == 7:
        out += _upapada_evidence(reading)
    if house in (2, 11):
        out += _finance_evidence(reading, house)
    return out


def _varga_evidence(reading: ParasharaReading, house: int, planet: str, role: str,
                    tag: str, name: str) -> list[Evidence]:
    varga = reading.shodasavarga.get(planet)
    if not varga or tag not in varga:
        return []
    dig = _varga_dignity(planet, varga[tag])
    if dig == 0:
        return []
    return [Evidence(
        topic=house, tier=Tier.CORROBORATION, category="corroboration",
        polarity=Polarity.SUPPORTS if dig > 0 else Polarity.CONTRADICTS,
        rule=f"the {role} {planet} is {'dignified' if dig > 0 else 'weak'} in the {name} ({tag})",
        condition=f"{tag.lower()}_dignity",
        observed=f"{planet} in {tag} sign {varga[tag]} "
                 f"({'own/exalted' if dig > 0 else 'debilitated/enemy'})",
        source=DOMAINS_SOURCE)]


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
        observed=str(getattr(s, "verdict", adj)), source=UPAPADA_SPOUSE_SOURCE)]


def _finance_evidence(reading: ParasharaReading, house: int) -> list[Evidence]:
    f = reading.pada_finance
    if not (f.amplified or f.uninterrupted):
        return []
    return [Evidence(
        topic=house, tier=Tier.CORROBORATION, category="corroboration", polarity=Polarity.SUPPORTS,
        rule="the Arudha-pada finance-reading is strong "
             f"({'amplified' if f.amplified else 'uninterrupted'})",
        condition="pada_finance",
        observed=f"wealth {getattr(f, 'nature', '')} (quantum {getattr(f, 'quantum', '')})".strip(),
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


def _varga_dignity(planet: str, sign: int) -> int:
    """+1 own/exaltation, -1 debilitation/enemy's sign, else 0 — dignity within a division (ch.3)."""
    if planet not in EXALTATION:
        return 0
    if sign == EXALTATION[planet] or SIGN_LORDS.get(sign) == planet:
        return 1
    if sign == ((EXALTATION[planet] - 1 + 6) % 12) + 1:            # debilitation = 7th from exaltation
        return -1
    lord = SIGN_LORDS[sign]
    if planet in MOOLATRIKONA and lord in MOOLATRIKONA and naisargika(planet, lord) == "shatru":
        return -1
    return 0
