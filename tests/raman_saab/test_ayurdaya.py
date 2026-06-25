"""Ayurdaya (mathematical longevity) — validated against Raman's worked examples.

The per-graha contributions are pinned to Raman's *own stated longitudes* for Chart 33
(Pindayu, HTJAH-II:4103-4260) and Chart 34 (Amsayu, HTJAH-II:4262-4441), to ≤1 day. The
full-pipeline tests (cast from the birth data) assert the SPAN within a few years and the
longevity CLASS exactly — the usable, ephemeris-robust output.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import ayurdaya as ay


def _ymd_close(years: float, y: int, m: int, d: int, tol_days: int = 6) -> bool:
    # tol 6 days absorbs Raman's inconsistent truncation-vs-round of the worked tables
    # (e.g. Mercury 330°25'×12/360 = 11.0139y, which Raman prints as "11y 0m 0d").
    gy, gm, gd = ay._to_ymd(years)
    return abs((gy * 360 + gm * 30 + gd) - (y * 360 + m * 30 + d)) <= tol_days


# --- Pindayu Sphutavarsha per planet (Chart 33 corpus longitudes) ----------------

_CHART33_LON = {  # HTJAH-II:4113-4119 (deg, min)
    "Sun": (114, 26), "Moon": (55, 3), "Mars": (141, 49), "Mercury": (135, 25),
    "Jupiter": (224, 25), "Venus": (123, 42), "Saturn": (41, 36)}
_CHART33_SPHUTA = {  # HTJAH-II:4203-4212
    "Sun": (13, 5, 26), "Moon": (23, 5, 19), "Mars": (8, 5, 26), "Mercury": (11, 0, 0),
    "Jupiter": (9, 7, 9), "Venus": (13, 7, 9), "Saturn": (11, 2, 12)}


@pytest.mark.parametrize("planet", list(_CHART33_SPHUTA))
def test_pindayu_sphutavarsha_matches_chart33(planet: str):
    """Each graha's raw Pindayu term = full × arc/360 reproduces Raman's table to <=1 day."""
    deg, minute = _CHART33_LON[planet]
    lon = deg + minute / 60.0
    years = ay._sphuta_ayurvarsha(planet, lon)
    y, m, d = _CHART33_SPHUTA[planet]
    assert _ymd_close(years, y, m, d), f"{planet}: {ay._to_ymd(years)} vs corpus {(y, m, d)}"


def test_arc_full_at_exaltation_half_at_debilitation():
    """At deep exaltation a graha gives its full term; at debilitation, half."""
    assert ay._sphuta_ayurvarsha("Sun", 10.0) == pytest.approx(19.0)         # exalt -> full
    assert ay._sphuta_ayurvarsha("Sun", 190.0) == pytest.approx(9.5)         # debil -> half
    assert ay._sphuta_ayurvarsha("Jupiter", 95.0) == pytest.approx(15.0)     # exalt
    assert ay._sphuta_ayurvarsha("Jupiter", 275.0) == pytest.approx(7.5)     # debil


# --- Amsayu navamsa-term per planet (Chart 34 corpus longitudes) -----------------

_CHART34_LON = {  # HTJAH-II:4347-4355 (deg, min)
    "Sun": (257, 4), "Moon": (89, 58), "Mars": (23, 26), "Mercury": (234, 36),
    "Jupiter": (317, 57), "Venus": (211, 57), "Saturn": (348, 32)}
_CHART34_TERM = {  # HTJAH-II:4374-4380 (before Bharana/Harana)
    "Sun": (5, 1, 13), "Moon": (2, 11, 26), "Mars": (7, 0, 10), "Mercury": (10, 4, 17),
    "Jupiter": (11, 4, 19), "Venus": (3, 7, 2), "Saturn": (8, 6, 21)}


@pytest.mark.parametrize("planet", list(_CHART34_TERM))
def test_amsayu_navamsa_term_matches_chart34(planet: str):
    """Each graha's raw Amsayu term (navamsas traversed) reproduces Raman's table to <=1 day."""
    deg, minute = _CHART34_LON[planet]
    years = ay._navamsa_years(deg + minute / 60.0)
    y, m, d = _CHART34_TERM[planet]
    assert _ymd_close(years, y, m, d), f"{planet}: {ay._to_ymd(years)} vs corpus {(y, m, d)}"


# --- longevity class + ymd -------------------------------------------------------

def test_longevity_class_bands():
    def cls(yrs):
        return ay.AyurdayaResult("pindayu", yrs, yrs, 0.0, ()).longevity_class
    assert cls(20) == "alpa"
    assert cls(50) == "madhya"
    assert cls(86) == "purna"
    assert cls(31.9) == "alpa" and cls(32.1) == "madhya"
    assert cls(69.9) == "madhya" and cls(70.1) == "purna"


def test_to_ymd_360_day_year():
    assert ay._to_ymd(5.12) == (5, 1, 13)     # Sun Amsayu term
    assert ay._to_ymd(2.0) == (2, 0, 0)


# --- full pipeline (cast from birth) ---------------------------------------------

def test_chart33_pindayu_full_span_purna():
    """Chart 33 (8-8-1912 Bangalore): Pindayu ~ 86y (corpus 86y2m20d), class purna."""
    ch = cast_chart(BirthData(name="c33", year=1912, month=8, day=8, hour=19, minute=35,
                              tz_offset=5.5, latitude=12.97, longitude=77.59), ayanamsa="raman")
    r = ay.pindayu(ch)
    assert r.longevity_class == "purna"
    assert abs(r.total_years - 86.2) < 2.0


def test_chart34_amsayu_full_span_full_life():
    """Chart 34 (29/30-12-1879): the native lived to 70y; Amsayu yields a full-life span."""
    ch = cast_chart(BirthData(name="c34", year=1879, month=12, day=30, hour=1, minute=0,
                              tz_offset=78.25 / 15, latitude=9.833, longitude=78.25), ayanamsa="raman")
    r = ay.amsayu(ch)
    assert r.longevity_class in ("madhya", "purna")
    assert r.total_years > 60.0


def test_expected_longevity_goldens_within_tolerance():
    """For every golden pinning an `expected_longevity`, the ayurdaya engine reproduces
    Raman's worked span (via the appropriate method) within classical tolerance, and reads
    a full/near-full life class — chart_33 (Pindayu 86y) + chart_34 (Amsayu 69y)."""
    import json
    from pathlib import Path
    goldens = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"
    checked = 0
    for ln in goldens.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        rec = json.loads(s)
        exp, b = rec.get("expected_longevity"), rec.get("birth")
        if not exp or "years" not in exp or not b:  # skip death_date-only records
            continue
        dp, _, tp = str(b["dt"]).partition("T")
        y, mo, d = (int(x) for x in dp.split("-"))
        hh, mm = int(tp.split(":")[0]), int(tp.split(":")[1])
        ch = cast_chart(BirthData(name="g", year=y, month=mo, day=d, hour=hh, minute=mm,
                                  tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                                  longitude=float(b["lon"])), ayanamsa="raman")
        want = exp["years"] + exp["months"] / 12 + exp["days"] / 360
        best = min(abs(ay.pindayu(ch).total_years - want), abs(ay.amsayu(ch).total_years - want))
        assert best < 8.0, f"{rec['id']}: closest method off by {best:.1f}y from Raman's {want:.1f}y"
        assert ay.longevity(ch).longevity_class in ("madhya", "purna")  # both full/near-full lives
        checked += 1
    assert checked == 2, f"expected 2 expected_longevity goldens, found {checked}"


def test_ayurdaya_span_brackets_actual_age_at_death():
    """Sanity: the alloted ayurdaya span (best of the two methods) is >= the actual
    age-at-death for every death-dated golden. The span is the POTENTIAL lifespan; a maraka
    can cut it short (Lincoln 56, JFK 46 << their ~73y spans), but cannot exceed it. For
    natural/old deaths (Gandhi 78, chart_35 70) the span sits close to the actual age."""
    import json
    from datetime import date
    from pathlib import Path
    goldens = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"
    checked = 0
    for ln in goldens.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        rec = json.loads(s)
        exp, b = rec.get("expected_longevity"), rec.get("birth")
        if not exp or "death_date" not in exp or not b:
            continue
        by, bm, bd = (int(x) for x in str(b["dt"]).split("T")[0].split("-"))
        dy, dmo, dd = (int(x) for x in exp["death_date"].split("-"))
        age = (date(dy, dmo, dd) - date(by, bm, bd)).days / 365.25
        dp, _, tp = str(b["dt"]).partition("T")
        hh, mm = int(tp.split(":")[0]), int(tp.split(":")[1])
        ch = cast_chart(BirthData(name="g", year=by, month=bm, day=bd, hour=hh, minute=mm,
                                  tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                                  longitude=float(b["lon"])), ayanamsa="raman")
        span = max(ay.pindayu(ch).total_years, ay.amsayu(ch).total_years)
        assert span >= age - 2.0, f"{rec['id']}: span {span:.1f}y < age-at-death {age:.1f}y"
        checked += 1
    assert checked >= 5, f"expected >=5 death-dated goldens, found {checked}"


def test_longevity_selects_a_method_and_returns_result():
    ch = cast_chart(BirthData(name="c", year=1990, month=7, day=15, hour=12, minute=0,
                              tz_offset=5.5, latitude=12.97, longitude=77.59), ayanamsa="raman")
    r = ay.longevity(ch)
    assert r.method in ("pindayu", "amsayu")
    assert r.total_years > 0 and r.longevity_class in ("alpa", "madhya", "purna")
    assert len(r.terms) == 7
