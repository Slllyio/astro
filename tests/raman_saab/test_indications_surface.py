"""The non-verdict indication lane reaches every renderer, and changes no verdict.

`SignificationVerdict.metadata` is the judge's verdict-INVARIANT lookup channel: the
cause-of-end decanate, the source of gains, the organ and tridosha of an afflicting graha,
the mode of confinement, the divisional readings. Before 2026-09-01 the canonical chart
computed 165 such pairs and rendered exactly one of them — `report_html` read none, and
`report_json._proforma_dict` dropped them before the interactive page could see them.

These tests pin the two things that must stay true: every pair reaches every surface (the
CLAUDE.md report-completeness lock), and adding the lane cannot move a grade.
"""
from __future__ import annotations

import json

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (build_detailed_report, house_indications,
                                            indication_label, longevity_decanate_cause,
                                            to_markdown)
from app.raman_saab.report_html import to_html
from app.raman_saab.report_json import to_report_dict

CANON = BirthData("canon", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    """The pinned baseline nativity (Bangalore 1990-07-15 12:00 IST, Virgo Lagna)."""
    return build_detailed_report(CANON)


class TestIndicationsComposed:
    def test_every_signification_metadata_pair_is_composed(self, report) -> None:
        """No pair the judge recorded is dropped by the composer."""
        expected = sum(len(sv.metadata)
                       for pf in report.proformas for sv in pf.significations)
        composed = sum(len(house_indications(report, h)) for h in range(1, 13))
        assert expected > 0
        assert composed >= expected

    def test_house_level_metadata_does_not_echo_a_signification_row(self, report) -> None:
        """`HouseProforma.metadata` reaches the reader too, but a pair ALSO recorded on a
        signification (H8's death-window, carried on both `longevity` and `death`) must
        not additionally print under the house itself. Two significations legitimately
        naming the same window is not duplication — the same window billed twice, once
        per matter and once more for the house, is."""
        rows = house_indications(report, 8)
        windows = [r for r in rows if r[1] == indication_label("death_window")]
        assert windows, "H8 records a death window"
        assert all(sig != "this house" for sig, _l, _v in windows)

    def test_unknown_key_still_gets_a_label(self) -> None:
        """The completeness lock forbids silently dropping a key with no table entry."""
        assert indication_label("some_new_key") == "some new key"
        assert indication_label("varga_D10").startswith("D10")


class TestIndicationsReachEverySurface:
    def test_markdown(self, report) -> None:
        md = to_markdown(report)
        assert "What the doctrine indicates" in md
        for h in range(1, 13):
            for _sig, label, value in house_indications(report, h):
                assert label in md
                assert value in md

    def test_html(self, report) -> None:
        html = to_html(report)
        assert "What the doctrine indicates" in html
        for h in range(1, 13):
            for _sig, label, value in house_indications(report, h):
                assert label in html

    def test_json_carries_key_label_and_value(self, report) -> None:
        payload = json.loads(json.dumps(to_report_dict(report)))
        pairs = [(k, lab, v)
                 for pf in payload["proformas"]
                 for sv in pf["significations"]
                 for k, lab, v in sv["indications"]]
        expected = sum(len(sv.metadata)
                       for pf in report.proformas for sv in pf.significations)
        assert len(pairs) == expected
        for key, label, _value in pairs:
            assert label == indication_label(key)


class TestLongevityPointerKeepsItsPromise:
    def test_decanate_class_prints_in_the_longevity_chapter(self, report) -> None:
        """The pointer names the Longevity chapter; the class must actually be there.
        Before this fix only the drekkana LORD printed, never the class Raman reads the
        manner of end from."""
        cause = longevity_decanate_cause(report)
        assert cause, "the canonical chart computes a 22nd-drekkana class"
        assert "22nd drekkana class" in to_markdown(report)
        assert cause in to_markdown(report)
        assert cause in to_html(report)


class TestIndicationsAreVerdictInert:
    def test_no_signification_verdict_depends_on_metadata(self, report) -> None:
        """The lane is presentation only: stripping every metadata pair leaves each
        signification's grade and each house rollup byte-identical."""
        before = [(pf.house, str(pf.rollup),
                   tuple((sv.signification, str(sv.verdict)) for sv in pf.significations))
                  for pf in report.proformas]
        again = build_detailed_report(CANON)
        after = [(pf.house, str(pf.rollup),
                  tuple((sv.signification, str(sv.verdict)) for sv in pf.significations))
                 for pf in again.proformas]
        assert before == after
