"""Activation v2 — BPHS-native window grading, targeting, and the honesty flags.

Pins the ch.52-60 antardasha rule (AD lord's position FROM the MD lord + its dignity), the ch.47
MD-lord quality, node-safe targeting, and the maraka/beyond-span annotations.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.reading import read
from app.parashara.synthesis.activation import (
    AD_ADVERSE_SOURCE, AD_DIGNITY_SOURCE, AD_QUALITY_SOURCE, MD_QUALITY_SOURCE,
    QUALITY_RANK, TARGETING_SOURCE, active_windows, influences, md_quality, window_quality)

from types import SimpleNamespace


def _chart(asc_sign: int, signs: dict[str, int]) -> SimpleNamespace:
    """A minimal duck-typed chart: the grading functions read only asc_sign + longitudes."""
    return SimpleNamespace(asc_sign=asc_sign,
                           longitudes={p: (s - 1) * 30 + 5.0 for p, s in signs.items()})


class TestWindowQuality:
    def test_trikona_from_md_lord_is_auspicious(self):
        """AD lord in the 5th from the MD lord -> auspicious (BPHS-53:364)."""
        ch = _chart(1, {"Jupiter": 1, "Venus": 5})
        quality, ad_from_md, _ = window_quality(ch, "Jupiter", "Venus")
        assert ad_from_md == 5 and quality == "auspicious"

    def test_dusthana_from_md_lord_is_adverse(self):
        """AD lord in the 8th from the MD lord -> adverse (BPHS-53:375)."""
        ch = _chart(1, {"Jupiter": 1, "Mercury": 8})
        quality, ad_from_md, _ = window_quality(ch, "Jupiter", "Mercury")
        assert ad_from_md == 8 and quality == "adverse"

    def test_debilitation_drags_a_neutral_position_adverse(self):
        """AD lord in the 3rd (no position vote) but debilitated -> adverse (BPHS-53:375)."""
        # Sun debilitated in Libra (7); MD lord Venus in Taurus (2): 3rd-from is (7-2)%12+1 = 6...
        # pick Mars in Capricorn? Mars EXALTS there. Use Jupiter debilitated in Capricorn (10),
        # MD lord Saturn in Scorpio (8): ad_from_md = (10-8)%12+1 = 3 -> position 0, dignity -1.
        # Sagittarius lagna keeps Jupiter (Capricorn) in the 2nd from the Ascendant — no lagna vote.
        ch = _chart(9, {"Saturn": 8, "Jupiter": 10})
        quality, ad_from_md, dig = window_quality(ch, "Saturn", "Jupiter")
        assert ad_from_md == 3 and dig == -1 and quality == "adverse"

    def test_opposed_votes_disclose_mixed(self):
        """Adverse position but exalted AD lord -> 'mixed', not silently averaged away."""
        # MD lord Sun in Virgo (6); Saturn exalted in Libra (7): ad_from_md = (7-6)%12+1 = 2...
        # need 6/8/12-from. Sun in Pisces (12), Saturn in Libra (7): (7-12)%12+1 = 8 -> pos -1,
        # dignity +1 (exalted) -> mixed.
        # Virgo lagna keeps Saturn (Libra) in the 2nd from the Ascendant — no lagna vote.
        ch = _chart(6, {"Sun": 12, "Saturn": 7})
        quality, ad_from_md, dig = window_quality(ch, "Sun", "Saturn")
        assert ad_from_md == 8 and dig == 1 and quality == "mixed"

    def test_ascendant_frame_votes(self):
        """AD lord in a trikona FROM THE ASCENDANT lifts an otherwise silent window auspicious
        (BPHS-57:237): Aquarius lagna, Mercury in Gemini = the 5th; 3rd from the MD lord Jupiter."""
        ch = _chart(11, {"Jupiter": 1, "Mercury": 3})
        quality, ad_from_md, _ = window_quality(ch, "Jupiter", "Mercury")
        assert ad_from_md == 3 and quality == "auspicious"

    def test_venus_in_saturn_with_venus_in_lagna_is_not_adverse(self):
        """The verse's own case: Venus in the lagna (kendra) during Saturn's dasa is promised
        'marriage, birth of a son' (BPHS-57:228) — even 12th from Saturn it must not read adverse."""
        ch = _chart(8, {"Saturn": 9, "Venus": 8})
        quality, ad_from_md, _ = window_quality(ch, "Saturn", "Venus")
        assert ad_from_md == 12 and quality == "mixed"

    def test_own_dasha_bhukti_rides_on_dignity(self):
        """The MD lord's own AD counts position 1 (kendra); own-sign dignity lifts it auspicious."""
        ch = _chart(1, {"Mars": 1})                              # Mars in own Aries
        quality, ad_from_md, dig = window_quality(ch, "Mars", "Mars")
        assert ad_from_md == 1 and dig == 1 and quality == "auspicious"

    def test_sources_resolve(self):
        """Every activation citation points at a real corpus line."""
        for src in (TARGETING_SOURCE, MD_QUALITY_SOURCE, AD_QUALITY_SOURCE,
                    AD_ADVERSE_SOURCE, AD_DIGNITY_SOURCE):
            assert verify(src), src


class TestMdQuality:
    def test_lagna_placement_is_favourable(self):
        """MD lord in the Ascendant -> favourable (BPHS-47:76)."""
        assert md_quality(_chart(2, {"Venus": 2}), "Venus") == "favourable"

    def test_dusthana_placement_is_unfavourable(self):
        """MD lord in the 8th house -> unfavourable (BPHS-47:76)."""
        # Aries lagna; Venus in Scorpio (sign 8) = the 8th house.
        assert md_quality(_chart(1, {"Venus": 8}), "Venus") == "unfavourable"

    def test_friends_sign_is_favourable(self):
        """MD lord in a friend's sign -> favourable (Moon in Leo, the Sun a natural friend);
        Cancer lagna keeps Leo out of the dusthana houses so the dignity clause decides."""
        assert md_quality(_chart(4, {"Moon": 5}), "Moon") == "favourable"

    def test_node_grades_by_house_alone(self):
        """A node has no ch.3 dignity: only a dusthana placement grades it."""
        assert md_quality(_chart(1, {"Rahu": 12}), "Rahu") == "unfavourable"
        assert md_quality(_chart(1, {"Rahu": 5}), "Rahu") == "neutral"


class TestInfluences:
    def test_owner_influences_its_house(self):
        """A graha lording a house targets it (Aries lagna: Mars lords the 1st)."""
        assert influences(_chart(1, {"Mars": 8}), "Mars", 1)

    def test_occupant_influences_its_house(self):
        """A graha occupying a house targets it."""
        assert influences(_chart(1, {"Jupiter": 5}), "Jupiter", 5)

    def test_seventh_aspect_influences(self):
        """Every graha aspects the 7th from itself, so it targets that house."""
        assert influences(_chart(1, {"Venus": 1}), "Venus", 7)

    def test_node_casts_no_aspect_influence(self):
        """A node casts no drishti: Rahu in the 1st does not aspect-target the 7th."""
        assert not influences(_chart(1, {"Rahu": 1}), "Rahu", 7)


class TestActiveWindows:
    @pytest.fixture(scope="class")
    def reading(self):
        return read(cast(year=1990, month=7, day=15, hour=12, minute=0,
                         tz_offset=5.5, latitude=12.97, longitude=77.59))

    def test_windows_sorted_best_quality_then_age(self, reading):
        """Windows come best-quality-first, chronological within a quality."""
        ws = active_windows(reading, (7,))
        assert ws, "the 7th should have activation windows"
        ranks = [QUALITY_RANK[w.quality] for w in ws]
        assert ranks == sorted(ranks)
        for a, b in zip(ws, ws[1:]):
            if a.quality == b.quality:
                assert a.start_age <= b.start_age

    def test_no_pre_birth_windows(self, reading):
        """Ages are clipped at birth."""
        assert all(w.start_age >= 0 for w in active_windows(reading, (1,)))

    def test_maraka_windows_flagged(self, reading):
        """Every window whose MD or AD lord is a maraka carries the flag (BPHS-44:51)."""
        maraka_names = {m.planet for m in reading.maraka_planets}
        for w in active_windows(reading, (8,)):
            assert w.maraka == (w.maha_lord in maraka_names or w.antar_lord in maraka_names)

    def test_beyond_span_annotated_not_clipped(self, reading):
        """Windows past the Nisargayu span are kept, annotated (surfaces only ADD)."""
        span = reading.nisargayu_full.total_years
        ws = active_windows(reading, (1,))
        late = [w for w in ws if w.start_age > span]
        assert late, "the 120-year cycle should extend past the computed span"
        assert all(w.beyond_span for w in late)
        assert all("beyond the computed Nisargayu span" in w.label for w in late)
