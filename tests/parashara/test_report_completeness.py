"""Report-completeness guard — every computed surface must render (CLAUDE.md REPORT COMPLETENESS).

Builds one full reading and asserts each doctrine section the engine now computes appears in
`to_markdown`, so a future refactor cannot silently drop a section. Conditional sections (dignity
concentrations, which need >=2 grahas sharing a dignity) are covered by their own module tests; this
pins every surface that is unconditional on a real cast chart.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.reading import read
from app.parashara.render import to_markdown

# Section markers that MUST appear for any cast chart (the canonical baseline exercises them all).
_REQUIRED_MARKERS = (
    "## House significations — Parashara's effects of each house (BPHS ch.12–23)",
    "## Planet-in-house effects (Saravali ch.30)",
    "## Two-planet conjunctions (Saravali ch.15)",
    "Three grahas sharing a sign (Saravali ch.16)",   # canonical: Sun+Jupiter+Venus conjunct
    "## Dignity concentrations (Saravali ch.45)",      # always shown now (else: 'none')
    "## Chara karakas & Karakamsa (BPHS ch.32",
    "Parashara's effects by the Karakamsa's sign",     # ch.33 sign passage
    "## Upagrahas",                                    # ch.3 sub-planets
    "Effect of each upagraha in the house",            # ch.25 house-effects
    "## Shodasavarga",                                 # ch.6-7 divisional table
    "What each varga is read for (BPHS-7:",            # ch.7 use-domains
    "## Special ascendants (BPHS ch.5)",               # ch.5 Bhava/Hora/Ghati lagna
    "## Sudarshana Chakra",                            # ch.74 three-lagna
    "## Arudha padas (BPHS ch.29",                     # ch.29-30 padas
    "**Pada & finance (BPHS-29:8-15):**",              # ch.29 gains
    "**Spouse from the Upapada (BPHS-30:7-12):**",     # ch.30 marriage
    "## Wealth (Dhana) yogas (BPHS ch.41)",            # ch.41 wealth yogas
    "## Penury (Daridra) yogas (BPHS ch.42)",          # ch.42 penury yogas
    "## Royal-association yogas (BPHS ch.40)",          # ch.40 royal yogas
    "## Drekkana",                                     # ch.6 decanates
    "### After the four haranas (BPHS-43:567)",        # Nisargayu reductions
    "### Complete span",                               # Nisargayu + ascendant
)


@pytest.fixture(scope="module")
def report() -> str:
    ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
              tz_offset=5.5, latitude=12.97, longitude=77.59)
    return to_markdown(read(ch))


@pytest.mark.parametrize("marker", _REQUIRED_MARKERS)
def test_section_renders(report: str, marker: str):
    assert marker in report, f"reading dropped a computed section: {marker!r}"


def test_reading_fields_are_populated():
    ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
              tz_offset=5.5, latitude=12.97, longitude=77.59)
    r = read(ch)
    # spot-check the loop-added fields exist and are non-empty
    assert len(r.planet_house_effects) == 7
    assert len(r.upagrahas) == 5 and len(r.upagraha_house_effects) == 5
    assert len(r.shodasavarga) == 9 and len(r.sudarshana) == 9 and len(r.drekkanas) == 9
    assert len(r.arudhas) == 12
    assert r.pada_finance is not None and r.spouse_from_upapada is not None
    assert r.nisargayu_full.total_years > 0
    assert r.chara_karakas["AK"] not in ("Rahu", "Ketu")
