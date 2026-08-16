"""Per-sign affliction sub-rules S1-S9 (house_01_lagna.sign_afflictions).

Tests verify:
1. Every citation resolves to a real on-disk corpus line.
2. Every rule is evaluable and has a non-None condition.
3. All-True self-verification: a chart that satisfies each rule's full
   And(LagnaInSign, <affliction>) condition fires the rule.
4. Lagna-guard: a chart satisfying the affliction but with the wrong rising
   sign does NOT fire.

Chart construction helper mirrors the pattern used throughout the doctrine
test suite: ``RamanChart.from_stated_positions`` with an explicit ``asc_lon``
to set the rising sign.

asc_lon ranges (sidereal, 1-indexed):
    sign 1  (Aries)      0 –  30 °
    sign 3  (Gemini)    60 –  90 °
    sign 6  (Virgo)    150 – 180 °
    sign 10 (Capricorn) 270 – 300 °
    sign 11 (Aquarius)  300 – 330 °
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_01_lagna import sign_afflictions
from app.raman_saab.doctrine.sources import verify
from corpus_presence import needs_corpus


# ── helpers ───────────────────────────────────────────────────────────────────

def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    """Minimal stated-position chart with given planetary longitudes and asc_lon."""
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


# Sign-specific asc_lon values (mid-sign, well within the range):
_ARIES_ASC = 15.0       # sign 1
_TAURUS_ASC = 45.0      # sign 2  (wrong-sign decoy)
_GEMINI_ASC = 75.0      # sign 3
_VIRGO_ASC = 165.0      # sign 6
_CAPRICORN_ASC = 285.0  # sign 10
_AQUARIUS_ASC = 315.0   # sign 11

# A natural malefic longitude that lands in the 1st house for any of the above
# ascendants: place the malefic in the same sign as the ascendant (mid-sign).
# We use Mars lon = asc_lon + 5 so it is always in the same sign.

# For S2: Saturn AND Moon both in Aries (house 1).
# For S6: Saturn combust = within 15° of Sun; debilitated Saturn = sign 1 (Aries)
#         but that's not Capricorn-lagna context — use combust for tractability:
#         Sun at 280°, Saturn at 285° (within orb, sign 10 = Capricorn for Capricorn lagna).
# For S7: Mars NOT in own sign = Mars in Gemini (sign 3, lon ~75°) with Capricorn lagna.
# For S9: Saturn in 4th from Aquarius lagna (sign 11 = Aquarius, 4th = Taurus = sign 2).


# ── citation and structural tests ─────────────────────────────────────────────

@needs_corpus
@pytest.mark.parametrize("rule", list(sign_afflictions.RULES), ids=lambda r: r.id)
def test_citation_resolves(rule):
    """Every S-rule cites a real on-disk corpus line."""
    assert verify(rule.source), (
        f"{rule.id} cites {rule.source} which does not resolve on disk"
    )


@pytest.mark.parametrize("rule", list(sign_afflictions.RULES), ids=lambda r: r.id)
def test_all_rules_are_evaluable_with_condition(rule):
    """All sign-affliction rules are evaluable and carry a non-None condition."""
    assert rule.kind == "evaluable", f"{rule.id}: expected kind='evaluable', got {rule.kind!r}"
    assert rule.condition is not None, f"{rule.id}: evaluable rule has no condition"


@pytest.mark.parametrize("rule", list(sign_afflictions.RULES), ids=lambda r: r.id)
def test_group_is_sign_affliction(rule):
    """All rules carry group='sign_affliction'."""
    assert rule.group == "sign_affliction", (
        f"{rule.id}: expected group='sign_affliction', got {rule.group!r}"
    )


@pytest.mark.parametrize("rule", list(sign_afflictions.RULES), ids=lambda r: r.id)
def test_signification_is_self(rule):
    """All rules carry signification='self' (1st-house self/body signification)."""
    assert rule.signification == "self", (
        f"{rule.id}: expected signification='self', got {rule.signification!r}"
    )


# ── all-True self-verification (fires on a matching chart) ───────────────────

def test_s1_aries_afflicted_fires():
    """S1: Aries lagna + malefic in 1st → head diseases rule fires."""
    # Mars at 20° (Aries = house 1), Aries ascendant.
    chart = _chart({"Mars": 20.0}, asc_lon=_ARIES_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.1")
    assert rule.fires(chart) is True


def test_s1_wrong_lagna_does_not_fire():
    """S1: malefic in 1st but Taurus lagna → does not fire."""
    chart = _chart({"Mars": 50.0}, asc_lon=_TAURUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.1")
    assert rule.fires(chart) is False


def test_s2_saturn_moon_in_aries_fires():
    """S2: Aries lagna + Saturn in Aries + Moon in Aries → derangement fires."""
    chart = _chart({"Saturn": 10.0, "Moon": 20.0}, asc_lon=_ARIES_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.2")
    assert rule.fires(chart) is True


def test_s2_saturn_only_does_not_fire():
    """S2: Saturn in Aries but Moon absent → does not fire."""
    chart = _chart({"Saturn": 10.0}, asc_lon=_ARIES_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.2")
    assert rule.fires(chart) is False


def test_s2_wrong_lagna_does_not_fire():
    """S2: Saturn+Moon in 1st but Gemini lagna (sign 3) → does not fire."""
    # Gemini lagna at 75°, Saturn and Moon also in Gemini (sign 3).
    chart = _chart({"Saturn": 76.0, "Moon": 78.0}, asc_lon=_GEMINI_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.2")
    assert rule.fires(chart) is False


def test_s3_evil_in_gemini_fires():
    """S3: Gemini lagna + malefic in 1st → trickery/deceit fires."""
    chart = _chart({"Saturn": 80.0}, asc_lon=_GEMINI_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.3")
    assert rule.fires(chart) is True


def test_s3_wrong_lagna_does_not_fire():
    """S3: malefic in 1st but Aries lagna → does not fire."""
    chart = _chart({"Saturn": 20.0}, asc_lon=_ARIES_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.3")
    assert rule.fires(chart) is False


def test_s4_virgo_afflicted_fires():
    """S4: Virgo lagna + malefic in 1st → chest weak fires."""
    chart = _chart({"Mars": 160.0}, asc_lon=_VIRGO_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.4")
    assert rule.fires(chart) is True


def test_s4_no_malefic_does_not_fire():
    """S4: Virgo lagna, only benefic in 1st → does not fire."""
    chart = _chart({"Venus": 160.0}, asc_lon=_VIRGO_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.4")
    assert rule.fires(chart) is False


def test_s5_virgo_afflicted_fires():
    """S5: Virgo lagna + malefic in 1st → nervous breakdowns/paralysis fires."""
    chart = _chart({"Saturn": 160.0}, asc_lon=_VIRGO_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.5")
    assert rule.fires(chart) is True


def test_s5_wrong_lagna_does_not_fire():
    """S5: malefic in 1st but Gemini lagna → does not fire."""
    chart = _chart({"Saturn": 80.0}, asc_lon=_GEMINI_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.5")
    assert rule.fires(chart) is False


def test_s6_saturn_afflicted_capricorn_fires():
    """S6: Capricorn lagna + Saturn debilitated (Aries, sign 1) → vindictive fires.

    ``from_stated_positions`` does not populate ``combust_fraction``, so the
    combustion branch is not testable here.  Use the debilitation branch instead:
    Saturn in Aries (sign 1) = Saturn's debilitation sign per classical table
    (exaltation Libra/sign 7 → debilitation opposite = Aries/sign 1).
    """
    # Saturn at 15° = Aries (sign 1) = debilitated; Capricorn lagna.
    chart = _chart({"Saturn": 15.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.6")
    assert rule.fires(chart) is True


def test_s6_saturn_clean_does_not_fire():
    """S6: Capricorn lagna + Saturn not afflicted → does not fire."""
    # Saturn in Capricorn (own sign = dignity 'own', not combust, not hemmed).
    # Sun far away so no combustion; no malefics flanking Saturn.
    chart = _chart({"Saturn": 285.0, "Sun": 15.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.6")
    assert rule.fires(chart) is False


def test_s6_wrong_lagna_does_not_fire():
    """S6: Saturn combust but Aquarius lagna → does not fire."""
    chart = _chart({"Sun": 315.0, "Saturn": 318.0}, asc_lon=_AQUARIUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.6")
    assert rule.fires(chart) is False


def test_s7_mars_not_in_own_sign_fires():
    """S7: Capricorn lagna + Mars in Gemini (not Aries/Scorpio) → lack-confidence fires."""
    # Mars at 75° = Gemini (sign 3), not his own sign.
    chart = _chart({"Mars": 75.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.7")
    assert rule.fires(chart) is True


def test_s7_mars_in_aries_does_not_fire():
    """S7: Capricorn lagna + Mars in Aries (own sign) → does not fire."""
    chart = _chart({"Mars": 15.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.7")
    assert rule.fires(chart) is False


def test_s7_mars_in_scorpio_does_not_fire():
    """S7: Capricorn lagna + Mars in Scorpio (own sign) → does not fire."""
    chart = _chart({"Mars": 225.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.7")
    assert rule.fires(chart) is False


def test_s7_wrong_lagna_does_not_fire():
    """S7: Mars not in own sign but Aries lagna → does not fire."""
    chart = _chart({"Mars": 75.0}, asc_lon=_ARIES_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.7")
    assert rule.fires(chart) is False


def test_s8_aquarius_afflicted_fires():
    """S8: Aquarius lagna + malefic in 1st → fails-as-teacher fires."""
    chart = _chart({"Saturn": 310.0}, asc_lon=_AQUARIUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.8")
    assert rule.fires(chart) is True


def test_s8_no_malefic_does_not_fire():
    """S8: Aquarius lagna, only benefic in 1st → does not fire (sign is free from affliction)."""
    chart = _chart({"Jupiter": 310.0}, asc_lon=_AQUARIUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.8")
    assert rule.fires(chart) is False


def test_s9_saturn_in_4th_aquarius_fires():
    """S9: Aquarius lagna + Saturn in 4th (Taurus) → chest-weak fires."""
    # Aquarius lagna (sign 11, asc ~315°). 4th whole-sign house = Taurus (sign 2, lon ~30-60°).
    chart = _chart({"Saturn": 45.0}, asc_lon=_AQUARIUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.9")
    assert rule.fires(chart) is True


def test_s9_saturn_not_in_4th_does_not_fire():
    """S9: Aquarius lagna + Saturn in 1st (not 4th) → does not fire."""
    chart = _chart({"Saturn": 310.0}, asc_lon=_AQUARIUS_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.9")
    assert rule.fires(chart) is False


def test_s9_wrong_lagna_does_not_fire():
    """S9: Saturn in 4th house but Capricorn lagna → does not fire."""
    # Capricorn lagna (sign 10). 4th from Capricorn = Aries (sign 1, lon ~0-30°).
    chart = _chart({"Saturn": 15.0}, asc_lon=_CAPRICORN_ASC)
    rule = next(r for r in sign_afflictions.RULES if r.id == "H1.S.9")
    assert rule.fires(chart) is False
