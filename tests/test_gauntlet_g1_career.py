"""Tests for the stateless control-sampler and dasha-lookup logic in gauntlet_g1_career."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.gauntlet_g1_career import (
    _YEAR_OFFSETS,
    _md_lord_at,
    _md_windows,
    _transit_signs_at,
)


class TestYearOffsets:
    def test_no_offset_inside_blackout_band(self):
        """Every control offset is at least 2 years from the event (|k| >= 2)."""
        assert all(abs(k) >= 2 for k in _YEAR_OFFSETS)
        assert 0 not in _YEAR_OFFSETS and 1 not in _YEAR_OFFSETS

    def test_symmetric_twelve_offsets(self):
        """The sampler offers -7..-2 and +2..+7 — twelve age-near candidates."""
        assert len(_YEAR_OFFSETS) == 12
        assert set(_YEAR_OFFSETS) == {-k for k in _YEAR_OFFSETS}


class TestMdWindows:
    def _windows(self):
        pd_windows = pd.DataFrame({
            "person_id": ["p1"] * 4,
            "md_seq": [1, 1, 2, 2],
            "md_lord": ["Venus", "Venus", "Sun", "Sun"],
            "start_jd": [1000.0, 2000.0, 3000.0, 3500.0],
            "end_jd": [2000.0, 3000.0, 3500.0, 4000.0],
        })
        return _md_windows(pd_windows)

    def test_pd_windows_collapse_to_md_level(self):
        """PD rows sharing an md_seq merge into one MD interval with its lord."""
        w = self._windows()["p1"]
        assert w == ([1000.0, 3000.0], [3000.0, 4000.0], ["Venus", "Sun"])

    def test_lookup_inside_each_window(self):
        """A jd inside an MD window returns that window's lord."""
        w = self._windows()["p1"]
        assert _md_lord_at(w, 1500.0) == "Venus"
        assert _md_lord_at(w, 3600.0) == "Sun"

    def test_lookup_outside_all_windows_is_none(self):
        """A jd before the first or after the last window yields None."""
        w = self._windows()["p1"]
        assert _md_lord_at(w, 500.0) is None
        assert _md_lord_at(w, 4001.0) is None
        assert _md_lord_at(None, 1500.0) is None


class TestTransitSigns:
    def test_nine_grahas_with_valid_signs_and_opposed_nodes(self):
        """J2000 transit block: 9 grahas, signs 1..12, Ketu opposite Rahu."""
        signs = _transit_signs_at(2451545.0)  # 2000-01-01 12:00 TT
        assert len(signs) == 9
        assert all(1 <= s <= 12 for s in signs.values())
        assert (signs["Rahu"] - 1 + 6) % 12 + 1 == signs["Ketu"]

    def test_sun_sidereal_sign_at_j2000(self):
        """On 2000-01-01 the sidereal (Lahiri) Sun is in Sagittarius (sign 9)."""
        assert _transit_signs_at(2451545.0)["Sun"] == 9
