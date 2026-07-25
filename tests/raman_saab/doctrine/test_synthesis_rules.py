"""Tests for the cross-feature synthesis layer (report-only, citation-verified)."""
from __future__ import annotations

import pytest
import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.doctrine.synthesis_rules import (
    SYNTHESIS_RULES,
    descriptive_rules,
    detect_synthesis,
)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_JD = swe.julday(2026, 7, 25, 12.0)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL, ayanamsa="lahiri")


@pytest.fixture(scope="module")
def fired(chart):
    return detect_synthesis(chart, _JD)


class TestSynthesisRegistry:
    def test_ids_unique(self):
        """Every synthesis rule id is unique."""
        ids = [r.id for r in SYNTHESIS_RULES]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("rule", [r for r in SYNTHESIS_RULES if r.source is not None],
                             ids=lambda r: r.id)
    def test_raman_band_citations_verify(self, rule):
        """Every cited rule resolves into a live book at a real line (the corpus vouches)."""
        assert rule.band == "raman"          # only the Raman band may carry live citations
        assert verify(rule.source)

    def test_flagged_bands_carry_no_live_citation(self):
        """Classical/AV/modern rules must NOT cite the corpus (the divergence firewall)."""
        for r in SYNTHESIS_RULES:
            if r.band != "raman":
                assert r.source is None, r.id
                assert r.provenance != "RAMAN_EXPLICIT", r.id

    def test_every_rule_is_two_voiced(self):
        """Doctrine statement + plain meaning + links — the report's contract per insight."""
        for r in SYNTHESIS_RULES:
            assert r.doctrine and r.simple_meaning and r.links, r.id


class TestDetector:
    def test_fires_on_the_canonical_chart(self, fired):
        """The canonical chart yields several personalised cross-feature insights."""
        assert len(fired) >= 4
        assert all(f.detail for f in fired)

    def test_band_precedence_order(self, fired):
        """Raman-band insights come first — the AV band can never outrank them."""
        order = {"raman": 0, "classical": 1, "av": 2}
        seq = [order[f.rule.band] for f in fired]
        assert seq == sorted(seq)

    def test_r1_names_the_stronger_yoga_lord(self, fired):
        """Gajakesari on the canonical chart: Jupiter (stronger) delivers, per 3HC:1359."""
        r1 = next((f for f in fired if f.rule.id == "SYN_R1_STRONGER_LORD_DELIVERS"), None)
        assert r1 is not None
        assert "Jupiter" in r1.detail and "rupas" in r1.detail

    def test_descriptive_rules_never_fire(self, fired):
        """Doctrine-on-record entries are listed, not fired."""
        fired_ids = {f.rule.id for f in fired}
        for d in descriptive_rules():
            assert d.id not in fired_ids

    def test_report_only_no_verdict_path_import(self):
        """The verdict path must never import the synthesis layer (authority invariant)."""
        import inspect

        from app.raman_saab import proforma
        from app.raman_saab.judges import house_template
        for mod in (house_template, proforma):
            assert "synthesis_rules" not in inspect.getsource(mod)
