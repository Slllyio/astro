"""Gap-module annotator — call Track B's 8 Gap modules over a Track-A reading.

Track B's "Gap" modules add predictive depth that Track A doesn't have:

| Gap | Module | What it adds |
|---|---|---|
| A | ``ashtakavarga_predictive`` | SAV/BAV with kakshya owner, sage_dasha_bhukti grade |
| B | ``varga_confirmation`` | Cross-D-chart bhava verdict confirmation |
| D | ``karakamsa_arudha`` | Atmakaraka karakamsa + Arudha + Upapada padas |
| E | ``sensitive_points`` | Bhrigu Bindu, Pranapada, Upagrahas, Maandi, Beeja/Kshetra |
| F | ``avastha_completion`` | Baladi + Deeptadi avasthas |
| G | ``vimsopaka_bala`` | Composite multi-varga dignity score |
| H | ``nakshatra_deep`` | Tara Chakra, Gana/Yoni/Nadi kootas, attributes |
| J | ``bhavat_bhavam`` | (UNAVAILABLE on Windows — CP1252 encoding bug in module docstring) |

This adapter builds a Track-B ``Chart`` from a Track-A reading and runs the
applicable Gap modules over it. Modules that need inputs we don't have are
**gracefully skipped** with a reason string in the output.

Public surface
--------------
- ``annotate_with_gap_modules(reading_dict, *, day_of_week=None,
                              is_day_birth=None)`` → ``GapAnnotatedReading``
- ``chart_from_reading(reading_dict)`` → ``Chart`` (exposed for advanced
  callers who want the Track-B Chart bridge without the Gap-module wrappers)

Methodology
-----------
This adapter does NOT mutate the input reading. The output envelope
wraps the original ``reading`` dict alongside a ``gap_modules`` block
keyed by Gap letter (A/B/D/E/F/G/H). Each Gap entry is either:

- ``{"available": true, "result": {...}}`` — module ran successfully
- ``{"available": false, "reason": "..."}`` — module skipped (import error,
  missing input, runtime error). The reason is human-readable.

This degradation pattern matches Track B's own ``compose_master_reading``
philosophy: ship whatever ran successfully, transparently note what didn't.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Track B Chart model. This import is safe; the bhavat_bhavam encoding bug
# is only triggered when bhavat_bhavam itself is imported.
from app.core.chart_model import Chart


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class GapModuleEntry(BaseModel):
    """One Gap module's result or skip reason."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gap_letter: str = Field(description="A/B/D/E/F/G/H/J")
    module_name: str
    available: bool
    result: dict[str, Any] | None = None
    reason: str | None = None


class GapAnnotatedReading(BaseModel):
    """Envelope wrapping a Track-A reading + per-Gap module output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.3.0"
    reading: dict[str, Any]
    chart_built: bool
    chart_summary: dict[str, Any] | None = None
    gap_modules: dict[str, GapModuleEntry]
    available_count: int
    skipped_count: int


# ---------------------------------------------------------------------------
# Chart bridge
# ---------------------------------------------------------------------------

def chart_from_reading(reading: dict[str, Any]) -> Chart:
    """Build a Track-B ``Chart`` from a Track-A reading dict.

    Required fields in the reading:
    - ``chart.cusps.sign`` (Lagna sign 1..12)
    - ``chart.lagna_longitude`` (Lagna longitude in degrees)
    - ``chart.planets[planet]`` for each of the 9 grahas with
      ``sign``, ``longitude``, ``house``, ``is_retrograde``.

    Raises
    ------
    KeyError
        If the reading is missing required structure (e.g. no chart.planets).
    """
    chart_block = reading.get("chart") or {}
    cusps = chart_block.get("cusps") or {}
    planets = chart_block.get("planets") or {}

    asc_sign = cusps.get("sign")
    asc_lon = chart_block.get("lagna_longitude")
    if asc_sign is None or asc_lon is None:
        raise KeyError(
            "reading.chart missing lagna_longitude or cusps.sign — cannot build Chart"
        )

    planet_signs: dict[str, int] = {}
    planet_lons: dict[str, float] = {}
    planet_houses: dict[str, int] = {}
    planet_retrograde: dict[str, bool] = {}

    for planet_name, body in planets.items():
        if not isinstance(body, dict):
            continue
        if "sign" in body:
            planet_signs[planet_name] = int(body["sign"])
        if "longitude" in body:
            planet_lons[planet_name] = float(body["longitude"])
        if "house" in body:
            planet_houses[planet_name] = int(body["house"])
        if "is_retrograde" in body:
            planet_retrograde[planet_name] = bool(body["is_retrograde"])

    person_id = (reading.get("meta") or {}).get("reading_id")

    return Chart(
        asc_sign=int(asc_sign),
        asc_lon=float(asc_lon),
        planet_signs=planet_signs,
        planet_houses=planet_houses,
        planet_lons=planet_lons,
        planet_retrograde=planet_retrograde,
        person_id=str(person_id) if person_id else None,
    )


# ---------------------------------------------------------------------------
# Per-Gap callers — each wrapped in defensive try/except
# ---------------------------------------------------------------------------

def _safely_call(gap_letter: str, module_name: str, fn) -> GapModuleEntry:
    """Invoke ``fn()`` and return a GapModuleEntry capturing success/failure."""
    try:
        raw = fn()
    except ImportError as exc:
        return GapModuleEntry(
            gap_letter=gap_letter, module_name=module_name,
            available=False,
            reason=f"import failed: {exc}",
        )
    except (KeyError, ValueError, TypeError) as exc:
        return GapModuleEntry(
            gap_letter=gap_letter, module_name=module_name,
            available=False,
            reason=f"input error: {type(exc).__name__}: {exc}",
        )
    except Exception as exc:  # pragma: no cover — defensive net
        return GapModuleEntry(
            gap_letter=gap_letter, module_name=module_name,
            available=False,
            reason=f"runtime error: {type(exc).__name__}: {exc}",
        )

    if hasattr(raw, "model_dump"):
        result = raw.model_dump(mode="json")
    elif hasattr(raw, "__dict__") and not isinstance(raw, dict):
        result = {k: _serialise(v) for k, v in vars(raw).items()}
    else:
        result = _serialise(raw)

    return GapModuleEntry(
        gap_letter=gap_letter, module_name=module_name,
        available=True,
        result=result if isinstance(result, dict) else {"value": result},
    )


def _serialise(obj: Any) -> Any:
    """Best-effort JSON-friendly projection for dataclass / Pydantic / dict trees."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__") and not isinstance(obj, dict):
        return {k: _serialise(v) for k, v in vars(obj).items()}
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialise(item) for item in obj]
    return obj


def _gap_a_ashtakavarga(chart: Chart) -> GapModuleEntry:
    """Gap A — Ashtakavarga predictive."""
    def _run() -> Any:
        from app.core.ashtakavarga_predictive import compute_predictive
        return compute_predictive(chart)
    return _safely_call("A", "ashtakavarga_predictive", _run)


def _gap_b_varga_confirmation(chart: Chart) -> GapModuleEntry:
    """Gap B — Varga confirmation. The public function takes
    (bhava, d1_pillar_score, varga_pillar_score=None, ...) — we cannot
    invoke it without a per-bhava pillar score from Track A's domain
    layer, so it's always skipped here. The Chart bridge exists; calling
    it is the caller's responsibility once they have a pillar score."""
    return GapModuleEntry(
        gap_letter="B",
        module_name="varga_confirmation",
        available=False,
        reason=(
            "varga_confirmation needs (bhava, d1_pillar_score) per bhava as input. "
            "Track A's DomainReading does not expose pillar scores in a directly-"
            "compatible format. Build a per-domain projection first; see "
            "dkp_modulator_adapter.py for the pillar-score synthesis pattern."
        ),
    )


def _gap_d_karakamsa(chart: Chart) -> GapModuleEntry:
    """Gap D — Karakamsa + Arudha Pada."""
    def _run() -> Any:
        from app.core.karakamsa_arudha import all_arudhas, arudha_lagna, dara_pada, upapada_lagna
        return {
            "arudha_lagna": arudha_lagna(chart),
            "upapada_lagna": upapada_lagna(chart),
            "dara_pada": dara_pada(chart),
            "all_arudhas": all_arudhas(chart),
        }
    return _safely_call("D", "karakamsa_arudha", _run)


def _gap_e_sensitive_points(
    chart: Chart, day_of_week: int | None, is_day_birth: bool | None,
) -> GapModuleEntry:
    """Gap E — Sensitive points (Bhrigu Bindu, Pranapada, Upagrahas)."""
    def _run() -> Any:
        from app.core.sensitive_points import compute_all
        return compute_all(
            chart, day_of_week=day_of_week, is_day_birth=is_day_birth,
        )
    return _safely_call("E", "sensitive_points", _run)


def _gap_f_avastha(chart: Chart) -> GapModuleEntry:
    """Gap F — Avastha completion (Baladi + Deeptadi)."""
    def _run() -> Any:
        from app.core.avastha_completion import avastha_report
        return avastha_report(chart)
    return _safely_call("F", "avastha_completion", _run)


def _gap_g_vimsopaka(chart: Chart) -> GapModuleEntry:
    """Gap G — Vimsopaka Bala (multi-varga dignity score).

    Without per-planet per-varga sign data from Track A, this falls back
    to D1-only mode (vimsopaka_for_chart computes per-varga signs internally
    from the D1 chart's planet positions and Lahiri varga math)."""
    def _run() -> Any:
        from app.core.vimsopaka_bala import vimsopaka_for_chart
        return vimsopaka_for_chart(chart)
    return _safely_call("G", "vimsopaka_bala", _run)


def _gap_h_nakshatra_deep(chart: Chart) -> GapModuleEntry:
    """Gap H — Nakshatra deep (attributes for Moon's nakshatra)."""
    def _run() -> Any:
        from app.core.nakshatra_deep import attributes_for_longitude
        moon_lon = chart.planet_lons.get("Moon")
        if moon_lon is None:
            raise KeyError("Moon longitude missing from chart")
        return {
            "moon_nakshatra_attributes": attributes_for_longitude(moon_lon),
        }
    return _safely_call("H", "nakshatra_deep", _run)


def _gap_j_bhavat_bhavam(chart: Chart) -> GapModuleEntry:
    """Gap J — Bhavat Bhavam. Known CP1252 import bug on Windows."""
    def _run() -> Any:
        # Importing the module triggers the docstring decode on Windows;
        # this is a Track B bug independent of this adapter.
        import app.core.bhavat_bhavam as bb  # noqa: F401
        return {"note": "module imported but no public function called"}
    return _safely_call("J", "bhavat_bhavam", _run)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def annotate_with_gap_modules(
    reading: dict[str, Any],
    *,
    day_of_week: int | None = None,
    is_day_birth: bool | None = None,
) -> GapAnnotatedReading:
    """Run all 8 Gap modules over the Track-A reading and attach results.

    Parameters
    ----------
    reading
        A Track-A reading dict (from ``app.reading.proforma.compute()``).
    day_of_week
        Optional 0..6 (Mon=0). Required for Maandi calculation in
        sensitive_points. If None, Maandi will be skipped within Gap E
        (other sensitive points still compute).
    is_day_birth
        Optional. Required for Maandi. If None, Maandi skipped.

    Returns
    -------
    GapAnnotatedReading
        Envelope with the reading + per-Gap result/skip-reason matrix.

    Notes
    -----
    If the reading lacks the structure to build a Chart (missing
    ``chart.planets`` or ``chart.cusps``), ``chart_built`` is False and
    every Gap module is marked skipped with the Chart construction error.
    """
    chart: Chart | None = None
    chart_summary: dict[str, Any] | None = None
    chart_build_error: str | None = None

    try:
        chart = chart_from_reading(reading)
        chart_summary = {
            "asc_sign": chart.asc_sign,
            "asc_lon": chart.asc_lon,
            "planet_count": len(chart.planet_signs),
            "planets_with_position": sorted(chart.planet_signs.keys()),
        }
    except Exception as exc:
        chart_build_error = f"chart construction failed: {type(exc).__name__}: {exc}"

    gaps: dict[str, GapModuleEntry] = {}

    if chart is None:
        # All gaps skipped due to chart-build failure.
        for letter, module_name in [
            ("A", "ashtakavarga_predictive"),
            ("B", "varga_confirmation"),
            ("D", "karakamsa_arudha"),
            ("E", "sensitive_points"),
            ("F", "avastha_completion"),
            ("G", "vimsopaka_bala"),
            ("H", "nakshatra_deep"),
            ("J", "bhavat_bhavam"),
        ]:
            gaps[letter] = GapModuleEntry(
                gap_letter=letter, module_name=module_name,
                available=False,
                reason=chart_build_error or "Chart unavailable",
            )
    else:
        gaps["A"] = _gap_a_ashtakavarga(chart)
        gaps["B"] = _gap_b_varga_confirmation(chart)
        gaps["D"] = _gap_d_karakamsa(chart)
        gaps["E"] = _gap_e_sensitive_points(chart, day_of_week, is_day_birth)
        gaps["F"] = _gap_f_avastha(chart)
        gaps["G"] = _gap_g_vimsopaka(chart)
        gaps["H"] = _gap_h_nakshatra_deep(chart)
        gaps["J"] = _gap_j_bhavat_bhavam(chart)

    available = sum(1 for g in gaps.values() if g.available)
    skipped = sum(1 for g in gaps.values() if not g.available)

    return GapAnnotatedReading(
        reading=reading,
        chart_built=chart is not None,
        chart_summary=chart_summary,
        gap_modules=gaps,
        available_count=available,
        skipped_count=skipped,
    )
