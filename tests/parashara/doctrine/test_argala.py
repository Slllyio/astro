"""Argala — planetary intervention (BPHS ch.31).

Pinned to Parashara's own hypothetical chart (Aries ascendant: Mars in the 4th, Sun+Mercury in the
2nd, Jupiter in the 11th cause argala for the ascendant, BPHS-31) and to the pairing/verdict rules:
argala from 2/4/11/5 obstructed by 12/10/3/9, prevailing by count; Vipareeta from 3+ malefics.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine import argala as A
from app.parashara.doctrine.sources import verify


class TestArgalaForAscendant:
    def test_parashara_hypothetical_chart(self):
        # BPHS-31's own example: Aries lagna (target sign 1); Mars 4th (Cancer=4), Sun+Mercury 2nd
        # (Taurus=2), Jupiter 11th (Aquarius=11).
        ps = {"Mars": 4, "Sun": 2, "Mercury": 2, "Jupiter": 11}
        res = {a.argala_house: a for a in A.argala_for(1, ps)}
        assert set(res) == {2, 4, 11}
        assert set(res[2].argala_planets) == {"Sun", "Mercury"}
        assert res[4].argala_planets == ("Mars",)
        assert res[11].argala_planets == ("Jupiter",)

    def test_unobstructed_argala_prevails(self):
        ps = {"Jupiter": 4}                       # 4th-house argala, nothing in the 10th
        (a,) = A.argala_for(1, ps)
        assert a.argala_house == 4 and a.obstructor_house == 10 and a.prevails is True

    def test_obstructor_outnumbering_defeats_argala(self):
        # One planet in the 2nd (argala) vs two in the 12th (obstructor) -> argala does not prevail.
        ps = {"Jupiter": 2, "Saturn": 12, "Mars": 12}
        (a,) = A.argala_for(1, ps)
        assert a.argala_house == 2 and a.prevails is False

    def test_vipareeta_from_three_malefics_in_third(self):
        # 3 malefics in the 3rd (Gemini=3 from Aries) -> Vipareeta argala on the 11th-place argala.
        ps = {"Sun": 3, "Mars": 3, "Saturn": 3, "Jupiter": 11}
        res = {a.argala_house: a for a in A.argala_for(1, ps)}
        assert res[11].vipareeta is True and res[11].prevails is True

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            A.argala_for(13, {})


class TestCitation:
    def test_source_resolves(self):
        assert verify(A.SOURCE)
