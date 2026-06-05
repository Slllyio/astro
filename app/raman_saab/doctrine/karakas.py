"""Bhava karakas — the 'significator' planet for each house (the third pillar of
judgment alongside the House and its Lord; methodology overview §2, HTJAH-I:983).

Raman judges every matter through House + Lord + Karaka. These are the FIXED
naisargika/bhava karakas (NOT Jaimini chara-karakas — locked divergence D4). The
karaka is judged AS A LAGNA from its own position (the 'from-karaka' frame).

`BHAVA_KARAKA` gives the primary significator per house; `BHAVA_KARAKAS` gives the
full set where a house has several (e.g. 4th: mother=Moon, property=Mars,
education=Mercury, vehicles=Venus).
"""
from __future__ import annotations

from typing import Final

# Primary significator per house (1..12).
BHAVA_KARAKA: Final[dict[int, str]] = {
    1: "Sun",       # body / vitality / self
    2: "Jupiter",   # wealth / family
    3: "Mars",      # siblings / courage
    4: "Moon",      # mother / happiness
    5: "Jupiter",   # children / intellect
    6: "Mars",      # enemies / injury (Saturn for disease — see BHAVA_KARAKAS)
    7: "Venus",     # spouse
    8: "Saturn",    # longevity
    9: "Jupiter",   # fortune / dharma (Sun for father)
    10: "Saturn",   # karma / profession (also Mercury/Jupiter/Sun)
    11: "Jupiter",  # gains
    12: "Saturn",   # loss / moksha
}

# Full karaka sets where a house carries several significators (overview §6.1 routing).
BHAVA_KARAKAS: Final[dict[int, tuple[str, ...]]] = {
    1: ("Sun",),
    2: ("Jupiter",),
    3: ("Mars",),
    4: ("Moon", "Mars", "Mercury", "Venus"),
    5: ("Jupiter",),
    6: ("Mars", "Saturn"),
    7: ("Venus",),
    8: ("Saturn",),
    9: ("Jupiter", "Sun"),
    10: ("Saturn", "Mercury", "Jupiter", "Sun"),
    11: ("Jupiter",),
    12: ("Saturn",),
}
