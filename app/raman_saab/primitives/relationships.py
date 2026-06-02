from __future__ import annotations
from typing import Final

# (sign 1..12, degree within sign) of deep exaltation.
EXALTATION: Final[dict[str, tuple[int, float]]] = {
    "Sun": (1, 10.0), "Moon": (2, 3.0), "Mars": (10, 28.0), "Mercury": (6, 15.0),
    "Jupiter": (4, 5.0), "Venus": (12, 27.0), "Saturn": (7, 20.0),
}
DEBILITATION: Final[dict[str, tuple[int, float]]] = {
    p: (((s + 6 - 1) % 12) + 1, d) for p, (s, d) in EXALTATION.items()
}
# Moolatrikona: (sign, start_deg, end_deg).
# Mercury: Virgo 16-20 per Santhanam/Raman (minority editions read 15-20)
MOOLATRIKONA: Final[dict[str, tuple[int, float, float]]] = {
    "Sun": (5, 0.0, 20.0), "Moon": (2, 4.0, 30.0), "Mars": (1, 0.0, 12.0),
    "Mercury": (6, 16.0, 20.0), "Jupiter": (9, 0.0, 10.0), "Venus": (7, 0.0, 15.0),
    "Saturn": (11, 0.0, 20.0),
}
# Naisargika (natural) friendship — Parashara. friends/enemies; anything else neutral.
_FRIENDS: Final[dict[str, frozenset[str]]] = {
    "Sun": frozenset({"Moon", "Mars", "Jupiter"}),
    "Moon": frozenset({"Sun", "Mercury"}),
    "Mars": frozenset({"Sun", "Moon", "Jupiter"}),
    "Mercury": frozenset({"Sun", "Venus"}),
    "Jupiter": frozenset({"Sun", "Moon", "Mars"}),
    "Venus": frozenset({"Mercury", "Saturn"}),
    "Saturn": frozenset({"Mercury", "Venus"}),
}
_ENEMIES: Final[dict[str, frozenset[str]]] = {
    "Sun": frozenset({"Venus", "Saturn"}),
    "Moon": frozenset(),
    "Mars": frozenset({"Mercury"}),
    "Mercury": frozenset({"Moon"}),
    "Jupiter": frozenset({"Mercury", "Venus"}),
    "Venus": frozenset({"Sun", "Moon"}),
    "Saturn": frozenset({"Sun", "Moon", "Mars"}),
}
# General combustion orbs (degrees from Sun).
# direct-motion orbs; retrograde Mercury=12, Venus=8 is a later refinement
# Note: the longevity Astangata-harana uses its own orbs (doctrine/ayus_tables, Phase 4)
# — do NOT reuse these there.
COMBUSTION_ORB: Final[dict[str, float]] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
    "Venus": 10.0, "Saturn": 15.0,
}


def naisargika(of: str, towards: str) -> str:
    if towards in _FRIENDS.get(of, frozenset()):
        return "friend"
    if towards in _ENEMIES.get(of, frozenset()):
        return "enemy"
    return "neutral"
