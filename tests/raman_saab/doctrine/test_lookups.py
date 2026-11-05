"""Guard + pin tests for app/raman_saab/doctrine/lookups/ (special-grid lookups).

Spec (doctrinal review promotion #6 — encode special grids as doctrine data):
  1. Every row of every lookup carries >=1 ``Citation`` that resolves to a real
     on-disk corpus line (``sources.verify``).
  2. Known-value accessor pins per table, against the printed methodology text.
  3. Accessors validate input (ValueError on garbage) and return ``None`` where
     the printed source is silent (Mercury inversion, Leo/Aquarius confinement,
     Venus organ, node tridosha) — silence is faithful, not an oversight.

Usage:
    py -3.12 -m pytest tests/raman_saab/doctrine/test_lookups.py -q
"""
from __future__ import annotations

import dataclasses

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.doctrine.lookups.bhavartha_ratnakara import (
    KARAKA_IN_12_INVERSIONS,
    karaka_in_12_inversion,
)
from app.raman_saab.doctrine.lookups.confinement_modes import (
    CONFINEMENT_MODES,
    confinement_mode,
)
from app.raman_saab.doctrine.lookups.decanate_cause import (
    DECANATE_CAUSES,
    cause_of_death_fallback,
)
from app.raman_saab.doctrine.lookups.disease_map import (
    PLANET_ORGANS,
    PLANET_SEASONS,
    PLANET_TRIDOSHAS,
    organ_of,
    season_of,
    tridosha_of,
)
from app.raman_saab.doctrine.lookups.source_of_gains import (
    PLANET_IN_11TH_GAINS,
    SECOND_LORD_HOUSE_GAINS,
    gains_via_second_lord,
    source_of_gains,
)
from app.raman_saab.doctrine.sources import verify

# ---------------------------------------------------------------------------
# Helpers — flatten every row of every lookup into (row_id, record) pairs
# ---------------------------------------------------------------------------

_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Classical drekkana lords: 1st = sign lord, 2nd = lord of 5th sign therefrom,
# 3rd = lord of 9th sign therefrom (local copy — no engine imports in this test).
_SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


def _all_rows() -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    rows += [(f"decanate:{s}:{i}", r) for (s, i), r in DECANATE_CAUSES.items()]
    rows += [(f"gains11:{p}", r) for p, r in PLANET_IN_11TH_GAINS.items()]
    rows += [(f"gains2L:H{h}", r) for h, r in SECOND_LORD_HOUSE_GAINS.items()]
    rows += [(f"bhavartha:{p}", r) for p, r in KARAKA_IN_12_INVERSIONS.items()]
    rows += [(f"confine:{s}", r) for s, r in CONFINEMENT_MODES.items()]
    rows += [(f"organ:{p}", r) for p, r in PLANET_ORGANS.items()]
    rows += [(f"dosha:{p}", r) for p, r in PLANET_TRIDOSHAS.items()]
    rows += [(f"season:{p}", r) for p, r in PLANET_SEASONS.items()]
    return rows


_CITATION_PARAMS = [
    pytest.param(cit, id=f"{row_id}@{cit.work}:{cit.line}")
    for row_id, record in _all_rows()
    for cit in record.sources  # type: ignore[attr-defined]
]

_REGISTRIES = [
    pytest.param(DECANATE_CAUSES, id="DECANATE_CAUSES"),
    pytest.param(PLANET_IN_11TH_GAINS, id="PLANET_IN_11TH_GAINS"),
    pytest.param(SECOND_LORD_HOUSE_GAINS, id="SECOND_LORD_HOUSE_GAINS"),
    pytest.param(KARAKA_IN_12_INVERSIONS, id="KARAKA_IN_12_INVERSIONS"),
    pytest.param(CONFINEMENT_MODES, id="CONFINEMENT_MODES"),
    pytest.param(PLANET_ORGANS, id="PLANET_ORGANS"),
    pytest.param(PLANET_TRIDOSHAS, id="PLANET_TRIDOSHAS"),
    pytest.param(PLANET_SEASONS, id="PLANET_SEASONS"),
]


class TestRegistryImmutability:
    """The module-level lookup registries are read-only mapping proxies."""

    @pytest.mark.parametrize("registry", _REGISTRIES)
    def test_registry_rejects_mutation(self, registry) -> None:
        """Assigning into a doctrine registry raises TypeError (MappingProxyType)."""
        with pytest.raises(TypeError):
            registry["__intruder__"] = None  # type: ignore[index]


# ---------------------------------------------------------------------------
# 1. Citation integrity — EVERY row of EVERY lookup resolves on disk
# ---------------------------------------------------------------------------

class TestCitationIntegrity:
    """Every lookup row cites a real on-disk corpus line."""

    @needs_corpus
    @pytest.mark.parametrize("citation", _CITATION_PARAMS)
    def test_citation_resolves_on_disk(self, citation) -> None:
        """The cited work/line pair exists in the corpus under data/knowledge_library."""
        assert verify(citation), f"dangling citation {citation.work}:{citation.line}"

    def test_every_row_has_at_least_one_citation(self) -> None:
        """No uncited doctrine: each record carries a non-empty sources tuple."""
        for row_id, record in _all_rows():
            assert record.sources, f"{row_id} has no citation"  # type: ignore[attr-defined]

    def test_all_records_are_frozen(self) -> None:
        """Doctrine data is immutable (frozen dataclasses)."""
        for row_id, record in _all_rows():
            with pytest.raises(dataclasses.FrozenInstanceError):
                record.__setattr__("sources", ())  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Decanate cause-of-death grid (H8, HTJAH-II:3736-3845)
# ---------------------------------------------------------------------------

class TestDecanateCause:
    """22nd-drekkana decanate -> cause-of-death fallback grid (36 cells)."""

    def test_grid_is_complete_36_cells(self) -> None:
        """All 12 signs x 3 decanates are present — the mandatory fallback never misses."""
        assert len(DECANATE_CAUSES) == 36
        for sign in _SIGNS:
            for idx in (1, 2, 3):
                assert (sign, idx) in DECANATE_CAUSES

    def test_printed_lords_follow_classical_drekkana_scheme(self) -> None:
        """Raman's printed decanate lords = lords of the 1st/5th/9th signs therefrom."""
        for (sign, idx), rec in DECANATE_CAUSES.items():
            start = _SIGNS.index(sign)
            expected = _SIGN_LORDS[_SIGNS[(start + 4 * (idx - 1)) % 12]]
            assert rec.decanate_lord == expected, f"{sign} decanate {idx}"

    def test_aries_first_decanate_is_mars_spleen(self) -> None:
        """HTJAH-II:3738 — Aries 1st decanate (Mars): spleen/bilious complaints or poisoning."""
        rec = cause_of_death_fallback("Aries", 1)
        assert rec.decanate_lord == "Mars"
        assert "spleen" in rec.cause

    def test_capricorn_second_decanate_is_venus_snake_bite(self) -> None:
        """HTJAH-II:3825 — Capricorn 2nd decanate (Venus): snake-bite."""
        rec = cause_of_death_fallback("Capricorn", 2)
        assert rec.decanate_lord == "Venus"
        assert "snake-bite" in rec.cause

    def test_pisces_third_decanate_is_mars_stomach_distension(self) -> None:
        """HTJAH-II:3844 — Pisces 3rd decanate (Mars): distension of the stomach."""
        rec = cause_of_death_fallback("Pisces", 3)
        assert rec.decanate_lord == "Mars"
        assert "distension of the stomach" in rec.cause

    def test_rejects_bad_sign_and_bad_index(self) -> None:
        """Garbage input fails fast with ValueError (boundary validation)."""
        with pytest.raises(ValueError):
            cause_of_death_fallback("Arise", 1)
        with pytest.raises(ValueError):
            cause_of_death_fallback("Aries", 4)
        with pytest.raises(ValueError):
            cause_of_death_fallback("Aries", 0)


# ---------------------------------------------------------------------------
# 3. Source of gains (H11, HTJAH-II:14373-14386 + 2nd-lord variant HTJAH-I:2504-2512)
# ---------------------------------------------------------------------------

class TestSourceOfGains:
    """Planet-in-11th -> income channel, plus 2nd-lord-placement variant."""

    def test_covers_seven_grahas(self) -> None:
        """Raman's 11th-house income list names exactly the 7 visible planets."""
        assert set(PLANET_IN_11TH_GAINS) == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
        }

    def test_sun_in_11th_gives_inheritance(self) -> None:
        """HTJAH-II:14374-14375 — Sun in the 11th: fortune as an inheritance."""
        assert "inheritance" in source_of_gains("Sun")

    def test_venus_in_11th_gives_fine_arts(self) -> None:
        """HTJAH-II:14384-14385 — Venus: dance, drama, cinema, fine arts, music, women."""
        channel = source_of_gains("Venus")
        assert "fine arts" in channel and "music" in channel

    def test_saturn_in_11th_gives_industries_labour_agriculture(self) -> None:
        """HTJAH-II:14386 — Saturn: wealth through industries, labour and agriculture."""
        assert source_of_gains("Saturn") == "industries, labour and agriculture"

    def test_second_lord_variant_covers_all_12_houses(self) -> None:
        """HTJAH-I:2504-2512 — 2nd lord in each of the 12 houses names a source."""
        assert set(SECOND_LORD_HOUSE_GAINS) == set(range(1, 13))

    def test_second_lord_in_8th_gives_legacies_and_enemies(self) -> None:
        """HTJAH-I:2510 — 2nd lord in the 8th: legacies and enemies."""
        assert "legacies" in gains_via_second_lord(8)

    def test_second_lord_in_1st_gives_own_exertion(self) -> None:
        """HTJAH-I:2505 — 2nd lord in the 1st: own exertions / manual labour."""
        assert "exertion" in gains_via_second_lord(1)

    def test_rejects_unknown_planet_and_house(self) -> None:
        """Garbage input fails fast with ValueError (boundary validation)."""
        with pytest.raises(ValueError):
            source_of_gains("Pluto")
        with pytest.raises(ValueError):
            gains_via_second_lord(13)


# ---------------------------------------------------------------------------
# 4. Bhavartha Ratnakara karaka-in-12 inversion (H12, HTJAH-II:16543-16569)
# ---------------------------------------------------------------------------

class TestBhavarthaRatnakara:
    """Karaka in the 12th from Lagna -> fortunate in that karaka's own bhava(s)."""

    def test_sun_in_12_fortunate_re_9th(self) -> None:
        """HTJAH-II:16561+16564-16566 — Sun in 12th: fortunate re 9th-house matters."""
        result = karaka_in_12_inversion("Sun")
        assert result is not None and "9th" in result

    def test_moon_in_12_fortunate_re_4th(self) -> None:
        """HTJAH-II:16552 (OCR-truncated) restored from 16566-16567 — Moon: 4th house."""
        result = karaka_in_12_inversion("Moon")
        assert result is not None and "4th" in result

    def test_venus_in_12_fortunate_re_7th(self) -> None:
        """HTJAH-II:16555+16568 — Venus in 12th: fortunate re 7th-house indications."""
        result = karaka_in_12_inversion("Venus")
        assert result is not None and "7th" in result

    def test_mercury_has_no_printed_karaka_role(self) -> None:
        """HTJAH-II:16549-16563 assigns Mercury no bhava — None is faithful to source."""
        assert karaka_in_12_inversion("Mercury") is None
        assert KARAKA_IN_12_INVERSIONS["Mercury"].bhavas == ()

    def test_jupiter_holds_four_bhavas(self) -> None:
        """HTJAH-II:16550/16553/16562/16563 — Jupiter: karaka of 2nd, 5th, 10th, 11th."""
        assert KARAKA_IN_12_INVERSIONS["Jupiter"].bhavas == (2, 5, 10, 11)

    def test_rejects_nodes_and_garbage(self) -> None:
        """The dictum covers the 7 visible planets only; nodes/garbage -> ValueError."""
        with pytest.raises(ValueError):
            karaka_in_12_inversion("Rahu")
        with pytest.raises(ValueError):
            karaka_in_12_inversion("Neptune")


# ---------------------------------------------------------------------------
# 5. Bandhana confinement modes (H12, HTJAH-II:16429-16436)
# ---------------------------------------------------------------------------

class TestConfinementModes:
    """Mode of captivity keyed to the rising sign (Bandhana Yoga grid)."""

    def test_aries_group_bound_by_ropes(self) -> None:
        """HTJAH-II:16431-16432 — Aries/Taurus/Sagittarius rising: bound by ropes."""
        for sign in ("Aries", "Taurus", "Sagittarius"):
            mode = confinement_mode(sign)
            assert mode is not None and "ropes" in mode

    def test_scorpio_underground_cell(self) -> None:
        """HTJAH-II:16433-16434 — Scorpio rising: thrown into an underground cell."""
        mode = confinement_mode("Scorpio")
        assert mode is not None and "underground cell" in mode

    def test_gemini_group_put_in_fetters(self) -> None:
        """HTJAH-II:16434-16435 — Gemini/Libra/Virgo rising: put in fetters."""
        for sign in ("Gemini", "Libra", "Virgo"):
            mode = confinement_mode(sign)
            assert mode is not None and "fetters" in mode

    def test_pisces_group_protected_building(self) -> None:
        """HTJAH-II:16435-16436 — Pisces/Cancer/Capricorn: large protected building."""
        for sign in ("Pisces", "Cancer", "Capricorn"):
            mode = confinement_mode(sign)
            assert mode is not None and "protected building" in mode

    def test_leo_and_aquarius_silent_in_source(self) -> None:
        """The printed text names only 10 signs; Leo/Aquarius -> None (faithful gap)."""
        assert confinement_mode("Leo") is None
        assert confinement_mode("Aquarius") is None

    def test_rejects_garbage_sign(self) -> None:
        """Garbage input fails fast with ValueError (boundary validation)."""
        with pytest.raises(ValueError):
            confinement_mode("Ophiuchus")


# ---------------------------------------------------------------------------
# 6. Disease map (H6, HTJAH-I:6439-6477)
# ---------------------------------------------------------------------------

class TestDiseaseMap:
    """Planet -> organ, planet -> tridosha, planet -> season-of-appearance."""

    def test_sun_rules_stomach(self) -> None:
        """HTJAH-I:6439 — 'The Sun - stomach'."""
        assert organ_of("Sun") == "stomach"

    def test_rahu_rules_feet(self) -> None:
        """HTJAH-I:6441 — 'and Rahu—the feet'."""
        assert organ_of("Rahu") == "feet"

    def test_venus_absent_from_organ_list(self) -> None:
        """HTJAH-I:6439-6441 omits Venus from the organ allocation — None is faithful."""
        assert organ_of("Venus") is None

    def test_mars_is_pure_pitta(self) -> None:
        """HTJAH-I:6450 — 'Mars—Pitta (bile)'."""
        assert tridosha_of("Mars") == "pitta (bile)"

    def test_jupiter_is_mostly_kapha(self) -> None:
        """HTJAH-I:6454 — Jupiter: more kapha (phlegm), a little vatha (wind)."""
        dosha = tridosha_of("Jupiter")
        assert dosha is not None and "kapha" in dosha

    def test_nodes_absent_from_tridosha_list(self) -> None:
        """HTJAH-I:6446-6458 covers the 7 visible planets only — nodes -> None."""
        assert tridosha_of("Rahu") is None
        assert tridosha_of("Ketu") is None

    def test_venus_season_is_vasantha_spring(self) -> None:
        """HTJAH-I:6467 — Venus: Vasantha (spring)."""
        season = season_of("Venus")
        assert season is not None and "Vasantha" in season and "spring" in season

    def test_sun_and_mars_share_grishma_summer(self) -> None:
        """HTJAH-I:6469 — Sun and Mars: Grishma (summer)."""
        for planet in ("Sun", "Mars"):
            season = season_of(planet)
            assert season is not None and "Grishma" in season

    def test_table_sizes(self) -> None:
        """7 organ rows (6 planets + Rahu, no Venus), 7 tridosha rows, 7 season rows."""
        assert len(PLANET_ORGANS) == 7
        assert "Venus" not in PLANET_ORGANS
        assert len(PLANET_TRIDOSHAS) == 7
        assert len(PLANET_SEASONS) == 7

    def test_rejects_garbage_planet(self) -> None:
        """Garbage input fails fast with ValueError (boundary validation)."""
        with pytest.raises(ValueError):
            organ_of("Uranus")
        with pytest.raises(ValueError):
            tridosha_of("Lilith")
        with pytest.raises(ValueError):
            season_of("Chiron")
