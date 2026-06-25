"""B6 backlog coverage pins — the three proposed "HPA/HTJAH house rules" are
ALREADY encoded; this test locks that coverage so the rules cannot silently
regress and nobody re-adds them as duplicates.

DOCTRINE_BACKLOG.md B6 was closed *resolved-by-audit* (2026-06-25) after a
bphs-doctrine-reviewer pass: B6.1/B6.2 COVERED (a new rule would double-count —
the judge dedups by ``rule.id``, not by placement), B6.3 PARTIALLY-COVERED
(the 7th-*lord*-in-dual-sign refinement is deliberately kept text-only to avoid
inflating the over-harsh H7 marriage tail). Each test states the doctrine fact.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets import house_04_sukha, house_07_kalatra
from app.raman_saab.doctrine.rules import RuleRecord


def _by_id(*rule_tuples: tuple[RuleRecord, ...]) -> dict[str, RuleRecord]:
    out: dict[str, RuleRecord] = {}
    for t in rule_tuples:
        for r in t:
            out[r.id] = r
    return out


_RULES = _by_id(house_07_kalatra.RULES, house_04_sukha.RULES)


def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


class TestB6HouseRuleCoverage:
    """Each B6 doctrine fires through an already-shipped RuleRecord."""

    def test_b6_1_mars_in_7th_fires_planet_rule(self):
        """B6.1: Aries Lagna, Mars in the 7th (Libra) → H7.P.Mars (HTJAH-II:532)
        fires — the 'clashes/tensions/two wives' dictum HTJAH-I:8170 restates."""
        chart = _chart({"Mars": 185.0}, 5.0)
        assert _RULES["H7.P.Mars"].fires(chart) is True

    def test_b6_1_mars_in_7th_partitions_into_other_submatters(self):
        """B6.1: the SAME Mars-in-7th placement also drives marital_happiness
        (Kuja-Dosha H7.KD.1, HTJAH-II:2579) and coverture (H7.C.60, HTJAH-II:913).
        It is partitioned across sub-matters by signification, so a duplicate
        spouse-tagged rule would double-count in the spouse preponderance."""
        chart = _chart({"Mars": 185.0}, 5.0)
        assert _RULES["H7.KD.1"].fires(chart) is True
        assert _RULES["H7.C.60"].fires(chart) is True

    def test_b6_2_fourth_lord_in_12_property_loss_via_bridge(self):
        """B6.2: Aries Lagna, 4th lord (Moon) in the 12th (Pisces) → the property-loss
        doctrine (HPA-19:247 / HTJAH-I:4187) is carried into the `property` verdict by
        the mother_home BRIDGE rule H4.L.12. H4.C.3 (HTJAH-I:4208) is DESCRIPTIVE since
        the 2026-06-25 de-dup — it documents the same dusthana-lord property loss but does
        NOT fire, so the placement is not double-counted in the property preponderance."""
        chart = _chart({"Moon": 340.0}, 5.0)
        assert _RULES["H4.L.12"].fires(chart) is True
        assert _RULES["H4.C.3"].kind == "descriptive"
        assert _RULES["H4.C.3"].fires(chart) is False

    def test_b6_3_dual_sign_seventh_and_venus_fires_multiplicity(self):
        """B6.3: Sagittarius Lagna (7th sign = Gemini, a common/dual sign) with
        Venus also in a dual sign (Gemini) → H7.C.38 (HTJAH-II:484, the exact
        source the backlog names) fires — the ≥2-marriages dual-sign signature."""
        chart = _chart({"Venus": 75.0}, 245.0)
        assert _RULES["H7.C.38"].fires(chart) is True

    def test_b6_3_h7c38_keys_on_seventh_sign_not_seventh_lord(self):
        """B6.3 boundary: H7.C.38 keys on the 7th SIGN being dual, NOT the 7th
        LORD sitting in a dual sign (the reviewer's geometric distinction).
        Aries Lagna (7th sign = Libra, NOT dual) with Venus in a dual sign →
        H7.C.38 does NOT fire; the 7th-lord-in-dual refinement stays text-only."""
        chart = _chart({"Venus": 75.0}, 5.0)
        assert _RULES["H7.C.38"].fires(chart) is False

    def test_b6_no_duplicate_mars_in_7th_spouse_rule(self):
        """Guard against re-adding B6.1 as a duplicate: on a bare Mars-in-7th
        chart exactly one spouse-tagged evaluable rule fires (H7.P.Mars). A second
        rule keyed on the same placement would double-count in the spouse
        preponderance, since the judge dedups by rule.id, not by placement."""
        chart = _chart({"Mars": 185.0}, 5.0)
        fired = {r.id for r in _RULES.values()
                 if r.signification == "spouse" and r.fires(chart)}
        assert fired == {"H7.P.Mars"}
