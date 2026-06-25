"""Layer-A `degree` (strong/moderate/mild) — the deterministic verdict intensity.

`_compute_degree` surfaces the gradation the engine already computes (pillar count,
decisive/veto flags, marginal-shift) as strong/moderate/mild, giving verdict x degree =
7 graded output states WITHOUT changing the verdict bucket. Each test states the rule.
"""
from __future__ import annotations

from app.raman_saab.judges import house_template as ht


def _ledger(*, lord_strong=None, karaka_strong=None, bhava_strong=None,
            navamsa="neutral", karaka_intact=True, fired_malefic=()):
    """A minimal FrameLedger with the fields _compute_degree reads."""
    return ht.FrameLedger(
        frame="lagna", lord="Sun", lord_strong=lord_strong, karaka="Mars",
        karaka_strong=karaka_strong, bhava_bala=None, bhava_bala_strong=bhava_strong,
        navamsa_status=navamsa, karaka_intact=karaka_intact, maraka_active=False,
        parivartana_resilient=False, lord_karaka_identical=False,
        fired_benefic=(), fired_malefic=fired_malefic, fired_neutral=())


def test_insufficient_evidence_is_mild():
    """No evidence to grade -> mild."""
    assert ht._compute_degree("insufficient-evidence", _ledger(), False) == "mild"


def test_marginal_shift_is_mild():
    """A verdict nudged at the margin (navamsa / relief floor) -> mild, regardless of pillars."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=True)
    assert ht._compute_degree("favourable", led, True) == "mild"


def test_favourable_all_pillars_confirmed_is_strong():
    """Favourable with all known pillars strong + navamsa confirms -> strong."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=True, navamsa="confirms")
    assert ht._compute_degree("favourable", led, False) == "strong"


def test_favourable_two_strong_is_strong():
    """Favourable with a 2+ strong-pillar majority -> strong."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=False)
    assert ht._compute_degree("favourable", led, False) == "strong"


def test_favourable_one_strong_is_moderate():
    """Favourable resting on a single strong pillar (no majority) -> moderate."""
    led = _ledger(lord_strong=True, karaka_strong=None, bhava_strong=None)
    assert ht._compute_degree("favourable", led, False) == "moderate"


def test_afflicted_all_pillars_weak_is_strong():
    """Afflicted with all known pillars weak -> strong."""
    led = _ledger(lord_strong=False, karaka_strong=False, bhava_strong=False)
    assert ht._compute_degree("afflicted", led, False) == "strong"


def test_afflicted_broken_karaka_is_strong():
    """Afflicted via a broken karaka (veto) -> strong, even without weak pillars."""
    led = _ledger(lord_strong=True, karaka_intact=False)
    assert ht._compute_degree("afflicted", led, False) == "strong"


def test_afflicted_one_weak_amid_strong_is_moderate():
    """Afflicted on a single weak pillar amid a strong one (not all-weak, no >=2 weak,
    no decisive flag) -> moderate."""
    led = _ledger(lord_strong=False, karaka_strong=True, bhava_strong=None)
    assert ht._compute_degree("afflicted", led, False) == "moderate"


def test_mixed_is_moderate():
    """Mixed is the genuine middle -> moderate (mild only when shifted)."""
    led = _ledger(lord_strong=True, karaka_strong=False)
    assert ht._compute_degree("mixed", led, False) == "moderate"


# --- Avastha deepening (Layer A) -------------------------------------------------

class _StubPos:
    def __init__(self, sign: int, lon: float) -> None:
        self.sign, self.lon = sign, lon


class _StubChart:
    def __init__(self, planets: dict) -> None:
        self.planets = planets


_ALL_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def test_avastha_score_clamped_sum():
    """A planet's avastha score is the baladi+jagradadi sum clamped to {-1,0,+1}."""
    assert ht._planet_avastha_score({"Saturn": {"baladi": "Mrita", "jagradadi": "Sushupti"}}, "Saturn") == -1  # -2 -> -1
    assert ht._planet_avastha_score({"Saturn": {"baladi": "Mrita", "jagradadi": "Jagrad"}}, "Saturn") == 0     # -1+1
    assert ht._planet_avastha_score({"Jupiter": {"baladi": "Yuva", "jagradadi": "Jagrad"}}, "Jupiter") == 1    # +2 -> +1
    assert ht._planet_avastha_score({"Sun": {"baladi": "Kumara", "jagradadi": "Swapna"}}, "Sun") == 0          # 0+0


def test_avastha_score_absent_is_zero():
    """Absent planet or unavailable avasthas -> 0 (graceful, no pull)."""
    assert ht._planet_avastha_score(None, "Sun") == 0
    assert ht._planet_avastha_score({}, "Sun") == 0


def test_avastha_combined_min_weakest_deliverer():
    """combined = min(lord, karaka): a strong karaka cannot rescue a Mrita+Sushupti lord."""
    av = {"Sun": {"baladi": "Mrita", "jagradadi": "Sushupti"},
          "Jupiter": {"baladi": "Yuva", "jagradadi": "Jagrad"}}
    assert ht._avastha_combined(av, "Sun", "Jupiter") == -1   # min(-1, +1) -> demote
    assert ht._avastha_combined(av, "Jupiter", "Jupiter") == 1  # min(+1, +1) -> promote


def test_compute_degree_avastha_demotes_one_step():
    """A net-weak deliverer avastha (av_adjust=-1) drops the degree one step (strong->moderate)."""
    led = _ledger(lord_strong=True, karaka_strong=True, navamsa="confirms")  # base strong
    assert ht._compute_degree("favourable", led, False, av_adjust=0) == "strong"
    assert ht._compute_degree("favourable", led, False, av_adjust=-1) == "moderate"


def test_compute_degree_avastha_promotes_moderate_to_strong():
    """Both deliverers strong (av_adjust=+1) lift a moderate to strong; a mild/shifted verdict
    is NOT promoted (its margin dominates)."""
    led = _ledger(lord_strong=True)  # one strong pillar -> base moderate
    assert ht._compute_degree("favourable", led, False, av_adjust=0) == "moderate"
    assert ht._compute_degree("favourable", led, False, av_adjust=1) == "strong"
    assert ht._compute_degree("favourable", led, True, av_adjust=1) == "mild"  # shifted stays mild


def test_compute_degree_avastha_floors_at_mild():
    """Demotion never goes below mild; mild/insufficient-evidence stay mild."""
    led = _ledger(lord_strong=True, karaka_strong=False)  # mixed base -> moderate
    assert ht._compute_degree("mixed", led, False, av_adjust=-1) == "mild"
    assert ht._compute_degree("insufficient-evidence", led, False, av_adjust=-1) == "mild"


def test_safe_avasthas_missing_graha_returns_none():
    """A chart missing grahas (Track-B book chart) -> None, never a crash (mandatory guard)."""
    ch = _StubChart({"Sun": _StubPos(1, 10.0), "Moon": _StubPos(2, 20.0)})  # only 2 of 9
    assert ht._safe_avasthas(ch) is None


def test_safe_avasthas_full_chart_ok():
    """A chart with all 9 grahas yields per-planet avastha dicts."""
    ch = _StubChart({g: _StubPos(1, 10.0) for g in _ALL_GRAHAS})
    av = ht._safe_avasthas(ch)
    assert av is not None and "Sun" in av and "baladi" in av["Sun"]
