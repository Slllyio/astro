"""Sudarshana Chakra — the three-lagna house view (BPHS ch.74).

Parashara's three-fold confirmation: a matter is read not from the Lagna alone but from three
reference points at once — the Ascendant, the Moon (Chandra Lagna) and the Sun (Surya Lagna).
"The Ascendant, the Moon and the Sun represent the first house; the 2nd, 3rd ... upto 12th from the
Moon and the Sun" are counted likewise (BPHS-74:91). A significance confirmed from all three circles
is the strongest reading.

This computes, for every body, the house it occupies from each of the three references, and the
occupants of each house from each reference — the positional substrate of the chakra. Pure whole-sign
arithmetic (the project's locked convention); the per-house effect prose of ch.74 is not force-graded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-74", 91)     # "Ascendant, the Moon and the Sun ... first house"

REFERENCES: Final[tuple[str, ...]] = ("Lagna", "Moon", "Sun")


def _sign(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def _reference_signs(chart) -> dict[str, int]:
    """The three reference signs: Lagna (ascendant sign), the Moon's sign, the Sun's sign."""
    return {"Lagna": chart.asc_sign,
            "Moon": _sign(chart.longitudes["Moon"]),
            "Sun": _sign(chart.longitudes["Sun"])}


@dataclass(frozen=True)
class SudarshanaPosition:
    body: str
    from_lagna: int      # house 1..12 from the Ascendant
    from_moon: int       # house 1..12 from the Moon (Chandra Lagna)
    from_sun: int        # house 1..12 from the Sun (Surya Lagna)


def sudarshana_positions(chart) -> dict[str, SudarshanaPosition]:
    """Every body's house from each of the three references (Lagna, Moon, Sun)."""
    refs = _reference_signs(chart)
    out: dict[str, SudarshanaPosition] = {}
    for body, lon in chart.longitudes.items():
        s = _sign(lon)
        out[body] = SudarshanaPosition(
            body=body,
            from_lagna=((s - refs["Lagna"]) % 12) + 1,
            from_moon=((s - refs["Moon"]) % 12) + 1,
            from_sun=((s - refs["Sun"]) % 12) + 1,
        )
    return out


def house_occupants(chart, reference: str) -> dict[int, list[str]]:
    """{house 1..12: bodies in it} counted from one reference ('Lagna' | 'Moon' | 'Sun')."""
    if reference not in REFERENCES:
        raise ValueError(f"reference must be one of {REFERENCES}, got {reference!r}")
    ref_sign = _reference_signs(chart)[reference]
    out: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for body, lon in chart.longitudes.items():
        house = ((_sign(lon) - ref_sign) % 12) + 1
        out[house].append(body)
    return out


def confirmed_occupied(chart) -> dict[int, list[str]]:
    """Houses (numbered from the Lagna) that a body occupies in ALL THREE circles simultaneously —
    the strongest Sudarshana testimony. Keyed by the Lagna house; value = the bodies so placed."""
    pos = sudarshana_positions(chart)
    out: dict[int, list[str]] = {}
    for body, p in pos.items():
        if p.from_lagna == p.from_moon == p.from_sun:
            out.setdefault(p.from_lagna, []).append(body)
    return out
