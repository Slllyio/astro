"""D-7 (Sapthamsa) children gate — `house_template._saptamsa_gate`.

The gate lets the child-varga confirm/temper a BORDERLINE children verdict, on the exact
discipline of the D9 navamsa modulation: only a 'mixed' moves, one step, and a decisive
verdict never shifts. It is scoped to the H5 children matter alone and runs before the
decisive Beeja/Kshetra fertility gate. Each test states the doctrinal behaviour it pins.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.significations import Signification, significations_of
from app.raman_saab.judges.house_template import FrameLedger, _saptamsa_gate

_CHILDREN = next(s for s in significations_of(5) if s.key == "children")


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


def _ledger(lord: str = "Sun", karaka: str = "Jupiter") -> FrameLedger:
    """A minimal lead ledger — the gate reads only ``lord`` and ``karaka`` off it."""
    return FrameLedger(
        frame="lagna", lord=lord, lord_strong=None, karaka=karaka, karaka_strong=None,
        bhava_bala=None, bhava_bala_strong=None, navamsa_status="neutral",
        karaka_intact=True, maraka_active=False, parivartana_resilient=False,
        lord_karaka_identical=False, fired_benefic=(), fired_malefic=(), fired_neutral=())


# Charts whose D-7 read for (Sun, Jupiter) is confirms / weakens (pinned in
# test_saptamsa_status.py): Jupiter Aries 15 -> D-7 Cancer (exalt) = confirms;
# Jupiter Capricorn 27 -> D-7 Capricorn (debil) = weakens.
_CONFIRM = {"Sun": 15.0, "Jupiter": 15.0}
_WEAKEN = {"Sun": 15.0, "Jupiter": 297.0}


class TestSaptamsaGate:
    def test_mixed_confirmed_lifts_to_favourable(self) -> None:
        """A borderline children 'mixed' with a confirming D-7 is lifted to favourable."""
        c = _chart(_CONFIRM)
        v, md = _saptamsa_gate(c, _CHILDREN, "mixed", _ledger(), EvalContext(c))
        assert v == "favourable"
        assert ("saptamsa", "confirms") in md

    def test_mixed_weakened_drops_to_afflicted(self) -> None:
        """A borderline children 'mixed' with a weakening D-7 is dropped to afflicted."""
        c = _chart(_WEAKEN)
        v, md = _saptamsa_gate(c, _CHILDREN, "mixed", _ledger(), EvalContext(c))
        assert v == "afflicted"
        assert ("saptamsa", "weakens") in md

    def test_decisive_favourable_never_shifts(self) -> None:
        """A decisive favourable is not overturned by a weakening D-7 — only 'mixed' moves."""
        c = _chart(_WEAKEN)
        v, md = _saptamsa_gate(c, _CHILDREN, "favourable", _ledger(), EvalContext(c))
        assert v == "favourable"
        assert ("saptamsa", "weakens") in md          # still surfaced as report metadata

    def test_decisive_afflicted_never_shifts(self) -> None:
        """A decisive afflicted is not lifted by a confirming D-7."""
        c = _chart(_CONFIRM)
        v, md = _saptamsa_gate(c, _CHILDREN, "afflicted", _ledger(), EvalContext(c))
        assert v == "afflicted"
        assert ("saptamsa", "confirms") in md

    def test_neutral_d7_reports_but_does_not_move(self) -> None:
        """A neutral D-7 leaves even a 'mixed' unchanged, but is still reported."""
        c = _chart({"Sun": 2.0, "Jupiter": 297.0})   # one confirm + one weaken -> neutral
        v, md = _saptamsa_gate(c, _CHILDREN, "mixed", _ledger(), EvalContext(c))
        assert v == "mixed"
        assert ("saptamsa", "neutral") in md

    def test_non_children_matter_untouched(self) -> None:
        """The gate is scoped to H5 children — any other matter passes through unchanged
        with no saptamsa metadata."""
        c = _chart(_CONFIRM)
        mother = Signification(key="mother", house=4, primary_karaka="Moon")
        v, md = _saptamsa_gate(c, mother, "mixed", _ledger(), EvalContext(c))
        assert v == "mixed"
        assert md == ()

    def test_unresolvable_d7_is_a_no_op(self) -> None:
        """When the D-7 cannot be read (pillars absent), the gate neither moves the verdict
        nor emits metadata."""
        c = _chart({"Moon": 100.0})                   # neither Sun (lord) nor Jupiter present
        v, md = _saptamsa_gate(c, _CHILDREN, "mixed", _ledger(), EvalContext(c))
        assert v == "mixed"
        assert md == ()
