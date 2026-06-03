"""Orchestrate the full Shadbala (6 graha-bala components + Ishta/Kashta) for a
real, ephemeris-cast chart.

This is the *chart layer* glue: it ties the pure Shadbala primitives
(``primitives/shadbala/{sthana,dig,kala,cheshta,naisargika,drik,total,ishta_kashta}``)
together with the two ephemeris-derived context builders
(``chart/kala_context`` for the temporal facts, ``chart/mean_longitudes`` for the
Cheshta mean longitudes + seegrochchas).  The adapter calls this once per
``cast_chart`` and attaches the result to every ``PlanetPos``.

Frame consistency
-----------------
All longitudes used here are sidereal in Raman's frame (the chart's true
longitudes and the epoch-method mean longitudes share that frame, so the
Cheshta arc carries no ayanamsa).  The two places that need the *sayana*
(tropical) longitude — Ayana Bala inside Kala, and the Sun/Moon Ishta/Kashta
Cheshta surrogates — add ``ayanamsa_deg`` explicitly.

Documented carry-over (Phase 1c-3)
----------------------------------
The Kala Ahargana year/month lords are still flagged ``UNKNOWN`` in
``kala_context`` (GBB-5:343-423).  The pure Kala formulae award 0 Sh to a lord
that matches no real planet, so a real chart's Kala is (correctly) *under-counted*
by at most 45 Sh (15 Abda + 30 Masa) — never mis-counted.  This is acceptable
for Phase 1 and lands the total slightly low rather than wrong.

Usage::

    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.shadbala_compute import compute_shadbala
    import swisseph as swe
    from app.raman_saab.chart.ayanamsa import sidereal_mode

    chart = cast_chart(birth, ayanamsa="raman")
    with sidereal_mode("raman"):
        ayan = swe.get_ayanamsa_ut(chart.jd_ut)
    out = compute_shadbala(chart, birth, ayan)   # {planet: (breakdown, ishta, kashta)}
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart import kala_context as kala_context_mod
from app.raman_saab.chart import mean_longitudes as mean_longitudes_mod
from app.raman_saab.chart.model import BirthData, RamanChart, ShadbalaBreakdown
from app.raman_saab.primitives.shadbala import (
    cheshta,
    dig,
    drik,
    ishta_kashta,
    kala,
    naisargika,
    sthana,
    total,
)

# The 7 visible grahas carry Shadbala; the nodes (Rahu/Ketu) never do.
_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# Cheshta Bala is awarded only to these 5 (Sun/Moon get 0 in the total — GBB-6:23-28).
_CHESHTA_PLANETS: Final[frozenset[str]] = frozenset(
    {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
)


def compute_shadbala(
    chart: RamanChart,
    birth: BirthData,
    ayanamsa_deg: float,
) -> dict[str, tuple[ShadbalaBreakdown, float, float]]:
    """Compute the full Shadbala for the 7 visible grahas of an ephemeris chart.

    Args:
        chart: a real (ephemeris) chart with ``jd_ut`` set and Sripathi cusps.
        birth: the birth data (for the Kala temporal context — sunrise/weekday/hora).
        ayanamsa_deg: the chart's ayanamsa in degrees (``swe.get_ayanamsa_ut(jd)``
            inside the matching ``sidereal_mode``); used by Ayana Bala and the
            Sun/Moon Ishta/Kashta surrogates.

    Returns:
        ``{planet: (ShadbalaBreakdown, ishta_phala, kashta_phala)}`` for each of the
        7 visible grahas present in the chart.  Ishta/Kashta are Shashtiamsa scores
        in [0, 60]; ``ShadbalaBreakdown.total`` is in Shashtiamsas (Rupas = total/60).

    Raises:
        ValueError: if the chart has no ``jd_ut`` (a Track-B stated-positions chart);
            Shadbala cannot be derived without the birth moment.
    """
    if chart.jd_ut is None:
        raise ValueError(
            "compute_shadbala requires a real (ephemeris) chart with jd_ut set; "
            "a from_stated_positions chart has no birth moment."
        )

    ctx = kala_context_mod.kala_context(birth, chart, ayanamsa=ayanamsa_deg)
    mns = mean_longitudes_mod.mean_longitudes(chart.jd_ut, birth.year)
    means = mns["mean"]
    seegs = mns["seeg"]

    sun_lon = chart.planets["Sun"].lon if "Sun" in chart.planets else None
    moon_lon = chart.planets["Moon"].lon if "Moon" in chart.planets else None

    out: dict[str, tuple[ShadbalaBreakdown, float, float]] = {}
    for p in _SEVEN:
        if p not in chart.planets:
            continue

        # ── 6 graha-bala components (Shashtiamsas) ───────────────────────────
        sthana_sh = sthana.sthana_bala(p, chart)
        dig_sh = dig.dig_bala(p, chart)
        kala_sh = kala.kala_bala(p, chart, ctx)
        cheshta_sh = cheshta.cheshta_bala_for_chart(p, chart, means, seegs)
        naisargika_sh = naisargika.naisargika_bala(p)
        drik_sh = drik.drik_bala(p, chart)
        br = total.assemble_shadbala(
            sthana_sh, dig_sh, kala_sh, cheshta_sh, naisargika_sh, drik_sh
        )

        # ── Ishta / Kashta phala (GBB-10) ────────────────────────────────────
        # Ochcha is the Sthana sub-component; Cheshta is the true arc for the 5
        # star-planets, and a fold-based surrogate for the two luminaries.
        ochcha_sh = sthana.ochcha_bala(p, chart)
        if p in _CHESHTA_PLANETS:
            chesta_for_ik = cheshta_sh
        elif p == "Sun":
            # Sun has no true Cheshta; surrogate uses the SAYANA Sun longitude.
            chesta_for_ik = ishta_kashta.sun_chesta_surrogate(
                (sun_lon + ayanamsa_deg) if sun_lon is not None else ayanamsa_deg
            )
        else:  # Moon
            chesta_for_ik = (
                ishta_kashta.moon_chesta_surrogate(moon_lon, sun_lon)
                if (moon_lon is not None and sun_lon is not None)
                else 0.0
            )

        ishta = ishta_kashta.ishta_phala(ochcha_sh, chesta_for_ik)
        kashta = ishta_kashta.kashta_phala(ochcha_sh, chesta_for_ik)

        out[p] = (br, ishta, kashta)

    return out
