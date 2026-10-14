"""Affliction gathering — the own-lord exemption, conditional malefics, and the shared dignity read.

Pins the Phase-1 doctrine fixes: BPHS-11:208 (the lord's aspect is an antidote, never an
affliction), BPHS-3:187 (the waning Moon and malefic-joined Mercury ARE malefics), and the single
shared ch.3 dignity helper.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.parashara.judges import richer_bhava
from app.parashara.primitives.relationships import dignity_in_sign
from app.parashara.synthesis.chart_facts import functioning_malefics
from app.parashara.synthesis.evidence import Polarity
from app.parashara.synthesis.evidence_engine import gather_affliction


def _reading(asc_sign: int, signs: dict[str, int], *, moon_waxing: bool = True,
             yogakarakas: tuple[str, ...] = ()) -> SimpleNamespace:
    """A minimal duck-typed reading: gather_affliction reads .chart + .yogakarakas."""
    chart = SimpleNamespace(asc_sign=asc_sign, moon_waxing=moon_waxing,
                            longitudes={p: (s - 1) * 30 + 5.0 for p, s in signs.items()})
    return SimpleNamespace(chart=chart, yogakarakas=yogakarakas)


class TestOwnLordExemption:
    def test_own_lord_occupant_casts_no_affliction(self):
        """Mars occupying its own Aries lagna is ch.11 prosperity, never a malefic-occupant vote."""
        ev = gather_affliction(_reading(1, {"Mars": 1}), 1)
        assert not any(e.condition == "malefic_occupant" for e in ev)

    def test_own_lord_aspect_disclosed_neutral(self):
        """Mars aspecting its own Scorpio (8th from Aries) is the antidote: one NEUTRAL disclosure,
        no CONTRADICTS vote (BPHS-11:208)."""
        ev = gather_affliction(_reading(1, {"Mars": 1}), 8)
        own = [e for e in ev if e.condition == "own_lord_aspect"]
        assert len(own) == 1 and own[0].polarity is Polarity.NEUTRAL
        assert own[0].source.work == "BPHS-11" and own[0].source.line == 208
        assert not any(e.condition == "malefic_aspect" and "Mars" in e.observed for e in ev)

    def test_foreign_malefic_aspect_still_votes(self):
        """Saturn aspecting a house it does not lord still votes CONTRADICTS."""
        # Aries lagna; Saturn in sign 5 casts its 3rd-aspect on sign 7 (house 7, lord Venus).
        ev = gather_affliction(_reading(1, {"Saturn": 5}), 7)
        hits = [e for e in ev if e.condition == "malefic_aspect" and "Saturn" in e.observed]
        assert len(hits) == 1 and hits[0].polarity is Polarity.CONTRADICTS


class TestConditionalMalefics:
    def test_waning_moon_is_malefic(self):
        """A waning Moon with no benefic company or aspect joins the affliction set (BPHS-3:187)."""
        r = _reading(1, {"Moon": 2}, moon_waxing=False)
        assert "Moon" in functioning_malefics(r.chart)

    def test_waxing_moon_is_not(self):
        """A waxing Moon stays benefic."""
        r = _reading(1, {"Moon": 2}, moon_waxing=True)
        assert "Moon" not in functioning_malefics(r.chart)

    def test_waning_moon_rescued_by_benefic_aspect(self):
        """A benefic's aspect turns even a waning Moon benefic (BPHS-3:208)."""
        # Jupiter in sign 8 casts its 7th-aspect on sign 2, where the waning Moon sits.
        r = _reading(1, {"Moon": 2, "Jupiter": 8}, moon_waxing=False)
        assert "Moon" not in functioning_malefics(r.chart)

    def test_mercury_joined_by_malefic_turns_malefic(self):
        """Mercury conjunct Saturn is a malefic (BPHS-3:187) and votes as an occupant."""
        r = _reading(1, {"Mercury": 4, "Saturn": 4}, moon_waxing=True)
        assert "Mercury" in functioning_malefics(r.chart)
        ev = gather_affliction(r, 4)
        assert any(e.condition == "malefic_occupant" and "Mercury" in e.observed
                   and e.polarity is Polarity.CONTRADICTS for e in ev)

    def test_mercury_alone_stays_benefic(self):
        """Unafflicted Mercury casts no affliction."""
        r = _reading(1, {"Mercury": 4}, moon_waxing=True)
        assert "Mercury" not in functioning_malefics(r.chart)

    def test_upachaya_occupant_still_neutralized(self):
        """A foreign malefic in an upachaya (3rd) is disclosed NEUTRAL, not counted."""
        # Mars in Gemini = the 3rd from Aries; Mercury lords it, so Mars is not exempt as lord.
        ev = gather_affliction(_reading(1, {"Mars": 3}), 3)
        occ = [e for e in ev if e.condition == "malefic_occupant"]
        assert occ and all(e.polarity is Polarity.NEUTRAL for e in occ)

    def test_yogakaraka_exempt_from_affliction(self):
        """A yogakaraka Saturn (Libra lagna) is disclosed NEUTRAL, never a CONTRADICTS vote
        (BPHS-34:90) — occupancy and aspect alike."""
        # Libra lagna (asc=7); Saturn in Cancer (sign 4) = the 10th house, aspecting e.g. the 4th
        # (3rd-aspect on sign 6 = house 12? compute: Saturn in 4 aspects 6, 10, 13->1). Use the
        # aspected house sign 10 -> house 4 (Capricorn from Libra).
        r = _reading(7, {"Saturn": 4}, yogakarakas=("Saturn",))
        for house in (10, 4):                      # occupied 10th; aspected 4th (sign 1... )
            ev = gather_affliction(r, house)
            assert not any("Saturn" in e.observed and e.polarity is Polarity.CONTRADICTS
                           for e in ev)
            if any(e.condition == "yogakaraka_exempt" for e in ev):
                break
        else:
            raise AssertionError("expected at least one yogakaraka_exempt disclosure")


class TestSharedDignity:
    def test_one_dignity_answer(self):
        """richer_bhava and the synthesis share the ONE ch.3 dignity helper (they used to diverge)."""
        assert richer_bhava._dignity is dignity_in_sign

    def test_dignity_values(self):
        """Exaltation/own +1; debilitation/enemy -1; neutral 0; nodes 0."""
        assert dignity_in_sign("Sun", 1) == 1          # exalted in Aries
        assert dignity_in_sign("Sun", 5) == 1          # own Leo
        assert dignity_in_sign("Sun", 7) == -1         # debilitated in Libra
        assert dignity_in_sign("Sun", 11) == -1        # Aquarius, an enemy's (Saturn's) sign
        assert dignity_in_sign("Jupiter", 1) == 0      # friend's sign, no dignity either way
        assert dignity_in_sign("Rahu", 1) == 0         # nodes carry no ch.3 dignity
