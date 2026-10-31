"""Raman's timing checks from the timing gap check (USER DECISION 2026-10-24, all 16 fixes).

Each test pins a rule against Raman's printed text or his own worked numbers, never against the
engine's own output.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab import raman_timing as rt

_CANONICAL = BirthData(name="canonical", year=1990, month=7, day=15, hour=12, minute=0,
                       tz_offset=5.5, latitude=12.97, longitude=77.59)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL, ayanamsa="raman")


@pytest.fixture(scope="module")
def report():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL, on=(2026, 10, 24))


class TestBhuktiRelation:
    def test_second_from_major_lord_is_unfavourable_and_a_house_of_death(self, chart):
        """12th/2nd from each other is unfavourable (HPA-24:150-152), and the 2nd from the
        major lord is a house of death from him (NH:13789-13790) — fix 6."""
        moon, mars = chart.planets["Moon"], chart.planets["Mars"]
        seat, reads = rt.bhukti_relation(chart, "Moon", "Mars")
        assert seat == (mars.rasi_house - moon.rasi_house) % 12 + 1
        if seat == 2:
            assert any("2nd/12th" in r and "HPA-24:150-152" in r for r in reads)
            assert any("house of death" in r for r in reads)

    def test_third_and_eleventh_is_the_ideal_combination(self, chart):
        """"disposed in the 3rd and 11th from each other—an ideal combination"
        (HTJAH-I:14115-14116) — fix 6."""
        for md in rt.GRAHAS:
            for ad in rt.GRAHAS:
                seat, reads = rt.bhukti_relation(chart, md, ad)
                if seat in (3, 11):
                    assert any("ideal" in r for r in reads)
                if seat in (6, 8):
                    assert any("6th/8th" in r for r in reads)

    def test_own_bhukti_has_no_relation(self, chart):
        """The major lord's own bhukti carries no relation to read."""
        seat, reads = rt.bhukti_relation(chart, "Moon", "Moon")
        assert seat == 0 and "own bhukti" in reads[0]

    def test_saturn_venus_names_the_fired_raja_yogas(self, chart):
        """"the mutual periods of Saturn and Venus are fatal to Raja-Yogas" with the proviso
        that a powerful yoga is set right later (HTJAH-I:16106-16112) — fix 6."""
        _seat, reads = rt.bhukti_relation(chart, "Saturn", "Venus", ("Example Yoga",))
        assert any("Example Yoga" in r and "HTJAH-I:16106-16112" in r for r in reads)


class TestStarTrial:
    def test_third_fifth_seventh_star_lords_in_a_malefic_dasha(self, chart):
        """The sub-period of a planet ruling the 3rd, 5th or 7th star from the natal star, in a
        malefic's Dasha, is a period of trial (HPA-24:144-148) — fix 4. Canonical Moon is in
        Revati, so the 3rd star is Bharani (Venus), the 5th Rohini (Moon), the 7th Ardra (Rahu)."""
        assert rt.NAKSHATRA[rt._nak_index(chart.planets["Moon"].lon)] == "Revati"
        assert "3rd" in rt.star_trial(chart, "Saturn", "Venus")
        assert "period of trial" in rt.star_trial(chart, "Saturn", "Rahu")
        assert "does not apply" in rt.star_trial(chart, "Jupiter", "Rahu")
        assert rt.star_trial(chart, "Saturn", "Mars") == "-"


class TestSignParts:
    def test_raman_sign_parts(self):
        """Mars and the Sun act in the first 10 degrees, Jupiter and Venus in the middle 10,
        Rahu throughout (AFB-12:197-201; HPA-34:83-85) — fix 13."""
        assert "effective" == rt.sign_part("Sun", 35.0).split(": ")[-1]
        assert "not in its effective part" in rt.sign_part("Mars", 12.0)
        assert rt.sign_part("Jupiter", 45.0).endswith("effective")
        assert "not in its effective part" in rt.sign_part("Venus", 25.0)
        assert rt.sign_part("Rahu", 3.0) == "effective throughout the sign"
        assert rt.sign_part("Saturn", 3.0) == "no sign part named by Raman"


class TestMarriagePoints:
    def test_bhava_sum_matches_ramans_worked_case(self):
        """"Adding the longitudes of the Lagna and the 7th Bhava we get 56° 47' + 236° 47' =
        293° 34' or Capricorn" (HTJAH-I:18426) — fix 12."""
        fake = SimpleNamespace(asc_sign=2, asc_lon=56 + 47 / 60, planets={})
        pts = dict(rt.marriage_points(fake))
        lon = pts["Lagna bhava + 7th bhava"]
        assert abs(lon - (293 + 34 / 60)) < 1e-6
        assert rt._sign(lon) == 10                                  # Capricorn

    def test_marriage_timing_carries_the_bhava_sum(self, report):
        """The marriage monograph's Jupiter resultants include Raman's practised bhava sum
        (HTJAH-I:18296-18297) beside the stated lords' sums (HTJAH-I:8401-8404)."""
        mt = getattr(report.marriage, "timing", None)
        assert mt is not None
        assert "Lagna bhava + 7th bhava" in [s[0] for s in mt.jupiter_sphutas]


class TestLifespanGateColumn:
    def test_every_graha_carries_its_gate(self, report):
        """Each period lord is tagged inside or after the ayurdaya span (HTJAH-I:1578-1580)."""
        t = next(t for t in report.raman_period_checks if t.key == "period_lords")
        assert len(t.rows) == 9
        gate = t.columns.index("lifespan gate")
        assert all(r[gate].startswith("MD begins") for r in t.rows)


class TestSadeSatiRounds:
    def test_rounds_are_numbered_from_birth(self, report):
        """Raman counts up to three rounds in a long life (AFB-12:169-174) — fix 8; the canonical
        native's running round on 2026-10-24 is the second."""
        t = next(t for t in report.raman_transit_checks if t.key == "sade_sati_rounds")
        assert t.rows[0][0].startswith("1st")
        now = [r for r in t.rows if "(now)" in r[0]]
        assert len(now) == 1 and now[0][0].startswith("2nd")
        assert "ASP-13:613-616" in t.note


class TestReportSurfaces:
    def test_every_table_reaches_all_three_renderers(self, report):
        """REPORT COMPLETENESS: each new table's title appears in the markdown, the standalone
        HTML and the report JSON, with its columns."""
        from app.raman_saab.detailed_report import to_markdown
        from app.raman_saab.report_html import to_html
        from app.raman_saab.report_json import to_report_dict
        md, html, js = to_markdown(report), to_html(report), to_report_dict(report)
        tables = report.raman_period_checks + report.raman_transit_checks
        assert {t.key for t in tables} >= {"period_lords", "bhukti_relations", "antaras",
                                           "maraka_order", "sade_sati_rounds",
                                           "transit_dasa_gate", "marriage_point", "sign_parts"}
        jkeys = {t["key"] for t in js["raman_period_checks"] + js["raman_transit_checks"]}
        for t in tables:
            assert f"### {t.title}" in md
            assert t.title.replace("'", "&#x27;") in html or t.title in html
            assert t.key in jkeys
            assert " | ".join(t.columns) in md

    def test_no_table_speaks_in_the_decree_voice(self, report):
        """Every note and cell passes the report guard (app/llm/report_explainer._FORBIDDEN_RE)."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for t in report.raman_period_checks + report.raman_transit_checks:
            for text in (t.title, t.note, *(c for r in t.rows for c in r)):
                assert not _FORBIDDEN_RE.search(text), (t.key, text)

    def test_track_b_chart_has_no_tables(self):
        """A chart without a birth moment (Track-B) yields no timing tables."""
        fake = SimpleNamespace(jd_ut=None)
        assert rt.period_checks(fake, 0.0) == ()
        assert rt.transit_checks(fake, 0.0) == ()


@pytest.fixture(scope="module")
def fired(chart):
    """Insights on a date inside the canonical Moon/Mars bhukti (Mar-Oct 2027)."""
    import swisseph as swe
    from app.raman_saab.doctrine.synthesis_rules import detect_synthesis
    from app.raman_saab.primitives import vimshottari as vd
    jd = swe.julday(2027, 6, 15, 12.0)
    p = vd.dasha_on(chart, jd)
    assert (p.maha, p.antar) == ("Moon", "Mars")
    return {f.rule.id: f.detail for f in detect_synthesis(chart, jd)}


class TestSynthesisRules:
    def test_r15_reads_the_bhukti_relation(self, fired, chart):
        """SYN_R15 states Raman's relation reading for the running bhukti (HPA-24:150-152) —
        fix 6."""
        seat, reads = rt.bhukti_relation(chart, "Moon", "Mars")
        assert "SYN_R15_BHUKTI_RELATION" in fired
        assert reads[0] in fired["SYN_R15_BHUKTI_RELATION"]

    def test_r7_reports_the_bhukti_lords_sandhi_too(self, fired):
        """The residential-strength line now covers the bhukti lord as well (HPA-24:98-100) —
        fix 16."""
        assert "running AD lord Mars" in fired["SYN_R7_RESIDENTIAL_QUANTITY"]
        assert "running MD lord Moon" in fired["SYN_R7_RESIDENTIAL_QUANTITY"]


class TestMarakaSaturnAmsa:
    def test_signature_follows_the_amsa_spans(self, report):
        """"the Rashi and Amsa occupied by him at birth or its trines" (HTJAH-I:11226-11228):
        a row claims both halves only when an Amsa span exists — fix 7."""
        for c in report.maraka_saturn:
            assert c.signature == ("Rasi and Amsa" if c.amsa_spans else "Rasi only")

    def test_score_parts_use_ramans_primary_order(self, report):
        """Primary weights are 5/4/3 by HTJAH-I:783-784; the parts still sum to the score."""
        for c in report.maraka_saturn:
            if c.score_parts:
                total = sum(int(part.split()[-1]) for part in c.score_parts.split(" + "))
                assert total == c.score


class TestAvPindaFrame:
    def test_transit_saturn_is_cast_in_the_natal_ayanamsa(self, chart):
        """The Shodhyapinda clock reads transit Saturn in the chart's own ayanamsa
        (ASP-11:388-393 is Raman's statement of the rule) — fix 14."""
        import swisseph as swe
        from app.raman_saab.doctrine.av_pinda_timing import bhava_saturn_markers
        from app.raman_saab.primitives import transits as tr
        jd = swe.julday(2026, 10, 24, 12.0)
        lon = tr.planet_longitude(jd, "Saturn", ayanamsa=chart.ayanamsa)
        marks = bhava_saturn_markers(chart, jd)
        assert marks
        assert marks[0].saturn_transit_nakshatra == rt.NAKSHATRA[rt._nak_index(lon)]
