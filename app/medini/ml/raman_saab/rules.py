"""Candidate Raman death-timing rules — the house-independent (dasha) subset.

Each rule is a named hypothesis that death is enriched (or depleted) during
the Vimshottari dasha of a set of lords. These are the rules testable without
birth times (see docs/death_timing_findings.md §3a / §6). House/lord-based
maraka rules (2nd & 7th lords, 8th-house occupancy) are NOT here — they need
an ascendant, which the birth-time-free corpus can't supply.

Citations marked ⚑ must be pinned by the bphs-doctrine-reviewer before a rule
is promoted past `provisional` (per DOCTRINE_RATCHET_PLAN.md §1).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    rule_id: str
    family: str
    lords: frozenset[str]
    # "enrich" => predicted RR > 1 during these lords' dashas;
    # "deplete" => predicted RR < 1 (protective).
    direction: str
    levels: tuple[str, ...]  # subset of ("md", "ad", "md_or_ad")
    citation: str  # ⚑ to be pinned
    rationale: str = ""


# The natural death significator per the repo's own EVENT_KARAKAS
# (survival_analysis.py) and Raman's ayushkaraka emphasis: Saturn.
CANDIDATE_RULES: tuple[Rule, ...] = (
    Rule(
        rule_id="raman.karaka.saturn_dasha",
        family="longevity",
        lords=frozenset({"Saturn"}),
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Raman, How to Judge a Horoscope; EVENT_KARAKAS['death']=(Saturn,)",  # ⚑
        rationale="Saturn is the natural karaka of death/longevity (ayushkaraka); "
                  "its dasha periods should over-represent death timing.",
    ),
    Rule(
        rule_id="raman.karaka.mars_saturn_dasha",
        family="longevity",
        lords=frozenset({"Mars", "Saturn"}),
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="EVENT_KARAKAS['death by disease']=(Saturn, Mars)",  # ⚑
        rationale="Saturn (chronic decay) + Mars (accident/violence) as the "
                  "disease/injury death karakas.",
    ),
    Rule(
        rule_id="raman.malefic_dasha",
        family="longevity",
        lords=frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"}),
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Classical natural-malefic set (BPHS)",  # ⚑
        rationale="Death is classically associated with malefic periods; test "
                  "whether the natural malefics collectively over-represent death.",
    ),
    Rule(
        rule_id="raman.benefic_dasha_protective",
        family="longevity",
        lords=frozenset({"Jupiter", "Venus", "Mercury", "Moon"}),
        direction="deplete",
        levels=("md", "ad", "md_or_ad"),
        citation="Dual of the malefic rule (benefics as protective)",  # ⚑
        rationale="If malefic dashas enrich death, benefic dashas should deplete "
                  "it — a falsifiable dual that guards against a trivial artifact.",
    ),
    Rule(
        rule_id="raman.karaka.rahu_ketu_dasha",
        family="longevity",
        lords=frozenset({"Rahu", "Ketu"}),
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Nodal dashas as sudden/unusual death (bayesian_rule_validation "
                 "rahu_in_8th_unusual_death, ketu_in_8th_spiritual_end)",  # ⚑
        rationale="Nodes are cited for sudden/unusual death; test their dashas.",
    ),
)


PER_LORD_LEVELS: tuple[str, ...] = ("md", "ad", "md_or_ad")


# --------------------------------------------------------------------------- #
# Chart-dependent (house-based) maraka rules — need a timed birth (lagna).     #
# The lord set varies per person; `resolver` names a Kundali-based derivation  #
# implemented in maraka_validate.py.                                           #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ChartRule:
    rule_id: str
    family: str
    resolver: str      # key into maraka_validate._RESOLVERS
    direction: str     # "enrich" | "deplete"
    levels: tuple[str, ...]
    citation: str      # ⚑ to be pinned
    rationale: str = ""


MARAKA_RULES: tuple[ChartRule, ...] = (
    ChartRule(
        rule_id="raman.maraka.lords_2_7",
        family="longevity",
        resolver="maraka_lords",
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Raman, How to Judge a Horoscope (maraka adhyaya); "
                 "BPHS Ch.44 (2nd & 7th lords as marakas)",  # ⚑
        rationale="THE core classical death-timing rule: dashas of the lords "
                  "of the 2nd and 7th from lagna are the death-inflicting "
                  "(maraka) periods.",
    ),
    ChartRule(
        rule_id="raman.maraka.lord_8",
        family="longevity",
        resolver="lord_8",
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="8th lord as ayus lord; its dasha as a mortality window",  # ⚑
        rationale="The 8th (ayus) lord's periods as longevity-critical.",
    ),
    ChartRule(
        rule_id="raman.maraka.lords_2_7_8",
        family="longevity",
        resolver="maraka_and_8",
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Union of maraka lords and 8th lord",  # ⚑
        rationale="Broadest classical death-window set.",
    ),
    ChartRule(
        rule_id="raman.maraka.saturn_as_maraka",
        family="longevity",
        resolver="saturn_if_maraka",
        direction="enrich",
        levels=("md", "ad", "md_or_ad"),
        citation="Raman/classical: 'Saturn as a maraka lord kills without "
                 "compunction' — Saturn's dasha in charts where Saturn rules "
                 "2H or 7H",  # ⚑
        rationale="Sharpest form: Saturn restricted to charts where it holds "
                  "maraka lordship (Cancer/Leo/Gemini/Capricorn... lagnas "
                  "where Saturn rules 2 or 7).",
    ),
)
