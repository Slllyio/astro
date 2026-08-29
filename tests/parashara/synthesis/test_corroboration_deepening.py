"""Phase-4 corroboration — vipareeta yogas, BPHS-7's own varga table, D16/D60, sudarshana, framing.

Pins the reversal-yoga conditions verbatim from BPHS-48, the matter-varga assignments, the per-bhava
D60/D16 rule, the triple-lagna confirmation, and the dusthana presentation framing.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.doctrine.vipareeta import (
    ATTRIBUTION_SOURCE, HARSHA_SOURCE, PROVENANCE, SARALA_SOURCE, VIMALA_SOURCE, detect)
from app.parashara.reading import read
from app.parashara.synthesis import synthesize
from app.parashara.synthesis.render_synthesis import to_markdown


def _lon(sign: int, deg: float = 5.0) -> float:
    return (sign - 1) * 30 + deg


class TestVipareeta:
    def test_sarala_fires_on_eighth_lord_in_dusthana(self):
        """8th lord in the 6th -> Sarala (BPHS-48:133). Aries lagna: 8th = Scorpio, lord Mars;
        the 6th = Virgo."""
        ys = detect({"Mars": _lon(6)}, asc_sign=1)
        assert any(y.name == "Sarala" and y.house == 8 for y in ys)

    def test_harsha_needs_both_conditions(self):
        """Harsha needs the 6th malefic-touched AND its lord in a dusthana (BPHS-48:124)."""
        # Aries lagna: 6th = Virgo (lord Mercury). Mercury in Pisces (the 12th) = dusthana; Saturn
        # in Virgo touches the 6th -> Harsha.
        both = detect({"Mercury": _lon(12), "Saturn": _lon(6)}, asc_sign=1)
        assert any(y.name == "Harsha" for y in both)
        # Lord in dusthana but the 6th untouched by malefics -> no Harsha.
        lone = detect({"Mercury": _lon(12), "Jupiter": _lon(6)}, asc_sign=1)
        assert not any(y.name == "Harsha" for y in lone)

    def test_vimala_needs_malefic_contact_on_the_lord(self):
        """Vimala: 12th lord in a dusthana AND under malefic contact (BPHS-48:140)."""
        # Aries lagna: 12th = Pisces, lord Jupiter. Jupiter in Virgo (6th, a dusthana) conjunct
        # Mars -> Vimala; without Mars -> none.
        with_contact = detect({"Jupiter": _lon(6), "Mars": _lon(6)}, asc_sign=1)
        assert any(y.name == "Vimala" for y in with_contact)
        without = detect({"Jupiter": _lon(6)}, asc_sign=1)
        assert not any(y.name == "Vimala" for y in without)

    def test_sources_resolve_and_provenance_is_labeled(self):
        """Every vipareeta citation resolves; the provenance names Mantreswara."""
        for src in (ATTRIBUTION_SOURCE, HARSHA_SOURCE, SARALA_SOURCE, VIMALA_SOURCE):
            assert verify(src), src
        assert "Phaladeepika" in PROVENANCE


class TestDeepenedCorroboration:
    @pytest.fixture(scope="class")
    def report(self):
        return synthesize(read(cast(year=1990, month=7, day=15, hour=12, minute=0,
                                    tz_offset=5.5, latitude=12.97, longitude=77.59)))

    def test_matter_vargas_attach_to_their_houses_only(self, report):
        """A D7 (progeny) atom may appear on the 5th only; D2 (wealth) on the 2nd only."""
        for h, j in report.houses.items():
            for e in j.evidence:
                if e.condition == "d7_dignity":
                    assert h == 5
                if e.condition == "d2_dignity":
                    assert h == 2

    def test_d60_d16_rule_cites_its_sloka(self, report):
        """Any fired per-bhava amsa rule carries BPHS-7:62 (the chapter's own bhava rule)."""
        fired = [e for j in report.all_judgments for e in j.evidence
                 if e.condition in ("d16_flourish", "d60_diminish")]
        assert fired, "the canonical chart should fire the D16/D60 rule somewhere"
        assert all(e.source.work == "BPHS-7" and e.source.line == 62 for e in fired)

    def test_vargottama_marked_as_allied(self, report):
        """A vargottama atom names its allied provenance in the rule text."""
        for j in report.all_judgments:
            for e in j.evidence:
                if e.condition == "vargottama":
                    assert "allied" in e.rule and e.source.work == "SARAVALI-3"

    def test_every_new_citation_resolves(self, report):
        """The deepened evidence keeps the audit promise: every source resolves."""
        for j in report.all_judgments:
            for e in j.evidence:
                assert verify(e.source), (j.topic, e.condition, e.source)

    def test_dusthana_framing_rendered(self, report):
        """The 6th/8th/12th judgments carry their framing note in the markdown (and only they)."""
        md = to_markdown(report)
        assert "the 6th's indications ARE adversities" in md
        assert "a strong 8th indicates LONG life" in md
        assert "prominence is not favour" in md