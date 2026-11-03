"""Reader 4's traditional marriage conditions, read descriptively (ruling R28)."""

from __future__ import annotations

from app.kp.chart import Birth, cast
from app.kp.citations import CITATIONS
from app.kp.marriage_conditions import (
    CITATIONS as MC_CITES,
)
from app.kp.marriage_conditions import (
    EXCLUDED,
    Signs,
    conditions_from_signs,
    marriage_conditions,
)

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
# Aries=0 .. Pisces=11
ARI, TAU, GEM, CAN, LEO, VIR, LIB, SCO, SAG, CAP, AQU, PIS = range(12)


def _signs(lagna: int, cusp7: int, **planet: int) -> Signs:
    base = {"Sun": ARI, "Moon": ARI, "Mars": ARI, "Mercury": ARI, "Jupiter": ARI, "Venus": ARI,
            "Saturn": ARI, "Rahu": ARI, "Ketu": LIB}
    base.update(planet)
    return Signs(lagna, cusp7, base)


def _met(s: Signs) -> set[str]:
    return {c.key for c in conditions_from_signs(s) if c.met}


class TestCoverage:
    def test_every_printed_letter_is_encoded_or_excluded(self) -> None:
        """KPR4 pp.70-73 list youth (a)-(z) and late (a)-(g); each is encoded or excluded, never both."""
        printed = {f"youth.{c}" for c in "abcdefghijklmnopqrstuvwxyz"} | {f"late.{c}" for c in "abcdefg"}
        encoded = {c.key for c in marriage_conditions(cast(BANGALORE))}
        assert encoded | set(EXCLUDED) == printed
        assert not encoded & set(EXCLUDED)

    def test_citations_exist(self) -> None:
        """The module cites only registered Reader quotes."""
        assert set(MC_CITES) <= set(CITATIONS)


class TestHandBuilt:
    def test_fruitful_signs_and_cusp(self) -> None:
        """(a) Moon and Venus both in fruitful signs; (b) the 7th cusp in one."""
        assert {"youth.a", "youth.b"} <= _met(_signs(ARI, SCO, Moon=CAN, Venus=PIS))
        assert "youth.a" not in _met(_signs(ARI, LIB, Moon=CAN, Venus=ARI))

    def test_jupiter_moon_conjunction_needs_the_house(self) -> None:
        """(d) Jupiter with the Moon counts only in 1, 5, 10 or 11 from the Lagna sign."""
        assert "youth.d" in _met(_signs(ARI, LIB, Jupiter=LEO, Moon=LEO))  # 5th
        assert "youth.d" not in _met(_signs(ARI, LIB, Jupiter=GEM, Moon=GEM))  # 3rd

    def test_lords_of_one_and_seven_five_nine(self) -> None:
        """(h) Aries Lagna: Mars (lord 1) in Aries, Venus (lord 7) in Leo is 5 signs on."""
        assert "youth.h" in _met(_signs(ARI, LIB, Mars=ARI, Venus=LEO))
        assert "youth.h" not in _met(_signs(ARI, LIB, Mars=ARI, Venus=TAU))

    def test_madhana_gopala_exchange(self) -> None:
        """(p) Aries Lagna: Mars in Libra and Venus in Aries exchange the 1st and 7th lordships."""
        assert "youth.p" in _met(_signs(ARI, LIB, Mars=LIB, Venus=ARI))

    def test_benefics_from_lagna_and_moon(self) -> None:
        """(i) needs a benefic in 2/7/11 from the Lagna AND from the Moon, Moon not counting itself."""
        s = _signs(ARI, LIB, Moon=CAP, Jupiter=TAU, Mercury=LEO, Venus=LEO)  # Jupiter 2nd; Jupiter 5th from Moon
        assert "youth.i" not in _met(s)
        s = _signs(ARI, LIB, Moon=CAP, Jupiter=AQU)  # Jupiter 11th from Lagna, 2nd from Moon
        assert "youth.i" in _met(s)

    def test_saturn_late_and_its_ownership(self) -> None:
        """late (a): Saturn 1/3/5/7/10 from Lagna or Moon delays only if he owns none of 2, 7, 11."""
        # Taurus Lagna: Saturn owns 9 and 10; in Leo he is 1st from a Leo Moon.
        assert "late.a" in _met(_signs(TAU, SCO, Saturn=LEO, Moon=LEO))
        # Aries Lagna: Saturn owns 10 and 11, so the same slot does not count.
        assert "late.a" not in _met(_signs(ARI, LIB, Saturn=CAN, Moon=TAU))

    def test_saturn_aspects_seventh_lord_and_venus(self) -> None:
        """late (f): Saturn in Aries casts full aspects on Gemini (3rd), Libra (7th), Capricorn (10th)."""
        s = _signs(ARI, LIB, Saturn=ARI, Venus=LIB)  # Venus is lord of 7 and sits in Saturn's 7th
        assert "late.f" in _met(s)
        assert "late.f" not in _met(_signs(ARI, LIB, Saturn=ARI, Venus=LEO))
