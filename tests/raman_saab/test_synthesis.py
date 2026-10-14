"""Synthesis layer — the unified per-matter reading that fuses D1 + navamsa + varga + Ashtakavarga
+ dasha activation + transits. Pure assembly over already-computed data (verdict-invariant)."""
from __future__ import annotations

from app.raman_saab.chart.model import BirthData
from app.raman_saab.proforma import read_chart
from app.raman_saab.synthesis import BEYOND_SEQUENCE, running_period, synthesize, to_text

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_synthesize_has_twelve_matters_and_header():
    s = synthesize(_MAINPURI, on=(2026, 6, 28))
    assert len(s.matters) == 12
    assert s.lagna == "Scorpio" and s.atmakaraka == "Sun" and s.arudha_lagna == "Cancer"
    assert s.navamsa_lagna == "Scorpio"            # vargottama
    assert s.karakamsa == "Leo" and s.upapada == "Sagittarius" and s.spouse_significator == "Venus"
    assert s.karakamsa_reading and all("JS 1.2" in line for line in s.karakamsa_reading)
    assert len(s.deeptadi) >= 7 and any("Deeptha" in d or "Vikala" in d for d in s.deeptadi)
    assert s.career and "navamsa-dispositor" in s.career
    assert s.panchanga and "Tithi" in s.panchanga and "Vara" in s.panchanga
    assert s.running_md == "Saturn" and s.running_ad == "Jupiter"
    assert s.chara == "Pisces"
    assert s.sade_sati and "setting" in s.sade_sati
    assert all(mr.reading for mr in s.matters)


def test_synthesis_verdicts_match_read_chart():
    """The synthesis must REPORT the D1 verdicts, never alter them."""
    s = synthesize(_MAINPURI, on=(2026, 6, 28))
    r = read_chart(_MAINPURI, ayanamsa="lahiri")
    assert [mr.verdict for mr in s.matters] == [pf.rollup for pf in r.proformas]


def test_to_text_renders():
    txt = to_text(synthesize(_MAINPURI, on=(2026, 6, 28)))
    assert "SYNTHESIS" in txt and "Lagna Scorpio" in txt
    assert "Ashtakavarga" in txt and "navamsa" in txt


_CANONICAL = BirthData(name="C", year=1990, month=7, day=15, hour=12, minute=0,
                       tz_offset=5.5, latitude=12.97, longitude=77.59)


def test_navamsa_clause_names_both_frames_when_they_differ():
    """Canonical chart H3: the LEAD ledger is the MOON frame (navamsa 'confirms') while the
    LAGNA ledger — which the report's pillar line prints as 'Navamsa neutral' — differs. The
    reading line must DISCLOSE the frame so both lines are true statements about named frames
    (REPORT_CRITIQUE_2026-08-17 P0: the H3 self-contradiction)."""
    s = synthesize(_CANONICAL, on=(2026, 8, 17))
    h3 = next(mr for mr in s.matters if mr.house == 3)
    assert "and the navamsa confirms it (delivered)" in h3.reading
    assert "read from the Moon-frame" in h3.reading
    assert "from the Lagna the navamsa is neutral" in h3.reading


def test_navamsa_clause_undisclosed_when_frames_agree_or_lead_is_lagna():
    """No disclosure tail when the lead IS the lagna frame, or when both frames' navamsa
    testimonies agree — the original wording is byte-identical."""
    from app.raman_saab.synthesis import _compose
    base = _compose("favourable", "confirms", None, None, None)
    assert base == _compose("favourable", "confirms", None, None, None,
                            lead_frame="lagna", lagna_navamsa="neutral")
    assert base == _compose("favourable", "confirms", None, None, None,
                            lead_frame="moon", lagna_navamsa="confirms")
    assert "frame" not in base


def test_frame_disclosure_is_ascii():
    """The disclosure tail must survive the ASCII fold (CP1252 consoles)."""
    from app.raman_saab.synthesis import _compose
    line = _compose("afflicted", "confirms", None, None, None,
                    lead_frame="moon", lagna_navamsa="neutral")
    assert line == line.encode("ascii", "ignore").decode()


class TestAChartReadBeyondItsDashaTimeline:
    """The Vimshottari sequence is unrolled 140 years from the birth Mahadasha's start
    (``vimshottari.mahadasha_timeline``'s ``span_years``). Read on a date past that end,
    ``dasha_on`` legitimately has no period to return — a historical nativity read today is
    the ordinary case, not an exotic one. The synthesis must say so rather than crash.

    Before this, ``synthesize`` dereferenced ``period.maha`` on ``None`` and every birth
    more than ~140 years back raised ``AttributeError`` — reachable from the public API,
    which accepts ``year >= 1800``, so it surfaced as a 500.
    """

    _EINSTEIN = BirthData(name="E", year=1879, month=3, day=14, hour=11, minute=30,
                          tz_offset=1.0, latitude=48.40, longitude=9.99)

    def test_a_nineteenth_century_birth_read_today_does_not_raise(self):
        """1879 + 140 years of unrolled Vimshottari ends in 2019; 2026 is past it."""
        s = synthesize(self._EINSTEIN, on=(2026, 8, 20))
        assert len(s.matters) == 12

    def test_the_running_period_says_it_is_beyond_the_sequence(self):
        """Honest absence, in the same words the chara dasha already uses two lines below
        it — not a silent fallback to the first Mahadasha, which would read as a real
        period and be indistinguishable from one."""
        s = synthesize(self._EINSTEIN, on=(2026, 8, 20))
        assert s.running_md == "(beyond computed sequence)"
        assert s.running_ad == "(beyond computed sequence)"

    def test_to_text_still_renders_the_header(self):
        """The header interpolates both fields; a None would render as the string 'None'."""
        assert "(beyond computed sequence)" in to_text(synthesize(self._EINSTEIN, on=(2026, 8, 20)))

    def test_the_same_chart_inside_its_window_still_names_real_lords(self):
        """The fallback must not leak into charts that DO have a running period — read at
        age 40 the same nativity sits well inside the unrolled sequence."""
        s = synthesize(self._EINSTEIN, on=(1919, 3, 14))
        assert s.running_md != "(beyond computed sequence)"
        assert s.running_ad != "(beyond computed sequence)"


class TestHistoricalChartsBeyondTheVimshottariSpan:
    """A nativity whose ~140-year Vimshottari unroll ended before today.

    `dasha_on` has always been typed `Optional[DashaPeriod]` and documented as returning None
    "if `jd` falls outside the unrolled timeline". `synthesize` dereferenced it anyway, so
    ANY such chart raised `AttributeError: 'NoneType' object has no attribute 'maha'` and no
    report could be produced at all.

    That is not an exotic edge: **most of Raman's own worked nativities are 19th century**, so
    the engine could not report on the very charts it is validated against — the measurement
    tools had to work around it with `on=(birth.year + 35, ...)`.

    The fix follows the precedent already sitting one line below the crash, where the Chara
    dasha surfaces `"(beyond computed sequence)"` rather than a silent fallback. The sentinel is
    a NON-EMPTY string, so prose consumers must route through `running_period()`; truth-testing
    the field yields "You are in a (beyond computed sequence) chapter".
    """

    #: Died 1901; her 120-year cycle from 1819 ended long before any plausible "now".
    VICTORIA = BirthData("Queen Victoria", 1819, 5, 24, 4, 15, 0.0, 51.51, -0.14)

    def test_a_nineteenth_century_chart_produces_a_report(self):
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(self.VICTORIA)
        assert r is not None
        assert r.synthesis.running_md == BEYOND_SEQUENCE

    def test_running_period_reports_absence_rather_than_a_sentinel(self):
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(self.VICTORIA)
        assert running_period(r.synthesis) is None, (
            "the predicate exists so consumers never string-compare; it must collapse the "
            "sentinel to None"
        )

    def test_a_contemporary_chart_still_reports_its_period(self):
        """The guard must not swallow the normal case — otherwise every chart silently loses
        its running period and the tests above would still pass."""
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5,
                                            12.97, 77.59))
        rp = running_period(r.synthesis)
        assert rp is not None and rp[0] and rp[0] != BEYOND_SEQUENCE

    def test_the_sentinel_never_reaches_the_reader_as_prose(self):
        """The whole point of the predicate. A sentinel in a LABEL is fine; a sentinel inside a
        sentence is the engine talking nonsense to a person."""
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown
        from app.raman_saab.report_html import to_html
        r = build_detailed_report(self.VICTORIA)
        for surface, text in (("markdown", to_markdown(r)), ("html", to_html(r))):
            for bad in (f"in a {BEYOND_SEQUENCE} chapter", f"{BEYOND_SEQUENCE}-led",
                        f"living a {BEYOND_SEQUENCE}"):
                assert bad not in text, f"{surface}: sentinel leaked into prose — {bad!r}"

    def test_the_absence_is_disclosed_not_hidden(self):
        """Measured Truth: say the placing-in-time is unavailable, do not quietly omit it."""
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown
        md = to_markdown(build_detailed_report(self.VICTORIA))
        assert "falls outside" in md, "the report must SAY the date is outside the sequence"
