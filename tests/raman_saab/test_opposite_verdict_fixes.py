"""Held fixes F2 and F5 from the opposite-verdict study (2026-11-05). Both ship OFF."""
from __future__ import annotations

import pytest

from app.raman_saab import house_audit as ha
from app.raman_saab.cited import corpus
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets.house_12_vyaya import combinations as h12
from app.raman_saab.judges import house_template as ht


def _chart(gid: str):
    rec = next(r for r in corpus.worked_examples() if r["id"] == gid)
    return ha._golden_chart(rec)


class TestHeldFlags:
    def test_flags_default_off(self) -> None:
        """Both fixes are held for the user's decision, so the shipped engine is unchanged."""
        assert h12.F2_KETU_FROM_KARAKAMSA is False
        assert ht.F5_BHAVA_RESCUE_UNVOTED is False


class TestKetuTwelfthFromKarakamsa:
    def test_ramana_maharshi_fires(self) -> None:
        """NH No. 46: Moon (Atmakaraka) in Gemini Navamsa, Ketu in Taurus Navamsa, the 12th from it."""
        ch = _chart("NH.chart_46")
        assert ch.planets["Ketu"].navamsa_sign == 2
        assert h12._KetuTwelfthFromKarakamsa().evaluate(C.EvalContext(ch)) is True

    def test_other_chart_does_not_fire(self) -> None:
        """Roosevelt (NH No. 47): Ketu is not in the 12th from his Karakamsa."""
        ch = _chart("NH.chart_47")
        assert h12._KetuTwelfthFromKarakamsa().evaluate(C.EvalContext(ch)) is False


class TestBhavaRescueUnvoted:
    def test_rescue_moves_h11_08_gains(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTJAH-II Chart 217: weak lord and karaka, benefic rules on the 11th, no Bhava vote."""
        ch = _chart("HTJAH-II.h11_08")

        def gains() -> str:
            pf = ht.judge_house(ch, 11)
            return str(next(s for s in pf.significations if s.signification == "gains").verdict)

        assert gains() == "afflicted"
        monkeypatch.setattr(ht, "F5_BHAVA_RESCUE_UNVOTED", True)
        assert gains() != "afflicted"
