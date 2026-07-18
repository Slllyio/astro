"""Report tests — resolution honesty per evidence mix, interval-only winners, channel
subtotals, side-by-side ayanamsa blocks and the ayanamsa-verdict section in both
renderings.
"""
from __future__ import annotations

from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification import candidates as C
from app.raman_saab.rectification import scoring as S
from app.raman_saab.rectification.events import LifeEvent
from app.raman_saab.rectification.report import build_report, to_markdown, to_text

_KW = dict(year=1989, month=10, day=12, latitude=27.23, longitude=79.03, tz_offset=5.5)


def _report(events: tuple[LifeEvent, ...], window=(9.9, 10.2)):
    cands = C.generate_candidates(
        **_KW, window_local_hours=window, ayanamsas=("raman", "lahiri"),
        event_jds=tuple(ev.jd_point() for ev in events))
    cache = C.ChartCache()
    scored = tuple(S.score_candidate(c, cache, events) for c in cands)
    return build_report(mode="rectify", scored=scored, events=events, facts=())


class TestResolutionStatement:
    def test_year_only_evidence_forbids_minute_claims(self) -> None:
        """Year-grade events -> the statement denies minute resolution outright."""
        rep = _report((LifeEvent("childbirth", 2018),))
        assert "NOT claimable" in rep.resolution_statement

    def test_day_grade_evidence_upgrades_the_claim(self) -> None:
        """A day-grade event upgrades the claim to ~minute-scale classes."""
        rep = _report((LifeEvent("marriage", 2017, 12, 4),))
        assert "day-grade" in rep.resolution_statement

    def test_winner_is_always_an_interval(self) -> None:
        """The statement carries the winner's CLASS INTERVAL, never a point time."""
        rep = _report((LifeEvent("marriage", 2017, 12, 4),))
        assert "CLASS INTERVAL" in rep.resolution_statement


class TestRendering:
    def test_both_ayanamsa_blocks_and_verdict_render(self) -> None:
        """Dual-ayanamsa is mandatory: both track blocks + the verdict section appear
        in text and markdown."""
        rep = _report((LifeEvent("marriage", 2017, 12, 4),
                       LifeEvent("career_start", 2016, 2)))
        txt, md = to_text(rep), to_markdown(rep)
        for out in (txt, md):
            assert "raman" in out and "lahiri" in out
            assert "verdict" in out.lower()
        assert "[raman track]" in txt and "[lahiri track]" in txt
        assert "### raman track" in md and "### lahiri track" in md

    def test_channel_subtotals_are_visible(self) -> None:
        """lords/houses/facts/arith subtotals render — never one opaque number."""
        rep = _report((LifeEvent("marriage", 2017, 12, 4),))
        txt = to_text(rep)
        for label in ("lords", "houses", "facts", "arith"):
            assert label in txt

    def test_active_house_panel_renders_for_the_leader(self) -> None:
        """The HTJAH-II:680-694 activation picture is shown per event."""
        rep = _report((LifeEvent("marriage", 2017, 12, 4),))
        assert "active houses" in to_text(rep).lower()

    def test_best_by_ayanamsa_lists_both_tracks(self) -> None:
        rep = _report((LifeEvent("marriage", 2017, 12, 4),))
        ays = {row[0] for row in rep.ayanamsa_verdict.best_by_ayanamsa}
        assert ays == {"raman", "lahiri"}
