"""Two-spouse progeny synthesis — `judges/two_spouse_children.py`.

Pins the report-only cross-reference of BOTH parents' children testimonies (HTJAH-I:5436) and
the offsetting/redemptive thread (HTJAH-I:5968). Readings are hand-built (no swisseph cast), so
these tests are fast and deterministic and exercise the concordance/redemption logic directly.
Each test states the doctrinal fact it verifies. The governing contract is 'report both, net
nothing' — there is NO combined verdict.
"""
from __future__ import annotations

from dataclasses import fields

from app.raman_saab.judges.saptamsa_reading import (
    ChildLocus, D7Overlay, RamanCore, SaptamsaChildrenReading, Tagged)
from app.raman_saab.judges.two_spouse_children import (
    TwoSpouseChildrenSynthesis, synthesize_from_readings)


def _reading(*, verdict: str, fifth_lord: str = "Mercury", fifth_lord_house: int = 8,
             fifth_lord_dignity: str = "neutral", pk_house: int = 8, pk_nav: str = "own",
             beeja: bool | None = False, kshetra: bool | None = False,
             eldest_affl: tuple[Tagged, ...] = ()) -> SaptamsaChildrenReading:
    """A minimal Saptamsa reading carrying only the fields the synthesis distils."""
    rc = RamanCore(
        rasi_fifth_sign=3, rasi_fifth_lord=fifth_lord, rasi_fifth_lord_house=fifth_lord_house,
        rasi_fifth_lord_dignity=fifth_lord_dignity,  # type: ignore[arg-type]
        rasi_fifth_occupants=(), rasi_fifth_aspecting=(), putrakaraka="Jupiter",
        putrakaraka_house=pk_house, putrakaraka_dignity="neutral",
        putrakaraka_navamsa_dignity=pk_nav,  # type: ignore[arg-type]
        beeja_strong=beeja, kshetra_strong=kshetra, children_verdict=verdict,
        verdict_metadata=())
    eldest = ChildLocus(ordinal=1, label="eldest", frame="D7-lagna",
                        scheme="RAMAN_GENERAL_PRINCIPLE", sign=1, lord="Sun",
                        occupants=(), aspecting=(), afflictions=eldest_affl)
    ov = D7Overlay(lagna_sign=1, lagna_lord="Sun", lagna_occupants=(), fifth_sign=5,
                   fifth_lord="Sun", fifth_occupants=(), jupiter_sign=1, jupiter_house=1,
                   jupiter_dignity="neutral", child_loci=(eldest,), gender_indicators=())
    return SaptamsaChildrenReading(raman_core=rc, d7_overlay=ov, notes=())


def _has(tags: tuple[Tagged, ...], needle: str) -> bool:
    return any(needle in t.text for t in tags)


class TestTwoSpouseChildren:
    def test_both_afflicted_and_both_sphutas_weak_are_concordances(self) -> None:
        """Both spouses' 5th houses afflicted + both Beeja & Kshetra weak → three concordances
        (HTJAH-I:5436 two-witness verdict; HTJAH-I:5517 barren sphutas in both)."""
        father = _reading(verdict="afflicted", fifth_lord="Jupiter", fifth_lord_house=8)
        mother = _reading(verdict="afflicted", fifth_lord="Mercury", fifth_lord_house=8,
                          fifth_lord_dignity="exalt", pk_house=5)
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert _has(syn.concordances, "read the children matter AFFLICTED")
        assert _has(syn.concordances, "Beeja")
        assert _has(syn.concordances, "Kshetra")

    def test_both_fifth_lords_in_dusthana_is_a_concordance(self) -> None:
        """Both 5th-lords in the 8th (a dusthana) → the exiled-significator concordance fires."""
        father = _reading(verdict="afflicted", fifth_lord="Jupiter", fifth_lord_house=8)
        mother = _reading(verdict="afflicted", fifth_lord="Mercury", fifth_lord_house=8)
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert _has(syn.concordances, "5th-lord sits in a dusthana in BOTH")

    def test_navamsa_own_in_both_is_a_two_witness_redemption(self) -> None:
        """Putra-Karaka navamsa-own in BOTH charts → a per-parent line each + the TWO-WITNESS
        redemptive line (HTJAH-I:5968)."""
        father = _reading(verdict="afflicted", pk_nav="own")
        mother = _reading(verdict="afflicted", pk_nav="own")
        syn = synthesize_from_readings(father, "father", mother, "mother")
        per_parent = [t for t in syn.redemptive_thread if "navamsa-own in the" in t.text]
        assert len(per_parent) == 2
        assert _has(syn.redemptive_thread, "TWO-WITNESS")

    def test_mother_specific_mitigants_are_reported(self) -> None:
        """An exalted 5th-lord and a Putra-Karaka seated in the 5th → both offsetting
        significators surface, attributed to the mother (HTJAH-I:5968)."""
        father = _reading(verdict="afflicted", fifth_lord="Jupiter", fifth_lord_house=8)
        mother = _reading(verdict="afflicted", fifth_lord="Mercury", fifth_lord_house=8,
                          fifth_lord_dignity="exalt", pk_house=5)
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert _has(syn.redemptive_thread, "5th-lord Mercury is EXALTED in the mother's chart")
        assert _has(syn.redemptive_thread, "occupies the 5th itself in the mother's chart")

    def test_reports_both_and_nets_no_combined_verdict(self) -> None:
        """The 'report both, net nothing' contract: two testimonies surface, and the synthesis
        exposes NO combined/overall verdict field."""
        father = _reading(verdict="afflicted")
        mother = _reading(verdict="afflicted")
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert len(syn.testimonies) == 2
        assert {f.name for f in fields(TwoSpouseChildrenSynthesis)} == {
            "testimonies", "concordances", "redemptive_thread", "notes"}
        assert not hasattr(syn, "combined_verdict")
        assert not hasattr(syn, "verdict")

    def test_one_favourable_parent_raises_no_false_concordance(self) -> None:
        """If only one parent is afflicted (the other favourable with strong sphutas), the
        both-afflicted and both-weak concordances must NOT fire — no fabricated agreement."""
        father = _reading(verdict="afflicted", beeja=False, kshetra=False)
        mother = _reading(verdict="favourable", beeja=True, kshetra=True, pk_house=5)
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert not _has(syn.concordances, "AFFLICTED")
        assert not _has(syn.concordances, "Beeja")
        assert not _has(syn.concordances, "Kshetra")

    def test_eldest_seat_afflictions_carry_into_the_testimony(self) -> None:
        """Each parent's eldest-child (D-7 lagna) afflictions are preserved on the testimony."""
        mark = Tagged("Ketu on the seat - lacks the human touch", "RAMAN_GENERAL_PRINCIPLE",
                      "HTJAH-I:5293")
        father = _reading(verdict="afflicted", eldest_affl=(mark,))
        mother = _reading(verdict="afflicted")
        syn = synthesize_from_readings(father, "father", mother, "mother")
        assert syn.testimonies[0].d7_eldest_afflictions == (mark,)

    def test_the_no_netting_caveat_is_always_present(self) -> None:
        """The honesty note that Raman gives no netting formula must always be emitted."""
        syn = synthesize_from_readings(
            _reading(verdict="afflicted"), "father", _reading(verdict="afflicted"), "mother")
        assert any(t.provenance == "ABSENT_IN_RAMAN" for t in syn.notes)
