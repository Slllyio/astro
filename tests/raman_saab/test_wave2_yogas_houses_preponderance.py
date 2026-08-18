"""Wave-2 (2026-08-18) — yogas coverage honesty, deep-read enrichment, timing context,
house-block disclosures, preponderance witness classes. All add-only re-reads: these tests
also pin that no verdict, lean, count-used-for-status, or gate changed shape."""
from __future__ import annotations

import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (
    build_detailed_report,
    graded_buckets,
    house_chief_combinations,
    house_current_tier_line,
    house_frame_line,
    house_moderating_clause,
    to_markdown,
    yoga_next_ripening,
)
from app.raman_saab.doctrine.yogas import (
    MAHAPURUSHA_IDS,
    YOGA_FAMILIES,
    YOGAS,
    family_breakdown,
    yoga_family,
)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
#: A chart whose Moon HAS Kemadruma geometry that IS cancelled (found by scan over the
#: bhanga primitives; the canonical chart lacks the geometry entirely).
_KEM_CANCELLED = BirthData("Kem Cancelled", 1985, 1, 5, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


class TestYogaCoverageHonesty:
    """Item A — the 'Yogas present' section discloses what it actually checks."""

    def test_family_map_covers_every_record_exactly_once(self):
        """Every encoded YogaRecord id carries exactly one family tag and vice versa."""
        ids = {y.id for y in YOGAS}
        assert set(YOGA_FAMILIES) == ids
        assert sum(n for _f, n in family_breakdown()) == len(YOGAS)

    def test_coverage_paragraph_pins_the_encoded_count(self, markdown):
        """The disclosure names N == len(YOGAS) and closes with the unchecked-not-absent
        sentence."""
        assert (f"Coverage disclosure: {len(YOGAS)} named combinations are encoded"
                in markdown)
        assert "A yoga absent from this list is unchecked, not absent." in markdown
        for fam, n in family_breakdown():
            assert f"{fam} {n}" in markdown

    def test_notable_absences_computed_from_fired_set(self, report, markdown):
        """Canonical chart fires no Mahapurusha and no arishta yoga — both absence lines
        show; the lines are computed, not hard-coded (they invert with the fired set)."""
        assert not any(y.id in MAHAPURUSHA_IDS for y in report.yogas)
        assert not any(y.kind == "arishta" for y in report.yogas)
        assert "no Pancha Mahapurusha yoga fires" in markdown
        assert "no encoded arishta yoga fires" in markdown

    def test_family_names_replace_bare_other_kind(self, report, markdown):
        """A fired 'other'-kind yoga renders its Raman-taxonomy family, not 'other'."""
        vesi = next((y for y in report.yogas if y.id == "Y.VESI"), None)
        assert vesi is not None and vesi.kind == "other"
        assert yoga_family("Y.VESI") == "solar (Ravi-flank)"
        assert "**Vesi Yoga** (solar (Ravi-flank))" in markdown
        assert "**Pasa Yoga** (Nabhasa-Sankhya)" in markdown

    def test_bullets_ordered_by_deep_read_rank(self, report, markdown):
        """List order == the deep-read's comparison rank (meaningful post-Wave-0)."""
        rank_of = {yd.id: yd.comparison_rank for yd in report.yoga_deep}
        i = markdown.find("## Yogas present in this chart")
        j = markdown.find("## Yoga x Dasha timing")
        section = markdown[i:j]
        positions = [(section.find(f"**{y.name}**"), rank_of.get(y.id, 10_000))
                     for y in report.yogas]
        assert all(p >= 0 for p, _rk in positions)
        by_pos = [rk for p, rk in sorted(positions)]
        assert by_pos == sorted(by_pos)


class TestCancelledKemadruma:
    """Item A2 — the geometry-present-but-cancelled state surfaces instead of vanishing."""

    def test_branch_helper_agrees_with_the_bhanga_primitive(self, report):
        """kemadruma_cancellation_branch is non-None exactly when kemadruma_bhanga is
        True — the disclosure re-read can never contradict the primitive."""
        from app.raman_saab.primitives.bhangas import kemadruma_bhanga
        from app.raman_saab.yoga_deep_read import kemadruma_cancellation_branch
        assert (kemadruma_cancellation_branch(report.chart) is not None) == \
            kemadruma_bhanga(report.chart)

    def test_cancelled_state_renders_a_line_with_the_branch(self):
        """On a geometry-plus-bhanga chart the Yogas section reports the cancelled state
        and names the cancelling branch; Y.KEMADRUMA itself still does not fire."""
        from app.raman_saab.primitives.bhangas import kemadruma, kemadruma_bhanga
        r2 = build_detailed_report(_KEM_CANCELLED)
        assert kemadruma(r2.chart) and kemadruma_bhanga(r2.chart)
        assert not any(y.id == "Y.KEMADRUMA" for y in r2.yogas)
        md2 = to_markdown(r2)
        assert "Kemadruma geometry is present but cancelled by" in md2
        assert "the yoga does not fire" in md2

    def test_canonical_chart_shows_no_kemadruma_line(self, report, markdown):
        """No geometry -> no line (the state is computed, never templated in)."""
        from app.raman_saab.primitives.bhangas import kemadruma
        assert not kemadruma(report.chart)
        assert "Kemadruma geometry is present" not in markdown


class TestYogaDeepReadEnrichment:
    """Item B — placement/functional tags and the per-yoga SYN_R1 line."""

    def test_participants_carry_placement_and_functional_tags(self, report):
        from app.raman_saab.yoga_deep_read import placement_tag
        for yd in report.yoga_deep:
            for f in yd.participants:
                assert f.placement == placement_tag(f.house)
                assert f.functional in ("benefic", "malefic", "neutral", "yogakaraka")

    def test_placement_tag_classes(self):
        from app.raman_saab.yoga_deep_read import placement_tag
        assert placement_tag(1) == "kendra-trikona (Lagna)"
        assert placement_tag(7) == "kendra"
        assert placement_tag(9) == "trikona"
        assert placement_tag(8) == "dusthana"
        assert placement_tag(11) == "other"

    def test_syn_r1_line_names_the_stronger_participant(self, report):
        """Every 2+-participant yoga with rupas carries the 3HC:1359 line, and the named
        lead is the max-rupas participant."""
        for yd in report.yoga_deep:
            scored = [f for f in yd.participants if f.rupas is not None]
            if len(scored) >= 2 and len({f.planet for f in scored}) >= 2:
                assert yd.syn_r1_line, yd.name
                lead = max(scored, key=lambda f: f.rupas)
                assert yd.syn_r1_line.startswith("of the ")
                assert lead.planet in yd.syn_r1_line.split(" delivers ")[0]
                assert "(3HC:1359)" in yd.syn_r1_line
            else:
                assert yd.syn_r1_line == ""

    def test_markdown_renders_the_new_deep_read_fields(self, report, markdown):
        assert "**Stronger-participant delivery**" in markdown
        assert "functional " in markdown and "for this Lagna" in markdown
        gaj = next((yd for yd in report.yoga_deep if "Gajakesari" in yd.name), None)
        if gaj is not None:
            assert gaj.syn_r1_line and "3HC:1359" in gaj.syn_r1_line


class TestYogaTimingContext:
    """Item C — MD-context on AD rows, NOW marker, next-ripening summary."""

    def test_ad_rows_carry_their_md_context(self, report):
        """Every AD row's `maha` is the MD lord of the timeline period it was built
        from; MD rows carry None."""
        for t in report.yoga_timing:
            if t.role == "AD":
                assert t.maha is not None
                tp = next(tp for tp in report.timeline.periods
                          if tp.period.start_jd == t.period_start_jd
                          and tp.period.antar == t.planet)
                assert t.maha == tp.period.maha
            else:
                assert t.maha is None

    def test_markdown_ad_rows_say_under_which_md(self, markdown):
        assert re.search(r"\| AD \(under \w+ MD\) \|", markdown)

    def test_now_marker_present_on_exactly_the_running_rows(self, report, markdown):
        """The NOW cell appears on every table row containing the reference date and on
        no other row. (Wave-3 grouped the rows by yoga into one table per yoga, so the
        slice is the whole section rather than the first table.)"""
        i = markdown.find("| Yoga | Period | Planet | Window | Delivery | Now |")
        assert i > 0
        table = markdown[i:markdown.find("## Yoga deep-read", i)]
        rows = [ln for ln in table.splitlines() if ln.startswith("| ") and "---" not in ln
                and not ln.startswith("| Yoga |")]
        live = [t for t in report.yoga_timing
                if t.period_start_jd <= report.ref_jd < t.period_end_jd]
        assert live, "canonical ref date sits inside at least one constituent window"
        assert sum(1 for ln in rows if ln.rstrip().endswith("| NOW |")) == len(live)

    def test_next_ripening_one_line_per_resolvable_yoga(self, report, markdown):
        """One summary line per fired yoga that has timing rows; the full table is
        retained below it (REPORT COMPLETENESS)."""
        ripening = yoga_next_ripening(report)
        with_rows = {t.yoga_id for t in report.yoga_timing}
        assert len(ripening) == len([y for y in report.yogas if y.id in with_rows])
        assert "_Next ripening, per yoga (the full table below is retained):_" in markdown
        from app.raman_saab.render import _ascii
        for name, sent in ripening:
            assert _ascii(f"- **{name}** — {sent}")[:40] in markdown

    def test_ripening_sentences_are_now_or_future(self, report):
        for _name, sent in yoga_next_ripening(report):
            assert ("ripe NOW" in sent or "next ripens in" in sent
                    or "no further constituent-lord window" in sent)


class TestHouseBlockDisclosures:
    """Item D — chief combinations, frame line, moderating clause, current-period tier."""

    def test_h3_chief_combinations_render_raman_prose(self, report, markdown):
        chief = house_chief_combinations(report, 3)
        assert chief, "H3 fires rules on the canonical chart"
        i = markdown.find("### House 3 ")
        j = markdown.find("### House 4 ")
        block = markdown[i:j]
        assert "**Chief combinations**" in block
        sig, rid, text, cite = chief[0]
        assert f"`{rid}`" in block and cite in block
        # Raman's effect prose, not a bare count (ASCII-folded in the rendered surface).
        from app.raman_saab.render import _ascii
        assert _ascii(text)[:40] in block

    def test_chief_combinations_skip_the_placeholder_and_dedupe(self, report):
        for h in range(1, 13):
            rows = house_chief_combinations(report, h)
            ids = [rid for _s, rid, _t, _c in rows]
            assert len(ids) == len(set(ids))
            for _s, _rid, text, _c in rows:
                assert "no specifically favourable variant given" not in text
                assert text.strip()

    def test_h3_frame_line_names_both_frames(self, report, markdown):
        line = house_frame_line(report, 3)
        assert "from the Lagna" in line
        assert "Moon (Chandra Lagna)" in line
        assert "HTJAH-I:645-646" in line
        i = markdown.find("### House 3 ")
        block = markdown[i:markdown.find("### House 4 ")]
        assert "**Frame**" in block

    def test_frame_line_uses_the_lead_frame(self, report):
        """The line opens with the frame the verdict path actually led with."""
        for pf in report.proformas:
            if not pf.significations:
                continue
            lead = str(pf.significations[0].lead_frame)
            line = house_frame_line(report, pf.house)
            if lead == "lagna":
                assert line.startswith("Judged from the Lagna frame")
            elif lead == "moon":
                assert line.startswith("Judged from the Moon (Chandra Lagna) frame")

    def test_tier_line_matches_vimshottari_grading(self, report, markdown):
        """The per-house current-period line reproduces graded_buckets' tier for the
        running bhukti — same shared implementation, no drift."""
        tp = next(tp for tp in report.timeline.periods
                  if tp.period.start_jd <= report.ref_jd < tp.period.end_jd)
        _assoc, buckets = graded_buckets(tp, report.chart)
        tier_of = {a.house: tier for tier, items in buckets.items() for a in items}
        for h in range(1, 13):
            line = house_current_tier_line(report, h)
            assert f"{tp.period.maha} MD" in line
            if tier_of.get(h):
                assert f"this house grades {tier_of[h]}" in line
            else:
                assert "neither period-lord influences this house" in line
        assert "**Current period**" in markdown

    def test_moderating_clause_composed_only_from_ledger_flags(self, report):
        """When the clause is non-empty it appears in the Conclusion, and each of its
        arms traces to a ledger flag / metadata entry the judge recorded."""
        from app.raman_saab.detailed_report import house_conclusion
        for pf in report.proformas:
            clause = house_moderating_clause(report, pf.house)
            if not clause:
                continue
            assert clause.startswith("the affliction is qualified - ")
            concl = house_conclusion(report, pf.house)
            assert "affliction is qualified" in concl
            led = pf.significations[0].ledger
            gates = [v for k, v in pf.metadata if k == "catastrophic_gate"]
            if "parivartana" in clause:
                assert led.parivartana_resilient
            if "core significator is not struck" in clause:
                assert led.karaka_intact and led.karaka_strong
            if "catastrophic reading was demoted" in clause:
                assert gates

    def test_verdicts_and_headlines_untouched(self, report, markdown):
        """The add-only law: every house headline still equals the proforma rollup."""
        for pf in report.proformas:
            assert f"### House {pf.house} " in markdown
        for ht in report.preponderance.houses:
            pf = next(p for p in report.proformas if p.house == ht.house)
            assert ht.verdict == str(pf.rollup)


class TestPreponderanceWitnessClasses:
    """Item E — core/overlay tags, the second count pair, direct-vs-aspect yoga rows."""

    def test_every_testimony_carries_a_class(self, report):
        core_names = {"lord (lagna frame)", "karaka", "navamsa"}
        for ht in report.preponderance.houses:
            for t in ht.testimonies:
                assert t.klass in ("core", "overlay")
                assert (t.klass == "core") == (t.name in core_names)

    def test_core_and_overlay_counts_sum_to_the_flat_counts(self, report):
        """core F/A + overlay F/A == the flat For/Against the status words derive from —
        the new pair restates, never replaces."""
        for ht in report.preponderance.houses:
            core_f = sum(1 for t in ht.testimonies
                         if t.klass == "core" and t.lean == "favourable-leaning")
            core_a = sum(1 for t in ht.testimonies
                         if t.klass == "core" and t.lean == "adverse-leaning")
            over_f = sum(1 for t in ht.testimonies
                         if t.klass == "overlay" and t.lean == "favourable-leaning")
            over_a = sum(1 for t in ht.testimonies
                         if t.klass == "overlay" and t.lean == "adverse-leaning")
            assert ht.core_favourable == core_f and ht.core_adverse == core_a
            assert core_f + over_f == ht.favourable
            assert core_a + over_a == ht.adverse
            # flat partition invariant unchanged (the pre-existing conservation law)
            assert (ht.favourable + ht.adverse + ht.neutral + ht.absent
                    == len(ht.testimonies))

    def test_markdown_renders_the_core_pair_beside_the_flat_counts(self, report,
                                                                   markdown):
        for ht in report.preponderance.houses:
            assert (f"core: {ht.core_favourable} for / {ht.core_adverse} against"
                    in markdown)
        assert "Core (For/Against)" in markdown

    def test_yoga_rows_disclose_direct_vs_aspect(self, report):
        """Each bearing-yoga row names its matched factor, and the tag agrees with the
        append-only detail companion."""
        from app.raman_saab.doctrine.synthesis_rules import (
            yoga_house_bearings, yoga_house_bearings_detail)
        details = {y.id: yoga_house_bearings_detail(report.chart, y)
                   for y in report.yogas}
        by_name = {y.name: y for y in report.yogas}
        for ht in report.preponderance.houses:
            for t in ht.testimonies:
                if not t.name.startswith("yoga: "):
                    continue
                y = by_name[t.name[len("yoga: "):]]
                tag = (details[y.id] or {}).get(ht.house)
                assert tag in ("direct", "aspect")
                expected = ("[direct - own/occupy]" if tag == "direct"
                            else "[aspect-derived - admitted extension]")
                assert expected in t.value
        # the detail companion never changes the house set
        for y in report.yogas:
            bh = yoga_house_bearings(report.chart, y)
            det = details[y.id]
            assert (bh is None) == (det is None)
            if bh is not None:
                assert frozenset(det) == bh

    def test_status_words_and_leans_unchanged_by_the_tags(self, report):
        """The status column still derives from the FLAT counts only (the same words the
        pre-Wave-2 rule produced for these counts)."""
        for ht in report.preponderance.houses:
            if ht.verdict == "favourable":
                expect = ("well-corroborated" if ht.preponderance == "benefic"
                          else "contested" if ht.preponderance in ("adverse",
                                                                   "evenly balanced")
                          else "thinly attested")
            elif ht.verdict == "afflicted":
                expect = ("well-corroborated" if ht.preponderance == "adverse"
                          else "contested" if ht.preponderance in ("benefic",
                                                                   "evenly balanced")
                          else "thinly attested")
            elif ht.verdict == "mixed":
                expect = "(mixed headline)"
            else:
                expect = "(undecided headline)"
            assert ht.status == expect


class TestJsonAndHtmlSurfaces:
    """Template contract: every renderer shows every addition (append-only)."""

    def test_json_carries_the_new_appended_fields(self, report):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        cov = d["yoga_coverage"]
        assert cov["encoded"] == len(YOGAS)
        assert sum(f["count"] for f in cov["families"]) == len(YOGAS)
        assert cov["note"] == "a yoga absent from this list is unchecked, not absent"
        assert cov["kemadruma"]["state"] in ("no geometry", "cancelled", "fires")
        ts = d["testimony_support"]["4"]
        assert {"core_favourable", "core_adverse"} <= set(ts)
        h1 = d["preponderance"]["houses"][0]
        assert "core_favourable" in h1 and h1["testimonies"][0]["klass"]
        yd = d["yoga_deep"][0]
        assert "syn_r1_line" in yd and "placement" in yd["participants"][0]
        ad = next(t for t in d["yoga_timing"] if t["role"] == "AD")
        assert ad["maha"]

    def test_html_renders_the_new_disclosures(self, report):
        from app.raman_saab.report_html import to_html
        html = to_html(report)
        for probe in ("Coverage disclosure", "unchecked, not absent",
                      "Notable absences", "Next ripening", "AD (under",
                      "Chief combinations", "core (for/against)", "[core]",
                      "Stronger-participant delivery"):
            assert probe in html, probe


class TestGuardSweep:
    """All new prose passes the decree-voice guard (_FORBIDDEN_RE) — timed indications
    in the classical idiom are allowed; the decree voice is not."""

    def test_new_prose_carries_no_decree_voice(self, report, markdown):
        from app.llm.report_explainer import _FORBIDDEN_RE
        probes: list[str] = []
        # coverage / absence / kemadruma prose (canonical + synthetic wording)
        for marker in ("Coverage disclosure:", "Notable absences",
                       "_Next ripening, per yoga"):
            probes += [ln for ln in markdown.splitlines() if marker in ln]
        probes.append("Kemadruma geometry is present but cancelled by X - the yoga "
                      "does not fire (bhanga per 3HC:2182-2185; the Arishta chapter "
                      "reports the same three-state read).")
        for h in range(1, 13):
            probes.append(house_frame_line(report, h))
            probes.append(house_current_tier_line(report, h))
            probes.append(house_moderating_clause(report, h))
        for yd in report.yoga_deep:
            probes.append(yd.syn_r1_line)
        for _n, sent in yoga_next_ripening(report):
            probes.append(sent)
        for text in probes:
            assert not _FORBIDDEN_RE.search(text or ""), text
