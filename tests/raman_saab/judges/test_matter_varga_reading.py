"""Generalized matter-varga reading — `judges/matter_varga_reading.py`.

Public-baseline structure/smoke over all five spec'd matters (never private data), the unknown-matter
guard, and the report-only invariant.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import matter_varga_reading as mv

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)
_ALLOWED = {"favourable", "mixed", "afflicted", "insufficient-evidence"}


class TestMatterVargaReading:
    @pytest.fixture(scope="class")
    def chart(self):
        return cast_chart(_BASELINE, ayanamsa="raman")

    def test_all_five_matters_build_with_real_verdicts(self, chart) -> None:
        """wealth/siblings/property/comforts/spiritual each build and carry a real verdict on the
        right house + varga."""
        expect = {"wealth": (2, 2), "siblings": (3, 3), "property": (4, 4),
                  "comforts": (4, 16), "spiritual": (9, 20)}
        for matter, (house, varga) in expect.items():
            r = mv.build_matter_varga_reading(chart, matter)
            assert r.core.house == house and r.overlay.varga == varga
            assert r.core.verdict in _ALLOWED
            assert any(n.provenance == "RAMAN_EXPLICIT" for n in r.notes)

    def test_matters_constant_matches_specs(self) -> None:
        """MATTERS enumerates exactly the spec'd matters."""
        assert set(mv.MATTERS) == {"wealth", "siblings", "property", "comforts", "spiritual"}

    def test_unknown_matter_raises(self, chart) -> None:
        """An unknown matter is a hard error."""
        with pytest.raises(ValueError):
            mv.build_matter_varga_reading(chart, "elephants")


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_matter_varga_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "matter_varga_reading" not in Path(ht.__file__).read_text(encoding="utf-8")
