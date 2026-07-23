"""Family soul-group synthesis — `judges/family_soul_group.py`.

Pins the interlock detectors on hand-built soul-signatures (swisseph-free, like
`test_two_spouse_children.py`): each fires on genuine agreement and NOT on distinct signatures, and
the 'nets nothing' contract holds (no group verdict). Each test states the interlock it checks.
"""
from __future__ import annotations

from dataclasses import fields

from app.raman_saab.judges.family_soul_group import (
    FamilySoulGroup, SoulSignature, synthesize_from_signatures)


def _sig(role: str, *, ak_planet: str = "Sun", ak_sign: int = 1, ak_nak: int = 1,
         ks: int = 1, ketu_sign: int = 1, ketu_nak: int = 1,
         karakas: tuple[tuple[str, str], ...] = (), arudha: int = 1) -> SoulSignature:
    return SoulSignature(role=role, ak_planet=ak_planet, ak_sign=ak_sign, ak_nakshatra=ak_nak,
                         karakamsa_sign=ks, ketu_sign=ketu_sign, ketu_nakshatra=ketu_nak,
                         karakas=karakas, arudha_sign=arudha)


def _has(tags: tuple, needle: str) -> bool:
    return any(needle in t.text for t in tags)


class TestFamilySoulGroup:
    def test_shared_ak_sign_is_a_soul_frame(self) -> None:
        """Two members with the same Ātmakāraka sign share a soul-frame."""
        g = synthesize_from_signatures((_sig("father", ak_sign=5), _sig("mother", ak_sign=5)))
        assert _has(g.shared_soul_frames, "father, mother share the same Ātmakāraka sign")

    def test_distinct_signatures_raise_no_false_frame(self) -> None:
        """Fully distinct signatures (signs AND nakshatras) → no fabricated shared frame."""
        g = synthesize_from_signatures((
            _sig("father", ak_sign=1, ak_nak=1, ks=2, ketu_sign=3, ketu_nak=3),
            _sig("mother", ak_sign=4, ak_nak=4, ks=5, ketu_sign=6, ketu_nak=6)))
        assert g.shared_soul_frames == ()

    def test_karmic_role_swap_ak_is_anothers_darakaraka(self) -> None:
        """The father's soul-planet being the mother's Darakāraka is a karmic role-interlock."""
        g = synthesize_from_signatures((
            _sig("father", ak_planet="Venus"),
            _sig("mother", ak_planet="Jupiter", karakas=(("AK", "Jupiter"), ("DK", "Venus")))))
        assert _has(g.role_swaps, "father's soul-planet (Venus) is mother's DK")

    def test_ketu_axis_shared_sign(self) -> None:
        """Two members with the same Ketu sign sit on a shared past-life axis."""
        g = synthesize_from_signatures((_sig("a", ketu_sign=8), _sig("b", ketu_sign=8)))
        assert _has(g.ketu_axis, "share the same Ketu sign")

    def test_ketu_seats_another_karakamsa(self) -> None:
        """One member's Ketu sign equal to another's Karakāṁśa → the mokṣa-vehicle seats the soul."""
        g = synthesize_from_signatures((_sig("a", ketu_sign=3), _sig("b", ks=3, ketu_sign=9)))
        assert _has(g.ketu_axis, "seats")

    def test_recurring_motif_when_majority_share_ak_sign(self) -> None:
        """An AK sign held by ≥ half the members is the family's dominant soul-motif."""
        g = synthesize_from_signatures((
            _sig("a", ak_sign=7), _sig("b", ak_sign=7), _sig("c", ak_sign=7), _sig("d", ak_sign=2)))
        assert _has(g.recurring_motif, "recurs in 3/4")

    def test_nets_no_group_verdict(self) -> None:
        """The 'report both, net nothing' contract: no combined/group verdict field exists."""
        g = synthesize_from_signatures((_sig("a"), _sig("b")))
        names = {f.name for f in fields(FamilySoulGroup)}
        assert names == {"signatures", "shared_soul_frames", "role_swaps", "ketu_axis",
                         "recurring_motif", "narrative", "notes"}
        assert not hasattr(g, "group_verdict")

    def test_group_narrative_is_a_readable_story(self) -> None:
        """The group narrative weaves the interlocks into one readable story."""
        g = synthesize_from_signatures((_sig("a", ak_sign=5), _sig("b", ak_sign=5)))
        assert g.narrative.startswith("These 2 souls")
        assert "soul-frame" in g.narrative

    def test_nets_nothing_caveat_always_present(self) -> None:
        """The honesty note that no text nets souls together must always be emitted."""
        g = synthesize_from_signatures((_sig("a"), _sig("b")))
        assert any(n.provenance == "ABSENT_IN_RAMAN" for n in g.notes)
