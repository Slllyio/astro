"""Bhava prosperity — Parashara's own house-judgment method (BPHS ch.11, slokas 14-16).

This is the Parashara engine's verdict spine. It is deliberately NOT Raman's `_decide`: it is the
scheme BPHS ch.11 states in its own words, with the antidote clauses Parashara attaches to it.

## Prosperity — "the wellbeing of a house is assured" (BPHS-11:14)
    (a) the house contains a benefic
    (b) the house is aspected by a benefic
    (c) its lord is in Kumaravastha or Yuvavastha (Baladi avastha, ch.45)
    (d) its lord is in own sign or exaltation (Prabuddha/Jagrad avastha)
    (e) its lord is placed in the 10th from the ascendant

## Annihilation — "conditions under which a house suffers" (BPHS-11:16), each with its antidote
    (a) the bhava is UNASPECTED by its own lord — but "this does not mean the bhava suffers
        annihilation ... can look upto alternative sources". So standalone this is MILD (it merely
        withholds a help), not an annihilation. Its real role is the converse: the lord's aspect
        IS the antidote to a malefic relation (b/c).
    (b) the lord joins a malefic — mitigated if that malefic is friendly to the lord, or they join
        in a favourable house, or the malefic is exalted.
    (c) the lord conjoins a lord of the 6th/8th/12th — but "if he himself is an evil lord, then
        some relief can be expected" (the bhava lord already being a dusthana lord).
        NOTE on the evil-lord set: the printed sloka reads "lords of evil and such other houses
        (i.e. 3rd, 6th, 8th, 11th and 12th)" (BPHS-11:152-153); the translator's notes narrow it
        to the 6th/8th/12th (BPHS-11:218-219), and this module deliberately follows the notes —
        the classical dusthana set. A doctrine-contested reading, labeled here (2026-08-29).
    (d) the lord is defeated in a planetary war (graha yuddha) — "its bhava's potence is void".
    (e) the lord is in Vriddhavastha or Mritavastha (Baladi avastha, ch.45).

## The net verdict
Parashara gives conditions, not weights, so the combination stays transparent: count the prosperity
conditions that hold, and the annihilation conditions that hold AND are not antidoted; the larger
side wins, a tie (including nothing firing) is `ordinary`. The full fired/antidoted breakdown is
returned so a reading shows its working rather than a bare label. This is honest to the text — it
invents no weighting Parashara does not give — while remaining a single reproducible rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

from app.parashara.doctrine.sources import Citation

Verdict = Literal["flourishing", "ordinary", "annihilated"]

# Line numbers into chapter_011_*.md (NOT sloka numbers — sloka 14-16 sits at line 147+; the
# frontmatter occupies the first ~17 lines, so citing 14/16 would resolve into YAML. Caught by the
# doctrine audit, 2026-08-22).
PROSPERITY_SOURCE: Final[Citation] = Citation("BPHS-11", 147)      # "PROSPERITY OR ANNIHILATION..."
ANNIHILATION_SOURCE: Final[Citation] = Citation("BPHS-11", 151)    # "The bhava which is not aspected..."
SUPTA_SOURCE: Final[Citation] = Citation("BPHS-11", 158)           # the three killing Avasthas named


@dataclass(frozen=True)
class BhavaFactors:
    """Everything ch.11's conditions need about ONE bhava. Booleans are stated as facts about the
    chart; the judge applies Parashara's logic to them."""
    house: int
    # prosperity
    benefic_occupant: bool                 # (P-a) a benefic sits in the house
    benefic_aspect: bool                   # (P-b) a benefic aspects the house
    lord_avastha: str                      # bala|kumara|yuva|vriddha|mrita (feeds P-c and A-e)
    lord_own_or_exalt: bool                # (P-d) lord in own sign or exaltation
    lord_in_tenth: bool                    # (P-e) lord in the 10th from lagna
    # annihilation
    lord_aspects_bhava: bool               # (A-a) lord aspects its own bhava (the antidote-giver)
    lord_conjunct_malefic: bool            # (A-b) lord joined by a malefic
    lord_malefic_conjunction_mitigated: bool = False   # (A-b antidote) friendly / favourable / exalted
    lord_conjunct_dusthana_lord: bool = False          # (A-c) lord joins a 6/8/12 lord
    lord_is_itself_dusthana_lord: bool = False         # (A-c antidote) lord already a 6/8/12 lord
    lord_defeated_in_war: bool = False                 # (A-d) graha yuddha loss
    lord_in_supta: bool = False                        # (A-f) Suptavastha: lord debilitated or in
                                                       # an enemy's sign (BPHS-11:158, defined :271)


@dataclass(frozen=True)
class FiredCondition:
    key: str
    fired: bool
    antidoted: bool
    note: str
    source: Citation


@dataclass(frozen=True)
class BhavaVerdict:
    house: int
    verdict: Verdict
    prosperity: tuple[FiredCondition, ...]
    annihilation: tuple[FiredCondition, ...]
    net_prosperity: int          # prosperity conditions that hold
    net_annihilation: int        # annihilation conditions that hold and are NOT antidoted

    @property
    def reasons(self) -> tuple[str, ...]:
        """Human-readable fired reasons, prosperity then annihilation, antidotes marked."""
        out = [f"+ {c.note}" for c in self.prosperity if c.fired]
        out += [f"- {c.note}" + (" (antidoted)" if c.antidoted else "")
                for c in self.annihilation if c.fired]
        return tuple(out)


def judge_prosperity(f: BhavaFactors) -> BhavaVerdict:
    """Apply BPHS ch.11 sl.14-16 to one bhava's factors. Pure doctrine — no chart mechanics."""
    p: list[FiredCondition] = [
        FiredCondition("benefic_occupant", f.benefic_occupant, False,
                       "a benefic occupies the house", PROSPERITY_SOURCE),
        FiredCondition("benefic_aspect", f.benefic_aspect, False,
                       "a benefic aspects the house", PROSPERITY_SOURCE),
        FiredCondition("lord_in_kumara_or_yuva", f.lord_avastha in ("kumara", "yuva"), False,
                       f"the lord is in {f.lord_avastha}avastha (a flourishing age-state)",
                       PROSPERITY_SOURCE),
        FiredCondition("lord_own_or_exalt", f.lord_own_or_exalt, False,
                       "the lord is in its own sign or exaltation (Prabuddha)", PROSPERITY_SOURCE),
        FiredCondition("lord_in_tenth", f.lord_in_tenth, False,
                       "the lord is in the 10th from the ascendant", PROSPERITY_SOURCE),
    ]

    # (A-b) malefic conjunction — antidoted if friendly/favourable/exalted, OR if the lord aspects
    # its own bhava (BPHS-11:16a: the lord's aspect is the antidote to a malefic relation).
    b_antidote = f.lord_malefic_conjunction_mitigated or f.lord_aspects_bhava
    # (A-c) dusthana-lord conjunction — antidoted if the bhava lord is itself an evil lord ("some
    # relief"), or again by the lord's own aspect.
    c_antidote = f.lord_is_itself_dusthana_lord or f.lord_aspects_bhava

    a: list[FiredCondition] = [
        # (A-a) unaspected by lord: fired for the record, but ALWAYS "antidoted" (mild) — Parashara
        # is explicit it is not itself annihilation. It never counts toward net_annihilation.
        FiredCondition("unaspected_by_lord", not f.lord_aspects_bhava, True,
                       "the lord does not aspect its own house (weakening, not fatal)",
                       ANNIHILATION_SOURCE),
        FiredCondition("lord_conjunct_malefic", f.lord_conjunct_malefic, b_antidote,
                       "the lord is joined by a malefic", ANNIHILATION_SOURCE),
        FiredCondition("lord_conjunct_dusthana_lord", f.lord_conjunct_dusthana_lord, c_antidote,
                       "the lord conjoins a lord of the 6th/8th/12th", ANNIHILATION_SOURCE),
        FiredCondition("lord_defeated_in_war", f.lord_defeated_in_war, False,
                       "the lord is defeated in a planetary war (its potence is void)",
                       ANNIHILATION_SOURCE),
        FiredCondition("lord_in_vriddha_or_mrita", f.lord_avastha in ("vriddha", "mrita"), False,
                       f"the lord is in {f.lord_avastha}avastha (a spent age-state)",
                       ANNIHILATION_SOURCE),
        # The THIRD killing avastha the sloka names alongside Vriddha and Mrita — Supta, i.e. the
        # lord debilitated or in an enemy's sign (Jagradadi sushupti). Omitting it left the
        # annihilation side asymmetric with the prosperity side's Prabuddha/Jagrad clause.
        FiredCondition("lord_in_supta", f.lord_in_supta, False,
                       "the lord is in Suptavastha (debilitated or in an enemy's sign)",
                       SUPTA_SOURCE),
    ]

    net_p = sum(1 for c in p if c.fired)
    net_a = sum(1 for c in a if c.fired and not c.antidoted)
    if net_p > net_a:
        verdict: Verdict = "flourishing"
    elif net_a > net_p:
        verdict = "annihilated"
    else:
        verdict = "ordinary"
    return BhavaVerdict(house=f.house, verdict=verdict,
                        prosperity=tuple(p), annihilation=tuple(a),
                        net_prosperity=net_p, net_annihilation=net_a)
