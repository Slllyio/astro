"""Vimsopaka bala — Parashara's 20-point cross-varga strength (BPHS ch.7, slokas 17-27).

The question Vimsopaka asks is orthogonal to Shadbala. Shadbala measures six kinds of strength in
ONE chart; Vimsopaka asks **how well a planet holds its dignity across the divisional charts at
once**. A planet exalted in the rasi but in an enemy's navamsa and an enemy's dwadasamsa is, to
Parashara, not strong — it is a promise the divisions do not keep.

## The four schemes (BPHS-7:220-265; every one totals exactly 20)

Parashara gives four, and the astrologer picks the one being worked
(``BPHS-7:295`` — "whichever is being considered by the astrologer"):

* **Shadvarga** (6)  — Rasi 6, Hora 2, Drekkana 4, Navamsa 5, Dwadasamsa 2, Trimsamsa 1
  ("The full strength, for each of the divisions respectively are 6, 2, 4, 5, 2 and 1", BPHS-7:220)
* **Saptavarga** (7) — adds Saptamsa; 5, 2, 3, 2½, 4½, 2, 1 (BPHS-7:224)
* **Dasavarga** (10) — adds Dasamsa, Shodasamsa, Shashtiamsa; "3 for Rasi, 5 for Shashtiamsa and
  [1½] for the other 8 divisions" (BPHS-7:238)
* **Shodasavarga** (16) — "Hora 1, Trimsamsa 1, decanate 1, Shodasamsa 2, Navamsa 3, Rasi 3½,
  Shashtiamsa 4, and the rest of the nine divisions each a half" (BPHS-7:265)

**Two values were lost by the OCR and are recovered by Parashara's own arithmetic, not guessed:**
the Dasavarga per-division figure (the scan reads "and for the other 8 divisions, each" with the
number missing) and the Shodasavarga Trimsamsa figure (scanned as "V"). Each scheme must total 20;
solving gives 1½ and 1 respectively, and both are cross-checked by the chapter's own tabulation
(BPHS-7:301+, where the Dasa column reads 1.5 for Hora/Drekkana/Navamsa/Dwadasamsa). The totals
are re-asserted in the tests, so a future re-OCR that shifts these cannot pass silently.

## Varga Viswa — the 6-tier dignity scale (BPHS-7:265-272)

The full weight is earned only in one's OWN varga; otherwise it declines by relationship:

    own 20 · extreme friend 18 · friend 15 · equal 10 · enemy 7 · sworn enemy 5

This is Parashara's own scale and it is **materially different from the coarse
exalt/own/neutral/debilitated model** an engine might reach for by default: note there is no
"exalted" tier (exaltation is not a varga-dignity here) and no zero — even a sworn enemy's varga
yields 5 of 20, so Vimsopaka never bottoms out at nothing.

## The computation (BPHS-7:283 "VIMSOPAKA PROPORTIONAL EVALUATION")

    "Multiply the figure due to full strength for the division by the Varga Viswa and divide by 20"

        score = Σ over divisions ( weight_d × viswa_d / 20 )      -> 0..20

## Parashara's own interpretation bands (BPHS-7:286-290)

    < 5   "not capable of giving auspicious results"
    5-10  "will yield some good effects"
    10-15 "indicative of mediocre effect"
    > 15  "will yield wholly favourable effects"

Usage:
    from app.parashara.primitives.vimsopaka import vimsopaka, SCHEMES
    r = vimsopaka("Jupiter", {"D1": 4, "D2": 5, ...}, scheme="saptavarga")
    r.score, r.band          # 14.2, 'mediocre'
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

# --------------------------------------------------------------------------- #
# The four schemes — BPHS ch.7 slokas 17-25. Each totals exactly 20.           #
# --------------------------------------------------------------------------- #

SHADVARGA: Final[Mapping[str, float]] = {
    "D1": 6.0, "D2": 2.0, "D3": 4.0, "D9": 5.0, "D12": 2.0, "D30": 1.0,
}
# NOTE (doctrine audit, 2026-08-22): the ch.7 PROSE sloka gives Navamsa 4.5 / Dwadasamsa 2.5 (D9 the
# heaviest sub-Rasi weight, consistent with Shadvarga's D9=5 and Shodasavarga's D9=3). The chapter's
# printed TABLE (chapter_007_*.md:347,355) shows these two TRANSPOSED (D9=2.5, D12=4.5) — an OCR/
# typesetting artifact that demotes Navamsa below Dwadasamsa. The prose reading here is correct and
# is independently corroborated by the repo's other engine (app/core/vimsopaka_bala.py: "Navamsa —
# heaviest" = 4.5). Do NOT "fix" this to match the corrupted table.
SAPTAVARGA: Final[Mapping[str, float]] = {
    "D1": 5.0, "D2": 2.0, "D3": 3.0, "D7": 2.5, "D9": 4.5, "D12": 2.0, "D30": 1.0,
}
DASAVARGA: Final[Mapping[str, float]] = {
    "D1": 3.0, "D60": 5.0,
    "D2": 1.5, "D3": 1.5, "D7": 1.5, "D9": 1.5,
    "D10": 1.5, "D12": 1.5, "D16": 1.5, "D30": 1.5,
}
SHODASAVARGA: Final[Mapping[str, float]] = {
    "D1": 3.5, "D2": 1.0, "D3": 1.0, "D9": 3.0, "D16": 2.0, "D30": 1.0, "D60": 4.0,
    "D4": 0.5, "D7": 0.5, "D10": 0.5, "D12": 0.5,
    "D20": 0.5, "D24": 0.5, "D27": 0.5, "D40": 0.5, "D45": 0.5,
}

SCHEMES: Final[Mapping[str, Mapping[str, float]]] = {
    "shadvarga": SHADVARGA,
    "saptavarga": SAPTAVARGA,
    "dasavarga": DASAVARGA,
    "shodasavarga": SHODASAVARGA,
}

#: Each scheme's defining sloka, for the record a reading shows.
SCHEME_SOURCE: Final[Mapping[str, Citation]] = {
    "shadvarga": Citation("BPHS-7", 220),
    "saptavarga": Citation("BPHS-7", 224),
    "dasavarga": Citation("BPHS-7", 238),
    "shodasavarga": Citation("BPHS-7", 265),
}

# --------------------------------------------------------------------------- #
# Varga Viswa — the dignity scale, BPHS-7:265-272                              #
# --------------------------------------------------------------------------- #

#: relationship of the planet to the lord of the sign it occupies IN that division -> points/20.
VARGA_VISWA: Final[Mapping[str, float]] = {
    "own": 20.0,
    "adhi_mitra": 18.0,    # extreme friend
    "mitra": 15.0,         # friend
    "sama": 10.0,          # equal
    "shatru": 7.0,         # enemy
    "adhi_shatru": 5.0,    # sworn enemy
}
VISWA_SOURCE: Final[Citation] = Citation("BPHS-7", 272)

#: Parashara's own bands (BPHS-7:286-290), as (inclusive upper bound, label, his own phrasing).
_BANDS: Final[tuple[tuple[float, str, str], ...]] = (
    (5.0, "inauspicious", "not capable of giving auspicious results"),
    (10.0, "some-good", "will yield some good effects"),      # exclusive upper; see band_for
    (15.0, "mediocre", "indicative of mediocre effect"),
    (20.0, "wholly-favourable", "will yield wholly favourable effects"),
)
BANDS_SOURCE: Final[Citation] = Citation("BPHS-7", 286)

#: The lowest score the scale can produce: every division at sworn-enemy = 20 * (5/20).
#: See `band_for` — this is what settles the open boundary in Parashara's wording.
MINIMUM_POSSIBLE_SCORE: Final[float] = 5.0


@dataclass(frozen=True)
class VimsopakaScore:
    """One planet's Vimsopaka strength under one scheme."""
    planet: str
    scheme: str
    score: float                          # 0..20
    band: str                             # inauspicious | some-good | mediocre | wholly-favourable
    verdict: str                          # Parashara's own phrasing for the band
    per_varga: Mapping[str, float]        # division -> its contribution (weight * viswa / 20)
    source: Citation


def band_for(score: float) -> tuple[str, str]:
    """Parashara's band for a 0..20 Vimsopaka score, as (label, his own phrasing).

    The sloka reads: "below 5 ... not capable of giving auspicious results. If it is above 5 but
    below 10 ... some good effects. Later on upto 15 ... mediocre effect. A planet with above 15
    will yield wholly favourable effects" (BPHS-7:286-290). That wording leaves the exact
    boundaries 5, 10 and 15 unassigned, so a faithful encoding has to settle them — and one of
    them is settled by the scale itself rather than by preference:

    **The floor of the scale IS exactly 5.0** — every division at sworn-enemy gives
    20 x (5/20) = 5.0, and no arrangement scores lower (``MINIMUM_POSSIBLE_SCORE``). Read "below 5"
    strictly and Parashara's own lowest band could never occur for any chart ever cast, which
    cannot be what he meant. So the bottom boundary is INCLUSIVE: score <= 5 is inauspicious, and
    the band is reachable exactly at the floor.

    The remaining boundaries follow his phrasing: "upto 15" is inclusive, so 15.0 is mediocre and
    "above 15" starts strictly after; 10.0 is excluded from "below 10" and so opens the mediocre
    band. Net: (-inf, 5] inauspicious - (5, 10) some-good - [10, 15] mediocre - (15, 20] wholly
    favourable.
    """
    if score <= _BANDS[0][0]:                      # <= 5.0, the reachable floor
        return _BANDS[0][1], _BANDS[0][2]
    if score < _BANDS[1][0]:                       # (5, 10)
        return _BANDS[1][1], _BANDS[1][2]
    if score <= _BANDS[2][0]:                      # [10, 15] — "upto 15"
        return _BANDS[2][1], _BANDS[2][2]
    return _BANDS[3][1], _BANDS[3][2]              # > 15 — "above 15"


def vimsopaka(planet: str, viswa_by_varga: Mapping[str, str], *,
              scheme: str = "shodasavarga") -> VimsopakaScore:
    """Vimsopaka bala for one planet.

    Args:
        planet: the graha being weighed.
        viswa_by_varga: division tag -> Varga Viswa key, i.e. the planet's relationship to the
            lord of the sign it occupies IN that division ("own", "adhi_mitra", "mitra", "sama",
            "shatru", "adhi_shatru"). Must cover every division the scheme names.
        scheme: one of SCHEMES.

    Raises:
        ValueError: unknown scheme, unknown Varga Viswa key, or a division the scheme requires but
            the caller did not supply. Failing loudly matters here — silently treating a missing
            division as `sama` would understate a strong planet and no one would notice.
    """
    try:
        weights = SCHEMES[scheme]
    except KeyError:
        raise ValueError(
            f"unknown Vimsopaka scheme {scheme!r}; Parashara gives {sorted(SCHEMES)}") from None

    missing = [d for d in weights if d not in viswa_by_varga]
    if missing:
        raise ValueError(
            f"{scheme} needs a Varga Viswa for every division; missing {missing}")

    contributions: dict[str, float] = {}
    for division, weight in weights.items():
        key = viswa_by_varga[division]
        try:
            viswa = VARGA_VISWA[key]
        except KeyError:
            raise ValueError(
                f"{division}: unknown Varga Viswa {key!r}; "
                f"Parashara's scale is {sorted(VARGA_VISWA)}") from None
        # BPHS-7:283 — "Multiply the figure due to full strength ... by the Varga Viswa, divide by 20"
        contributions[division] = weight * viswa / 20.0

    score = sum(contributions.values())
    label, phrasing = band_for(score)
    return VimsopakaScore(
        planet=planet, scheme=scheme, score=score, band=label, verdict=phrasing,
        per_varga=contributions, source=SCHEME_SOURCE[scheme])
