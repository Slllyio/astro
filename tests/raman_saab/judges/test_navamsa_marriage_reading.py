"""Navāṁśa (D-9) marriage reading — `judges/navamsa_marriage_reading.py`.

Kuja-doṣa detection on Track-B + a public-baseline structure/smoke (never private data) + the
report-only invariant. Each test states the fact it checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import navamsa_marriage_reading as nm

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


class TestKujaDosha:
    def test_mars_in_7th_is_kuja(self) -> None:
        """Mars in Libra (the 7th from an Aries Lagna) → Kuja doṣa flagged."""
        assert nm._kuja_dosha(_chart({"Mars": 185.0})) is True

    def test_mars_in_3rd_is_not_kuja(self) -> None:
        """Mars in Gemini (the 3rd, not a Kuja house) → no doṣa."""
        assert nm._kuja_dosha(_chart({"Mars": 65.0})) is False


class TestNavamsaMarriageSmoke:
    @pytest.fixture(scope="class")
    def reading(self) -> nm.NavamsaMarriageReading:
        return nm.build_navamsa_marriage_reading(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_core_and_overlay_assemble(self, reading: nm.NavamsaMarriageReading) -> None:
        """The reading builds: Raman core (7th + Venus + navāṁśa-7th) + the D-9 overlay."""
        c = reading.core
        assert 1 <= c.seventh_sign <= 12 and c.seventh_lord
        assert c.navamsa_seventh_lord            # the spouse significator resolved
        assert 1 <= reading.overlay.lagna_sign <= 12

    def test_verdicts_present(self, reading: nm.NavamsaMarriageReading) -> None:
        """Spouse and marital-happiness verdicts come from Raman's real method."""
        allowed = {"favourable", "mixed", "afflicted", "insufficient-evidence"}
        assert reading.core.spouse_verdict in allowed
        assert reading.core.marital_verdict in allowed

    def test_notes_are_raman_explicit(self, reading: nm.NavamsaMarriageReading) -> None:
        """The core method is cited to Raman (RAMAN_EXPLICIT)."""
        assert any(n.provenance == "RAMAN_EXPLICIT" for n in reading.notes)


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_navamsa_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "navamsa_marriage" not in Path(ht.__file__).read_text(encoding="utf-8")
