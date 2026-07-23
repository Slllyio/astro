"""Matter-varga dashboard — `judges/matter_varga_dashboard.py`.

Public-baseline structure/smoke (never private data) + the report-only invariant. Confirms every
life-matter dispatches to its deep reader and reports a Raman-method verdict.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import matter_varga_dashboard as mvd

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)
_ALLOWED = {"favourable", "mixed", "afflicted", "insufficient-evidence"}


class TestMatterVargaDashboard:
    @pytest.fixture(scope="class")
    def dash(self) -> mvd.MatterVargaDashboard:
        return mvd.build_matter_varga_dashboard(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_five_matters_mapped_to_their_vargas(self, dash: mvd.MatterVargaDashboard) -> None:
        """children→D7, marriage→D9, career→D10, education→D24, health→D30."""
        got = {e.matter: e.varga for e in dash.entries}
        assert got == {"children": 7, "marriage": 9, "career": 10, "education": 24, "health": 30}

    def test_every_verdict_is_a_real_verdict(self, dash: mvd.MatterVargaDashboard) -> None:
        """Each matter carries an authoritative (Raman-method) verdict from its deep reader."""
        assert all(e.verdict in _ALLOWED for e in dash.entries)

    def test_each_entry_names_its_deep_reader(self, dash: mvd.MatterVargaDashboard) -> None:
        """Each row points at the dedicated module to consult for the full reading."""
        readers = {e.reader for e in dash.entries}
        assert "saptamsa_reading" in readers and "navamsa_marriage_reading" in readers


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_dashboard(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "matter_varga_dashboard" not in Path(ht.__file__).read_text(encoding="utf-8")
