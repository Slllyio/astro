"""Varga confirmation layer for bhava verdicts — Gap B.

Classical principle: **D1 promises, the relevant varga delivers**. A
marriage promise visible in D1 7H must verify in D9 (Navamsha) before
it can be called confirmed. Career promise in D1 10H needs D10
(Dasamsa) confirmation. Children promise in D1 5H needs D7 (Saptamsa).

## Domain → Varga mapping

Per BPHS Ch.4-7 + Phaladeepika Ch.5 + Mansagari:

| Bhava | Domain                 | Primary Varga | Secondary Varga |
|-------|------------------------|---------------|-----------------|
| 1     | Self / body            | D1            | D2 (Hora)       |
| 2     | Wealth / family        | D2 (Hora)     | D4              |
| 3     | Siblings / courage     | D3 (Drekkana) | —               |
| 4     | Mother / home          | D4 (Chaturthamsa) | D12         |
| 5     | Children / intellect   | D7 (Saptamsa) | D24             |
| 6     | Disease / service      | D30 (Trimsamsa) | D6 (not used) |
| 7     | Spouse / partnership   | D9 (Navamsha) | D7              |
| 8     | Longevity / occult     | D8 (rare) / D30 | —             |
| 9     | Father / dharma        | D9            | D12             |
| 10    | Career / status        | D10 (Dasamsa) | D1              |
| 11    | Gains / income         | D11 (rare) / D1 | —             |
| 12    | Loss / moksha          | D30           | D60             |

## Verdict labels

For each (bhava, varga) pair we compute a 4-way label:

- **CONFIRMED**: D1 promise + varga promise both positive → strong delivery
- **PROMISE_NO_DELIVERY**: D1 positive but varga negative → fame without
  substance; the karma-classical reason "promise made, not kept"
- **HIDDEN_PROMISE**: D1 negative but varga positive → late-bloom delivery
  that D1-only analysis missed
- **CONSISTENT_AFFLICTION**: both negative → the bhava is genuinely afflicted
- **UNKNOWN**: missing varga data
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


# Canonical bhava → primary varga mapping
BHAVA_TO_VARGA: Final[Mapping[int, str]] = {
    1: "D1",
    2: "D2",
    3: "D3",
    4: "D4",
    5: "D7",
    6: "D30",
    7: "D9",
    8: "D30",   # Trimsamsa for mortality
    9: "D9",    # Navamsha doubles as 9H confirmation
    10: "D10",
    11: "D1",   # No dedicated varga; D1 + Sarvashtakavarga
    12: "D30",
}


@dataclass(frozen=True)
class VargaConfirmation:
    """Verdict from cross-checking a bhava promise in its relevant varga."""
    bhava: int
    varga_name: str
    d1_label: str                  # "positive" / "neutral" / "negative"
    varga_label: str               # same labels
    confirmation_label: str        # CONFIRMED / PROMISE_NO_DELIVERY /
                                   # HIDDEN_PROMISE / CONSISTENT_AFFLICTION / UNKNOWN
    rationale: str


def _label_pillar_score(score: float) -> str:
    """Map a -1..+1 pillar score to positive/neutral/negative."""
    if score >= 0.15:
        return "positive"
    if score <= -0.15:
        return "negative"
    return "neutral"


def _confirmation_label(d1: str, varga: str) -> str:
    """Map (d1_label, varga_label) pair to confirmation verdict."""
    if d1 == "neutral" or varga == "neutral":
        # Neutral signals are weak — return based on the non-neutral side
        if d1 == "positive" or varga == "positive":
            return "HIDDEN_PROMISE" if d1 == "neutral" else "PROMISE_NO_DELIVERY"
        if d1 == "negative" or varga == "negative":
            return "CONSISTENT_AFFLICTION"
        return "UNKNOWN"
    if d1 == "positive" and varga == "positive":
        return "CONFIRMED"
    if d1 == "positive" and varga == "negative":
        return "PROMISE_NO_DELIVERY"
    if d1 == "negative" and varga == "positive":
        return "HIDDEN_PROMISE"
    if d1 == "negative" and varga == "negative":
        return "CONSISTENT_AFFLICTION"
    return "UNKNOWN"


def _rationale(label: str, bhava: int, varga: str) -> str:
    """Human-readable explanation per confirmation label."""
    domain = {
        1: "self/body", 2: "wealth/family", 3: "siblings/courage",
        4: "mother/home", 5: "children/intellect", 6: "disease/service",
        7: "spouse/marriage", 8: "longevity/occult", 9: "father/dharma",
        10: "career/status", 11: "gains/network", 12: "loss/moksha",
    }.get(bhava, f"bhava {bhava}")
    return {
        "CONFIRMED": (
            f"D1 promises {domain}; {varga} confirms. The bhava delivers "
            "fully — classical 'promise made and kept'."
        ),
        "PROMISE_NO_DELIVERY": (
            f"D1 promises {domain} but {varga} contradicts. Classical pattern: "
            "external image of success without inner substance. The promise "
            "appears in life but doesn't ultimately deliver the karmic fruit."
        ),
        "HIDDEN_PROMISE": (
            f"D1 shows no {domain} promise but {varga} contains it. Late-bloom "
            "delivery: the bhava activates unexpectedly, often via dasha-of-"
            f"{varga}-lord rather than the natal Lagna-frame."
        ),
        "CONSISTENT_AFFLICTION": (
            f"Both D1 and {varga} agree negatively on {domain}. The bhava is "
            "genuinely afflicted; expect challenges that don't resolve through "
            "outer effort alone."
        ),
        "UNKNOWN": (
            f"Insufficient data — {varga} placements unavailable. Cannot "
            f"confirm/contradict the D1 reading of {domain}."
        ),
    }.get(label, "(no rationale)")


def varga_confirmation(
    bhava: int,
    d1_bhava_pillar_score: float,
    varga_bhava_pillar_score: float | None = None,
    varga_name: str | None = None,
) -> VargaConfirmation:
    """Cross-check a bhava's D1 verdict against its primary varga.

    Args:
        bhava: 1..12.
        d1_bhava_pillar_score: the Phase 6 bhava-judge pillar score
            from D1 (range -1.0 .. +1.0).
        varga_bhava_pillar_score: same score computed against the
            divisional chart; None if not available.
        varga_name: override the default varga for this bhava.

    Returns:
        VargaConfirmation with the 4-way label + rationale.
    """
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    used_varga = varga_name or BHAVA_TO_VARGA.get(bhava, "D1")
    d1_label = _label_pillar_score(d1_bhava_pillar_score)
    if varga_bhava_pillar_score is None:
        return VargaConfirmation(
            bhava=bhava, varga_name=used_varga,
            d1_label=d1_label, varga_label="unknown",
            confirmation_label="UNKNOWN",
            rationale=_rationale("UNKNOWN", bhava, used_varga),
        )
    varga_label = _label_pillar_score(varga_bhava_pillar_score)
    conf_label = _confirmation_label(d1_label, varga_label)
    return VargaConfirmation(
        bhava=bhava, varga_name=used_varga,
        d1_label=d1_label, varga_label=varga_label,
        confirmation_label=conf_label,
        rationale=_rationale(conf_label, bhava, used_varga),
    )


def primary_varga_for_bhava(bhava: int) -> str:
    """Get the classical primary varga for a bhava."""
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    return BHAVA_TO_VARGA[bhava]
