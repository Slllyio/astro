"""Tests for the HTML presenter of the detailed report (two-voice, theme-aware, safe)."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.report_html import standalone_html, to_html

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def body(report):
    return to_html(report)


class TestReportHtml:
    def test_has_style_and_all_house_sections(self, body):
        """One inline stylesheet and a section for each of the 12 bhavas."""
        assert body.count("<style>") == 1
        assert body.count('class="house"') == 12

    def test_designs_both_themes(self, body):
        """Palette is token-driven with an OS-dark media query and a data-theme override."""
        assert "@media (prefers-color-scheme: dark)" in body
        assert ':root[data-theme="dark"]' in body

    def test_two_voices_and_provenance(self, body):
        """The doctrine/instrument duality and the not-Raman provenance are present."""
        assert 'class="doctrine"' in body
        assert 'class="instrument"' in body
        assert "EMPIRICAL_ASTRODATABANK" in body

    def test_inverted_channel_tagged(self, body):
        """H12 incarceration, an atlas-proven inverted channel, carries the warning tag."""
        assert "tag--warn" in body
        assert "inverted channel" in body

    def test_divisional_and_timeline_rendered(self, body):
        """Divisional <details> blocks and the Dasha timeline both render."""
        assert body.count('class="varga"') >= 5
        assert body.count('class="period"') >= 5

    def test_timeline_shows_four_tier_grading(self, body):
        """Each Antardasha shows the HTJAH-I grading: association note + all four grade labels."""
        assert "assoc-note" in body
        assert "associated with MD" in body
        for tier in ("par excellence", "ordinary", "limited", "feeble"):
            assert f">{tier}</span>" in body

    def test_calibration_row_shows_the_verdict(self, body):
        """Every calibrated row carries its verdict chip — without it the reader cannot see why a
        house rolled up as it did (this was the H10 'afflicted vs favourable career' contradiction)."""
        assert body.count('class="cal-row"') >= 50

    def test_every_house_closes_with_a_conclusion_line(self, body):
        """Each of the 12 house sections carries the Conclusion note (Raman's own closing
        device), rendered from the same house_conclusion composer the markdown uses."""
        assert body.count("<b>Conclusion</b>") == 12
        first_house = body.find('class="house"')
        assert body.find("<b>Conclusion</b>") > first_house >= 0

    def test_preponderance_renders_between_house_strength_and_longevity(self, body):
        """v14: the testimony-ledger table sits right after the House strength cross-check it
        generalizes, before Longevity, with one row per house and the honesty rules printed."""
        h_start = body.find('id="house-strength"')
        p_start = body.find('id="preponderance"')
        l_start = body.find('id="longevity"')
        assert 0 <= h_start < p_start < l_start
        section = body[p_start:l_start]
        assert "HTJAH-I:983-991" in section and "HTJAH-I:8870" in section
        assert "NO numeric rule" in section
        assert "NOT counted among its own witnesses" in section
        assert section.count("<tr>") == 13    # header + 12 houses

    def test_ruler_of_nativity_renders_after_header(self, body):
        """v13: the Ruler of the nativity card sits right after the header (the chart signature
        chips live inside it) and before the Running-now box, citing the first-impression
        doctrine (HTJAH-I:16001-16002) and the strongest-planet passage (HTJAH-I:6248)."""
        h_start = body.find('class="sig"')
        r_start = body.find('id="ruler"')
        n_start = body.find('id="now"')
        assert 0 <= h_start < r_start < n_start
        section = body[r_start:n_start]
        assert "HTJAH-I:16001-16002" in section
        assert "HTJAH-I:6248" in section
        assert "not a prediction" in section
        # a verdict chip must appear inside cal-rows, not only on house heads
        assert 'class="cal-row"><span class="sig-name"' in body
        assert body.count("chip chip--") > body.count('class="house-head"')

    def test_new_sections_all_render(self, body):
        """Info box, distinctive table, positions, yogas, SAV, now-box, glossary, ToC."""
        for marker in ('class="infobox"', 'id="stands-out"', 'id="positions"', 'id="yogas"',
                       'id="sav"', 'class="nowbox"', 'id="glossary"', 'class="toc"'):
            assert marker in body

    def test_house_pillars_and_driver(self, body):
        """Raman's pillars (lord/karaka/navamsa) and the rollup driver reach the HTML."""
        assert 'class="pillars"' in body
        assert "<b>Lord</b>" in body and "<b>Karaka</b>" in body
        assert 'class="driver"' in body

    def test_html_lord_tag_uses_the_lagna_frame_strength(self, report, body):
        """Regression test for a real bug: the HTML '<b>Lord</b> X (...)' strength word must
        match the lagna-frame ledger's own lord_strong, not whichever frame won as the lead
        signification's ledger (symptom on a real chart: 'Lord Mars (strong) | Karaka Mars
        (weak)' for the identical planet). Scoped to each house's own <section> block."""
        import re
        from app.raman_saab.detailed_report import _lagna_ledger
        blocks = body.split('<section class="house"')[1:]   # one entry per house, in H1..H12 order
        assert len(blocks) == 12
        for pf, block in zip(report.proformas, blocks):
            if not pf.significations:
                continue
            lagna_led = _lagna_ledger(pf.significations[0])
            if lagna_led.lord_strong is None:
                continue
            pattern = rf"<b>Lord</b> {re.escape(pf.lord)}(?: in H\d+)? \((strong|weak)\)"
            m = re.search(pattern, block)
            assert m is not None, f"no Lord tag found for house {pf.house} ({pf.lord})"
            assert m.group(1) == ("strong" if lagna_led.lord_strong else "weak")

    def test_renderer_parity_with_markdown(self, report, body):
        """Every non-empty Synthesis field the markdown shows must also appear in the HTML."""
        s = report.synthesis
        for value in (s.lagna, s.navamsa_lagna, s.atmakaraka, s.arudha_lagna, s.karakamsa,
                      s.upapada, s.spouse_significator, s.chara):
            assert value in body, f"HTML dropped {value!r}"
        if s.sade_sati:
            assert "Sade-Sati" in body
        if s.panchanga:
            assert "Panchanga" in body
        if s.deeptadi:
            assert "Deeptadi" in body

    def test_grading_is_not_duplicated_in_the_presenter(self):
        """Both renderers must consume the single hoisted grading implementation."""
        import inspect

        from app.raman_saab import report_html
        src = inspect.getsource(report_html)
        assert "graded_buckets" in src
        assert "bhukti_tier(" not in src          # no second copy of the doctrine grading

    def test_charts_are_drawn_and_astronomically_correct(self, report, body):
        """Rasi + Navamsa South-Indian grids render, with each graha in its computed sign."""
        import re
        assert body.count('class="chartgrid"') == 2
        rasi = body.split('class="chartgrid"')[1]
        for name, abbr in (("Sun", "Su"), ("Saturn", "Sa"), ("Moon", "Mo")):
            sign = report.chart.planets[name].sign
            cell = re.search(rf'grid-area:s{sign}">.*?</div>', rasi, re.S)
            assert cell and abbr in cell.group(0), f"{name} missing from sign {sign}"
        assert 'class="cbox asc"' in body          # ascendant is marked

    def test_divisional_blocks_are_cards_not_pre_dumps(self, body):
        """Varga readings render as structured cards, core visually split from overlay."""
        assert "<pre>" not in body
        assert "vsec vcore" in body and "vsec voverlay" in body
        assert 'class="vrow"' in body and 'class="vbanner"' in body

    def test_timeline_accordion_opens_only_the_running_md(self, body):
        """Mahadasha groups collapse; exactly the running one is expanded."""
        assert body.count('<details class="md-group"') >= 4
        assert body.count('<details class="md-group" open>') == 1

    def test_filters_tooltips_heatmap_and_sticky_bar(self, body):
        """Interactive affordances: filters, glossary tooltips, SAV heat, sticky header."""
        assert 'data-filter="all"' in body and 'data-filter="distinctive"' in body
        assert 'data-flags="' in body
        assert "has-gloss" in body and "cursor:help" in body
        assert 'class="num heat"' in body and "color-mix" in body
        assert 'id="stickybar"' in body and "IntersectionObserver" in body

    def test_caveat_tags_are_iconised(self, body):
        """INVERTED / NEAR-UNIVERSAL tags carry a border and glyph so they cannot be skimmed."""
        assert ".tag--warn::before" in body and ".tag--univ::before" in body
        assert "border:1px solid var(--warn)" in body

    def test_print_and_accessibility_fixes(self, body):
        """Print stylesheet, meter midpoint, and no opacity-dimmed text."""
        assert "@media print" in body
        assert "meter-mid" in body
        assert "translateX(-50%)" in body        # meter mark cannot clip at 100%

    def test_grade_legend_and_plain_summary(self, body):
        """A plain-language legend and per-bhukti plain summary make the jargon readable."""
        assert "grade-legend" in body
        assert 'class="plain"' in body
        assert "In plain terms" in body

    def test_info_box_names_inverted_locations(self, body):
        """The top-level info box lists inverted channels by house, not just a bare count."""
        assert "Inverted channels in this chart" in body
        assert "H3 courage" in body and "H12 incarceration" in body
        assert "infonote--warn" in body

    def test_split_status_badge_and_inverted_banner(self, body):
        """The majority-tenor badge and the inverted-driver banner both reach the HTML,
        addressing the H10/H12 weakest-link contradiction directly in the house head."""
        assert "split-badge" in body
        assert "split-note" in body
        assert "split-note--warn" in body
        assert "atlas-proven" in body and "INVERTED channel" in body

    def test_synthesis_insight_does_not_repeat_itself(self, body):
        """The HTML insight card leads with the plain reading once, then a distinctly-styled
        source quote — no duplicate 'In plain terms' restatement of the doctrine line. Scoped
        to the Integrated-insights section: the Life-narrative section legitimately keeps its
        OWN 'In plain terms:' label (plain_bhukti_summary) and must not be touched."""
        start = body.find('id="synthesis"')
        end = body.find('id="glossary"')
        assert 0 <= start < end
        section = body[start:end]
        assert "source-quote" in section
        assert "The text says:" in section
        assert "In plain terms:</b>" not in section   # that label belonged to the old, redundant line

    def test_html_escapes_untrusted_name(self):
        """A name with markup is escaped, never injected as live HTML."""
        evil = BirthData("<script>alert(1)</script>", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
        out = to_html(build_detailed_report(evil))
        assert "<script>alert(1)</script>" not in out
        assert "&lt;script&gt;" in out

    def test_html_plain_reading_precedes_signature_chips(self, body):
        """In the HTML document, 'Your Reading' renders before the technical signature chips —
        the plain answer comes first, the jargon-dense detail after."""
        pr_pos = body.find('id="plain-reading"')
        sig_pos = body.find('class="sig"')
        assert 0 <= pr_pos < sig_pos

    def test_nichod_section_rendered_last(self, body):
        """The Nichod capstone renders with its essence blockquote, appears after the
        Glossary, and its ingredients reuse the existing .vsec/.vrow component pattern."""
        assert 'id="nichod"' in body
        assert 'class="nichod-essence"' in body
        glossary_pos = body.find('id="glossary"')
        nichod_pos = body.find('id="nichod"')
        assert 0 <= glossary_pos < nichod_pos
        nichod_section = body[nichod_pos:]
        assert 'class="vsec vcore"' in nichod_section
        assert 'class="vrow"' in nichod_section

    def test_gochara_outlook_svg_renders_in_the_gochara_section(self, body):
        """The multi-year outlook is an SVG nested inside the existing #gochara section, not a
        new top-level section (the split-status precedent: enrich in place, no contract row)."""
        g_start = body.find('id="gochara"')
        g_end = body.find('id="vargas"')          # the next section after Gochara
        assert 0 <= g_start < g_end
        section = body[g_start:g_end]
        assert 'id="gochara-outlook"' in section
        assert section.count("<svg") == 1
        assert section.count('class="gochara-bar"') > 0

    def test_gochara_outlook_bars_carry_hover_detail_and_today_marker(self, body):
        """Each bar exposes its exact dates/AV/Vedha via a native <title> tooltip, and a 'today'
        marker orients the reader on the 25-year span."""
        g_start = body.find('id="gochara-outlook"')
        section = body[g_start:body.find('id="vargas"')]
        assert "<title>" in section and "AV support" in section
        assert ">today<" in section

    def test_dasha_transit_confluence_section_renders(self, body):
        """The Dasha x Transit confluence section sits between Gochara and Divisional deep-reads,
        with a row per confluence window."""
        g_start = body.find('id="gochara"')
        d_start = body.find('id="dasha-transit"')
        v_start = body.find('id="vargas"')
        assert 0 <= g_start < d_start < v_start
        section = body[d_start:v_start]
        assert "In simple terms:" in section
        assert "HTJAH-II:4679" in section
        assert section.count("<tr>") >= 2   # header + at least one confluence row

    def test_yoga_dasha_timing_section_renders(self, body):
        """Yoga x Dasha timing sits right after Yogas and before Ashtakavarga, with a row per
        yoga-lord confluence, and states the 3-family coverage gap."""
        y_start = body.find('id="yogas"')
        t_start = body.find('id="yoga-timing"')
        s_start = body.find('id="sav"')
        assert 0 <= y_start < t_start < s_start
        section = body[t_start:s_start]
        assert "In simple terms:" in section
        assert "HTJAH-I:4324" in section
        assert "coverage gap" in section
        assert section.count("<tr>") >= 2   # header + at least one yoga-timing row

    def test_house_strength_cross_check_renders(self, body):
        """House strength cross-check sits right after House-by-house and before the
        Preponderance section that generalizes it (v14 moved the slice boundary — previously
        Longevity was the next anchor), with one row per house, ranks and SAV bindus shown."""
        h_start = body.find('id="houses"')
        s_start = body.find('id="house-strength"')
        l_start = body.find('id="preponderance"')
        assert 0 <= h_start < s_start < l_start
        section = body[s_start:l_start]
        assert "In simple terms:" in section
        assert "GBB-9:332" in section
        assert section.count("<tr>") == 13    # header + 12 houses
        assert "of 12" in section

    def test_integrated_insights_generalizes_the_multi_axis_principle(self, body):
        """Item #8 of the confluence audit: right after the Integrated insights heading, a
        second section-sub paragraph must generalize the House strength cross-check's
        magnitude-vs-direction finding to Avastha (state), Ishta/Kashta (tendency) and AV
        bindus (a lower-reliability corroboration tier) as independent axes."""
        s_start = body.find('id="synthesis"')
        g_start = body.find('id="glossary"')
        assert 0 <= s_start < g_start
        section = body[s_start:g_start]
        assert "independent axes" in section.lower()
        assert "Deeptadi avasthas" in section and "HPA Ch.7" in section
        assert "GBB-10:134" in section
        assert "HTJAH-II:4453-4456" in section
        assert "not a contradiction" in section

    def test_ishta_kashta_outlook_renders(self, report, body):
        """Ishta/Kashta outlook sits right after Life-narrative and before the MD-lord
        condition outlook, one row per bhukti in the windowed timeline, doctrine cited."""
        t_start = body.find('id="timeline"')
        i_start = body.find('id="ishta-kashta"')
        m_start = body.find('id="md-condition"')
        assert 0 <= t_start < i_start < m_start
        section = body[i_start:m_start]
        assert "In simple terms:" in section
        assert "GBB-10:134" in section
        assert section.count("<tr>") == len(report.ishta_kashta) + 1   # header + one per bhukti

    def test_md_condition_outlook_renders(self, report, body):
        """MD-lord condition outlook sits right after Ishta/Kashta and before the AV dasha-seat
        outlook, one row per Mahadasha RUN (not per bhukti), doctrine cited."""
        i_start = body.find('id="ishta-kashta"')
        m_start = body.find('id="md-condition"')
        a_start = body.find('id="av-dasha-seat"')
        assert 0 <= i_start < m_start < a_start
        section = body[m_start:a_start]
        assert "In simple terms:" in section
        assert "HPA-24:51-86" in section
        assert section.count("<tr>") == len(report.md_condition) + 1   # header + one per MD run

    def test_av_dasha_seat_outlook_renders(self, report, body):
        """AV dasha-seat outlook sits right after MD-lord condition and before Gochara, one row
        per Mahadasha run, Raman's own AV-reliability caveat printed at the section head."""
        m_start = body.find('id="md-condition"')
        a_start = body.find('id="av-dasha-seat"')
        # v16 (2026-08-03): the Dasha-Kakshya section now sits between the AV seat and Gochara,
        # so the AV slice ends at ITS marker (the row-count assertion below must not swallow
        # the Kakshya table's rows).
        k_start = body.find('id="dasa-kakshya"')
        g_start = body.find('id="gochara"')
        end = k_start if 0 <= k_start < g_start else g_start
        assert 0 <= m_start < a_start < end
        section = body[a_start:end]
        assert "HTJAH-II:4453-4456" in section
        assert "does not seem to be quite reliable" in section
        assert "In simple terms:" in section
        assert section.count("<tr>") == len(report.av_dasha_seats) + 1

    def test_maraka_saturn_confluence_renders_when_present(self, body):
        """When the maraka x Saturn-transit section fires, it sits right after The maraka
        scheme and before Life-narrative, framed as method-not-prediction."""
        if 'id="maraka-saturn"' not in body:
            return   # this chart's death-window may not overlap the tracked Saturn span
        mk_start = body.find('id="maraka"')
        ms_start = body.find('id="maraka-saturn"')
        t_start = body.find('id="timeline"')
        assert 0 <= mk_start < ms_start < t_start
        section = body[ms_start:t_start]
        assert "HTJAH-II:4846-4849" in section
        assert "not a prediction" in section
        assert "real-outcome validation measured NO death-timing signal" in section

    def test_standalone_wraps_document(self, report):
        """The standalone wrapper is a full, titled UTF-8 document."""
        doc = standalone_html(report, title="My Reading")
        assert doc.startswith("<!doctype html>")
        assert "<title>My Reading</title>" in doc
        assert 'charset="utf-8"' in doc


class TestAshtakavargaCompletenessHtml:
    """AV completeness (2026-08-17): the HTML AV section shows the BAV matrix, the HPA-26
    reductions with their honesty label, the Sodya Pinda, and the Lagna/Moon column marks."""

    def test_av_section_carries_matrix_reductions_and_pinda(self, body):
        """All three new blocks render inside the Ashtakavarga section, before Houses."""
        s = body.find('id="sav"')
        e = body.find('id="houses"')
        sec = body[s:e]
        assert "Bhinnashtakavarga (BAV)" in sec
        assert "HPA-26 reductions (Trikona + Ekadhipathya Sodhana)" in sec
        assert "Sodya Pinda (Rasi + Graha Gunakara)" in sec
        assert ("used classically for special calculations; shown for completeness; ASP "
                "transit application deferred pending corpus") in sec
        assert "ASP-14:196-198" in sec and "103/88/191" in sec

    def test_av_grid_marks_lagna_and_moon_and_deviation(self, report, body):
        """The SAV grid gains a deviation row and Lagna/Moon marker cells; each of the 7 BAV
        rows highlights the planet's own natal-seat cell."""
        s = body.find('id="sav"')
        sec = body[s:body.find('id="houses"')]
        assert '<td class="strong">Lagna</td>' in sec
        assert '<td class="strong">Moon</td>' in sec
        assert "judged from the Moon" in sec
        assert sec.count('class="num strong"') == 7      # one seat cell per BAV row
        for planet, total in (("Sun", 48), ("Jupiter", 56), ("Saturn", 39)):
            assert f"<td>{planet}</td>" in sec
            assert f'<td class="num">{total}</td>' in sec


class TestWave1CompletenessHtml:
    """Wave-1 (2026-08-17) standalone-HTML parity: positions gain longitude/Ascendant/nak-lord,
    house strength gains the rupas column, Baladi/Jagradadi render in the Deeptadi section,
    maraka tiers name their reasons, confluence rows spell their addends, and the
    interactive-only Muhurtha panel is pointed at."""

    def test_positions_have_longitude_ascendant_and_nak_lord(self, body):
        """Ascendant row first with the canonical 23 Vi 59'.. longitude; Moon row names its
        Vimshottari lord Mercury."""
        s = body.find('id="positions"')
        sec = body[s:body.find('id="rect-confidence"')] or body[s:s + 6000]
        assert "<th>nak lord</th>" in sec and '<th class="num">longitude</th>' in sec
        # the minute/second quotes are HTML-escaped by _esc (&#x27; / &quot;)
        assert "<b>Ascendant</b>" in sec and "23 Vi 59&#x27;17&quot;" in sec
        assert sec.find("<b>Ascendant</b>") < sec.find("<b>Sun</b>")
        moon_i = sec.find("<b>Moon</b>")
        assert "<td>Mercury</td>" in sec[moon_i:moon_i + 400]

    def test_house_strength_shows_rupas_column(self, report, body):
        """The Bhava Bala magnitude joins the rank in the cross-check table."""
        assert "<th class=\"num\">Bhava Bala (rupas)</th>" in body
        row0 = report.house_strength[0]
        assert f'<td class="num">{row0.bhava_bala / 60.0:.2f}</td>' in body

    def test_deeptadi_shows_baladi_jagradadi_table(self, body):
        """Canonical pin Saturn = Mrita/Swapna appears in the per-planet avastha table with
        the CLASSICAL_NONCITABLE provenance label."""
        s = body.find('id="deeptadi"')
        assert s >= 0
        sec = body[s:s + 6000]
        assert "<th>Baladi (ageing)</th>" in sec
        assert "<b>Saturn</b></td><td>Mrita</td><td>Swapna</td>" in sec
        assert "CLASSICAL_NONCITABLE" in sec

    def test_maraka_reasons_and_score_parts_render(self, report, body):
        """Tier rows name each graha's qualifying clause; the confluence table spells the
        score addends."""
        assert "Venus (lord of the 2nd)" in body
        assert "Jupiter (lord of the 7th)" in body
        if report.maraka_saturn:
            c0 = report.maraka_saturn[0]
            assert f"{c0.score} = {c0.score_parts}" in body

    def test_muhurtha_pointer_present(self, body):
        """The pointer paragraph renders after the timing sections, before the divisionals,
        and adds no new section heading."""
        i = body.find("Today for you (Muhurtha)")
        assert i >= 0
        assert body.find('id="gochara"') < i < body.find('id="vargas"')
        assert "computed live at\n    view time" in body
