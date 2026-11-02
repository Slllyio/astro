"""Krishnamurti's natal indication rules (Readers 3 and 4) and Reader 4's descriptive tables."""

from __future__ import annotations

import pytest

from app.kp.chart import Birth, cast, sign_index
from app.kp.citations import CITATIONS
from app.kp.descriptions import SIGNS, describe_partner, love_and_life, love_table, partner_table
from app.kp.indications import INDICATIONS, KINDS, indications
from app.kp.significators import houses_signified

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
ALIBAG = Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18 + 39 / 60, lon=72 + 55 / 60)


class TestRegistry:
    def test_every_rule_cited_in_reader3_or_4(self) -> None:
        """Each indication quotes Reader 3 (by line) or Reader 4 (by page)."""
        assert len(INDICATIONS) == 59
        for i in INDICATIONS.values():
            assert CITATIONS[i.citation].source in ("KPR3", "KPR4"), i.key
            assert i.kind in KINDS and 1 <= i.cusp <= 12

    def test_no_death_rules(self) -> None:
        """Death, lifespan and partner-death rules are left out (ruling R22)."""
        for i in INDICATIONS.values():
            text = (i.indicates + " " + CITATIONS[i.citation].quote).lower()
            assert not any(w in text for w in ("passes away", "death", "short-lived", "unnatural"))

    def test_ascendant_one_and_ten(self) -> None:
        """KPR3: the ascendant CSL signifying 1 and 10 gives honour; both houses are needed."""
        i = INDICATIONS["asc_1_10"]
        assert i.cusp == 1 and i.kind == "signifies" and i.arg == (frozenset({1}), frozenset({10}))


@pytest.mark.parametrize("birth", [BANGALORE, ALIBAG])
class TestFiring:
    def test_fired_rules_hold(self, birth: Birth) -> None:
        """Every fired indication's condition is true of the chart, and every unfired one false."""
        c = cast(birth)
        fired = {f.indication.key: f for f in indications(c)}
        for i in INDICATIONS.values():
            csl = c.cusp(i.cusp).sub_lord
            star = c.planets[csl].star_lord
            if i.kind == "signifies":
                ok = all(houses_signified(c, csl) & g for g in i.arg)
            elif i.kind == "star_signifies":
                ok = all(houses_signified(c, star) & g for g in i.arg)
            elif i.kind == "is":
                ok = csl in i.arg
            elif i.kind == "star_in_sign":
                ok = sign_index(c.planets[star].longitude) in i.arg
            else:
                continue
            assert (i.key in fired) == ok, i.key
        for f in fired.values():
            assert "not a validated prediction" in f.to_dict()["framing"]

    def test_one_ascendant_star_sign_fires(self, birth: Birth) -> None:
        """Exactly one of the twelve 'ascendant CSL in the star of a planet in <sign>' rules fires."""
        keys = [f.indication.key for f in indications(cast(birth)) if f.indication.key.startswith("asc_star_in_")]
        assert len(keys) == 1


@pytest.mark.skipif(partner_table() is None, reason="KP Reader 4 text not present (data/ is gitignored)")
class TestDescriptions:
    def test_partner_table_is_complete(self) -> None:
        """Seven planets by twelve signs: all 84 entries parse and are non-empty (KPR4 pp.86-97)."""
        t = partner_table()
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            for s in range(12):
                assert len(t[(p, s)]) > 40, (p, SIGNS[s])

    def test_printed_entries(self) -> None:
        """Spot checks against the print: Sun in Aries, Saturn in Capricorn."""
        t = partner_table()
        assert t[("Sun", 0)].startswith("Middle statue, strong and well-made")
        assert t[("Saturn", 9)].startswith("Lean, bony, black hair")

    def test_love_table_is_complete(self) -> None:
        """Twelve signs, a Male and a Female paragraph each (KPR4 pp.156-170)."""
        t = love_table()
        assert all(len(t[(s, x)]) > 200 for s in range(12) for x in ("male", "female"))

    def test_chart_reads(self) -> None:
        """The 7th CSL and its star lord each get the entry for the sign they occupy."""
        c = cast(BANGALORE)
        ds = describe_partner(c)
        assert ds and all(d.text for d in ds)
        assert love_and_life(c, "female")
