"""P7 domain engine — per-house aggregation of compendium rules composed
with the three-pillar bhava verdict."""
import pytest

from app.medini.doctrine.domains.houses import (
    HOUSE_DOMAIN,
    DomainReading,
    read_all_domains,
    read_domain,
)
from app.medini.doctrine.engine.predicates import EvalContext
from app.medini.doctrine.raman_chart import from_positions

# Synthetic chart: Virgo lagna (155°). Houses hand-checkable.
LONS = {
    "Sun": 89.0, "Moon": 215.0, "Mars": 5.0, "Mercury": 95.0,
    "Jupiter": 100.0, "Venus": 45.0, "Saturn": 280.0,
    "Rahu": 118.0, "Ketu": 298.0,
}
LAGNA = 155.0


@pytest.fixture(scope="module")
def chart():
    return from_positions(LONS, LAGNA, birth_jd=2448088.0)


class TestReadDomain:
    def test_reads_every_house(self, chart):
        readings = read_all_domains(chart)
        assert set(readings) == set(range(1, 13))
        for h, r in readings.items():
            assert isinstance(r, DomainReading)
            assert r.house == h and r.domain == HOUSE_DOMAIN[h]
            assert -1.0 <= r.doctrine_score <= 1.0
            assert r.n_fired <= r.n_evaluable
            assert r.bhava_verdict.bhava == h  # composed framework verdict

    def test_domain_score_from_fired_polarities(self, chart):
        # a house whose rules fire; the score is the mean polarity sign
        r = read_domain(chart, 7)
        assert r.n_evaluable > 0
        pols = [f.polarity for f in r.fired]
        signed = [1 if p == "favorable" else -1 for p in pols
                  if p in ("favorable", "unfavorable")]
        expected = round(sum(signed) / len(signed), 4) if signed else 0.0
        assert r.doctrine_score == expected

    def test_labels(self, chart):
        r = read_domain(chart, 1)
        assert r.doctrine_label in ("favourable", "mixed", "afflicted")
        assert isinstance(r.agrees_with_framework, bool)

    def test_invalid_house(self, chart):
        with pytest.raises(ValueError):
            read_domain(chart, 13)

    def test_dasha_context_flows_through(self, chart):
        # a timeline dasha context is accepted and passed to rule evaluation
        r = read_domain(chart, 8, dasha={"md": "Saturn", "ad": "Venus"})
        assert isinstance(r, DomainReading)


class TestComposition:
    def test_reading_is_side_by_side_not_merged(self, chart):
        # the compendium score and the framework verdict are independent
        r = read_domain(chart, 10)
        assert hasattr(r, "doctrine_score")
        assert hasattr(r.bhava_verdict, "composite_score")
        # agreement is derived, both retained
        fw = r.bhava_verdict.composite_score
        if r.doctrine_score != 0.0 and fw != 0.0:
            assert r.agrees_with_framework == ((r.doctrine_score > 0) == (fw > 0))

    def test_fired_rules_carry_provenance(self, chart):
        readings = read_all_domains(chart)
        for r in readings.values():
            for f in r.fired:
                assert f.rule_id.startswith("raman.")
                assert f.book and f.text
                assert f.polarity in ("favorable", "unfavorable", "mixed", "neutral")

    def test_some_rules_fire_across_the_chart(self, chart):
        readings = read_all_domains(chart)
        assert sum(r.n_fired for r in readings.values()) > 0
