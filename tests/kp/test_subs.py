"""KP sub table pinned to Krishnamurti's own printed values (KP Reader 3)."""

from __future__ import annotations

from fractions import Fraction

from app.kp.subs import DASA_ORDER, divisions, dms, horary_number_longitude, lords_of, subs


class TestSubTable:
    def test_243_subs_become_249_divisions(self) -> None:
        """27 stars x 9 subs = 243; six cross a sign edge and are split, giving KP's 249."""
        assert len(subs()) == 243
        assert len(divisions()) == 249

    def test_divisions_tile_the_zodiac(self) -> None:
        """Divisions are contiguous from 0 to 360 with no gap or overlap."""
        d = divisions()
        assert d[0].start == 0 and d[-1].end == 360
        assert all(a.end == b.start for a, b in zip(d, d[1:]))

    def test_sub_widths_follow_vimshottari(self) -> None:
        """Each sub is 13°20' x years/120: Ketu sub 0°46'40", Venus sub 2°13'20" (KPR3-SUB)."""
        a, b, star, sub = subs()[0]
        assert (star, sub, b - a) == ("Ketu", "Ketu", Fraction(40, 3) * 7 / 120)
        a, b, _, sub = subs()[1]
        assert (sub, b - a) == ("Venus", Fraction(40, 3) * 20 / 120)

    def test_each_star_starts_with_its_own_sub(self) -> None:
        """The first sub of every star belongs to the star lord."""
        for i in range(27):
            _, _, star, sub = subs()[i * 9]
            assert star == sub == DASA_ORDER[i % 9]


class TestHoraryNumbers:
    def test_number_206_is_capricorn_26_06_40(self) -> None:
        """KPR3:19551-19553: 'the commencement of 206th sub ... Capricorn 26° 6' 40"'."""
        assert dms(horary_number_longitude(206)) == "Capricorn 26°06'40\""

    def test_number_37_is_taurus_22_40(self) -> None:
        """KPR3:19779-19780: 'Number 37 implies that the horary ascendant is Taurus 22° 40''."""
        assert dms(horary_number_longitude(37)) == "Taurus 22°40'00\""


class TestLords:
    def test_rohini_saturn_sub_example(self) -> None:
        """KPR3 Role of Sub: Taurus, Rohini (Moon star), Saturn sub lies inside 10°-23°20' Taurus."""
        hits = [d for d in divisions() if d.sign_lord == "Venus" and d.star_lord == "Moon" and d.sub_lord == "Saturn"
                and 30 <= d.start < 60]
        assert len(hits) == 1
        mid = float((hits[0].start + hits[0].end) / 2)
        lo = lords_of(mid)
        assert (lo.sign, lo.star, lo.sub_lord) == ("Taurus", "Rohini", "Saturn")

    def test_boundary_belongs_to_following_division(self) -> None:
        """A point exactly on 13°20' Aries is Bharani (Venus), not Aswini."""
        assert lords_of(40 / 3).star_lord == "Venus"
