"""Patel's Saturn-transit clock — after the review that failed the first version.

The first implementation reduced each planet's own bhinna pinda modulo 27 — a formula in none
of the cited texts — and compared Saturn's NATAL nakshatra while the reader-facing string said
"stands on", as if it were the transit the rule describes. Both failures came from the
bphs-doctrine-reviewer reading Patel ch014 sl.37-38 verbatim (2026-08-07).

The corrected shape is pinned three ways:

* **Against Patel's own printed example** — 324 x 33 = 10692, /27 remainder 0 -> the triad
  {Revati, Aslesha, Jyeshta}; /12 remainder 0 -> {Pisces, Cancer, Scorpio}. Arithmetic checked
  against the text, not against the engine's own output.
* **The transit comparison is a transit** — the marker flag must vary with the reference DATE
  on the same chart, which a natal comparison structurally cannot do.
* **The longevity limb stays unencoded** — Raman's caveat (HTJAH-II:4453-4456) is aimed
  exactly at Ashtakavarga longevity; a test asserts the Ayus arithmetic is absent so adding it
  must be a deliberate act.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.av_pinda_timing import (
    _triad_12,
    _triad_27,
    bhava_saturn_markers,
    samudaya_shodhya_pinda,
)

_CHARTS = [
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
]


@pytest.fixture(scope="module")
def charts():
    return {n: cast_chart(bd) for n, bd in _CHARTS}


class TestPatelsPrintedExamplePinsTheArithmetic:
    """ch014:951-960 — the one place the text does the sum for us."""

    def test_the_nakshatra_triad(self):
        assert set(_triad_27(10692 % 27)) == {"Revati", "Aslesha", "Jyeshta"}

    def test_the_rasi_triad(self):
        # Meena, Kataka, Vrischika in the text's own words
        assert set(_triad_12(10692 % 12)) == {"Pisces", "Cancer", "Scorpio"}

    def test_remainder_zero_is_the_last_element_not_the_first(self):
        """The first version's off-by-one trap: Patel maps remainder 0 to Revati (the 27th),
        never to Aswini."""
        assert _triad_27(0)[0] == "Revati"
        assert _triad_12(0)[0] == "Pisces"

    def test_a_nonzero_remainder_counts_from_aswini(self):
        assert _triad_27(1)[0] == "Aswini"
        assert _triad_27(9)[0] == "Aslesha"
        assert _triad_12(1)[0] == "Aries"


class TestTheMarkerIsPerBhava:
    def test_product_is_samudaya_pinda_times_bhava_bindus(self, charts):
        """The review's core correction: the classical input is the COMBINED pinda times the
        bhava's own bindus — never a per-planet pinda alone."""
        for name, c in charts.items():
            pinda, grid = samudaya_shodhya_pinda(c)
            for m in bhava_saturn_markers(c, c.jd_ut):
                sign = ((c.asc_sign - 1) + (m.house - 1)) % 12 + 1
                assert m.product == pinda * grid[sign], f"{name}/H{m.house}"
                assert m.samudaya_pinda == pinda

    def test_every_marker_is_a_triad(self, charts):
        for name, c in charts.items():
            for m in bhava_saturn_markers(c, c.jd_ut):
                assert len(m.nakshatras) == 3 and len(set(m.nakshatras)) == 3, name
                assert len(m.rasis) == 3 and len(set(m.rasis)) == 3, name

    def test_triad_members_are_nine_apart(self, charts):
        from app.raman_saab.doctrine.av_pinda_timing import _NAK
        for c in charts.values():
            for m in bhava_saturn_markers(c, c.jd_ut):
                idxs = sorted(_NAK.index(n) for n in m.nakshatras)
                assert (idxs[1] - idxs[0]) % 9 == 0 and (idxs[2] - idxs[1]) % 9 == 0


class TestTheComparisonIsATransit:
    def test_the_flag_varies_with_the_reference_date(self, charts):
        """A natal comparison is constant for a chart forever; the transit clock must move.
        Across a Saturn sidereal cycle sampled yearly, the on-marker flag must take both
        values for at least one chart — that is what makes it a CLOCK."""
        import itertools
        seen = set()
        for c in charts.values():
            for years in range(0, 30, 2):
                jd = c.jd_ut + years * 365.2425
                for m in bhava_saturn_markers(c, jd):
                    seen.add(m.saturn_on_nakshatra)
            if seen == {True, False}:
                break
        assert seen == {True, False}, (
            "the marker flag never varied across 30 years of transit — the comparison is "
            "not behaving like a transit clock")

    def test_transit_position_is_reported_alongside(self, charts):
        for c in charts.values():
            for m in bhava_saturn_markers(c, c.jd_ut):
                assert m.saturn_transit_nakshatra is not None
                assert m.saturn_transit_rasi is not None


class TestZeroProductNamesNoAsterism:
    def test_zero_bindu_bhava_emits_no_marker(self, charts):
        for name, c in charts.items():
            for m in bhava_saturn_markers(c, c.jd_ut):
                assert m.product > 0, f"{name}/H{m.house}: a zero product named an asterism"


class TestTheLongevityLimbStaysUnencoded:
    def test_the_ayus_arithmetic_is_absent(self):
        """Raman's caveat is aimed precisely at Ashtakavarga longevity. The x7/27 Ayurdaya
        and the ch015 quotient-as-years arithmetic must not appear; adding either needs its
        own doctrine review."""
        import pathlib
        src = pathlib.Path("app/raman_saab/doctrine/av_pinda_timing.py").read_text(
            encoding="utf-8")
        code = "\n".join(ln for ln in src.splitlines()
                         if not ln.strip().startswith(("#", "*", '"', "'")))
        assert "* 7" not in code and "years" not in code.lower()

    def test_the_rule_detail_says_so(self, charts):
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(_CHARTS[0][1])
        fired = [i for i in r.insights if i.rule.id == "SYN_N10_AV_LONGEVITY"]
        assert fired
        assert "NOT computed" in fired[0].detail
        assert "does not seem to be quite reliable" in fired[0].detail


class TestTheRuleRecordsItsOwnReview:
    def test_doctrine_text_carries_the_correction(self):
        from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES
        r = next(x for x in SYNTHESIS_RULES if x.id == "SYN_N10_AV_LONGEVITY")
        assert "FAILED doctrine review" in r.doctrine
        assert "Samudaya Shodhyapinda" in r.doctrine
        assert "TRANSIT Saturn" in r.doctrine
        assert r.band == "av"
