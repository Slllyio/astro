"""Shared planet/sign lexicon — the ONE source for the qualitative vocabulary.

Both the classical narrative (`classical_narrative.py`) and the native profile
(`native_profile.py`) describe a planet's higher-and-shadow expression, a sign's
temperament, and whether a graha is well placed. Keeping that vocabulary in one
module means the two readings can never drift apart on the same planet.

Pure data + one pure predicate; no engine imports, no I/O.
"""
from __future__ import annotations

from typing import Any, Mapping

# Each sign's temperament (Raman's ascendant-character descriptions).
SIGN_TEMPERAMENT: dict[int, str] = {
    1: "energetic, pioneering and somewhat impulsive, with a martial cast of mind",
    2: "steady, patient and fond of comfort, with fixity of purpose",
    3: "intellectual, versatile and communicative, fond of learning and movement",
    4: "sensitive, imaginative and domestic, with a somewhat changeful mind",
    5: "ambitious, dignified and generous, with a marked desire for recognition",
    6: "analytical, discriminating and methodical, at times over-critical",
    7: "balanced, refined and sociable, fond of harmony and the arts",
    8: "intense, reserved and determined, with considerable reserves of will",
    9: "frank, philosophical and optimistic, inclined to religion and travel",
    10: "practical, cautious and persevering, with organising ability",
    11: "humane, independent and reflective, with a philosophical bent",
    12: "kind, emotional and impressionable, with a spiritual inclination",
}

# What each planet signifies.
PLANET_SIG: dict[str, str] = {
    "Sun": "will, authority, vitality and the father",
    "Moon": "the mind, the emotions and the mother",
    "Mars": "energy, courage, initiative and enterprise",
    "Mercury": "intellect, speech, reasoning and commerce",
    "Jupiter": "wisdom, fortune, progeny and devotion",
    "Venus": "refinement, comforts, marriage and the arts",
    "Saturn": "discipline, endurance, labour and longevity",
    "Rahu": "worldly ambition, the unconventional and the foreign",
    "Ketu": "detachment, intuition and spiritual tendencies",
}

# Each planet's higher expression (well placed) and its shadow (afflicted).
PLANET_QUALITY: dict[str, tuple[str, str]] = {
    "Sun": ("dignity, a firm will and a love of honour",
            "an inclination to pride or a domineering temper"),
    "Moon": ("a receptive, contented and sympathetic mind",
             "changefulness of mood and emotional dependence"),
    "Mars": ("courage, decision and executive capacity",
             "haste, irritability or a combative streak"),
    "Mercury": ("quickness of intellect and an aptitude for learning and affairs",
                "restlessness and a want of steadiness in thought"),
    "Jupiter": ("wisdom, generosity, faith and good fortune",
                "over-optimism or a tendency to excess"),
    "Venus": ("refinement, artistic taste and domestic happiness",
              "an over-fondness for ease and pleasure"),
    "Saturn": ("patience, endurance and a capacity for sustained labour",
               "melancholy, delay and a want of self-confidence"),
}


def well_placed(dignity: str | None, composite: float | None,
                combust: bool) -> bool | None:
    """Is a graha's higher nature showing? True = yes, False = its shadow,
    None = mixed. Dignity and combustion decide first; otherwise the composite
    (≥55 → good, <42 → poor, between → mixed). This is the exact rule the
    classical narrative has always used — now shared so the native profile
    reads the same way."""
    dig = str(dignity or "").lower()
    if dig in ("exalted", "own", "moolatrikona") and not combust:
        return True
    if dig == "debilitated" or combust:
        return False
    if composite is not None:
        return True if composite >= 55 else False if composite < 42 else None
    return None


def strength_index(planet_strength: Mapping[str, Any] | None
                   ) -> dict[str, dict[str, Any]]:
    """planet -> its planet_strength row, for the reducers that need dignity /
    composite / combust / house by planet name."""
    out: dict[str, dict[str, Any]] = {}
    if not planet_strength:
        return out
    for r in (planet_strength.get("planets") or []):
        if isinstance(r, dict) and r.get("planet"):
            out[r["planet"]] = r
    return out
