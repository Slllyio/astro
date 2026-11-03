"""Pins against Krishnamurti's worked horary cases in KP Reader 6."""

from __future__ import annotations

import pytest

from app.kp.chart import Birth
from app.kp.horary.cast import cast_horary
from app.kp.horary.judge import judge_horary
from app.kp.horary.rectify import rp_candidates
from app.kp.horary.timing import next_rising, positions

MADRAS = dict(lat=13.08, lon=80.27)


class TestHoraryCast:
    def test_number_48_at_madras(self) -> None:
        """KPR6 Example 1: 48 gives Gemini 8°40'; printed cusps 2/3/10/11/12 within 30'."""
        c = cast_horary(48, Birth(1969, 12, 11, 10, 0, tz=5.5, lat=13.0, lon=80.27))
        assert abs(c.cusp(1).longitude - (60 + 8 + 40 / 60)) < 1e-9
        printed = {2: 90 + 4 + 47 / 60, 3: 120 + 1 + 47 / 60, 10: 330 + 2 + 47 / 60,
                   11: 5 + 47 / 60, 12: 30 + 8 + 47 / 60}
        for h, p in printed.items():
            assert abs(((c.cusp(h).longitude - p + 180) % 360) - 180) < 0.5, h

    def test_opposite_cusps(self) -> None:
        """Cusps 7-12 are 180° from 1-6 (KPR6 p.100)."""
        c = cast_horary(74, Birth(1969, 12, 11, 7, 30, tz=5.5, lat=28.63, lon=77.2))
        for h in range(1, 7):
            assert abs(((c.cusp(h + 6).longitude - c.cusp(h).longitude) % 360) - 180) < 1e-6

    def test_number_out_of_range(self) -> None:
        """Only 1..249 are horary numbers."""
        with pytest.raises(ValueError):
            cast_horary(250, Birth(1969, 12, 11, 7, 30, tz=5.5, **MADRAS))


class TestRulingPlanetTiming:
    def test_trunk_call(self) -> None:
        """KPR6 p.126: fruitful Sun, Jupiter, Venus -> Libra 29°20' (Venus sign, Jupiter star, Sun sub, Venus sub-sub), call at 9-41."""
        r = next_rising(Birth(1969, 9, 21, 9, 0, tz=5.5, lat=7.47, lon=80.62),
                        ("Sun", "Jupiter", "Venus"), lagna_lord="Venus")
        p = r.position
        assert (p.sign_lord, p.star_lord, p.sub_lord, p.sub_sub_lord) == ("Venus", "Jupiter", "Sun", "Venus")
        assert abs(r.target - (180 + 29 + 20 / 60)) < 1e-6
        h, m = map(int, r.local(5.5)[-5:].split(":"))
        assert abs((h * 60 + m) - (9 * 60 + 41)) <= 5

    def test_servant(self) -> None:
        """KPR6 p.129-130: RPs Venus, Sun, Mercury, Saturn -> Taurus, Sun star, Saturn sub, Mercury sub-sub; 4 P.M."""
        r = next_rising(Birth(1968, 12, 13, 11, 0, tz=5.5, **MADRAS),
                        ("Venus", "Sun", "Mercury", "Saturn"), lagna_lord="Saturn")
        p = r.position
        assert (p.sign_lord, p.star_lord, p.sub_lord, p.sub_sub_lord) == ("Venus", "Sun", "Saturn", "Mercury")
        h, m = map(int, r.local(5.5)[-5:].split(":"))
        assert abs((h * 60 + m) - 16 * 60) <= 5

    def test_friend(self) -> None:
        """KPR6 p.127-128: RPs Sun, Rahu, Venus, Moon -> Rohini, Sun sub, Rahu sub-sub (Taurus 22°50')."""
        r = next_rising(Birth(1969, 2, 9, 13, 10, tz=5.5, **MADRAS),
                        ("Sun", "Rahu", "Venus", "Moon"), lagna_lord="Venus")
        p = r.position
        assert (p.sign_lord, p.star_lord, p.sub_lord, p.sub_sub_lord) == ("Venus", "Moon", "Sun", "Rahu")
        assert p.sub_sub_start <= 30 + 22 + 50 / 60 < p.end

    def test_positions_need_distinct_lords(self) -> None:
        """Ruling RH3: no position repeats a lord while another fruitful planet is unused."""
        for p in positions(("Sun", "Jupiter", "Venus")):
            assert len({p.sign_lord, p.star_lord, p.sub_lord}) == 3


class TestRulingPlanetRectification:
    def test_case_two_virgo_23(self) -> None:
        """KPR6 p.141: Mercury sign, Moon star, Sun sub, Mercury sub-sub = Virgo 23°10'; 3-36-45 A.M."""
        c = rp_candidates(Birth(1948, 11, 13, 2, 30, tz=5.5, lat=17 + 44 / 60, lon=83 + 23 / 60), 150,
                          judged=Birth(1967, 12, 24, 18, 45, tz=5.5, **MADRAS),
                          ruling=("Sun", "Moon", "Mercury"))
        assert len(c) == 1
        p = c[0].position
        assert (p.sign_lord, p.star_lord, p.sub_lord, p.sub_sub_lord) == ("Mercury", "Moon", "Sun", "Mercury")
        assert abs(c[0].longitude - (150 + 23 + 10 / 60)) < 0.1
        h, m = map(int, c[0].local_time[11:16].split(":"))
        assert abs(h * 60 + m - (3 * 60 + 37)) <= 2

    def test_case_one_his_choice_is_a_candidate(self) -> None:
        """KPR6 p.140: his Mercury sign, Moon star, Rahu sub is among the candidates (he chose by judgment)."""
        c = rp_candidates(Birth(1919, 10, 16, 4, 30, tz=5.5, lat=21.0, lon=73 + 40 / 60), 60,
                          judged=Birth(1968, 1, 21, 8, 30, tz=5.5, **MADRAS),
                          ruling=("Rahu", "Moon", "Mercury", "Sun", "Saturn"))
        assert any((x.position.sign_lord, x.position.star_lord, x.position.sub_lord) ==
                   ("Mercury", "Moon", "Rahu") for x in c)


class TestHoraryJudge:
    def test_record_shape_and_framing(self) -> None:
        """A horary verdict is a plain record with ruling planets, fruitful planets and framing."""
        d = judge_horary(48, Birth(1969, 12, 11, 10, 0, tz=5.5, **MADRAS), "marriage").to_dict()
        assert d["verdict"] in {"PROMISED", "DENIED", "MIXED", "NOT_SIGNIFIED"}
        assert set(d["fruitful"]) <= set(d["usable_ruling_planets"])
        assert "not a validated prediction" in d["framing"]


def test_natal_kp_never_imports_horary() -> None:
    """The horary package is walled: no natal KP module imports it."""
    from pathlib import Path
    for f in Path("app/kp").glob("*.py"):
        assert "horary" not in "\n".join(
            l for l in f.read_text(encoding="utf-8").splitlines() if l.startswith(("import", "from"))
        ), f.name
