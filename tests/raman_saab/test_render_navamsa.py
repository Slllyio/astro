"""Paired test for app/raman_saab/render_navamsa.py — the D-9 marriage text renderer.

Pins the corrected Kuja-dosha provenance note (docs/raman_saab/REPORT_CRITIQUE_2026-08-17.md):
the full multi-frame check (Lagna/Moon/Venus reference points, per-sign exemptions,
Mars+Jupiter / Mars+Moon neutralisations, HTJAH-II:2579-2632) IS encoded — in the House-7
kalatra rule set (`_KujaDosha`, house_07_kalatra/combinations.py) — and the D-9 line is
only the narrow Lagna-frame screen. The old note falsely claimed all of it was
"not yet encoded here".
"""
from __future__ import annotations

import dataclasses

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.render_navamsa import to_text

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def reading():
    return build_navamsa_marriage_reading(cast_chart(_CANONICAL))


def _with_dosha(reading):
    """The note only prints when kuja_dosha is True — force it, chart-independent."""
    return dataclasses.replace(
        reading, core=dataclasses.replace(reading.core, kuja_dosha=True))


class TestKujaDoshaNote:
    def test_note_no_longer_claims_the_checks_are_unencoded(self, reading):
        """The false provenance claim ('not yet encoded here') is gone."""
        assert "not yet encoded" not in to_text(_with_dosha(reading))

    def test_note_points_to_the_house_7_rule_set(self, reading):
        """The corrected note states where the full multi-frame check actually lives."""
        txt = to_text(_with_dosha(reading))
        assert "House-7 kalatra" in txt
        assert "Lagna," in txt and "Moon and Venus" in txt          # the three frames
        assert "per-sign exemptions" in txt
        assert "Mars+Jupiter / Mars+Moon" in txt                    # the neutralisations
        assert "HTJAH-II:2579-2632" in txt
        assert "narrow Lagna-frame screen" in txt

    def test_null_measurement_framing_is_kept(self, reading):
        """The Measured-Truth lines (2,322 charts, OR 1.09, null) were not removed."""
        txt = to_text(_with_dosha(reading))
        assert "2,322 real charts" in txt
        assert "odds ratio 1.09, null" in txt

    def test_no_note_when_dosha_absent(self, reading):
        """Without the dosha the screen line still prints, the NOTE block does not."""
        no_dosha = dataclasses.replace(
            reading, core=dataclasses.replace(reading.core, kuja_dosha=False))
        txt = to_text(no_dosha)
        assert "Kuja (Mangal) dosha: absent" in txt
        assert "NOTE:" not in txt
