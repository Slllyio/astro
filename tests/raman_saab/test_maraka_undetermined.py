"""An undetermined maraka check is reported as undetermined, never as "no maraka-tier lord".

Audit 2026-10-23: `build_detailed_report` set the running-period maraka flag to False when
`is_maraka_period` raised, and every surface then printed "The running period carries no
maraka-tier lord." — a confident statement the engine never made. The flag is now tri-state.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari
from app.raman_saab.primitives.vimshottari import maraka_running_phrase

_CANONICAL = BirthData(name="C", year=1990, month=7, day=15, hour=12, minute=0,
                       tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestMarakaRunningPhrase:
    def test_none_is_said_to_be_undetermined(self):
        """None never reads as a negative."""
        assert maraka_running_phrase(None) == "could not be determined for this chart"
        assert "no maraka" not in maraka_running_phrase(None)

    def test_true_and_false_keep_their_wording(self):
        """The determined cases are worded exactly as before."""
        assert maraka_running_phrase(True) == "carries a maraka-tier lord"
        assert maraka_running_phrase(False) == "carries no maraka-tier lord"


class TestReportOnFailedMarakaCheck:
    def test_failed_check_is_reported_as_undetermined(self, monkeypatch):
        """A raising maraka check yields None and the markdown says it could not be determined."""
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown

        def _boom(*a, **k):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(vimshottari, "is_maraka_period", _boom)
        r = build_detailed_report(_CANONICAL, on=(2026, 1, 1))
        assert r.maraka_period_now is None
        md = to_markdown(r)
        assert "could not be determined for this chart" in md
        assert "carries no maraka-tier lord" not in md
