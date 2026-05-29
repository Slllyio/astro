"""Tests for ``app.reading.computations.remedies.gemstones``.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs) + classical lagna-suitability gating. Gemstones
strengthen a planet; strengthening a functional malefic is karmically
DANGEROUS. So gem recommendations are STRICTLY gated:

  Eligibility (positive recommendation):
    planet in {lagna_lord, fifth_lord, ninth_lord, atmakaraka}
    AND functional_natures[planet] in {"yogakaraka", "functional_benefic"}

  Blockage (negative recommendation, must be surfaced):
    functional_natures[planet] == "functional_malefic"

  No-op (silent):
    everything else (functional_neutral planet not in the trio+AK)

Canonical lagna-blocking rules (NON-NEGOTIABLE practitioner-locked):
  - Blue Sapphire (Saturn) BLOCKED for Aries (1), Leo (5), Cancer (4), Scorpio (8).
  - Yellow Sapphire (Jupiter) BLOCKED for Taurus (2), Libra (7), Capricorn (10).

Each blocking is verified DIRECTLY via the functional_nature mapping (no
hand-encoded lagna list). The asc_sign is recorded in evidence for trace.

ID grammar: ``practitioner.remedies.gemstone.<gem_slug>`` (gem slug
lowercased, spaces->underscores).
classification: ``"primitive"``.
direction: ``"positive"`` (safe) | ``"negative"`` (BLOCKED).
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# (gem, planet, gem-slug used in Finding id) — verbatim per practitioner table.
_GEM_PLANET_TABLE = [
    ("Ruby",            "Sun",     "ruby"),
    ("Pearl",           "Moon",    "pearl"),
    ("Red Coral",       "Mars",    "red_coral"),
    ("Emerald",         "Mercury", "emerald"),
    ("Yellow Sapphire", "Jupiter", "yellow_sapphire"),
    ("Diamond",         "Venus",   "diamond"),
    ("Blue Sapphire",   "Saturn",  "blue_sapphire"),
    ("Hessonite",       "Rahu",    "hessonite"),
    ("Cat's Eye",       "Ketu",    "cats_eye"),
]


def _natures_all(label: str) -> dict[str, str]:
    """Helper: build a functional_natures dict where every planet has `label`."""
    return {p: label for p in _PLANETS}


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestRecommendGemstonesShape:
    """Construction / type / id / classification invariants."""

    def test_returns_finding_list(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones
        from app.reading.schema import Finding

        result = recommend_gemstones(
            lagna_lord="Mars",
            fifth_lord="Sun",
            ninth_lord="Jupiter",
            atmakaraka="Jupiter",
            asc_sign=1,
            functional_natures=_natures_all("functional_neutral"),
        )
        assert isinstance(result, list)
        for f in result:
            assert isinstance(f, Finding)

    def test_all_findings_are_primitive(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        for f in result:
            assert f.classification == "primitive"

    def test_verdicts_under_140_chars(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_malefic")
        nats["Mars"] = "yogakaraka"
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        for f in result:
            assert len(f.verdict) <= 140, f"verdict too long: {f.verdict!r}"

    def test_rule_field(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Jupiter"] = "functional_benefic"
        result = recommend_gemstones(
            lagna_lord="Jupiter", fifth_lord="Mars", ninth_lord="Sun",
            atmakaraka="Jupiter", asc_sign=9, functional_natures=nats,
        )
        assert any(f.rule == "gemstone_remedy" for f in result)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        with pytest.raises(ValueError):
            recommend_gemstones(
                lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
                atmakaraka="Mars", asc_sign=13,
                functional_natures=_natures_all("functional_neutral"),
            )
        with pytest.raises(ValueError):
            recommend_gemstones(
                lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
                atmakaraka="Mars", asc_sign=0,
                functional_natures=_natures_all("functional_neutral"),
            )


# ---------------------------------------------------------------------------
# Eligibility (positive recommendations)
# ---------------------------------------------------------------------------


class TestPositiveEligibility:
    """A gemstone is recommended POSITIVE iff:
       planet in {lagna_lord, fifth_lord, ninth_lord, atmakaraka}
       AND functional_natures[planet] in {yogakaraka, functional_benefic}.
    """

    def test_lagna_lord_benefic_gets_gem(self):
        """Mars as Aries lagna lord (functional_benefic) -> Red Coral recommended."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Sun", asc_sign=1, functional_natures=nats,
        )
        positives = [f for f in result if f.direction == "positive"]
        gem_ids = [f.id for f in positives]
        assert "practitioner.remedies.gemstone.red_coral" in gem_ids

    def test_yogakaraka_gets_gem(self):
        """Mars as Cancer YK (5L+10L) — eligible for Red Coral."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "yogakaraka"
        nats["Moon"] = "functional_benefic"
        result = recommend_gemstones(
            lagna_lord="Moon", fifth_lord="Mars", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=4, functional_natures=nats,
        )
        positives = [f for f in result if f.direction == "positive"]
        assert any(f.id == "practitioner.remedies.gemstone.red_coral" for f in positives)

    def test_atmakaraka_benefic_gets_gem(self):
        """Atmakaraka eligible even if not 1L/5L/9L, when functional_benefic."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Venus"] = "functional_benefic"
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Venus", asc_sign=1, functional_natures=nats,
        )
        positives = [f for f in result if f.direction == "positive"]
        assert any(f.id == "practitioner.remedies.gemstone.diamond" for f in positives)

    def test_non_eligible_planet_silent(self):
        """A functional_benefic NOT in {1L,5L,9L,AK} -> no positive Finding."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mercury"] = "functional_benefic"  # benefic but not in trio
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        emerald_pos = [
            f for f in result
            if f.id == "practitioner.remedies.gemstone.emerald" and f.direction == "positive"
        ]
        assert emerald_pos == []

    def test_neutral_planet_in_trio_not_recommended(self):
        """A planet in the eligible trio but functional_neutral -> no gem."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        result = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        pos = [f for f in result if f.direction == "positive"]
        assert pos == []


# ---------------------------------------------------------------------------
# Blockage (negative findings — the critical practitioner invariant)
# ---------------------------------------------------------------------------


class TestBlockageInvariant:
    """The NON-NEGOTIABLE practitioner rule: a gem corresponding to a
    functional_malefic planet must be BLOCKED (negative direction)."""

    def test_blue_sapphire_blocked_for_aries_lagna(self):
        """D-7 says Saturn is functional_malefic for Aries lagna. Blue
        sapphire MUST be blocked. THIS IS THE CRITICAL INVARIANT."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        nats["Saturn"] = "functional_malefic"   # Aries: Saturn = 10L+11L mal
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Jupiter", asc_sign=1, functional_natures=nats,
        )
        blue_sapphire = [
            f for f in findings if "blue sapphire" in f.verdict.lower()
        ]
        assert blue_sapphire, "Blue sapphire blocking Finding missing for Aries"
        assert all(f.direction == "negative" for f in blue_sapphire), (
            "Blue sapphire must be BLOCKED for Aries lagna"
        )

    def test_blue_sapphire_blocked_for_leo_lagna(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"   # Leo: Saturn = 6L+7L mal
        findings = recommend_gemstones(
            lagna_lord="Sun", fifth_lord="Jupiter", ninth_lord="Mars",
            atmakaraka="Sun", asc_sign=5, functional_natures=nats,
        )
        blue_sapphire = [
            f for f in findings if "blue sapphire" in f.verdict.lower()
        ]
        assert blue_sapphire
        assert all(f.direction == "negative" for f in blue_sapphire)

    def test_blue_sapphire_blocked_for_cancer_lagna(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"   # Cancer: Saturn = 7L+8L mal
        findings = recommend_gemstones(
            lagna_lord="Moon", fifth_lord="Mars", ninth_lord="Jupiter",
            atmakaraka="Moon", asc_sign=4, functional_natures=nats,
        )
        blue_sapphire = [
            f for f in findings if "blue sapphire" in f.verdict.lower()
        ]
        assert blue_sapphire
        assert all(f.direction == "negative" for f in blue_sapphire)

    def test_yellow_sapphire_blocked_for_taurus_lagna(self):
        """Taurus: Jupiter=8L+11L (functional_malefic). Yellow sapphire BLOCKED."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Jupiter"] = "functional_malefic"
        findings = recommend_gemstones(
            lagna_lord="Venus", fifth_lord="Mercury", ninth_lord="Saturn",
            atmakaraka="Venus", asc_sign=2, functional_natures=nats,
        )
        yellow_sapphire = [
            f for f in findings if "yellow sapphire" in f.verdict.lower()
        ]
        assert yellow_sapphire
        assert all(f.direction == "negative" for f in yellow_sapphire)

    def test_yellow_sapphire_blocked_for_libra_lagna(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Jupiter"] = "functional_malefic"   # Libra: Jupiter=3L+6L mal
        findings = recommend_gemstones(
            lagna_lord="Venus", fifth_lord="Saturn", ninth_lord="Mercury",
            atmakaraka="Venus", asc_sign=7, functional_natures=nats,
        )
        yellow_sapphire = [
            f for f in findings if "yellow sapphire" in f.verdict.lower()
        ]
        assert yellow_sapphire
        assert all(f.direction == "negative" for f in yellow_sapphire)

    def test_yellow_sapphire_blocked_for_capricorn_lagna(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Jupiter"] = "functional_malefic"   # Cap: Jupiter=3L+12L mal
        findings = recommend_gemstones(
            lagna_lord="Saturn", fifth_lord="Venus", ninth_lord="Mercury",
            atmakaraka="Saturn", asc_sign=10, functional_natures=nats,
        )
        yellow_sapphire = [
            f for f in findings if "yellow sapphire" in f.verdict.lower()
        ]
        assert yellow_sapphire
        assert all(f.direction == "negative" for f in yellow_sapphire)

    def test_blocking_finding_id_includes_gem_slug(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        blockings = [f for f in findings if f.direction == "negative"]
        assert any(f.id == "practitioner.remedies.gemstone.blue_sapphire" for f in blockings)

    def test_no_block_for_yk_planet(self):
        """A planet which is yogakaraka must NEVER be blocked."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "yogakaraka"
        findings = recommend_gemstones(
            lagna_lord="Moon", fifth_lord="Mars", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=4, functional_natures=nats,
        )
        # Red Coral may appear as positive but never negative for this Mars
        coral = [
            f for f in findings if f.id == "practitioner.remedies.gemstone.red_coral"
        ]
        assert coral, "Red Coral missing"
        assert all(f.direction == "positive" for f in coral)


# ---------------------------------------------------------------------------
# Evidence + doctrine sentinel
# ---------------------------------------------------------------------------


class TestEvidence:
    """Evidence must record asc_sign, planet, gem, nature, and doctrine."""

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        for f in findings:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")),
                None,
            )
            assert doctrine is not None, f"{f.id} missing doctrine sentinel"
            assert "practitioner" in doctrine.lower()

    def test_evidence_contains_asc_sign(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        coral = next(
            (f for f in findings if f.id == "practitioner.remedies.gemstone.red_coral"),
            None,
        )
        assert coral is not None
        asc_evidence = next(
            (e for e in coral.evidence if e.startswith("asc_sign=")),
            None,
        )
        assert asc_evidence == "asc_sign=1"

    def test_blocking_evidence_records_nature(self):
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Saturn"] = "functional_malefic"
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Mars", asc_sign=1, functional_natures=nats,
        )
        blue = next(
            (f for f in findings if f.id == "practitioner.remedies.gemstone.blue_sapphire"),
            None,
        )
        assert blue is not None
        nature_evidence = next(
            (e for e in blue.evidence if e.startswith("nature=")),
            None,
        )
        assert nature_evidence == "nature=functional_malefic"


# ---------------------------------------------------------------------------
# Gem-to-planet table integrity
# ---------------------------------------------------------------------------


class TestGemPlanetTable:
    """The GEMSTONE_PLANET_TABLE constant is exported and pinned."""

    def test_table_exists(self):
        from app.reading.computations.remedies.gemstones import GEMSTONE_PLANET_TABLE

        assert isinstance(GEMSTONE_PLANET_TABLE, dict)
        # 9 planets each map to exactly one gem
        assert set(GEMSTONE_PLANET_TABLE.keys()) == set(_PLANETS)

    @pytest.mark.parametrize("gem,planet,slug", _GEM_PLANET_TABLE)
    def test_table_cell(self, gem, planet, slug):
        from app.reading.computations.remedies.gemstones import GEMSTONE_PLANET_TABLE

        cell = GEMSTONE_PLANET_TABLE[planet]
        assert cell["gem"] == gem
        assert cell["slug"] == slug


# ---------------------------------------------------------------------------
# Multi-planet combinations
# ---------------------------------------------------------------------------


class TestMultiPlanet:
    """Realistic scenario tests: Aries lagna with Saturn malefic, Mars benefic."""

    def test_aries_lagna_typical_scenario(self):
        """Aries: Mars=1L ben, Saturn=10L+11L mal, Jupiter=9L ben.
        Expect: Red Coral positive (Mars), Yellow Sapphire positive
        (Jupiter as 9L), Blue Sapphire blocked (Saturn malefic)."""
        from app.reading.computations.remedies.gemstones import recommend_gemstones

        nats = _natures_all("functional_neutral")
        nats["Mars"] = "functional_benefic"      # 1L
        nats["Jupiter"] = "functional_benefic"   # 9L
        nats["Saturn"] = "functional_malefic"    # blocked
        findings = recommend_gemstones(
            lagna_lord="Mars", fifth_lord="Sun", ninth_lord="Jupiter",
            atmakaraka="Jupiter", asc_sign=1, functional_natures=nats,
        )
        ids_pos = {f.id for f in findings if f.direction == "positive"}
        ids_neg = {f.id for f in findings if f.direction == "negative"}
        assert "practitioner.remedies.gemstone.red_coral" in ids_pos
        assert "practitioner.remedies.gemstone.yellow_sapphire" in ids_pos
        assert "practitioner.remedies.gemstone.blue_sapphire" in ids_neg
