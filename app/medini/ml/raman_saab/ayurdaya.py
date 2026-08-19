"""Ayurdaya (longevity band) — the Jaimini/Raman three-pairs method. Leg 3.

Computes the classical Alpayu / Madhyayu / Purnayu longevity band from the
natal chart. Method and every textual ambiguity are pinned in
``docs/raman_saab/RUN3_PREREG.md`` (pins P1–P12); the pin IDs are referenced
inline below. Full Parashari BPHS Ch.43 (Pindayu/Amsayu/Nisargayu + haranas)
is pre-registered OUT of scope for run 3 (pin P1): it needs Shadbala at
population scale plus ~a dozen additional harana ambiguity pins, and emits a
year count rather than the band the Triple-Lock indicator consumes.

## The three pairs (P2) ⚑

1. **Lagna & Lagna-lord** — the lagna sign and the sign occupied by the
   lagna's ruler.
2. **Moon & Saturn** — the signs occupied by the natal Moon and Saturn.
3. **Lagna & Hora Lagna** — the lagna sign and the Hora-Lagna sign (P8).

Each pair votes a band from the modalities of its two signs (P3) ⚑:

    chara+chara  or sthira+dvisvabhava  -> Purnayu  (full life)
    dvisvabhava+dvisvabhava or chara+sthira -> Madhyayu (middle life)
    sthira+sthira or chara+dvisvabhava  -> Alpayu   (short life)

Majority vote (2 of 3) decides; on a three-way split the **Lagna & Hora-Lagna
pair prevails** (P7) ⚑, with the tie recorded for audit and a pre-registered
sensitivity rerun using Madhyayu-fallback instead.

## Hora Lagna (P8) ⚑

``HL(t) = sun_sidereal_lon(sunrise) + 30° × hours since sunrise``, mod 360 —
the HL advances one sign per hour from the Sun's longitude at the sunrise
preceding birth. Sunrise via ``swe.rise_trans`` (disc-center, swisseph default
refraction, ``FLG_MOSEPH``) anchored at birth_jd − 1, matching the strategy in
``app/reading/computations/gulika.py`` (P9). The mid-sign v1 stub in
``special_lagnas.py`` is deliberately NOT reused. Persons at |lat| > 60° are
excluded upstream (circumpolar sunrise risk, P9).

Classical exceptions — Saturn-in-lagna modification, Balarishta overrides,
kakshya hrasa/vriddhi, mrityu-bhaga — are pre-registered as NOT applied in v1
(P11); the samasaptaka (mutual-7th) reversal is recorded on the PairVerdict
but never applied (P5).

Band cutoffs for scoring observed deaths (P6) ⚑: Alpayu death age < 32,
Madhyayu 32 ≤ age < 70, Purnayu 70 ≤ age ≤ 120 (closed-left, half-open right).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final

import swisseph as swe

from app.medini.ml.raman_saab.kundali import SIGN_RULER, Kundali, _nth_sign

# ── Modalities (1 Aries .. 12 Pisces) ────────────────────────────────────────
_CHARA: Final = frozenset({1, 4, 7, 10})        # movable
_STHIRA: Final = frozenset({2, 5, 8, 11})       # fixed
_DVISVABHAVA: Final = frozenset({3, 6, 9, 12})  # dual


class AyuBand(IntEnum):
    ALPAYU = 0
    MADHYAYU = 1
    PURNAYU = 2


# P6 cutoffs (years). Closed-left, half-open right.
ALPAYU_MAX: Final = 32.0
MADHYAYU_MAX: Final = 70.0
PURNAYU_MAX: Final = 120.0


def modality(sign: int) -> str:
    if sign in _CHARA:
        return "chara"
    if sign in _STHIRA:
        return "sthira"
    if sign in _DVISVABHAVA:
        return "dvisvabhava"
    raise ValueError(f"sign out of range: {sign}")


def pair_band(sign_a: int, sign_b: int) -> AyuBand:
    """Band voted by one pair of signs, per the P3 modality table."""
    ma, mb = modality(sign_a), modality(sign_b)
    pair = {ma, mb}
    if pair == {"chara"} or pair == {"sthira", "dvisvabhava"}:
        return AyuBand.PURNAYU
    if pair == {"dvisvabhava"} or pair == {"chara", "sthira"}:
        return AyuBand.MADHYAYU
    # sthira+sthira or chara+dvisvabhava
    return AyuBand.ALPAYU


def band_of_age(age_years: float) -> AyuBand:
    """Observed band of a death age, per the P6 cutoffs."""
    if age_years < ALPAYU_MAX:
        return AyuBand.ALPAYU
    if age_years < MADHYAYU_MAX:
        return AyuBand.MADHYAYU
    return AyuBand.PURNAYU


# ── Sunrise + Hora Lagna (P8/P9) ─────────────────────────────────────────────

def sunrise_before(birth_jd: float, lat: float, lon: float,
                   *, epheflag: int = swe.FLG_MOSEPH) -> float:
    """JD of the sunrise immediately preceding ``birth_jd``.

    Anchors at birth_jd − 1 and takes rises until one lands past birth_jd
    (same anchor strategy as ``gulika._sunrise_sunset``, Moshier-flagged).
    Raises RuntimeError on swisseph failure (e.g. circumpolar).
    """
    geopos = (lon, lat, 0.0)
    t = birth_jd - 1.0
    prev: float | None = None
    for _ in range(4):  # at most a few iterations; guards odd polar cases
        status, tret = swe.rise_trans(t, swe.SUN, swe.CALC_RISE, geopos,
                                      0.0, 0.0, epheflag)
        if status < 0 or not tret:
            raise RuntimeError(f"rise_trans failed: status={status}")
        rise = tret[0]
        if rise > birth_jd:
            if prev is None:
                # birth within a day of the anchor's first rise: step back
                t -= 1.0
                continue
            return prev
        prev = rise
        t = rise + 1e-4  # nudge past this rise to find the next
    if prev is None:
        raise RuntimeError("no sunrise found preceding birth")
    return prev


_LAHIRI_SET = False


def _sun_sidereal_lon(jd: float) -> float:
    global _LAHIRI_SET
    if not _LAHIRI_SET:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        _LAHIRI_SET = True
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    return float(swe.calc_ut(jd, swe.SUN, flags)[0][0]) % 360.0


def hora_lagna_lon(birth_jd: float, sunrise_jd: float) -> float:
    """P8: HL = Sun's sidereal longitude at sunrise + 30° per hour elapsed."""
    hours = (birth_jd - sunrise_jd) * 24.0
    return (_sun_sidereal_lon(sunrise_jd) + 30.0 * hours) % 360.0


# ── The three-pair computation ───────────────────────────────────────────────

@dataclass(frozen=True)
class PairVerdict:
    pair_id: str          # "lagna_lagnalord" | "moon_saturn" | "lagna_horalagna"
    member_a: str
    member_b: str
    sign_a: int
    sign_b: int
    modality_a: str
    modality_b: str
    band: AyuBand
    same_sign: bool       # P4 audit flag (degenerate same-modality cell)
    mutual_7th: bool      # P5: recorded, never applied in v1


@dataclass(frozen=True)
class AyurdayaResult:
    band: AyuBand
    votes: tuple[AyuBand, AyuBand, AyuBand]
    pairs: tuple[PairVerdict, PairVerdict, PairVerdict]
    tie_broken: bool
    tie_rule: str | None
    sunrise_jd: float
    hora_lagna_lon: float
    hora_lagna_sign: int


def _verdict(pair_id: str, member_a: str, member_b: str,
             sign_a: int, sign_b: int) -> PairVerdict:
    return PairVerdict(
        pair_id=pair_id, member_a=member_a, member_b=member_b,
        sign_a=sign_a, sign_b=sign_b,
        modality_a=modality(sign_a), modality_b=modality(sign_b),
        band=pair_band(sign_a, sign_b),
        same_sign=sign_a == sign_b,
        mutual_7th=((sign_b - sign_a) % 12) == 6,
    )


def planet_sign(k: Kundali, planet: str) -> int:
    """Whole-sign identity: a planet in house h occupies the h-th sign."""
    return _nth_sign(k.lagna_sign, k.planet_house[planet])


def compute_ayurdaya(k: Kundali, lat: float, lon: float) -> AyurdayaResult:
    """The three-pairs ayurdaya band for one kundali (P1–P11)."""
    lagna_lord = SIGN_RULER[k.lagna_sign]
    p1 = _verdict("lagna_lagnalord", "Lagna", lagna_lord,
                  k.lagna_sign, planet_sign(k, lagna_lord))
    p2 = _verdict("moon_saturn", "Moon", "Saturn",
                  planet_sign(k, "Moon"), planet_sign(k, "Saturn"))
    sunrise_jd = sunrise_before(k.birth_jd, lat, lon)
    hl_lon = hora_lagna_lon(k.birth_jd, sunrise_jd)
    hl_sign = int(hl_lon // 30.0) + 1
    p3 = _verdict("lagna_horalagna", "Lagna", "HoraLagna",
                  k.lagna_sign, hl_sign)

    votes = (p1.band, p2.band, p3.band)
    counts = {b: votes.count(b) for b in set(votes)}
    best, best_n = max(counts.items(), key=lambda kv: kv[1])
    if best_n >= 2:
        band, tie_broken, tie_rule = best, False, None
    else:
        # P7: three-way split -> Lagna & Hora-Lagna pair prevails.
        band, tie_broken, tie_rule = p3.band, True, "lagna_horalagna_prevails"
    return AyurdayaResult(
        band=band, votes=votes, pairs=(p1, p2, p3),
        tie_broken=tie_broken, tie_rule=tie_rule,
        sunrise_jd=sunrise_jd, hora_lagna_lon=hl_lon, hora_lagna_sign=hl_sign,
    )
