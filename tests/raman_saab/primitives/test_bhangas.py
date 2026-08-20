from __future__ import annotations

import pytest

from app.raman_saab.primitives import bhangas as b
from app.raman_saab.chart.model import RamanChart


def _c(lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def test_exchange_and_parivartana():
    # Mars in Taurus(Venus-owned) + Venus in Aries(Mars-owned) -> exchange.
    c = _c({"Mars": 35.0, "Venus": 5.0})
    assert b.exchange("Mars", "Venus", c) is True
    # Aries lagna: 1st lord Mars in 2nd (Taurus), 2nd lord Venus in 1st (Aries) -> parivartana(1,2).
    assert b.parivartana(1, 2, c) is True
    assert b.parivartana(1, 3, c) is False


def test_neecha_bhanga_dispositor_in_kendra():
    # Sun debilitated in Libra (190). Dispositor Venus in Capricorn (280) = the 10th
    # house (a kendra) from Aries lagna (asc_lon 0) -> cancellation.
    c = _c({"Sun": 190.0, "Venus": 280.0})
    assert b.neecha_bhanga("Sun", c) is True
    assert b.effective_dignity("Sun", c) == "neecha_bhanga"


def test_no_neecha_bhanga_when_not_debilitated():
    c = _c({"Sun": 10.0})            # exalted, not debilitated
    assert b.neecha_bhanga("Sun", c) is False
    assert b.effective_dignity("Sun", c) == "exalt"


def test_kemadruma_moon_isolated():
    # Moon alone, nothing in 2nd/12th from Moon, nothing with it (Sun excluded) -> kemadruma.
    c = _c({"Moon": 100.0})
    assert b.kemadruma(c) is True


def test_kemadruma_bhanga_planet_in_kendra_from_moon():
    # 3HC:2182-2185 kendra-from-Moon branch: Moon h2 isolated; Saturn h5 is the
    # 4th from the Moon (a kendra from the Moon) but NOT a kendra from the Lagna.
    c = _c({"Moon": 35.0, "Saturn": 125.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is True


def test_kemadruma_bhanga_sun_conjunct_moon():
    # 3HC:2182-2185 conjunction branch (Sun policy): the Sun conjunct the Moon
    # does not stop formation (Sun is excluded there) but DOES cancel — the
    # cited line says "a planet" with no Sun exception.
    c = _c({"Moon": 35.0, "Sun": 40.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is True


def test_kemadruma_bhanga_absent_when_moon_truly_isolated():
    # Moon alone in h6: no kendra from the Lagna, nothing in a kendra from the
    # Moon (the Moon itself never counts), no conjunction, no benefic drishti.
    c = _c({"Moon": 160.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is False


class TestKemadrumaBhangaAttribution:
    """The scope question at 3HC:2187-2188, settled from the mounted text (Track 4b).

    The Remarks report the cancellation as "some authors" and then dismiss "these
    observations". If that dismissal covered the kendra branches, the engine would be
    encoding a rule Raman rejected. It does not: he applies those two branches himself, on
    worked charts, a few lines later — and the earlier pass missed it only because the OCR
    spells them "Kemadiuma" and "Kemidiumi".
    """

    def test_raman_applies_the_two_kendra_branches_in_his_own_voice(self):
        """The passage that settles the scope. Pinned so a corpus re-import that drops or
        renumbers it fails loudly instead of quietly reopening a closed question."""
        from app.raman_saab.doctrine.sources import passage
        p = passage("3HC:2263-2268")
        if p is None:
            pytest.skip("corpus not present on this machine")
        text = p["text"].lower()
        assert "cam" in text or "cancellation" in text     # "distinct cam < 1 Hi< i" (OCR)
        assert "moon are occupied" in text
        assert "lagna are also occupied" in text

    def test_the_converse_is_stated_on_chart_no_8(self):
        from app.raman_saab.doctrine.sources import passage
        p = passage("3HC:2255-2261")
        if p is None:
            pytest.skip("corpus not present on this machine")
        text = " ".join(p["text"].lower().split())
        assert "kendras either from lagna" in text

    def test_the_dismissal_is_still_in_the_text_and_still_before_them(self):
        """The reading rests on ORDER: the dismissal at :2188 precedes the worked
        application at :2263, so the application cannot be what is dismissed."""
        from app.raman_saab.doctrine.sources import passage
        p = passage("3HC:2185-2188")
        if p is None:
            pytest.skip("corpus not present on this machine")
        assert "not generally" in " ".join(p["text"].lower().split())

    def test_the_conjunction_branch_is_provably_redundant(self):
        """Branch (c) can never fire where branch (b) has not: `_in_kendra_from` scores the
        same rasi-house as distance 1 and the 1st is a kendra. Asserted on the mechanism, so
        it holds for every chart rather than for a sample."""
        from app.raman_saab.primitives.bhangas import _KENDRA, _in_kendra_from
        assert 1 in _KENDRA

        class _P:
            def __init__(self, h): self.rasi_house = h

        class _C:
            planets = {"Sun": _P(5)}
        assert _in_kendra_from("Sun", 5, _C()), \
            "a planet conjunct the reference must already count as in its kendra"

    def test_the_extended_branch_is_not_redundant_and_is_still_labelled_not_ramans(self):
        """Jupiter in the 5th or 9th from the Moon aspects it from outside every kendra, so
        unlike (c) this branch could matter — which is exactly why its NOT-3HC label has to
        survive."""
        from app.raman_saab.primitives.bhangas import _KENDRA, kemadruma_bhanga
        assert 5 not in _KENDRA and 9 not in _KENDRA
        assert "NOT-3HC" in (kemadruma_bhanga.__doc__ or "")
