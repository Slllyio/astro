"""Trimsāṁśa (D-30) health reading — `judges/trimsamsa_health_reading.py`.

Smoke + structure test on the PUBLIC canonical baseline (Bangalore 1990-07-15, CLAUDE.md) — never
private birth data. Verifies the provenance-honest split assembles from a real cast chart: the
Raman-core health verdicts + bālāriṣṭa + Moon/Mercury kāraka reads, and the report-only D-30
overlay. Each test states the fact it checks.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.trimsamsa_health_reading import (
    HealthCore, TrimsamsaHealthReading, build_trimsamsa_health_reading)

# CLAUDE.md canonical baseline: Bangalore 1990-07-15 12:00 IST -> Virgo lagna (sign 6).
_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


@pytest.fixture(scope="module")
def reading() -> TrimsamsaHealthReading:
    return build_trimsamsa_health_reading(cast_chart(_BASELINE, ayanamsa="raman"))


class TestTrimsamsaHealthReading:
    def test_assembles_with_core_and_overlay(self, reading: TrimsamsaHealthReading) -> None:
        """The reading is the provenance-honest split: an authoritative core + a D-30 overlay."""
        assert isinstance(reading.core, HealthCore)
        assert 1 <= reading.overlay.lagna_sign <= 12   # the D-30 actually cast

    def test_core_lagna_is_the_canonical_virgo(self, reading: TrimsamsaHealthReading) -> None:
        """The canonical baseline is Virgo lagna (sign 6) — the core reads the rāśi, not the D-30."""
        assert reading.core.lagna_sign == 6

    def test_core_carries_the_three_health_verdicts(self, reading: TrimsamsaHealthReading) -> None:
        """H1 health, H6 disease, H8 longevity are surfaced from Raman's real method."""
        allowed = {"favourable", "mixed", "afflicted", "insufficient-evidence"}
        assert reading.core.health_verdict in allowed
        assert reading.core.disease_verdict in allowed
        assert reading.core.longevity_verdict in allowed

    def test_balarishta_state_is_surfaced(self, reading: TrimsamsaHealthReading) -> None:
        """The infant-longevity gate is reported (applies/cancelled), never silently dropped."""
        assert isinstance(reading.core.balarishta_applies, bool)
        assert isinstance(reading.core.balarishta_cancelled, bool)

    def test_mercury_and_moon_karaka_reads_present(self, reading: TrimsamsaHealthReading) -> None:
        """Moon (mind) and Mercury (nervous-system/intellect) are read with their affliction load."""
        assert isinstance(reading.core.moon_afflictions, tuple)
        assert isinstance(reading.core.mercury_afflictions, tuple)
        assert 1 <= reading.core.mercury_house <= 12

    def test_not_medical_caveat_always_present(self, reading: TrimsamsaHealthReading) -> None:
        """The 'not a medical prognosis' caveat must always be emitted."""
        assert any("medical" in n.text.lower() for n in reading.notes)
