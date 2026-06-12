"""Tests for House 1 Moon/mind rules (moon_mind.py).

Self-verify contract:
  - All citations resolve on disk (via sources.verify).
  - All evaluable rules have a condition.
  - Each per-sign rule fires for the correct Moon sign and not for others.
  - G2 fires only when Sun + Moon + Lagna are each afflicted by ≥2 malefics.
  - G3 fires when Rahu + Ketu are both in node-angle signs and a luminary shares
    one of those signs.
  - MD and G1 are descriptive (condition=None), never fire via .fires().
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_01_lagna import moon_mind
from app.raman_saab.doctrine.sources import verify


# ── helpers ──────────────────────────────────────────────────────────────────

def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    """Build a minimal RamanChart from stated longitudes + ascendant longitude.

    `asc_lon=0.0` = 0° Aries lagna (sign 1, house 1).
    """
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


def _rule(rule_id: str):
    return next(r for r in moon_mind.RULES if r.id == rule_id)


# ── citation integrity ────────────────────────────────────────────────────────

@pytest.mark.parametrize("rule", list(moon_mind.RULES), ids=lambda r: r.id)
def test_every_moon_mind_rule_cites_real_corpus_line(rule):
    """Every RuleRecord must cite a line that exists on disk (HTJAH-I corpus)."""
    assert verify(rule.source), (
        f"{rule.id} cites {rule.source} which does not resolve on disk"
    )


@pytest.mark.parametrize("rule", list(moon_mind.RULES), ids=lambda r: r.id)
def test_evaluable_rules_have_a_condition(rule):
    """Evaluable rules must carry a Condition tree."""
    if rule.kind == "evaluable":
        assert rule.condition is not None, (
            f"{rule.id} is evaluable but condition is None"
        )


@pytest.mark.parametrize("rule", list(moon_mind.RULES), ids=lambda r: r.id)
def test_descriptive_rules_have_no_condition(rule):
    """Descriptive rules must have condition=None."""
    if rule.kind == "descriptive":
        assert rule.condition is None, (
            f"{rule.id} is descriptive but has a condition"
        )


@pytest.mark.parametrize("rule", list(moon_mind.RULES), ids=lambda r: r.id)
def test_all_rules_have_moon_frame(rule):
    """All moon_mind rules carry frame='MOON'."""
    assert rule.frame == "MOON", f"{rule.id} has frame={rule.frame!r}, expected 'MOON'"


@pytest.mark.parametrize("rule", list(moon_mind.RULES), ids=lambda r: r.id)
def test_all_rules_in_moon_mind_group(rule):
    """All rules belong to the 'moon_mind' group."""
    assert rule.group == "moon_mind", (
        f"{rule.id} has group={rule.group!r}, expected 'moon_mind'"
    )


# ── descriptive rules do not fire ─────────────────────────────────────────────

def test_md_is_descriptive_and_does_not_fire():
    """H1.M.MD is descriptive; .fires() is always False for descriptive rules."""
    r = _rule("H1.M.MD")
    assert r.kind == "descriptive"
    assert r.fires(_chart({})) is False


def test_g1_is_descriptive_and_does_not_fire():
    """H1.M.G1 is descriptive; .fires() is always False."""
    r = _rule("H1.M.G1")
    assert r.kind == "descriptive"
    assert r.fires(_chart({})) is False


# ── per-sign Moon rules (S01–S12) ────────────────────────────────────────────

# Each sign's midpoint longitude (0° of sign n = (n-1)*30, midpoint = (n-1)*30+15).
_SIGN_MIDPOINTS = {n: (n - 1) * 30 + 15.0 for n in range(1, 13)}

_SIGN_RULE_IDS = [f"H1.M.S{n:02d}" for n in range(1, 13)]


@pytest.mark.parametrize("rule_id,sign", zip(_SIGN_RULE_IDS, range(1, 13)))
def test_per_sign_rule_fires_for_correct_sign(rule_id: str, sign: int):
    """H1.M.S<n> fires when Moon is in sign n and not in any other sign."""
    r = _rule(rule_id)
    # Moon in the correct sign — fires.
    chart_match = _chart({"Moon": _SIGN_MIDPOINTS[sign]})
    assert r.fires(chart_match) is True, (
        f"{rule_id} should fire with Moon at {_SIGN_MIDPOINTS[sign]}° (sign {sign})"
    )
    # Moon in next sign — does not fire.
    other_sign = (sign % 12) + 1
    chart_no_match = _chart({"Moon": _SIGN_MIDPOINTS[other_sign]})
    assert r.fires(chart_no_match) is False, (
        f"{rule_id} should NOT fire with Moon in sign {other_sign}"
    )


# ── G2: violent/sudden death (Sun+Moon+Lagna all multi-afflicted) ─────────────

def test_g2_fires_when_all_three_afflicted_by_two_malefics():
    """G2 fires when Sun, Moon, and Lagna are each aspected by ≥2 malefics.

    Setup: Aries lagna (asc=0°).
    - Mars at 185° (Libra, 7th house) — 7th-house whole-sign aspects house 1 (Aries).
    - Saturn at 185° (Libra, 7th) — also aspects house 1.
    Both Mars and Saturn aspect the Sun (in house 1), the Moon (in house 1),
    and the Lagna.  Sun and Moon placed at 5° (Aries, house 1).
    """
    r = _rule("H1.M.G2")
    # All three (Sun, Moon, Lagna) in Aries; Mars + Saturn in Libra → 7th aspect on all.
    chart = _chart({"Sun": 5.0, "Moon": 10.0, "Mars": 185.0, "Saturn": 190.0})
    assert r.fires(chart) is True


def test_g2_does_not_fire_with_only_one_malefic_on_moon():
    """G2 does not fire if only one malefic aspects the Moon."""
    r = _rule("H1.M.G2")
    # Only Saturn in 7th aspects Sun/Moon/Lagna — one malefic, not two.
    chart = _chart({"Sun": 5.0, "Moon": 10.0, "Saturn": 185.0})
    assert r.fires(chart) is False


def test_g2_does_not_fire_if_lagna_not_doubly_afflicted():
    """G2 does not fire if Sun and Moon are afflicted but Lagna is not."""
    r = _rule("H1.M.G2")
    # Mars and Saturn both aspect the Moon (placed in 10th / Capricorn).
    # Moon at 275° (Capricorn, house 10); Mars at 95° (Cancer, house 4) aspects house 10;
    # Saturn at 185° (Libra, house 7) aspects house 10 by 4th aspect.
    # But neither aspects Lagna (house 1 = Aries) with two malefics here.
    chart = _chart({"Sun": 5.0, "Moon": 275.0, "Mars": 95.0, "Saturn": 185.0})
    # Sun is in house 1 — Mars (4th) and Saturn (7th) do aspect it, so Sun IS
    # doubly afflicted; Moon at 275° (house 10): Mars (house 4) aspects house 10 (7th
    # aspect from 4), Saturn (house 7) aspects house 10 (4th aspect from 7) — both
    # aspect Moon; Lagna (house 1): Mars in house 4 aspects house 1 (check: 4+4-1=7? no,
    # Mars's special aspects are 4/7/8 from Mars; Mars in house 4 → special aspects on
    # houses 4+4-1=7, 4+7-1=10, 4+8-1=11, standard 7th=house 10 -- but house 1 is NOT
    # among them).  Saturn in house 7 → aspects houses 7+3-1=9, 7+7-1=13=1, 7+10-1=16=4
    # (Saturn's special: 3/7/10 aspect from Saturn's house) → house 1 IS aspected by
    # Saturn.  So only Saturn aspects Lagna → one malefic on Lagna → G2 does NOT fire.
    assert r.fires(chart) is False


# ── G3: Rahu+Ketu in node-angle signs with a luminary ────────────────────────

def test_g3_fires_when_nodes_in_angle_signs_with_luminary():
    """G3 fires when Rahu and Ketu are both in node-angle signs and a luminary shares one.

    Node-angle signs: Aries(1)=0-30°, Taurus(2)=30-60°, Scorpio(8)=210-240°,
    Capricorn(10)=270-300°.
    Rahu at 15° (Aries=1), Ketu at 195° (Libra=7) — Ketu NOT in angle → should not fire.
    Rahu at 15° (Aries=1), Ketu at 215° (Scorpio=8), Moon at 45° (Taurus=2) → fires.
    """
    r = _rule("H1.M.G3")
    # Rahu in Aries (1), Ketu in Scorpio (8), Moon in Taurus (2) — all conditions met.
    chart_fires = _chart({"Rahu": 15.0, "Ketu": 215.0, "Moon": 45.0, "Sun": 100.0})
    assert r.fires(chart_fires) is True

    # Ketu in Libra (7) — not a node-angle sign → does not fire.
    chart_no_ketu = _chart({"Rahu": 15.0, "Ketu": 195.0, "Moon": 45.0, "Sun": 100.0})
    assert r.fires(chart_no_ketu) is False


def test_g3_does_not_fire_without_luminary_in_angle_sign():
    """G3 does not fire if nodes are in angle signs but no luminary is there."""
    r = _rule("H1.M.G3")
    # Rahu in Aries (1), Ketu in Scorpio (8), but Sun and Moon outside angle signs.
    # Sun at 65° (Gemini=3), Moon at 130° (Leo=5) — neither in {1,2,8,10}.
    chart = _chart({"Rahu": 15.0, "Ketu": 215.0, "Sun": 65.0, "Moon": 130.0})
    assert r.fires(chart) is False


def test_g3_fires_with_sun_in_angle_sign():
    """G3 fires when Sun (not Moon) is the luminary in a node-angle sign."""
    r = _rule("H1.M.G3")
    # Rahu in Taurus (2), Ketu in Capricorn (10), Sun in Aries (1).
    chart = _chart({"Rahu": 45.0, "Ketu": 285.0, "Sun": 15.0, "Moon": 130.0})
    assert r.fires(chart) is True
