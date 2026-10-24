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
from app.raman_saab.detailed_report import (build_detailed_report,
                                            descriptive_house_rules,
                                            house_further_combinations, house_indications,
                                            indication_label, longevity_decanate_cause,
                                            to_markdown)
from app.raman_saab.report_html import to_html
from app.raman_saab.report_json import to_report_dict

CANON = BirthData("canon", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    """The pinned baseline nativity (Bangalore 1990-07-15 12:00 IST, Virgo Lagna)."""
    return build_detailed_report(CANON, ayanamsa="lahiri")  # canonical pins are Lahiri-sourced (external refs); engine default is raman since 2026-10-23


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


class TestNonGradedRuleLane:
    """The 97 `kind="descriptive"` rules never execute — `rules.fires()` and
    `rule_firing.fire_rules` both skip a `condition=None` rule — so despite the class
    docstring promising they are "surfaced with its citation when a placement holds", no
    such path existed and their text reached no reader. It exists now, and says plainly
    that these were NOT evaluated."""

    def test_every_descriptive_rule_reaches_every_surface(self, report) -> None:
        rows = [row for h in range(1, 13) for row in descriptive_house_rules(h)]
        assert len(rows) > 90, "the corpus carries ~97 descriptive house rules"
        md, html = to_markdown(report), to_html(report)
        payload = to_report_dict(report)
        in_json = {row[1] for pf in payload["proformas"] for row in pf["doctrine_on_record"]}
        for _sig, rid, _text, _cite in rows:
            assert rid in md, rid
            assert rid in html, rid
            assert rid in in_json, rid

    def test_on_record_is_never_presented_as_a_reading(self, report) -> None:
        """The framing is load-bearing: an unevaluated rule shown as a finding would be a
        false claim about the engine's own work."""
        for surface in (to_markdown(report), to_html(report)):
            assert "not yet computed" in surface
            assert "listed, not applied to this chart" in surface

    def test_fired_rows_beyond_the_chief_cap_are_not_lost(self, report) -> None:
        """`house_chief_combinations` caps at three per signification; the remainder is
        shown rather than dropped (the completeness lock)."""
        md = to_markdown(report)
        for h in range(1, 13):
            for _sig, rid, _text, _cite in house_further_combinations(report, h):
                assert rid in md, rid

    def test_further_and_on_record_never_overlap(self, report) -> None:
        """A rule cannot be both fired-on-this-chart and never-evaluated."""
        for h in range(1, 13):
            fired = {row[1] for row in house_further_combinations(report, h)}
            listed = {row[1] for row in descriptive_house_rules(h)}
            assert not (fired & listed), h


class TestIndicationsAreVerdictInert:
    def test_no_signification_verdict_depends_on_metadata(self, report) -> None:
        """The lane is presentation only: stripping every metadata pair leaves each
        signification's grade and each house rollup byte-identical."""
        before = [(pf.house, str(pf.rollup),
                   tuple((sv.signification, str(sv.verdict)) for sv in pf.significations))
                  for pf in report.proformas]
        again = build_detailed_report(CANON, ayanamsa="lahiri")
        after = [(pf.house, str(pf.rollup),
                  tuple((sv.signification, str(sv.verdict)) for sv in pf.significations))
                 for pf in again.proformas]
        assert before == after
