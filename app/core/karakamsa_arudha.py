"""Karakamsa + Arudha Pada (Jaimini soul layer) — Gap D.

Two of the most-cited Jaimini techniques absent from the framework
until now. KN Rao calls Karakamsa "the soul's chart" and Arudha Pada
"the image the world sees".

## Karakamsa (BPHS Ch.32 + Jaimini Sutra 1.2 + KN Rao's *Chara Dasa*)

The Atmakaraka (AK) is the planet with the highest degree-within-sign
among the 7 visible planets + Rahu (longitude inverted). Its NAVAMSHA
(D9) sign is the **Karakamsa Lagna** — a new chart-frame from which
to read the 12 bhavas. The reading is *soul-purpose-centered*:

- 5H from Karakamsa = what the soul came to teach / mantra-affinity
- 7H from Karakamsa = dharma-partner / soul-purpose-relationship
- 9H from Karakamsa = the soul's guru-lineage
- 10H from Karakamsa = the soul's worldly mission
- 12H from Karakamsa = the soul's moksha-vehicle (which deity-tradition)

The classical use is to identify a native's **ishta-devata** (chosen
deity for worship) from the 12H of Karakamsa, and **career-by-soul**
from the 10H of Karakamsa.

## Arudha Pada (Jaimini Sutra 1.4 + BPHS Ch.29)

For each bhava B, the Arudha Pada (AB) is computed:

  1. Find B's lord (L).
  2. Count the distance D from B to L.
  3. Count D more houses from L. That's the Arudha sign.

Substitution rules:
  - If the result lands ON the original bhava B, use the 10th from B.
  - If the result lands ON the 7th from B, use the 4th from B.

The most-used Arudhas:
  - **Arudha Lagna (AL = Arudha of 1H)** — how the world perceives
    the native (status-image vs real self). Often called "social mask".
  - **Upapada Lagna (UL = Arudha of 12H)** — marriage indicator. The
    sign of UL = type of spouse. The 2nd from UL = duration of first
    marriage. (Sanjay Rath's school treats UL as more reliable than 7H
    for marriage timing in many cases.)
  - **A7 (Dara Pada)** — first marriage spouse-image.
  - **A10 (Karya-arudha)** — career image / public-action perception.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.functional_roles import functional_roles


# Sign rulership for finding bhava lord — duplicated minimally to keep
# this module independent of bhava_judge's private constants.
_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


@dataclass(frozen=True)
class KarakamsaReading:
    """The Karakamsa Lagna + per-bhava-from-Karakamsa hints."""
    atmakaraka: str
    atmakaraka_d1_sign: int
    karakamsa_sign: int            # = AK's D9 sign
    bhava_readings: Mapping[int, str]   # bhava 1..12 from Karakamsa → hint


@dataclass(frozen=True)
class ArudhaPada:
    """The Arudha Pada (projected image) of one bhava."""
    bhava: int                     # source bhava (1..12)
    bhava_lord: str
    arudha_sign: int               # the Arudha Pada in zodiac terms
    arudha_natal_house: int        # which natal house the Arudha falls in
    interpretation_hint: str


_BHAVA_FROM_KARAKAMSA_HINTS: Final[Mapping[int, str]] = {
    1: "Soul's natural physical/mental disposition; ishta of the body",
    2: "Soul's accumulated speech, voice, family-of-origin karma",
    3: "Soul's siblings-of-spirit, courage-training, short journeys",
    4: "Soul's emotional foundation; mother of the soul; inherited home of being",
    5: "Soul's purpose-mantra; what it came to teach; bija-mantra affinity",
    6: "Soul's enemies-of-purpose (obstacles to dharma); illnesses-as-teaching",
    7: "Dharma-partner; soul-purpose-relationship; ideal complement",
    8: "Soul's hidden karma; transformative initiation; occult path",
    9: "Soul's guru-lineage; inherited dharma; pilgrimage-of-being",
    10: "Soul's worldly mission; karma-yoga channel; what soul DOES",
    11: "Soul's network of kindred souls; spiritual gains",
    12: "Soul's moksha-vehicle; ishta-devata indicator; final liberation path",
}


def karakamsa_lagna(
    atmakaraka: str,
    atmakaraka_d1_sign: int,
    atmakaraka_d9_sign: int,
) -> KarakamsaReading:
    """Compute the Karakamsa Lagna reading.

    Args:
        atmakaraka: the AK planet (Sun..Saturn or Rahu).
        atmakaraka_d1_sign: AK's natal D1 sign.
        atmakaraka_d9_sign: AK's D9 (Navamsha) sign — this is the
            Karakamsa Lagna.

    Returns:
        KarakamsaReading with the 12 bhava-from-Karakamsa hint phrases.
    """
    if not 1 <= atmakaraka_d1_sign <= 12:
        raise ValueError(f"atmakaraka_d1_sign must be 1..12")
    if not 1 <= atmakaraka_d9_sign <= 12:
        raise ValueError(f"atmakaraka_d9_sign must be 1..12")
    return KarakamsaReading(
        atmakaraka=atmakaraka,
        atmakaraka_d1_sign=atmakaraka_d1_sign,
        karakamsa_sign=atmakaraka_d9_sign,
        bhava_readings=dict(_BHAVA_FROM_KARAKAMSA_HINTS),
    )


def _step_signs(from_sign: int, distance: int) -> int:
    """Step `distance` signs forward (inclusive count, wraps at 12)."""
    return ((from_sign - 1 + distance - 1) % 12) + 1


def arudha_pada(bhava: int, chart: Chart) -> ArudhaPada:
    """Compute the Arudha Pada of a given bhava per Jaimini Sutra 1.4.

    Algorithm:
      1. Find bhava lord (planet ruling the sign at this bhava).
      2. Count distance D from the bhava-sign to the lord's sign
         (inclusive, forward).
      3. Count D more signs from the lord's sign — that's the Arudha sign.
      4. If Arudha = bhava sign → use 10th from bhava (substitution).
      5. If Arudha = 7th sign from bhava → use 4th from bhava.

    Args:
        bhava: 1..12 — source bhava.
        chart: Chart with planet positions.

    Returns:
        ArudhaPada with the projected sign + interpretation hint.
    """
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    bhava_sign = _step_signs(chart.asc_sign, bhava)
    bhava_lord = _SIGN_LORDS[bhava_sign]
    lord_sign = chart.sign_of(bhava_lord)
    if lord_sign is None:
        raise ValueError(f"chart missing position for bhava {bhava} lord {bhava_lord}")
    # Distance from bhava-sign to lord-sign (inclusive, forward)
    distance = ((lord_sign - bhava_sign) % 12) + 1
    # Step that distance again from lord-sign
    arudha_sign = _step_signs(lord_sign, distance)
    # Substitution rules
    if arudha_sign == bhava_sign:
        arudha_sign = _step_signs(bhava_sign, 10)
    elif arudha_sign == _step_signs(bhava_sign, 7):
        arudha_sign = _step_signs(bhava_sign, 4)
    # Natal-Lagna-frame house
    arudha_natal_house = ((arudha_sign - chart.asc_sign) % 12) + 1
    hint = _arudha_hint(bhava, arudha_sign)
    return ArudhaPada(
        bhava=bhava, bhava_lord=bhava_lord,
        arudha_sign=arudha_sign,
        arudha_natal_house=arudha_natal_house,
        interpretation_hint=hint,
    )


def _arudha_hint(bhava: int, arudha_sign: int) -> str:
    """Generate the interpretation hint for the Arudha of a bhava."""
    bhava_role = {
        1: "social mask (Arudha Lagna AL — how others perceive the native)",
        2: "perceived family/wealth image",
        3: "perceived courage / sibling-image",
        4: "perceived home / mother-image",
        5: "perceived intellect / children-image",
        6: "perceived enemies / service-role-image",
        7: "perceived spouse (Dara Pada A7) — first marriage image",
        8: "perceived transformations / hidden-life image",
        9: "perceived dharma / father-image / guru-image",
        10: "perceived career (Karya Arudha A10) — public-action image",
        11: "perceived gains / network-image",
        12: "perceived losses (Upapada UL) — primary marriage indicator + moksha image",
    }
    role = bhava_role.get(bhava, f"perceived bhava {bhava}")
    return f"Arudha of bhava {bhava} ({role}) projects in sign {arudha_sign}"


def all_arudhas(chart: Chart) -> dict[int, ArudhaPada]:
    """Compute Arudha Padas for all 12 bhavas."""
    return {b: arudha_pada(b, chart) for b in range(1, 13)}


def upapada_lagna(chart: Chart) -> ArudhaPada:
    """The Arudha of the 12H = Upapada Lagna (UL).

    Most-used Arudha for marriage timing in Sanjay Rath's school.
    The sign of UL = type of spouse. The 2nd from UL = duration of
    first marriage / quality of marital years.
    """
    return arudha_pada(12, chart)


def arudha_lagna(chart: Chart) -> ArudhaPada:
    """The Arudha of the 1H = Arudha Lagna (AL).

    The social-perception reading — how the native appears to the
    world, often quite different from the real self (Lagna).
    """
    return arudha_pada(1, chart)


def dara_pada(chart: Chart) -> ArudhaPada:
    """The Arudha of the 7H = Dara Pada (A7).

    First-marriage spouse-image. Used jointly with UL for marriage
    analysis: UL = first marriage event, A7 = first spouse's actual nature.
    """
    return arudha_pada(7, chart)
