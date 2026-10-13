"""Houses 4, 7, 9 strength-slot sweep (2026-10-13): H4 8/12, H7 0/12, H9 1/12 correctly encoded.

H7 and H9 were both pinned as "ruled CORRECT" by an earlier review. They were the two worst
fairly-sampled houses of the whole sweep, because nearly every conditional sentence in their
tables is gated on AFFLICTION or benefic contact, which the weak-strength slot cannot test.
"""
from __future__ import annotations

import re

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}
_NEW = [r.id for r in ALL_RULES
        if r.house in (4, 7, 9) and r.group == "lord_in_house"
        and not re.fullmatch(r"H\d+\.L\.\d+", r.id)]   # every child, incl. H9.L.S1/S2


class TestEveryRehomedClause:
    @pytest.mark.parametrize("rid", _NEW)
    def test_is_cited_and_casts_no_good_or_bad_vote(self, rid: str) -> None:
        """Re-homed clauses show Raman's words; their parent already votes for the placement."""
        r = _R[rid]
        assert r.source.line > 0 and r.polarity == "neutral", rid

    def test_the_batch_is_the_size_the_reviews_produced(self) -> None:
        assert len(_NEW) == 44, len(_NEW)   # H4 5 + H7 22 + H9 17


class TestHouseSeven:
    def test_the_only_weak_slot_text_left_is_ramans_one_plain_weakness_clause(self) -> None:
        """HTJAH-II:273 "If the 7th lord is weak, there may be no children" is the section's
        ONLY sentence gated on the 7th lord's strength alone."""
        weak = {f"H7.L.{n}": _R[f"H7.L.{n}"].afflicted for n in range(1, 13)}
        assert {k for k, v in weak.items() if v} == {"H7.L.5"}
        assert "weak" in weak["H7.L.5"]

    def test_weak_and_afflicted_was_parked_not_faked_and_is_now_exact(self) -> None:
        """295 needs BOTH halves. An affliction-conditioned record in the weak slot would still
        have shown to a STRONG afflicted lord (fire_rules falls through to the weak text when the
        other slots are empty), so it was parked rather than faked. RESOLVED 2026-10-13: IsWeak
        exists, so both halves now live in the condition and the text is unconditioned."""
        r = _R["H7.L.7a"]
        assert r.kind == "evaluable"
        assert {type(c).__name__ for c in r.condition.conds} >= {"IsWeak", "AfflictedBy"}
        assert r.afflicted is None and "TODO(" not in r.general


class TestHouseNine:
    def test_h9_l2_is_gone_because_raman_gives_it_no_unconditioned_reading(self) -> None:
        assert "H9.L.2" not in _R
        assert {"H9.L.2a", "H9.L.2b"} <= set(_R)

    def test_the_dropped_section_level_strength_clause_is_recorded(self) -> None:
        """7398 'If the ninth lord is very powerful' is the section's only strength clause and
        names a band ABOVE is_powerful's minimum, so it is parked rather than filed."""
        assert "very powerful" in _R["H9.L.S1"].fortified

    def test_the_misprint_is_flagged_not_silently_corrected(self) -> None:
        assert "[sic" in _R["H9.L.4a"].general


class TestBeneficInfluence:
    def test_firm_benefics_are_jupiter_and_venus_only(self) -> None:
        """The Moon and Mercury are benefic only conditionally in Raman."""
        assert C.FIRM_BENEFICS == {"Jupiter", "Venus"}

    def test_influenced_by_detects_benefic_contact_with_a_house_lord(self) -> None:
        """Taurus rising: Saturn is the 9th lord (Capricorn). Jupiter conjunct Saturn in the 9th
        is benefic contact; Mars conjunct it instead is not."""
        def ctx(other: str):
            return C.EvalContext(RamanChart.from_stated_positions(
                {"Saturn": {"lon": 280.0, "bhava": 9}, other: {"lon": 282.0, "bhava": 9}},
                asc_lon=35.0, ayanamsa="raman"))
        assert C.InfluencedBy("LORD_OF:9").evaluate(ctx("Jupiter")) is True
        assert C.InfluencedBy("LORD_OF:9").evaluate(ctx("Mars")) is False
