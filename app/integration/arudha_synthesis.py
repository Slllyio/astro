"""M6 — Arudha image synthesis (Jaimini Sutras 1.1.30-39 + 2.1.1-20).

Arudha Lagna (AL) is the chart's PUBLIC IMAGE — how the world perceives
the native. Upapada Lagna (UPL) is the marriage-image projection.

Track-B's gap_annotator computes Arudha sign + house. This module reads
what those positions actually MEAN by extracting:
- House from natal lagna the Arudha falls in
- Planets in the Arudha sign
- The Arudha lord's placement
- Argala (intervention) on the Arudha
- Similar for Upapada (marriage signifier)

Public surface
--------------
- ``synthesise_arudha(reading)`` -> ``ArudhaSynthesis``
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.integration.gap_annotator import annotate_with_gap_modules
from app.integration.md_lord_dossier import _SIGN_LORDS, _SIGN_NAMES


# Standard Jaimini house-from-lagna interpretations of the Arudha.
_ARUDHA_HOUSE_THEMES: dict[int, str] = {
    1: "self-image aligned with true self — public face matches inner reality",
    2: "image projects wealth, family-orientation, voice — perceived as a "
       "speaker / wealth-holder regardless of actual status",
    3: "image projects courage, effort, hands-on engagement — perceived as "
       "active and self-driven",
    4: "image projects comfort, conventional rootedness — perceived as "
       "settled / family-anchored",
    5: "image projects intelligence, creativity, dignity — perceived as "
       "learned / lordly",
    6: "image projects struggle, service, contention — perceived as battling "
       "or competing",
    7: "image projects partnerships, public engagement — perceived through "
       "the partner / public dealings",
    8: "image projects depth, mystery, occult — perceived as researcher / "
       "transformer, sometimes hidden",
    9: "image projects dharma, teaching, fortune — perceived as wise / "
       "fortunate / spiritually-inclined",
    10: "image projects status, action, career — perceived through the "
        "public role",
    11: "image projects gains, networks, fulfillment of desires — perceived "
        "as well-connected and resourceful",
    12: "image projects withdrawal, foreign-ness, dissolution — perceived "
        "as elusive / detached / private",
}

_UPAPADA_HOUSE_THEMES: dict[int, str] = {
    1: "spouse seen as alter-ego or co-equal partner",
    2: "spouse brings wealth, family stability, voice / speech",
    3: "spouse is active, courageous, contributes to siblings/efforts",
    4: "spouse provides home / comfort / emotional foundation",
    5: "spouse intelligent, creative; brings children theme",
    6: "spouse-relationship has struggle / service / health theme",
    7: "classical 7H spouse signature — direct partnership emphasis",
    8: "spouse has depth / mystery / transformation theme; sometimes "
       "second-marriage signifier",
    9: "spouse is dharmic / teacher / fortunate; foreign or learned partner",
    10: "spouse brings status / career advantage",
    11: "spouse brings gains, networks, fulfilment of partnership desires",
    12: "spouse foreign / withdrawn / brings dissolution-theme — sometimes "
        "renunciation or distance",
}


class ArudhaSynthesis(BaseModel):
    """Arudha + Upapada synthesised reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Arudha Lagna
    arudha_sign: int = Field(ge=1, le=12)
    arudha_sign_name: str
    arudha_house_from_lagna: int = Field(ge=1, le=12)
    arudha_house_theme: str
    arudha_lord: str
    arudha_lord_house: int = Field(ge=1, le=12)
    arudha_lord_sign_name: str
    planets_in_arudha: tuple[str, ...]
    image_summary: str

    # Upapada Lagna (marriage signifier)
    upapada_sign: int = Field(ge=1, le=12)
    upapada_sign_name: str
    upapada_house_from_lagna: int = Field(ge=1, le=12)
    upapada_house_theme: str
    upapada_lord: str
    upapada_lord_house: int = Field(ge=1, le=12)
    upapada_lord_sign_name: str
    planets_in_upapada: tuple[str, ...]
    marriage_summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _house_from_lagna(lagna_sign: int, target_sign: int) -> int:
    """N-th house from lagna where the target_sign falls."""
    return ((target_sign - lagna_sign) % 12) + 1


def _planets_in_sign(planets: dict, sign: int) -> tuple[str, ...]:
    """Planets currently in the given sign."""
    out: list[str] = []
    for name, body in planets.items():
        if isinstance(body, dict) and int(body.get("sign", 0)) == sign:
            out.append(name)
    return tuple(sorted(out))


def _compose_image_summary(
    arudha_house: int, arudha_lord: str, arudha_lord_house: int,
    planets_in_arudha: tuple[str, ...],
) -> str:
    parts = [f"Arudha falls in {arudha_house}H from lagna"]
    parts.append(_ARUDHA_HOUSE_THEMES.get(arudha_house, ""))
    if planets_in_arudha:
        parts.append(f"Planets in Arudha sign: {', '.join(planets_in_arudha)}")
    parts.append(f"Arudha lord {arudha_lord} sits in {arudha_lord_house}H")
    return " — ".join(p for p in parts if p)


def _compose_marriage_summary(
    upapada_house: int, upapada_lord: str, upapada_lord_house: int,
    planets_in_upapada: tuple[str, ...],
) -> str:
    parts = [f"Upapada falls in {upapada_house}H from lagna"]
    parts.append(_UPAPADA_HOUSE_THEMES.get(upapada_house, ""))
    if planets_in_upapada:
        parts.append(f"Planets in Upapada sign: {', '.join(planets_in_upapada)}")
    parts.append(f"Upapada lord {upapada_lord} sits in {upapada_lord_house}H")
    return " — ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesise_arudha(reading: Mapping[str, Any]) -> ArudhaSynthesis:
    """Build Arudha + Upapada synthesised reading."""
    chart = reading.get("chart") or {}
    planets = chart.get("planets") or {}
    lagna_sign = int((chart.get("cusps") or {}).get("sign", 1))

    # Get Arudha + Upapada from Gap-D
    gap = annotate_with_gap_modules(reading)
    d = gap.gap_modules.get("D")
    if not d or not d.available:
        raise ValueError("Gap-D (karakamsa_arudha) unavailable for this reading")

    al_block = (d.result or {}).get("arudha_lagna") or {}
    upl_block = (d.result or {}).get("upapada_lagna") or {}
    arudha_sign = int(al_block.get("arudha_sign", 1))
    upapada_sign = int(upl_block.get("arudha_sign", 1))

    # Arudha
    arudha_house_from_lagna = _house_from_lagna(lagna_sign, arudha_sign)
    arudha_lord = _SIGN_LORDS[arudha_sign]
    arudha_lord_body = planets.get(arudha_lord) or {}
    arudha_lord_house = int(arudha_lord_body.get("house", 0))
    arudha_lord_sign = int(arudha_lord_body.get("sign", 0))
    arudha_lord_sign_name = _SIGN_NAMES[arudha_lord_sign] if 1 <= arudha_lord_sign <= 12 else "?"
    planets_in_arudha = _planets_in_sign(planets, arudha_sign)
    image_summary = _compose_image_summary(
        arudha_house_from_lagna, arudha_lord, arudha_lord_house,
        planets_in_arudha,
    )

    # Upapada
    upapada_house_from_lagna = _house_from_lagna(lagna_sign, upapada_sign)
    upapada_lord = _SIGN_LORDS[upapada_sign]
    upapada_lord_body = planets.get(upapada_lord) or {}
    upapada_lord_house = int(upapada_lord_body.get("house", 0))
    upapada_lord_sign = int(upapada_lord_body.get("sign", 0))
    upapada_lord_sign_name = _SIGN_NAMES[upapada_lord_sign] if 1 <= upapada_lord_sign <= 12 else "?"
    planets_in_upapada = _planets_in_sign(planets, upapada_sign)
    marriage_summary = _compose_marriage_summary(
        upapada_house_from_lagna, upapada_lord, upapada_lord_house,
        planets_in_upapada,
    )

    return ArudhaSynthesis(
        arudha_sign=arudha_sign,
        arudha_sign_name=_SIGN_NAMES[arudha_sign],
        arudha_house_from_lagna=arudha_house_from_lagna,
        arudha_house_theme=_ARUDHA_HOUSE_THEMES.get(arudha_house_from_lagna, ""),
        arudha_lord=arudha_lord,
        arudha_lord_house=arudha_lord_house,
        arudha_lord_sign_name=arudha_lord_sign_name,
        planets_in_arudha=planets_in_arudha,
        image_summary=image_summary,
        upapada_sign=upapada_sign,
        upapada_sign_name=_SIGN_NAMES[upapada_sign],
        upapada_house_from_lagna=upapada_house_from_lagna,
        upapada_house_theme=_UPAPADA_HOUSE_THEMES.get(upapada_house_from_lagna, ""),
        upapada_lord=upapada_lord,
        upapada_lord_house=upapada_lord_house,
        upapada_lord_sign_name=upapada_lord_sign_name,
        planets_in_upapada=planets_in_upapada,
        marriage_summary=marriage_summary,
    )
