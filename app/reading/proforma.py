"""Main orchestrator for `app.reading`.

Two-function pattern per spec Section 5 (Data flow / Public-vs-private
orchestration):

- `_run_core_pipeline` — private, deterministic, Stages 1-7. No RAG. No
  recursion. Birth-time-robustness MUST import this directly (rather than
  `compute`) to avoid recursion through Tier-3 modules that re-invoke the
  engine on time perturbations.
- `compute` — public; runs the core pipeline and, when `enrich=True`,
  layers Tier-3 enrichments (citations, consensus, dispute, robustness,
  contradiction detection) via `_apply_tier3_enrichments`.

Phase 7 wiring discipline:

- Each downstream module call is wrapped in try/except. Failures are
  collected into the top-level ``warnings`` block and never propagated as
  exceptions — the engine must not crash a user. This is the
  graceful-degradation contract.
- Tier-3 lazy-import discipline: ``rag_citations``, ``consensus_scoring``,
  ``dispute_surfacing``, ``yoga_calibration``, ``contradiction_detector``,
  and ``birth_time_robustness`` are imported INSIDE
  ``_apply_tier3_enrichments`` so the ``--no-enrich`` path never loads
  ``sentence_transformers`` / ``torch``.
- ``birth_time_robustness`` re-enters the engine through
  ``_run_core_pipeline`` (the private entry-point), NOT ``compute``, to
  avoid unbounded Tier-3 recursion.
"""
from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from typing import Any, Callable

from app.reading.schema import (
    ChartBlock,
    ChartInput,
    ClassicalYoga,
    Contradiction,
    DoctrineConfig,
    DomainsBlock,
    Finding,
    FoundationsBlock,
    Meta,
    PractitionerBlock,
    PrimitivesBlock,
    ReadingOutput,
    SequencesBlock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine version sourcing
# ---------------------------------------------------------------------------

_ENGINE_VERSION_FALLBACK = "0.0.0+phase7"


def _engine_version() -> str:
    """Best-effort engine version string."""
    return _ENGINE_VERSION_FALLBACK


def _swiss_ephemeris_version() -> str:
    """Swiss Ephemeris library version, or ``"unknown"`` if unavailable."""
    try:
        import swisseph as swe

        return str(swe.version)
    except Exception:  # pragma: no cover - swisseph is a hard dep in this repo
        logger.warning("swisseph version unavailable; defaulting to 'unknown'")
        return "unknown"


def _python_version() -> str:
    """Tuple-style Python version string, e.g. ``"3.12.10"``."""
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"


def _generated_at_iso() -> str:
    """Current UTC instant as ISO-8601 (timezone-aware)."""
    return datetime.now(UTC).isoformat()


_GRAHAS_9: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def _classical_yogas(
    d1_chart: dict[str, Any], asc_sign: int, lagna_longitude: float,
) -> list[ClassicalYoga]:
    """Run the core 88-detector yoga library over the D1 chart and return the
    active yogas with their classical citations, for the reading's
    classical-yogas section. Fail-soft: any error yields ``[]`` so a missing
    or partial chart never blocks a reading."""
    try:
        from app.core.chart_model import Chart
        from app.core.yoga_library import active_yogas

        signs: dict[str, int] = {}
        lons: dict[str, float] = {}
        for g in _GRAHAS_9:
            entry = d1_chart.get(g) or {}
            if entry.get("sign") is not None and entry.get("longitude") is not None:
                signs[g] = int(entry["sign"])
                lons[g] = float(entry["longitude"])
        if len(signs) < len(_GRAHAS_9):
            return []
        houses = {g: ((signs[g] - asc_sign) % 12) + 1 for g in signs}
        chart = Chart(
            planet_signs=signs, planet_houses=houses, planet_lons=lons,
            asc_sign=asc_sign, asc_lon=lagna_longitude,
        )
        return [
            ClassicalYoga(
                name=y.name, sanskrit=y.sanskrit, reference=y.reference,
                description=y.description, intensity=round(float(y.intensity), 3),
            )
            for y in active_yogas(chart)
        ]
    except Exception:  # noqa: BLE001 — cosmetic section; never block a reading
        return []


def _dasha_activation(d1_chart: dict[str, Any], lagna_longitude: float) -> dict[str, Any]:
    """Per-graha bhāva activation following Raman's ENCODED HTJAH influence
    doctrine — faithfully mirrors ``_influence_factors`` / ``_pair_tier`` in
    ``app/medini/doctrine/domains/house_judgment.py`` (HTJAH Vol.I ch.IV,
    pp.44-48). A planet **activates house H** by any of Raman's six factors:

      (a) owns H · (b) occupies H · (c) aspects H (graha dṛṣṭi) ·
      (d) aspects H's lord · (e) conjoins H's lord · (f) is lord of H from the Moon.

    The period's fructification tier (computed client-side from the two lords'
    influence maps) is par-excellence/predominant when BOTH the MD and AD lords
    influence H, limited when one does, dormant when neither — the doctrine's
    fully / partial / none. (The engine's ``_influence_factors`` needs a heavy
    ``RamanChart``/``ChartBundle``; this reuses the identical rule on the
    reading's D1 primitives.) Fail-soft."""
    try:
        from app.core.dignity import SIGN_RULERS
        from app.core.drishti_argala import aspects_from_planet

        lagna_sign = int(lagna_longitude % 360.0 // 30) + 1
        ph: dict[str, int] = {}      # planet -> whole-sign house from Lagna
        moon_sign: int | None = None
        for g in _GRAHAS_9:
            s = (d1_chart.get(g) or {}).get("sign")
            if s is None:
                continue
            ph[g] = ((int(s) - lagna_sign) % 12) + 1
            if g == "Moon":
                moon_sign = int(s)
        if moon_sign is None or len(ph) < len(_GRAHAS_9):
            return {}

        def lord_of(house: int) -> str:                      # sign-lord of Hth bhava
            return SIGN_RULERS[((lagna_sign - 1 + house - 1) % 12) + 1]

        def lord_from_moon(house: int) -> str:               # factor (f)
            return SIGN_RULERS[((moon_sign + house - 2) % 12) + 1]

        def factors(planet: str, house: int) -> list[str]:
            lord = lord_of(house)
            asp = aspects_from_planet(planet, ph[planet])
            facs: list[str] = []
            if planet == lord:
                facs.append("owns")
            if ph[planet] == house:
                facs.append("occupies")
            if house in asp:
                facs.append("aspects house")
            if planet != lord:
                if ph[lord] in asp:
                    facs.append("aspects lord")
                if ph[planet] == ph[lord]:
                    facs.append("conjoins lord")
            if planet == lord_from_moon(house) and "owns" not in facs:
                facs.append("lord from Moon")
            return facs

        planets: dict[str, dict[str, Any]] = {}
        for g in ph:
            infl = {str(h): f for h in range(1, 13) if (f := factors(g, h))}
            planets[g] = {"occ": ph[g],
                          "aspects": list(aspects_from_planet(g, ph[g])),
                          "influences": infl}
        return {"lagna_sign": lagna_sign, "planets": planets}
    except Exception:  # noqa: BLE001
        return {}


def _divisional_lagnas(lagna_longitude: float) -> dict[str, int]:
    """Ascendant sign (1..12) in D1/D9/D10 — lets the view mark the lagna cell in
    the divisional chart grids. Fail-soft."""
    try:
        from app.core.shodashavarga import compute_divisional_longitude

        out = {"D1": int(lagna_longitude % 360 // 30) + 1}
        for name, div in (("D9", 9), ("D10", 10)):
            out[name] = int(compute_divisional_longitude(lagna_longitude, div) % 360.0 // 30) + 1
        return out
    except Exception:  # noqa: BLE001
        return {}


# ---------------------------------------------------------------------------
# Input parsing helpers
# ---------------------------------------------------------------------------


def _parse_chart_input(
    chart_input: ChartInput,
) -> tuple[int, int, int, int, int, float]:
    """Decompose a ChartInput into ephemeris-engine arguments.

    Returns ``(year, month, day, hour, minute, tz_offset_hours)``.
    """
    dt = datetime.fromisoformat(f"{chart_input.dob} {chart_input.time}:00")
    tz_sign = 1
    tz_str = chart_input.tz
    if tz_str.startswith("-"):
        tz_sign = -1
        tz_str = tz_str[1:]
    elif tz_str.startswith("+"):
        tz_str = tz_str[1:]
    tz_hh, tz_mm = tz_str.split(":")
    tz_offset = tz_sign * (int(tz_hh) + int(tz_mm) / 60.0)
    return dt.year, dt.month, dt.day, dt.hour, dt.minute, tz_offset


def _safe_call(
    warnings: list[str],
    module_label: str,
    fn: Callable[..., Any],
    *args: Any,
    default: Any = None,
    **kwargs: Any,
) -> Any:
    """Invoke ``fn(*args, **kwargs)`` catching every exception.

    On failure: append a warning string to ``warnings`` and return ``default``.
    The graceful-degradation contract: the engine MUST never crash a user.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        msg = f"{module_label} failed: {type(exc).__name__}: {exc}"
        logger.warning(msg)
        warnings.append(msg)
        return default


def _flatten_findings(value: Any) -> list[Finding]:
    """Normalise a Tier-0/1/2 module return into a flat ``list[Finding]``.

    Modules variously return ``list[Finding]``, ``dict[str, Finding]``,
    ``dict[int, Finding]``, or a single ``Finding``. We unify them here.
    """
    if value is None:
        return []
    if isinstance(value, Finding):
        return [value]
    if isinstance(value, list):
        return [f for f in value if isinstance(f, Finding)]
    if isinstance(value, dict):
        out: list[Finding] = []
        for v in value.values():
            if isinstance(v, Finding):
                out.append(v)
        return out
    return []


def _add_findings(
    block_findings: list[Finding],
    by_module: dict[str, list[Finding]],
    module_name: str,
    value: Any,
) -> None:
    """Record a module's findings into both the flat list and the by-module map."""
    flat = _flatten_findings(value)
    if not flat:
        return
    block_findings.extend(flat)
    by_module[module_name] = flat


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_core_pipeline(chart_input: ChartInput) -> dict[str, Any]:
    """Run Stages 1-7 of the kundli pipeline.

    Private. Deterministic. No RAG. No recursion. Birth-time-robustness
    calls this directly to evaluate flip-rates over time perturbations
    without triggering Tier-3 enrichment on each call.
    """
    logger.info(
        "Running core pipeline for dob=%s time=%s tz=%s lat=%s lon=%s",
        chart_input.dob,
        chart_input.time,
        chart_input.tz,
        chart_input.lat,
        chart_input.lon,
    )

    warnings: list[str] = []

    # -----------------------------------------------------------------------
    # Stage 1: Natal chart compute
    # -----------------------------------------------------------------------
    chart: dict[str, Any] = {}
    try:
        year, month, day, hour, minute, tz_offset = _parse_chart_input(chart_input)
        from app.core.ephemeris_engine import calculate_all_charts

        chart = calculate_all_charts(
            year, month, day, hour, minute, tz_offset,
            latitude=chart_input.lat, longitude=chart_input.lon,
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"stage1.ephemeris_engine.calculate_all_charts failed: {type(exc).__name__}: {exc}"
        logger.warning(msg)
        warnings.append(msg)

    d1_chart = chart.get("d1") or {}
    d9_chart = chart.get("d9") or {}
    d10_chart = chart.get("d10") or {}
    divisional_charts = chart.get("divisional_charts") or {}
    ascendant = chart.get("ascendant") or {}
    asc_sign = int(ascendant.get("sign", 1)) if ascendant else 1
    lagna_longitude = float(ascendant.get("longitude", 0.0)) if ascendant else 0.0
    birth_jd = float(chart.get("birth_jd", chart.get("jd", 0.0)))
    ayanamsa = chart.get("ayanamsa")

    moon_entry = d1_chart.get("Moon") or {}
    moon_sign = int(moon_entry.get("sign", 1)) if moon_entry else 1
    moon_lon = float(moon_entry.get("longitude", 0.0)) if moon_entry else 0.0
    sun_entry = d1_chart.get("Sun") or {}
    sun_lon = float(sun_entry.get("longitude", 0.0)) if sun_entry else 0.0

    weekday = int(birth_jd + 1.5) % 7 if birth_jd else 0

    # Determine is_daytime + sunrise_jd via sunrise/sunset; fail soft.
    is_daytime = True
    sunrise_jd = birth_jd
    try:
        import swisseph as swe
        geopos = (chart_input.lon, chart_input.lat, 0.0)
        status, tret = swe.rise_trans(
            birth_jd - 1.0, swe.SUN, swe.CALC_RISE, geopos, 0.0, 0.0, swe.FLG_SWIEPH,
        )
        if status >= 0 and tret:
            sunrise_jd = float(tret[0])
        status, tret = swe.rise_trans(
            sunrise_jd, swe.SUN, swe.CALC_SET, geopos, 0.0, 0.0, swe.FLG_SWIEPH,
        )
        if status >= 0 and tret:
            sunset_jd = float(tret[0])
            is_daytime = sunrise_jd <= birth_jd < sunset_jd
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"stage1.sunrise_sunset failed: {type(exc).__name__}: {exc}"
        )

    # Build the public ChartBlock payload.
    chart_block_payload: dict[str, Any] = {
        "lagna_longitude": lagna_longitude if ascendant else None,
        "ayanamsa": ayanamsa,
        "planets": d1_chart,
        "cusps": ascendant if ascendant else {},
        "extras": {
            "birth_jd": birth_jd,
            "is_daytime": is_daytime,
            "sunrise_jd": sunrise_jd,
            "weekday": weekday,
            "current_mahadasha": chart.get("current_mahadasha"),
            "divisional_charts": divisional_charts,
            "divisional_lagnas": _divisional_lagnas(lagna_longitude),
            "dasha_activation": _dasha_activation(d1_chart, lagna_longitude),
            "panchanga": chart.get("panchanga"),
            "ashtakavarga": chart.get("ashtakavarga"),
            "avasthas": chart.get("avasthas"),
        },
    }

    # -----------------------------------------------------------------------
    # Stage 2: Tier-0 primitives
    # -----------------------------------------------------------------------
    prim_findings: list[Finding] = []
    prim_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            arudha_upapada,
            avasthas as avasthas_mod,
            gandanta,
            gulika as gulika_mod,
            ishta_phal,
            karakamsha,
            karakas,
            panchanga_reader,
            planet_retrograde,
            residential_strength,
            vimsopaka,
        )

        _add_findings(
            prim_findings, prim_by_module, "planet_retrograde",
            _safe_call(warnings, "planet_retrograde",
                       planet_retrograde.detect_retrograde, d1_chart),
        )
        _add_findings(
            prim_findings, prim_by_module, "gandanta",
            _safe_call(warnings, "gandanta",
                       gandanta.detect_gandanta, d1_chart),
        )
        if birth_jd:
            _add_findings(
                prim_findings, prim_by_module, "panchanga_reader",
                _safe_call(warnings, "panchanga_reader",
                           panchanga_reader.read_panchanga,
                           birth_jd, moon_lon, sun_lon, weekday),
            )
        karaka_findings = _safe_call(
            warnings, "karakas", karakas.compute_karakas, d1_chart,
        )
        _add_findings(prim_findings, prim_by_module, "karakas", karaka_findings)
        lagna_deg_in_sign = lagna_longitude % 30.0
        _add_findings(
            prim_findings, prim_by_module, "residential_strength",
            _safe_call(warnings, "residential_strength",
                       residential_strength.compute_residential_strength,
                       d1_chart, lagna_deg_in_sign),
        )
        if birth_jd:
            _add_findings(
                prim_findings, prim_by_module, "gulika",
                _safe_call(warnings, "gulika",
                           gulika_mod.compute_gulika_and_mandi,
                           birth_jd, chart_input.lat, chart_input.lon,
                           is_daytime, weekday),
            )
        _add_findings(
            prim_findings, prim_by_module, "avasthas",
            _safe_call(warnings, "avasthas",
                       avasthas_mod.compute_deeptadi_avasthas, d1_chart),
        )

        arudha_padas: dict[str, Finding] = _safe_call(
            warnings, "arudha_upapada",
            arudha_upapada.compute_arudha_padas, d1_chart, asc_sign,
            default={},
        ) or {}
        _add_findings(
            prim_findings, prim_by_module, "arudha_upapada", arudha_padas,
        )

        if d9_chart:
            _add_findings(
                prim_findings, prim_by_module, "karakamsha",
                _safe_call(warnings, "karakamsha",
                           karakamsha.compute_karakamsha, d1_chart, d9_chart),
            )
        if divisional_charts:
            # vimsopaka expects ``{divisor:int -> per-varga chart dict}``,
            # but `compute_divisional_charts` keys by name (e.g. "D9_Navamsa").
            # Translate via SHODASHAVARGA_NAMES.
            divisor_keyed: dict[int, dict[str, Any]] = {1: d1_chart}
            try:
                from app.core.shodashavarga import SHODASHAVARGA_NAMES
                for divisor, name in SHODASHAVARGA_NAMES.items():
                    if name in divisional_charts:
                        divisor_keyed[divisor] = divisional_charts[name]
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"vimsopaka_inputs failed: {type(exc).__name__}: {exc}"
                )
            _add_findings(
                prim_findings, prim_by_module, "vimsopaka",
                _safe_call(warnings, "vimsopaka",
                           vimsopaka.compute_vimsopaka,
                           d1_chart, divisor_keyed),
            )

        # Build shadbala components (cheshta + uchcha) for ishta_phal.
        shadbala_components: dict[str, dict[str, float]] = {}
        try:
            from app.core.shadbala import cheshta_bala, uchcha_bala
            for p, entry in d1_chart.items():
                if p == "Ketu":
                    continue
                lon = float(entry.get("longitude", 0.0))
                is_retro = bool(entry.get("is_retrograde", False))
                shadbala_components[p] = {
                    "cheshta": cheshta_bala(p, is_retro),
                    "uchcha": uchcha_bala(p, lon),
                }
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"shadbala_components_build failed: {type(exc).__name__}: {exc}"
            )

        if shadbala_components:
            _add_findings(
                prim_findings, prim_by_module, "ishta_phal",
                _safe_call(warnings, "ishta_phal",
                           ishta_phal.compute_ishta_phal,
                           d1_chart, shadbala_components),
            )
    else:
        arudha_padas = {}

    # -----------------------------------------------------------------------
    # Stage 3: Tier-1 foundations
    # -----------------------------------------------------------------------
    found_findings: list[Finding] = []
    found_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            argala,
            ashtakavarga_reader,
            bhava_bala,
            bhava_chalit,
            functional_nature,
            jaimini_drishti,
            karaka_triangulation,
            shadbala_phase1,
        )

        _add_findings(
            found_findings, found_by_module, "functional_nature",
            _safe_call(warnings, "functional_nature",
                       functional_nature.compute_functional_nature, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "bhava_chalit",
            _safe_call(warnings, "bhava_chalit",
                       bhava_chalit.compute_bhava_chalit,
                       d1_chart, lagna_longitude, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "bhava_bala",
            _safe_call(warnings, "bhava_bala",
                       bhava_bala.compute_bhava_bala, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "shadbala_phase1",
            _safe_call(warnings, "shadbala_phase1",
                       shadbala_phase1.compute_shadbala_phase1,
                       d1_chart, asc_sign, is_daytime),
        )
        _add_findings(
            found_findings, found_by_module, "ashtakavarga_reader",
            _safe_call(warnings, "ashtakavarga_reader",
                       ashtakavarga_reader.read_ashtakavarga, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "jaimini_drishti",
            _safe_call(warnings, "jaimini_drishti",
                       jaimini_drishti.compute_jaimini_drishti,
                       d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "argala",
            _safe_call(warnings, "argala",
                       argala.compute_argala, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "karaka_triangulation",
            _safe_call(warnings, "karaka_triangulation",
                       karaka_triangulation.compute_karaka_triangulation,
                       d1_chart, asc_sign, moon_sign),
        )

    # -----------------------------------------------------------------------
    # Stage 4: Tier-2 practitioner
    # -----------------------------------------------------------------------
    prac_findings: list[Finding] = []
    prac_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            eclipse_natal_activation,
            graha_yuddha,
            marana_karaka_sthana,
            sade_sati_severity,
            special_lagnas,
            trika_doctrine,
        )

        _add_findings(
            prac_findings, prac_by_module, "marana_karaka_sthana",
            _safe_call(warnings, "marana_karaka_sthana",
                       marana_karaka_sthana.detect_mks, d1_chart, asc_sign),
        )
        _add_findings(
            prac_findings, prac_by_module, "trika_doctrine",
            _safe_call(warnings, "trika_doctrine",
                       trika_doctrine.detect_trika_exchanges, d1_chart, asc_sign),
        )
        _add_findings(
            prac_findings, prac_by_module, "graha_yuddha",
            _safe_call(warnings, "graha_yuddha",
                       graha_yuddha.detect_graha_yuddha, d1_chart),
        )
        if birth_jd and sunrise_jd:
            _add_findings(
                prac_findings, prac_by_module, "special_lagnas",
                _safe_call(warnings, "special_lagnas",
                           special_lagnas.compute_special_lagnas,
                           birth_jd, sunrise_jd, asc_sign),
            )
        # eclipse activation needs an `eclipses` sequence — skip when not available.
        eclipses = chart.get("eclipses") or []
        if eclipses:
            _add_findings(
                prac_findings, prac_by_module, "eclipse_natal_activation",
                _safe_call(warnings, "eclipse_natal_activation",
                           eclipse_natal_activation.detect_eclipse_activation,
                           d1_chart, asc_sign, eclipses),
            )

        # Sade Sati needs transit_saturn_sign — skip when not natal-only.
        transit_saturn_sign = chart.get("transit_saturn_sign")
        if transit_saturn_sign:
            _add_findings(
                prac_findings, prac_by_module, "sade_sati_severity",
                _safe_call(warnings, "sade_sati_severity",
                           sade_sati_severity.compute_sade_sati_severity,
                           d1_chart, asc_sign, int(transit_saturn_sign)),
            )

        # Yogas (unified entry).
        from app.reading.computations.yogas_extended import detect_yogas
        yoga_findings_list = _safe_call(
            warnings, "yogas_extended",
            detect_yogas, d1_chart, asc_sign, moon_sign,
            default=[],
        ) or []
        _add_findings(
            prac_findings, prac_by_module, "yogas_extended", yoga_findings_list,
        )

        # Divisional readings.
        from app.reading.computations.divisional_readings import (
            d2_hora, d3_drekkana, d7_saptamsa, d9_navamsha,
            d10_dashamsha, d12_dwadasamsa, d24_chaturvimsamsa, d60_shashtiamsa,
        )

        def _div(key: str) -> dict[str, Any]:
            return divisional_charts.get(key) or {}

        d2 = _div("D2_Hora")
        d3 = _div("D3_Drekkana")
        d7 = _div("D7_Saptamsa")
        d12 = _div("D12_Dwadasamsa")
        d24 = _div("D24_Chaturvimsamsa")
        d60 = _div("D60_Shastiamsa")

        if d2:
            _add_findings(
                prac_findings, prac_by_module, "d2_hora",
                _safe_call(warnings, "d2_hora",
                           d2_hora.read_d2_hora, d2, asc_sign),
            )
        if d3:
            _add_findings(
                prac_findings, prac_by_module, "d3_drekkana",
                _safe_call(warnings, "d3_drekkana",
                           d3_drekkana.read_d3_drekkana, d3, asc_sign),
            )
        if d7:
            _add_findings(
                prac_findings, prac_by_module, "d7_saptamsa",
                _safe_call(warnings, "d7_saptamsa",
                           d7_saptamsa.read_d7_saptamsa, d7, asc_sign),
            )
        if d9_chart:
            _add_findings(
                prac_findings, prac_by_module, "d9_navamsha",
                _safe_call(warnings, "d9_navamsha",
                           d9_navamsha.read_d9_navamsha,
                           d1_chart, d9_chart, asc_sign),
            )

        # D10 needs amatya_karaka — pull from karakas Findings.
        amatya = None
        for f in prim_by_module.get("karakas", []):
            if f.rule == "amatya_karaka" or "amatya" in f.id.lower():
                for ev in f.evidence:
                    if ev.startswith("planet="):
                        amatya = ev.split("=", 1)[1]
                        break
                if not amatya and f.verdict:
                    # parse first word of verdict as planet name fallback
                    words = f.verdict.split()
                    if words:
                        amatya = words[0]
                break
        if d10_chart and amatya:
            _add_findings(
                prac_findings, prac_by_module, "d10_dashamsha",
                _safe_call(warnings, "d10_dashamsha",
                           d10_dashamsha.read_d10_dashamsha,
                           d1_chart, d10_chart, asc_sign, amatya),
            )
        if d12:
            _add_findings(
                prac_findings, prac_by_module, "d12_dwadasamsa",
                _safe_call(warnings, "d12_dwadasamsa",
                           d12_dwadasamsa.read_d12_dwadasamsa, d12, asc_sign),
            )
        if d24:
            _add_findings(
                prac_findings, prac_by_module, "d24_chaturvimsamsa",
                _safe_call(warnings, "d24_chaturvimsamsa",
                           d24_chaturvimsamsa.read_d24_chaturvimsamsa,
                           d24, asc_sign),
            )
        # D60 needs atmakaraka.
        atmakaraka = None
        for f in prim_by_module.get("karakas", []):
            if f.rule == "atmakaraka" or "atma" in f.id.lower():
                for ev in f.evidence:
                    if ev.startswith("planet="):
                        atmakaraka = ev.split("=", 1)[1]
                        break
                if not atmakaraka and f.verdict:
                    words = f.verdict.split()
                    if words:
                        atmakaraka = words[0]
                break
        if d60 and atmakaraka:
            _add_findings(
                prac_findings, prac_by_module, "d60_shashtiamsa",
                _safe_call(warnings, "d60_shashtiamsa",
                           d60_shashtiamsa.read_d60_shashtiamsa,
                           d60, asc_sign, atmakaraka),
            )

    # -----------------------------------------------------------------------
    # Stage 5: Sequences
    # -----------------------------------------------------------------------
    seq_block_payload: dict[str, Any] = {
        "amsha_bala_krama": None,
        "career_executive": None,
        "md_judgments": [],
        "ad_judgments": [],
        "chara_dasha": None,   # V1.5 D-17 — populated below if d1 present
        "yogini_dasha": None,  # V1.5 D-18 — populated below if d1 present
    }

    current_md = chart.get("current_mahadasha") or {}
    current_md_lord = current_md.get("mahadasha_lord") or ""
    current_ad_lord = current_md_lord  # natal-only fallback

    if d1_chart and current_md_lord:
        from app.reading.sequences import (
            amsha_bala_krama, career_executive,
            vimshottari_ad, vimshottari_md,
        )

        md_result = _safe_call(
            warnings, "sequences.vimshottari_md",
            vimshottari_md.run_sequence, chart, asc_sign, moon_sign,
        )
        if md_result is not None:
            try:
                seq_block_payload["md_judgments"] = list(md_result.timeline)
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"sequences.vimshottari_md.timeline_unpack failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # Antardasha — need current MD start/end JDs.
        current_md_start_jd: float | None = None
        current_md_end_jd: float | None = None
        if md_result is not None:
            try:
                cmd = md_result.current_md_judgment
                current_md_start_jd = float(cmd.start_jd)
                current_md_end_jd = float(cmd.end_jd)
                # Also use the current MD lord from the MD result for consistency.
                current_md_lord = cmd.md_lord
            except Exception:  # noqa: BLE001
                pass
        if current_md_start_jd is not None and current_md_end_jd is not None:
            ad_result = _safe_call(
                warnings, "sequences.vimshottari_ad",
                vimshottari_ad.run_sequence,
                chart, asc_sign, moon_sign, current_md_lord,
                current_md_start_jd, current_md_end_jd,
            )
            if ad_result is not None:
                try:
                    seq_block_payload["ad_judgments"] = list(
                        ad_result.current_md_ads
                    ) + list(ad_result.next_md_first_3_ads)
                    # Pick the leading AD as current_ad_lord for downstream
                    # marriage_trigger (best-effort, falls back to MD lord).
                    if ad_result.current_md_ads:
                        current_ad_lord = ad_result.current_md_ads[0].ad_lord
                except Exception as exc:  # noqa: BLE001
                    warnings.append(
                        f"sequences.vimshottari_ad.unpack failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

        amsha_result = _safe_call(
            warnings, "sequences.amsha_bala_krama",
            amsha_bala_krama.run_sequence,
            chart, asc_sign, moon_sign,
            current_md_lord, current_ad_lord,
        )
        if amsha_result is not None:
            seq_block_payload["amsha_bala_krama"] = amsha_result

        career_result = _safe_call(
            warnings, "sequences.career_executive",
            career_executive.run_sequence,
            chart, asc_sign, moon_sign, current_md_lord,
            birth_jd, chart_input.lat, chart_input.lon, is_daytime, weekday,
        )
        if career_result is not None:
            seq_block_payload["career_executive"] = career_result

    # V1.5 — Chara Dasha (D-17 Jaimini sign-frame).
    # Wired into the deterministic pipeline (runs in --no-enrich too).
    # Pass-through model_dump so SequencesBlock can carry it as dict[str, Any]
    # (importing CharaDashaResult into schema.py would create a circular import).
    if d1_chart:
        try:
            from app.reading.sequences import chara_dasha
            chara_result = _safe_call(
                warnings, "sequences.chara_dasha",
                chara_dasha.run_sequence, chart, asc_sign, moon_sign,
            )
            if chara_result is not None:
                seq_block_payload["chara_dasha"] = chara_result.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"sequences.chara_dasha.import failed: {type(exc).__name__}: {exc}"
            )

    # V1.5 — Yogini Dasha (D-18 36-year specialty dasha).
    # Yogini takes moon_nakshatra (1..27), not moon_sign — derive from moon_lon.
    if d1_chart and moon_lon:
        try:
            from app.core.nakshatra import nakshatra_for_longitude
            from app.reading.sequences import yogini_dasha
            moon_nak_info = nakshatra_for_longitude(moon_lon)
            moon_nakshatra_1based = int(moon_nak_info["index"]) + 1
            yogini_result = _safe_call(
                warnings, "sequences.yogini_dasha",
                yogini_dasha.run_sequence,
                chart, asc_sign, moon_nakshatra_1based,
            )
            if yogini_result is not None:
                seq_block_payload["yogini_dasha"] = yogini_result.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"sequences.yogini_dasha.import failed: {type(exc).__name__}: {exc}"
            )

    # marriage_trigger — Tier-2, but needs current_ad_lord which we just got.
    if d1_chart and current_md_lord and arudha_padas:
        transit_jupiter_sign = chart.get("transit_jupiter_sign")
        transit_saturn_sign = chart.get("transit_saturn_sign")
        if transit_jupiter_sign and transit_saturn_sign and d9_chart:
            from app.reading.computations import marriage_trigger
            mt_finding = _safe_call(
                warnings, "marriage_trigger",
                marriage_trigger.compute_marriage_trigger,
                d1_chart, d9_chart, asc_sign, moon_sign,
                arudha_padas, current_md_lord, current_ad_lord,
                int(transit_jupiter_sign), int(transit_saturn_sign),
            )
            if isinstance(mt_finding, Finding):
                prac_findings.append(mt_finding)
                prac_by_module["marriage_trigger"] = [mt_finding]

    # -----------------------------------------------------------------------
    # Stage 6: Domain synthesis
    # -----------------------------------------------------------------------
    dom_block_payload: dict[str, Any] = {
        "career": None, "marriage": None, "children": None,
        "wealth": None, "health": None, "education": None,
    }

    if d1_chart:
        from app.reading.domains import (
            career as career_dom,
            children as children_dom,
            education as edu_dom,
            health as health_dom,
            marriage as marriage_dom,
            wealth as wealth_dom,
        )

        primitives_view = {
            "findings": list(prim_findings),
            "by_module": dict(prim_by_module),
        }
        foundations_view = {
            "findings": list(found_findings),
            "by_module": dict(found_by_module),
        }
        sequences_view: dict[str, Any] = {
            "amsha_bala_krama": seq_block_payload["amsha_bala_krama"],
            "career_executive": seq_block_payload["career_executive"],
            "md_judgments": seq_block_payload["md_judgments"],
            "ad_judgments": seq_block_payload["ad_judgments"],
        }

        for key, fn, label in (
            ("career", career_dom.synthesize_career, "domains.career"),
            ("marriage", marriage_dom.synthesize_marriage, "domains.marriage"),
            ("children", children_dom.synthesize_children, "domains.children"),
            ("wealth", wealth_dom.synthesize_wealth, "domains.wealth"),
            ("health", health_dom.synthesize_health, "domains.health"),
            ("education", edu_dom.synthesize_education, "domains.education"),
        ):
            result = _safe_call(
                warnings, label, fn,
                chart, asc_sign, moon_sign,
                sequences_view, primitives_view, foundations_view,
            )
            if result is not None:
                dom_block_payload[key] = result

    # -----------------------------------------------------------------------
    # rookie_guards — runs over the assembled reading to flag invariants.
    # -----------------------------------------------------------------------
    pre_reading: dict[str, Any] = {
        "primitives": {
            "findings": prim_findings, "by_module": prim_by_module,
        },
        "foundations": {
            "findings": found_findings, "by_module": found_by_module,
        },
        "practitioner": {
            "findings": prac_findings, "by_module": prac_by_module,
        },
        "sequences": seq_block_payload,
        "domains": dom_block_payload,
    }
    try:
        from app.reading.computations import rookie_guards
        rookie_findings = _safe_call(
            warnings, "rookie_guards",
            rookie_guards.check_rookie_invariants, pre_reading, default=[],
        ) or []
        if rookie_findings:
            prac_findings.extend(rookie_findings)
            prac_by_module["rookie_guards"] = rookie_findings
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"rookie_guards.import failed: {type(exc).__name__}: {exc}")

    # -----------------------------------------------------------------------
    # Classical yogas — the core 88-detector library, surfaced with citations.
    # (The practitioner `yogas_extended` module is a 9-detector graded subset;
    # this is the wider named-yoga catalog. Cosmetic, fail-soft.)
    # -----------------------------------------------------------------------
    classical_yogas_payload = _classical_yogas(d1_chart, asc_sign, lagna_longitude)

    # -----------------------------------------------------------------------
    # Stage 7: Assembly
    # -----------------------------------------------------------------------
    meta = Meta(
        engine_version=_engine_version(),
        swiss_ephemeris_version=_swiss_ephemeris_version(),
        python_version=_python_version(),
        generated_at=_generated_at_iso(),
        chart_input=chart_input,
        doctrines_used=[],
        doctrine_config=DoctrineConfig(),
        enrichment_enabled=False,
        robustness_enabled=False,
        stage_timings_ms={},
    )

    try:
        output = ReadingOutput(
            meta=meta,
            chart=ChartBlock(**chart_block_payload),
            primitives=PrimitivesBlock(
                findings=prim_findings, by_module=prim_by_module,
            ),
            foundations=FoundationsBlock(
                findings=found_findings, by_module=found_by_module,
            ),
            practitioner=PractitionerBlock(
                findings=prac_findings, by_module=prac_by_module,
            ),
            sequences=SequencesBlock(**seq_block_payload),
            domains=DomainsBlock(**dom_block_payload),
            contradictions=[],
            warnings=warnings,
            classical_yogas=classical_yogas_payload,
        )
    except Exception as exc:  # noqa: BLE001
        # Last-resort fallback: emit an empty-blocks reading with the
        # assembly error logged, so the CLI's schema check still passes.
        logger.warning(
            "ReadingOutput assembly failed; emitting empty fallback: %s", exc
        )
        warnings.append(
            f"stage7.assembly failed: {type(exc).__name__}: {exc}"
        )
        output = ReadingOutput(
            meta=meta,
            chart=ChartBlock(),
            primitives=PrimitivesBlock(),
            foundations=FoundationsBlock(),
            practitioner=PractitionerBlock(),
            sequences=SequencesBlock(),
            domains=DomainsBlock(),
            contradictions=[],
            warnings=warnings,
        )

    # -----------------------------------------------------------------------
    # V1.5 — modern-life enrichment.
    # Appends classification="primitive" Findings to each domain's
    # cross_checks list. Runs in --no-enrich path (deterministic, no LLM/RAG).
    # We pass the assembled ReadingOutput in object mode; the synthesizer
    # rebuilds the frozen DomainReading instances with augmented cross_checks
    # and returns a new ReadingOutput.
    # -----------------------------------------------------------------------
    if d1_chart:
        try:
            from app.reading.modern_life.synthesizer import enrich_with_modern_signals
            output = enrich_with_modern_signals(output, chart, asc_sign)
        except Exception as exc:  # noqa: BLE001
            msg = f"stage6.modern_life_enrichment failed: {type(exc).__name__}: {exc}"
            logger.warning(msg)
            # output.warnings is frozen — propagate by re-assembling Pydantic-ly
            warnings.append(msg)
            try:
                output = output.model_copy(update={"warnings": list(warnings)})
            except Exception:  # noqa: BLE001
                pass

    return output.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Tier-3 enrichment afterpass
# ---------------------------------------------------------------------------


def _findings_from_dicts(finding_dicts: list[dict[str, Any]]) -> list[Finding]:
    """Best-effort rebuild Finding objects from dicts. Skip on failure."""
    out: list[Finding] = []
    for d in finding_dicts:
        try:
            out.append(Finding.model_validate(d))
        except Exception:  # noqa: BLE001
            continue
    return out


def _apply_finding_enrichments_to_block(
    block: dict[str, Any], enriched_by_id: dict[str, Finding]
) -> None:
    """Replace dict-findings in ``block`` with enriched versions in-place.

    Walks ``findings`` list AND ``by_module`` map, swapping each by id.
    """
    if not isinstance(block, dict):
        return
    findings = block.get("findings")
    if isinstance(findings, list):
        for i, f in enumerate(findings):
            if isinstance(f, dict):
                enriched = enriched_by_id.get(f.get("id", ""))
                if enriched is not None:
                    findings[i] = enriched.model_dump(mode="json")
    by_module = block.get("by_module")
    if isinstance(by_module, dict):
        for mod_name, mod_findings in list(by_module.items()):
            if isinstance(mod_findings, list):
                for i, f in enumerate(mod_findings):
                    if isinstance(f, dict):
                        enriched = enriched_by_id.get(f.get("id", ""))
                        if enriched is not None:
                            mod_findings[i] = enriched.model_dump(mode="json")


def _apply_tier3_enrichments(
    base: dict[str, Any], chart_input: ChartInput
) -> dict[str, Any]:
    """Layer Tier-3 enrichments on top of the core pipeline output.

    Tier-3 chain: citations -> consensus -> dispute -> yoga calibration
    -> contradiction detection -> robustness. Each subsystem reads the
    bare ReadingOutput payload and returns enriched Findings.

    Lazy imports — these heavy modules (sentence_transformers, torch via
    rag_citations) are imported here so the ``--no-enrich`` path never
    pulls them. Per spec Section 9 perf discipline.
    """
    logger.debug(
        "Tier-3 enrichment invoked for dob=%s", chart_input.dob
    )
    warnings: list[str] = list(base.get("warnings") or [])

    # Lazy imports — see module docstring for rationale.
    from app.reading.computations import (
        consensus_scoring,
        contradiction_detector,
        dispute_surfacing,
        rag_citations,
        yoga_calibration,
    )

    # Collect every flat findings list from the 3 stage blocks.
    blocks_to_walk = ("primitives", "foundations", "practitioner")
    flat_dicts: list[dict[str, Any]] = []
    for key in blocks_to_walk:
        block = base.get(key) or {}
        for f in block.get("findings") or []:
            if isinstance(f, dict):
                flat_dicts.append(f)
    findings_list = _findings_from_dicts(flat_dicts)

    primitives_view = base.get("primitives") or {"findings": [], "by_module": {}}

    # Step 1: citations.
    try:
        findings_list = rag_citations.attach_citations(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.rag_citations failed: {type(exc).__name__}: {exc}"
        )
        logger.warning("rag_citations failed: %s", exc)

    # Step 2: consensus (depends on citations).
    try:
        findings_list = consensus_scoring.score_consensus(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.consensus_scoring failed: {type(exc).__name__}: {exc}"
        )

    # Step 3: dispute surfacing.
    try:
        findings_list = dispute_surfacing.surface_disputes(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.dispute_surfacing failed: {type(exc).__name__}: {exc}"
        )

    # Step 4: yoga calibration.
    try:
        findings_list = yoga_calibration.calibrate_yogas(
            findings_list, primitives_view,
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.yoga_calibration failed: {type(exc).__name__}: {exc}"
        )

    # Apply enriched findings back into the base dict.
    enriched_by_id = {f.id: f for f in findings_list}
    for key in blocks_to_walk:
        _apply_finding_enrichments_to_block(base.get(key) or {}, enriched_by_id)

    # Step 5: contradiction detection (top-level, reads the assembled output).
    try:
        contradictions = contradiction_detector.detect_contradictions(base)
        base["contradictions"] = [c.model_dump(mode="json") for c in contradictions]
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.contradiction_detector failed: {type(exc).__name__}: {exc}"
        )

    # Step 6: robustness — uses the PRIVATE _run_core_pipeline.
    try:
        from app.reading.computations import birth_time_robustness
        robustness_findings = birth_time_robustness.score_robustness(
            chart_input, base,
        )
        rob_by_id = {f.id: f for f in robustness_findings}
        # Merge robustness back into the per-stage findings.
        for key in blocks_to_walk:
            _apply_finding_enrichments_to_block(base.get(key) or {}, rob_by_id)
        base["meta"]["robustness_enabled"] = True
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.birth_time_robustness failed: {type(exc).__name__}: {exc}"
        )

    base["meta"]["enrichment_enabled"] = True
    base["warnings"] = warnings
    return base


def compute(chart_input: ChartInput, enrich: bool = True) -> dict[str, Any]:
    """Run the full kundli pipeline and return a `ReadingOutput`-shaped dict.

    This is the public engine entry point. CLI, API routes, and downstream
    callers (LLM narrators, frontend, RAG layers) should call this rather
    than `_run_core_pipeline`. The only exception is birth-time-robustness,
    which calls `_run_core_pipeline` directly to avoid recursion.

    Args:
        chart_input: Validated user-supplied birth-data envelope.
        enrich: If True (default), layer Tier-3 enrichments after the core
            pipeline completes. If False, return the bare deterministic
            output.

    Returns:
        A dict matching the `ReadingOutput` Pydantic schema.
    """
    base = _run_core_pipeline(chart_input)
    if not enrich:
        return base
    return _apply_tier3_enrichments(base, chart_input)
