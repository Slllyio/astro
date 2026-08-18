"""Wave-2 matter-monograph additions (REPORT_CRITIQUE_2026-08-17, matter appendix).

Pure re-read pins that hold on any machine, corpus or not: the marriage
happiness/coverture split + Kuja-dosha per-frame narration + Jupiter-on-7th
windows + fortified-first grouping, the children D-7 corroboration + reframe-note
placement + putrakaraka condition, the profession D-10 row + H10 timing +
same-graha convergence disclosure, the wealth dhana/daridra row + lord conditions
+ non-differential self-disclosure + population-context column, the
longevity/arishta balarishta screen disclosure + harmonised band labels +
distinguished no-bhanga cases, and the health-readout provenance relabel.
Every addition is swept past the decree guard (_FORBIDDEN_RE).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (build_detailed_report,
                                            longevity_band_label, to_markdown)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


def _section(md: str, heading: str) -> str:
    i = md.index(heading)
    j = md.index("\n## ", i + 3)
    return md[i:j]


class TestMarriageWave2:
    """Item 1: the B3 split, Kuja narration, Jupiter windows, rule grouping."""

    def test_happiness_coverture_split_rereads_the_h7_significations(self, report):
        """marital_happiness/coverture restate the H7 proforma verdicts verbatim."""
        m = report.marriage
        pf7 = report.proformas[6]
        for field, key in ((m.marital_happiness, "marital_happiness"),
                           (m.coverture, "coverture")):
            sv = next(s for s in pf7.significations if s.signification == key)
            assert field == f"{sv.verdict} ({sv.degree})"

    def test_happiness_coverture_line_renders_in_markdown(self, markdown):
        """The split line shows both significations apart, in the client's chapter."""
        sec = _section(markdown, "## Marriage monograph")
        assert "Marital happiness:" in sec
        assert "the partner's own longevity (coverture):" in sec
        assert "two separate 7th-house significations" in sec

    def test_kuja_narration_names_frames_and_exemption_checks(self, report):
        """Canonical chart: Mars (Aries) is 8th from Lagna and 2nd from Moon —
        both frames narrated with their per-house sign-exemption check."""
        kn = " | ".join(report.marriage.kuja_narration)
        assert "from the Lagna, Mars falls in the 8th" in kn
        assert "from the Moon, Mars falls in the 2nd" in kn
        assert "not an exempt sign" in kn
        assert "conjoins neither Jupiter nor the Moon" in kn

    def test_kuja_narration_conclusion_matches_the_rules_own_firing(self, report):
        """The narration's stands/does-not-arise conclusion is the rule's verdict."""
        from app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations import (
            evaluate_kuja_dosha)
        kd = evaluate_kuja_dosha(report.chart)
        last = report.marriage.kuja_narration[-1]
        assert last == ("the dosha stands" if kd.fires else "the dosha does not arise")

    def test_kuja_accessor_mirrors_the_rule_condition(self, report):
        """evaluate_kuja_dosha.fires equals _KujaDosha().evaluate — no re-decision."""
        from app.raman_saab.doctrine import conditions as C
        from app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations import (
            _KujaDosha, evaluate_kuja_dosha)
        kd = evaluate_kuja_dosha(report.chart)
        assert kd.fires == _KujaDosha().evaluate(C.EvalContext(report.chart))

    def test_kuja_accessor_frames_are_the_canonical_placements(self, report):
        """Mars in Aries H8: Lagna frame house 8, Moon frame house 2 (Moon in H7),
        Venus frame none — none sign-exempt (Aries exempts neither the 8th nor 2nd)."""
        from app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations import (
            evaluate_kuja_dosha)
        kd = evaluate_kuja_dosha(report.chart)
        by = {f.origin: f for f in kd.frames}
        assert by["the Lagna"].house == 8 and by["the Lagna"].stands
        assert by["the Moon"].house == 2 and by["the Moon"].stands
        assert by["Venus"].house == 0 and not by["Venus"].stands
        assert not kd.universal_exempt

    def test_jupiter_h7_windows_reread_the_gochara_outlook(self, report):
        """Every listed window is a favourable Jupiter segment on the 7th from
        the Moon, straight from the already-computed outlook — a pure filter."""
        from app.raman_saab.render import _jd_to_date
        expect = tuple(
            f"{_jd_to_date(seg.start_jd)} to {_jd_to_date(seg.end_jd)}"
            for seg in report.gochara_outlook.get("Jupiter", ())
            if seg.gochara_good and (seg.end_jd - seg.start_jd) >= 25
            and seg.house_from_moon == 7)
        assert report.marriage.jupiter_h7_windows == expect
        assert expect  # the canonical chart has such windows

    def test_fired_rules_grouped_fortified_first_with_tally(self, markdown):
        """The kalatra bullets carry a tally and every fortified row precedes
        every afflicted row."""
        sec = _section(markdown, "## Marriage monograph")
        assert "fortified," in sec and "afflicted):" in sec
        branches = [ln.strip()[3:].split(")")[0] for ln in sec.splitlines()
                    if ln.strip().startswith("- (")]
        assert branches, "no fired-rule bullets rendered"
        last_fort = max(i for i, b in enumerate(branches) if b == "fortified")
        first_affl = min(i for i, b in enumerate(branches) if b == "afflicted")
        assert last_fort < first_affl

    def test_maintainer_notes_routed_to_fine_print(self, markdown):
        """"v1-OOS" / "owned by H7.C.60" no longer sit in client bullets; both
        survive in the trailing fine-print line (ADD-ONLY routing)."""
        sec = _section(markdown, "## Marriage monograph")
        fine = [ln for ln in sec.splitlines() if "Encoding-scope notes" in ln]
        assert len(fine) == 1
        assert "v1-OOS" in fine[0] and "owned by H7.C.60" in fine[0]
        bullets = [ln for ln in sec.splitlines()
                   if ln.strip().startswith("- (") and "Encoding-scope" not in ln]
        assert all("v1-OOS" not in ln and "owned by H7" not in ln for ln in bullets)


class TestSplitMaintainerNotes:
    """The routing helper itself."""

    def test_parenthetical_marker_is_routed(self):
        """A parenthetical carrying 'owned by H7' leaves the client text."""
        from app.raman_saab.monographs import split_maintainer_notes
        clean, note = split_maintainer_notes(
            "Mars in the 2nd (the leg is owned by H7.C.60 to avoid double-counting)")
        assert clean == "Mars in the 2nd"
        assert "owned by H7.C.60" in note

    def test_marker_sentence_outside_parentheses_is_routed(self):
        """A whole trailing sentence carrying 'v1-OOS' leaves the client text."""
        from app.raman_saab.monographs import split_maintainer_notes
        clean, note = split_maintainer_notes(
            "affliction to marriage. Bhava-frame kept in text; grid is v1-OOS")
        assert clean == "affliction to marriage."
        assert "v1-OOS" in note and "kept in text" in note

    def test_clean_text_passes_through_unchanged(self):
        """Text without markers is returned whole, with no note."""
        from app.raman_saab.monographs import split_maintainer_notes
        clean, note = split_maintainer_notes("a happy marriage (HTJAH frame)")
        assert clean == "a happy marriage (HTJAH frame)"
        assert note == ""


class TestChildrenWave2:
    """Item 2: D-7 corroboration, putrakaraka condition, reframe placement."""

    def test_d7_corroboration_rereads_the_saptamsa_core(self, report):
        """The D-7 row restates beeja/kshetra from the Saptamsa reading itself."""
        from app.raman_saab.judges.saptamsa_reading import (
            build_saptamsa_children_reading)
        sr = build_saptamsa_children_reading(report.chart)
        row = report.children.d7_corroboration
        yn = {True: "yes", False: "no", None: "not computed"}
        assert f"Beeja (male fertility point) strong: {yn[sr.raman_core.beeja_strong]}" in row
        assert f"Kshetra (female): {yn[sr.raman_core.kshetra_strong]}" in row

    def test_d7_row_renders_in_markdown(self, markdown):
        """The chapter now shows the Saptamsa row its preamble promises."""
        sec = _section(markdown, "## Children chapter")
        assert "Saptamsa (D-7) corroboration" in sec

    def test_putrakaraka_condition_line_is_computed(self, report):
        """Jupiter's line carries house/dignity/avastha + navamsa dignity."""
        line = report.children.putrakaraka_line
        assert line.startswith("Jupiter (putrakaraka)")
        assert "dignity" in line and "navamsa dignity" in line

    def test_reframe_note_is_the_d7_sections_own_text(self, report):
        """The note is copied verbatim from the Saptamsa reading's notes."""
        from app.raman_saab.judges.saptamsa_reading import (
            build_saptamsa_children_reading)
        sr = build_saptamsa_children_reading(report.chart)
        expect = next(n.text for n in sr.notes if "classical shorthand" in n.text)
        assert report.children.reframe_note == expect

    def test_reframe_note_renders_before_the_fired_rules(self, markdown):
        """"loses a number of children" is never the first thing a parent reads:
        the reframe note precedes the fired-rule bullets in the chapter."""
        sec = _section(markdown, "## Children chapter")
        assert sec.index("classical shorthand for DEGREES") \
            < sec.index("Putra rules firing in THIS chart")
        assert sec.index("classical shorthand for DEGREES") \
            < sec.index("loses a number of children")


class TestProfessionWave2:
    """Item 3: the D-10 row, H10 timing, same-graha convergence disclosure."""

    def test_dasamsa_row_rereads_the_computed_d10_reading(self, report):
        """The row restates the Dasamsa career verdict and D-10 lord dignity."""
        from app.raman_saab.judges.dasamsa_career_reading import (
            build_dasamsa_career_reading)
        dr = build_dasamsa_career_reading(report.chart)
        row = report.profession.dasamsa_row
        assert row[1] == f"career {dr.core.career_verdict}"
        assert dr.core.tenth_lord in row[2]
        assert str(dr.overlay.tenth_lord_d10_dignity) in row[2]

    def test_dasamsa_row_renders_and_is_not_a_convergence_vote(self, report, markdown):
        """The table shows the D-10 row; the convergence tally is computed from
        `sources` only, so appending the row changed no existing count."""
        sec = _section(markdown, "## Profession synthesis")
        assert "The Dasamsa D-10 (re-read; corroboration, not a convergence vote)" in sec
        assert all(src.source != report.profession.dasamsa_row[0]
                   for src in report.profession.sources)

    def test_h10_windows_reread_the_life_chapters(self, report):
        """Each H10 window restates a life-chapter houses_lit entry for H10."""
        from app.raman_saab.render import _jd_to_date
        expect = tuple(
            f"{ch.maha} MD ({_jd_to_date(ch.start_jd)} to {_jd_to_date(ch.end_jd)}): "
            f"H10 {tier}"
            for ch in report.life_chapters.chapters
            for h, tier, _v in ch.houses_lit if h == 10)
        assert report.profession.h10_windows == expect
        assert expect

    def test_convergence_note_names_the_sun_thrice_counted(self, report, markdown):
        """Canonical chart: strongest planet, AK and running MD all resolve to
        the Sun — the note discloses one planet counted three times."""
        note = report.profession.convergence_note
        assert "Sun" in note and "counted 3 times" in note
        assert "One planet, several hats" in _section(markdown,
                                                      "## Profession synthesis")


class TestWealthWave2:
    """Item 4: dhana/daridra row, lord conditions, self-disclosure, percentiles."""

    def test_dhana_row_states_absence_against_the_encoded_set(self, report):
        """No Y.DHANA.*/Y.DARIDRA fires on the canonical chart — presence AND
        absence stated explicitly, checked against the chart's own fired set."""
        fired = {y.id for y in report.yogas}
        assert not any(i.startswith(("Y.DHANA", "Y.DARIDRA")) for i in fired)
        row = report.wealth.dhana_row
        assert "Dhana yogas: none of the encoded set" in row
        assert "Daridra: absent" in row

    def test_dhana_row_renders_in_markdown(self, markdown):
        """The classical first question about wealth appears in the chapter."""
        assert "Dhana / Daridra yogas" in _section(markdown, "## Wealth chapter")

    def test_lord_conditions_cover_the_2nd_and_11th_lords(self, report):
        """Both wealth lords carry a computed house/dignity/avastha line."""
        lines = report.wealth.lord_conditions
        assert len(lines) == 2
        assert lines[0].startswith(f"The 2nd lord {report.proformas[1].lord}")
        assert lines[1].startswith(f"The 11th lord {report.proformas[10].lord}")
        assert all("dignity" in ln and "avastha" in ln for ln in lines)

    def test_population_context_column_carries_percentiles(self, report, markdown):
        """Calibrated signification rows re-read their own percentile; lookup
        rows show '-'; the column renders in the table."""
        sec = _section(markdown, "## Wealth chapter")
        assert "| Population context |" in sec
        h2 = next(x for x in report.wealth.rows
                  if x.channel == "Accumulation (H2 wealth)")
        assert "% of the population" in h2.context
        style = next(x for x in report.wealth.rows
                     if x.channel.startswith("Earning style"))
        assert style.context == ""

    def test_expansion_self_disclosure_fires_when_lens_is_non_differential(
            self, report, markdown):
        """Canonical chart: all five MDs light H2/H11 at par excellence — the
        chapter applies its own calibration standard to itself."""
        assert len(report.wealth.expansion_periods) == \
            len(report.life_chapters.chapters)
        assert "non-differential" in report.wealth.expansion_note
        assert "Self-disclosure" in _section(markdown, "## Wealth chapter")


class TestLongevityArishtaWave2:
    """Item 5: balarishta screen disclosure, band labels, no-bhanga cases."""

    def test_balarishta_screen_disclosed_on_the_clear_case(self, report, markdown):
        """Canonical chart: balarishta does not apply — both chapters disclose
        exactly what was screened, from the primitive's own condition list."""
        from app.raman_saab.primitives.balarishta import screened_conditions
        assert report.balarishta is not None and not report.balarishta.applies
        for heading in ("## Longevity", "## Arishta & Bhanga"):
            sec = _section(markdown, heading)
            assert "screened:" in sec and "- none present" in sec
            for _label, cite in screened_conditions():
                assert cite in sec

    def test_screened_conditions_carry_the_hpa14_cites(self):
        """The disclosure list names the three checked yogas with HPA-14 cites."""
        from app.raman_saab.primitives.balarishta import screened_conditions
        cites = [cite for _l, cite in screened_conditions()]
        assert cites == ["HPA-14:93", "HPA-14:96-98", "HPA-14:111-112"]

    def test_band_label_harmonised_everywhere(self, report, markdown):
        """'purna' renders as 'Purnayu (purna band)' in the Longevity class line,
        the Arishta band row, and the health-readout band."""
        assert longevity_band_label("purna") == "Purnayu (purna band)"
        assert "class **Purnayu (purna band)**" in _section(markdown, "## Longevity")
        assert report.arishta.band.startswith("Purnayu (purna band)")
        assert report.health_readout.longevity_band.startswith("Purnayu (purna band)")

    def test_developer_speak_replaced_with_reader_language(self, markdown):
        """The lifespan coda speaks to the reader, not about the engine."""
        assert "this report never converts the band into a date" in markdown
        assert "the engine's own health layer defers lifespan" not in markdown

    def test_no_bhanga_clear_case_is_distinguished(self, report, markdown):
        """Canonical chart: no planet is debilitated — the chapter says so,
        instead of the ambiguous 'no cancellation operates'."""
        assert report.arishta.bhangas == ()
        assert report.arishta.uncancelled_debilities == ()
        sec = _section(markdown, "## Arishta & Bhanga")
        assert ("no planet is debilitated in this chart, so no cancellation "
                "question arises") in sec
        assert "no debilitation-cancellation operates" not in sec


class TestHealthRelabelWave2:
    """Item 6: the karaka rows' provenance label matches the module's doctrine."""

    def test_karaka_rows_relabelled_single_chart_core(self, report):
        """Moon/Mercury rows say 'single-chart health core (H1/H6/H8 + karakas)';
        the self-contradicting 'D-30 health core' label is gone from every row."""
        provs = [row.provenance for row in report.health_readout.rows]
        assert provs.count("single-chart health core (H1/H6/H8 + karakas)") == 2
        assert all("D-30 health core" not in p for p in provs)


class TestWave2GuardSweep:
    """Every new composed string passes the decree guard (_FORBIDDEN_RE)."""

    def test_new_prose_is_decree_free(self, report):
        """Timed indications in the classical idiom are allowed; the decree
        voice is not — none of the Wave-2 composed strings trips the guard."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        m, c, w, pf, a = (report.marriage, report.children, report.wealth,
                          report.profession, report.arishta)
        from app.raman_saab.primitives.balarishta import screened_conditions
        prose = [
            f"Marital happiness: {m.marital_happiness}; the partner's own "
            f"longevity (coverture): {m.coverture}",
            *m.kuja_narration,
            "; ".join(m.jupiter_h7_windows),
            c.d7_corroboration, c.putrakaraka_line,
            w.dhana_row, *w.lord_conditions, w.expansion_note,
            *(row.context for row in w.rows),
            " ".join(pf.dasamsa_row), pf.convergence_note,
            "; ".join(pf.h10_windows),
            "screened: " + "; ".join(f"{l} ({ci})"
                                     for l, ci in screened_conditions())
            + " - none present",
            longevity_band_label(report.longevity_class),
            "this report never converts the band into a date",
            "no planet is debilitated in this chart, so no cancellation "
            "question arises",
            a.band,
        ]
        hits = {p: [x.group(0) for x in _FORBIDDEN_RE.finditer(p)]
                for p in prose if p and _FORBIDDEN_RE.search(p)}
        assert not hits, hits


class TestWave2HtmlParity:
    """Every markdown addition also renders on the standalone HTML surface."""

    def test_html_carries_every_wave2_addition(self, report):
        """REPORT COMPLETENESS: the additions appear on ALL renderers."""
        from app.raman_saab.report_html import to_html
        h = to_html(report)
        for probe in ("Marital happiness:", "coverture",
                      "Kuja (Mangal) dosha, checked frame by frame",
                      "Jupiter transits touching the 7th",
                      "Encoding-scope notes",
                      "Saptamsa (D-7) corroboration",
                      "classical shorthand for DEGREES",
                      "One planet, several hats", "The Dasamsa D-10",
                      "H10 activations in the window",
                      "Dhana / Daridra yogas", "Lord condition",
                      "Self-disclosure", "population context",
                      "screened:", "none present", "Purnayu (purna band)",
                      "never converts the band into a date",
                      "no planet is debilitated in this chart"):
            assert probe in h, f"HTML missing: {probe}"

    def test_json_carries_every_wave2_field(self, report):
        """The JSON contract exposes the new fields (asdict flow + longevity keys)."""
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        assert {"marital_happiness", "coverture", "kuja_narration",
                "jupiter_h7_windows"} <= set(d["marriage"])
        assert {"d7_corroboration", "putrakaraka_line",
                "reframe_note"} <= set(d["children"])
        assert {"dasamsa_row", "h10_windows",
                "convergence_note"} <= set(d["profession"])
        assert {"dhana_row", "lord_conditions",
                "expansion_note"} <= set(d["wealth"])
        assert "uncancelled_debilities" in d["arishta"]
        assert d["longevity"]["class_label"] == "Purnayu (purna band)"
        assert len(d["longevity"]["balarishta_screened"]) == 3
