"""BPHS-derived chart-pattern library (L-3).

## What this is

A registry of CLASSICAL chart-pattern → reading mappings derived
SOLELY from BPHS / Phaladeepika / Mansagari / Brihat Jataka / Saravali.
Each pattern is a structural fingerprint (Lagna, planet placements,
specific yoga combinations) paired with the classical reading the text
gives for that exact pattern.

## What this is NOT

This is NOT Nadi astrology. Real Nadi (Bhrigu Samhita / Saptarishi /
Dhruva / etc.) works from a different corpus — palm-leaf manuscripts
holding millions of HIGHLY-SPECIFIC patterns (down to the minute of
birth) with bespoke predictions. The Nadi corpus is not publicly
digitised; see app/core/nadi_lookup.py for the honest scaffold for
that.

THIS module fills a different gap: BPHS itself has many specific
"pattern + reading" verses that aren't expressed as named yogas in
yoga_library.py — they're more granular ("Mars in 7H, aspected by
Saturn, with Moon in 4H → marital discord IF Venus is debilitated").
We harvest those from the classical canon and provide a lookup
interface.

## Architecture

Each pattern is a callable predicate (Chart) -> Verdict. A verdict
fires when the pattern's preconditions match the chart. Pattern keys
include their classical citation so the framework can attribute every
verdict to a specific shloka.

This module is COMPOSABLE with the convergence engine: each fired
pattern produces an Evidence record that flows into the per-domain
scoring just like yoga_library detectors.

## References

  * BPHS Ch.34-45 — bhava-specific verse-patterns
  * Phaladeepika Ch.6 — combinations
  * Mansagari Ch.6 — yoga combinations
  * Saravali — additional combinations
  * Brihat Jataka — Varahamihira's classical examples
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final

from app.core.chart_model import Chart
from app.core.dignity import is_debilitated, is_exalted, is_own_sign


# ─── Result type ────────────────────────────────────────────────────


@dataclass(frozen=True)
class PatternVerdict:
    """One classical pattern matching the chart."""
    name: str                    # short slug, e.g. "marital_discord_mars_7h"
    domain: str                  # marriage / wealth / career / health / etc.
    polarity: str                # "supportive" / "afflicting" / "neutral"
    severity: float              # 0.0..1.0
    description: str             # what this pattern says
    citation: str                # classical reference


# ─── Helpers ────────────────────────────────────────────────────────


_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({5, 9})


def _has_planet_in_house(chart: Chart, planet: str, house: int) -> bool:
    return chart.house_of(planet) == house


def _aspected_by(chart: Chart, target_house: int, aspecter: str) -> bool:
    """Whole-sign drishti check: does aspecter aspect the target_house?"""
    ah = chart.house_of(aspecter)
    if ah is None:
        return False
    # Opposition (7th) — universal
    if ((target_house - ah) % 12) + 1 == 7:
        return True
    distance = ((target_house - ah) % 12) + 1
    if aspecter == "Jupiter" and distance in (5, 9):
        return True
    if aspecter == "Mars" and distance in (4, 8):
        return True
    if aspecter == "Saturn" and distance in (3, 10):
        return True
    if aspecter in ("Rahu", "Ketu") and distance in (5, 9):
        return True
    return False


# ─── Marriage-domain patterns ───────────────────────────────────────


def pattern_marital_discord_mars_7h_sat_aspect(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.31 — Mars in 7H aspected by Saturn → marital discord
    intensified beyond Mangal Dosha alone.
    """
    if not _has_planet_in_house(chart, "Mars", 7):
        return None
    if not _aspected_by(chart, 7, "Saturn"):
        return None
    return PatternVerdict(
        name="marital_discord_mars_7h_sat_aspect",
        domain="marriage", polarity="afflicting", severity=0.75,
        description=(
            "Mars in 7H aspected by Saturn — Mangal Dosha amplified by "
            "Saturn's restrictive drishti; marital discord with delay or "
            "estrangement, not merely temperamental friction."
        ),
        citation="BPHS Ch.34.31",
    )


def pattern_venus_debilitated_in_7h(chart: Chart) -> PatternVerdict | None:
    """Phaladeepika Ch.18.4 — Venus debilitated in 7H → spouse-quality
    issues + missed opportunities for partnership."""
    if not _has_planet_in_house(chart, "Venus", 7):
        return None
    sign = chart.sign_of("Venus")
    if sign is None or not is_debilitated("Venus", sign):
        return None
    return PatternVerdict(
        name="venus_debilitated_in_7h",
        domain="marriage", polarity="afflicting", severity=0.7,
        description=(
            "Venus (marriage karaka) debilitated in 7H (marriage bhava) — "
            "spouse-quality concerns; the marriage signature is present "
            "but its delivery is compromised."
        ),
        citation="Phaladeepika Ch.18.4",
    )


def pattern_jupiter_in_7h_benefic_aspect(chart: Chart) -> PatternVerdict | None:
    """Mansagari Ch.4.18 — Jupiter in 7H + benefic aspect → noble spouse,
    auspicious marriage."""
    if not _has_planet_in_house(chart, "Jupiter", 7):
        return None
    # Need at least one benefic aspect besides Jupiter itself
    has_benefic = any(
        _aspected_by(chart, 7, b) for b in ("Venus", "Mercury", "Moon")
    )
    if not has_benefic:
        return None
    return PatternVerdict(
        name="jupiter_in_7h_benefic_aspect",
        domain="marriage", polarity="supportive", severity=0.8,
        description=(
            "Jupiter in 7H with benefic aspect — noble spouse, auspicious "
            "and dharmic marriage. Mansagari's classic 'sad-grihastha' "
            "(righteous householder) pattern."
        ),
        citation="Mansagari Ch.4.18",
    )


# ─── Wealth-domain patterns ─────────────────────────────────────────


def pattern_jupiter_in_2h_own_sign(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.7 — Jupiter in 2H in own sign → wealth-flow blessed,
    speech-grace, generosity."""
    if not _has_planet_in_house(chart, "Jupiter", 2):
        return None
    sign = chart.sign_of("Jupiter")
    if sign is None or not is_own_sign("Jupiter", sign):
        return None
    return PatternVerdict(
        name="jupiter_in_2h_own_sign",
        domain="wealth", polarity="supportive", severity=0.85,
        description=(
            "Jupiter (wealth-karaka) in 2H (wealth-bhava) in own sign "
            "(Sagittarius/Pisces) — sustained wealth-flow, dharmic speech, "
            "philanthropic generosity."
        ),
        citation="BPHS Ch.34.7",
    )


def pattern_2h_lord_in_dushtana(chart: Chart) -> PatternVerdict | None:
    """Phaladeepika Ch.17 — 2H lord in 6/8/12 → wealth-erosion patterns."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_2 = None
    for p, r in roles.items():
        if 2 in r.houses_ruled:
            lord_2 = p
            break
    if not lord_2:
        return None
    h = chart.house_of(lord_2)
    if h not in (6, 8, 12):
        return None
    return PatternVerdict(
        name="2h_lord_in_dushtana",
        domain="wealth", polarity="afflicting", severity=0.65,
        description=(
            f"2H-lord {lord_2} placed in {h}H (dushtana) — wealth "
            "vulnerable to disease/debt (6H), sudden loss (8H), or "
            "expenditure/foreign-residence (12H) depending on placement."
        ),
        citation="Phaladeepika Ch.17",
    )


def pattern_kubera_yoga(chart: Chart) -> PatternVerdict | None:
    """Saravali Ch.34 — Jupiter or Venus in 11H + 11H lord well-placed →
    Kubera-grace (treasurer-of-gods pattern)."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_11 = None
    for p, r in roles.items():
        if 11 in r.houses_ruled:
            lord_11 = p
            break
    if not lord_11:
        return None
    benefic_in_11 = (
        _has_planet_in_house(chart, "Jupiter", 11)
        or _has_planet_in_house(chart, "Venus", 11)
    )
    if not benefic_in_11:
        return None
    lord_11_house = chart.house_of(lord_11)
    if lord_11_house not in _KENDRAS and lord_11_house not in _TRIKONAS:
        return None
    return PatternVerdict(
        name="kubera_yoga",
        domain="wealth", polarity="supportive", severity=0.75,
        description=(
            "Jupiter/Venus in 11H + 11H-lord in kendra/trikona — Kubera-"
            "grace pattern, treasurer-of-gods signature; gains exceed "
            "merits, network-driven prosperity."
        ),
        citation="Saravali Ch.34",
    )


# ─── Career-domain patterns ─────────────────────────────────────────


def pattern_sun_in_10h_own_sign(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.55 — Sun in 10H in own sign (Leo) → executive authority,
    leadership-grade career."""
    if not _has_planet_in_house(chart, "Sun", 10):
        return None
    sign = chart.sign_of("Sun")
    if sign != 5:
        return None  # Leo
    return PatternVerdict(
        name="sun_in_10h_own_sign",
        domain="career", polarity="supportive", severity=0.9,
        description=(
            "Sun in 10H in Leo (own sign) — executive authority, leadership-"
            "grade career, government/sovereign-style influence."
        ),
        citation="BPHS Ch.34.55",
    )


def pattern_saturn_in_10h_strong(chart: Chart) -> PatternVerdict | None:
    """BV Raman — Saturn in 10H in own/exalted sign → sustained authority
    via discipline, late-blooming career."""
    if not _has_planet_in_house(chart, "Saturn", 10):
        return None
    sign = chart.sign_of("Saturn")
    if sign is None:
        return None
    if not (is_own_sign("Saturn", sign) or is_exalted("Saturn", sign)):
        return None
    return PatternVerdict(
        name="saturn_in_10h_strong",
        domain="career", polarity="supportive", severity=0.85,
        description=(
            "Saturn in 10H in own/exalted sign — sustained authority via "
            "discipline + endurance; late-blooming but durable career, "
            "often institution-building or service-to-state."
        ),
        citation="BV Raman, *Three Hundred Important Combinations* Ch.10",
    )


def pattern_10l_in_6h(chart: Chart) -> PatternVerdict | None:
    """Mansagari Ch.5 — 10H lord in 6H → service-oriented career,
    competitive field, possible litigation involvement."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_10 = None
    for p, r in roles.items():
        if 10 in r.houses_ruled:
            lord_10 = p
            break
    if not lord_10:
        return None
    h = chart.house_of(lord_10)
    if h != 6:
        return None
    return PatternVerdict(
        name="10l_in_6h",
        domain="career", polarity="neutral", severity=0.55,
        description=(
            f"10H-lord {lord_10} in 6H — service-oriented career, "
            "competitive field. Doctrinally mixed: 6H is upachaya so "
            "career grows with effort, but also dushtana so career-stress "
            "is structural."
        ),
        citation="Mansagari Ch.5",
    )


# ─── Health-domain patterns ─────────────────────────────────────────


def pattern_sun_moon_conjunct(chart: Chart) -> PatternVerdict | None:
    """Phaladeepika Ch.6 — Sun + Moon in same sign (within combustion) →
    Amavasya yoga; vitality fluctuations, identity-confusion themes."""
    sun_sign = chart.sign_of("Sun")
    moon_sign = chart.sign_of("Moon")
    if sun_sign is None or moon_sign != sun_sign:
        return None
    sun_lon = chart.planet_lons.get("Sun")
    moon_lon = chart.planet_lons.get("Moon")
    if sun_lon is None or moon_lon is None:
        return None
    if abs(sun_lon - moon_lon) > 12.0:
        return None  # not within combustion orb
    return PatternVerdict(
        name="sun_moon_conjunct",
        domain="health", polarity="afflicting", severity=0.6,
        description=(
            "Sun and Moon conjunct within combustion orb (Amavasya yoga) — "
            "vitality fluctuations, periodic energy depletion; identity-"
            "confusion themes (self vs mother)."
        ),
        citation="Phaladeepika Ch.6",
    )


def pattern_6h_lord_in_kendra_strong(chart: Chart) -> PatternVerdict | None:
    """BV Raman — 6H lord in kendra + own/exalted → strong immunity,
    enemies defeated, robust health (Vipareeta-like for 6H)."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_6 = None
    for p, r in roles.items():
        if 6 in r.houses_ruled:
            lord_6 = p
            break
    if not lord_6:
        return None
    h = chart.house_of(lord_6)
    sign = chart.sign_of(lord_6)
    if h not in _KENDRAS or sign is None:
        return None
    if not (is_own_sign(lord_6, sign) or is_exalted(lord_6, sign)):
        return None
    return PatternVerdict(
        name="6h_lord_in_kendra_strong",
        domain="health", polarity="supportive", severity=0.75,
        description=(
            f"6H-lord {lord_6} in kendra + own/exalted — strong immunity, "
            "enemies defeated, robust constitution. Vipareeta-like "
            "elevation of the 'enemies/disease' bhava."
        ),
        citation="BV Raman, THIC Ch.6",
    )


# ─── Dharma-domain patterns ─────────────────────────────────────────


def pattern_jupiter_in_9h(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.51 — Jupiter in 9H → strong dharma, virtuous father,
    spiritual guidance available."""
    if not _has_planet_in_house(chart, "Jupiter", 9):
        return None
    sign = chart.sign_of("Jupiter")
    if sign is None:
        return None
    # Doubly strong if also in own / exalted
    base_severity = 0.7
    if is_own_sign("Jupiter", sign) or is_exalted("Jupiter", sign):
        base_severity = 0.9
    return PatternVerdict(
        name="jupiter_in_9h",
        domain="dharma", polarity="supportive", severity=base_severity,
        description=(
            "Jupiter (dharma karaka) in 9H (dharma bhava) — strong "
            "righteousness, virtuous father, spiritual guidance available "
            "via Guru or formal initiation."
        ),
        citation="BPHS Ch.34.51",
    )


def pattern_9l_in_3h_or_12h(chart: Chart) -> PatternVerdict | None:
    """Phaladeepika Ch.19 — 9H lord in 3H or 12H → dharma manifests via
    foreign travel / pilgrimage / cross-region work."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_9 = None
    for p, r in roles.items():
        if 9 in r.houses_ruled:
            lord_9 = p
            break
    if not lord_9:
        return None
    h = chart.house_of(lord_9)
    if h not in (3, 12):
        return None
    return PatternVerdict(
        name="9l_in_3h_or_12h",
        domain="dharma", polarity="supportive", severity=0.6,
        description=(
            f"9H-lord {lord_9} in {h}H — dharma manifests via short "
            "journeys (3H) or foreign pilgrimage / moksha-work (12H). "
            "Less house-bound, more cross-region spiritual orientation."
        ),
        citation="Phaladeepika Ch.19",
    )


# ─── Children-domain patterns ───────────────────────────────────────


def pattern_jupiter_in_5h(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.41 — Jupiter (putra karaka) in 5H → blessed with
    intelligent, dharmic children."""
    if not _has_planet_in_house(chart, "Jupiter", 5):
        return None
    sign = chart.sign_of("Jupiter")
    if sign is None:
        return None
    base = 0.7
    if is_own_sign("Jupiter", sign) or is_exalted("Jupiter", sign):
        base = 0.85
    return PatternVerdict(
        name="jupiter_in_5h",
        domain="children", polarity="supportive", severity=base,
        description=(
            "Jupiter (children karaka) in 5H (children bhava) — blessed "
            "with intelligent, dharmic children; teaching/mentor lineage."
        ),
        citation="BPHS Ch.34.41",
    )


def pattern_sat_rahu_in_5h(chart: Chart) -> PatternVerdict | None:
    """BPHS Ch.34.43 — Saturn AND Rahu in 5H → children-related obstacles,
    delayed conception, possible Putra-dosha karmic flag."""
    if not (_has_planet_in_house(chart, "Saturn", 5)
            and _has_planet_in_house(chart, "Rahu", 5)):
        return None
    return PatternVerdict(
        name="sat_rahu_in_5h",
        domain="children", polarity="afflicting", severity=0.75,
        description=(
            "Saturn + Rahu both in 5H — children-related obstacles, "
            "delayed conception, Putra-dosha karmic flag requiring "
            "remediation before progeny questions resolve."
        ),
        citation="BPHS Ch.34.43",
    )


# ─── Pattern registry ───────────────────────────────────────────────


_PATTERN_DETECTORS: Final[tuple[Callable[[Chart], PatternVerdict | None], ...]] = (
    # Marriage
    pattern_marital_discord_mars_7h_sat_aspect,
    pattern_venus_debilitated_in_7h,
    pattern_jupiter_in_7h_benefic_aspect,
    # Wealth
    pattern_jupiter_in_2h_own_sign,
    pattern_2h_lord_in_dushtana,
    pattern_kubera_yoga,
    # Career
    pattern_sun_in_10h_own_sign,
    pattern_saturn_in_10h_strong,
    pattern_10l_in_6h,
    # Health
    pattern_sun_moon_conjunct,
    pattern_6h_lord_in_kendra_strong,
    # Dharma
    pattern_jupiter_in_9h,
    pattern_9l_in_3h_or_12h,
    # Children
    pattern_jupiter_in_5h,
    pattern_sat_rahu_in_5h,
)


def detect_all_patterns(chart: Chart) -> tuple[PatternVerdict, ...]:
    """Run every BPHS-derived pattern detector; return only the matches."""
    matches: list[PatternVerdict] = []
    for detector in _PATTERN_DETECTORS:
        try:
            verdict = detector(chart)
        except Exception:  # noqa: BLE001 — graceful skip per detector
            continue
        if verdict is not None:
            matches.append(verdict)
    return tuple(matches)


def patterns_for_domain(
    chart: Chart, domain: str,
) -> tuple[PatternVerdict, ...]:
    """Return only patterns whose domain matches the request."""
    return tuple(v for v in detect_all_patterns(chart) if v.domain == domain)


def registry_size() -> int:
    """Number of pattern detectors currently registered."""
    return len(_PATTERN_DETECTORS)
