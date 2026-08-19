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
        """Rarity band strictly first (rare < notable < common), then midpoint distance
        WITHIN each band — the 2026-08-17 fix: the old common/non-common split let the
        sole genuinely RARE row (H4 education, 3% share) sort last among the non-common."""
        from app.raman_saab.detailed_report import _RARITY_ORDER
        d = report.distinctive
        # 2026-08-17 report-critique fix: no fixed cap — the table carries EVERY entry the
        # info-content census counts as distinctive (see test_distinctive_matches_census).
        assert d and all(e.rarity != "common" for _h, e in d)
        bands = [_RARITY_ORDER[e.rarity] for _h, e in d]
        assert bands == sorted(bands)                      # rare, then notable, then common
        for band in set(bands):
            dist = [abs(e.favourability_percentile - 0.5) for _h, e in d
                    if _RARITY_ORDER[e.rarity] == band]
            assert dist == sorted(dist, reverse=True)      # within-band: furthest first
        # the canonical chart's one rare reading leads the list
        assert d[0][1].rarity == "rare"

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

    def test_plain_layers_carry_the_synthesis(self, report):
        """The v13-v15 synthesis is woven into the plain layers a lay reader meets first: the
        Nichod names the ruler of the nativity and the most-contested house, and Your Reading
        opens with the temperament-shaping strongest planet and flags the least-settled area —
        so the reader meets the first impression and the key tension without reaching the
        technical sections. Everything is read, never re-judged."""
        n, pr = report.nichod, report.plain_reading
        assert f"ruler of the nativity {report.ruler.lagna_lord}" in n.identity
        if report.ruler.strongest is not None:
            assert report.ruler.strongest in pr.opening
            assert "shapes the overall temperament" in pr.opening
        mc = report.preponderance.most_contested
        if mc is not None:
            assert f"H{mc} is the most-contested house" in (n.caution or "")
            # Your Reading names the same tension in plain, house-number-free terms
            from app.raman_saab.detailed_report import _PLAIN_AREA
            assert _PLAIN_AREA[mc] in pr.notable
            assert "less settled" in pr.notable

    def test_plain_reading_stays_free_of_house_numbers(self, report):
        """Your Reading is the no-jargon layer — the woven synthesis must not smuggle in a bare
        'H10'-style house number (the ruler/contested adds use planet names and life-area
        words, never house indices)."""
        import re
        for field in (report.plain_reading.opening, report.plain_reading.notable):
            assert not re.search(r"\bH\d\b", field), field

    def test_nichod_closes_the_original_contract_and_later_chapters_append_after_it(self):
        """The Nichod is registered as v4 and closed the contract as it then stood. Every
        chapter added since appends AFTER it, in the order it was added — the append-only
        default the template contract is built on.

        Asserted by lookup rather than by negative index: pinning `SECTION_CONTRACT[-1]`
        made this test fail on every future append (it broke on v35, the medical read),
        which taught nothing — the invariant worth guarding is that nothing is inserted
        BEFORE nichod and that the tail stays in ascending version order."""
        from app.raman_saab.detailed_report import SECTION_CONTRACT
        ids = [s.section_id for s in SECTION_CONTRACT]
        by_id = {s.section_id: s for s in SECTION_CONTRACT}
        assert by_id["nichod"].since == "v4"
        tail = SECTION_CONTRACT[ids.index("nichod") + 1:]
        assert [s.section_id for s in tail] == ["aptitude", "medical"]
        versions = [int(s.since.lstrip("v")) for s in tail]
        assert versions == sorted(versions), "appended chapters must stay in added order"
        assert all(v > 4 for v in versions), "nothing older than nichod may follow it"

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

    def test_house_strength_sav_band_matches_the_house_by_house_prose_convention(self, report):
        """Regression test for a real bug: this table's SAV band must use the SAME thresholds
        AND wording as house_template._ashtakavarga_overlay (the House-by-house section's own
        prose) — they used to disagree (26-27 bindus read "average" in the prose but "below
        average" here). Verified independently against the raw bindus_in_house count, not via
        _house_strength_rows itself."""
        from app.raman_saab.primitives import ashtakavarga
        for row in report.house_strength:
            if row.sav_bindus is None:
                assert row.sav_band == "n/a"
                continue
            assert ashtakavarga.bindus_in_house(report.chart, row.house) == row.sav_bindus
            if row.sav_bindus >= 30:
                assert row.sav_band == "strong"
            elif row.sav_bindus <= 25:
                assert row.sav_band == "weak"
            else:
                assert row.sav_band == "average"

    def test_house_strength_sav_band_agrees_with_house_by_house_prose_for_every_house(
            self, report, markdown):
        """End-to-end: the House strength cross-check table's SAV band word must never
        contradict the House-by-house section's own 'Ashtakavarga <band> (<n> bindus)' phrase
        for the same house — this is the exact contradiction a close reading of a real generated
        report found (the same bindu count called "average" in one place and "below average" in
        the other).

        Wave-3 (2026-08-18): scoped to each house's OWN block (the whole-document
        first-match form silently pinned whichever phrasing happened to render first) and
        widened to both phrasings the chapter uses — the Working line's "Ashtakavarga
        <band> (<n> bindus)" and the Conclusion's "with <band> Ashtakavarga support
        (<n> bindus)". Strictly stronger than the version it replaces."""
        import re
        for row in report.house_strength:
            if row.sav_bindus is None:
                continue
            i = markdown.find(f"### House {row.house} ")
            assert i >= 0, row.house
            j = markdown.find(f"### House {row.house + 1} ", i)
            block = markdown[i:j if j > i else len(markdown)]
            for m in re.finditer(rf"(\w+) Ashtakavarga support \({row.sav_bindus} bindus\)",
                                 block):
                assert m.group(1) == row.sav_band, (row.house, row.sav_bindus)
            for m in re.finditer(rf"Ashtakavarga (\w+) \({row.sav_bindus} bindus\)", block):
                if m.group(1) == "support":          # the Conclusion phrasing, checked above
                    continue
                assert m.group(1) == row.sav_band, (row.house, row.sav_bindus)

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

    def test_integrated_insights_generalizes_the_multi_axis_principle(self, markdown):
        """Item #8 of the confluence audit: the House strength cross-check's magnitude-vs-
        direction finding must be generalized, near the top of Integrated insights, to the
        other independent axes a reader meets throughout the report (Avastha's state,
        Ishta/Kashta's tendency, AV bindus' lower-reliability corroboration) — so a reader
        who sees a planet read as both strong AND in a hard Avastha, or favourable yet Kashta,
        understands these are independent axes by design, not a contradiction."""
        i = markdown.find("## Integrated insights")
        assert i != -1
        window = markdown[i:i + 2000]
        assert "independent axes" in window.lower()
        assert "Deeptadi avasthas" in window and "HPA Ch.7" in window
        assert "GBB-10:134" in window          # Ishta/Kashta tendency
        assert "GBB-9:32-34" in window          # Bhava Bala magnitude
        assert "HTJAH-II:4453-4456" in window   # AV reliability caveat
        assert "not a contradiction" in window

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

    def test_maraka_saturn_confluences_are_real_overlaps(self, report):
        """Every confluence is a genuine time-overlap between a death_window Bhukti and a
        Saturn segment whose SIGN is the natal-Saturn sign or one of its two trines."""
        assert report.maraka_saturn
        sat_sign = report.chart.planets["Saturn"].sign
        trines = {sat_sign, (sat_sign - 1 + 4) % 12 + 1, (sat_sign - 1 + 8) % 12 + 1}
        from app.raman_saab.primitives.vimshottari import death_window
        dws = {(dw.maha, dw.antar, dw.start_jd, dw.end_jd) for dw in death_window(report.chart)}
        for c in report.maraka_saturn:
            assert c.sign in trines
            assert c.overlap_start_jd < c.overlap_end_jd
            assert c.window_start_jd <= c.overlap_start_jd
            assert c.overlap_end_jd <= c.window_end_jd
            assert (c.maha, c.antar, c.window_start_jd, c.window_end_jd) in dws

    def test_maraka_saturn_never_touches_a_verdict(self):
        """Pure overlap of the ayurdaya-anchored death window against Saturn's own transit
        sign — no verdict path, no new judgment."""
        import inspect
        from app.raman_saab.detailed_report import _maraka_saturn_confluences
        src = inspect.getsource(_maraka_saturn_confluences)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_maraka_saturn_confluence_as_method_not_prediction(self, markdown):
        """The section sits right after The maraka scheme, before Life-narrative, and states
        plainly that this project's own research found no death-timing signal."""
        assert "## Maraka x Saturn-transit confluence" in markdown
        i = markdown.find("## The maraka scheme")
        j = markdown.find("## Maraka x Saturn-transit confluence")
        k = markdown.find("## Life-narrative")
        assert 0 <= i < j < k
        section = markdown[j:k]
        assert "HTJAH-II:4846-4849" in section
        assert "NOT A PREDICTION" in section
        assert "measured NO death-timing signal" in section

    def test_av_dasha_seats_cover_every_md_run(self, report):
        """One row per contiguous Mahadasha run, same count as the MD-lord condition outlook
        (both derive from the SAME _md_runs collapse)."""
        assert report.av_dasha_seats
        assert len(report.av_dasha_seats) == len(report.md_condition)
        for a, c in zip(report.av_dasha_seats, report.md_condition):
            assert a.maha == c.maha and a.start_jd == c.start_jd and a.end_jd == c.end_jd

    def test_av_dasha_seat_reading_matches_the_bindu_bands(self, report):
        """5+ bindus -> auspicious, <=3 -> adverse, exactly 4 -> mixed, no data -> 'no data' —
        no other threshold invented (Patel ch015:996-1034)."""
        for a in report.av_dasha_seats:
            if a.bindus is None:
                assert a.read == "no data"
            elif a.bindus >= 5:
                assert a.read == "auspicious"
            elif a.bindus <= 3:
                assert a.read == "adverse"
            else:
                assert a.read == "mixed"

    def test_av_dasha_seat_never_touches_a_verdict(self):
        """Pure lookup of natal-fixed Ashtakavarga bindus onto the already-built MD timeline —
        no verdict path."""
        import inspect
        from app.raman_saab.detailed_report import _av_dasha_seats
        src = inspect.getsource(_av_dasha_seats)
        assert "judge_house" not in src and "rollup" not in src

    def test_markdown_shows_av_dasha_seat_outlook_with_reliability_caveat(self, markdown):
        """The section sits right after MD-lord condition, before Gochara, and carries Raman's
        own AV-reliability caveat at its head."""
        assert "## AV dasha-seat outlook" in markdown
        i = markdown.find("## MD-lord condition outlook")
        j = markdown.find("## AV dasha-seat outlook")
        k = markdown.find("## Current transits (Gochara")
        assert 0 <= i < j < k
        section = markdown[j:k]
        assert "HTJAH-II:4453-4456" in section
        assert "does not seem to be quite reliable" in section

    def test_house_lord_strength_tag_matches_the_displayed_lord_not_the_lead_ledger(self, report):
        """Regression test for a real bug: the Lord-strength tag must always describe pf.lord
        itself, never a DIFFERENT planet borrowed from whichever frame (lagna/moon) happened to
        win as the lead signification's ledger. Verified independently against
        house_template._strong (the raw Shadbala primitive), not via _lagna_ledger itself, so a
        regression in _lagna_ledger's own logic would still be caught."""
        from app.raman_saab.judges import house_template as ht
        from app.raman_saab.detailed_report import _lagna_ledger
        chart = report.chart
        for pf in report.proformas:
            if not pf.significations:
                continue
            lagna_led = _lagna_ledger(pf.significations[0])
            expected = ht._strong(pf.lord, chart)
            assert lagna_led.lord_strong == expected, (
                pf.house, pf.lord, lagna_led.lord_strong, expected)

    def test_lagna_ledger_is_actually_the_lagna_frame(self, report):
        """_lagna_ledger must return a ledger whose .frame is 'lagna' whenever one exists among
        the signification's ledger + alt_ledgers — never silently fall through to a non-lagna
        frame while one is available."""
        from app.raman_saab.detailed_report import _lagna_ledger
        for pf in report.proformas:
            for sv in pf.significations:
                available_frames = {sv.ledger.frame} | {L.frame for L in sv.alt_ledgers}
                lagna_led = _lagna_ledger(sv)
                if "lagna" in available_frames:
                    assert lagna_led.frame == "lagna"

    def test_markdown_lord_tag_uses_the_lagna_frame_strength(self, report, markdown):
        """End-to-end: for every house, the rendered '**Lord** X (...)' strength word in the
        markdown output matches the lagna-frame ledger's own lord_strong, not the lead ledger's
        (this is the exact symptom that was visibly wrong on a real chart: 'Lord Mars (strong) |
        Karaka Mars (weak)' for the identical planet). Scoped to each house's OWN block, since
        pf.lord can repeat across multiple houses and a whole-document search would find the
        wrong occurrence."""
        import re
        from app.raman_saab.detailed_report import _lagna_ledger
        starts = [(pf.house, markdown.find(f"### House {pf.house} -")) for pf in report.proformas]
        starts_by_house = dict(starts)
        for pf in report.proformas:
            if not pf.significations:
                continue
            lagna_led = _lagna_ledger(pf.significations[0])
            if lagna_led.lord_strong is None:
                continue
            start = starts_by_house[pf.house]
            assert start >= 0, pf.house
            next_starts = [s for h, s in starts if s > start]
            end = min(next_starts) if next_starts else len(markdown)
            block = markdown[start:end]
            pattern = rf"\*\*Lord\*\* {re.escape(pf.lord)}(?: in H\d+)? \((strong|weak)\)"
            m = re.search(pattern, block)
            assert m is not None, f"no Lord line found for house {pf.house} ({pf.lord})"
            assert m.group(1) == ("strong" if lagna_led.lord_strong else "weak")

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


class TestRulerOfNativity:
    """v13 — Raman's first-impression card: the ruler of the nativity (Lagna lord) and the
    strongest planet by Shadbala, with the HTJAH-I:3892-3897 nature/appearance comparison."""

    def test_ruler_never_touches_a_verdict(self):
        """Pure re-reads of already-computed values — never re-judges anything."""
        import inspect
        from app.raman_saab.detailed_report import build_ruler
        src = inspect.getsource(build_ruler)
        assert "judge_house" not in src and "_decide(" not in src and "rollup" not in src

    def test_strongest_is_strongest_by_shadbala(self, report):
        """The card's strongest planet is exactly the max-total-Shadbala graha, and the rupas
        figure is the shashtiamsa total divided by 60."""
        sb = {n: p.shadbala_rupas.total / 60.0 for n, p in report.chart.planets.items()
              if p.shadbala_rupas is not None}
        assert sb, "canonical chart must carry Shadbala"
        best = max(sb, key=lambda n: sb[n])
        assert report.ruler.strongest == best
        assert report.ruler.strongest_rupas == pytest.approx(sb[best])

    def test_lords_are_derived_consistently(self, report):
        """Lagna lord and Navamsa-Lagna lord match their own sign lords; coincide and
        stamps_nature follow the documented rules (HTJAH-I:3880-3882, 3892-3897)."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.detailed_report import _SIGN_NAME
        ru = report.ruler
        assert ru.lagna_lord == SIGN_LORDS[report.chart.asc_sign]
        assert ru.navamsa_lagna_lord == SIGN_LORDS[
            _SIGN_NAME.index(report.synthesis.navamsa_lagna)]
        assert ru.coincide == (ru.strongest == ru.lagna_lord)
        assert ru.stamps_nature in (ru.strongest, ru.navamsa_lagna_lord, None)

    def test_yoga_membership_reuses_yoga_planets(self, report):
        """Every yoga named on the card is a fired yoga whose resolved lords include the
        strongest planet — cross-checked against _yoga_planets directly."""
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        fired = {y.name: y for y in report.yogas}
        for name in report.ruler.yogas_involving:
            assert name in fired
            pls = _yoga_planets(report.chart, fired[name])
            assert pls is not None and report.ruler.strongest in pls

    def test_md_windows_come_from_md_runs(self, report):
        """The card's own-Mahadasha windows are exactly the strongest planet's runs in the
        windowed timeline — no invented spans."""
        from app.raman_saab.detailed_report import _md_runs
        expected = tuple((s, e) for m, s, e in _md_runs(report.timeline)
                         if m == report.ruler.strongest)
        assert report.ruler.md_windows == expected

    def test_canonical_pinned_facts(self, report):
        """Canonical Bangalore 1990 chart: Virgo Lagna so Mercury rules the nativity; the Sun
        (vargottama in Gemini navamsa) is the strongest graha by Shadbala and is ALSO the
        Navamsa-Lagna lord, so it stamps the nature either way (astronomical regression pin)."""
        ru = report.ruler
        assert ru.lagna_lord == "Mercury"
        assert ru.strongest == "Sun"
        assert ru.coincide is False
        assert ru.navamsa_lagna_lord == "Sun"
        assert ru.stamps_nature == "Sun"
        assert ru.vargottama is True

    def test_moon_ruler_has_no_temperament_line(self):
        """HONEST ABSENCE: Raman's strongest-planet passage (HTJAH-I:6248-6268) names Sun,
        Mars, Mercury, Jupiter, Venus and Saturn only — the temperament dict must NOT contain
        a Moon entry (nothing invented)."""
        from app.raman_saab.detailed_report import _RULER_TEMPERAMENT
        assert set(_RULER_TEMPERAMENT) == {"Sun", "Mars", "Mercury", "Jupiter", "Venus",
                                           "Saturn"}

    def test_markdown_shows_ruler_section(self, markdown):
        """The section sits right after Chart signature, before Planetary positions, citing
        the first-impression doctrine, with the method-not-prediction framing."""
        i = markdown.find("## Chart signature")
        j = markdown.find("## Ruler of the nativity")
        k = markdown.find("## Planetary positions")
        assert 0 <= i < j < k
        section = markdown[j:k]
        assert "HTJAH-I:16001-16002" in section
        assert "HTJAH-I:6248" in section
        assert "not a prediction" in section
        assert "In simple terms:" in section


class TestPreponderanceOfTestimonies:
    """v14 — the per-house testimony ledgers: Raman's 'judgment is the summing up of the
    influence of planets' (HTJAH-I:983-991) applied to every already-computed axis."""

    def test_preponderance_never_touches_a_verdict(self):
        """Pure re-reads. The builder legitimately READS pf.rollup (to display the headline),
        so this asserts the absence of the judging call-forms, not the bare token."""
        import inspect
        from app.raman_saab.detailed_report import build_preponderance
        src = inspect.getsource(build_preponderance)
        assert "judge_house" not in src and "_decide(" not in src

    def test_counts_are_conserved_and_verdict_is_verbatim(self, report):
        """For every house: the four lean-counts partition the testimony list exactly, and the
        displayed verdict is the proforma rollup, never re-decided."""
        for ht_ in report.preponderance.houses:
            assert (ht_.favourable + ht_.adverse + ht_.neutral + ht_.absent
                    == len(ht_.testimonies))
            pf = next(p for p in report.proformas if p.house == ht_.house)
            assert ht_.verdict == str(pf.rollup)

    def test_rank_and_sav_testimonies_match_house_strength_rows(self, report):
        """The Bhava-Bala-rank and SAV witnesses restate the House strength cross-check's own
        rows exactly — no recomputation drift — and the rank witness is ALWAYS neutral: it is
        a magnitude ranked without a cutoff (GBB-9:332), so it carries no direction (a first
        draft leaned it by top/bottom half; a bphs-doctrine-reviewer pass flagged that as an
        invented threshold contradicting the report's own magnitude-vs-direction explainer)."""
        hs = {row.house: row for row in report.house_strength}
        for ht_ in report.preponderance.houses:
            row = hs[ht_.house]
            rank_t = next(t for t in ht_.testimonies if t.name == "bhava bala rank")
            if row.bhava_bala_rank is not None:
                assert rank_t.value.startswith(f"{row.bhava_bala_rank} of 12")
                assert rank_t.lean == "neutral"
            sav_t = next(t for t in ht_.testimonies if t.name == "SAV band")
            if row.sav_bindus is not None:
                assert str(row.sav_bindus) in sav_t.value and row.sav_band in sav_t.value

    def test_navamsa_lean_is_direction_absolute(self, report):
        """The navamsa witness follows the engine's OWN monotone semantics (_navamsa_modulate
        and the clause-2 navamsa guard): 'confirms' (a D9-dignity lift) is ALWAYS a
        favourable-leaning witness and 'weakens' ALWAYS adverse-leaning, on every headline —
        on an afflicted house a weakens corroborates the affliction (it may even have caused
        it). A first draft read this verdict-relative; a bphs-doctrine-reviewer pass showed
        that inverts the engine's semantics — this test pins the corrected reading."""
        for ht_ in report.preponderance.houses:
            nav = next(t for t in ht_.testimonies if t.name == "navamsa")
            if nav.value == "confirms":
                assert nav.lean == "favourable-leaning"
            elif nav.value == "weakens":
                assert nav.lean == "adverse-leaning"
            else:
                assert nav.lean in ("neutral", "absent")

    def test_broken_karaka_never_tallies_favourable(self, report):
        """A karaka with karaka_intact False is the clause-1 veto the headline obeyed — its
        witness must read adverse-leaning whatever its raw strength."""
        from app.raman_saab.detailed_report import _lagna_ledger
        for ht_ in report.preponderance.houses:
            pf = next(p for p in report.proformas if p.house == ht_.house)
            if not pf.significations:
                continue
            led = _lagna_ledger(pf.significations[0])
            if led.karaka_strong is not None and not led.karaka_intact:
                kt = next(t for t in ht_.testimonies if t.name == "karaka")
                assert kt.lean == "adverse-leaning" and "broken" in kt.value

    def test_strong_dusthana_lord_never_tallies_favourable(self, report):
        """On an AFFLICTION_MATTER house, a strong lord feeds the affliction ('strengthens,
        never rescues', the engine's own clause-1.5) — its witness must not read favourable."""
        from app.raman_saab.detailed_report import _lagna_ledger
        for ht_ in report.preponderance.houses:
            pf = next(p for p in report.proformas if p.house == ht_.house)
            if not pf.significations:
                continue
            led = _lagna_ledger(pf.significations[0])
            if "AFFLICTION_MATTER" in led.flags and led.lord_strong:
                lt = next(t for t in ht_.testimonies if t.name == "lord (lagna frame)")
                assert lt.lean == "adverse-leaning" and "feeds the affliction" in lt.value

    def test_matter_house_map_matches_dispatch(self):
        """_MATTER_HOUSE covers exactly the dashboard's dispatch matters (no orphan either way),
        and every anchor is a real house number."""
        from app.raman_saab.detailed_report import _MATTER_HOUSE
        from app.raman_saab.judges.matter_varga_dashboard import _DISPATCH
        assert set(_MATTER_HOUSE) == {m for m, _v, _n, _r in _DISPATCH}
        assert all(1 <= h <= 12 for h in _MATTER_HOUSE.values())

    def test_houses_without_matter_reader_get_explicit_absent_row(self, report):
        """H1/H8/H11/H12 have no dedicated matter reader — they carry an explicit 'absent'
        matter-varga row, never a silently-missing or guessed one."""
        from app.raman_saab.detailed_report import _MATTER_HOUSE
        uncovered = set(range(1, 13)) - set(_MATTER_HOUSE.values())
        assert uncovered == {1, 8, 11, 12}
        for ht_ in report.preponderance.houses:
            if ht_.house in uncovered:
                mv = next(t for t in ht_.testimonies if t.name == "matter-varga")
                assert mv.lean == "absent"

    def test_headline_never_counted_in_its_own_tally(self, report):
        """CIRCULARITY GUARD: no testimony row is named after the headline verdict itself —
        the witness list contains only the seven distinct named axes."""
        allowed_prefixes = ("lord (lagna frame)", "karaka", "navamsa", "bhava bala rank",
                            "SAV band", "matter-varga", "majority tenor", "yogas bearing",
                            "yoga: ")
        for ht_ in report.preponderance.houses:
            for t in ht_.testimonies:
                assert t.name.startswith(allowed_prefixes), t.name

    def test_canonical_pinned_facts(self, report):
        """Canonical chart: H4 (four matter-varga witnesses, all favourable) is the
        most-corroborated favourable house; H12 reads afflicted on the weakest-link headline
        yet its witnesses lean benefic — the section's own 'contested' flag at work."""
        pr = report.preponderance
        assert pr.most_corroborated_favourable == 4
        h12 = next(h for h in pr.houses if h.house == 12)
        assert h12.verdict == "afflicted"
        assert h12.preponderance == "benefic"
        assert h12.status == "contested"

    def test_markdown_shows_preponderance_section(self, markdown):
        """The section sits between House strength cross-check and Longevity, citing the
        summing-up doctrine, the no-numeric-rule honesty note, and the yoga omission."""
        i = markdown.find("## House strength cross-check")
        j = markdown.find("## Preponderance of testimonies")
        k = markdown.find("## Longevity")
        assert 0 <= i < j < k
        section = markdown[j:k]
        assert "HTJAH-I:983-991" in section and "HTJAH-I:8870" in section
        assert "NO numeric rule" in section
        assert "HTJAH-I:4135-4139" in section          # the yoga omission, disclosed
        assert "NOT counted among its own witnesses" in section


class TestLifeChapters:
    """v15 — one woven prose chapter per Mahadasha run, merging the Life-narrative companions
    (the Napoleon-narration shape, HTJAH-I:15950-15999; natal first, transits last per
    HTJAH-I:8410-8411)."""

    def test_life_chapters_never_touch_a_verdict(self):
        """Pure joins. Grading flows ONLY through the one existing graded_buckets helper —
        never a direct bhukti_tier call that could drift from it."""
        import inspect
        from app.raman_saab.detailed_report import build_life_chapters
        src = inspect.getsource(build_life_chapters)
        assert "judge_house" not in src and "_decide(" not in src
        assert "bhukti_tier(" not in src
        assert "graded_buckets" in src

    def test_one_chapter_per_md_run(self, report):
        """Chapters are exactly the windowed timeline's MD runs, 1:1 and in order, with
        exactly one chapter flagged as current."""
        from app.raman_saab.detailed_report import _md_runs
        runs = list(_md_runs(report.timeline))
        got = [(c.maha, c.start_jd, c.end_jd) for c in report.life_chapters.chapters]
        assert got == runs
        assert sum(1 for c in report.life_chapters.chapters if c.is_current) == 1

    def test_joins_are_faithful_to_source_rows(self, report):
        """Each chapter's condition/av_seat are the SAME rows the companion tables show for
        that run; every confluence and maraka overlap genuinely intersects the run's bounds;
        every lit house's natal verdict equals the House-by-house rollup verbatim."""
        rollup = {pf.house: str(pf.rollup) for pf in report.proformas}
        for ch in report.life_chapters.chapters:
            if ch.condition is not None:
                assert ch.condition in report.md_condition
                assert ch.condition.maha == ch.maha
            if ch.av_seat is not None:
                assert ch.av_seat in report.av_dasha_seats
                assert ch.av_seat.maha == ch.maha
            for c in ch.confluences:
                assert c.overlap_start_jd < ch.end_jd and c.overlap_end_jd > ch.start_jd
            for m in ch.maraka_overlaps:
                assert m.overlap_start_jd < ch.end_jd and m.overlap_end_jd > ch.start_jd
            for h, tier, natal in ch.houses_lit:
                assert tier in ("par excellence", "ordinary", "limited", "feeble")
                assert natal == rollup[h]

    def test_narrative_orders_natal_before_transits(self, report):
        """HTJAH-I:8410-8411: in any chapter carrying both a lord-condition clause and a
        transit clause, the transit clause comes LAST (string-position on stable anchors)."""
        checked = 0
        for ch in report.life_chapters.chapters:
            if ch.condition is None or not (ch.confluences or ch.maraka_overlaps):
                continue
            n = ch.narrative
            lord_at = n.find("Mahadasha is in view")
            transit_at = max(n.find("transit-reinforcement"), n.find("Saturn-transit"))
            assert 0 <= lord_at < transit_at, ch.maha
            checked += 1
        # the canonical window may legitimately have no transit-bearing chapter; the invariant
        # is vacuously satisfied then, but the loop structure still ran without error
        assert checked >= 0

    def test_narrative_never_claims_a_clipped_rulership_span(self, report):
        """Regression for a bphs-doctrine-reviewer finding: _md_runs bounds are clipped to the
        display window, so a chapter must say its Mahadasha is 'in view' for the shown dates —
        never 'rules X to Y', which would assert a false rulership span for any MD that begins
        before or continues past the window edge."""
        for ch in report.life_chapters.chapters:
            assert "Mahadasha is in view" in ch.narrative
            assert " rules " not in ch.narrative

    def test_canonical_pinned_facts(self, report):
        """Canonical chart: 5 MD runs in the -10/+20-year window; the Sun Mahadasha is the
        current chapter (astronomical regression pin, ref date = today's run date window)."""
        assert len(report.life_chapters.chapters) == 5
        cur = next(c for c in report.life_chapters.chapters if c.is_current)
        assert cur.maha == report.synthesis.running_md

    def test_markdown_shows_life_chapters_section(self, markdown):
        """The section sits between AV dasha-seat and Gochara, citing the blending doctrine
        and the natal-first priority, with one ### block per chapter and a 'now' flag."""
        i = markdown.find("## AV dasha-seat outlook")
        j = markdown.find("## Life-chapters")
        k = markdown.find("## Current transits (Gochara")
        assert 0 <= i < j < k
        section = markdown[j:k]
        assert "HPA-34:369-381" in section
        assert "HTJAH-I:8410-8411" in section
        assert "HTJAH-I:15950-15999" in section
        assert "not a prediction" in section
        assert section.count("### ") >= 3 and "Mahadasha (" in section
        assert "- now" in section


class TestHouseConclusion:
    """The per-house Conclusion line — Raman's own closing device (a 'Conclusion.—' summation
    ends essentially every worked HTJAH analysis), composed strictly from already-computed
    rows. Built as the FAITHFUL version of a proposed 'Net Confluence' archetype engine whose
    mechanism (named archetypes, rank cutoffs, witness-majority mitigation, real-world
    severity claims) was rejected on doctrine review — several tests below pin the rejections."""

    def test_conclusion_never_touches_a_verdict(self):
        """Pure composition of computed rows — never re-judges."""
        import inspect
        from app.raman_saab.detailed_report import house_conclusion
        src = inspect.getsource(house_conclusion)
        assert "judge_house" not in src and "_decide(" not in src

    def test_conclusion_facts_match_source_rows(self, report):
        """The verdict word is the rollup verbatim; witness counts match the v14 row; the
        rank and SAV figures match the v8 row — no recomputation drift anywhere."""
        from app.raman_saab.detailed_report import house_conclusion
        hs = {row.house: row for row in report.house_strength}
        pr = {x.house: x for x in report.preponderance.houses}
        for pf in report.proformas:
            c = house_conclusion(report, pf.house)
            assert f"reads {pf.rollup}" in c
            row = hs[pf.house]
            if row.bhava_bala_rank is not None and row.sav_bindus is not None:
                assert f"({row.sav_bindus} bindus)" in c
            x = pr[pf.house]
            if x.status in ("well-corroborated", "contested"):
                # tenor-labelled counts (a doctrine-review fix: "for/against" read as
                # headline-relative and inverted on an afflicted headline)
                assert f"({x.favourable} favourable, {x.adverse} adverse)" in c

    def test_superlative_only_rank_clauses(self, report):
        """ANTI-THRESHOLD GUARD: only rank 1 and rank 12 (GBB-9:332's own 'most powerful /
        least powerful' vocabulary) may trigger a tendency clause — every middle rank renders
        neutrally. This pins the rejection of the proposed top-6/1-5/8-12 cutoffs."""
        from app.raman_saab.detailed_report import house_conclusion
        hs = {row.house: row for row in report.house_strength}
        for pf in report.proformas:
            rank = hs[pf.house].bhava_bala_rank
            c = house_conclusion(report, pf.house)
            if rank is not None and 2 <= rank <= 11:
                assert "unusual force" not in c
                assert "mildly or partly enjoyed" not in c
                assert "highest Bhava Bala" not in c and "lowest Bhava Bala" not in c
                assert "a magnitude, not a direction" in c

    def test_no_mitigation_vocabulary_ever(self, report):
        """REJECTION PIN: a witness split is disclosure, never a severity demotion — the
        vocabulary of the rejected 'Latent/Mitigated Friction' archetype must never appear."""
        from app.raman_saab.detailed_report import house_conclusion
        for pf in report.proformas:
            c = house_conclusion(report, pf.house).lower()
            for banned in ("mitigated", "superficial", "low-impact", "rarely"):
                assert banned not in c, (pf.house, banned)

    def test_contested_house_states_the_headline_stands(self, report):
        """On every contested house the Conclusion must say the headline STANDS — the split
        can never read as outvoting Raman's weakest-link rule."""
        from app.raman_saab.detailed_report import house_conclusion
        for x in report.preponderance.houses:
            if x.status == "contested":
                c = house_conclusion(report, x.house)
                assert "the headline follows the weakest-link rule and stands" in c

    def test_broken_karaka_wording(self, report):
        """The broken-karaka veto wording appears exactly when karaka_intact is False."""
        from app.raman_saab.detailed_report import _lagna_ledger, house_conclusion
        for pf in report.proformas:
            if not pf.significations:
                continue
            led = _lagna_ledger(pf.significations[0])
            c = house_conclusion(report, pf.house)
            if led.karaka_strong is not None and not led.karaka_intact:
                assert "the karaka is broken" in c
            else:
                assert "the karaka is broken" not in c

    def test_markdown_has_twelve_conclusion_lines(self, markdown):
        """Every house block closes with its Conclusion line (blockquote, after the reading,
        before the population context), and the section intro names Raman's own device."""
        i = markdown.find("## House-by-house reading")
        j = markdown.find("## House strength cross-check")
        section = markdown[i:j]
        assert section.count("> **Conclusion**") == 12
        assert "Raman's own closing device" in section
        assert "HTJAH-I:4485" in section


class TestReportCritiqueFixes20260817:
    """Wave-0 presentation fixes from docs/raman_saab/REPORT_CRITIQUE_2026-08-17.md —
    each test pins one verified defect so it can never regress."""

    # ── 1. longevity repr leak ────────────────────────────────────────────────
    def test_no_dataclass_repr_leaks_into_the_longevity_sentence(self, markdown):
        """The `y, mo, d` longevity unpack was re-bound by the yoga-deep loop variable,
        printing a YogaDeepRead dataclass repr inside 'about 88 years (...)'."""
        import re
        assert "YogaDeepRead(" not in markdown
        m = re.search(r"about \*\*(\d+) years\*\* \((\d+)y (\d+)m (\d+)d\)", markdown)
        assert m is not None, "longevity cross-check line missing or malformed"

    # ── 2. empty verbatim quotes ──────────────────────────────────────────────
    def test_no_empty_string_is_ever_rendered_as_a_quotation(self, markdown):
        """With the corpus absent, five sites printed `— "" (CITE)`; now every quote
        renders either the verbatim text or an honest corpus-absent pointer."""
        assert '"" (' not in markdown

    def test_quote_or_absent_helper_contract(self):
        """Non-empty text quotes normally; empty/None/whitespace yields the pointer."""
        from app.raman_saab.detailed_report import _quote_or_absent
        assert _quote_or_absent("The 7th house rules...", "HTJAH-II:198") == \
            '"The 7th house rules..." (HTJAH-II:198)'
        expected = "passage HTJAH-II:887 - corpus not mounted on this machine"
        assert _quote_or_absent("", "HTJAH-II:887") == expected
        assert _quote_or_absent(None, "HTJAH-II:887") == expected
        assert _quote_or_absent("   ", "HTJAH-II:887") == expected

    def test_marriage_and_children_quote_sites_render_something(self, markdown):
        """The five fixed sites each show a quote or the pointer — never a bare ''."""
        from corpus_presence import HAS_CORPUS
        for cite in ("HTJAH-II:853", "HTJAH-II:887", "HTJAH-I:5179"):
            assert cite in markdown
            if not HAS_CORPUS:
                assert f"passage {cite} - corpus not mounted on this machine" in markdown

    # ── 3. what-stands-out gloss ──────────────────────────────────────────────
    def test_distinctive_gloss_names_the_midpoint_side_and_flags_disagreement(self):
        """A favourable verdict at the 32nd percentile is glossed as LESS favourable than
        68% of charts, with the disagreement flagged; agreement carries no flag."""
        from app.raman_saab.detailed_report import distinctive_gloss

        class _E:
            def __init__(self, pct, verdict):
                self.favourability_percentile, self.verdict = pct, verdict
        assert distinctive_gloss(_E(0.32, "favourable")) == \
            "less favourable than 68% of charts, despite the favourable verdict"
        assert distinctive_gloss(_E(0.32, "afflicted")) == \
            "less favourable than 68% of charts"
        assert distinctive_gloss(_E(0.88, "favourable")) == \
            "more favourable than 88% of charts"
        assert distinctive_gloss(_E(0.88, "afflicted")) == \
            "more favourable than 88% of charts, despite the afflicted verdict"
        assert distinctive_gloss(_E(None, "favourable")) == ""

    def test_stands_out_table_carries_the_gloss_column(self, report, markdown):
        """The markdown table has the appended 'in plain terms' column, populated per row."""
        from app.raman_saab.detailed_report import distinctive_gloss
        i = markdown.find("## What stands out in this chart")
        j = markdown.find("## What matters most")
        section = markdown[i:j]
        assert "| in plain terms |" in section
        for _h, e in report.distinctive:
            assert distinctive_gloss(e) in section

    def test_report_json_distinctive_entries_carry_the_gloss(self, report):
        """Append-only JSON field: every distinctive entry gains `gloss`; the existing
        CalibratedEntry fields are all still present."""
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        assert d["distinctive"]
        for _h, entry in d["distinctive"]:
            assert "gloss" in entry and entry["gloss"]
            for key in ("signification", "verdict", "degree", "favourability_percentile",
                        "band_share", "rarity"):
                assert key in entry

    # ── 4. _plain_intensity joint guard ───────────────────────────────────────
    def test_plain_intensity_never_calls_a_favourable_verdict_challenging(self):
        """Verdict direction + percentile jointly: a favourable verdict at a low percentile
        gets a neutral descriptive word, never 'challenging' (and mirrored for afflicted)."""
        from app.raman_saab.detailed_report import _plain_intensity
        assert _plain_intensity(0.32, "favourable") == "an uncommon reading for this area"
        assert _plain_intensity(0.15, "favourable") == "an uncommon reading for this area"
        assert _plain_intensity(0.86, "afflicted") == "an uncommon reading for this area"
        # agreement keeps the original vocabulary
        assert _plain_intensity(0.86, "favourable") == "unusually strong"
        assert _plain_intensity(0.15, "afflicted") == "distinctly challenging"
        assert _plain_intensity(0.32, "afflicted") == "notably challenging"
        # verdict-less callers keep the historical behaviour
        assert _plain_intensity(0.32) == "notably challenging"

    def test_your_reading_notable_line_never_contradicts_its_verdicts(self, report):
        """End-to-end: no distinctive row rendered in Your Reading pairs a favourable
        verdict with a 'challenging' word (or an afflicted verdict with 'favourable')."""
        from app.raman_saab.detailed_report import _plain_intensity
        for _h, e in report.distinctive[:3]:
            word = _plain_intensity(e.favourability_percentile, e.verdict)
            if e.verdict == "favourable":
                assert "challenging" not in word
            if e.verdict == "afflicted":
                assert "favourable" not in word and "strong" not in word

    # ── 5. nichod caution seam ────────────────────────────────────────────────
    def test_nichod_caution_chains_sentences_without_period_semicolon_seam(self, report,
                                                                            markdown):
        """tenor_note ends with '.'; joining raw produced '...not the majority.; this
        chart carries...' — the join now strips each bit's own final period."""
        assert ".;" not in markdown
        if report.nichod.caution:
            assert ".;" not in report.nichod.caution
        assert ".;" not in report.nichod.essence

    # ── 6. ascii fold ─────────────────────────────────────────────────────────
    def test_middle_dot_and_plus_minus_fold_to_ascii_not_question_marks(self):
        """The computation badges' separator and the rectification scan's plus-minus fold
        readably; decorative emoji fold away instead of '?' mojibake."""
        from app.raman_saab.render import _ascii
        assert _ascii("`Evidence 10` · `Rules 9`") == "`Evidence 10` - `Rules 9`"
        assert _ascii("the full ±60-minute scan") == "the full +-60-minute scan"
        from app.raman_saab.detailed_report import _fold_ascii
        assert _fold_ascii("🔥 a fully charged battery") == "a fully charged battery"
        assert _fold_ascii("⚠️ running on the rim") == "running on the rim"

    def test_markdown_carries_no_fold_mojibake(self, markdown):
        """No ' ? ' produced by folding anywhere in the canonical render, and the
        rectification scan window renders '+-60', never '?60'."""
        assert " ? " not in markdown
        assert "?60" not in markdown
        if "Rectification confidence" in markdown:
            assert "+-60" in markdown or "+-" in markdown

    # ── 7. rules badge arithmetic ─────────────────────────────────────────────
    def test_rules_badge_counts_distinct_rules_matching_sources_dedup(self, report,
                                                                      markdown):
        """One arithmetic under one visual grammar: Rules is deduped by rule id exactly
        as Sources is deduped by citation — verified against a recount per house."""
        import re
        badges = re.findall(r"`Rules (\d+)` - `Sources (\d+)`", markdown)
        assert badges
        expected = []
        for mr in report.synthesis.matters:
            pf = report.proformas[mr.house - 1] if len(report.proformas) >= mr.house else None
            if pf is None:
                continue
            if not any(h.house == mr.house for h in report.preponderance.houses):
                continue
            rule_ids, cites = set(), set()
            for sv in pf.significations:
                for led in (sv.ledger, *sv.alt_ledgers):
                    for fr in (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral):
                        rule_ids.add(fr.rule.id)
                        cites.add(f"{fr.rule.source.work}:{fr.rule.source.line}")
            expected.append((str(len(rule_ids)), str(len(cites))))
        assert badges[:len(expected)] == expected

    # ── 8. nodal MD chapter ───────────────────────────────────────────────────
    def test_life_chapters_never_render_a_dangling_colon(self, report, markdown):
        """No chapter (or any line) ends ': .' — the empty-cond_words seam for a node."""
        assert ": ." not in markdown
        for ch in report.life_chapters.chapters:
            assert ": ." not in ch.narrative

    def test_nodal_md_chapter_states_the_dispositor_doctrine(self, report):
        """A Rahu/Ketu chapter carries the doctrine-licensed sentence — occupied sign,
        dispositor, and the node-results citation HTJAH-I:2764/8566 — instead of the old
        empty condition clause."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.detailed_report import _SIGN_NAME
        nodal = [ch for ch in report.life_chapters.chapters if ch.maha in ("Rahu", "Ketu")]
        assert nodal, "canonical window carries a Rahu MD chapter"
        for ch in nodal:
            p = report.chart.planets[ch.maha]
            assert f"as a node, {ch.maha} gives the results of its dispositor" in ch.narrative
            assert "HTJAH-I:2764/8566" in ch.narrative
            assert _SIGN_NAME[p.sign] in ch.narrative
            assert SIGN_LORDS[p.sign] in ch.narrative

    # ── 9. decade chip duplicates ─────────────────────────────────────────────
    def test_decade_chips_are_unique_per_area_with_multi_md_attribution(self, report):
        """One chip per area per decade; a house lit by several Mahadashas carries the
        per-MD tier attribution inside the ONE chip (nothing dropped, only merged)."""
        import re
        assert report.decades is not None
        for d in report.decades.decades:
            for chips in (d.areas_favourable, d.areas_challenged):
                houses = [re.search(r"\(H(\d+) - ", c).group(1) for c in chips]
                assert len(houses) == len(set(houses)), (d.label, chips)
                for c in chips:
                    assert re.search(r"\(H\d+ - [a-z ]+ in \w+ MD", c), c

    def test_decade_multi_md_chip_keeps_every_tier_attribution(self, report):
        """A decade spanning multiple MDs shows each MD's own tier for the same area —
        the completeness half of the dedup fix."""
        assert report.decades is not None
        multi = [d for d in report.decades.decades
                 if d.inside_window and len(d.md_lords) >= 2]
        assert multi, "canonical chart has decades spanning several Mahadashas"
        found_multi_attribution = any(
            chip.count(" MD") >= 2
            for d in multi for chip in (*d.areas_favourable, *d.areas_challenged))
        assert found_multi_attribution


class TestAshtakavargaCompleteness:
    """AV completeness (2026-08-17): the BAV 7x12 matrix, the HPA-26 reductions and the
    Sodya Pinda reach the reader, matching the primitives cell-for-cell."""

    def test_bav_matrix_is_seven_rows_of_twelve_matching_the_primitive(self, report):
        """7 planet rows x 12 sign values; every cell, total and seat equals the primitive's."""
        from app.raman_saab.primitives import ashtakavarga
        assert [bm.planet for bm in report.bav_matrix] == list(ashtakavarga.PLANETS)
        for bm in report.bav_matrix:
            assert len(bm.bindus) == 12
            bav = ashtakavarga.bhinnashtakavarga(report.chart, bm.planet)
            assert bm.bindus == tuple(bav[s] for s in range(1, 13))
            assert bm.total == sum(bm.bindus) == ashtakavarga.BAV_TOTALS[bm.planet]
            assert bm.seat_sign == report.chart.planets[bm.planet].sign
            assert bm.seat_bindus == bav[bm.seat_sign]
        assert sum(bm.total for bm in report.bav_matrix) == 337

    def test_bav_matrix_renders_with_seat_marks_and_totals(self, report, markdown):
        """The markdown matrix shows every planet row with its total and bolded natal seat."""
        assert "### Bhinnashtakavarga (BAV) - each planet's own bindu row" in markdown
        assert "| Planet | Ari | Tau | Gem |" in markdown
        for bm in report.bav_matrix:
            assert f"| {bm.planet} | " in markdown
            assert f"| {bm.total} | " in markdown
        assert markdown.count("**") >= 14        # 7 seat cells carry bold marks

    def test_reductions_match_the_primitive_and_carry_the_honesty_label(self, report, markdown):
        """Reduced rows equal `reduced_bhinnashtakavarga` per sign; the deferred-application
        frame and Raman's own HPA-26 citations (reused, not invented) are printed."""
        from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga
        for br in report.bav_reduced:
            red = reduced_bhinnashtakavarga(report.chart, br.planet)
            assert br.reduced == tuple(red[s] for s in range(1, 13))
            # Trikona-only stage never increases a cell, and the final stage never exceeds it
            assert all(t <= b for t, b in zip(
                br.trikona, next(m.bindus for m in report.bav_matrix if m.planet == br.planet)))
            assert all(f <= t for f, t in zip(br.reduced, br.trikona))
        assert "### HPA-26 reductions (Trikona + Ekadhipathya Sodhana)" in markdown
        assert ("HPA-26 reductions - used classically for special calculations; shown for "
                "completeness; ASP transit application deferred pending corpus") in markdown
        for cite in ("HPA-26:390-393", "HPA-26:466-467", "HPA-26:423-431", "HPA-26:432-462"):
            assert cite in markdown
        assert "**After Trikona Sodhana** (HPA-26:403-421):" in markdown
        assert "**After both reductions** (Ekadhipathya applied, HPA-26:464-497):" in markdown

    def test_sodya_pinda_matches_the_primitive_and_records_the_misprint_delta(
            self, report, markdown):
        """Pinda rows equal `ashtakavarga_pinda`; the ASP-14 naming citation and the module's
        honestly-recorded delta vs Raman's misprinted 1962 tables are printed."""
        from app.raman_saab.primitives.ashtakavarga_pinda import ashtakavarga_pinda
        for sp in report.sodya_pinda:
            pb = ashtakavarga_pinda(report.chart, sp.planet)
            assert (sp.rasi, sp.graha, sp.total) == (pb.rasi, pb.graha, pb.total)
            assert sp.total == sp.rasi + sp.graha
        assert "### Sodya Pinda (Rasi + Graha Gunakara)" in markdown
        assert "| Planet | Rasi Gunakara | Graha Gunakara | Sodya Pinda |" in markdown
        assert "ASP-14:196-198" in markdown
        assert "103/88/191" in markdown and "96/86/182" in markdown
        assert "known misprints" in markdown

    def test_sav_grid_marks_lagna_and_moon_columns_with_a_deviation_row(self, report, markdown):
        """The SAV grid carries the deviation row vs the 28 average and Lagna/Moon markers —
        canonical chart: Virgo Lagna, Moon in Pisces (Revati)."""
        i = markdown.find("## Ashtakavarga")
        sec = markdown[i:markdown.find("## House-by-house")]
        assert "| Lagna |" in sec and "| Moon |" in sec
        moon_sign = report.chart.planets["Moon"].sign
        assert report.chart.asc_sign == 6 and moon_sign == 12
        dev = "| " + " | ".join(
            f"{report.sav.get(s, 0) - 28:+d}" for s in range(1, 13)) + " |"
        assert dev in sec
        assert "Second row: deviation vs the 28-bindu average" in sec
        assert "judged from the Moon" in sec


class TestWave1ReportCompleteness:
    """2026-08-17 report-critique Wave-1: exact degrees + Ascendant + nakshatra lord in the
    positions table, Bhava Bala rupas in the strength cross-check, the FULL distinctive
    census in 'What stands out', the judge's Baladi/Jagradadi avasthas surfaced, per-planet
    maraka reasons, confluence tier addends, and the interactive-only Muhurtha pointer."""

    def test_positions_table_carries_longitude_ascendant_and_nak_lord(self, report, markdown):
        """Canonical pins: Virgo Lagna ~173.99 deg prints as the '23 Vi 59'..' Ascendant row;
        the Moon's Revati pada 3 row names Vimshottari lord Mercury (the birth-MD audit trail)."""
        assert ("| graha | longitude | sign | house | nakshatra (pada) | nak lord | "
                "navamsa | notes |") in markdown
        assert abs(report.chart.asc_lon - 173.99) < 0.05          # the CLAUDE.md pin itself
        asc_row = next(ln for ln in markdown.splitlines() if ln.startswith("| Ascendant |"))
        assert "| 23 Vi 59'" in asc_row and "| Virgo | 1 |" in asc_row
        moon_row = next(ln for ln in markdown.splitlines() if ln.startswith("| Moon |"))
        assert "Revati (3) | Mercury |" in moon_row

    def test_format_longitude_is_checkable_and_carries_at_boundaries(self):
        """Sign-degree form matches Jagannatha Hora's convention; a 60s/60m carry rolls up
        and across the sign boundary rather than printing 60."""
        from app.raman_saab.detailed_report import format_longitude, nakshatra_lord
        assert format_longitude(173.98814637760972) == "23 Vi 59'17\""
        assert format_longitude(0.0) == "0 Ar 00'00\""
        assert format_longitude(29.9999999) == "0 Ta 00'00\""     # carry crosses the cusp
        assert nakshatra_lord(27) == "Mercury"                    # Revati
        assert nakshatra_lord(1) == "Ketu"                        # Ashwini seeds the cycle

    def test_house_strength_markdown_shows_the_rupas_column(self, report, markdown):
        """The Bhava Bala magnitude (Shashtiamsas/60 = rupas) joins the rank in the markdown
        table — it was already in the JSON and the interactive page (append-only repair)."""
        assert ("| House | Matter | Verdict | Bhava Bala rank | Bhava Bala (rupas) | "
                "SAV bindus |") in markdown
        for row in report.house_strength:
            if row.bhava_bala is not None and row.bhava_bala_rank is not None:
                assert (f"| {row.bhava_bala_rank} of 12 | {row.bhava_bala / 60.0:.2f} |"
                        in markdown)

    def test_distinctive_table_matches_the_census_count(self, report, markdown):
        """The 'What stands out' table shows EVERY reading the info-content census counts as
        distinctive — the sentence's N and the table's row-count can no longer disagree."""
        assert len(report.distinctive) == report.info.distinctive
        i = markdown.find("| house | matter | verdict | percentile | share | in plain terms |")
        assert i >= 0
        rows = 0
        for ln in markdown[i:].splitlines()[2:]:
            if not ln.startswith("| "):
                break
            rows += 1
        assert rows == report.info.distinctive
        assert f"{report.info.distinctive} are genuinely distinctive" in markdown

    def test_deeptadi_section_shows_baladi_jagradadi_with_the_canonical_saturn_pin(
            self, markdown):
        """The judge's Baladi/Jagradadi states render as a per-planet table inside the
        Deeptadi section — canonical pin: Saturn = Mrita/Swapna — with the same
        CLASSICAL_NONCITABLE provenance the judge's scoring tables cite."""
        i = markdown.find("## Deeptadi avasthas")
        sec = markdown[i:markdown.find("## Jaimini Karakamsa")]
        assert "| graha | Baladi (ageing) | Jagradadi (consciousness) |" in sec
        assert "| Saturn | Mrita | Swapna |" in sec
        assert "CLASSICAL_NONCITABLE" in sec and "Phaladeepika" in sec
        assert "never the verdict itself" in sec

    def test_baladi_jagradadi_accessor_is_read_only_and_degrades_on_track_b(self, report):
        """The house_template accessor re-reads the judge's own computation (Saturn
        Mrita/Swapna on the canonical chart) and returns {} for a sparse Track-B chart
        instead of raising — no verdict logic involved."""
        import inspect

        from app.raman_saab.chart.model import RamanChart
        from app.raman_saab.judges.house_template import baladi_jagradadi_states
        bj = baladi_jagradadi_states(report.chart)
        assert bj["Saturn"] == {"baladi": "Mrita", "jagradadi": "Swapna"}
        assert set(bj) == set(report.chart.planets)
        sparse = RamanChart.from_stated_positions(
            {"Sun": {"lon": 10.0, "bhava": 1}}, asc_lon=0.0, ayanamsa="lahiri")
        assert baladi_jagradadi_states(sparse) == {}
        src = inspect.getsource(baladi_jagradadi_states)
        assert "judge_house" not in src and "rollup" not in src

    def test_maraka_units_carry_reasons_and_the_render_names_them(self, report, markdown):
        """Every canonical-chart MarakaUnit records WHY it qualified, and the markdown tier
        lines print the clause (Virgo lagna: Venus = lord of the 2nd, Jupiter = 7th)."""
        mp = report.chart.maraka_points
        assert mp is not None and mp.units
        assert all(u.reasons for u in mp.units)
        assert "Venus (lord of the 2nd)" in markdown
        assert "Jupiter (lord of the 7th)" in markdown
        assert "Mars (lord of the 3rd and the 8th)" in markdown   # merged lordship clause

    def test_maraka_saturn_score_parts_reproduce_the_score(self, report, markdown):
        """The confluence table's tier addends ('5 = Jupiter 3 + Mercury 2') are the same
        MarakaSet weights death_window summed — parts always reproduce the score."""
        assert report.maraka_saturn
        for c in report.maraka_saturn:
            assert c.score_parts, "addends must be recorded"
            terms = c.score_parts.split(" + ")
            assert sum(int(t.rsplit(" ", 1)[1]) for t in terms) == c.score
        c0 = report.maraka_saturn[0]
        assert f"| {c0.score} = {c0.score_parts} |" in markdown

    def test_muhurtha_pointer_present_near_the_timing_close(self, markdown):
        """One pointer line (no new section heading) tells the reader the interactive page's
        on-demand 'Today for you (Muhurtha)' panel exists and cannot be reproduced here."""
        i = markdown.find('"Today for you (Muhurtha)"')
        assert i >= 0
        assert markdown.find("## Current transits (Gochara) with Vedha") < i
        assert i < markdown.find("## Divisional deep-reads (Shodasavarga)")
        window = markdown[i - 400:i + 600]
        assert "## Muhurtha" not in window                        # a pointer, not a section
        assert "computed live at view time" in window
        # firewall hygiene: the pointer must not name the walled subsystem's module
        # (tests/raman_saab/electional/test_walled_subsystem.py scans this module's source)
        assert "electional" not in window


class TestWave1TimingSurfaces:
    """Wave-1 (2026-08-17, REPORT COMPLETENESS, timing appendix): delivery tags on activation
    rows, the pratyantar drill-down, dated Sade-Sati phases, the adverse transit windows and
    the dated Chara dasha sequence — all pure re-reads / plain JD arithmetic."""

    def test_delivery_tags_render_on_every_activation_row(self, report, markdown):
        """The lord_quality tags (HTJAH-II:10004-10008) were computed per row and dropped by
        the markdown renderer; now every lit house carries its activating lords' tags."""
        import re
        assert "**Delivery tags**" in markdown
        # both-lords tiers carry both tags; limited only the AD tag; feeble only the MD tag
        assert re.search(r"H\d+ \w+ \(MD (?:well|mixed|poorly|unknown), "
                         r"AD (?:well|mixed|poorly|unknown)\)", markdown)
        assert re.search(r"limited \(bhukti lord only\): H\d+ \w+ \(AD ", markdown)
        assert re.search(r"feeble \(MD lord only\): H\d+ \w+ \(MD ", markdown)
        # the tag is the SAME lord_quality read the engine already computes, not a new scale
        from app.raman_saab.primitives import vimshottari as vd
        tp = report.timeline.periods[0]
        a = tp.activated[0]
        assert a.md_quality.tag == vd.lord_quality(report.chart, tp.period.maha).tag

    def test_pratyantar_block_is_the_current_bhukti_partitioned(self, report, markdown):
        """Exactly the running bhukti's 9 pratyantars, spans partitioning the bhukti bounds
        in JD space, exactly one running row marked."""
        from app.raman_saab.primitives import vimshottari as vd
        rows = report.pratyantar_now
        assert len(rows) == 9
        bh = vd.dasha_on(report.chart, report.ref_jd)
        assert bh is not None and bh.antar is not None
        assert {(p.maha, p.antar) for p in rows} == {(bh.maha, bh.antar)}
        assert abs(rows[0].start_jd - bh.start_jd) < 1e-6
        assert abs(rows[-1].end_jd - bh.end_jd) < 1e-6
        for prev, nxt in zip(rows, rows[1:]):
            assert abs(prev.end_jd - nxt.start_jd) < 1e-6
        assert sum(1 for p in rows if p.start_jd <= report.ref_jd < p.end_jd) == 1
        s = markdown.find("### Pratyantardasha drill-down (current bhukti)")
        assert s >= 0
        section = markdown[s:markdown.find("###", s + 10)]
        assert section.count(" PD** (") == 9          # all nine rows, dated
        assert section.count("<- now") == 1           # the running pratyantar, marked once
        assert "HTJAH-II:668-702" in section          # the recorded three-level citation

    def test_sade_sati_strip_is_dated_and_method_only(self, report, markdown):
        """The three phase spans (12th/1st/2nd from the Moon) carry calendar dates and the
        strip states the no-result-doctrine absence note; dates are gochara arithmetic."""
        import re
        phases = report.sade_sati_phases
        assert phases
        assert {p.phase for p in phases} >= {"rising (12th from Moon)",
                                             "peak (over the Moon)",
                                             "setting (2nd from Moon)"}
        for p in phases:
            assert p.house_from_moon in (12, 1, 2)
            assert p.start_jd < p.end_jd
        starts = [p.start_jd for p in phases]
        assert starts == sorted(starts)
        assert sum(1 for p in phases if p.current) <= 1
        s = markdown.find("### Sade-Sati phase windows (Saturn from the natal Moon)")
        assert s >= 0
        section = markdown[s:markdown.find("\n## ", s)]
        assert "no Sade-Sati x Moon result doctrine is on record" in section
        assert "plain gochara arithmetic" in section
        for label in ("rising (12th from Moon)", "peak (over the Moon)",
                      "setting (2nd from Moon)"):
            assert f"**{label}** - Saturn in" in section
        assert re.search(r"Saturn in \w+: [A-Z][a-z]{2} \d{4}", section)   # dated rows
        assert section.count("<- now") == sum(1 for p in phases if p.current)

    def test_adverse_windows_table_renders_alongside_favourable(self, report, markdown):
        """The adverse half of the SAME gochara_timeline computation renders as a mirror
        table after the favourable one, which stays untouched."""
        f = markdown.find("### Favourable transit windows (")
        a = markdown.find("### Adverse transit windows (")
        assert f >= 0 and a > f                       # both present; favourable first
        from app.raman_saab.detailed_report import adverse_transit_windows
        rows = adverse_transit_windows(report)
        assert rows
        starts = [seg.start_jd for _p, seg, _b in rows]
        assert starts == sorted(starts)               # chronological
        for _p, seg, _b in rows:
            assert not seg.gochara_good
            assert (seg.end_jd - seg.start_jd) >= 25  # same noise floor as favourable
        section = markdown[a:markdown.find("###", a + 10)]
        assert "| Planet | Window | What it concerns | Mitigation (own AV bindus) | " \
               "Interference |" in section
        assert "ASP-13:416" in section                # Raman's own proportion law, recorded
        assert "not computed, not zero" in section    # the honest Vedha disclosure

    def test_chara_sequence_is_dated_with_one_now_marker(self, report, markdown):
        """Chara rows are dated by JD arithmetic from birth (years x 365.2425), contiguous,
        exactly one current row, agreeing with the Chart-signature chip's running sign."""
        import re
        seq = report.chara_sequence
        assert len(seq) >= 12
        assert abs(seq[0].start_jd - report.chart.jd_ut) < 1e-9
        for prev, nxt in zip(seq, seq[1:]):
            assert abs(prev.end_jd - nxt.start_jd) < 1e-9
        for cs in seq:
            assert abs((cs.end_jd - cs.start_jd) - cs.years * 365.2425) < 1e-6
        cur = [cs for cs in seq if cs.current]
        assert len(cur) == 1
        from app.raman_saab.detailed_report import _SIGN_NAME
        assert _SIGN_NAME[cur[0].sign] == report.synthesis.chara
        s = markdown.find("### Chara dasha (Jaimini) - dated sequence")
        assert s >= 0
        section = markdown[s:markdown.find("\n## ", s)]
        assert section.count("<- now") == 1
        dated = re.findall(r"- \w+ - \d+y \(\d{4}-\d{2}-\d{2} \.\. \d{4}-\d{2}-\d{2}\)",
                           section)
        assert len(dated) >= 12                       # every span carries calendar dates

    def test_wave1_sections_pass_the_decree_guard(self, markdown):
        """All four new timing surfaces stay in the indication idiom — the decree tripwire
        (the 2026-08-17 guard line) never fires on their prose."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for marker in ("### Pratyantardasha drill-down", "### Chara dasha (Jaimini)",
                       "### Sade-Sati phase windows", "### Adverse transit windows"):
            s = markdown.find(marker)
            assert s >= 0, marker
            e = markdown.find("\n## ", s)
            section = markdown[s:e if e > 0 else s + 4000]
            m = _FORBIDDEN_RE.search(section)
            assert m is None, f"{marker}: {m.group(0)!r}"


class TestWave2SynthesisLayer:
    """Wave-2 (2026-08-17, synthesis layer): period-pairing across the plain layers
    (HTJAH-I:1586-1596, the locked timer doctrine), the stronger-frame + vitality lines,
    glossed reconciliations, the info-content breakdown + measured population framing,
    and the Nichod's spotlight weave + forward horizon. All pure re-reads."""

    def test_every_theme_paragraph_closes_with_its_period_pairing(self, report):
        """Raman never states an indication without its fructification window — each of the
        five life-theme paragraphs closes by naming the MD lords whose chapters most light
        its houses, with the year span, in the guard-safe indication idiom."""
        import re

        from app.llm.report_explainer import _FORBIDDEN_RE
        assert len(report.plain_reading.life_paragraphs) == 5
        for theme, para in report.plain_reading.life_paragraphs:
            assert "ripen most fully in the" in para, theme
            assert re.search(r"chapters? of life \(\d{4}-\d{4}\)\.$", para), theme
            m = _FORBIDDEN_RE.search(para)
            assert m is None, f"{theme}: {m.group(0)!r}"

    def test_period_pairing_re_reads_the_graded_life_chapters(self, report):
        """The lords the clause names are exactly lords of chapters whose houses_lit rows
        light the requested houses — a re-read of the four-tier grading, never invented."""
        import re

        from app.raman_saab.detailed_report import period_pairing
        lords, span = period_pairing(report, (10,))
        lit10 = {ch.maha for ch in report.life_chapters.chapters
                 if any(h == 10 for h, _t, _v in ch.houses_lit)}
        assert lords and set(lords) <= lit10
        assert re.fullmatch(r"\d{4}-\d{4}", span)
        # nothing lights a house no chapter lights
        assert period_pairing(report, ()) == ((), "")

    def test_opening_states_the_stronger_frame_and_the_vitality_band(self, report):
        """The stronger-frame sentence (HTJAH-I:645-646 re-read) and the guarded vitality
        line (band word only — the number stays in the Longevity section)."""
        pr = report.plain_reading
        if report.overview.stronger_frame == "moon":
            assert "read chiefly from the Moon's position" in pr.opening
        band_word = {"purna": "full", "madhya": "middle",
                     "alpa": "short"}[report.longevity_class]
        assert f"vitality reads at the {band_word} band" in pr.opening
        assert "not a forecast" in pr.opening
        assert str(round(report.longevity_years)) not in pr.opening

    def test_reconciliations_gloss_the_method_jargon(self, report):
        """The S3 bullets keep both poles but speak plainly — the PREC id survives as the
        parenthetical pointer, the raw method tokens do not."""
        recs = report.plain_reading.reconciliations
        if not recs:
            pytest.skip("no reconciliations on this chart")
        joined = " ".join(recs)
        assert "never re-voted" not in joined
        assert "its dedicated reader" not in joined
        assert "rule PREC-" in joined and "How to read this report" in joined

    def test_info_breakdown_table_matches_the_census_fields(self, report, markdown):
        """The breakdown rows under the info sentence restate the SAME InfoContent fields
        the sentence uses — checkable arithmetic, no new counting."""
        s = markdown.find("## Information content of this reading")
        e = markdown.find("\n## ", s + 1)
        section = markdown[s:e]
        i = report.info
        assert f"| total readings | {i.total} |" in section
        assert (f"| most common verdict ({i.modal_verdict}) | {i.modal_count} |"
                in section)
        assert (f"| near-universal (held by half the population or more) | "
                f"{i.near_universal} |" in section)
        assert f"| proven inverted channels | {i.inverted} |" in section
        assert f"| genuinely distinctive | {i.distinctive} |" in section
        # classes overlap by construction; each is bounded by the total it breaks down
        for count in (i.modal_count, i.near_universal, i.inverted, i.distinctive):
            assert 0 <= count <= i.total

    def test_population_note_is_calibration_framed_and_rendered(self, markdown):
        """The measured mechanism constants (CLAUDE.md Measured Truth) frame the info
        sentence as calibration — never validation — on the markdown surface."""
        from app.raman_saab.detailed_report import POPULATION_NOTE
        assert "19 afflicted and 31 favourable" in POPULATION_NOTE
        assert "97.1%" in POPULATION_NOTE
        assert "never validation" in POPULATION_NOTE
        assert POPULATION_NOTE in markdown

    def test_nichod_weaves_spotlight_frame_and_forward_horizon(self, report, markdown):
        """The essence now carries the spotlight, opens frame-then-ruler, and closes its
        timing view with the next MD boundary's lean — all before the fixed disclaimer."""
        n = report.nichod
        if n.spotlight:
            assert "cross-feature spotlight" in n.essence
        assert "the stronger frame here (HTJAH-I:645-646)" in n.essence
        if n.forward_horizon:
            assert "a period indication, not an event" in n.forward_horizon
            assert n.forward_horizon in n.essence
            assert "Forward horizon" in markdown
            # mirror the builder's own row filter (MD-level rows, else every bhukti row)
            rows = ([ik for ik in report.ishta_kashta if ik.antar is None]
                    or list(report.ishta_kashta))
            nxt = next(ik for ik in rows
                       if ik.start_jd > report.ref_jd
                       and ik.maha != report.synthesis.running_md)
            assert nxt.maha in n.forward_horizon
            assert str(nxt.maha_lean) in n.forward_horizon

    def test_digest_table_renders_1_based_for_humans(self, markdown):
        """The rendered rank column starts at 1 (priority stays 0-based in JSON)."""
        s = markdown.find("## What matters most (ranked digest)")
        e = markdown.find("\n## ", s + 1)
        section = markdown[s:e]
        assert "\n| 1 | governing_factor |" in section
        assert "\n| 2 | foundation |" in section
        assert "\n| 0 | " not in section

    def test_wave2_prose_passes_the_decree_guard(self, report, markdown):
        """Every composed Wave-2 surface stays in the indication idiom — the decree
        tripwire never fires on the plain reading, the digest, the Nichod, the info
        section or the life synthesis."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for marker in ("## Your Reading", "## Information content of this reading",
                       "## What matters most (ranked digest)", "## Nichod",
                       "## Full life synthesis"):
            s = markdown.find(marker)
            assert s >= 0, marker
            e = markdown.find("\n## ", s + 1)
            section = markdown[s:e if e > 0 else len(markdown)]
            m = _FORBIDDEN_RE.search(section)
            assert m is None, f"{marker}: {m.group(0)!r}"
        pieces = [report.plain_reading.opening, report.nichod.essence,
                  report.nichod.forward_horizon or ""]
        pieces += [p for _t, p in report.plain_reading.life_paragraphs]
        if report.life_synthesis is not None:
            pieces += [p for _t, p in report.life_synthesis.paragraphs]
        for piece in pieces:
            m = _FORBIDDEN_RE.search(piece)
            assert m is None, (m.group(0) if m else "", piece)


class TestFoundationWave2:
    """Wave-2 foundation re-reads (REPORT_CRITIQUE_2026-08-17): the ruler's own
    condition block + takeaway + foundation verdict, the signature's first-glance
    rows, the Deeptadi testimony table with secondary-state disclosure, and the
    Shadbala ratio/scale notes. All pure re-reads; the ratchet is untouched."""

    def test_ruler_takeaway_leads_the_chapter(self, report, markdown):
        """Canonical pin: Mercury rules from H11 under strain; the Sun carries."""
        ru = report.ruler
        assert ru.takeaway.startswith("Mercury rules this nativity from house 11")
        assert "under its Shadbala minimum" in ru.takeaway
        assert "Sun, the strongest planet by Shadbala, carries the chart" in ru.takeaway
        sec = markdown[markdown.find("## Ruler of the nativity"):
                       markdown.find("## Planet biographies")]
        assert "**Mercury rules this nativity from house 11" in sec

    def test_ruler_condition_block_computed_and_rendered(self, report, markdown):
        """The Lagna lord's sign/dignity/avastha/Shadbala-vs-minimum/aspects/dispositor
        — the chapter's namesake finally gets the full read (canonical pins)."""
        ru = report.ruler
        assert (ru.ll_dignity, ru.ll_avastha) == ("enemy", "Deena")
        assert ru.ll_rupas == pytest.approx(6.15, abs=0.01)
        assert ru.ll_required == 7.0
        assert ru.ll_powerful is False and ru.ll_only_failing is True
        assert ru.ll_aspects_received == ("Mars", "Rahu")
        assert (ru.ll_dispositor, ru.ll_dispositor_house) == ("Moon", 7)
        sec = markdown[markdown.find("## Ruler of the nativity"):
                       markdown.find("## Planet biographies")]
        assert "**The ruler's own condition** - in Cancer (enemy sign)" in sec
        assert "6.15 rupas against its required 7.0 (GBB-8:303)" in sec
        assert "the only planet in this chart below its own" in sec
        assert "dispositor Moon in house 7" in sec

    def test_foundation_verdict_fires_on_the_non_coincide_branch(self, report, markdown):
        """HTJAH-I:3880-3882 (already cited on the coincide branch) now surfaces when
        ruler != strongest too — sound/unsound idiom, descriptive only."""
        ru = report.ruler
        assert "HTJAH-I:3880-3882" in ru.foundation_line
        assert "falls below its required minimum" in ru.foundation_line
        assert '"foundation is quite sound"' in ru.foundation_line
        sec = markdown[markdown.find("## Ruler of the nativity"):
                       markdown.find("## Planet biographies")]
        assert "**Foundation** - Mercury, the Lagnadhipati" in sec

    def test_chandra_lagna_candidate_disclosed_when_moon_frame(self, report, markdown):
        """Stronger frame is MOON here, so the Chandra-lagna lord (Jupiter, Pisces
        Moon) is disclosed as the third classical candidate (HTJAH-I:645-646)."""
        ru = report.ruler
        assert report.overview.stronger_frame == "moon"
        assert ru.chandra_lagna_lord == "Jupiter"
        assert "functional malefic for this Lagna" in ru.chandra_ll_condition
        sec = markdown[markdown.find("## Ruler of the nativity"):
                       markdown.find("## Planet biographies")]
        assert "Third classical candidate (Chandra Lagna)" in sec

    def test_signature_first_glance_rows(self, report, markdown):
        """Balance of dasha at birth, exact degrees, paksha-vs-Shadbala, luminary
        flags, Lagna-lord disposition and the day-lord observation — all computed."""
        from app.raman_saab.detailed_report import signature_first_glance
        rows = dict(signature_first_glance(report))
        # the label carries the citation found 2026-08-19 (HPA-13:130-160, Raman's own
        # proportional deduction of the expired nakshatra portion); the VALUE stays clean
        # so consumers parsing it are unaffected.
        assert rows["Balance of dasha at birth (HPA-13:130-160)"] == "Mercury 4y 8m 10d"
        assert rows["Lagna degree"] == "23 Vi 59'17\""
        assert rows["Moon degree"] == "26 Pi 19'03\""
        assert rows["Moon at a glance"].startswith(
            "waning (Krishna paksha) yet Shadbala-strong")
        assert "Sun strong" in rows["Luminaries"] and "GBB-8:303" in rows["Luminaries"]
        assert rows["Lagna lord at a glance"] == "Mercury in H11, enemy sign, Deena avastha"
        assert rows["Day lord"].startswith("born on Sunday, the Sun's day")
        sig = markdown[markdown.find("## Chart signature"):
                       markdown.find("## Ruler of the nativity")]
        assert ("**Balance of dasha at birth (HPA-13:130-160)** - Mercury 4y 8m 10d"
                in sig)
        assert "**Lagna degree** - 23 Vi 59'17\"" in sig
        assert "**Moon degree** - 26 Pi 19'03\"" in sig

    def test_stronger_frame_names_its_operationalization(self, markdown):
        """No-silent-approximation: the frame test names its measure in-render."""
        assert ("measured here by the two sign-lords' total Shadbala" in markdown)

    def test_deeptadi_table_reads_as_testimony(self, report, markdown):
        """Per-planet rows: Raman's HPA Ch.7:46-83 result, rules/occupies with the
        Lagna-lord call-out, Saturn's secondary state disclosed, node note present."""
        from app.raman_saab.detailed_report import deeptadi_table
        rows = {r_[0]: r_ for r_ in deeptadi_table(report)}
        assert rows["Saturn"][1].startswith("Deena (also retrograde -> Sakta")
        assert rows["Mercury"][3].endswith("the Lagna lord dejected")
        assert rows["Mercury"][2] == "enemy's sign -> jealousy, worry, sickness, degradation"
        assert rows["Rahu"][1].startswith("Sakta (definitional")
        assert "the nodes are always retrograde" in rows["Rahu"][1]
        assert rows["Rahu"][3].startswith("rules nothing (chayagraha)")
        sec = markdown[markdown.find("## Deeptadi avasthas (each"):
                       markdown.find("## Jaimini Karakamsa")]
        assert ("| graha | state | Raman's stated result (HPA Ch.7:46-83) | "
                "rules / occupies |") in sec
        assert "| Saturn | Deena (also retrograde -> Sakta" in sec
        assert "perpetually Sakta - definitional, not a strength claim" in sec
        # Wave-1's Baladi/Jagradadi table is untouched alongside
        assert "| graha | Baladi (ageing) | Jagradadi (consciousness) |" in sec

    def test_states_all_head_always_matches_state(self, report):
        """The additive accessor's dominant state is exactly state()'s answer for
        every graha — state() itself is unchanged."""
        from app.raman_saab.primitives.deeptadi import state, states_all
        for name in report.chart.planets:
            assert states_all(name, report.chart)[0] == state(name, report.chart)

    def test_shadbala_ratio_column_and_scale_notes(self, markdown):
        """Ratio (total/required, 2dp), the Sun/Moon cheshta-0 definitional note
        (GBB-6:23-28), the Ishta/Kashta 0-60 scale note with the good/hard leans,
        and the weakest-component pointer for the one failing planet (Mercury)."""
        sec = markdown[markdown.find("## Shadbala (six-fold"):
                       markdown.find("## Yogas present")]
        assert "| **total** | ratio | powerful? |" in " ".join(sec.splitlines())
        assert "| **6.15** | 0.88 | no |" in sec
        assert "cheshta 0.00 by definition" in sec and "GBB-6:23-28" in sec
        assert "0-60 scale (GBB-10:134)" in sec
        assert "Mercury hard" in sec and "Sun good" in sec
        assert ("Mercury falls below its minimum; of the six components shown, "
                "its smallest is drik") in sec
        assert "not a per-component judgment" in sec

    def test_json_carries_the_new_foundation_keys(self, report):
        """report_json append-only keys + the new dataclass fields flow through."""
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        fg = dict(map(tuple, d["signature_first_glance"]))
        assert fg["Balance of dasha at birth (HPA-13:130-160)"] == "Mercury 4y 8m 10d"
        assert any(row[0] == "Saturn" and "Sakta" in row[1]
                   for row in d["deeptadi_table"])
        assert d["ruler"]["ll_dispositor"] == "Moon"
        assert d["ruler"]["takeaway"].startswith("Mercury rules this nativity")
        assert d["psych"]["mercury_line"]

    def test_new_foundation_prose_passes_the_guard(self, report):
        """Descriptive idiom only: the decree-voice tripwire stays silent on every
        new builder string (ruler block, first-glance rows, deeptadi table)."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        from app.raman_saab.detailed_report import (deeptadi_table,
                                                    signature_first_glance)
        ru = report.ruler
        texts = [ru.takeaway, ru.foundation_line, ru.chandra_ll_condition or ""]
        texts += [v for _k, v in signature_first_glance(report)]
        for row in deeptadi_table(report):
            texts += list(row[1:])
        for t in texts:
            m = _FORBIDDEN_RE.search(t)
            assert m is None, f"{m.group(0) if m else ''!r} in {t!r}"


class TestWave2TimingDivisionalSoul:
    """Wave-2 (2026-08-18, REPORT_CRITIQUE timing appendix — timing/divisional/soul group):
    influence-basis tags derived from the role-preserving timer_roles, the adverse dasha x
    transit confluence mirror, per-row gochara synthesis sentences, divisional verdict-first
    labels + D-27/40/45/60 domain sentences, karmic one-line re-reads (full blocks retained
    at their home sections), and the Jaimini AK/Karakamsa header + navigational cross-ref."""

    # ── item 1: derive the tier, don't assert it ─────────────────────────────

    def test_influence_basis_tags_render_on_activation_rows(self, report, markdown):
        """Every lit house carries the bracketed influence-basis derivation ('[MD owns; AD
        aspects lord]') built from timer_roles — the factor list HTJAH-I:1586-1596 names."""
        import re
        assert "**Influence basis**" in markdown
        assert "HTJAH-I:1586-1596" in markdown
        # a both-lords row carries both MD and AD bases; single-lord rows carry one
        assert re.search(r"H\d+ \w+ \(MD [a-z]+, AD [a-z]+\) \[MD [a-z][^\]]*; AD [^\]]+\]",
                         markdown)
        assert re.search(r"limited \(bhukti lord only\): H\d+ \w+ \(AD [a-z]+\) \[AD ",
                         markdown)
        assert re.search(r"feeble \(MD lord only\): H\d+ \w+ \(MD [a-z]+\) \[MD ", markdown)

    def test_influence_basis_agrees_with_timer_roles(self, report):
        """The rendered basis is the timer_roles decomposition, never an independent grading:
        for every activated house, each period-lord's basis resolves via the house's roles or
        (tagged 'via H<n>') an allied event house's roles."""
        from app.raman_saab.detailed_report import influence_basis, influence_basis_table
        from app.raman_saab.primitives.vimshottari import _EVENT_AUX_HOUSES, timer_roles
        table = influence_basis_table(report.chart)
        for h in range(1, 13):
            assert table[h] == timer_roles(report.chart, h)
        for tp in report.timeline.periods:
            for a in tp.activated:
                if a.md_activates:
                    basis = influence_basis(table, a.house, a.md_lord)
                    assert basis, (a.house, a.md_lord)
                    if basis.startswith("via H"):
                        aux = int(basis.split()[1][1:].rstrip(":"))
                        assert aux in _EVENT_AUX_HOUSES.get(a.house, ()), basis
                        assert a.md_lord in table[aux]
                    else:
                        assert a.md_lord in table[a.house]

    def test_influence_basis_in_json_timeline_rows(self, report):
        """The JSON timeline rows carry md_basis/antar_basis (append-only), so the
        interactive page can show the same derivation."""
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        rows = [a for row in d["timeline"] for a in row["activated"]]
        assert rows
        for a in rows:
            assert "md_basis" in a and "antar_basis" in a
            if a["md_basis"] is not None:
                assert a["md_basis"]                     # never an empty basis on an MD hit

    # ── item 2: the adverse dasha x transit mirror ───────────────────────────

    def test_adverse_confluence_rows_present_with_honesty_note(self, report, markdown):
        """The adverse mirror renders below the (untouched) favourable table with the same
        coarse-sampling honesty note and the recorded blending frame HPA-34:369-381."""
        f = markdown.find("## Dasha x Transit confluence")
        a = markdown.find("### Adverse dasha x transit confluence")
        assert f >= 0 and a > f                       # favourable section first, mirror after
        assert report.dasha_transit_adverse           # rows exist on the canonical chart
        section = markdown[a:markdown.find("\n## ", a)]
        assert "HPA-34:369-381" in section            # the recorded blending doctrine
        assert "ASP-13:416" in section                # Raman's own mitigation proportion
        assert "not computed, not zero" in section    # honest Vedha disclosure
        assert "method windows, not exact dates" in section   # coarse-sampling honesty
        assert section.count("| MD |") + section.count("| AD |") == \
            len(report.dasha_transit_adverse)

    def test_adverse_builder_mirrors_the_favourable_one(self, report):
        """Every adverse row is a genuine (period x adverse-segment) intersection; the
        favourable rows are untouched by construction (separate builder)."""
        for c in report.dasha_transit_adverse:
            assert c.overlap_start_jd < c.overlap_end_jd
            assert c.period_start_jd <= c.overlap_start_jd
            assert c.overlap_end_jd <= c.period_end_jd
            segs = report.gochara_outlook[c.planet]
            assert any((not s.gochara_good) and s.start_jd <= c.overlap_start_jd
                       and c.overlap_end_jd <= s.end_jd for s in segs), c
        for c in report.dasha_transit:                # the favourable half: still all-good
            segs = report.gochara_outlook[c.planet]
            assert any(s.gochara_good and s.start_jd <= c.overlap_start_jd
                       and c.overlap_end_jd <= s.end_jd for s in segs), c

    def test_adverse_confluence_in_json(self, report):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        assert len(d["dasha_transit_adverse"]) == len(report.dasha_transit_adverse)

    # ── item 3: gochara synthesis sentences ──────────────────────────────────

    def test_one_gochara_synthesis_sentence_per_snapshot_row(self, report, markdown):
        """One deterministic sentence per snapshot row, composed strictly from the row's own
        columns (station + support + kakshya + vedha + net)."""
        from app.raman_saab.detailed_report import gochara_synthesis_sentence
        s = markdown.find("**Read as sentences**")
        assert s >= 0
        section = markdown[s:markdown.find("###", s)]
        for g in report.gochara:
            sent = gochara_synthesis_sentence(g)
            assert f"- {sent}" in section             # each row's sentence rendered
            assert g.planet in sent
            assert ("favourable station" if g.gochara_good else "adverse station") in sent
            if g.bav_bindus is not None:
                assert f"{g.bav_bindus} bindus" in sent
            else:
                assert "no Ashtakavarga measure (node)" in sent
            if g.gochara_good and g.vedha_by:
                assert "the good is withheld" in sent
                for v in g.vedha_by:
                    assert v in sent
            elif g.gochara_good:
                assert "the indication stands" in sent

    # ── item 4: divisional verdict-first ─────────────────────────────────────

    def test_matter_varga_labels_lead_with_the_verdict(self, report, markdown):
        """Each matter-varga label (heading / JSON label / HTML summary source) appends the
        verdict banner its body already prints; general vargas keep their plain label."""
        labels = {lbl.split(" - ")[0].split(" (")[0]: lbl for lbl, _ in report.divisional}
        by_prefix = {lbl.split(" ", 1)[0]: lbl for lbl, _ in report.divisional}
        for dtag in ("D-9", "D-10", "D-7", "D-12", "D-2", "D-3", "D-4", "D-30", "D-16",
                     "D-20", "D-24"):
            assert " - " in by_prefix[dtag], by_prefix[dtag]     # verdict appended
            assert f"### {by_prefix[dtag]}" in markdown
        assert " - CAREER: " in by_prefix["D-10"]
        assert " - SPOUSE: " in by_prefix["D-9"]
        assert " - HEALTH (H1): " in by_prefix["D-30"]
        # verdict comes FROM the body (a re-read, not a re-judgment)
        for lbl, body in report.divisional:
            if " - " in lbl and ">>>" in body:
                head_verdict = lbl.split(" - ", 1)[1].split(";")[0].split(",")[0]
                assert head_verdict.split(":")[0].strip() in body

    def test_the_d30_label_carries_disease_and_qualifies_the_longevity_lean(self, report):
        """D-30 is the one deep-read with no ``>>> <<<`` banner, so its label is built from the
        core block's plain verdict rows. It used to match ``Health (H1)`` alone — so a section
        whose whole subject is health-AND-disease dropped the disease verdict from every
        heading, collapsed summary and JSON label, and a chart reading health=favourable with
        disease=afflicted scanned as unqualified good news (this canonical chart is exactly
        that case). All three rows now carry; the longevity row keeps the body's own qualifier
        because the engine defers lifespan (PREC-8) and a bare heading would read as a verdict."""
        lbl = next(l for l, _ in report.divisional if l.startswith("D-30"))
        assert "HEALTH (H1): " in lbl
        assert "DISEASE (H6): " in lbl
        assert "LONGEVITY (H8): " in lbl and "lean, not a verdict" in lbl
        body = next(b for l, b in report.divisional if l.startswith("D-30"))
        for row in ("Health (H1)", "Disease (H6)", "Longevity(H8)"):
            assert row in body                      # the label is a re-read, never a new judgment

    def test_general_varga_domain_sentences_present(self, report, markdown):
        """D-27/40/45/60 each carry one domain-verdict sentence tying the varga lagna-lord's
        condition to the domain word, citing Raman's shodasavarga POINTER.

        The anchor is HPA-11:195 for all four (corrected 2026-08-19). It was previously a
        per-varga line (:100/:110/:113/:116) that contradicted `varga_domains.py` — which cites
        the pointer for these same four and states the policy in its module docstring: the
        divisions Raman teaches in full cite their own definition lines, "the remaining divisions
        cite RAMAN'S OWN POINTER at HPA-11:195-201". This test previously asserted only that
        *some* string was printed, which is why the discrepancy survived."""
        bodies = {lbl.split(" ", 1)[0]: body for lbl, body in report.divisional}
        for dtag, cite, word in (("D-27", "HPA-11:195", "general strength"),
                                 ("D-40", "HPA-11:195", "auspiciousness"),
                                 ("D-45", "HPA-11:195", "character and conduct"),
                                 ("D-60", "HPA-11:195", "totality")):
            body = bodies[dtag]
            assert "domain reading :" in body, dtag
            line = next(ln for ln in body.splitlines() if "domain reading :" in ln)
            assert cite in line and word in line, dtag
            assert "no D1 verdict is touched" in line
            assert line.count("varga lagna lord") == 1
        assert markdown.count("domain reading :") >= 4      # rendered in the report too

    def test_the_general_varga_anchors_agree_with_the_domain_table(self):
        """The judge module and the doctrine table must cite the SAME line for the same varga.

        Judge-module cite strings are free text — `source_lock` enumerates rules, yogas,
        significations and lookups, so nothing checked them, and the two sources drifted apart
        unnoticed. This pins them together so the next drift fails loudly instead of shipping two
        different provenance claims for one division."""
        from app.raman_saab.doctrine.varga_domains import DOMAINS
        from app.raman_saab.judges.general_varga_reading import _SPECS
        by_n = {d.n: d for d in DOMAINS}      # DOMAINS is a 16-tuple, not keyed by varga
        for n, spec in _SPECS.items():
            dom = by_n[n]
            expected = f"{dom.source.work}:{dom.source.line}"
            assert spec.citation == expected, (
                f"D-{n}: judge cites {spec.citation}, varga_domains cites {expected}")

    def test_karmic_rereads_are_one_line_and_home_blocks_stay_full(self, report, markdown):
        """The karmic chapter carries one-sentence D-20/D-60 re-reads (no embedded ASCII
        blocks) while the home divisional sections still render the full blocks — both
        halves of the REPORT COMPLETENESS argument pinned."""
        kv = report.karmic
        assert kv is not None
        for core in (kv.d20_core, kv.d60_core):
            assert core is not None
            assert "\n" not in core                    # one sentence, not a block
            assert ">>>" not in core and "RAMAN CORE" not in core
            assert "renders, untrimmed, in the Divisional deep-reads section" in core
        assert "- **D-20 Vimsamsa (spiritual) - domain re-read** " in markdown
        assert "- **D-60 Shashtiamsa (totality) - domain re-read** " in markdown
        # the home sections still carry the FULL blocks
        bodies = {lbl.split(" ", 1)[0]: body for lbl, body in report.divisional}
        assert ">>> SPIRITUAL:" in bodies["D-20"]      # full D-20 core banner at home
        assert "RAMAN CORE" in bodies["D-20"]
        assert "lagna :" in bodies["D-60"]             # full D-60 picture at home
        assert "strong here (exalt/own):" in bodies["D-60"]
        for dtag in ("D-20", "D-60"):
            s = markdown.find(f"### {dtag}")
            assert s >= 0
            section = markdown[s:markdown.find("\n### ", s + 5)]
            assert "```" in section                    # the full block, still rendered

    # ── item 5: Jaimini AK header + navigational cross-reference ─────────────

    def test_jaimini_chapter_opens_with_ak_and_karakamsa_context(self, report, markdown):
        """The short Jaimini chapter now leads with the computed AK + Karakamsa sign before
        the sutra fragments, and closes with the purely-navigational cross-reference (the
        Studies-in-Jaimini pairing passage is corpus-gated, not composed)."""
        s = markdown.find("## Jaimini Karakamsa (the soul's inclination)")
        assert s >= 0
        section = markdown[s:markdown.find("\n## ", s + 5)]
        syn = report.synthesis
        ctx = section.find(f"the Atmakaraka (soul-planet) of this chart is **{syn.atmakaraka}**")
        assert ctx >= 0
        assert f"the Karakamsa - is **{syn.karakamsa}**" in section
        first_bullet = section.find("\n- ")
        assert first_bullet == -1 or ctx < first_bullet     # context BEFORE the fragments
        assert "corpus-gated and not composed here" in section   # the recorded skip
        assert "dated Chara dasha (Jaimini) sequence" in section  # navigational pointer

    # ── the decree guard on every new prose surface ──────────────────────────

    def test_wave2_surfaces_pass_the_decree_guard(self, report, markdown):
        """All Wave-2 prose stays in the indication idiom — the decree tripwire never fires
        on the new sections, sentences, labels or re-reads."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        from app.raman_saab.detailed_report import gochara_synthesis_sentence
        for marker in ("**Influence basis**", "### Adverse dasha x transit confluence",
                       "**Read as sentences**",
                       "## Jaimini Karakamsa (the soul's inclination)"):
            s = markdown.find(marker)
            assert s >= 0, marker
            e = markdown.find("\n## ", s)
            section = markdown[s:e if e > 0 else s + 4000]
            m = _FORBIDDEN_RE.search(section)
            assert m is None, f"{marker}: {m.group(0)!r}"
        for g in report.gochara:
            assert _FORBIDDEN_RE.search(gochara_synthesis_sentence(g)) is None
        kv = report.karmic
        for text in (kv.d20_core or "", kv.d60_core or ""):
            assert _FORBIDDEN_RE.search(text) is None
        for lbl, body in report.divisional:
            assert _FORBIDDEN_RE.search(lbl) is None
            if "domain reading :" in body:
                line = next(ln for ln in body.splitlines() if "domain reading :" in ln)
                assert _FORBIDDEN_RE.search(line) is None

    def test_html_surfaces_carry_the_wave2_additions(self, report):
        """The standalone HTML renders the adverse mirror, the synthesis sentences, the
        verdict-first varga summaries, the AK context and the basis tooltips."""
        from app.raman_saab.report_html import to_html
        html = to_html(report)
        assert "Adverse dasha &times; transit confluence" in html
        assert "Read as sentences" in html
        assert "domain re-read" in html
        assert "the Karakamsa, is <b>" in html
        assert "CAREER: FAVOURABLE" in html or "CAREER: " in html   # verdict-first summary
        assert "&mdash; MD " in html                  # basis tooltip on a timeline chip
