"""Daśāṁśa (D-10) career reading — `judges/dasamsa_career_reading.py`.

Public-baseline structure/smoke (never private data) + the report-only invariant.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import dasamsa_career_reading as dc

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestDasamsaCareerSmoke:
    @pytest.fixture(scope="class")
    def reading(self) -> dc.DasamsaCareerReading:
        return dc.build_dasamsa_career_reading(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_core_and_overlay_assemble(self, reading: dc.DasamsaCareerReading) -> None:
        """Raman core (10th + lord's navāṁśa + kārakas) + the D-10 overlay both build."""
        c = reading.core
        assert 1 <= c.tenth_sign <= 12 and c.tenth_lord
        assert c.tenth_lord_navamsa_dignity      # Raman's key profession-strength signal resolved
        assert 1 <= reading.overlay.lagna_sign <= 12

    def test_four_career_karakas(self, reading: dc.DasamsaCareerReading) -> None:
        """The four career kārakas (Saturn/Mercury/Jupiter/Sun) are surfaced with house+dignity."""
        names = {k for k, _h, _d in reading.core.karakas}
        assert names == {"Saturn", "Mercury", "Jupiter", "Sun"}

    def test_verdicts_present(self, reading: dc.DasamsaCareerReading) -> None:
        """Career and honour verdicts come from Raman's real method."""
        allowed = {"favourable", "mixed", "afflicted", "insufficient-evidence"}
        assert reading.core.career_verdict in allowed
        assert reading.core.honour_verdict in allowed


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_dasamsa_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "dasamsa_career" not in Path(ht.__file__).read_text(encoding="utf-8")
