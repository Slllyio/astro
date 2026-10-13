"""Gauquelin 36-sector geometry: the sector boundaries fall where rising, culmination and setting are."""
from __future__ import annotations

from tools.validation.gauquelin_sectors import KEY, sector


class TestSector:
    def test_equator_equinox_quadrants(self):
        """At lat 0, dec 0 the semi-diurnal arc is 90 deg: rise at H=-90, culminate 0, set +90, IC 180."""
        assert sector(-89.9, 0, 0) == 1        # just risen
        assert sector(-0.1, 0, 0) == 9         # just before upper culmination
        assert sector(0.1, 0, 0) == 10         # just past upper culmination
        assert sector(90.1, 0, 0) == 19        # just set
        assert sector(-90.1, 0, 0) == 36       # just before rising

    def test_each_sector_is_ten_degrees_at_equator(self):
        """With a 90-deg semi-arc, sectors are 10 deg wide: H=-75 is sector 2."""
        assert sector(-75, 0, 0) == 2

    def test_key_sectors_are_gauquelin_plus_zones(self):
        """The plus zones straddle rising (36,1,2,3) and upper culmination (9,10,11,12)."""
        assert KEY == {36, 1, 2, 3, 9, 10, 11, 12}
