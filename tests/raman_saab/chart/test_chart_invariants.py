"""Universal invariants (Layer 1) — laws that must hold for EVERY chart, killing bug classes.

The suite is otherwise example-based; these are the universal laws — determinism, single-house
membership, circular-orb symmetry, a metamorphic sign-rotation law, and verdict totality — checked
over a seeded random sample. Deterministic RNG (fixed seed); no `hypothesis` dependency (noted as an
optional future upgrade for shrinking).
"""
from __future__ import annotations

import random

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine.yogas import detect_yogas
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives.combustion import _circ_sep

_VERDICTS = {"favourable", "mixed", "afflicted", "insufficient-evidence"}
_SEED = 424242


def _random_births(n: int, seed: int = _SEED) -> list[BirthData]:
    """Random VALID births at moderate latitude (so the cast always succeeds — extreme latitude is
    Phase B's concern)."""
    rng = random.Random(seed)
    return [BirthData(
        name=f"inv{i}", year=rng.randint(1900, 2040), month=rng.randint(1, 12),
        day=rng.randint(1, 28), hour=rng.randint(0, 23), minute=rng.randint(0, 59),
        tz_offset=rng.choice([-5.0, 0.0, 5.5, 8.0]),
        latitude=round(rng.uniform(-55.0, 55.0), 4),
        longitude=round(rng.uniform(-179.0, 179.0), 4)) for i in range(n)]


def _stated_chart(rng: random.Random, offset: float = 0.0) -> RamanChart:
    grahas = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    stated = {g: {"lon": (rng.uniform(0.0, 360.0) + offset) % 360.0, "bhava": 1} for g in grahas}
    asc = (rng.uniform(0.0, 360.0) + offset) % 360.0
    return RamanChart.from_stated_positions(stated, asc_lon=asc, ayanamsa="raman")


_BIRTHS = _random_births(50)


class TestDeterminism:
    @pytest.mark.parametrize("birth", _BIRTHS[:20], ids=lambda b: b.name)
    def test_casting_is_deterministic(self, birth: BirthData) -> None:
        """The same birth cast twice yields identical positions + verdicts (no wall-clock/RNG leak)."""
        a, b = cast_chart(birth, ayanamsa="raman"), cast_chart(birth, ayanamsa="raman")
        assert {n: p.lon for n, p in a.planets.items()} == {n: p.lon for n, p in b.planets.items()}
        assert a.asc_lon == b.asc_lon
        for h in range(1, 13):
            va = [(s.signification, s.verdict) for s in ht.judge_house(a, h).significations]
            vb = [(s.signification, s.verdict) for s in ht.judge_house(b, h).significations]
            assert va == vb, f"house {h} verdict non-determinism"

    def test_yoga_detection_is_deterministic(self) -> None:
        rng = random.Random(_SEED)
        for _ in range(30):
            ch = _stated_chart(rng)
            assert [y.id for y in detect_yogas(ch)] == [y.id for y in detect_yogas(ch)]


class TestMembership:
    @pytest.mark.parametrize("birth", _BIRTHS, ids=lambda b: b.name)
    def test_every_planet_sits_in_exactly_one_valid_house(self, birth: BirthData) -> None:
        chart = cast_chart(birth, ayanamsa="raman")
        assert len(chart.bhava_madhyas) == 12
        assert all(0.0 <= m < 360.0 for m in chart.bhava_madhyas)
        for name, p in chart.planets.items():
            assert 1 <= p.sign <= 12, name
            assert 1 <= p.rasi_house <= 12, name
            assert 1 <= p.nakshatra <= 27 and 1 <= p.pada <= 4, name
            assert 1 <= p.navamsa_sign <= 12, name
            assert 1 <= p.bhava <= 12, name


class TestCircularOrbSymmetry:
    def test_symmetry_range_and_cusp(self) -> None:
        rng = random.Random(_SEED)
        for _ in range(500):
            a, b = rng.uniform(0.0, 360.0), rng.uniform(0.0, 360.0)
            d = _circ_sep(a, b)
            assert _circ_sep(a, b) == _circ_sep(b, a), "orb must be symmetric"
            assert 0.0 <= d <= 180.0, "orb must be in [0, 180]"
        # The 359/1 Pisces-Aries cusp is 2 deg apart, NOT 358 (the reason the convention exists).
        assert abs(_circ_sep(359.0, 1.0) - 2.0) < 1e-9
        assert abs(_circ_sep(0.0, 180.0) - 180.0) < 1e-9
        assert _circ_sep(42.0, 42.0) == 0.0


class TestMetamorphicSignRotation:
    def test_full_sign_rotation_preserves_rasi_house(self) -> None:
        """Rotating every longitude (and the ascendant) by one whole sign (+30 deg) must leave every
        planet's rasi_house UNCHANGED (the house is sign-relative) and shift its sign by +1 (mod 12).
        A metamorphic law: no example chart proves it, but every chart must obey it."""
        seeder = random.Random(_SEED + 1)
        for _ in range(200):
            seed = seeder.randint(0, 10**9)
            # Same seed + same offset -> same random draws, so the only difference is the +30 rotation.
            base = _stated_chart(random.Random(seed), offset=0.0)
            rot = _stated_chart(random.Random(seed), offset=30.0)
            for name in base.planets:
                assert base.planets[name].rasi_house == rot.planets[name].rasi_house, name
                assert rot.planets[name].sign == (base.planets[name].sign % 12) + 1, name


class TestVerdictTotality:
    @pytest.mark.parametrize("birth", _BIRTHS, ids=lambda b: b.name)
    def test_judge_house_only_ever_returns_valid_verdicts(self, birth: BirthData) -> None:
        """`judge_house` for every house returns only valid Verdict enum members and never raises."""
        chart = cast_chart(birth, ayanamsa="raman")
        for h in range(1, 13):
            pf = ht.judge_house(chart, h)
            assert pf.rollup in _VERDICTS, f"house {h} rollup {pf.rollup!r}"
            for sv in pf.significations:
                assert sv.verdict in _VERDICTS, f"house {h} sig {sv.signification} -> {sv.verdict!r}"
