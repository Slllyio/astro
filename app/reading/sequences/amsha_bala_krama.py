"""Doctrine source: notebook NotebookLM proforma — "The Architecture of Fate:
Shodasha Varga System" (BPHS Vol.I Ch.6-7, Shodashavarga doctrine).

Sequence 1 — BPHS layered Varga judgment (the *Amsha Bala Krama*, the
"order of strengths across vargas").

The methodology walks four steps in order:

1. **analyze_d1** — read the natal D1 chart for the primary promise and
   physical manifestation. The D1 sets the gross frame: lagna lord
   placement, functional benefic/malefic mix, the natural yogas
   already formed.

2. **consult_d9** — refer to D9 Navamsha for inner strength, dharma,
   and the ultimate "fruit" (phaladayaka). A planet weak in D1 can
   become dramatically strong in D9 (vargottama), and vice versa.

3. **specific_varga_refinement** — drop into the domain-specific Varga
   the user wants judged (D10 for career, D7 for children, D2 for
   wealth, D24 for education, D60 for past-life karma). This sequence
   defaults to D10 because career is the most common consultation.

4. **dasha_transit_activation** — identify which Mahadasha + Antardasha
   lord is firing now, so the static promise from steps 1-3 is anchored
   to a *when*.

Architectural discipline (per Phase 4 brief)
--------------------------------------------

This module ORCHESTRATES — it does NOT recompute. Every step delegates
to an existing Tier-0/1/2 computation:

  * Step 1 (analyze_d1)       -> ``computations.functional_nature``,
                                  ``core.yogas.detect_yogas``,
                                  ``computations.karakas``
  * Step 2 (consult_d9)       -> ``computations.divisional_readings.d9_navamsha``
  * Step 3 (specific_varga_refinement)
                              -> ``computations.divisional_readings.d{2,7,9,10,24,60}_*``
  * Step 4 (dasha_transit_activation)
                              -> chart["current_mahadasha"] + caller-supplied
                                 AD lord (the dasha engine output already in
                                 the chart envelope)

Public API
==========

    run_sequence(chart, asc_sign, moon_sign, current_md_lord,
                 current_ad_lord, target_varga="d10")
        -> AmshaBalaKramaResult

The result satisfies the schema validator: ``steps`` keys must be exactly
:data:`AMSHA_BALA_KRAMA_KEYS`. Finding ids follow the ``seq_1.<step>...``
grammar so cross-references stay stable.
"""
from __future__ import annotations

import logging
from typing import Any, Final, Literal, Mapping

from app.core.dignity import SIGN_RULERS
from app.core.yogas import detect_yogas
from app.reading.computations.divisional_readings.d2_hora import read_d2_hora
from app.reading.computations.divisional_readings.d7_saptamsa import (
    read_d7_saptamsa,
)
from app.reading.computations.divisional_readings.d9_navamsha import (
    read_d9_navamsha,
)
from app.reading.computations.divisional_readings.d10_dashamsha import (
    read_d10_dashamsha,
)
from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
    read_d24_chaturvimsamsa,
)
from app.reading.computations.divisional_readings.d60_shashtiamsa import (
    read_d60_shashtiamsa,
)
from app.reading.computations.functional_nature import (
    compute_functional_nature,
)
from app.reading.computations.karakas import compute_karakas
from app.reading.schema import (
    AMSHA_BALA_KRAMA_KEYS,
    AmshaBalaKramaResult,
    ConfidenceScore,
    Finding,
)

logger = logging.getLogger(__name__)


_SEQUENCE_NAME: Final[str] = "amsha_bala_krama"


# Sequence-level confidence envelope — each step is a structural
# orchestration, not a 3-pillar judgment. Bands stay at indicative_only
# because downstream domain layers re-score with full evidence weighting.
_SEQUENCE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Ch.6-7 (Shodashavarga) — Amsha Bala Krama"
)


# Allowed target vargas per the brief; each maps to its divisor-key in
# the chart["divisional_charts"] dict and the reader to delegate to.
_TARGET_VARGAS: Final[frozenset[str]] = frozenset(
    {"d2", "d7", "d9", "d10", "d24", "d60"}
)


def _validate_asc_sign(value: int) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(
            f"asc_sign must be a 1-indexed sign in 1..12, got {value!r}"
        )
    return value


def _validate_target_varga(value: str) -> str:
    if value not in _TARGET_VARGAS:
        raise ValueError(
            f"target_varga must be one of {sorted(_TARGET_VARGAS)}, "
            f"got {value!r}"
        )
    return value


def _planet_sign(
    chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


# ---------------------------------------------------------------------------
# Step 1 — analyze_d1
# ---------------------------------------------------------------------------


def _check_analyze_d1(
    chart: Mapping[str, Any], asc_sign: int,
) -> Finding:
    """Step 1: Primary promise and physical manifestation from D1.

    Delegates to:
      * ``app.reading.computations.functional_nature.compute_functional_nature``
        for the lagna lord's functional nature (the gross dharmic
        orientation of the chart).
      * ``app.core.yogas.detect_yogas`` for natural yogas already formed
        in D1.
      * ``app.reading.computations.karakas.compute_karakas`` for the
        Atmakaraka identification (soul-significator anchor).
    """
    d1_chart = chart["d1"]
    ascendant = chart.get("ascendant") or {"sign": asc_sign}

    natures = compute_functional_nature(asc_sign)
    lagna_lord = SIGN_RULERS[asc_sign]
    lagna_lord_nature_finding = natures.get(lagna_lord)
    lagna_lord_nature = "unknown"
    if lagna_lord_nature_finding is not None:
        for line in lagna_lord_nature_finding.evidence:
            if line.startswith("nature="):
                lagna_lord_nature = line.split("=", 1)[1]
                break

    yogas = detect_yogas(d1_chart, ascendant) if ascendant.get("sign") else []
    yoga_names = [y["name"] for y in yogas]

    karakas = compute_karakas(d1_chart)
    ak_planet = "unknown"
    ak_finding = karakas.get("atmakaraka")
    if ak_finding is not None:
        for line in ak_finding.evidence:
            if line.startswith("planet="):
                ak_planet = line.split("=", 1)[1]
                break

    yoga_phrase = f"{len(yoga_names)} yogas" if yoga_names else "no major yogas"
    verdict = (
        f"D1 promise: lagna lord {lagna_lord}={lagna_lord_nature}; "
        f"AK={ak_planet}; {yoga_phrase}"
    )[:140]

    return Finding(
        id="seq_1.step_1.analyze_d1",
        rule="amsha_bala_krama.analyze_d1",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction="neutral",
        verdict=verdict,
        evidence=[
            "varga=D1 (Rashi — primary promise)",
            f"asc_sign={asc_sign}",
            f"lagna_lord={lagna_lord}",
            f"lagna_lord_functional_nature={lagna_lord_nature}",
            f"atmakaraka={ak_planet}",
            f"natural_yogas={yoga_names}",
            "delegate=functional_nature + yogas + karakas (Tier-0/1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 2 — consult_d9
# ---------------------------------------------------------------------------


def _check_consult_d9(
    chart: Mapping[str, Any], asc_sign: int,
) -> Finding:
    """Step 2: D9 Navamsha — inner strength, dharma, ultimate fruit.

    Delegates to ``divisional_readings.d9_navamsha.read_d9_navamsha``.
    Summarises the count of vargottama planets (each is a strong stable
    significator) and the D9 lagna-lord placement.
    """
    d1_chart = chart["d1"]
    d9_chart = chart["d9"]

    d9_findings = read_d9_navamsha(d1_chart, d9_chart, asc_sign)

    # Count vargottama planets from the d9.planet_in_* findings.
    vargottama_planets: list[str] = []
    for fid, f in d9_findings.items():
        if not fid.startswith("d9.planet_in_"):
            continue
        for line in f.evidence:
            if line == "is_vargottama=yes":
                # Recover planet name from id suffix.
                vargottama_planets.append(
                    fid.replace("d9.planet_in_", "").capitalize()
                )
                break

    d9_lagna_lord_state = "n/a"
    ll_finding = d9_findings.get("d9.lagna_lord")
    if ll_finding is not None:
        d9_lagna_lord_state = ll_finding.verdict

    verdict = (
        f"D9 dharma: {len(vargottama_planets)} vargottama "
        f"({', '.join(vargottama_planets) or 'none'})"
    )[:140]

    return Finding(
        id="seq_1.step_2.consult_d9",
        rule="amsha_bala_krama.consult_d9",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"vargottama_count={len(vargottama_planets)}",
            f"vargottama_planets={vargottama_planets}",
            f"d9_lagna_lord_summary={d9_lagna_lord_state}",
            f"d9_findings_total={len(d9_findings)}",
            "delegate=divisional_readings.d9_navamsha (Tier-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 3 — specific_varga_refinement
# ---------------------------------------------------------------------------


def _check_specific_varga_refinement(
    chart: Mapping[str, Any], asc_sign: int, target_varga: str,
) -> Finding:
    """Step 3: Drop into the domain-specific Varga (default D10).

    Delegates to the matching divisional reader. D10/D60 need an
    Amatya/Atma karaka argument — we re-use the karakas primitive to
    derive it on demand.
    """
    d1_chart = chart["d1"]
    div_charts = chart.get("divisional_charts", {})

    varga = target_varga.lower()
    varga_sign_count = 0
    varga_label = varga.upper()
    summary = "no_findings"

    if varga == "d10":
        # D10 needs Amatya Karaka from karakas primitive.
        karakas = compute_karakas(d1_chart)
        amk = "Sun"
        amk_f = karakas.get("amatyakaraka")
        if amk_f is not None:
            for line in amk_f.evidence:
                if line.startswith("planet="):
                    amk = line.split("=", 1)[1]
                    break
        d10_chart = chart["d10"]
        findings = read_d10_dashamsha(d1_chart, d10_chart, asc_sign, amk)
        varga_sign_count = len(findings)
        summary_finding = findings.get("d10.career_5_pillars")
        if summary_finding is not None:
            summary = summary_finding.verdict
    elif varga == "d9":
        d9_chart = chart["d9"]
        findings = read_d9_navamsha(d1_chart, d9_chart, asc_sign)
        varga_sign_count = len(findings)
        summary = findings.get("d9.lagna", findings[next(iter(findings))]).verdict
    elif varga == "d2":
        d2_chart = div_charts.get("D2_Hora") or {}
        findings = read_d2_hora(d2_chart, asc_sign)
        varga_sign_count = len(findings)
        summary = f"D2 Hora reading emitted {varga_sign_count} findings"
    elif varga == "d7":
        d7_chart = div_charts.get("D7_Saptamsa") or {}
        findings = read_d7_saptamsa(d7_chart, asc_sign)
        varga_sign_count = len(findings)
        summary = findings.get("d7.lagna", findings[next(iter(findings))]).verdict
    elif varga == "d24":
        d24_chart = div_charts.get("D24_Chaturvimsamsa") or {}
        findings = read_d24_chaturvimsamsa(d24_chart, asc_sign)
        varga_sign_count = len(findings)
        summary = findings.get("d24.lagna", findings[next(iter(findings))]).verdict
    elif varga == "d60":
        karakas = compute_karakas(d1_chart)
        ak = "Sun"
        ak_f = karakas.get("atmakaraka")
        if ak_f is not None:
            for line in ak_f.evidence:
                if line.startswith("planet="):
                    ak = line.split("=", 1)[1]
                    break
        d60_chart = div_charts.get("D60_Shastiamsa") or {}
        findings = read_d60_shashtiamsa(d60_chart, asc_sign, ak)
        varga_sign_count = len(findings)
        summary = findings.get("d60.lagna", findings[next(iter(findings))]).verdict
    else:
        # Defensive: validator should have rejected earlier.
        raise ValueError(f"unsupported target_varga={target_varga!r}")

    verdict = (
        f"{varga_label} domain refinement: {varga_sign_count} findings; "
        f"summary={summary}"
    )[:140]

    return Finding(
        id=f"seq_1.step_3.specific_varga_refinement.{varga}",
        rule="amsha_bala_krama.specific_varga_refinement",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"target_varga={varga_label}",
            f"findings_count={varga_sign_count}",
            f"summary={summary}",
            f"delegate=divisional_readings.{varga} (Tier-1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Step 4 — dasha_transit_activation
# ---------------------------------------------------------------------------


def _check_dasha_transit_activation(
    chart: Mapping[str, Any],
    asc_sign: int,
    md_lord: str,
    ad_lord: str,
) -> Finding:
    """Step 4: Identify which dasha lords are firing the promise NOW.

    Uses the already-computed Vimshottari output in
    ``chart["current_mahadasha"]`` (set by
    ``app.core.ephemeris_engine.calculate_all_charts``); the caller
    provides the current AD lord. The functional nature of each is
    surfaced so domain layers can route accordingly.
    """
    md_block = chart.get("current_mahadasha") or {}
    md_window = "n/a"
    if md_block:
        md_window = f"{md_block.get('start_date')} -> {md_block.get('end_date')}"

    natures = compute_functional_nature(asc_sign)

    def _nature_of(planet: str) -> str:
        f = natures.get(planet)
        if f is None:
            return "unknown"
        for line in f.evidence:
            if line.startswith("nature="):
                return line.split("=", 1)[1]
        return "unknown"

    md_nature = _nature_of(md_lord)
    ad_nature = _nature_of(ad_lord)

    verdict = (
        f"Now firing: MD {md_lord}={md_nature}, AD {ad_lord}={ad_nature}"
    )[:140]

    return Finding(
        id="seq_1.step_4.dasha_transit_activation",
        rule="amsha_bala_krama.dasha_transit_activation",
        source_sequence=_SEQUENCE_NAME,
        classification="trigger",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"md_lord={md_lord}",
            f"md_functional_nature={md_nature}",
            f"ad_lord={ad_lord}",
            f"ad_functional_nature={ad_nature}",
            f"md_window={md_window}",
            "delegate=current_mahadasha + functional_nature (Tier-0/1)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Overall verdict — synthesis of the 4 steps
# ---------------------------------------------------------------------------


def _overall_verdict(
    steps: dict[str, Finding], target_varga: str, md_lord: str, ad_lord: str,
) -> Finding:
    # Pick up condensed signals from each step.
    yoga_count = 0
    vargottama_count = 0
    d1_step = steps["analyze_d1"]
    for line in d1_step.evidence:
        if line.startswith("natural_yogas="):
            # Repr-list-shaped; count by separators.
            yoga_count = line.count("'") // 2
    d9_step = steps["consult_d9"]
    for line in d9_step.evidence:
        if line.startswith("vargottama_count="):
            try:
                vargottama_count = int(line.split("=", 1)[1])
            except ValueError:
                vargottama_count = 0
            break

    verdict = (
        f"Amsha Bala Krama: D1 yogas={yoga_count}; D9 vargottama="
        f"{vargottama_count}; {target_varga.upper()} domain; now MD={md_lord}/AD={ad_lord}"
    )[:140]

    return Finding(
        id="seq_1.overall",
        rule="amsha_bala_krama.overall",
        source_sequence=_SEQUENCE_NAME,
        classification="promise",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"target_varga={target_varga.upper()}",
            f"yoga_count_from_d1={yoga_count}",
            f"vargottama_count_from_d9={vargottama_count}",
            f"current_md_lord={md_lord}",
            f"current_ad_lord={ad_lord}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_SEQUENCE_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_sequence(
    chart: dict,
    asc_sign: int,
    moon_sign: int,
    current_md_lord: str,
    current_ad_lord: str,
    target_varga: Literal["d2", "d7", "d9", "d10", "d24", "d60"] = "d10",
) -> AmshaBalaKramaResult:
    """Run the 4-step BPHS Amsha-Bala-Krama orchestration.

    Args:
        chart: Full natal chart dict from
            ``app.core.ephemeris_engine.calculate_all_charts`` —
            must carry ``d1``, ``d9``, ``d10``, ``divisional_charts``,
            ``ascendant``, ``current_mahadasha``.
        asc_sign: 1-indexed natal ascendant rashi (1..12).
        moon_sign: 1-indexed natal Moon rashi (1..12). Reserved for
            future extension; current implementation does not depend on
            it directly because the D9 / D10 readers anchor on D1 lagna.
        current_md_lord: Planet name of the currently-active Mahadasha
            lord (e.g. ``"Mercury"``).
        current_ad_lord: Planet name of the currently-active Antardasha
            lord.
        target_varga: Which domain-specific Varga to refine in step 3.
            One of ``"d2"`` (wealth), ``"d7"`` (children), ``"d9"``
            (dharma — redundant with step 2 but offered for symmetry),
            ``"d10"`` (career — default), ``"d24"`` (education), or
            ``"d60"`` (past-life karma).

    Returns:
        :class:`AmshaBalaKramaResult` — schema-validated; ``steps`` keys
        are exactly :data:`AMSHA_BALA_KRAMA_KEYS`.

    Raises:
        ValueError: If ``asc_sign`` is out of range, ``target_varga`` is
            not in the allowed set, or any required chart key is missing.
    """
    _validate_asc_sign(asc_sign)
    if not isinstance(moon_sign, int) or not (1 <= moon_sign <= 12):
        raise ValueError(
            f"moon_sign must be a 1-indexed sign in 1..12, got {moon_sign!r}"
        )
    _validate_target_varga(target_varga)
    if not isinstance(current_md_lord, str) or not current_md_lord:
        raise ValueError("current_md_lord must be a non-empty planet name")
    if not isinstance(current_ad_lord, str) or not current_ad_lord:
        raise ValueError("current_ad_lord must be a non-empty planet name")

    step_d1 = _check_analyze_d1(chart, asc_sign)
    step_d9 = _check_consult_d9(chart, asc_sign)
    step_varga = _check_specific_varga_refinement(chart, asc_sign, target_varga)
    step_dasha = _check_dasha_transit_activation(
        chart, asc_sign, current_md_lord, current_ad_lord,
    )

    steps: dict[str, Finding] = {
        "analyze_d1": step_d1,
        "consult_d9": step_d9,
        "specific_varga_refinement": step_varga,
        "dasha_transit_activation": step_dasha,
    }
    # Defensive: assert the dict matches the schema's enum exactly so a
    # silent reorder above does not break validator detection later.
    assert set(steps.keys()) == set(AMSHA_BALA_KRAMA_KEYS), (
        "AMSHA_BALA_KRAMA_KEYS / steps mismatch"
    )

    overall = _overall_verdict(steps, target_varga, current_md_lord, current_ad_lord)

    return AmshaBalaKramaResult(steps=steps, overall_verdict=overall)


__all__ = ["run_sequence"]
