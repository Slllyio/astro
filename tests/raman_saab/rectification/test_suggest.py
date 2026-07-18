"""Suggester + orthogonality tests — the interactive 'ask the next orthogonal question'
move of the worked session, computed: unsupplied event types ranked by how differently
their match windows fall across the leading candidates, and natal-fact questions where
the two ayanamsas' judge_house verdicts disagree (the 'mother' move, pinned).
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification import candidates as C
from app.raman_saab.rectification import scoring as S
from app.raman_saab.rectification import suggest as SG
from app.raman_saab.rectification.events import LifeEvent
from app.raman_saab.rectification.report import build_report

_KW = dict(year=1989, month=10, day=12, latitude=27.23, longitude=79.03, tz_offset=5.5)
_BIRTH_JD = swe.julday(1989, 10, 12, 10.0333 - 5.5, swe.GREG_CAL)
_HORIZON_JD = vim.date_to_jd(2026, 7, 18)


@pytest.fixture(scope="module")
def ranked_and_cache():
    events = (LifeEvent("marriage", 2017, 12, 4), LifeEvent("career_start", 2016, 2))
    cands = C.generate_candidates(
        **_KW, window_local_hours=(9.9, 10.2), ayanamsas=("raman", "lahiri"),
        event_jds=tuple(ev.jd_point() for ev in events))
    cache = C.ChartCache()
    scored = tuple(S.score_candidate(c, cache, events) for c in cands)
    ranked = tuple(sorted(scored, key=lambda cs: cs.channels.total, reverse=True))
    return ranked, cache, events


class TestIntervalMath:
    def test_jaccard_distance_disjoint_and_identical(self) -> None:
        """Disjoint windows -> 1.0; identical -> 0.0 — the discrimination extremes."""
        a, b = [(0.0, 10.0)], [(20.0, 30.0)]
        assert SG._jaccard_distance(a, b) == pytest.approx(1.0)
        assert SG._jaccard_distance(a, a) == pytest.approx(0.0)

    def test_partial_overlap_is_proportional(self) -> None:
        """Half-overlapping equal windows -> |sym diff|/|union| = 2/3."""
        assert SG._jaccard_distance([(0.0, 10.0)], [(5.0, 15.0)]) == pytest.approx(2 / 3)


class TestEventSuggestions:
    def test_unsupplied_types_are_ranked_and_supplied_excluded(self, ranked_and_cache):
        """Suggestions never repeat supplied evidence and carry a positive power."""
        ranked, cache, events = ranked_and_cache
        sugg = SG.suggest_events(ranked, cache,
                                 frozenset(ev.event_type for ev in events),
                                 birth_jd=_BIRTH_JD, horizon_jd=_HORIZON_JD)
        assert sugg, "the 2-year dasha offset must yield discriminating types"
        keys = {s.key for s in sugg}
        assert "marriage" not in keys and "career_start" not in keys
        assert all(s.power > 0 for s in sugg)
        assert all(s.kind == "event" for s in sugg)

    def test_powers_are_sorted_descending(self, ranked_and_cache):
        ranked, cache, events = ranked_and_cache
        sugg = SG.suggest_events(ranked, cache, frozenset(),
                                 birth_jd=_BIRTH_JD, horizon_jd=_HORIZON_JD)
        powers = [s.power for s in sugg]
        assert powers == sorted(powers, reverse=True)


class TestFactSuggestions:
    def test_property_is_surfaced_as_the_ayanamsa_discriminator(self, ranked_and_cache):
        """A sharp H4 splitter is surfaced as a zero-date question: raman judges property
        favourable, lahiri afflicted -> answering it picks the ayanamsa. (The mother
        discriminator was retired when the catastrophic-nodal fix made raman's mother
        favourable too.)"""
        ranked, cache, _ = ranked_and_cache
        sugg = SG.suggest_facts(ranked, cache, frozenset())
        assert any(s.key == "property" for s in sugg)
        prop = next(s for s in sugg if s.key == "property")
        assert "ayanamsa" in prop.detail

    def test_supplied_subjects_are_excluded(self, ranked_and_cache):
        ranked, cache, _ = ranked_and_cache
        sugg = SG.suggest_facts(ranked, cache, frozenset({"mother"}))
        assert all(s.key != "mother" for s in sugg)


class TestOrthogonalityInReport:
    def test_spread_splits_discriminators_from_flat(self, ranked_and_cache):
        """A no-signal event (litigation 1995: same penalty everywhere) reads flat;
        the marriage (which scores raman above lahiri) reads as a discriminator."""
        _, cache, _ = ranked_and_cache
        events = (LifeEvent("marriage", 2017, 12, 4), LifeEvent("litigation", 1995))
        cands = C.generate_candidates(
            **_KW, window_local_hours=(9.9, 10.2), ayanamsas=("raman", "lahiri"),
            event_jds=tuple(ev.jd_point() for ev in events))
        scored = tuple(S.score_candidate(c, cache, events) for c in cands)
        rep = build_report(mode="rectify", scored=scored, events=events, facts=())
        assert "litigation" in rep.flat_events
        assert "marriage" in rep.discriminators
