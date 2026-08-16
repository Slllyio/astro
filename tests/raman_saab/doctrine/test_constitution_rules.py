"""Constitution rules H1.B.13-H1.B.19 — self-verify suite.

Each test asserts that the correct chart activates the rule (all-True) and
a counter-example does not (all-False). Citations are validated inline.

Corpus anchor: HTJAH-I:1105-1114.
"""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_01_lagna.constitution import RULES
from app.raman_saab.doctrine.sources import verify


# ── helpers ───────────────────────────────────────────────────────────────────

def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    """Build a minimal chart from stated longitudes and ascendant."""
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


def _rule(rule_id: str):
    """Look up a RuleRecord from the constitution RULES tuple by id."""
    for r in RULES:
        if r.id == rule_id:
            return r
    raise KeyError(f"Rule {rule_id!r} not found in constitution.RULES")


# ── citation guard ────────────────────────────────────────────────────────────

@needs_corpus
@pytest.mark.parametrize("rule", list(RULES), ids=lambda r: r.id)
def test_citation_resolves_on_disk(rule) -> None:
    """Every constitution rule must cite a real on-disk HTJAH-I corpus line."""
    assert verify(rule.source), (
        f"{rule.id} cites {rule.source} which does not resolve on disk"
    )


# ── H1.B.13: Sushka planet in Lagna → lean ───────────────────────────────────
# HTJAH-I:1105 — "If a Sushka (dry) planet occupies the Lagna the person will
# be lean. (Sushka planets are the Sun, Mars and Saturn)."

class TestH1B13SushkaPlanetInLagna:
    """Sushka planet in house 1 fires the lean-constitution rule."""

    def test_sun_in_lagna_fires(self) -> None:
        """Sun (a Sushka planet) in Lagna activates H1.B.13."""
        rule = _rule("H1.B.13")
        # Aries Lagna (asc_lon=0); Sun at 5° = Aries = house 1
        assert rule.fires(_chart({"Sun": 5.0}, asc_lon=0.0)) is True

    def test_mars_in_lagna_fires(self) -> None:
        """Mars (a Sushka planet) in Lagna activates H1.B.13."""
        rule = _rule("H1.B.13")
        assert rule.fires(_chart({"Mars": 15.0}, asc_lon=0.0)) is True

    def test_saturn_in_lagna_fires(self) -> None:
        """Saturn (a Sushka planet) in Lagna activates H1.B.13."""
        rule = _rule("H1.B.13")
        assert rule.fires(_chart({"Saturn": 25.0}, asc_lon=0.0)) is True

    def test_benefic_only_in_lagna_does_not_fire(self) -> None:
        """Jupiter in Lagna (not a Sushka planet) does not activate H1.B.13."""
        rule = _rule("H1.B.13")
        assert rule.fires(_chart({"Jupiter": 10.0}, asc_lon=0.0)) is False

    def test_sushka_planet_in_other_house_does_not_fire(self) -> None:
        """Sun in the 2nd house does not activate H1.B.13."""
        rule = _rule("H1.B.13")
        # Aries Lagna; Sun at 35° = Taurus = house 2
        assert rule.fires(_chart({"Sun": 35.0}, asc_lon=0.0)) is False


# ── H1.B.14: Sushka rasi rising → emaciated ──────────────────────────────────
# HTJAH-I:1106 — "If the ascendant falls in any of the Sushka Rashis (signs
# owned by Mars, Saturn and the Sun) the body will be emanciated."
# Sushka rasis: Aries (1), Leo (5), Scorpio (8), Capricorn (10), Aquarius (11).

class TestH1B14SushkaRasiRising:
    """Sushka rasi on the ascendant fires the emaciated-body rule."""

    def test_aries_lagna_fires(self) -> None:
        """Aries (sign 1) is a Sushka rasi — H1.B.14 fires."""
        rule = _rule("H1.B.14")
        # asc_lon=0 → sign 1 (Aries)
        assert rule.fires(_chart({}, asc_lon=0.0)) is True

    def test_leo_lagna_fires(self) -> None:
        """Leo (sign 5, owned by the Sun) is a Sushka rasi — H1.B.14 fires."""
        rule = _rule("H1.B.14")
        # asc_lon=120° → sign 5 (Leo)
        assert rule.fires(_chart({}, asc_lon=120.0)) is True

    def test_scorpio_lagna_fires(self) -> None:
        """Scorpio (sign 8, owned by Mars) is a Sushka rasi — H1.B.14 fires."""
        rule = _rule("H1.B.14")
        # asc_lon=210° → sign 8 (Scorpio)
        assert rule.fires(_chart({}, asc_lon=210.0)) is True

    def test_capricorn_lagna_fires(self) -> None:
        """Capricorn (sign 10, owned by Saturn) is a Sushka rasi — H1.B.14 fires."""
        rule = _rule("H1.B.14")
        # asc_lon=270° → sign 10 (Capricorn)
        assert rule.fires(_chart({}, asc_lon=270.0)) is True

    def test_aquarius_lagna_fires(self) -> None:
        """Aquarius (sign 11, owned by Saturn) is a Sushka rasi — H1.B.14 fires."""
        rule = _rule("H1.B.14")
        # asc_lon=300° → sign 11 (Aquarius)
        assert rule.fires(_chart({}, asc_lon=300.0)) is True

    def test_taurus_lagna_does_not_fire(self) -> None:
        """Taurus (sign 2, owned by Venus) is not a Sushka rasi — H1.B.14 does not fire."""
        rule = _rule("H1.B.14")
        # asc_lon=30° → sign 2 (Taurus)
        assert rule.fires(_chart({}, asc_lon=30.0)) is False

    def test_cancer_lagna_does_not_fire(self) -> None:
        """Cancer (sign 4, watery) is not a Sushka rasi — H1.B.14 does not fire."""
        rule = _rule("H1.B.14")
        # asc_lon=90° → sign 4 (Cancer)
        assert rule.fires(_chart({}, asc_lon=90.0)) is False


# ── H1.B.15: Lord of Lagna conjunct Sushka planet → lean/emaciated ───────────
# HTJAH-I:1107 — "If the lord of the Lagna is in conjunction with Sushka
# planets then also similar results will follow."

class TestH1B15LagnaLordConjunctSushka:
    """Lagna-lord sharing a rasi with a Sushka planet fires H1.B.15."""

    def test_cancer_lagna_moon_with_mars_fires(self) -> None:
        """Cancer Lagna (lord=Moon); Moon conjunct Mars (Sushka) → fires."""
        rule = _rule("H1.B.15")
        # asc_lon=90° → sign 4 (Cancer); Moon at 95° = Cancer; Mars at 91° = Cancer
        assert rule.fires(_chart({"Moon": 95.0, "Mars": 91.0}, asc_lon=90.0)) is True

    def test_taurus_lagna_venus_with_saturn_fires(self) -> None:
        """Taurus Lagna (lord=Venus); Venus conjunct Saturn (Sushka) → fires."""
        rule = _rule("H1.B.15")
        # asc_lon=30° → sign 2 (Taurus); Venus at 40°=Taurus; Saturn at 45°=Taurus
        assert rule.fires(_chart({"Venus": 40.0, "Saturn": 45.0}, asc_lon=30.0)) is True

    def test_gemini_lagna_mercury_with_sun_fires(self) -> None:
        """Gemini Lagna (lord=Mercury); Mercury conjunct Sun (Sushka) → fires."""
        rule = _rule("H1.B.15")
        # asc_lon=60° → sign 3 (Gemini); Mercury at 65°=Gemini; Sun at 70°=Gemini
        assert rule.fires(_chart({"Mercury": 65.0, "Sun": 70.0}, asc_lon=60.0)) is True

    def test_lagna_lord_alone_does_not_fire(self) -> None:
        """Cancer Lagna; Moon alone in Cancer with no Sushka planet → does not fire."""
        rule = _rule("H1.B.15")
        # Moon at 95°=Cancer, no Sushka planet in same sign
        assert rule.fires(_chart({"Moon": 95.0, "Jupiter": 100.0}, asc_lon=90.0)) is False

    def test_sushka_planet_different_sign_does_not_fire(self) -> None:
        """Cancer Lagna; Moon in Cancer, Mars in Leo (different sign) → does not fire."""
        rule = _rule("H1.B.15")
        assert rule.fires(_chart({"Moon": 95.0, "Mars": 125.0}, asc_lon=90.0)) is False


# ── H1.B.16: Watery rasi rising with good planets → corpulent ────────────────
# HTJAH-I:1108 — "He will be corpulent if ascendant be Cancer, Scorpio, or
# Pisces with good planets."

class TestH1B16WateryRasiWithBenefics:
    """Watery Lagna with a benefic in house 1 fires H1.B.16."""

    def test_cancer_lagna_jupiter_in_lagna_fires(self) -> None:
        """Cancer Lagna + Jupiter in house 1 → corpulent (H1.B.16 fires)."""
        rule = _rule("H1.B.16")
        # asc_lon=90° → Cancer; Jupiter at 95° → house 1
        assert rule.fires(_chart({"Jupiter": 95.0}, asc_lon=90.0)) is True

    def test_scorpio_lagna_venus_in_lagna_fires(self) -> None:
        """Scorpio Lagna + Venus in house 1 → fires."""
        rule = _rule("H1.B.16")
        # asc_lon=210° → Scorpio; Venus at 215° → house 1
        assert rule.fires(_chart({"Venus": 215.0}, asc_lon=210.0)) is True

    def test_pisces_lagna_moon_in_lagna_fires(self) -> None:
        """Pisces Lagna + Moon in house 1 → fires."""
        rule = _rule("H1.B.16")
        # asc_lon=330° → Pisces; Moon at 335° → house 1
        assert rule.fires(_chart({"Moon": 335.0}, asc_lon=330.0)) is True

    def test_watery_lagna_malefic_only_does_not_fire(self) -> None:
        """Cancer Lagna + Saturn only (no benefic in house 1) → does not fire."""
        rule = _rule("H1.B.16")
        assert rule.fires(_chart({"Saturn": 95.0}, asc_lon=90.0)) is False

    def test_benefic_in_lagna_but_non_watery_sign_does_not_fire(self) -> None:
        """Aries Lagna (not watery) + Jupiter in house 1 → does not fire."""
        rule = _rule("H1.B.16")
        assert rule.fires(_chart({"Jupiter": 5.0}, asc_lon=0.0)) is False


# ── H1.B.17: Ascendant lord is watery planet → stout ─────────────────────────
# HTJAH-I:1109 — "If the ascendant lord is a watery planet (Venus and the Moon),
# strong and well conjoined, the native becomes stout."

class TestH1B17LagnaLordIsWatery:
    """Lagna whose lord is Venus or Moon fires H1.B.17."""

    def test_cancer_lagna_lord_moon_fires(self) -> None:
        """Cancer Lagna (lord=Moon) is a watery-lord Lagna → H1.B.17 fires."""
        rule = _rule("H1.B.17")
        # asc_lon=90° → Cancer; Moon lord present somewhere
        assert rule.fires(_chart({"Moon": 185.0}, asc_lon=90.0)) is True

    def test_taurus_lagna_lord_venus_fires(self) -> None:
        """Taurus Lagna (lord=Venus) → H1.B.17 fires."""
        rule = _rule("H1.B.17")
        assert rule.fires(_chart({"Venus": 40.0}, asc_lon=30.0)) is True

    def test_libra_lagna_lord_venus_fires(self) -> None:
        """Libra Lagna (lord=Venus) → H1.B.17 fires."""
        rule = _rule("H1.B.17")
        # asc_lon=180° → Libra
        assert rule.fires(_chart({"Venus": 200.0}, asc_lon=180.0)) is True

    def test_aries_lagna_lord_mars_does_not_fire(self) -> None:
        """Aries Lagna (lord=Mars, not watery) → H1.B.17 does not fire."""
        rule = _rule("H1.B.17")
        assert rule.fires(_chart({"Mars": 10.0}, asc_lon=0.0)) is False

    def test_capricorn_lagna_lord_saturn_does_not_fire(self) -> None:
        """Capricorn Lagna (lord=Saturn, not watery) → H1.B.17 does not fire."""
        rule = _rule("H1.B.17")
        assert rule.fires(_chart({"Saturn": 280.0}, asc_lon=270.0)) is False


# ── H1.B.18: Benefic-owned Lagna AND D9-lord of Lagna-lord in watery sign ────
# HTJAH-I:1110 — "Corpulence can also be predicted if the Lagna is owned by a
# benefice and if the lord of the Navamsha occupied by the lord of Lagna
# occupies a watery sign."

class TestH1B18BeneficLagnaNavamshaWatery:
    """Benefic-owned Lagna + D9-navamsha lord of Lagna-lord in watery sign fires H1.B.18."""

    def test_cancer_lagna_moon_in_cancer_navamsa_watery_fires(self) -> None:
        """Cancer Lagna (lord=Moon, a natural benefic); Moon's navamsa-sign lord
        placed in a watery D1 sign → H1.B.18 fires.

        Moon at 90.0° (first degree of Cancer): D1 sign = Cancer (4, watery).
        navamsa_sign(90.0) = 4 (Cancer, Vargottama).
        Lord of navamsa sign 4 (Cancer) = Moon itself.
        Moon's own D1 sign = Cancer (4) → watery → both arms hold → fires.
        """
        rule = _rule("H1.B.18")
        # Cancer Lagna (90°), Moon at exactly 90° → D1 sign=Cancer(4),
        # navamsa_sign=4 (Cancer), lord of navamsa=Moon, Moon D1 sign=Cancer=watery.
        assert rule.fires(_chart({"Moon": 90.0}, asc_lon=90.0)) is True

    def test_malefic_owned_lagna_does_not_fire(self) -> None:
        """Aries Lagna (lord=Mars, not a benefic) → H1.B.18 does not fire
        regardless of D9 placement."""
        rule = _rule("H1.B.18")
        assert rule.fires(_chart({"Mars": 5.0}, asc_lon=0.0)) is False

    def test_benefic_lagna_but_navamsha_lord_not_watery_does_not_fire(self) -> None:
        """Gemini Lagna (lord=Mercury, benefic); Mercury's navamsa sign lord
        placed in a non-watery sign → H1.B.18 does not fire.

        Mercury at 65° (Gemini); navamsa of 65° = sign 3 (Gemini).
        Lord of navamsa-sign Gemini = Mercury itself.
        Mercury's D1 sign = Gemini (3), not watery → does not fire.
        """
        rule = _rule("H1.B.18")
        # Gemini Lagna (60°), Mercury at 65° in Gemini, navamsa in Gemini (3), not watery
        assert rule.fires(_chart({"Mercury": 65.0}, asc_lon=60.0)) is False


# ── H1.B.19: Jupiter in Lagna / Jupiter aspects from watery sign / watery+benefic ─
# HTJAH-I:1112 — "If Jupiter occupies Lagna or if Jupiter aspects Lagna from a
# watery sign or if the Lagna happens to be a watery sign with benefices in it
# then also the body will be stout."

class TestH1B19JupiterOrWateryBenefic:
    """Three disjunctive arms of the stout-body rule each independently fire H1.B.19."""

    def test_jupiter_in_lagna_fires(self) -> None:
        """Arm 1: Jupiter in house 1 → H1.B.19 fires."""
        rule = _rule("H1.B.19")
        # Aries Lagna; Jupiter at 10° = house 1
        assert rule.fires(_chart({"Jupiter": 10.0}, asc_lon=0.0)) is True

    def test_jupiter_aspects_lagna_from_watery_sign_fires(self) -> None:
        """Arm 2: Jupiter in watery sign, its 7th aspect reaches the Lagna → fires.

        Aries Lagna (sign 1). Jupiter in Libra (sign 7, house 7 from Aries).
        Libra is not watery (signs 4/8/12 are watery).
        Use Cancer (sign 4, house 4 from Aries) for Jupiter:
        Jupiter's special 10th aspect from Cancer: 4+9-1=12 → Pisces ≠ Aries.
        Jupiter's 5th aspect from Cancer: 4+4=8 → Scorpio ≠ Aries.
        Jupiter's 7th aspect from Cancer (4+6=10) → Capricorn ≠ Aries.

        Try Jupiter in Scorpio (sign 8, watery, house 8).
        Jupiter's 7th aspect: 8+6=14 → 14-12=2 → Taurus ≠ Aries.
        Jupiter's 5th: 8+4=12 → Pisces ≠ Aries.
        Jupiter's 9th: 8+8=16 → 4 → Cancer ≠ Aries.

        Try Pisces (sign 12, watery, house 12 from Aries).
        Jupiter's 7th: 12+6=18 → 6 → Virgo ≠ Aries.
        Jupiter's 5th: 12+4=16 → 4 → Cancer ≠ Aries.
        Jupiter's 9th: 12+8=20 → 8 → Scorpio ≠ Aries.

        Use Sagittarius Lagna (sign 9, asc_lon=240°).
        Jupiter in Cancer (sign 4, watery). From sign 4:
        5th aspect: 4+4=8 → Scorpio; 7th: 4+6=10 → Capricorn; 9th: 4+8=12 → Pisces.
        None reach Sagittarius (9).

        Use Virgo Lagna (sign 6, asc_lon=150°). Jupiter in Pisces (sign 12, watery).
        7th from Pisces: 12+6=18-12=6 → Virgo ✓  Fires!
        """
        rule = _rule("H1.B.19")
        # Virgo Lagna (asc_lon=150°), Jupiter in Pisces (325° = sign 11 → wrong)
        # Pisces = signs 330-360, so 335° gives sign 12 (Pisces)
        assert rule.fires(_chart({"Jupiter": 335.0}, asc_lon=150.0)) is True

    def test_jupiter_aspects_lagna_non_watery_does_not_fire_arm2(self) -> None:
        """Arm 2 alone: Jupiter in non-watery sign aspecting Lagna → does NOT fire
        (unless arm 1 or arm 3 also fires)."""
        rule = _rule("H1.B.19")
        # Virgo Lagna (150°); Jupiter in Pisces but with malefic sign as lagna check:
        # Need Jupiter to aspect Lagna but NOT be in a watery sign.
        # Jupiter in Virgo (150°, sign 6, not watery) aspects Pisces (7th from Virgo).
        # With Pisces Lagna (330°) Jupiter at 150° (Virgo, house 4 from Pisces) →
        # Jupiter's 10th aspect: 6+9=15-12=3 → Gemini ≠ Pisces.
        # Use: Aries Lagna, Jupiter in Libra (sign 7, not watery).
        # Jupiter's 7th from Libra = Aries ✓ — but Libra is not watery, arm2 fails.
        # Arm 1: Jupiter not in house 1. Arm 3: Aries not watery. → should not fire.
        assert rule.fires(_chart({"Jupiter": 185.0}, asc_lon=0.0)) is False

    def test_watery_lagna_with_mercury_fires(self) -> None:
        """Arm 3: Cancer Lagna + Mercury in house 1 → fires."""
        rule = _rule("H1.B.19")
        # Cancer Lagna (90°), Mercury at 92° → house 1 (Cancer)
        assert rule.fires(_chart({"Mercury": 92.0}, asc_lon=90.0)) is True

    def test_no_arm_fires_returns_false(self) -> None:
        """No arm active: Aries Lagna (non-watery), no Jupiter in house 1,
        no Jupiter in watery sign → H1.B.19 does not fire."""
        rule = _rule("H1.B.19")
        # Aries Lagna; Mars in house 1 only — no Jupiter at all
        assert rule.fires(_chart({"Mars": 5.0}, asc_lon=0.0)) is False
