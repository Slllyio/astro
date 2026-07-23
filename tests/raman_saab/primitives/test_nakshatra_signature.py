"""Nakshatra soul-signature table — `primitives/nakshatra_signature.py`.

Pins the 27-row classical table (index/name/deity/gana) and the longitude lookup. Pure data — no
chart cast. The archetype/keyword columns are editorial and not asserted verbatim, only present.
"""
from __future__ import annotations

import pytest

from app.raman_saab.primitives.nakshatra_signature import (
    signature_for, signature_for_lon)

_GANAS = {"deva", "manushya", "rakshasa"}


class TestNakshatraSignature:
    def test_table_is_27_rows_indexed_1_to_27_distinct_names(self) -> None:
        """All 27 nakshatras present, index == position, names distinct, gana well-formed."""
        sigs = [signature_for(n) for n in range(1, 28)]
        assert [s.index for s in sigs] == list(range(1, 28))
        assert len({s.name for s in sigs}) == 27
        assert all(s.gana in _GANAS for s in sigs)
        assert all(s.soul_archetype and s.soul_keyword for s in sigs)

    def test_known_rows(self) -> None:
        """Spot-check three anchors: Ashwini (deva, Ashwini Kumaras), Ashlesha (rakshasa, Nagas),
        Revati (deva, Pushan)."""
        assert signature_for(1).name == "Ashwini" and signature_for(1).gana == "deva"
        assert "Ashwini Kumaras" in signature_for(1).devata
        assert signature_for(9).name == "Ashlesha" and signature_for(9).gana == "rakshasa"
        assert signature_for(27).name == "Revati" and signature_for(27).devata == "Pushan"

    def test_lookup_by_longitude(self) -> None:
        """Ashwini spans 0-13°20'; a longitude of 5° falls in Ashwini (index 1)."""
        assert signature_for_lon(5.0).index == 1
        # Just past the Ashwini/Bharani cusp (13°20') falls in Bharani (index 2).
        assert signature_for_lon(14.0).index == 2

    def test_out_of_range_raises(self) -> None:
        """Index outside 1..27 is a hard error (no silent clamp)."""
        with pytest.raises(ValueError):
            signature_for(0)
        with pytest.raises(ValueError):
            signature_for(28)
