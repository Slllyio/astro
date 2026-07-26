"""Tests for the unified detailed report composer (report + honesty overlay)."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown

# Canonical pin (CLAUDE.md): Bangalore 1990-07-15 12:00 IST -> Virgo Lagna, purna longevity.
_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


class TestDetailedReport:
    def test_covers_all_twelve_houses(self, report):
        """Calibration is attached for every one of the 12 bhavas."""
        assert set(report.calibration) == set(range(1, 13))
        assert all(hr.entries for hr in report.calibration.values())

    def test_canonical_lagna_is_virgo(self, report):
        """The pinned Bangalore chart rises in Virgo (astronomical regression guard)."""
        assert report.synthesis.lagna == "Virgo"

    def test_longevity_is_positive_and_classed(self, report):
        """Numeric Ayurdaya yields a positive span and a named longevity class."""
        assert report.longevity_years > 0
        assert report.longevity_class in {"alpa", "madhya", "purna"}

    def test_markdown_has_all_sections(self, markdown):
        """The document carries every top-level section header."""
        for header in ("# Detailed reading", "## Chart signature", "## Longevity",
                       "## House-by-house reading", "### House 1 ", "### House 12 "):
            assert header in markdown

    def test_inverted_channel_is_flagged(self, markdown):
        """H12 incarceration is an atlas-proven inverted channel and must warn."""
        assert "INVERTED channel" in markdown

    def test_two_voices_present(self, markdown):
        """Both the doctrine verdict and the empirical disclosure appear."""
        assert "_Population context:_" in markdown
        assert "EMPIRICAL_ASTRODATABANK" in markdown
        assert "not a validated prediction" in markdown

    def test_output_is_ascii_safe(self, markdown):
        """Rendered like every other renderer: ASCII-safe for CP1252 consoles."""
        assert markdown.isascii()

    def test_divisional_deep_reads_present(self, report, markdown):
        """The Shodasavarga deep-reads (D9/D10/D7/D12/D30/D24) are composed and rendered."""
        assert len(report.divisional) >= 5
        assert "## Divisional deep-reads (Shodasavarga)" in markdown
        assert "### D-9 Marriage (Navamsa)" in markdown
        assert "### D-10 Career (Dasamsa)" in markdown
        assert "RAMAN CORE" in markdown          # the authoritative core block

    def test_life_narrative_is_windowed_md_ad(self, report, markdown):
        """The narrative is MD -> AD and clipped to [now-back, now+forward] with a 'now' marker."""
        assert len(report.timeline.periods) >= 5
        # every shown period is an Antardasha (has an antar lord) inside the window
        lo = report.ref_jd - report.window_back * 365.2425
        hi = report.ref_jd + report.window_forward * 365.2425
        for tp in report.timeline.periods:
            assert tp.period.antar is not None
            assert tp.period.end_jd >= lo and tp.period.start_jd <= hi
        assert "## Life-narrative (Vimshottari Dasha) -" in markdown
        assert "Mahadasha" in markdown and " AD** (" in markdown
        # the HTJAH-I four-tier grading vocabulary all appears across the window
        for tier in ("par excellence", "ordinary", "limited (bhukti lord only)",
                     "feeble (MD lord only)"):
            assert tier in markdown
        assert "associated with MD" in markdown
        assert "<- now**" in markdown          # the current AD is flagged
        # a plain-language legend + a per-bhukti plain summary for lay readers
        assert "What the grades mean:" in markdown
        assert "In plain terms:" in markdown

    def test_plain_summary_reads_for_a_layperson(self, report):
        """The plain gloss names life-areas, not house numbers, and grades intensity."""
        from app.raman_saab.detailed_report import plain_bhukti_summary
        # a strongly-associated (par-excellence) bhukti reads as a strong stretch
        assoc_rows = next(tp.activated for tp in report.timeline.periods
                          if tp.period.antar == tp.period.maha)   # own bhukti = associated
        s = plain_bhukti_summary(assoc_rows, associated=True)
        assert s.startswith("In plain terms:")
        assert "strong, well-supported" in s
        assert "H10" not in s and "career" in s.lower()   # named area, not a house number

    def test_lords_associated_conjunction_and_self(self):
        """Sun/Jupiter/Venus conjoin in H10 on the canonical chart -> associated; a lord is
        trivially associated with itself (own bhukti)."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.primitives.vimshottari import lords_associated
        ch = cast_chart(_CANONICAL, ayanamsa="lahiri")
        assert lords_associated(ch, "Sun", "Jupiter") is True    # co-located in the 10th
        assert lords_associated(ch, "Sun", "Sun") is True        # own bhukti

    def test_information_content_names_inverted_locations(self, report, markdown):
        """The top-level honesty headline names WHICH houses/significations are proven
        inverted, not just a bare count — addressing 'flag these in the summary' feedback."""
        assert report.info.inverted_locations == ("H3 courage", "H12 incarceration")
        assert "H3 courage" in markdown and "H12 incarceration" in markdown
        assert "treat any house driven by one of these" in markdown

    def test_information_content_is_an_honest_aggregate(self, report, markdown):
        """The honesty headline counts the whole calibration, not a sample."""
        i = report.info
        assert i.total == sum(len(hr.entries) for hr in report.calibration.values())
        assert 0 < i.modal_count <= i.total
        assert i.near_universal >= 0 and i.inverted >= 2   # H3 courage + H12 incarceration
        assert "Information content of this reading" in markdown
        assert "not a statement about a life" in markdown

    def test_distinctive_entries_are_ranked_and_rare_first(self, report):
        """Distinctive readings are furthest from the midpoint, non-common rarity first."""
        d = report.distinctive
        assert d and len(d) <= 7
        rar = [0 if e.rarity == "common" else 1 for _h, e in d]
        assert rar == sorted(rar, reverse=True)            # rare/notable before common
        dist = [abs(e.favourability_percentile - 0.5) for _h, e in d if e.rarity != "common"]
        assert dist == sorted(dist, reverse=True)

    def test_evidentiary_layer_present(self, report, markdown):
        """Yogas, positions, Ashtakavarga, nakshatra and pillars all reach the page."""
        assert report.yogas                                 # canonical chart fires several
        assert "## Yogas present in this chart" in markdown
        assert "## Planetary positions" in markdown and "Revati" in markdown
        assert "## Ashtakavarga" in markdown
        assert "**Lord**" in markdown and "**Karaka**" in markdown
        assert report.overview.stronger_frame in ("lagna", "moon")
        assert sum(report.sav.values()) == 337              # SAV invariant

    def test_house_head_names_the_rollup_driver(self, markdown):
        """A house states WHY it rolled up as it did — no silent contradiction."""
        assert "driven by _" in markdown
        assert "weakest decided matter" in markdown         # the rule is stated

    def test_longevity_is_band_first_and_not_false_precision(self, markdown):
        """Raman's order (band, then period) and no two-decimal lifespan."""
        assert "Balarishta" in markdown and "Band by combination" in markdown
        assert "88.24" not in markdown
        assert "never a prediction of death" in markdown

    def test_no_pre_birth_activation_windows(self, report, markdown):
        """Activation windows are clipped to the native's life (was 1978 on a 1990 birth)."""
        import re
        for start, end in re.findall(r"\((?:lord|karaka|timer|maraka|afflictor)\) "
                                     r"(\d{4})-(\d{4})", markdown):
            assert int(end) >= report.birth.year
            assert int(start) >= report.birth.year

    def test_glossary_defines_the_jargon(self, markdown):
        """Every technical term the report uses has a plain-language entry."""
        from app.raman_saab.detailed_report import GLOSSARY
        assert "## Glossary" in markdown
        for term in ("karaka", "bhava", "maraka", "Sade-Sati", "Kuja dosha"):
            assert term in GLOSSARY
        assert "odds ratio 1.09" in GLOSSARY["Kuja dosha"]   # the empirical disclosure

    def test_synthesis_insight_does_not_repeat_itself(self, report, markdown):
        """Each fired insight states its plain reading ONCE, then quotes the source text
        distinctly ('The text says') rather than paraphrasing the same sentence twice back
        to back — the redundancy a reader flagged between the doctrine line and the old
        'In plain terms' restatement. Scoped to the Integrated-insights section only: the
        Life-narrative section legitimately uses its OWN, unrelated 'In plain terms:' label
        (plain_bhukti_summary) and must not be touched."""
        start = markdown.find("## Integrated insights")
        end = markdown.find("## Glossary")
        assert 0 <= start < end
        section = markdown[start:end]
        assert "_The text says_:" in section
        assert "_In plain terms_:" not in section   # the old, redundant label is gone HERE
        from app.raman_saab.detailed_report import _fold_ascii
        for ins in report.insights:
            block_start = section.find(f"**{ins.rule.name}**")
            assert block_start >= 0
            next_item = section.find("\n- **", block_start + 1)
            block = section[block_start:next_item if next_item > 0 else len(section)]
            # the output is ASCII-folded (em dashes -> hyphens etc.), so fold both sides
            # before comparing. The plain meaning appears once (as the lead), not duplicated.
            assert block.count(_fold_ascii(ins.rule.simple_meaning)) == 1
            assert _fold_ascii(ins.rule.doctrine) in block

    def test_complementary_sections_content(self, report, markdown):
        """v2 sections carry their substance: 12 matters, full Shodasavarga, soul, framed maraka."""
        assert len(report.dashboard.entries) == 12
        assert len(report.divisional) == 15          # the full Shodasavarga minus D-1
        for label in ("D-2 Wealth", "D-16 Comforts", "D-27 Strength", "D-60 Totality"):
            assert label in markdown
        assert len(report.soul.jaimini_overlay.chara_karakas) == 7   # strict 7-karaka Jaimini
        assert "not a prediction" in markdown        # the maraka framing
        assert "22nd drekkana lord" in markdown

    def test_pitru_banner_is_mandatory(self, markdown):
        """The pitru section may never appear without its non-Raman provenance notice."""
        pit = markdown.find("## Pitru dosha")
        assert pit >= 0
        assert "Provenance notice" in markdown[pit:pit + 600]
        assert "CLASSICAL_NONCITABLE" in markdown[pit:pit + 600]

    def test_gochara_net_verdict_applies_vedha(self, report, markdown):
        """The transit table's net column = classical verdict minus Vedha obstruction."""
        assert "## Current transits (Gochara) with Vedha" in markdown
        for g in report.gochara:
            assert g.net_good == (g.gochara_good and not g.vedha_by)

    def test_bhukti_tier_is_the_four_grade_scheme(self):
        """The HTJAH-I four grades map exactly (uniform for every house)."""
        from app.raman_saab.primitives.vimshottari import bhukti_tier
        assert bhukti_tier(True, True, associated=True) == "par excellence"
        assert bhukti_tier(True, True, associated=False) == "ordinary"
        assert bhukti_tier(False, True, associated=False) == "limited"   # bhukti lord only
        assert bhukti_tier(True, False, associated=False) == "feeble"    # MD lord only
        assert bhukti_tier(False, False, associated=True) is None        # neither influences

    def test_diacritics_folded_not_blanked(self, markdown):
        """Sanskrit IAST from the varga renderers folds to base letters, never '?' mojibake."""
        assert "Navamsa" in markdown
        assert "Nav?" not in markdown and "k?raka" not in markdown

    def test_split_status_note_when_majority_disagrees_with_headline(self, report, markdown):
        """H10/H12 on the canonical chart are afflicted headlines driven by one signification
        while the majority reads favourable — the split status must say so, without touching
        the verdict itself."""
        from app.raman_saab.detailed_report import (
            driver_entry, signification_tenor_split, tenor_note,
        )
        for house in (10, 12):
            mr = next(m for m in report.synthesis.matters if m.house == house)
            cal = report.calibration[house]
            split = signification_tenor_split(cal)
            assert split.majority == "favourable"
            note = tenor_note(split, mr.verdict)
            assert note is not None and "favourable" in note
        assert "Split status" in markdown
        assert "the headline follows the single weakest decided matter" in markdown

    def test_split_status_silent_when_headline_matches_majority(self, report):
        """A genuinely afflicted house (majority itself afflicted) gets no split note — the
        note exists to prevent false alarm, not to annotate every house."""
        from app.raman_saab.detailed_report import signification_tenor_split, tenor_note
        mr6 = next(m for m in report.synthesis.matters if m.house == 6)
        split = signification_tenor_split(report.calibration[6])
        assert split.majority == mr6.verdict           # canonical H6 is genuinely afflicted
        assert tenor_note(split, mr6.verdict) is None

    def test_tenor_split_tie_reads_as_even_split_not_zero_mixed(self):
        """A 2-favourable/2-afflicted tie must read as 'an even split', never as a nonsensical
        '0 of N mixed' (the bug caught while implementing this)."""
        from app.raman_saab.detailed_report import TenorSplit, tenor_note
        tie = TenorSplit(favourable=2, afflicted=2, mixed=0, total=4, majority="mixed")
        note = tenor_note(tie, "afflicted")
        assert note is not None
        assert "even split" in note
        assert "0 of 4" not in note

    def test_genuine_mixed_majority_reads_correctly(self):
        """A true mixed-verdict plurality (not a tie) is worded distinctly from a tie."""
        from app.raman_saab.detailed_report import TenorSplit, tenor_note
        genuinely_mixed = TenorSplit(favourable=1, afflicted=0, mixed=3, total=4, majority="mixed")
        note = tenor_note(genuinely_mixed, "afflicted")
        assert note is not None and "3 of 4" in note and "genuinely mixed" in note

    def test_driver_entry_flags_inverted_channel_inline(self, report, markdown):
        """H12's driver (incarceration) is the atlas-proven inverted channel — the house head
        must carry an explicit WARNING, not just the small per-row tag."""
        from app.raman_saab.detailed_report import driver_entry
        mr12 = next(m for m in report.synthesis.matters if m.house == 12)
        d = driver_entry(report.calibration[12], mr12.verdict)
        assert d is not None and d.signification == "incarceration" and d.inverted_warning
        assert "WARNING" in markdown and "atlas-proven INVERTED channel" in markdown

    def test_your_reading_is_first_and_jargon_free(self, report, markdown):
        """'Your Reading' is the section right after the title/preamble, before any technical
        content — and it must NEVER leak the jargon that made earlier report versions hard to
        understand (Shadbala, bindus, tier names, MD/AD, raw house numbers)."""
        title_pos = markdown.find("# Detailed reading")
        pr_pos = markdown.find("## Your Reading")
        info_pos = markdown.find("## Information content")
        assert 0 <= title_pos < pr_pos < info_pos

        from app.raman_saab.detailed_report import _fold_ascii
        pr = report.plain_reading
        section = markdown[pr_pos:info_pos]
        # the renderer ASCII-folds output (em dashes -> hyphens etc.); fold both sides to compare
        assert _fold_ascii(pr.opening) in section
        for _theme, para in pr.life_paragraphs:
            assert _fold_ascii(para) in section
        assert _fold_ascii(pr.now) in section
        assert _fold_ascii(pr.notable) in section
        assert _fold_ascii(pr.closing) in section

        banned = ("Shadbala", "rupas", "bindus", "Ashtakavarga", "Vedha", "Ishta", "Kashta",
                  "Karakamsa", "par excellence", "vargottama", "Navamsa", "Bhava Bala")
        for term in banned:
            assert term not in section, f"jargon leaked into Your Reading: {term!r}"
        for h in range(1, 13):
            assert f"H{h} " not in section and f"H{h}:" not in section, \
                f"raw house number leaked into Your Reading: H{h}"

    def test_your_reading_names_the_person_and_current_chapter(self, report):
        """The opening names the chart owner; 'now' names the actual running MD lord's theme,
        not a jargon label."""
        pr = report.plain_reading
        assert report.birth.name in pr.opening
        assert report.synthesis.running_md in pr.now

    def test_your_reading_never_calls_judge_house(self):
        """build_plain_reading must only read the already-assembled report — a translation,
        never a new judgment."""
        import inspect

        from app.raman_saab.detailed_report import build_plain_reading
        src = inspect.getsource(build_plain_reading)
        assert "judge_house" not in src

    def test_plain_signification_translates_known_jargon(self):
        """Sanskrit/technical signification keys get a genuine plain-English gloss, not a bare
        underscore-to-space pass-through."""
        from app.raman_saab.detailed_report import _plain_signification
        assert _plain_signification("poorvapunya") == "merit carried from the past"
        assert _plain_signification("coverture") == "security within marriage"
        assert _plain_signification("incarceration") == "confinement"
        # an unlisted key still degrades gracefully, never raises
        assert _plain_signification("totally_unknown_key") == "totally unknown key"

    def test_nichod_integrates_every_section(self, report, markdown):
        """The Nichod section pulls a concrete value from each major report block and appears
        as the final section, after the Glossary."""
        n = report.nichod
        assert report.synthesis.lagna in n.identity
        assert report.overview.stronger_frame.upper() in n.identity
        assert str(round(report.longevity_years)) in n.longevity
        assert report.longevity_class in n.longevity
        if report.yogas:
            assert report.yogas[0].name in n.yogas
        if report.distinctive:
            h0, e0 = report.distinctive[0]
            assert f"H{h0}" in n.stands_out and e0.signification in n.stands_out
        assert "of 12 matters" in n.matters_tally
        assert n.essence and n.essence.endswith(
            "should be read against the population-context percentiles shown throughout this "
            "report.")
        glossary_pos = markdown.find("## Glossary")
        nichod_pos = markdown.find("## Nichod")
        assert 0 <= glossary_pos < nichod_pos          # nichod is the true final section

    def test_nichod_essence_never_a_new_judgment(self, report):
        """build_nichod must never call judge_house or any verdict-deciding path directly —
        it may only read the already-assembled DetailedReport (the same invariant the rest of
        the report honours)."""
        import inspect

        from app.raman_saab.detailed_report import build_nichod
        src = inspect.getsource(build_nichod)
        assert "judge_house" not in src
        assert "_decide(" not in src

    def test_nichod_caution_reuses_the_split_status_fix(self, report):
        """When the current period lights a house whose weakest-link headline disagrees with
        its majority, the Nichod's caution names it — the same machinery as the house-by-house
        split-status fix, not a re-derivation."""
        n = report.nichod
        if n.caution and "5 of 6" in n.caution:
            assert "H10" in n.caution or "H12" in n.caution   # the canonical chart's known cases

    def test_nichod_names_inverted_locations_when_present(self, report):
        """If the chart carries atlas-proven inverted channels, the Nichod's caution says so —
        it must not silently omit the report's own top-level honesty flag."""
        n = report.nichod
        if report.info.inverted_locations:
            assert n.caution is not None
            for loc in report.info.inverted_locations:
                assert loc in n.caution

    def test_nichod_section_is_v4_and_appended_last(self):
        """The Nichod is registered as v4 and sits after every other contracted section."""
        from app.raman_saab.detailed_report import SECTION_CONTRACT
        assert SECTION_CONTRACT[-1].section_id == "nichod"
        assert SECTION_CONTRACT[-1].since == "v4"

    def test_gochara_outlook_covers_the_four_slow_movers(self, report):
        """The multi-year outlook is attached for exactly Jupiter/Saturn/Rahu/Ketu, spanning the
        same [window_back, window_forward] the rest of the report already uses."""
        assert set(report.gochara_outlook.keys()) == {"Jupiter", "Saturn", "Rahu", "Ketu"}
        for planet, segs in report.gochara_outlook.items():
            assert segs, planet
            assert segs[0].start_jd == pytest.approx(
                report.ref_jd - report.window_back * 365.2425, abs=1.0)
            assert segs[-1].end_jd == pytest.approx(
                report.ref_jd + report.window_forward * 365.2425, abs=1.0)

    def test_gochara_outlook_never_touches_a_verdict(self, report):
        """The outlook is a pure transit-geometry computation — it must not appear anywhere near
        a house verdict path (mirrors the synthesis-layer import-boundary guard)."""
        import inspect
        from app.raman_saab.primitives import transits as tr
        src = inspect.getsource(tr.gochara_timeline)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_favourable_transit_windows(self, markdown):
        """The Gochara section gains a plain, doctrine-cited table of favourable windows across
        time, answering 'which years ahead/behind are favourable' rather than only 'right now'."""
        assert "### Favourable transit windows" in markdown
        i = markdown.find("## Current transits (Gochara) with Vedha")
        j = markdown.find("### Favourable transit windows")
        assert 0 <= i < j                                 # nested under the existing section
        assert "HTJAH-II:4679" in markdown[j:j + 2000]     # transit-secondary-to-Dasha caveat
        assert "In simple terms:" in markdown[j:j + 800]
        assert "What it supports" in markdown              # plain theme column, not raw jargon

    def test_favourable_windows_name_the_planets_life_theme(self, report, markdown):
        """Each row translates the planet into what it governs (reused from 'Your Reading''s
        _PLANET_THEME), not just a bare planet name and bindus count."""
        from app.raman_saab.detailed_report import _PLANET_THEME
        j = markdown.find("### Favourable transit windows")
        table = markdown[j:j + 6000]
        seen_planets = {seg.planet for segs in report.gochara_outlook.values() for seg in segs
                        if seg.gochara_good and (seg.end_jd - seg.start_jd) >= 25}
        for planet in seen_planets:
            assert _PLANET_THEME[planet] in table

    def test_favourable_windows_show_month_names_not_bare_numbers(self, report, markdown):
        """Dates read as 'Mar 2024', not '2024-03' — the plain, reader-facing format."""
        from app.raman_saab.detailed_report import _jd_month_year
        j = markdown.find("### Favourable transit windows")
        table = markdown[j:j + 6000]
        for segs in report.gochara_outlook.values():
            for seg in segs:
                if seg.gochara_good and (seg.end_jd - seg.start_jd) >= 25:
                    assert _jd_month_year(seg.start_jd) in table
                    break

    def test_favourable_windows_drop_sub_month_noise(self, report, markdown):
        """Station-wobble slivers under ~a month are documented as dropped, not silently shown."""
        assert "dropped as sampling noise" in markdown
        j = markdown.find("### Favourable transit windows")
        table = markdown[j:j + 6000]
        from app.raman_saab.detailed_report import _jd_month_year
        for segs in report.gochara_outlook.values():
            for seg in segs:
                if seg.gochara_good and (seg.end_jd - seg.start_jd) < 25:
                    assert f"{_jd_month_year(seg.start_jd)} to {_jd_month_year(seg.end_jd)}" \
                        not in table

    def test_dasha_transit_confluences_are_real_overlaps(self, report):
        """Every confluence window is a genuine time-overlap between a bhukti period and that
        SAME planet's own favourable Gochara segment — not an invented combination."""
        assert report.dasha_transit
        outlook = report.gochara_outlook
        periods = {(tp.period.maha, tp.period.antar, tp.period.start_jd, tp.period.end_jd)
                   for tp in report.timeline.periods}
        for c in report.dasha_transit:
            assert c.role in ("MD", "AD")
            assert c.overlap_start_jd < c.overlap_end_jd
            assert c.period_start_jd <= c.overlap_start_jd < c.overlap_end_jd <= c.period_end_jd
            # the overlap genuinely sits inside one of the timeline's own bhukti periods
            assert any(c.planet in (maha, antar) and lo <= c.overlap_start_jd
                      and c.overlap_end_jd <= hi
                      for maha, antar, lo, hi in periods)
            # ...and inside one of that planet's own favourable Gochara segments
            assert any(seg.gochara_good and seg.start_jd <= c.overlap_start_jd
                      and c.overlap_end_jd <= seg.end_jd
                      for seg in outlook.get(c.planet, ()))

    def test_dasha_transit_only_tracks_the_four_slow_movers(self, report):
        """No confluence row names a planet outside Jupiter/Saturn/Rahu/Ketu — those are the
        only ones gochara_timeline computes long-range."""
        for c in report.dasha_transit:
            assert c.planet in ("Jupiter", "Saturn", "Rahu", "Ketu")

    def test_dasha_transit_never_touches_a_verdict(self):
        """Pure overlap of two already-computed timelines — no verdict path involved."""
        import inspect
        from app.raman_saab.detailed_report import _dasha_transit_confluences
        src = inspect.getsource(_dasha_transit_confluences)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_dasha_transit_confluence_section(self, markdown):
        """The new section is nested right after Gochara, before Divisional deep-reads, and
        cites the same transit-secondary-to-Dasha doctrine as the outlook above it."""
        assert "## Dasha x Transit confluence" in markdown
        i = markdown.find("## Current transits (Gochara) with Vedha")
        j = markdown.find("## Dasha x Transit confluence")
        k = markdown.find("## Divisional deep-reads")
        assert 0 <= i < j < k
        assert "HTJAH-II:4679" in markdown[j:k]
        assert "In simple terms:" in markdown[j:j + 600]

    def test_yoga_timing_never_names_a_whole_chart_pattern_yoga(self, report):
        """The Nabhasa whole-chart-distribution yogas (Asraya/Dala/Sankhya/Akriti) and the
        deferred multi-arm HPA-20 yogas have no single structurally-certain 'lord' in Raman's
        own definition (they are properties of all seven visible planets together, not caused
        by one/two/three specific ones) — they must never appear as a yoga_timing row."""
        assert report.yoga_timing
        excluded = (
            "rajju", "musala", "nala yoga", "mala (srik)", "sarpa", "veena", "damini",
            "pasa yoga", "kedara", "sula yoga", "yuga yoga", "gola", "yupa", "ishu", "sakti",
            "danda", "nava (nauka)", "kuta yoga", "chatra", "chapa", "ardha-chandra", "chakra",
            "samudra", "gada yoga", "sakata yoga (akriti)", "vihaga", "vajra", "yava yoga",
            "sringhataka", "hala yoga", "kamala yoga", "vapee", "chatussagara", "sarada",
            "brihadbija",
        )
        for t in report.yoga_timing:
            name = t.yoga_name.lower()
            assert not any(s in name for s in excluded), t.yoga_name

    def test_yoga_planets_resolves_well_beyond_the_original_three_families(self):
        """_yoga_planets covers Pancha Mahapurusha, Dhana/Raja lordship yogas, and the
        candidate-discriminated flank/benefic yogas too — not just Gajakesari/Budha-Aditya/
        9th-10th (the original, narrower Phase-A scope)."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import YOGAS, FiredYoga
        chart = cast_chart(_CANONICAL, ayanamsa="lahiri")
        resolved_ids = set()
        for rec in YOGAS:
            stub = FiredYoga(id=rec.id, name=rec.name, kind=rec.kind, effect=rec.effect,
                             source=rec.source)
            if _yoga_planets(chart, stub):
                resolved_ids.add(rec.id)
        assert len(resolved_ids) >= 20, resolved_ids
        assert "Y.RUCHAKA" in resolved_ids or "Y.HAMSA" in resolved_ids  # Pancha Mahapurusha

    def test_yoga_planets_never_returns_a_duplicate_planet(self):
        """Two different houses can share a lord (e.g. Mars rules Aries and Scorpio) — a
        multi-house lookup must dedupe, never report the same planet twice in one tuple."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import YOGAS, FiredYoga
        for birth in (_CANONICAL,):
            chart = cast_chart(birth, ayanamsa="lahiri")
            for rec in YOGAS:
                stub = FiredYoga(id=rec.id, name=rec.name, kind=rec.kind, effect=rec.effect,
                                 source=rec.source)
                pls = _yoga_planets(chart, stub)
                if pls:
                    assert len(pls) == len(set(pls)), (rec.name, pls)

    def test_yoga_timing_md_runs_are_merged_not_per_bhukti(self, report):
        """An MD-role row spans the WHOLE contiguous Mahadasha run, not a single ~2-3 year
        bhukti slice — proving _md_runs collapses the windowed bhukti list correctly."""
        from app.raman_saab.primitives.vimshottari import DAYS_PER_VEDIC_YEAR
        for t in report.yoga_timing:
            if t.role != "MD":
                continue
            span_years = (t.period_end_jd - t.period_start_jd) / DAYS_PER_VEDIC_YEAR
            # a single bhukti is a small slice of its 120-year-cycle share; an MD run for any
            # of the 9 Vimshottari lords is at least several years (Ketu's, the shortest, is 7)
            assert span_years >= 5, f"{t.yoga_name} MD span looks bhukti-sized: {span_years:.1f}y"

    def test_yoga_timing_reuses_lord_quality_not_a_new_scale(self, report):
        """'Delivery' is exactly vimshottari.lord_quality's own tag vocabulary — no new grading
        scale invented for this section."""
        for t in report.yoga_timing:
            assert t.quality.tag in ("well", "poorly", "mixed", "unknown")

    def test_yoga_timing_never_touches_a_verdict(self):
        """Pure lookup of yoga-lord membership in the MD/AD timeline — no verdict path."""
        import inspect
        from app.raman_saab.detailed_report import _yoga_dasha_confluences
        src = inspect.getsource(_yoga_dasha_confluences)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_yoga_dasha_timing_section(self, markdown):
        """The new section sits right after Yogas, before Ashtakavarga, and states the 3-family
        coverage gap plainly rather than implying full yoga coverage."""
        assert "## Yoga x Dasha timing" in markdown
        i = markdown.find("## Yogas present in this chart")
        j = markdown.find("## Yoga x Dasha timing")
        k = markdown.find("## Ashtakavarga")
        assert 0 <= i < j < k
        assert "HTJAH-I:4324" in markdown[j:k]
        assert "coverage gap" in markdown[j:k]

    def test_house_strength_covers_all_twelve_houses(self, report):
        """One row per house, verdict unchanged from the proforma rollup, ranks 1..12 with no
        gaps or repeats."""
        assert len(report.house_strength) == 12
        houses = {row.house for row in report.house_strength}
        assert houses == set(range(1, 13))
        ranks = sorted(row.bhava_bala_rank for row in report.house_strength
                      if row.bhava_bala_rank is not None)
        assert ranks == list(range(1, len(ranks) + 1))

    def test_house_strength_verdict_matches_the_proforma_unchanged(self, report):
        """The verdict column is exactly HouseProforma.rollup — a cross-check, not a new
        judgment; the house-by-house section and this table must never disagree."""
        by_house = {pf.house: pf.rollup for pf in report.proformas}
        for row in report.house_strength:
            assert row.verdict == by_house[row.house]

    def test_house_strength_sav_band_matches_the_28_average_convention(self, report):
        """The SAV band reuses the SAME >=28 threshold already shown in the Ashtakavarga
        section's own text ('Average is 28 per sign') — no new cutoff invented."""
        for row in report.house_strength:
            if row.sav_bindus is None:
                assert row.sav_band == "n/a"
            elif row.sav_bindus > 28:
                assert row.sav_band == "above average"
            elif row.sav_bindus < 28:
                assert row.sav_band == "below average"
            else:
                assert row.sav_band == "average"

    def test_house_strength_never_touches_a_verdict(self):
        """Pure ranking/lookup of already-computed values — no verdict path."""
        import inspect
        from app.raman_saab.detailed_report import _house_strength_rows
        src = inspect.getsource(_house_strength_rows)
        assert "judge_house" not in src and "_decide(" not in src

    def test_markdown_shows_house_strength_cross_check(self, markdown):
        """The new section sits right after House-by-house, before Longevity, and cites the
        Bhava-Bala-ranking-only doctrine."""
        assert "## House strength cross-check" in markdown
        i = markdown.find("## House-by-house reading")
        j = markdown.find("## House strength cross-check")
        k = markdown.find("## Longevity")
        assert 0 <= i < j < k
        assert "GBB-9:332" in markdown[j:k]
        assert "In simple terms:" in markdown[j:j + 600]

    def test_ishta_kashta_covers_every_bhukti_in_the_window(self, report):
        """One row per bhukti in the windowed timeline — same count and same (maha, antar,
        start, end) as the Life-narrative section already shows, no periods dropped or added."""
        assert len(report.ishta_kashta) == len(report.timeline.periods)
        for ik, tp in zip(report.ishta_kashta, report.timeline.periods):
            assert ik.maha == tp.period.maha and ik.antar == tp.period.antar
            assert ik.start_jd == tp.period.start_jd and ik.end_jd == tp.period.end_jd

    def test_ishta_kashta_lean_is_good_hard_or_balanced(self, report):
        """Every non-None lean is one of the three words the doctrine defines — no other
        vocabulary invented."""
        for ik in report.ishta_kashta:
            for lean in (ik.maha_lean, ik.antar_lean):
                assert lean is None or lean in ("good", "hard", "balanced")

    def test_ishta_kashta_prevails_only_states_the_md_predominates_direction(self, report):
        """GBB-10:145-152 states only the MD-predominates direction; no converse is asserted —
        `prevails` must never name the AD lord, only the MD lord, and only when its own bhukti
        isn't itself the MD (antar != maha)."""
        for ik in report.ishta_kashta:
            if ik.prevails is not None:
                assert ik.prevails == f"{ik.maha}'s character prevails"
                assert ik.antar != ik.maha

    def test_ishta_kashta_never_touches_a_verdict(self):
        """Pure lookup of natal-fixed Ishta/Kashta and Shadbala values onto the already-built
        timeline — no verdict path."""
        import inspect
        from app.raman_saab.detailed_report import _ishta_kashta_periods
        src = inspect.getsource(_ishta_kashta_periods)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_ishta_kashta_outlook(self, markdown):
        """The new section sits right after Life-narrative, before Gochara, and cites GBB-10."""
        assert "## Ishta/Kashta outlook" in markdown
        i = markdown.find("## Life-narrative")
        j = markdown.find("## Ishta/Kashta outlook")
        k = markdown.find("## Current transits (Gochara")
        assert 0 <= i < j < k
        assert "GBB-10:134" in markdown[j:k]
        assert "In simple terms:" in markdown[j:j + 600]

    def test_md_condition_covers_every_md_run_not_every_bhukti(self, report):
        """One row per contiguous Mahadasha run — fewer rows than r.timeline.periods (which is
        bhukti-level), since SYN_R4 is scoped to the MD lord only."""
        assert report.md_condition
        assert len(report.md_condition) <= len(report.timeline.periods)
        # no two consecutive rows name the same MD lord (that would mean _md_runs failed to merge)
        for a, b in zip(report.md_condition, report.md_condition[1:]):
            assert a.maha != b.maha or a.end_jd != b.start_jd

    def test_md_condition_at_maximum_requires_both_strong_and_vargottama(self, report):
        """HPA-24:51-86's stated maximum needs BOTH conditions — at_maximum must never be True
        when either is missing."""
        for c in report.md_condition:
            if c.at_maximum:
                assert c.strong is True and c.vargottama is True

    def test_md_condition_never_touches_a_verdict(self):
        """Pure lookup of natal-fixed Shadbala/vargottama/navamsa onto the already-built MD
        timeline — no verdict path."""
        import inspect
        from app.raman_saab.detailed_report import _md_lord_conditions
        src = inspect.getsource(_md_lord_conditions)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_md_condition_outlook(self, markdown):
        """The new section sits right after Ishta/Kashta outlook, before Gochara, and cites
        HPA-24 for the strong-in-both-charts maximum."""
        assert "## MD-lord condition outlook" in markdown
        i = markdown.find("## Ishta/Kashta outlook")
        j = markdown.find("## MD-lord condition outlook")
        k = markdown.find("## Current transits (Gochara")
        assert 0 <= i < j < k
        assert "HPA-24:51-86" in markdown[j:k]
        assert "In simple terms:" in markdown[j:j + 600]

    def test_verdict_authority_invariant(self, report):
        """The overlay never alters a verdict — every calibrated verdict is a Raman verdict.

        Compared positionally against a lahiri-cast chart (entries are 1:1 in order with
        judge_house significations), so duplicate signification names cannot mask a drift.
        """
        from app.raman_saab.judges import house_template as ht
        from app.raman_saab.chart.adapter import cast_chart
        chart = cast_chart(_CANONICAL, ayanamsa="lahiri")
        for house, hr in report.calibration.items():
            raman = ht.judge_house(chart, house).significations
            assert len(raman) == len(hr.entries)
            for sv, e in zip(raman, hr.entries):
                assert e.signification == sv.signification
                assert e.verdict == sv.verdict
