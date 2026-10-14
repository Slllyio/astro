"""Nabhasa yogas (BPHS ch.35) — Asraya and Sankhya detectors + the cited catalogue.

Detectors are pinned to Parashara's own definitions: Asraya by shared modality (sl.7), Sankhya by the
count of signs the seven grahas occupy (sl.16-17). Citations must resolve; the catalogue must cover
the chapter.
"""
from __future__ import annotations

from app.parashara.doctrine import nabhasa as N
from app.parashara.doctrine.sources import verify


def _seven(*signs: int) -> dict:
    """A planet_signs map for the seven grahas from seven sign numbers."""
    return dict(zip(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"), signs))


class TestAsraya:
    def test_all_movable_is_rajju(self):
        y = N.asraya_yoga(_seven(1, 4, 7, 10, 1, 4, 7))     # all in movable signs
        assert y is not None and y.name == "Rajju" and y.operable is True

    def test_all_fixed_is_musala(self):
        assert N.asraya_yoga(_seven(2, 5, 8, 11, 2, 5, 8)).name == "Musala"

    def test_all_dual_is_nala(self):
        assert N.asraya_yoga(_seven(3, 6, 9, 12, 3, 6, 9)).name == "Nala"

    def test_mixed_modality_is_none(self):
        assert N.asraya_yoga(_seven(1, 2, 3, 4, 5, 6, 7)) is None


class TestSankhya:
    def test_all_in_one_sign_is_gola(self):
        y = N.sankhya_yoga(_seven(5, 5, 5, 5, 5, 5, 5))
        assert y.name == "Gola" and y.operable is None      # operability unconfirmed by design

    def test_count_to_name(self):
        # 7 grahas across N distinct signs -> the Sankhya name for N.
        cases = {2: "Yuga", 3: "Soola", 4: "Kedara", 5: "Pasa", 6: "Damini", 7: "Veena"}
        for n, name in cases.items():
            signs = [((i % n) + 1) for i in range(7)]        # exactly n distinct signs
            assert N.sankhya_yoga(_seven(*signs)).name == name, (n, name)


class TestCatalogueAndCitations:
    def test_citations_resolve(self):
        assert verify(N.ASRAYA_SOURCE) and verify(N.SANKHYA_SOURCE)

    def test_catalogue_covers_the_chapter(self):
        cat = N.catalogue()
        assert len(cat) >= 30                                 # ch.35 is a long, well-numbered chapter
        assert all(verify(s.source) for s in cat)
        text = " ".join(s.text for s in cat).lower()
        assert "rajju" in text and "sankhya" in text.replace("saakhya", "sankhya")
