"""Life-event taxonomy tests — every citation resolves on disk, every signification key is
doctrine-valid, and LifeEvent validation fails loudly (no silent guessing).
"""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.doctrine.significations import significations_of
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.primitives.vimshottari import date_to_jd
from app.raman_saab.life_events import EVENT_TAXONOMY, LifeEvent


class TestTaxonomyDoctrine:
    @needs_corpus
    def test_every_citation_resolves_on_disk(self) -> None:
        """Each EventSpec.source points at a real line of a citable Raman book (the
        divergence firewall in doctrine/sources.py)."""
        for spec in EVENT_TAXONOMY.values():
            assert verify(spec.source), (
                f"{spec.key}: citation {spec.source.work}:{spec.source.line} "
                f"does not resolve on disk")

    def test_every_signification_key_is_doctrine_valid(self) -> None:
        """Each signification_key exists among its house's Signification records."""
        for spec in EVENT_TAXONOMY.values():
            keys = {s.key for s in significations_of(spec.house)}
            assert spec.signification_key in keys, (spec.key, spec.signification_key)

    def test_relative_death_events_carry_the_maraka_overlay(self) -> None:
        """Death-of-relative events must consult the maraka apparatus (HTJAH-I:770-795)."""
        for key in ("mother_death", "father_death", "spouse_death", "sibling_death"):
            assert EVENT_TAXONOMY[key].maraka_overlay
        assert not EVENT_TAXONOMY["marriage"].maraka_overlay

    def test_marriage_karakas_are_venus_and_moon(self) -> None:
        """AFB-9:98 names Venus and the Moon as the marriage dasa karakas."""
        assert EVENT_TAXONOMY["marriage"].karakas == ("Venus", "Moon")
        assert EVENT_TAXONOMY["marriage"].house == 7


class TestLifeEvent:
    def test_precision_ladder_year_month_day(self) -> None:
        """Precision is inferred from which date parts the user actually supplied."""
        assert LifeEvent("marriage", 2001).precision == "year"
        assert LifeEvent("marriage", 2001, 6).precision == "month"
        assert LifeEvent("marriage", 2001, 6, 15).precision == "day"

    def test_jd_bounds_cover_the_stated_interval(self) -> None:
        """Bounds span exactly the stated year / month / day interval."""
        lo, hi = LifeEvent("marriage", 2001).jd_bounds()
        assert lo == date_to_jd(2001, 1, 1, 0.0) and hi == date_to_jd(2002, 1, 1, 0.0)
        lo, hi = LifeEvent("marriage", 2001, 6).jd_bounds()
        assert lo == date_to_jd(2001, 6, 1, 0.0) and hi == date_to_jd(2001, 7, 1, 0.0)
        lo, hi = LifeEvent("marriage", 2001, 6, 15).jd_bounds()
        assert hi - lo == pytest.approx(1.0)
        assert lo <= LifeEvent("marriage", 2001, 6, 15).jd_point() < hi

    def test_unknown_event_type_fails_with_hint(self) -> None:
        """An untypeable event is a hard error listing valid types (v1: no free text)."""
        with pytest.raises(ValueError, match="mariage|valid"):
            LifeEvent("mariage", 2001)

    def test_day_without_month_rejected(self) -> None:
        """A day-precision date needs its month — anything else is a data-entry bug."""
        with pytest.raises(ValueError):
            LifeEvent("marriage", 2001, None, 15)
