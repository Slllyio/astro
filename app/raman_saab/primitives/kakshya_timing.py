"""Kakshya time-division of Dasa periods — ASP ch.XII (Timing Events).

Three of Raman's timing devices, all riding on the Kakshya order and the Prasthara donors:

1. **The Dasa lord's natal Kakshya** (ASP-12:62-65): "Find out the Kakshya occupied by the
   Dasa lord. If there is a bindu in this particular Kakshya (in the Dasa lord's
   Ashtakavarga), the lord will be inclined to confer favourable results." The judgment is the
   same one `kakshya.transit_kakshya_reading` makes — applied to the lord's NATAL longitude.

2. **The eightfold division of a period** (ASP-12:174-182): "the period of a Dasa can be
   divided into 8 equal parts in the order of the orbits of the different planets from the
   earth ... the first and subsequent parts will be symbolically ruled by Saturn, Jupiter,
   Mars, Sun, Venus, Mercury, Moon and the Lagna" — the Kakshya order again, now in TIME.
   Raman reports the scheme as "some scholars opine" but immediately works it on the Standard
   Horoscope and later extends it to sub-periods with his own endorsement ("It has also been
   found that ...", ASP-12:305-311; "It occurs to me that this method of interpreting Dasas
   offers a vast field for research"). Encoded as he worked it; the report layer should carry
   his attribution tone, not upgrade it to a decree.

3. **The per-interval judgment** (ASP-12:211-219 + 305-311): the interval ruled by R runs
   adverse when R "has not contributed a bindu to the sign occupied by" the period lord (in
   the period lord's own Ashtakavarga), favourable when it has — and an adverse interval is
   NEUTRALISED when R's own two signs hold good bindus in that same Ashtakavarga ("But
   Saturn['s] two Rasis (in Jupiter's Ashtakavarga) have 5 and 4 bindus respectively so that
   the evil ... gets neutralised", ASP-12:215-219). Raman's neutralisation example has 5 and 4
   — both at or above the optimum 4 of the sub-period rule (ASP-12:76-80) — so the encoded
   bar is `>= 4` in BOTH owned signs, the only numeric reading his worked case supports.
   The Sun and Moon own one sign each; their single sign carries the test alone. The Lagna
   interval has no owned signs — never neutralised, judged on its donation only.

Usage:
    from app.raman_saab.primitives import kakshya_timing as kt
    kt.dasa_lord_natal_kakshya(chart, "Jupiter")        # device 1
    for iv in kt.kakshya_intervals(chart, "Jupiter", start_jd, end_jd):
        iv.ruler, iv.start_jd, iv.end_jd, iv.favourable, iv.neutralised
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.ashtakavarga import PLANETS, bhinnashtakavarga, prasthara
from app.raman_saab.primitives.kakshya import KAKSHYA_ORDER, KakshyaReading
from app.raman_saab.primitives.kakshya import transit_kakshya_reading as _reading

#: sign(s) owned by each interval ruler, for the neutralisation test (Lagna owns none).
_OWNED: Final[dict[str, tuple[int, ...]]] = {
    "Sun": (5,), "Moon": (4,), "Mars": (1, 8), "Mercury": (3, 6),
    "Jupiter": (9, 12), "Venus": (2, 7), "Saturn": (10, 11), "Lagna": (),
}

#: the neutralisation bar: Raman's worked case neutralises on owned-sign bindus of 5 and 4 —
#: both at/above the optimum 4 his sub-period rule names (ASP-12:76-80).
_NEUTRALISE_MIN: Final[int] = 4


def dasa_lord_natal_kakshya(chart: RamanChart, lord: str) -> KakshyaReading | None:
    """Device 1 (ASP-12:62-65): the Dasa lord's NATAL Kakshya, judged in its own Ashtakavarga.

    None when the lord has no Ashtakavarga (nodes) or is absent — an undecidable, not an
    adverse."""
    p = chart.planets.get(lord)
    if p is None or lord not in PLANETS:
        return None
    return _reading(chart, lord, p.lon)


@dataclass(frozen=True)
class KakshyaInterval:
    """One eighth of a Dasa/sub-period, symbolically ruled in Kakshya order (ASP-12:174-182)."""

    ruler: str
    start_jd: float
    end_jd: float
    donated: bool                  # ruler contributed a bindu to the period lord's natal sign
    neutralised: bool              # adverse-but-neutralised (ASP-12:215-219); False when donated

    @property
    def favourable(self) -> bool:
        return self.donated

    @property
    def adverse_unrelieved(self) -> bool:
        return not self.donated and not self.neutralised


def kakshya_intervals(chart: RamanChart, period_lord: str,
                      start_jd: float, end_jd: float) -> tuple[KakshyaInterval, ...]:
    """Divide [start_jd, end_jd) into the eight Kakshya-order intervals and judge each
    (ASP-12:174-182, 211-219, 305-311).

    The judgment sign is the PERIOD LORD's natal sign, in the period lord's own Ashtakavarga —
    exactly Raman's worked case ("Saturn has not contributed a bindu to the sign occupied by
    Jupiter. Hence the first two years ... should be adverse", ASP-12:211-214). Returns () for
    a lord with no Ashtakavarga (nodes): the scheme is undefined there, not adverse."""
    p = chart.planets.get(period_lord)
    if p is None or period_lord not in PLANETS:
        return ()
    donors = prasthara(chart, period_lord)[p.sign]
    bav = bhinnashtakavarga(chart, period_lord)
    span = (end_jd - start_jd) / 8.0
    out = []
    for i, ruler in enumerate(KAKSHYA_ORDER):
        donated = ruler in donors
        neut = (not donated
                and bool(_OWNED[ruler])
                and all(bav[s] >= _NEUTRALISE_MIN for s in _OWNED[ruler]))
        out.append(KakshyaInterval(
            ruler=ruler, start_jd=start_jd + i * span, end_jd=start_jd + (i + 1) * span,
            donated=donated, neutralised=neut))
    return tuple(out)
