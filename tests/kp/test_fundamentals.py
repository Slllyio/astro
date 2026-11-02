"""Reader 2's sign classes and rules (ruling R29), on hand-built charts and a real one."""

from __future__ import annotations

from dataclasses import dataclass

from app.kp.chart import Birth, cast
from app.kp.citations import CITATIONS
from app.kp.fundamentals import (
    BARREN,
    COMMON,
    FIXED,
    FRUITFUL,
    MOVABLE,
    MUTE,
    SEMI_FRUITFUL,
    VOICE,
    bestial_sign,
    fundamentals,
    human_sign,
)
from app.kp.subs import SIGN_LORDS


@dataclass
class _P:
    longitude: float
    bhava: int = 0


class _Chart:
    """Only what fundamentals() reads: cusps by sign, planets by sign and bhava."""

    def __init__(self, cusps: list[int], planets: dict[str, tuple[int, int]]) -> None:
        self._c = [_P(s * 30 + 10) for s in cusps]
        self.planets = {b: _P(s * 30 + 10, h) for b, (s, h) in planets.items()}

    def cusp(self, h: int) -> _P:
        return self._c[h - 1]

    def owned_houses(self, planet: str) -> tuple[int, ...]:
        return tuple(h for h in range(1, 13) if SIGN_LORDS[int(self._c[h - 1].longitude // 30)] == planet)


_BASE = {"Sun": (0, 1), "Moon": (0, 1), "Mars": (0, 1), "Mercury": (0, 1), "Jupiter": (0, 1),
         "Venus": (0, 1), "Saturn": (0, 1), "Rahu": (0, 1), "Ketu": (6, 7)}


def _met(chart: object) -> dict[str, bool]:
    return {f.key: f.met for f in fundamentals(chart)}  # type: ignore[arg-type]


class TestSignClasses:
    def test_qualities_partition_the_zodiac(self) -> None:
        """Movable, fixed and common signs are the three crosses, four signs each (KPR2 p.105)."""
        assert MOVABLE | FIXED | COMMON == frozenset(range(12))
        assert MOVABLE == {0, 3, 6, 9}

    def test_fruitful_and_barren_are_disjoint(self) -> None:
        """Watery signs are fruitful and mute; Aries, Gemini, Leo, Virgo barren (KPR2 pp.113-114)."""
        assert FRUITFUL == MUTE == {3, 7, 11}
        assert not (FRUITFUL | SEMI_FRUITFUL) & BARREN
        assert BARREN == {0, 2, 4, 5}
        assert VOICE == {2, 6, 10}

    def test_sagittarius_halves(self) -> None:
        """First half of Sagittarius is human, second half bestial (KPR2 p.115)."""
        assert human_sign(244.0) and not bestial_sign(244.0)
        assert bestial_sign(256.0) and not human_sign(256.0)


class TestRules:
    def test_angles_movable(self) -> None:
        """Movable signs on cusps 1, 4, 7, 10 meet the movable-angles rule only."""
        ch = _Chart([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], _BASE)
        m = _met(ch)
        assert m["angles.movable"] and not m["angles.fixed"] and not m["angles.common"]

    def test_progeny_none_needs_every_condition(self) -> None:
        """Barren 5/11, lords and Moon and Lagna and its lord not fruitful, no Moon/Jupiter in 5/11."""
        cusps = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 2, 11]   # 1st Aries, 5th Leo, 11th Gemini
        planets = dict(_BASE, Sun=(0, 1), Mercury=(0, 1), Mars=(0, 1), Moon=(0, 1), Jupiter=(0, 2))
        assert _met(_Chart(cusps, planets))["progeny.none"]
        planets_moon_in_5 = dict(planets, Moon=(0, 5))
        assert not _met(_Chart(cusps, planets_moon_in_5))["progeny.none"]
        planets_moon_fruitful = dict(planets, Moon=(3, 1))
        assert not _met(_Chart(cusps, planets_moon_fruitful))["progeny.none"]

    def test_marriage_early_and_late(self) -> None:
        """Fruitful 5th and 7th cusps with lords in fruitful signs: early; barren 1st and 5th: late."""
        cusps = [0, 1, 2, 3, 3, 5, 7, 7, 8, 9, 10, 11]   # 5th Cancer (Moon), 7th Scorpio (Mars)
        early = dict(_BASE, Moon=(11, 12), Mars=(3, 4))
        m = _met(_Chart(cusps, early))
        assert m["marriage.early"] and not m["marriage.late"]
        late = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]   # 1st Aries, 5th Leo
        assert _met(_Chart(late, _BASE))["marriage.late"]

    def test_speech_rules(self) -> None:
        """Mercury in a mute sign with the Moon in the 7th sign from it; Saturn in the 1st in a mute sign."""
        cusps = [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        ch = _Chart(cusps, dict(_BASE, Mercury=(3, 1), Moon=(9, 7), Saturn=(3, 1)))
        m = _met(ch)
        assert m["speech.mercury_moon"] and m["speech.saturn_lagna"]

    def test_voice_second(self) -> None:
        """A voice sign on the 2nd cusp; the stronger case needs Venus or Mercury in the 2nd."""
        cusps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]
        m = _met(_Chart(cusps, _BASE))
        assert m["voice.second"] and not m["voice.second_venus_mercury"]
        assert _met(_Chart(cusps, dict(_BASE, Venus=(2, 2))))["voice.second_venus_mercury"]

    def test_partnership_exchange(self) -> None:
        """Lagna lord in the 7th lord's sign and vice versa (parivartana)."""
        cusps = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]   # lords Mars (1) and Venus (7)
        assert _met(_Chart(cusps, dict(_BASE, Mars=(6, 7), Venus=(0, 1))))["partnership.exchange"]


class TestRealChart:
    def test_every_rule_is_cited_and_reproducible(self) -> None:
        """Bangalore 1990-07-15 12:00: every result names a known citation and is deterministic."""
        ch = cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))
        a, b = fundamentals(ch), fundamentals(ch)
        assert a == b and len(a) == 28
        assert all(f.citation in CITATIONS for f in a)
        assert all(CITATIONS[f.citation].source == "KPR2" for f in a)
