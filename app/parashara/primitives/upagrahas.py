"""The five Sun-derived upagrahas (Aprakasa grahas) — BPHS ch.3 sl.61-64.

Dhuma, Vyatipata, Parivesha, Indrachapa (Chapa / Indra Dhanus) and Upaketu are "planets devoid of
splendour, malefics by nature", computed by a fixed arithmetic chain from the Sun's longitude
(BPHS-3:1173). Together with Gulika/Mandi (the Saturn-based upagraha, `chart.gulika`) they complete
the sub-planet set.

    Dhuma      = Sun + 133 deg 20'
    Vyatipata  = 360 deg - Dhuma           ("reduce Dhooma from 12 signs")
    Parivesha  = Vyatipata + 180 deg
    Indrachapa = 360 deg - Parivesha       ("deduct Parivesha from 12 signs")
    Upaketu    = Indrachapa + 16 deg 40'

The chain carries its own proof: Parashara ends "by adding a sign to Upaketu, you get the original
longitude of the Sun", i.e. Upaketu + 30 deg == Sun (mod 360). This identity holds for the sloka's
prose chain above and is asserted in `demo()`. (The Santhanam Notes table prints an inconsistent
"Dhooma + 53 deg 20' = Vyatipata"; the sloka prose is authoritative and it, not the table, satisfies
the closing identity.)
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-3", 1173)      # sl.61-64, "Add 4 signs 13 degrees 20'..."

_DHUMA_OFFSET: Final[float] = 133.0 + 20.0 / 60.0       # 4 signs 13 deg 20'
_UPAKETU_OFFSET: Final[float] = 16.0 + 40.0 / 60.0      # 16 deg 40'

UPAGRAHA_NAMES: Final[tuple[str, ...]] = (
    "Dhuma", "Vyatipata", "Parivesha", "Indrachapa", "Upaketu")


def upagrahas(sun_longitude: float) -> dict[str, float]:
    """The five Sun-derived upagraha longitudes (0..360), from the Sun's longitude (BPHS-3:1173)."""
    sun = sun_longitude % 360.0
    dhuma = (sun + _DHUMA_OFFSET) % 360.0
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachapa + _UPAKETU_OFFSET) % 360.0
    return {"Dhuma": dhuma, "Vyatipata": vyatipata, "Parivesha": parivesha,
            "Indrachapa": indrachapa, "Upaketu": upaketu}


def upagraha_signs(sun_longitude: float) -> dict[str, int]:
    """Each upagraha's sign (1..12)."""
    return {name: int(lon // 30.0) + 1 for name, lon in upagrahas(sun_longitude).items()}


def demo() -> None:
    """Self-check: Parashara's closing identity Upaketu + 1 sign == Sun (BPHS-3:1173)."""
    for sun in (0.0, 12.97, 173.99, 288.5, 359.9):
        up = upagrahas(sun)
        assert abs(((up["Upaketu"] + 30.0) % 360.0) - (sun % 360.0)) < 1e-9, sun


if __name__ == "__main__":
    demo()
    print("[upagrahas] Upaketu + 1 sign == Sun holds for all test longitudes")
