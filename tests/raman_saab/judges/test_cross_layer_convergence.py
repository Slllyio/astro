"""Cross-layer convergence (Layer 4) — the D1 verdict vs the INDEPENDENT divisional signal.

`varga_judge` derives each varga's confirms/weakens status from the DIVISIONAL chart's own dignities
(NOT from `judge_house` — so it is genuinely independent, avoiding the tautology that every reading
surface's `core.verdict` IS the D1 verdict). This suite measures whether that independent signal
corroborates the D1 rollup of the varga's related house(s), and ratchets it.

HONEST FRAMING (see tools/raman_saab/cross_layer_report.py + the baseline comment): the OVERALL
agreement is only marginally above chance, because the uniform confirms<->favourable mapping is
doctrinally ambiguous for dusthana-governed vargas (a 'favourable 8th' has inverted polarity). So the
overall rate is used only as a NON-TAUTOLOGY + regression guard. The real convergence assertion is
D9 Navamsa — the one varga wired into the D1 verdict (`_navamsa_status`) — which must corroborate
strongly; a regression that decouples D9 from the 7th-house verdict fails here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.raman_saab import cross_layer_report as clr

_BASE = json.loads(Path("tests/fixtures/cross_layer_baseline.json").read_text(encoding="utf-8"))
_EPS = 0.03


@pytest.fixture(scope="module")
def conv() -> clr.Convergence:
    return clr.convergence_stats()


def test_independent_signal_is_non_tautological(conv: clr.Convergence) -> None:
    """If the varga status were just the D1 verdict re-labelled, agreement would be ~100%; if it were
    random, ~chance. A rate strictly between the two proves the layers are INDEPENDENT yet related."""
    assert conv.total >= 800, "too few signalled pairs — the harness is not exercising the corpus"
    assert 0.35 < conv.agreement_rate < 0.95, (
        f"overall agreement {conv.agreement_rate:.3f} is not in the independent-but-related band "
        f"(=1.0 would mean tautological, ~chance would mean random)")


def test_d9_navamsa_corroborates_the_d1_verdict(conv: clr.Convergence) -> None:
    """D9 is wired into the D1 verdict, so its independent status MUST agree strongly with the D1
    rollup of the 7th. This is the load-bearing convergence guard."""
    a, h, _s = conv.per_varga.get("D9 Navamsa", (0, 0, 0))
    polar = a + h
    assert polar >= 30, "D9 produced too few polar (confirms/weakens vs favourable/afflicted) pairs"
    d9_polar = a / polar
    assert d9_polar >= _BASE["d9_polar_agreement"] - _EPS, (
        f"D9-vs-D1 polar agreement dropped to {d9_polar:.3f} "
        f"(baseline {_BASE['d9_polar_agreement']:.3f}) — the navamsa layer decoupled from the verdict")


def test_overall_agreement_does_not_regress(conv: clr.Convergence) -> None:
    """Regression guard: engine changes must not erode overall D1<->varga corroboration."""
    assert conv.agreement_rate >= _BASE["agreement_rate"] - _EPS, (
        f"overall agreement {conv.agreement_rate:.3f} < baseline {_BASE['agreement_rate']:.3f}")


def test_no_hard_contradiction_storm(conv: clr.Convergence) -> None:
    """Guard against a wiring bug that flips the divisional layer: the polar-disagreement rate must
    not spike above baseline."""
    assert conv.hard_rate <= _BASE["hard_rate"] + _EPS, (
        f"hard-contradiction rate {conv.hard_rate:.3f} > baseline {_BASE['hard_rate']:.3f} "
        f"(+{_EPS}) — the D1 and divisional layers are diverging")
