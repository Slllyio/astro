"""Tier-2 doctrine: compound marriage timing trigger.

Doctrine source
===============

This module fuses two classical marriage-timing schools into a single
*compound* trigger that practitioners require to fire BEFORE predicting
a marriage event:

A. **Karaka-set leg** (Sanjay Rath, *Crux of Vedic Astrology* — UL +
   7L + D9 dispositor formulation): the running Mahadasha lord OR the
   running Antardasha lord must be a member of the marriage karaka set:

       {7L, planet in 7H, dispositor of 7L, navamsa-lord of 7L,
        dispositor of UL, natural karaka (Venus for male / Jupiter for
        female), Darakaraka}

B. **Transit leg** (classical Parashari "outer-planet trigger"): transit
   Jupiter OR transit Saturn must aspect the natal 7th house — whole-
   sign Vedic aspect (7th from aspecter; Jupiter adds 5/9; Saturn adds
   3/10).

When both legs fire the trigger is ACTIVE (direction=positive). When
either leg is absent the trigger is INACTIVE (direction=neutral) — never
"negative", because the absence of a positive trigger is not the same as
a negative indication.

This is a high-information Finding. The component sub-checks live in
``evidence`` so downstream Tier-3 enrichment can quote the exact karaka
match and the exact transit-aspect path without re-deriving them.

Public API
==========

    compute_marriage_trigger(
        d1_chart, d9_chart, asc_sign, moon_sign, arudha_padas,
        current_md_lord, current_ad_lord,
        transit_jupiter_sign, transit_saturn_sign,
        is_male=True,
    ) -> Finding
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.core.dignity import SIGN_RULERS
from app.reading.computations.karakas import compute_karakas
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _planet_sign(d1_chart: Mapping[str, Mapping[str, object]], planet: str) -> int:
    entry = d1_chart.get(planet)
    if entry is None:
        raise KeyError(f"planet {planet!r} missing from chart")
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        raise ValueError(
            f"planet {planet!r} chart entry has invalid sign {sign!r}"
        )
    return sign


def _seventh_house_sign(asc_sign: int) -> int:
    """Sign occupying the 7th bhava for a whole-sign Lagna at ``asc_sign``."""
    return ((asc_sign - 1) + 6) % 12 + 1


def _read_ul_sign(arudha_padas: Mapping[str, Finding]) -> int:
    """Extract the UL pada sign from the arudha-pada Finding bundle.

    Falls back to value 0 (sentinel) if no UL entry was provided.
    """
    ul = arudha_padas.get("ul") if arudha_padas else None
    if ul is None:
        return 0
    for line in ul.evidence:
        if line.startswith("pada_sign="):
            try:
                return int(line.split("=", 1)[1])
            except (ValueError, IndexError):
                return 0
    return 0


def _aspects_7h(
    aspecter: str, aspecter_sign: int, seventh_sign: int,
) -> tuple[bool, str | None]:
    """Return ``(True, path_name)`` if the named outer aspects 7H.

    Vedic whole-sign rules: every planet aspects the 7th from itself.
    Jupiter additionally aspects the 5th and 9th. Saturn additionally
    aspects the 3rd and 10th. The path string identifies which of the
    available rays connected (``"7th"``, ``"5th"``, ``"9th"``, ...).
    """
    distance = ((seventh_sign - aspecter_sign) % 12) + 1
    if distance == 7:
        return True, "7th"
    if aspecter == "Jupiter" and distance in (5, 9):
        return True, f"{distance}th"
    if aspecter == "Saturn" and distance in (3, 10):
        return True, f"{distance}th"
    return False, None


def _collect_karaka_set(
    d1_chart: Mapping[str, Mapping[str, object]],
    d9_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    arudha_padas: Mapping[str, Finding],
    is_male: bool,
) -> dict[str, str]:
    """Compute the marriage karaka set; return ``{planet_name: reason}``.

    The reason string describes *why* the planet is in the set so the
    Finding's verdict can cite the exact path. When multiple paths apply
    to the same planet, the first match in this canonical priority order
    wins:

        7L > planet-in-7H > dispositor-of-7L > navamsa-lord-of-7L
           > dispositor-of-UL > natural-karaka > Darakaraka
    """
    seventh_sign = _seventh_house_sign(asc_sign)
    seven_l = SIGN_RULERS[seventh_sign]

    karaka_set: dict[str, str] = {}

    def _record(planet: str, reason: str) -> None:
        # First-write wins (canonical priority order).
        karaka_set.setdefault(planet, reason)

    # 1. 7L itself.
    _record(seven_l, f"7L ({seven_l}, lord of {_SIGN_NAMES[seventh_sign]})")

    # 2. Planets sitting in 7H (whole-sign).
    for name, entry in d1_chart.items():
        sign = entry.get("sign") if isinstance(entry, Mapping) else None
        if isinstance(sign, int) and sign == seventh_sign:
            _record(name, f"in 7H ({_SIGN_NAMES[seventh_sign]})")

    # 3. Dispositor of 7L (lord of the sign 7L is in).
    seven_l_sign = _planet_sign(d1_chart, seven_l)
    seven_l_dispositor = SIGN_RULERS[seven_l_sign]
    _record(
        seven_l_dispositor,
        f"dispositor of 7L (7L sits in {_SIGN_NAMES[seven_l_sign]})",
    )

    # 4. Navamsa lord of 7L (= lord of the D9 sign 7L sits in).
    try:
        seven_l_d9_sign = _planet_sign(d9_chart, seven_l)
        nav_lord = SIGN_RULERS[seven_l_d9_sign]
        _record(
            nav_lord,
            f"navamsa lord of 7L (7L sits in D9 {_SIGN_NAMES[seven_l_d9_sign]})",
        )
    except (KeyError, ValueError):
        # D9 chart missing 7L -> silently skip this rule.
        pass

    # 5. Dispositor of UL.
    ul_sign = _read_ul_sign(arudha_padas)
    if 1 <= ul_sign <= 12:
        ul_dispositor = SIGN_RULERS[ul_sign]
        _record(
            ul_dispositor,
            f"dispositor of UL (UL in {_SIGN_NAMES[ul_sign]})",
        )

    # 6. Natural karaka: Venus (M), Jupiter (F).
    natural = "Venus" if is_male else "Jupiter"
    _record(natural, f"natural karaka ({'male' if is_male else 'female'})")

    # 7. Darakaraka (always last for priority).
    try:
        karakas = compute_karakas(d1_chart)
        dk = karakas.get("darakaraka")
        if dk is not None:
            for line in dk.evidence:
                if line.startswith("planet="):
                    dk_planet = line.split("=", 1)[1]
                    _record(dk_planet, "Darakaraka")
                    break
    except Exception as exc:  # noqa: BLE001
        logger.debug("compute_karakas failed for marriage trigger: %s", exc)

    return karaka_set


def compute_marriage_trigger(
    d1_chart: Mapping[str, Mapping[str, object]],
    d9_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    moon_sign: int,
    arudha_padas: Mapping[str, Finding],
    current_md_lord: str,
    current_ad_lord: str,
    transit_jupiter_sign: int,
    transit_saturn_sign: int,
    is_male: bool = True,
) -> Finding:
    """Compute the compound marriage-timing trigger Finding.

    Args:
        d1_chart: Natal D1 chart mapping ``planet_name -> position_dict``.
        d9_chart: Navamsa (D9) chart in the same shape as ``d1_chart``.
        asc_sign: 1-indexed Ascendant sign.
        moon_sign: 1-indexed natal Moon sign (kept for forward
            compatibility; not used by this trigger directly).
        arudha_padas: Output of
            ``app.reading.computations.arudha_upapada.compute_arudha_padas``.
            Only the ``"ul"`` entry is consulted (for the dispositor-of-UL
            karaka).
        current_md_lord: Name of the current Mahadasha lord.
        current_ad_lord: Name of the current Antardasha lord.
        transit_jupiter_sign: 1-indexed sign of transit Jupiter.
        transit_saturn_sign: 1-indexed sign of transit Saturn.
        is_male: True for male charts (Venus natural karaka); False for
            female charts (Jupiter natural karaka).

    Returns:
        Single Finding with id ``"practitioner.marriage_trigger.compound"``,
        classification ``"trigger"``, direction ``"positive"`` if both
        legs of the compound trigger fire and ``"neutral"`` otherwise.
    """
    _validate_sign(asc_sign, "asc_sign")
    _validate_sign(moon_sign, "moon_sign")
    _validate_sign(transit_jupiter_sign, "transit_jupiter_sign")
    _validate_sign(transit_saturn_sign, "transit_saturn_sign")

    seventh_sign = _seventh_house_sign(asc_sign)

    karaka_set = _collect_karaka_set(
        d1_chart=d1_chart, d9_chart=d9_chart, asc_sign=asc_sign,
        arudha_padas=arudha_padas, is_male=is_male,
    )

    # Leg A: MD or AD lord in karaka set?
    md_reason = karaka_set.get(current_md_lord)
    ad_reason = karaka_set.get(current_ad_lord)
    leg_a_matches: list[str] = []
    if md_reason is not None:
        leg_a_matches.append(f"MD {current_md_lord} = {md_reason}")
    if ad_reason is not None:
        leg_a_matches.append(f"AD {current_ad_lord} = {ad_reason}")
    leg_a_fired = bool(leg_a_matches)

    # Leg B: transit Jupiter or Saturn aspect 7H?
    jup_aspect, jup_path = _aspects_7h("Jupiter", transit_jupiter_sign, seventh_sign)
    sat_aspect, sat_path = _aspects_7h("Saturn", transit_saturn_sign, seventh_sign)
    leg_b_matches: list[str] = []
    if jup_aspect:
        leg_b_matches.append(
            f"transit Jupiter ({_SIGN_NAMES[transit_jupiter_sign]}) "
            f"{jup_path} aspect 7H ({_SIGN_NAMES[seventh_sign]})"
        )
    if sat_aspect:
        leg_b_matches.append(
            f"transit Saturn ({_SIGN_NAMES[transit_saturn_sign]}) "
            f"{sat_path} aspect 7H ({_SIGN_NAMES[seventh_sign]})"
        )
    leg_b_fired = bool(leg_b_matches)

    active = leg_a_fired and leg_b_fired
    direction = "positive" if active else "neutral"

    if active:
        # Pick the most informative leg-A and leg-B match for the verdict.
        leg_a_short = leg_a_matches[0]
        leg_b_short = leg_b_matches[0]
        verdict = (
            f"Marriage trigger ACTIVE: {leg_a_short}; {leg_b_short}"
        )[:140]
    else:
        if not leg_a_fired and not leg_b_fired:
            why = "no karaka-set MD/AD lord; no outer aspect on 7H"
        elif not leg_a_fired:
            why = "no karaka-set MD/AD lord (transit ready but lord miss)"
        else:
            why = "karaka lord present but no transit Jupiter/Saturn aspect on 7H"
        verdict = f"Marriage trigger INACTIVE: {why}"[:140]

    evidence: list[str] = [
        f"asc_sign={asc_sign}",
        f"asc_sign_name={_SIGN_NAMES[asc_sign]}",
        f"seventh_sign={seventh_sign}",
        f"seventh_sign_name={_SIGN_NAMES[seventh_sign]}",
        f"is_male={is_male}",
        f"current_md_lord={current_md_lord}",
        f"current_ad_lord={current_ad_lord}",
        f"transit_jupiter_sign={transit_jupiter_sign}",
        f"transit_saturn_sign={transit_saturn_sign}",
        f"leg_a_fired={leg_a_fired}",
        f"leg_b_fired={leg_b_fired}",
        f"compound_active={active}",
        f"karaka_set={sorted(karaka_set.keys())}",
        "doctrine=Sanjay Rath UL+7L+D9 compound + classical Jupiter/Saturn transit",
    ]
    for match in leg_a_matches:
        evidence.append(f"leg_a_match={match}")
    for match in leg_b_matches:
        evidence.append(f"leg_b_match={match}")

    return Finding(
        id="practitioner.marriage_trigger.compound",
        rule="marriage_trigger",
        source_sequence=None,
        classification="trigger",
        direction=direction,
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


__all__ = ["compute_marriage_trigger"]
