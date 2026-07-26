"""Pitṛ-doṣa / ancestral-karma reading — `judges/pitru_dosha_reading.py`.

Pins the classical curse-yoga detection on Track-B synthetic charts + a public-baseline structure
check. Every curse is tagged CLASSICAL_NONCITABLE; Raman's own children verdict is the one
authoritative line. Each test states the classical fact it checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import pitru_dosha_reading as pd

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    """Track-B chart; asc_lon 5.0 -> Aries ascendant, so the 5th is Leo (sign 5)."""
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


class TestSerpentCurse:
    def test_rahu_in_5th_without_benefic_aspect_fires(self) -> None:
        """Rahu in the 5th (Leo) with no benefic aspect → the serpent-curse (sarpa-śrāpa)."""
        c = _chart({"Rahu": 125.0})     # Leo = the 5th from Aries
        yogas = pd._serpent_curse(c, 5, "Sun")
        assert yogas and "serpent-curse" in yogas[0].text
        assert yogas[0].provenance == "CLASSICAL_NONCITABLE"

    def test_benefic_aspect_on_5th_suppresses_serpent_curse(self) -> None:
        """A benefic (Jupiter in the 1st, aspecting the 5th) cancels the serpent-curse."""
        c = _chart({"Rahu": 125.0, "Jupiter": 5.0})   # Jupiter in Aries aspects the 5th
        assert pd._serpent_curse(c, 5, "Sun") == ()

    def test_no_rahu_contact_no_serpent_curse(self) -> None:
        """Rahu away from the 5th and its lord → no serpent-curse."""
        c = _chart({"Rahu": 5.0})       # Aries, the 1st
        assert pd._serpent_curse(c, 5, "Sun") == ()


class TestAncestralCurse:
    def test_pitru_curse_needs_9th_affliction_and_struck_sun(self) -> None:
        """Father's-curse: the 9th afflicted by a malefic AND the Sun (pitṛ-kāraka) debilitated."""
        # asc Aries -> 9th = Sagittarius(9). Saturn in Sagittarius afflicts the 9th; Sun in
        # Libra(7) is debilitated.
        c = _chart({"Saturn": 250.0, "Sun": 190.0})
        yogas = pd._ancestral_curse(c, 9, "Sun", "father's curse (pitṛ-śrāpa)", "BPHS-83:30")
        assert yogas and "pitṛ-śrāpa" in yogas[0].text


class TestBuildAndInvariant:
    def test_build_on_public_baseline(self) -> None:
        """The full reading builds on the canonical baseline: Raman's verdict + classical notes."""
        r = pd.build_pitru_dosha_reading(cast_chart(_BASELINE, ayanamsa="raman"))
        assert r.raman_children_verdict in {"favourable", "mixed", "afflicted",
                                            "insufficient-evidence"}
        assert any(n.provenance == "RAMAN_EXPLICIT" for n in r.notes)     # Raman decides
        assert any(n.provenance == "CLASSICAL_NONCITABLE" for n in r.notes)  # curses are classical
        assert r.pitru_bhava  # the 9th (pitṛ-sthāna) is always described

    def test_house_template_never_imports_the_pitru_surface(self) -> None:
        """The D1 verdict path imports nothing from this surface — ratchet untouched."""
        import app.raman_saab.judges.house_template as ht
        assert "pitru_dosha" not in Path(ht.__file__).read_text(encoding="utf-8")

    def test_notes_layer_ancestral_curse_apart_from_the_houses_own_significations(self) -> None:
        """Regression test for a real tension found in a close reading of a generated report:
        'father's curse'/'mother's curse' ancestral language reads alongside a favourable House 9
        (father/fortune) or House 4 (mother/home) verdict elsewhere in the report with no note
        on how they relate. A note must name both House-by-house reading and Your Reading as the
        sections carrying the native's own significations, must acknowledge the curse-yoga test
        and the house verdict share the SAME house/karaka data (not claim false independence — a
        bphs-doctrine-reviewer pass found the first draft's 'independent classical layers' wording
        overstated this), and must state that a favourable house reading and a curse-yoga firing
        can still coexist because the house verdict weighs more factors, not because the two
        layers are unrelated."""
        r = pd.build_pitru_dosha_reading(cast_chart(_BASELINE, ayanamsa="raman"))
        note = next((n for n in r.notes if "SAME GROUND" in n.text), None)
        assert note is not None, [n.text for n in r.notes]
        assert "House-by-house reading" in note.text and "Your Reading" in note.text
        assert "coexist" in note.text
        assert "SAME house and" in note.text          # shares data, not "independent"
        assert "independent" not in note.text.lower()  # the overstated framing the reviewer flagged
