"""Population-calibrated reading overlay (`judges/calibrated_reading.py`) — the honest-instrument
correction layer. Pins: the VERDICT-AUTHORITY INVARIANT (imported by nothing in the verdict path),
the Raman verdict passing through unchanged, the percentile math against the committed calibration
table, the inverted-channel warnings, and the provenance tag.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import house_template as ht
from app.raman_saab.judges.calibrated_reading import (
    _INVERTED, build_calibrated_reading, _calibrate, _table)


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


_FULL = {"Sun": 130.0, "Moon": 35.0, "Mars": 220.0, "Mercury": 155.0, "Jupiter": 275.0,
         "Venus": 20.0, "Saturn": 305.0, "Rahu": 65.0, "Ketu": 245.0}


class TestReportOnlyInvariant:
    def test_verdict_path_never_imports_the_overlay(self) -> None:
        """house_template must not import calibrated_reading (golden ratchet untouched by construction)."""
        src = Path("app/raman_saab/judges/house_template.py").read_text(encoding="utf-8")
        assert "calibrated_reading" not in src

    def test_raman_verdict_passes_through_unchanged(self) -> None:
        """The overlay's verdict/degree equal judge_house's, signification by signification."""
        chart = _chart(_FULL)
        pf = ht.judge_house(chart, 5)
        cal = build_calibrated_reading(chart, 5)
        assert [(e.signification, e.verdict) for e in cal.entries] == \
               [(s.signification, s.verdict) for s in pf.significations]


class TestCalibrationMath:
    def test_percentile_matches_the_committed_table(self) -> None:
        """afflicted-mild on H5 children: percentile = share below + half own band (mid-rank)."""
        row = _table()["table"]["H5_children"]
        e = _calibrate(5, "children", "afflicted", "mild")
        expected = sum(row["shares"][:2]) + 0.5 * row["shares"][2]
        assert abs(e.favourability_percentile - round(expected, 4)) < 1e-6
        assert e.band_share == round(row["shares"][2], 4)

    def test_near_universal_reading_is_flagged_uninformative(self) -> None:
        """A band covering >=50% of the population carries the little-information note."""
        e = _calibrate(5, "children", "afflicted", "mild")   # 71.6% band
        assert "NEAR-UNIVERSAL" in e.note

    def test_rare_reading_is_marked_rare(self) -> None:
        e = _calibrate(5, "children", "afflicted", "strong")  # ~0.9% band
        assert e.rarity == "rare"

    def test_abstained_reading_is_uncalibrated(self) -> None:
        e = _calibrate(5, "children", "insufficient-evidence", "")
        assert e.favourability_percentile is None and e.rarity == "uncalibrated"


class TestInvertedChannels:
    def test_h12_incarceration_carries_the_inversion_warning(self) -> None:
        e = _calibrate(12, "incarceration", "afflicted", "mild")
        assert e.inverted_warning and "INVERTED" in e.note

    def test_h3_courage_is_the_other_inverted_channel(self) -> None:
        assert _INVERTED == frozenset({"H3_courage", "H12_incarceration"})

    def test_non_inverted_channel_has_no_warning(self) -> None:
        e = _calibrate(5, "children", "favourable", "strong")
        assert not e.inverted_warning


class TestProvenanceAndValidity:
    def test_every_entry_is_tagged_empirical(self) -> None:
        cal = build_calibrated_reading(_chart(_FULL), 7)
        assert all(e.provenance == "EMPIRICAL_ASTRODATABANK" for e in cal.entries)

    def test_validity_note_disclaims_prediction(self) -> None:
        cal = build_calibrated_reading(_chart(_FULL), 1)
        assert "not a validated prediction" in cal.validity_note

    def test_table_provenance_recorded(self) -> None:
        t = json.loads(Path("app/raman_saab/doctrine/calibration_table.json")
                       .read_text(encoding="utf-8"))
        assert "EMPIRICAL_ASTRODATABANK" in t["_provenance"]
        assert t["population_n"] > 10000 and len(t["table"]) == 56
