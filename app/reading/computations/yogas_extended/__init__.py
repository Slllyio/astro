"""Practitioner extended yoga detectors — unified entry point.

Doctrine source: BPHS Ch.39-40 (Adhi, Lakshmi, Neech Bhanga, Vipareeta)
+ Phaladeepika (Saraswati, Daridra, Chamara, Parivartana) + D-11 / D-12
lockfile (Neech Bhanga primary rule, Kala Sarpa strict definition).

This sub-package decomposes the extended-yoga detectors into one module
per yoga, each emitting Findings with a stable id pattern
``practitioner.yogas_extended.<name>.<variant>``.

Sub-modules
===========

Phase 3e1 (fortune yogas):

- :mod:`adhi`       — BPHS Ch.40 Adhi Yoga (Maha/Madhya/Alpa variants)
- :mod:`lakshmi`    — BPHS Ch.40 Lakshmi Yoga
- :mod:`saraswati`  — Phaladeepika Saraswati Yoga
- :mod:`daridra`    — Phaladeepika Daridra Yoga (poverty indicator)
- :mod:`chamara`    — Phaladeepika Chamara Yoga (regal yoga)

Phase 3e2 (doctrinally-tricky yogas):

- :mod:`vipareeta`    — positional Vipareeta variants (Harsha/Sarala/Vimala)
- :mod:`parivartana`  — mutual sign-exchange (Maha/Khala/Dainya)
- :mod:`kala_sarpa`   — strict 180° Rahu-leading per D-12 (KSY / Amrita)
- :mod:`neech_bhanga` — BPHS Ch.39 v.10 primary cancellation per D-11

Public entry point
==================

    detect_yogas(d1_chart, asc_sign, moon_sign) -> list[Finding]

Runs every detector in a fixed order and returns the flattened list of
Findings. Domains/* consume this for their yoga sections.
"""
from __future__ import annotations

from typing import Mapping

from app.reading.schema import Finding

from .adhi import detect_adhi
from .chamara import detect_chamara
from .daridra import detect_daridra
from .kala_sarpa import detect_kala_sarpa
from .lakshmi import detect_lakshmi
from .neech_bhanga import detect_neech_bhanga
from .parivartana import detect_parivartana
from .saraswati import detect_saraswati
from .vipareeta import detect_vipareeta


def detect_yogas(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    moon_sign: int,
) -> list[Finding]:
    """Master entry — run all 9 yoga detectors and return a flat list.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, "longitude": float, ...}}.
        asc_sign: 1..12 ascendant sign.
        moon_sign: 1..12 natal Moon sign (used by Neech Bhanga and any
            future Moon-anchored detector).

    Returns:
        A flat ``list[Finding]`` aggregating outputs of every detector
        in this sub-package. Order is fixed for stable iteration:
        adhi → lakshmi → saraswati → daridra → chamara →
        vipareeta → parivartana → kala_sarpa → neech_bhanga.

    Raises:
        ValueError: propagated from any underlying detector when
            ``asc_sign`` or ``moon_sign`` is outside 1..12.
    """
    results: list[Finding] = []
    results.extend(detect_adhi(d1_chart, asc_sign))
    results.extend(detect_lakshmi(d1_chart, asc_sign))
    results.extend(detect_saraswati(d1_chart, asc_sign))
    results.extend(detect_daridra(d1_chart, asc_sign))
    results.extend(detect_chamara(d1_chart, asc_sign))
    results.extend(detect_vipareeta(d1_chart, asc_sign))
    results.extend(detect_parivartana(d1_chart, asc_sign))
    results.extend(detect_kala_sarpa(d1_chart, asc_sign))
    results.extend(detect_neech_bhanga(d1_chart, asc_sign, moon_sign))
    return results


__all__ = [
    "detect_yogas",
    "detect_adhi",
    "detect_lakshmi",
    "detect_saraswati",
    "detect_daridra",
    "detect_chamara",
    "detect_vipareeta",
    "detect_parivartana",
    "detect_kala_sarpa",
    "detect_neech_bhanga",
]
