"""Scoring-channel tests on the rect_case_01 nativity — channel A (period lords),
channel B (house activation per HTJAH-II:680-694), the resolution-honesty gate, the
negative-evidence penalty, the natal-fact channel, and the Tier-L guard.

Expectations are hand-derived from the chart (Scorpio lagna; Moon Aquarius H4; Saturn
Sagittarius H2; Venus Scorpio H1; Sun+Mars+Mercury Virgo H11) and the session-pinned
dasha chains — external truth, not engine self-output.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification import candidates as C
from app.raman_saab.rectification import scoring as S
from app.raman_saab.rectification.events import LifeEvent, resolve_fact

_LAT, _LON, _TZ = 27.23, 79.03, 5.5
_JD_1002 = swe.julday(1989, 10, 12, 10.0333 - _TZ, swe.GREG_CAL)


def _chart(ayanamsa: str):
    return C.light_chart(_JD_1002, _LAT, _LON, ayanamsa)


class TestChannelALords:
    def test_marriage_day_event_matches_under_both_ayanamsas(self) -> None:
        """2017-12-04: raman runs Sa/Sun/Venus (Sun = 7th-lord-from-Moon, Venus = kalatra
        karaka -> AD+PD match); lahiri runs Sa/Venus/Saturn (AD Venus matches). The
        marriage alone therefore cannot reject either ayanamsa — the 'flat' case."""
        ev = LifeEvent("marriage", 2017, 12, 4)
        for ay in ("raman", "lahiri"):
            es = S.score_event(_chart(ay), ev)
            assert any(lm.matched and lm.scorable for lm in es.levels), ay
            assert es.penalty == 0.0

    def test_year_precision_gates_out_the_pratyantar(self) -> None:
        """A year-grade event can never claim PD-level evidence: no single Pratyantar
        (max ~0.6y here) covers a whole year — the resolution-honesty gate."""
        es = S.score_event(_chart("raman"), LifeEvent("childbirth", 2018))
        pd = next(lm for lm in es.levels if lm.level == "pratyantar")
        assert not pd.scorable
        assert any("pratyantar unresolvable" in n for n in es.notes)

    def test_negative_evidence_penalty_fires_on_a_wrong_period(self) -> None:
        """A marriage claimed in 1995 contradicts this chart: the year sits wholly in
        Jupiter MD, and Jupiter is no H7 significator here (in Gemini H8 it aspects
        H12/H2/H4, touches neither the 7th nor Venus, and is not a marriage karaka) —
        the only scorable level is unmatched -> the year-scaled penalty."""
        es = S.score_event(_chart("raman"), LifeEvent("marriage", 1995))
        assert es.penalty == pytest.approx(S.NO_MATCH_PENALTY * 0.5)
        assert any("negative evidence" in n for n in es.notes)


class TestChannelBHouseActivation:
    def test_marriage_h7_is_active_limited_under_both_ayanamsas(self) -> None:
        """At the marriage date exactly ONE of (MD, AD) lords times H7 (AD Sun-from-Moon
        lord under raman / AD Venus under lahiri; MD Saturn times neither) -> the
        HTJAH-II:680-694 grade is 'limited', worth +0.5."""
        ev = LifeEvent("marriage", 2017, 12, 4)
        for ay in ("raman", "lahiri"):
            es = S.score_event(_chart(ay), ev)
            assert es.active_grade == "limited", ay
            assert es.houses_part == pytest.approx(S.ACTIVE_LIMITED)

    def test_active_panel_lists_the_lit_houses(self) -> None:
        """The full activation picture travels on the score for report display."""
        es = S.score_event(_chart("raman"), LifeEvent("marriage", 2017, 12, 4))
        assert es.active_panel
        assert all(p.startswith("H") and ":" in p for p in es.active_panel)

    def test_channel_b_unscorable_when_ad_is(self) -> None:
        """House activation resolves at AD depth, so an AD-unscorable event interval
        yields no channel-B claim (0, with a note) — not a fake grade."""
        es = S.score_event(_chart("raman"), LifeEvent("litigation", 1975))
        assert es.active_grade is None
        assert es.houses_part == 0.0
        assert any("house-activation unscorable" in n for n in es.notes)

    def test_channel_subtotals_are_reported_separately(self) -> None:
        """lords_part and houses_part never collapse into one opaque number."""
        es = S.score_event(_chart("raman"), LifeEvent("marriage", 2017, 12, 4))
        assert es.subtotal == pytest.approx(es.lords_part + es.houses_part)


class TestMarakaFrameRotation:
    def test_relative_marakas_rotate_to_the_event_bhava(self) -> None:
        """HTJAH-I:4479-4481 frame rotation: for a mother event (H4, Scorpio lagna ->
        4th = Aquarius) the marakas are the lords/occupants of the 2nd and 7th FROM the
        4th — H5 (Pisces -> Jupiter) and H10 (Leo -> Sun, tenanted by Ketu under raman)."""
        rel = S._relative_marakas(_chart("raman"), 4)
        assert rel == frozenset({"Jupiter", "Sun", "Ketu"})

    def test_mother_death_bonus_requires_a_running_relative_maraka(self) -> None:
        """A hypothetical mother_death in 2000 (Jupiter MD — Jupiter IS a 2nd-from-4th
        maraka lord here) earns the frame-rotated strong bonus; the overlay never fires
        for non-death events."""
        es = S.score_event(_chart("raman"), LifeEvent("mother_death", 2000))
        assert es.maraka_bonus == pytest.approx(S.MARAKA_BONUS_STRONG)
        es2 = S.score_event(_chart("raman"), LifeEvent("marriage", 2017, 12, 4))
        assert es2.maraka_bonus == 0.0


class TestFactChannelAndGuard:
    def test_light_chart_into_fact_scorer_raises(self) -> None:
        """The tier guard: a Shadbala-less chart must never silently degrade verdicts."""
        with pytest.raises(ValueError, match="Tier-F"):
            S.score_fact(_chart("raman"), resolve_fact("mother", "afflicted"))

    def test_property_fact_discriminates_the_ayanamsa(self) -> None:
        """A natal fact discriminates the ayanamsa: raman judges H4 property favourable
        (agreement +1 with the owner's confirmed 'favourable'), lahiri afflicted
        (agreement -1). (The earlier mother discriminator was retired when the
        catastrophic-nodal fix H4.C.18a made raman's mother favourable too — property is
        the surviving sharp H4 splitter, and points to raman, the rectified frame.)"""
        from app.raman_saab.chart.adapter import cast_chart
        birth = BirthData(name="x", year=1989, month=10, day=12, hour=10, minute=2,
                          tz_offset=_TZ, latitude=_LAT, longitude=_LON)
        fact = resolve_fact("property", "favourable")
        raman = S.score_fact(cast_chart(birth, ayanamsa="raman"), fact)
        lahiri = S.score_fact(cast_chart(birth, ayanamsa="lahiri"), fact)
        assert raman.agreement == 1.0
        assert lahiri.agreement == -1.0


class TestScoreCandidate:
    def test_channels_aggregate_and_facts_stay_off_by_default(self) -> None:
        """score_candidate sums per-channel parts; the expensive fact channel runs only
        on request (top-K), and the arithmetic channel stays within its cap."""
        cands = C.generate_candidates(
            year=1989, month=10, day=12, latitude=_LAT, longitude=_LON, tz_offset=_TZ,
            window_local_hours=(9.9, 10.2), ayanamsas=("raman",),
            event_jds=(vim.date_to_jd(2017, 12, 4),))
        cache = C.ChartCache()
        events = (LifeEvent("marriage", 2017, 12, 4), LifeEvent("childbirth", 2018, 9))
        cs = S.score_candidate(cands[0], cache, events)
        assert cs.fact_scores == ()
        assert cs.channels.event_lords == pytest.approx(
            sum(es.lords_part for es in cs.event_scores))
        assert cs.channels.event_houses == pytest.approx(
            sum(es.houses_part for es in cs.event_scores))
        assert 0.0 <= cs.channels.arithmetic <= 0.65
        assert cs.channels.total == pytest.approx(
            cs.channels.event_lords + cs.channels.event_houses + cs.channels.arithmetic)
