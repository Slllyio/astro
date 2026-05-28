"""Structured yoga instance type used across the causal pipeline.

This is the unit the YSH-CM (Yoga-Slot Hierarchical Causal Model) trains
over. Each yoga detector produces zero or more ``YogaInstance``s; the
model gates each one by ``strength × dasha_activation × transit_modulation``
and learns a per-event-class weight per yoga slot.

Phase 0 introduces this only for Vipareeta Harsha. Phase 2 generalises it
to the full ~80-yoga catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

YogaCategory = Literal[
    "mahapurusha",       # Pancha Mahapurusha (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
    "raja",              # Raja Yogas (kendra-trikona lord interactions)
    "dhana",             # Dhana Yogas (wealth combinations)
    "vipareeta_raj",     # Vipareeta Raja Yogas (Harsha, Sarala, Vimala)
    "moon",              # Sunapha, Anapha, Durudhura, Kemadruma, Gajakesari, etc.
    "parivartana",       # Mutual sign exchange
    "kala_sarpa",        # All planets between Rahu-Ketu axis
    "neech_bhanga",      # Cancellation of debilitation
    "nabhasa",           # 32 Nabhasa Yogas (Akriti / Sankhya / Ashraya)
    "arishta",           # Affliction yogas (Visha, Daridra, Pitra Dosha, etc.)
    "wealth_fame",       # Saraswati, Lakshmi, Sankha, etc.
    "solar",             # Budha-Aditya and other Sun-based combinations
    "lunar",             # Pure Moon-based combinations
    "other",             # Reserved for non-classified entries during research
]


@dataclass(frozen=True, slots=True)
class YogaInstance:
    """A single detected yoga instance with its structural metadata.

    Fields
    ------
    name
        Human-readable name (e.g. "Vipareeta Harsha").
    category
        One of the classical categories above. Drives prior initialisation
        of the V[event_class, slot] matrix in the YSH-CM.
    participants
        Tuple of planet names that participate (e.g. ("Mercury",) for
        Vipareeta Harsha; ("Jupiter", "Moon") for Gajakesari).
    houses_activated
        1-indexed house numbers from Lagna that the yoga's outcome
        primarily affects.
    promise_axis
        Free-form tag pointing to the event-class family the yoga
        canonically influences (e.g. "career_via_adversity",
        "marriage", "fame", "death_by_disease"). Used by the YSH-CM's
        prior-initialisation logic to seed the V matrix.
    lords_involved
        Tuple of planet names that are the *lords* of the houses
        activated. Often the same as ``participants`` but not always —
        in a Raj Yoga where the 9th lord aspects the 10th lord, both
        lords are involved but a 3rd planet may be the actual
        aspecter (a participant).
    strength
        Continuous strength score in [0, 1]. Phase 0 computes this from
        Sthana-bala / 210; Phase 1 expands to full Shadbala.
    """

    name: str
    category: YogaCategory
    participants: tuple[str, ...]
    houses_activated: tuple[int, ...]
    promise_axis: str
    lords_involved: tuple[str, ...]
    strength: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.strength <= 1.0):
            raise ValueError(
                f"strength out of range [0, 1]: {self.strength!r}"
            )
        for h in self.houses_activated:
            if not (1 <= h <= 12):
                raise ValueError(
                    f"houses_activated must be in 1..12: {h!r}"
                )


__all__ = ["YogaInstance", "YogaCategory"]
