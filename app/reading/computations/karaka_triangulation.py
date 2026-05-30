"""Tier-1 foundation: Sanjay-Rath karaka triangulation (D-10 locked).

Doctrine lock -- D-10 (``docs/doctrine-decisions.md``)
======================================================

Use the **Sanjay-Rath formulation** of karaka triangulation: examine a
domain by computing the relevant signification's house from each of
three reference points (Lagna, Moon, natural karaka) and asking *do all
three anchors land on the same sign?*. Strict triple-AND is the
high-precision form preferred for v1 (lowest false-positive). The BPHS
Vol.I Ch.11 variant (Arudha Lagna substitution for some significations)
is a dispute case surfaced via ``dispute_surfacing.py``.

Domain table
============

  | Domain    | House(s)   | Anchors                  |
  |-----------|------------|--------------------------|
  | marriage  | 7          | Lagna, Moon, Venus       |
  | career    | 10         | Lagna, Moon, Sun         |
  | wealth    | 2, 11      | Lagna, Moon, Jupiter     |
  | children  | 5          | Lagna, Moon, Jupiter     |
  | health    | 1, 6       | Lagna, Moon              |
  | education | 4, 5       | Lagna, Moon, Mercury     |

For each domain we enumerate the Cartesian product ``house × anchor``
and resolve each pair to a target sign via the whole-sign rule
``target_sign = ((pivot_sign - 1 + house - 1) % 12) + 1``. Concordance
is the size of the most common (mode) sign-bucket divided by the total
anchor count.

Direction mapping
=================

  - **positive** : concordance == 1.0       (all anchors agree)
  - **neutral**  : concordance >= 0.5       (at least half agree)
  - **negative** : concordance <  0.5       (less than half agree)

The marriage/career/children domains have 3 anchors total; these match
the spec's "3/3 / 2/3 / 1/3" example exactly. Wealth and education
have 6 anchors (2 houses × 3 pivots); health has 4 (2 houses × 2
pivots) -- the same direction rule applies via the half-of-total
threshold.

Verdict format (spec example)
=============================

    'Marriage anchors: 7H from Lagna=Aries, 7H from Moon=Aries,
     7H from Venus=Aries (3/3 concordance)'

For multi-house domains the verdict lists houses jointly; the per-
anchor sign assignments live in the evidence list.

Public API
==========

  compute_karaka_triangulation(d1_chart, asc_sign, moon_sign)
      -> dict[str, Finding] keyed by domain name (marriage, career,
         wealth, children, health, education).
"""
from __future__ import annotations

import logging
from collections import Counter
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


# The 6 domains, their target houses, and the planets that provide
# pivots for each. "lagna" and "moon" are sentinel names resolved at
# call-time to ``asc_sign`` and ``moon_sign`` respectively; everything
# else must be a key present in ``d1_chart``.
_DOMAIN_TABLE: Final[dict[str, dict]] = {
    "marriage":  {"houses": (7,),       "pivots": ("lagna", "moon", "Venus")},
    "career":    {"houses": (10,),      "pivots": ("lagna", "moon", "Sun")},
    "wealth":    {"houses": (2, 11),    "pivots": ("lagna", "moon", "Jupiter")},
    "children":  {"houses": (5,),       "pivots": ("lagna", "moon", "Jupiter")},
    "health":    {"houses": (1, 6),     "pivots": ("lagna", "moon")},
    "education": {"houses": (4, 5),     "pivots": ("lagna", "moon", "Mercury")},
}


# Sign names for human-readable verdict prettiness.
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",  # 1-indexed
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# 3-vote envelope -- triangulation is a single deterministic concordance
# computation, not a 3-pillar judgment.
_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pivot_sign(
    pivot_name: str,
    asc_sign: int,
    moon_sign: int,
    d1_chart: dict,
) -> int | None:
    """Resolve a pivot name to the corresponding sidereal sign (1..12).

    Returns None when a non-sentinel pivot is missing from the chart;
    the caller treats this as an unresolvable anchor and excludes it
    from the concordance count.
    """
    if pivot_name == "lagna":
        return asc_sign
    if pivot_name == "moon":
        return moon_sign
    entry = d1_chart.get(pivot_name)
    if entry is None:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int):
        return None
    return sign


def _target_sign_from(pivot_sign: int, house: int) -> int:
    """Whole-sign count: house^th sign from the pivot."""
    return ((pivot_sign - 1 + house - 1) % 12) + 1


def _pivot_label(pivot_name: str) -> str:
    """Human-readable label for the verdict / evidence."""
    if pivot_name == "lagna":
        return "Lagna"
    if pivot_name == "moon":
        return "Moon"
    return pivot_name


def _enumerate_anchors(
    domain_name: str,
    asc_sign: int,
    moon_sign: int,
    d1_chart: dict,
) -> list[tuple[int, str, int]]:
    """Enumerate (house, pivot_label, target_sign) anchors for a domain.

    Skips anchors whose pivot is missing from the chart. The returned
    order is stable: outer = houses (insertion-ordered), inner = pivots
    (insertion-ordered) per ``_DOMAIN_TABLE``.
    """
    spec = _DOMAIN_TABLE[domain_name]
    anchors: list[tuple[int, str, int]] = []
    for house in spec["houses"]:
        for pivot in spec["pivots"]:
            pivot_sign = _pivot_sign(pivot, asc_sign, moon_sign, d1_chart)
            if pivot_sign is None:
                continue
            target = _target_sign_from(pivot_sign, house)
            anchors.append((house, _pivot_label(pivot), target))
    return anchors


def _direction_for(concordance: float) -> str:
    """Map concordance fraction to a Finding.direction value."""
    if concordance >= 1.0 - 1e-12:
        return "positive"
    if concordance >= 0.5 - 1e-12:
        return "neutral"
    return "negative"


def _concordance_stats(
    anchors: list[tuple[int, str, int]],
) -> tuple[int, int, float]:
    """Return ``(mode_count, total, concordance_ratio)`` for an anchor set.

    If ``total`` is 0 (every pivot missing -- pathological), the
    concordance is treated as 0.0.
    """
    if not anchors:
        return 0, 0, 0.0
    counter = Counter(target for _, _, target in anchors)
    mode_count = counter.most_common(1)[0][1]
    total = len(anchors)
    return mode_count, total, mode_count / total


def _verdict_for(
    domain: str,
    houses: tuple[int, ...],
    anchors: list[tuple[int, str, int]],
    mode_count: int,
    total: int,
) -> str:
    """Compose the verdict; truncate at the schema's 140-char cap."""
    label = domain.capitalize()
    house_str = "/".join(f"{h}H" for h in houses)
    if not anchors:
        return f"{label} {house_str} anchors: none (0/0 concordance)"

    # Render each anchor compactly; we may exceed 140 chars on
    # multi-house domains so we fall back to a summary form when long.
    pieces = [
        f"{h}H from {label_anchor}={_SIGN_NAMES[sign]}"
        for h, label_anchor, sign in anchors
    ]
    full = (
        f"{label} anchors: {', '.join(pieces)} ({mode_count}/{total} concordance)"
    )
    if len(full) <= 140:
        return full

    # Summary fallback when the per-anchor list is too long.
    return (
        f"{label} {house_str} triangulation: {mode_count}/{total} concordance"
    )


def _domain_finding(
    domain: str,
    houses: tuple[int, ...],
    anchors: list[tuple[int, str, int]],
    mode_count: int,
    total: int,
    concordance: float,
) -> Finding:
    """Build the Finding for one domain's triangulation."""
    direction = _direction_for(concordance)
    evidence = [
        f"domain={domain}",
        f"houses={list(houses)}",
        f"anchors={[(h, label, sign) for h, label, sign in anchors]}",
        f"total_anchors={total}",
        f"mode_count={mode_count}",
        f"concordance={concordance:.4f}",
        "doctrine=D-10 (Sanjay-Rath karaka triangulation, triple-AND)",
    ]
    return Finding(
        id=f"foundation.karaka_triangulation.{domain}",
        rule="karaka_triangulation",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=_verdict_for(domain, houses, anchors, mode_count, total),
        evidence=evidence,
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_karaka_triangulation(
    d1_chart: dict, asc_sign: int, moon_sign: int,
) -> dict[str, Finding]:
    """Compute Sanjay-Rath karaka triangulation for the 6 named domains.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each entry
            must carry at least ``sign`` (1..12). Missing planet pivots
            (e.g. no Venus entry) are silently dropped from the
            concordance count; this keeps the function tolerant of
            chart-shape changes.
        asc_sign: Ascendant rashi (1=Aries .. 12=Pisces).
        moon_sign: Moon's natal rashi (1..12).

    Returns:
        Dict keyed by domain name (``"marriage"``, ``"career"``,
        ``"wealth"``, ``"children"``, ``"health"``, ``"education"``);
        each value is a Finding with ``id =
        foundation.karaka_triangulation.<domain>``. Direction reflects
        concordance per the rule above.

    Raises:
        ValueError: if ``asc_sign`` or ``moon_sign`` is not in ``1..12``.

    Example:
        >>> findings = compute_karaka_triangulation(d1, asc_sign=6, moon_sign=12)
        >>> findings["marriage"].direction in {"positive", "neutral", "negative"}
        True
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )
    if not 1 <= moon_sign <= 12:
        raise ValueError(
            f"moon_sign must be in [1, 12], got {moon_sign!r}"
        )

    out: dict[str, Finding] = {}
    for domain_name, spec in _DOMAIN_TABLE.items():
        anchors = _enumerate_anchors(
            domain_name, asc_sign, moon_sign, d1_chart,
        )
        mode_count, total, concordance = _concordance_stats(anchors)
        out[domain_name] = _domain_finding(
            domain_name,
            tuple(spec["houses"]),
            anchors,
            mode_count,
            total,
            concordance,
        )
    return out


__all__ = ["compute_karaka_triangulation"]
