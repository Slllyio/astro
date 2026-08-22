"""Jagradadi avastha — the awake / dreaming / sleeping states of a planet (BPHS ch.45, sloka 5).

    "If a planet is in its own sign or in exaltation it is said to be in a state of awakening. In
     the sign of a friend or of a neutral it is in dreaming state while in enemy's sign or in
     debilitation it is in a state of sleeping. According to a planet being in Awakening, Dreaming
     or Sleeping states, the results due to it will be full, medium or nil." (BPHS-45:77)

Three states by the dignity of the OCCUPIED sign:
    jagrat (awake)     — own or exaltation sign        -> full results
    swapna (dreaming)  — friend's or neutral's sign    -> medium results
    sushupti (sleeping)— enemy's sign or debilitation  -> nil results

This is the same "Prabuddha / Jagrad" state ch.11's bhava judgment keys its own-or-exalt prosperity
clause on (BPHS-11:14) — encoded here as a first-class avastha in its own right, using the
relationship doctrine of ch.3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS, naisargika

STATE_SOURCE: Final[Citation] = Citation("BPHS-45", 77)

#: Result grade per state (BPHS-45:89 — full / medium / nil).
RESULT_GRADE: Final[dict[str, float]] = {"jagrat": 1.0, "swapna": 0.5, "sushupti": 0.0}


def _signs_owned(planet: str) -> tuple[int, ...]:
    return tuple(s for s, lord in SIGN_LORDS.items() if lord == planet)


def _debilitation_sign(planet: str) -> int:
    return ((EXALTATION[planet] - 1 + 6) % 12) + 1     # 7th from exaltation


@dataclass(frozen=True)
class JagradadiAvastha:
    state: str          # jagrat | swapna | sushupti
    grade: float        # 1.0 | 0.5 | 0.0


def jagradadi_avastha(planet: str, sign: int) -> JagradadiAvastha:
    """The Jagradadi state of `planet` occupying `sign` (1..12).

    Own/exaltation -> jagrat; debilitation or an enemy's sign -> sushupti; a friend's or neutral's
    sign -> swapna. Defined for the seven grahas (ch.3's relationship formula has no nodes).
    """
    if planet not in EXALTATION:
        raise ValueError(f"Jagradadi is defined for the seven grahas, not {planet!r}")
    if not 1 <= sign <= 12:
        raise ValueError(f"sign must be 1..12, got {sign}")

    if sign in _signs_owned(planet) or sign == EXALTATION[planet]:
        state = "jagrat"
    elif sign == _debilitation_sign(planet):
        state = "sushupti"
    else:
        rel = naisargika(planet, SIGN_LORDS[sign])     # to the lord of the occupied sign
        state = "swapna" if rel in ("mitra", "sama") else "sushupti"
    return JagradadiAvastha(state=state, grade=RESULT_GRADE[state])


def jagradadi_from_longitude(longitude: float, planet: str) -> JagradadiAvastha:
    """Convenience: Jagradadi state straight from a sidereal longitude."""
    return jagradadi_avastha(planet, int(longitude % 360.0 // 30) + 1)
