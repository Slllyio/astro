"""RuleRecord + Citation: a rule fires its condition tree, and its source resolves
to a real on-disk corpus line (the spec §5.4 citation discipline)."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation, verify


def _chart(lons: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def _rule(condition: C.Condition, kind: str = "evaluable") -> RuleRecord:
    return RuleRecord(id="H7.B.1", house=7, signification="spouse", group="combination",
                      kind=kind, condition=condition,
                      fortified="happy union", afflicted="discord",
                      frame="LAGNA", varga="D1", polarity="malefic",
                      source=Citation("HTJAH-II", 235))


def test_evaluable_rule_fires_its_condition():
    rule = _rule(C.And(C.InRashiHouse("Saturn", 7), C.Aspects("Mars", "Saturn")))
    # Saturn in 7th (Libra), Mars in 1st (Aries) -> Mars aspects Saturn (7th). Fires.
    assert rule.fires(_chart({"Saturn": 185.0, "Mars": 5.0})) is True
    # Mars in 2nd (Taurus) -> does NOT aspect Saturn. Does not fire.
    assert rule.fires(_chart({"Saturn": 185.0, "Mars": 35.0})) is False


def test_descriptive_rule_never_boolean_fires():
    rule = _rule(condition=None, kind="descriptive")
    assert rule.fires(_chart({"Saturn": 185.0})) is False


def test_citations_resolve_to_real_corpus_lines():
    # The corpus files exist on disk; these tags + lines must resolve.
    assert verify(Citation("HTJAH-I", 474)) is True       # 8 Considerations
    assert verify(Citation("HTJAH-II", 4544)) is True      # 64th-navamsa maraka line
    assert verify(Citation("HPA-14", 96)) is True          # balarishta houses 7/8/12
    assert verify(Citation("GBB-3", 462)) is True          # Saptavargaja ladder


def test_citation_verifier_rejects_bad_refs():
    assert verify(Citation("HTJAH-I", 10_000_000)) is False   # past EOF
    assert verify(Citation("NOPE", 1)) is False               # unknown work
    assert verify(Citation("HPA-99", 1)) is False             # no such chapter
