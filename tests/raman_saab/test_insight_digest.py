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
        known = {"dominant_theme", "convergence", "tension", "distinctive", "timing"}
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


class TestJson:
    def test_digest_is_serialized_and_json_safe(self, report):
        d = to_report_dict(report)
        assert "digest" in d
        assert d["digest"]["headline"] == report.info.sentence
        assert len(d["digest"]["items"]) == len(report.digest.items)
        json.dumps(d)                                 # must not raise (no dataclass/enum leaks)
