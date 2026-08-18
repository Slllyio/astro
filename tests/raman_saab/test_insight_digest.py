"""The Insight Digest — `app/raman_saab/insight_digest.py`.

The digest is the engine's own RANKED "what matters most": a pure re-read + transposition of
already-computed fields (preponderance roll-ups, band-sorted insights, rarity-sorted distinctive,
the current Life-chapter). These tests pin that (a) it ranks from the engine's own numbers, (b) it
recomputes no verdict, (c) its citations are the real tokens already attached to the findings, and
(d) it is JSON-safe. The one honest gap — population `distinctive` items carry NO Raman citation —
is asserted too.
"""
from __future__ import annotations

import json
import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.doctrine.sources import passage
from app.raman_saab.insight_digest import build_insight_digest
from app.raman_saab.report_json import to_report_dict

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_CITE_RE = re.compile(r"^[0-9A-Za-z][\w-]*:\d+(?:-\d+)?$")


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def digest(report):
    return report.digest


class TestDigestShape:
    def test_headline_is_the_info_sentence(self, report, digest):
        """The headline is the engine's own honesty sentence, verbatim — not a new claim."""
        assert digest.headline == report.info.sentence
        assert digest.headline.strip()

    def test_items_are_priority_ordered(self, digest):
        """Priorities are contiguous 0..n-1, ascending — the digest arrives pre-ranked, so the
        LLM narrator never has to (and must never) re-order it."""
        assert digest.items                                   # non-empty for the canonical chart
        assert [it.priority for it in digest.items] == list(range(len(digest.items)))

    def test_size_is_bounded(self, digest):
        """A digest is a shortlist, not the whole report — small enough for one grounded call."""
        assert 1 <= len(digest.items) <= 14

    def test_every_kind_is_known(self, digest):
        known = {"governing_factor", "foundation", "dominant_theme", "convergence",
                 "tension", "distinctive", "timing"}
        assert {it.kind for it in digest.items} <= known

    def test_every_lean_is_known(self, digest):
        assert {it.lean for it in digest.items} <= {"favourable", "adverse", "mixed", "neutral"}


class TestRankingFromEngineNumbers:
    def test_convergence_names_the_most_corroborated_house(self, report, digest):
        """The favourable convergence item is exactly the engine's `most_corroborated_favourable`
        house (its rank, not the digest's)."""
        h = report.preponderance.most_corroborated_favourable
        if h is None:
            pytest.skip("chart has no most-corroborated-favourable house")
        conv = next((it for it in digest.items
                     if it.kind == "convergence" and it.lean == "favourable"), None)
        assert conv is not None
        assert conv.houses == (h,)

    def test_tension_names_the_most_contested_house(self, report, digest):
        h = report.preponderance.most_contested
        if h is None:
            pytest.skip("chart has no most-contested house")
        tension = next((it for it in digest.items if it.kind == "tension"), None)
        assert tension is not None
        assert tension.houses == (h,)
        assert tension.lean == "mixed"

    def test_distinctive_follows_the_engine_rare_first_order(self, report, digest):
        """Distinctive items appear in the SAME order the engine already ranked them (rare-first),
        naming the same houses — the digest re-reads that ranking, never re-derives it."""
        dist_items = [it for it in digest.items if it.kind == "distinctive"]
        engine_houses = [h for h, _e in report.distinctive]
        assert [it.houses[0] for it in dist_items] == engine_houses[: len(dist_items)]

    def test_insights_appear_in_band_precedence_order(self, report, digest):
        """The dominant-theme items are the engine's already band-sorted insights (raman first),
        in that order."""
        theme_titles = [it.title for it in digest.items if it.kind == "dominant_theme"]
        engine_titles = [fi.rule.name for fi in report.insights]
        assert theme_titles == engine_titles[: len(theme_titles)]


class TestNoReJudgment:
    def test_convergence_detail_quotes_the_house_own_verdict(self, report, digest):
        """A convergence/tension item restates the house's OWN preponderance verdict — proving it
        re-reads the engine's value rather than inventing one."""
        for it in digest.items:
            if it.kind not in ("convergence", "tension"):
                continue
            house = it.houses[0]
            ht = next(h for h in report.preponderance.houses if h.house == house)
            assert ht.verdict in it.detail

    def test_rebuild_is_deterministic(self, report):
        """The digest is a pure function of the report — rebuilding yields identical items."""
        again = build_insight_digest(report)
        assert again == report.digest


class TestCitations:
    def test_all_cites_are_well_formed_tokens(self, digest):
        for it in digest.items:
            for c in it.cites:
                assert _CITE_RE.match(c), f"malformed cite {c!r} in {it.title!r}"

    def test_distinctive_carries_no_raman_citation(self, digest):
        """Population information content is EMPIRICAL, not doctrine — a distinctive item must
        never stamp a Raman citation on a statistic."""
        for it in digest.items:
            if it.kind == "distinctive":
                assert it.cites == ()

    def test_convergence_carries_the_ledger_citation(self, report, digest):
        if report.preponderance.most_corroborated_favourable is None:
            pytest.skip("no favourable convergence on this chart")
        conv = next(it for it in digest.items
                    if it.kind == "convergence" and it.lean == "favourable")
        assert "HTJAH-I:8870" in conv.cites

    def test_cites_resolve_to_source_when_corpus_present(self, digest):
        """Corpus-gated: when the doctrine library is vendored, every cited token resolves to a
        verbatim passage (so the frontend click-to-source and the LLM anchoring are real)."""
        all_cites = [c for it in digest.items for c in it.cites]
        if not all_cites:
            pytest.skip("no cites in this digest")
        # probe with the ledger cite; if the corpus is not vendored it resolves to None -> skip
        if passage("HTJAH-I:8870") is None:
            pytest.skip("doctrine corpus not vendored")
        for c in all_cites:
            assert passage(c) is not None, f"cite {c!r} did not resolve to a source passage"


class TestRamanOpeningOrder:
    """Wave-2 (2026-08-17): the digest opens the way Raman opens — governing factor first
    (HTJAH-I:16001-16002), longevity foundation second (HTJAH-I:11703 when the lift fired),
    then the bhava items; each convergence/tension item weighs its house by Bhava-Bala rank
    (GBB-9:332), and the timing item names its own four-tier grade (HTJAH-I:1592-1596)."""

    def test_governing_factor_is_the_rank_zero_item(self, report, digest):
        """Item #1 is the ruler-of-the-nativity re-read — literally Raman's opening move."""
        it0 = digest.items[0]
        assert it0.kind == "governing_factor" and it0.priority == 0
        assert report.ruler.lagna_lord in it0.title
        assert "HTJAH-I:16001-16002" in it0.cites
        assert "Ruler of the nativity" in it0.sections
        if report.ruler.strongest is not None and not report.ruler.coincide:
            assert report.ruler.strongest in it0.detail   # both factors named when distinct

    def test_foundation_item_is_second_and_band_worded(self, report, digest):
        """Item #2 grounds on the longevity band + Balarishta status — a band, never a date."""
        it1 = digest.items[1]
        assert it1.kind == "foundation" and it1.priority == 1
        assert report.longevity_class in it1.title
        assert "Balarishta" in it1.detail
        assert "never a date" in it1.detail
        assert "Longevity" in it1.sections

    def test_foundation_reuses_the_strength_lift_citation_when_fired(self, report, digest):
        """When SYN_R10 fired, the foundation item re-reads it and carries ITS citation
        (HTJAH-I:11703) — reuse, never a new citation."""
        lift = next((i for i in report.insights
                     if i.rule.id == "SYN_R10_STRENGTH_OVERRIDES_ARISHTA"), None)
        it1 = digest.items[1]
        if lift is None:
            assert it1.cites == ()
        else:
            assert "HTJAH-I:11703" in it1.cites
            assert "Strength lifts the band" in it1.detail

    def test_convergence_and_tension_carry_the_bhava_bala_rank(self, report, digest):
        """The house items weigh 'by how much relative to the rest' — the Bhava-Bala rank
        clause (magnitude, not direction) with the GBB-9:332 citation the report already
        carries."""
        seen = 0
        for it in digest.items:
            if it.kind not in ("convergence", "tension"):
                continue
            hs = next((row for row in report.house_strength
                       if row.house == it.houses[0]), None)
            if hs is None or hs.bhava_bala_rank is None:
                continue
            seen += 1
            assert f"ranks {hs.bhava_bala_rank} of 12" in it.detail
            assert "magnitude, not direction" in it.detail
            assert "GBB-9:332" in it.cites
        assert seen >= 1                                  # canonical chart has ranked houses

    def test_timing_item_names_its_own_four_tier_grade(self, report, digest):
        """Coherence fix: the timing item's Ishta/Kashta lean sits beside the bhukti-tier
        grade of the SAME running sub-period, so the two axes cannot read as contradiction."""
        ti = next((it for it in digest.items if it.kind == "timing"), None)
        if ti is None:
            pytest.skip("no running chapter resolved on this chart")
        assert "by Raman's four-tier scheme" in ti.detail
        assert ("par excellence" in ti.detail) or ("ordinary" in ti.detail)
        assert "different axes" in ti.detail
        assert "HTJAH-I:1592-1596" in ti.cites

    def test_digest_prose_passes_the_decree_guard(self, digest):
        """Every item's title+detail stays in the indication idiom — the decree tripwire
        never fires (the 2026-08-17 guard line)."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for it in digest.items:
            m = _FORBIDDEN_RE.search(f"{it.title} {it.detail}")
            assert m is None, f"{it.kind}: {m.group(0)!r}"


class TestJson:
    def test_digest_is_serialized_and_json_safe(self, report):
        d = to_report_dict(report)
        assert "digest" in d
        assert d["digest"]["headline"] == report.info.sentence
        assert len(d["digest"]["items"]) == len(report.digest.items)
        json.dumps(d)                                 # must not raise (no dataclass/enum leaks)
