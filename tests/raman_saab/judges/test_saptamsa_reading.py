"""Saptamsa (D-7) children reading surface — `judges/saptamsa_reading.py`.

The reading is REPORT-ONLY and provenance-honest: the verdict comes from Raman's real
method (Rasi 5th + Navamsa + Beeja/Kshetra), and the D-7 overlay corroborates with every
element carrying a provenance tag. These tests pin the structure, the tags, the
report-only invariant, and the confirmed field_case_01 facts.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import house_template as ht
from app.raman_saab.judges.saptamsa_reading import (
    build_saptamsa_children_reading)

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "field_case_01.json"


def _field_chart() -> RamanChart:
    b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
    return cast_chart(BirthData(name="field", year=b["year"], month=b["month"], day=b["day"],
                                hour=b["hour"], minute=b["minute"], tz_offset=b["tz_offset"],
                                latitude=b["latitude"], longitude=b["longitude"]),
                      ayanamsa="raman")


class TestStructureAndProvenance:
    def test_three_child_loci_ordered_eldest_first(self) -> None:
        """The overlay lays out three child loci, ordinal 1 (eldest) first."""
        r = build_saptamsa_children_reading(_field_chart())
        loci = r.d7_overlay.child_loci
        assert [l.ordinal for l in loci] == [1, 2, 3]
        assert loci[0].frame == "D7-lagna"

    def test_eldest_is_general_principle_successive_is_noncitable(self) -> None:
        """Doctrine provenance: the eldest (D-7 lagna) is a Raman general-principle read;
        the successive children use the non-citable KP/Rath scheme (Raman is silent)."""
        loci = build_saptamsa_children_reading(_field_chart()).d7_overlay.child_loci
        assert loci[0].scheme == "RAMAN_GENERAL_PRINCIPLE"
        assert all(l.scheme == "CLASSICAL_NONCITABLE" for l in loci[1:])

    def test_notes_flag_that_raman_never_reads_the_d7(self) -> None:
        """The reading is honest up front: a note records that Raman never reads a D-7."""
        r = build_saptamsa_children_reading(_field_chart())
        assert any("never casts or reads a D-7" in n.text for n in r.notes)

    def test_notes_soften_the_classical_affliction_wording(self) -> None:
        """A close reading of a real generated report found real tonal whiplash: the report's
        own plain-English 'Your Reading' section explicitly asks the reader not to feel alarm
        about a children-affliction reading, then the D-7 overlay narrates the SAME affliction
        in stark classical language ('deprives the person of children', 'children die after
        some time') with no gloss. A note must explain these are classical shorthand for
        DEGREES of difficulty, not literal stand-alone predictions, and must point back to the
        report's own calibrated House-5 reading as the thing that actually decides the verdict."""
        r = build_saptamsa_children_reading(_field_chart())
        note = next((n for n in r.notes if "shorthand for" in n.text), None)
        assert note is not None, [n.text for n in r.notes]
        assert "not literal" in note.text
        assert "House-by-house" in note.text or "Population context" in note.text


class TestReportOnlyInvariant:
    def test_verdict_path_never_imports_the_reading(self) -> None:
        """The reading must not feed the verdict: house_template never imports it."""
        src = Path(ht.__file__).read_text(encoding="utf-8")
        offenders = [ln for ln in src.splitlines()
                     if ln.startswith(("import ", "from ")) and "saptamsa_reading" in ln]
        assert not offenders, offenders

    def test_building_the_reading_does_not_change_the_children_verdict(self) -> None:
        """Building the reading is side-effect-free: judge_house(.,5) is identical before/after."""
        chart = _field_chart()
        before = [(sv.signification, sv.verdict) for sv in ht.judge_house(chart, 5).significations]
        build_saptamsa_children_reading(chart)
        after = [(sv.signification, sv.verdict) for sv in ht.judge_house(chart, 5).significations]
        assert before == after

    def test_reading_verdict_matches_judge_house(self) -> None:
        """The Raman-core verdict is exactly judge_house's children verdict (no re-derivation)."""
        chart = _field_chart()
        r = build_saptamsa_children_reading(chart)
        jh = next(sv.verdict for sv in ht.judge_house(chart, 5).significations
                  if sv.signification == "children")
        assert r.raman_core.children_verdict == jh


class TestSparseChart:
    def test_track_b_sparse_does_not_crash(self) -> None:
        """A minimal Track-B chart still produces a reading (None-safe pillars)."""
        sparse = RamanChart.from_stated_positions(
            {"Sun": {"lon": 100.0, "bhava": 5}}, asc_lon=15.0, ayanamsa="raman")
        r = build_saptamsa_children_reading(sparse)
        assert r.d7_overlay.lagna_sign in range(1, 13)


class TestFieldCase01:
    """The confirmed real nativity (Scorpio lagna, two daughters, eldest with an ongoing
    child-worry). These are the structural facts the elder-daughter reading rests on."""

    def test_rasi_fifth_lord_jupiter_in_the_eighth(self) -> None:
        """5th lord + Putrakaraka Jupiter sits in the 8th (Rasi) - the affliction seam."""
        rc = build_saptamsa_children_reading(_field_chart()).raman_core
        assert rc.rasi_fifth_lord == "Jupiter"
        assert rc.rasi_fifth_lord_house == 8

    def test_both_fertility_sphutas_barren(self) -> None:
        """Beeja AND Kshetra both weak - Raman's decisive progeny-denial signal."""
        rc = build_saptamsa_children_reading(_field_chart()).raman_core
        assert rc.beeja_strong is False and rc.kshetra_strong is False

    def test_children_verdict_afflicted(self) -> None:
        """The authoritative verdict is afflicted (the both-barren fertility denial)."""
        rc = build_saptamsa_children_reading(_field_chart()).raman_core
        assert rc.children_verdict == "afflicted"

    def test_putrakaraka_navamsa_own_is_the_redemptive_thread(self) -> None:
        """Jupiter is navamsa-own (Pisces) - the promise is afflicted but not annihilated."""
        rc = build_saptamsa_children_reading(_field_chart()).raman_core
        assert rc.putrakaraka_navamsa_dignity == "own"

    def test_eldest_seat_is_mars_ketu_on_the_d7_lagna(self) -> None:
        """The eldest-child seat (D-7 lagna, Leo) is tenanted by Mars + Ketu."""
        ov = build_saptamsa_children_reading(_field_chart()).d7_overlay
        assert ov.lagna_occupants == ("Mars", "Ketu")

    def test_eldest_affliction_carries_the_ketu_human_touch_citation(self) -> None:
        """Ketu on the eldest seat -> Raman's 'lacks the human touch towards one or two of
        the issues' (HTJAH-I:5293), applied to the D-7 by the general varga principle."""
        eldest = build_saptamsa_children_reading(_field_chart()).d7_overlay.child_loci[0]
        ketu = [a for a in eldest.afflictions if a.cite == "HTJAH-I:5293"]
        assert ketu and ketu[0].provenance == "RAMAN_GENERAL_PRINCIPLE"
        assert "human touch" in ketu[0].text
