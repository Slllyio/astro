"""Tests for modern-wealth detector."""
from __future__ import annotations

from app.reading.modern_life.wealth import detect_modern_wealth
from app.reading.schema import Finding


class TestDetectModernWealth:

    def test_returns_list(self, bangalore_chart, asc_sign):
        assert isinstance(detect_modern_wealth(bangalore_chart, asc_sign), list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_wealth(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_ids_use_modern_wealth_prefix(self, bangalore_chart, asc_sign):
        for f in detect_modern_wealth(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.wealth."), f.id

    def test_crypto_speculation_on_mercury_rahu_in_11h(self, synthetic):
        """Aries asc -> 11H = Aquarius (sign 11)."""
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Mercury": 11, "Rahu": 11},
        )
        findings = detect_modern_wealth(chart, 1)
        assert any(
            f.id == "modern_life.wealth.crypto_speculation" for f in findings
        )

    def test_online_business_on_mercury_rahu_in_10h(self, synthetic):
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Mercury": 10, "Rahu": 10},
        )
        findings = detect_modern_wealth(chart, 1)
        assert any(
            f.id == "modern_life.wealth.online_business" for f in findings
        )

    def test_passive_income_on_jupiter_venus_in_11h(self, synthetic):
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Jupiter": 11, "Venus": 11},
        )
        findings = detect_modern_wealth(chart, 1)
        assert any(
            f.id == "modern_life.wealth.passive_income" for f in findings
        )

    def test_debt_burden_on_saturn_rahu_in_2h(self, synthetic):
        """Aries asc -> 2H = Taurus (sign 2)."""
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Saturn": 2, "Rahu": 2},
        )
        findings = detect_modern_wealth(chart, 1)
        assert any(f.id == "modern_life.wealth.debt_burden" for f in findings)

    def test_foreign_income_on_rahu_in_11h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 11})
        findings = detect_modern_wealth(chart, 1)
        assert any(
            f.id == "modern_life.wealth.foreign_income" for f in findings
        )

    def test_stock_market_on_mercury_mars_rahu_in_11h(self, synthetic):
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Mercury": 11, "Mars": 11, "Rahu": 11},
        )
        findings = detect_modern_wealth(chart, 1)
        assert any(f.id == "modern_life.wealth.stock_market" for f in findings)

    def test_no_outcome_prediction_language(self, bangalore_chart, asc_sign):
        import re
        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_wealth(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden prediction language in {f.id}: {f.verdict!r}"
            )
