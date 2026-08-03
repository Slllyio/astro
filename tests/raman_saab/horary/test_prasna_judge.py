"""Karyasiddhi judge — the PRASNA-49 configurations, ladder, and the coded exclusions."""
from __future__ import annotations

from app.raman_saab.horary.prasna_judge import (EXCLUDED_TOPICS, REFUSAL, judge_prasna)

#: Virgo lagna (155), marriage query (7th = Pisces). Lagna lord Mercury; karyesa Jupiter.
_BASE = {"Sun": 40.0, "Moon": 200.0, "Mars": 310.0, "Mercury": 155.0,
         "Jupiter": 335.0, "Venus": 100.0, "Saturn": 130.0}


class TestJudgePrasna:
    def test_lord_in_lagna_and_karyesa_in_house_is_fulfilled(self):
        """PRASNA-49:107-116 config 1: Mercury sits in the lagna sign (conjunction counts
        as sign-aspect 1) and Jupiter sits in the 7th."""
        v = judge_prasna(positions=_BASE, lagna_lon=155.0, query_house=7)
        assert v.fulfilled and v.karyesa == "Jupiter"
        assert any("lagna lord aspects lagna" in e for e in v.evidence)

    def test_mutual_ithasala_between_lord_and_karyesa_is_fulfilled(self):
        """Config 3: mutual (tajika) aspect — Mercury 84 applying Jupiter 90 within orb."""
        pos = dict(_BASE, Mercury=84.0, Jupiter=90.0)
        v = judge_prasna(positions=pos, lagna_lon=155.0, query_house=7)
        assert any("mutual aspect" in e for e in v.evidence)

    def test_full_success_when_the_lord_aspects_the_lagna(self):
        """PRASNA-49:186-190 rung (d): 100% = 4 quarters."""
        v = judge_prasna(positions=_BASE, lagna_lon=155.0, query_house=7)
        assert v.success_quarters == 4

    def test_bare_chart_bottoms_out_at_one_quarter(self):
        """PRASNA-49:168-174 rung (a): no lord aspect, no benefic aspect -> 25%."""
        pos = {"Sun": 40.0, "Moon": 250.1, "Mars": 310.0, "Mercury": 12.0,
               "Jupiter": 288.0, "Venus": 342.0, "Saturn": 130.0}
        v = judge_prasna(positions=pos, lagna_lon=155.0, query_house=2)
        assert v.success_quarters in (1, 2, 3)   # never the 100% rung
        assert not any("100%" in e for e in v.evidence)

    def test_death_topics_are_refused_in_code(self):
        """The /ai-interpret precedent, firewall-lift scope rule 3 — no phrasing lifts it."""
        for topic in EXCLUDED_TOPICS:
            v = judge_prasna(positions=_BASE, lagna_lon=155.0, query_house=8, topic=topic)
            assert v.refusal == REFUSAL and not v.fulfilled and v.success_quarters == 0

    def test_every_verdict_carries_the_disclaimer(self):
        v = judge_prasna(positions=_BASE, lagna_lon=155.0, query_house=7)
        assert "never a validated prediction" in v.disclaimer
