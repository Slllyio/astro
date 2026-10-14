"""Matter routing — which house a reader's question is actually about.

`/report/ask` grounds every question in the WHOLE chart, which is right and undifferentiated:
"will my marriage work out?" arrives alongside fifty facts about career, wealth, siblings and
transits, and the one line the reader needs — House 7's own signification breakdown — is a
single headline among them.

This module names the house a question concerns, so the caller can ADD that house's detail to
the evidence. It never removes anything: the whole-chart grounding stays exactly as it was, and
the focus is a supplement (the same contract `plainspoken` follows — the lead sits above the
full data, never in place of it).

**This is DOCTRINE, not a measured improvement, and it must never be described as one.**
Raman judges marriage from the 7th, its lord and its karaka (HTJAH-II:225); children from the
5th; career from the 10th. The house a matter belongs to is his assignment, reused here from
the reviewed `_MATTER_HOUSE` table rather than restated.

The measurement that would have validated a *ranking* claim does not exist: `golden_attention`
labels each pronounced house with a signification, and all 48 significations map to exactly one
house, so a topic->house model scores p@1 = 1.000 by reading its own label
(`SALIENCE_BASELINE.md` Phase 5). Nothing here is offered as beating a baseline.

Two refusals, both deliberate:

* **Silence beats a guess.** A question naming no matter, or naming several, returns None and
  the evidence is untouched. Picking one of two matters a reader mentioned would quietly answer
  a question they did not ask.
* **No narrowing, ever.** This returns a house to ADD. A caller that swaps whole-chart evidence
  for one house's would hide the dasha, the 2nd and the 8th from a marriage question — the
  REPORT COMPLETENESS failure in a new place.

Usage:
    from app.raman_saab.matter_routing import focus_house
    house = focus_house("will my marriage work out?")     # -> 7
"""
from __future__ import annotations

import re
from typing import Final, Optional

#: matter -> the words a reader actually uses for it. Matters are the keys of the reviewed
#: `_MATTER_HOUSE` table in `tension_narrator`; only the vocabulary is new.
#:
#: Deliberately conservative. A word earns a place here when it names the matter plainly, not
#: when it merely associates with it — "money" is wealth, "rich" is a judgment about wealth and
#: is left out, because matching it would route a question about someone else's fortune.
MATTER_WORDS: Final[dict[str, tuple[str, ...]]] = {
    "marriage": ("marriage", "married", "marry", "spouse", "wife", "husband", "partner",
                 "wedding", "divorce"),
    "children": ("child", "children", "kids", "son", "daughter", "progeny", "childbirth",
                 "conceive", "pregnancy"),
    # NOT bare "work": "will my marriage work out?" matched career AND marriage and therefore
    # routed nowhere — the canonical question this exists for, defeated by an idiom. The
    # remaining words name the matter unambiguously; "how is my work going" now degrades to the
    # whole-chart answer, which is the safe direction to fail in.
    "career": ("career", "job", "profession", "professional", "occupation",
               "promotion", "employment", "vocation", "business"),
    "wealth": ("wealth", "money", "finance", "financial", "savings", "income", "salary",
               "earnings", "fortune"),
    "health": ("health", "illness", "disease", "sick", "sickness", "ailment", "medical",
               "recovery"),
    "gains": ("gain", "gains", "profit", "profits", "windfall"),
    "courage": ("sibling", "siblings", "brother", "brothers", "sister", "sisters", "courage"),
    "happiness": ("mother", "home", "property", "land", "vehicle", "comforts"),
    "fortune": ("father", "luck", "fortunate", "dharma", "pilgrimage"),
    "enemies": ("enemy", "enemies", "rival", "rivals", "litigation", "lawsuit", "debt",
                "debts", "obstacle", "obstacles"),
    "longevity": ("longevity", "lifespan", "life-span"),
    "losses": ("loss", "losses", "expense", "expenses", "foreign", "abroad", "isolation",
               "moksha", "liberation"),
}


def matters_in(question: str) -> set[str]:
    """Every matter the question names. Whole-word matching only.

    Substring matching routes "workout" to career and "sonata" to children; both are the kind
    of quiet wrongness this project keeps finding, so the boundaries are explicit.
    """
    if not question:
        return set()
    text = question.lower()
    found: set[str] = set()
    for matter, words in MATTER_WORDS.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text):
                found.add(matter)
                break
    return found


#: "the 7th house", "my 10th bhava", "house 5" — a reader naming a bhava outright.
_EXPLICIT_HOUSE = re.compile(
    r"\b(?:(\d{1,2})(?:st|nd|rd|th)?\s+(?:house|bhava)|(?:house|bhava)\s+(\d{1,2}))\b",
    re.IGNORECASE)


def explicit_house(question: str) -> Optional[int]:
    """The bhava a question names outright, or None.

    "house" is both a dwelling and a bhava. In a question about a chart the jargon reading wins,
    so it is matched here — precisely — rather than left in the `happiness` vocabulary, where
    "tell me about my 7th house" routed to the 4th.
    """
    m = _EXPLICIT_HOUSE.search(question or "")
    if not m:
        return None
    n = int(m.group(1) or m.group(2))
    return n if 1 <= n <= 12 else None


def focus_house(question: str) -> Optional[int]:
    """The house whose detail should be ADDED to the evidence, or None to change nothing.

    None on both failure modes that matter: no matter named (an open question about the whole
    life, which the whole-chart grounding already answers), and more than one named (answering
    for one of them silently drops the other).
    """
    from app.raman_saab.tension_narrator import _MATTER_HOUSE

    explicit = explicit_house(question)
    if explicit is not None:
        return explicit

    found = matters_in(question)
    if len(found) != 1:
        return None
    return _MATTER_HOUSE.get(next(iter(found)))
