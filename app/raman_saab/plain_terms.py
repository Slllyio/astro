"""The plain-terms layer — every technical term translated, with WHY IT MATTERS.

VOCABULARY ONLY, NEVER ASTROLOGY: each entry explains a word the report already uses;
the analogies are teaching devices, the bands re-label MEASURED values against Raman's
own thresholds (GBB-8:303 minimum rupas; HPA Ch.7's own avastha polarities). Nothing
here judges, scores, or predicts — a guard test runs every string through the LLM
tripwire, and a test pins that the user-named terms all carry four-field entries.

Entry shape (the reviewed design): technical term -> PlainTerm(plain, analogy,
why_it_matters, example) — example may be "".

The single source of truth: markdown, standalone HTML, JSON (`plain_terms` key) and the
interactive page all render FROM this module.

Usage:
    from app.raman_saab.plain_terms import (TERM_GLOSS, band_rupas, gloss_dict,
                                            plain_avastha)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional


@dataclass(frozen=True)
class PlainTerm:
    plain: str            # the plain name
    analogy: str          # one memorable line
    why_it_matters: str   # the consequence, one sentence
    example: str = ""     # a mini example where one teaches instantly


TERM_GLOSS: Final[dict[str, PlainTerm]] = {
    "Shadbala": PlainTerm(
        "planetary strength", "think of it as horsepower — a powerful engine can pull "
        "a heavier load",
        "a strong planet tends to express its indications more effectively in its "
        "periods; a weak one needs support from other combinations",
        "Jupiter at 9.2 rupas against his own required minimum reads Very strong"),
    "Rupas": PlainTerm(
        "strength units", "the horsepower number itself",
        "Raman states a minimum required per planet (GBB-8:303) — the band words in this "
        "report compare against HIS thresholds, not invented ones"),
    "Ishta": PlainTerm(
        "good-yield potential", "the sweetness a fruit is capable of",
        "a period lord high in Ishta inclines its Dasha toward pleasant results"),
    "Kashta": PlainTerm(
        "hard-yield potential", "the bitterness a fruit is capable of",
        "a period lord high in Kashta inclines its Dasha toward difficult results"),
    "Avastha": PlainTerm(
        "planetary state (mood)", "the same engine can run bright or exhausted",
        "the state colours HOW a planet delivers what it signifies"),
    "Deeptha": PlainTerm(
        "radiant — at its brightest (exalted)", "🔥 a fully charged battery",
        "delivers its significations at full power"),
    "Swastha": PlainTerm(
        "at ease (own sign)", "😌 at home, comfortable",
        "delivers steadily — fame, position, happiness in its topics"),
    "Muditha": PlainTerm(
        "delighted (friend's sign)", "🙂 a guest among friends",
        "inclines to happiness in its topics"),
    "Santha": PlainTerm(
        "calm (auspicious sub-division)", "🌤 good inner weather",
        "adds quiet strength and comfort"),
    "Sakta": PlainTerm(
        "empowered (retrograde)", "💪 pushing against the current and gaining",
        "adds courage, reputation and wealth in Raman's reading"),
    "Peedya": PlainTerm(
        "pressed (last quarter of the sign)", "⚠️ running on the rim",
        "inclines toward friction with authority in its topics"),
    "Deena": PlainTerm(
        "dejected — running weak (enemy's sign)", "⚠️ a guest among rivals",
        "inclines toward worry and struggle in its topics"),
    "Vikala": PlainTerm(
        "impaired (combust)", "🌫 outshone by the Sun, hard to see",
        "its indications arrive weakened or obscured"),
    "Khala": PlainTerm(
        "downcast (debilitated)", "❌ an engine at its lowest gear",
        "its indications struggle unless a cancellation (bhanga) lifts them"),
    "Bhita": PlainTerm(
        "afraid (defeated/accelerated)", "❌ shaken",
        "Raman reads losses and danger in its topics"),
    "Karaka": PlainTerm(
        "the natural significator", "the planet that carries a life-topic wherever it "
        "stands",
        "even outside the topic's house, the karaka still colours that topic",
        "Venus is the natural significator of marriage — even outside the 7th house, "
        "Venus still influences relationships"),
    "Lagna": PlainTerm(
        "the Ascendant — the rising sign", "the lens the whole chart is read through",
        "every house is counted from it; the personality portrait starts here"),
    "Navamsa": PlainTerm(
        "the ninth-division chart — the second inspection",
        "opening the engine to see whether the outside matches the inside",
        "many indications of the main chart are confirmed or weakened here"),
    "Bhava": PlainTerm(
        "a house — one life department", "twelve rooms of one life",
        "each house holds a family of topics judged together"),
    "Dasha": PlainTerm(
        "a planetary period", "whose hands are on the wheel, and for how long",
        "indications tend to fructify in the periods of the planets that carry them"),
    "Bhukti": PlainTerm(
        "a sub-period", "the co-driver within a period",
        "the sub-period lord refines WHAT of the period's promise is delivered"),
    "Gochara": PlainTerm(
        "transits — where the planets are NOW", "today's weather over the natal climate",
        "transits are catalytic and secondary — the Dasha decides, transits colour"),
    "Vedha": PlainTerm(
        "obstruction", "a green light cancelled by a blocked junction",
        "a favourable transit can be neutralised by another planet at the Vedha point"),
    "Bindu": PlainTerm(
        "a benefic point (Ashtakavarga)", "votes of support for a sign",
        "more bindus = more support when a planet transits that sign"),
    "Sarvashtakavarga": PlainTerm(
        "the all-planet bindu table", "the whole committee's vote per sign",
        "signs rich in bindus receive transits more kindly"),
    "Kakshya": PlainTerm(
        "an eighth-part of a sign", "lanes within a road",
        "a transit's micro-position decides which planet's lane it runs in"),
    "Vargottama": PlainTerm(
        "same sign in D-1 and D-9", "the inside matches the outside exactly",
        "a vargottama planet's indications are considered firmer"),
    "Maraka": PlainTerm(
        "a death-dealing determinant (technical tier)", "the timekeepers of the "
        "life-span doctrine",
        "a METHOD term for period analysis — this report never predicts from it, and "
        "says so wherever it appears"),
    "Arishta": PlainTerm(
        "an affliction combination", "a storm warning in the classical text",
        "always read WITH its cancellations — Raman gives both"),
    "Bhanga": PlainTerm(
        "a cancellation", "the storm warning lifted",
        "a stated bhanga neutralises the affliction it targets"),
    "Atmakaraka": PlainTerm(
        "the soul significator (highest-degree planet)", "the protagonist of the chart",
        "Jaimini reads character and calling from it"),
    "Karakamsa": PlainTerm(
        "the Atmakaraka's navamsa sign", "where the protagonist stands in the second "
        "inspection",
        "Jaimini reads mind and predispositions from planets around it"),
    "Upapada": PlainTerm(
        "the marriage arudha", "the marriage-house's public face",
        "Jaimini reads the partnership's circumstances from it"),
    "Tara": PlainTerm(
        "the nine-fold star count", "a compatibility count between stars",
        "electional work counts from the birth star to the day's star"),
}


#: "Why astrologers examine this" — the method's own inspection order per major section,
#: stating what that section ALREADY does and cites (teaching the method, never adding
#: doctrine). Rendered as an educational preamble in every surface.
SECTION_METHOD: Final[dict[str, tuple[str, tuple[str, ...]]]] = {
    "marriage": (
        "For marriage, classical astrology inspects a fixed sequence — and this chapter "
        "follows exactly that order",
        ("the 7th house and its lord", "Venus, the natural significator",
         "the Navamsa (the second inspection)", "the Upapada (Jaimini's marriage arudha)",
         "the Dasha periods that activate the 7th")),
    "children": (
        "For children, the classical sequence this chapter follows",
        ("the 5th house and its lord", "Jupiter, the natural significator",
         "the Saptamsa D-7 (the children division)",
         "the classical combination lists", "the periods that activate the 5th")),
    "profession": (
        "For profession, Raman's own method inspects, in order",
        ("the 10th house, its sign and lord",
         "the navamsa-dispositor of the 10th lord (his primary technique)",
         "the strongest planet", "the Dasamsa D-10", "the running period's colour")),
    "wealth": (
        "For wealth, the classical channels are read separately, in order",
        ("the 2nd house (accumulation) and its lord's placement",
         "the 11th house (gains) and its occupants", "the 8th (legacies, sudden gains)",
         "the 5th (speculation)", "the periods that activate the 2nd and 11th")),
    "health_readout": (
        "For health, the classical sequence this read-out re-reads",
        ("the 1st house (constitution)", "the 6th (disease), 8th (longevity lean), "
         "12th (confinement)", "the Moon (mind) and Mercury (nerves) as karakas",
         "the balarishta screen", "the Trimsamsa D-30 corroboration")),
    "longevity": (
        "For longevity, Raman's own order — band first, periods second",
        ("the band by combination (Balarishta / Alpayu / Madhyayu / Purnayu)",
         "the maraka scheme (2nd and 7th lords and associates)",
         "the numeric Ayurdaya as a cross-check only")),
    "psych": (
        "For temperament and mind, the classical inspection order",
        ("the rising sign's portrait", "the Moon as manas (mind) karaka",
         "the strongest planet's temperament", "the Navamsa lagna's stamp",
         "the Atmakaraka")),
}


def gloss_dict() -> dict[str, dict[str, str]]:
    """The JSON-shape of the glossary — the one source every surface renders from."""
    return {term: {"plain": t.plain, "analogy": t.analogy,
                   "why_it_matters": t.why_it_matters, "example": t.example}
            for term, t in TERM_GLOSS.items()}


def band_rupas(planet: str, rupas: Optional[float]) -> str:
    """The plain band for a Shadbala total, against RAMAN'S OWN minimum (GBB-8:303) —
    with the consequence, never a bare word."""
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
    if rupas is None:
        return "unmeasured on this chart"
    req = MIN_REQUIRED.get(planet)
    if req is None:
        return f"{rupas:.1f} rupas"
    ratio = rupas / req
    if ratio >= 1.5:
        return ("Very strong — well above Raman's required minimum; likely to deliver "
                "its indications consistently")
    if ratio >= 1.0:
        return ("Strong — meets Raman's required minimum; expresses its indications "
                "effectively")
    if ratio >= 0.8:
        return ("Adequate — just under the requirement; delivers with effort")
    return ("Below requirement — needs support from other combinations to deliver")


def plain_avastha(state: str) -> str:
    """'Deeptha' -> 'Deeptha (radiant — at its brightest (exalted)) 🔥-style' — the word
    first, the plain equivalent after it; unknown states pass through unchanged."""
    t = TERM_GLOSS.get(state)
    if t is None:
        return state
    head = t.analogy.split(" ", 1)[0]
    icon = head if any(ord(c) > 0x2600 for c in head) else ""
    return f"{icon} {state} ({t.plain})".strip() if icon else f"{state} ({t.plain})"
