"""Shared infrastructure for BPHS-compliance tests.

Phase 0 deliverable. Every yoga / dignity / strength rule that ships
under the Round 9 plan MUST be paired with a test that:

  1. Cites a Brihat Parashara Hora Shastra (BPHS) sloka (or commonly-
     accepted derivative source) for the rule.
  2. Asserts behavioral correctness on at least one canonical chart
     (presence/absence + strength ordering — Tier 1).
  3. Optionally asserts numeric correctness within ±5% of a reference
     software output (Jagannatha Hora / Parashara's Light — Tier 2).

Why this exists:
    The Round-9 wedge audit found three sign-coherent classical-fidelity
    bugs in a single yoga (Vipareeta Harsha), each silently passing the
    existing test suite because the tests didn't pin against external
    classical sources. This infrastructure prevents that recurrence.

Usage in a test:

    from tests.bphs_compliance import (
        BPHSCitation, RefChart, bphs, compute_reference_chart,
    )

    HAMSA_CITATION = BPHSCitation(
        sloka="BPHS 36.3-4 (Yogadhyaya, Hamsa Yoga)",
        source_book="Brihat Parashara Hora Shastra",
        chosen_convention="Jupiter exalted/own-sign in kendra from Lagna",
        alternatives_considered=("Mantreshwara Phaladeepika has same rule",),
        notes="Some texts also require Jupiter not be combust.",
    )

    @bphs(HAMSA_CITATION)
    def test_hamsa_on_indira_gandhi_chart() -> None:
        chart = compute_reference_chart("indira_gandhi")
        # ... Tier 1 behavioral assertion ...

Tier 1 (behavioral) failures STOP the build.
Tier 2 (numeric ±5%) failures are documented in `docs/bphs_reference.md`
and continued — they often reflect tradition / software-recension
differences rather than bugs.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import pytest

# --------------------------------------------------------------------------- #
# Citation metadata                                                           #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class BPHSCitation:
    """Metadata pinning a classical rule to a documented source.

    Every rule lookup (dignity, yoga, strength sub-component) carries one of
    these to make tradition choices auditable. When traditions disagree
    (e.g., Mercury combustion orb 13° vs 14°), the chosen convention is
    explicit and the alternative is listed.
    """

    sloka: str                                # e.g. "BPHS 36.3-4"
    source_book: str = "Brihat Parashara Hora Shastra"
    source_translation: str = "Santhanam"     # which translation we anchor to
    chosen_convention: str = ""               # what the code does
    alternatives_considered: tuple[str, ...] = ()
    notes: str = ""


# --------------------------------------------------------------------------- #
# pytest marker                                                               #
# --------------------------------------------------------------------------- #

F = TypeVar("F", bound=Callable[..., Any])


def bphs(citation: BPHSCitation) -> Callable[[F], F]:
    """Decorator that tags a test with its BPHS citation.

    Attaches the citation as a pytest marker so test reports can surface
    which sloka each test pins. Also stamps the citation on the function
    object so other test infrastructure can introspect it.
    """

    marker = pytest.mark.bphs(citation=citation)

    def decorator(fn: F) -> F:
        marked = marker(fn)
        marked.__bphs_citation__ = citation  # type: ignore[attr-defined]
        return marked

    return decorator


# --------------------------------------------------------------------------- #
# Reference-chart registry                                                    #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class RefChart:
    """A canonical chart used for behavioral pinning across the test suite.

    The five Round-9 reference charts (per `implementation_plan_round9.md`
    Phase 0) are registered below. New reference charts can be appended
    — keep the registry conservative: each addition costs time per yoga
    detector to verify.
    """

    slug: str
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz_offset: float
    latitude: float
    longitude: float
    rodden_rating: str  # "AA", "A", "B", "C" — confidence in birth time
    source: str         # where the birth data was sourced
    notes: str = ""


# Five canonical charts per the Round-9 plan.
# birth data sourced from Astro-Databank / published biographies.
# Tier-2 numeric pinning details should be added to docs/bphs_reference.md.
REFERENCE_CHARTS: dict[str, RefChart] = {
    "bangalore_baseline": RefChart(
        slug="bangalore_baseline",
        name="Bangalore baseline (project anchor)",
        year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5,
        latitude=12.97, longitude=77.59,
        rodden_rating="AA",
        source="Project's canonical pinning chart since round 1.",
        notes=(
            "Mercury MD 1978-03-26 to 1995-03-26. "
            "Virgo Lagna (~173.99°). Moon in Revati pada 3. "
            "Saturn Avastha Mrita / Swapna."
        ),
    ),
    "ramana_maharshi": RefChart(
        slug="ramana_maharshi",
        name="Ramana Maharshi",
        # IST didn't exist in 1879; use LMT for Tiruchuli longitude 78.16°E
        # → 78.16 / 15 = 5.211h. Astro-Databank rating B (per Natarajan).
        year=1879, month=12, day=30, hour=1, minute=0, tz_offset=5.211,
        latitude=9.65, longitude=78.16,
        rodden_rating="B",
        source="Astro-Databank entry (Natarajan 'Timeless in Time'). LMT 78.16°E.",
        notes=(
            "Tiruchuli, Tamil Nadu. Libra Lagna at 2-3° (vargottama) per "
            "VedAstro + AstroSage + Lagna360 consensus. Moon in Punarvasu "
            "p3 (Gemini). Jupiter MD at birth."
        ),
    ),
    "jiddu_krishnamurti": RefChart(
        slug="jiddu_krishnamurti",
        name="J. Krishnamurti",
        # IST adopted in India 1906; for 1895 use LMT for Madanapalle 78.50°E
        # → 78.50 / 15 = 5.233h.
        year=1895, month=5, day=12, hour=0, minute=30, tz_offset=5.233,
        latitude=13.55, longitude=78.50,
        rodden_rating="C",
        source="Astro-Databank (Rodden C — disputed). Madanapalle LMT.",
        notes="Birth-time disputed; tests lenient (±1 sign on lagna).",
    ),
    "indira_gandhi": RefChart(
        slug="indira_gandhi",
        name="Indira Gandhi",
        year=1917, month=11, day=19, hour=23, minute=11, tz_offset=5.5,
        latitude=25.45, longitude=81.85,
        rodden_rating="AA",
        source="Astro-Databank from autobiography. Allahabad / Prayagraj.",
        notes="Cancer ascendant; Jupiter exalted in Cancer → Hamsa Yoga.",
    ),
    "mother_teresa": RefChart(
        slug="mother_teresa",
        name="Mother Teresa",
        year=1910, month=8, day=26, hour=13, minute=25, tz_offset=1.43,
        latitude=41.99, longitude=21.42,
        rodden_rating="DD",   # Astro-Databank: Data Doubtful (not AA)
        source=(
            "Astro-Databank (Rodden DD). Skopje LMT (21.42°E/15). "
            "Engine outputs Scorpio (8) lagna; many Vedic readings cite "
            "Sagittarius (9) — depends on LMT vs CET interpretation."
        ),
        notes=(
            "Time-zone interpretation contested. Tests should be lenient: "
            "accept Scorpio (8) OR Sagittarius (9) lagna."
        ),
    ),
}


def compute_reference_chart(slug: str) -> dict[str, Any]:
    """Compute the full chart bundle for one of the registered reference
    charts.

    Delegates to `app.core.ephemeris_engine.calculate_all_charts`. The
    engine already adds Ketu inline and emits keys ``d1`` / ``d9`` /
    ``d10`` / ``current_mahadasha`` (NOT ``d1_chart`` / ``mahadasha`` —
    those are common typos worth keeping in mind). Convenience aliases
    ``d1_chart`` and ``mahadasha`` are added here for ergonomic test code.
    """
    from app.core.ephemeris_engine import calculate_all_charts

    if slug not in REFERENCE_CHARTS:
        raise KeyError(
            f"unknown reference chart {slug!r}; valid: {list(REFERENCE_CHARTS)}"
        )
    chart_meta = REFERENCE_CHARTS[slug]
    full = calculate_all_charts(
        chart_meta.year, chart_meta.month, chart_meta.day,
        chart_meta.hour, chart_meta.minute, chart_meta.tz_offset,
        chart_meta.latitude, chart_meta.longitude,
    )
    # Convenience aliases so test code can read either form.
    full["d1_chart"] = full["d1"]
    full["mahadasha"] = full["current_mahadasha"]
    full["chart_meta"] = chart_meta  # for diagnostic output on failures
    return full


# --------------------------------------------------------------------------- #
# Module-level marker registration                                            #
# --------------------------------------------------------------------------- #

# Register the custom marker so pytest doesn't warn about it. Tests can then
# be filtered via `pytest -m bphs` to run only BPHS-compliance tests.
def pytest_configure(config: Any) -> None:  # pragma: no cover - pytest hook
    config.addinivalue_line(
        "markers",
        "bphs(citation): mark a test as BPHS-compliance-pinned; "
        "citation is a BPHSCitation instance",
    )
