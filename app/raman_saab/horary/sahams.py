"""Sahams — the ten Raman prints, with his day/night formulas (VARSHA-7:84-190).

The general rule (VARSHA-7:84-99): saham = minuend − subtrahend + Lagna; "if from the
position of the minuend to that of the subtrahend there is no lagna, 30 degrees must be
added" — i.e. when the ascendant does NOT lie on the zodiacal arc from subtrahend to
minuend, add 30. Worked example pinned: Punya = 105°21' + 285°9' = 30°30' casting off 360,
with no +30 because "the ascendant is between the Moon and the Sun" (VARSHA-7:100-117).

The ten printed sahams (VARSHA-7:100-171), day formula first, night swaps minuend and
subtrahend unless marked "Day or Night":
Punya (Moon−Sun), Guru (Sun−Moon), Kirti (Jupiter−Punya Saham), Mitra (Guru Saham−Punya
Saham, then +Venus as the lagna-term base — see note), Raja (Saturn−Sun), Putra
(Jupiter−Moon, day or night), Jeeva (Saturn−Jupiter), Vyapara (Mars−Mercury), Vivaha
(Venus−Saturn, day or night), Satru (Mars−Saturn).

MITRA note (VARSHA-7:130-136): the one saham whose printed formula ADDS VENUS in place of
the general rule's lagna term — "Day: (Guru Saham − Punya Saham) + Sukra". Encoded exactly
so, with the +30 no-lagna-between check still made against the true lagna (the general
rule's own wording). The printed Night line is OCR-mangled ("+" where the day/night swap
pattern of every other saham implies the swapped difference); the swap pattern is applied
and this reading is recorded here, not silently corrected.

"Vidya" and "Karya" sahams (requested by an outside plan document) are NOT in Raman's
printed table and are therefore NOT encoded — Neelakantha knows 50 sahams, Raman prints
these ten (VARSHA-7:84-87), and the print governs.

Lords (VARSHA-7:190-192): "The lords of the rasis in which the longitudes of the various
sahams fall will be respectively the lords of such sahams."

Usage:
    from app.raman_saab.horary.sahams import compute_sahams, saham_longitude
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class Saham:
    name: str
    lon: float
    rasi: int                  # 1..12
    lord: str
    source: Citation


def _lagna_between(subtrahend: float, minuend: float, lagna: float) -> bool:
    """Is the lagna on the zodiacal arc travelling from subtrahend forward to minuend?"""
    arc = (minuend - subtrahend) % 360.0
    return (lagna - subtrahend) % 360.0 <= arc


def saham_longitude(minuend: float, subtrahend: float, lagna: float,
                    added_term: float | None = None) -> float:
    """The VARSHA-7:84-99 rule: minuend − subtrahend + lagna, +30 when the lagna is not
    between subtrahend and minuend. `added_term` overrides the additive lagna term (the
    Mitra saham adds Venus instead — VARSHA-7:130-136); the between-check always uses the
    true lagna, per the general rule's own wording."""
    s = ((minuend - subtrahend) % 360.0 + (lagna if added_term is None else added_term)) % 360.0
    if not _lagna_between(subtrahend, minuend, lagna):
        s = (s + 30.0) % 360.0
    return s


#: (day_minuend, day_subtrahend, day_or_night_fixed). Keys into the positions dict or the
#: sahams-so-far dict ("Punya"/"Guru Saham"). Night swaps the pair unless fixed.
_FORMULAS: Final[tuple[tuple[str, str, str, bool], ...]] = (
    ("Punya", "Moon", "Sun", False),                 # VARSHA-7:100-117
    ("Guru", "Sun", "Moon", False),                  # VARSHA-7:118-120
    ("Kirti", "Jupiter", "Punya", False),            # VARSHA-7:124-128
    ("Mitra", "Guru", "Punya", False),               # VARSHA-7:130-136 (see MITRA note)
    ("Raja", "Saturn", "Sun", False),                # VARSHA-7:138-141
    ("Putra", "Jupiter", "Moon", True),              # VARSHA-7:143-145
    ("Jeeva", "Saturn", "Jupiter", False),           # VARSHA-7:147-150
    ("Vyapara", "Mars", "Mercury", False),           # VARSHA-7:155-158
    ("Vivaha", "Venus", "Saturn", True),             # VARSHA-7:160-162
    ("Satru", "Mars", "Saturn", False),              # VARSHA-7:164-167
)

def compute_sahams(positions: dict[str, float], lagna: float, *, is_day: bool
                   ) -> tuple[Saham, ...]:
    """All ten printed sahams for a chart moment. `positions` maps the seven grahas to
    longitudes; Kirti/Mitra reference earlier sahams and are computed in table order."""
    done: dict[str, float] = {}
    out: list[Saham] = []
    for name, day_min, day_sub, fixed in _FORMULAS:
        m_key, s_key = (day_min, day_sub) if (is_day or fixed) else (day_sub, day_min)
        minuend = positions.get(m_key, done.get(m_key, 0.0))
        subtrahend = positions.get(s_key, done.get(s_key, 0.0))
        added = positions["Venus"] if name == "Mitra" else None    # VARSHA-7:130-136
        lon = saham_longitude(minuend, subtrahend, lagna, added_term=added)
        done[name] = lon
        rasi = int(lon // 30.0) + 1
        out.append(Saham(name, lon, rasi, SIGN_LORDS[rasi], Citation("VARSHA-7", 84)))
    return tuple(out)
