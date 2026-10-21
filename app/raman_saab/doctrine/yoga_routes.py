"""Yoga routes — which house and sub-matter each fired yoga may modulate.

Raman's consideration 4 (HTJAH-I:480-482) asks "whether the influence has been altered by any
yogas occurring in any particular house or houses": a yoga bears on the matter it is ABOUT, not
on every house that shares its `kind` tag. Until 2026-10-21 the house judge routed by kind alone
(any `dhana` yoga lifted H11 gains, any `raja` yoga H9/H10, any `arishta` yoga H1). That was
harmless while `dhana` meant a 2/11 lordship combination and `arishta` meant Sakata/Kemadruma;
the merge of main's 113 Three Hundred Combinations yogas made it wrong (review:
docs/raman_saab/MERGE_VERDICT_REVIEW_2026-10-21.md — 78 verdict moves, 67 contradicting the text).

So each yoga that may modulate is listed here with the house and sub-matter keys its own printed
text names. **A yoga absent from this table modulates nothing** — it is still detected, cited and
reported; it just never moves a house verdict. The `kind` still sets the DIRECTION (dhana/raja
lift, arishta drop) inside `house_template._yoga_modulate`; this table only sets the REACH.

Raja yogas of the completed 3HC (245-263, and Indra) are deliberately ABSENT: Raman's Remarks
make their weight conditional — "The theoretical presence of Raja yogas is of no consequence
unless the Raja Yogas have inherent vitality to produce the results ascribed to them. The student
must first learn to pick up Raja yogas and then weigh their relative strengths and weaknesses"
(3HCC:8580-8584) — and the passage gives no test of that vitality that could be encoded without
inventing one. Until a cited test exists they surface as metadata only.

Usage:
    from app.raman_saab.doctrine.yoga_routes import routes_to
    routes_to("Y.BHAGYA", 9, "fortune")      # True
    routes_to("Y.BHAGYA", 11, "gains")       # False
"""
from __future__ import annotations

from typing import Final

#: ((house, sub-matter keys), ...) — the reach of one yoga.
Route = tuple[tuple[int, frozenset[str]], ...]

#: Wealth: the H2 wealth matter and the H11 gains matter (gains + acquisitions, the two keys the
#: H11 dhana floor has always scoped). Never H11 friends or elder siblings, never H2 family,
#: speech or vision — they carry a `wealth`/`gains` rule tag but are not wealth.
_WEALTH: Final[Route] = ((2, frozenset({"wealth"})),
                         (11, frozenset({"gains", "acquisitions"})))

#: The native's own self, body and health (H1) — the reach the arishta drop has always had.
_SELF: Final[Route] = ((1, frozenset({"self", "body", "health"})),)

#: Fortune and career — the reach the HTJAH-I lordship raja yogas were calibrated on.
_FORTUNE_CAREER: Final[Route] = (
    (9, frozenset({"father", "fortune", "dharma", "higher_learning", "long_journeys"})),
    (10, frozenset({"career", "profession_authority", "profession_trade",
                    "profession_learned", "profession_labour", "status_honour"})))

#: Progeny (H5 children).
_PROGENY: Final[Route] = ((5, frozenset({"children"})),)

YOGA_ROUTES: Final[dict[str, Route]] = {
    # ── pre-merge yogas: the reach they were calibrated and doctrine-reviewed on ─────────────
    "Y.KEMADRUMA": _SELF, "Y.SAKATA": _SELF, "Y.BRIHADBIJA": _SELF,
    "Y.RAJA.KT": _FORTUNE_CAREER, "Y.RAJA.910X": _FORTUNE_CAREER,
    "Y.RAJA.910A": _FORTUNE_CAREER, "Y.VIPAREETA": _FORTUNE_CAREER,
    "Y.CHAMARA": _FORTUNE_CAREER, "Y.SREENATHA": _FORTUNE_CAREER,
    "Y.KHADGA": _FORTUNE_CAREER, "Y.KUSUMA": _FORTUNE_CAREER,
    # The HTJAH-I / 3HC dhana yogas are 2nd/11th wealth combinations; the reach is narrowed to
    # the wealth matters themselves (it used to include every `wealth`/`gains`-tagged key).
    "Y.DHANA.EXCH": _WEALTH, "Y.DHANA.59": _WEALTH, "Y.DHANA.CHAIN": _WEALTH,
    "Y.DHANA.BAHU": _WEALTH, "Y.DHANA.122": _WEALTH, "Y.DHANA.125": _WEALTH,
    # ── the completed 3HC (merged from main) ──────────────────────────────────────────────
    # Lakshmi: "Lakshmi has predominantly to do with wealth and one born in this combination
    # will be wealthy" (3HCH:1563).
    "Y.LAKSHMI": _WEALTH,
    # Vishnu: "acquire fortunes from various countries, earn in lakhs" (3HCC:3499-3500).
    "Y.VISHNU": _WEALTH,
    # Bhagya: a strong benefic "simultaneously aspecting the 9th" (3HCC:7989-7990); "extremely
    # fortunate" (3HCC:7991). Its house is the 9th; it never reaches the H11 gains floor.
    "Y.BHAGYA": ((9, frozenset({"fortune"})),),
    # Progeny curses and losses — each printed result is the loss of issues:
    # Sarpasapa 3HCC:6891, Pitrusapa 3HCC:7017-7018, Matrusapa 3HCC:7155, Bhratrusapa 3HCC:7200,
    # Pretasapa 3HCC:7219, Kalanirdesat Putranasa 3HCC:7487, Putrakalatraheena 3HCC:9601
    # ("deprived of family and children"), Vamsacheda 3HCC:9701 (the family line ends).
    "Y.SARPASAPA": _PROGENY, "Y.PITRUSAPA_SUTAKSHAYA": _PROGENY,
    "Y.MATRUSAPA_SUTAKSHAYA": _PROGENY, "Y.BHRATRUSAPA_SUTAKSHAYA": _PROGENY,
    "Y.PRETASAPA": _PROGENY, "Y.KALANIRDESAT_PUTRANASA": _PROGENY,
    "Y.PUTRAKALATRAHEENA": _PROGENY, "Y.VAMSACHEDA": _PROGENY,
    # Not routed (REPORT ONLY — detected, cited and shown in the reading, never moving a
    # verdict):
    # * The bodily-affliction and manner-of-death yogas — Vrana, Guhyaroga, Sirachchheda and the
    #   rest of that class (Sisnavyadhi, Kushtaroga, Bandhana, Durmarana, Peenasaroga, Pittaroga,
    #   Angaheena, Swetakushta, Pisacha Grastha, Vatharoga, Matibhramana, Galakarna, Sarpaganda,
    #   Kshayaroga, Karascheda, Yuddhe Marana, Sanghataka Marana). USER DECISION 2026-10-21
    #   ("No, report only"): Raman's own Remarks on Vrana caution "A literal application of the
    #   yoga is not at all recommended" (3HCC:8923-8924), so a disease yoga does not drop H1.
    # * Kalatrashanda (3HCC:9026) and Vikalangapatni (3HCC:9588) name the SPOUSE, a matter the
    #   yoga step has no wiring for; Raman cautions on both.
}


def routes_to(yoga_id: str, house: int, key: str) -> bool:
    """True when `yoga_id` may modulate the `key` sub-matter of `house`."""
    return any(h == house and key in keys for h, keys in YOGA_ROUTES.get(yoga_id, ()))
