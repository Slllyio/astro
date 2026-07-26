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


class TestBphsCurseYogas:
    """The faithful per-verse encodings of BPHS Ch.83's own curse-yogas — each Track-B chart
    below constructs exactly one verse's condition (Aries ascendant unless stated: H5 = Leo,
    lord Sun; H10 = Capricorn, lord Saturn; H8 = Scorpio; H12 = Pisces)."""

    def test_father_5_exchange_of_5th_and_10th_lords(self) -> None:
        """Father #5 (BPHS-83:53): 5th/10th lords exchanged + malefics occupying Asc and 5th.
        Aries asc: Sun (5th lord) in Capricorn (10th), Saturn (10th lord) in Leo (5th) — the
        exchange; Saturn in Leo is also the 5th-house malefic; Mars in Aries the Asc malefic."""
        c = _chart({"Sun": 285.0, "Saturn": 125.0, "Mars": 5.0})
        fired = pd._bphs_curse_yogas(c)
        assert any("#5" in t.text and "father's curse" in t.text for t in fired)
        assert any(t.cite == "BPHS-83:53" for t in fired)

    def test_father_10_lord_chain(self) -> None:
        """Father #10 (BPHS-83:89): 12th lord in Asc, 8th lord in 5th, 10th lord in 8th.
        Aries asc: Jupiter (12th lord, Pisces) in Aries; Mars (8th lord, Scorpio) in Leo;
        Saturn (10th lord) in Scorpio."""
        c = _chart({"Jupiter": 5.0, "Mars": 125.0, "Saturn": 215.0})
        fired = pd._bphs_curse_yogas(c)
        assert any("#10" in t.text and "father's curse" in t.text for t in fired)

    def test_mother_2_saturn_11th_moon_debilitated_in_5th(self) -> None:
        """Mother #2 (BPHS-83-ii:118): Saturn in the 11th, malefics in the 4th, Moon in the
        5th in debilitation. Cancer asc (so the 5th is Scorpio — the Moon's debilitation
        sign): Saturn in Taurus (11th), Mars in Libra (4th), Moon at Scorpio 3° (deep
        debilitation)."""
        c = _chart({"Saturn": 45.0, "Mars": 190.0, "Moon": 213.0}, asc_lon=95.0)
        fired = pd._bphs_curse_yogas(c)
        assert any("#2" in t.text and "mother's curse" in t.text for t in fired)
        assert any(t.cite == "BPHS-83-ii:118" for t in fired)

    def test_mother_13_the_8th_house_cluster(self) -> None:
        """Mother #13 (BPHS-83-ii:165): Mars+Rahu+Jupiter in the 8th, Saturn+Moon in the 5th.
        Aries asc: 8th = Scorpio, 5th = Leo."""
        c = _chart({"Mars": 215.0, "Rahu": 220.0, "Jupiter": 225.0,
                    "Saturn": 125.0, "Moon": 130.0})
        fired = pd._bphs_curse_yogas(c)
        assert any("#13" in t.text and "mother's curse" in t.text for t in fired)

    def test_no_yoga_fires_on_a_clean_chart(self) -> None:
        """A lone benefic chart fires none of the encoded verse-combinations."""
        c = _chart({"Jupiter": 5.0})
        assert pd._bphs_curse_yogas(c) == ()

    def test_mother_5_requires_association_not_mere_placement(self) -> None:
        """Regression for the independent doctrine review's one substantive finding: mother #5's
        operative condition is the ASSOCIATION (samyoga) of Saturn/Rahu/Mars with the 5th lord
        or the Moon — a first placement-only encoding fired when the malefics sat together in
        the OTHER of the two houses, associated with neither. Aries asc, 5th = Leo (lord Sun),
        9th = Sagittarius. Divergent case: Sun+Moon in Leo (5th), Saturn+Rahu+Mars together in
        Sagittarius (9th) — placement satisfied, association absent -> must NOT fire. Faithful
        case: all five together in Leo -> fires."""
        c_apart = _chart({"Sun": 125.0, "Moon": 130.0,
                          "Saturn": 245.0, "Rahu": 250.0, "Mars": 255.0})
        assert not pd._mother_curse_fires(c_apart, 5)
        c_together = _chart({"Sun": 125.0, "Moon": 130.0,
                             "Saturn": 126.0, "Rahu": 127.0, "Mars": 128.0})
        assert pd._mother_curse_fires(c_together, 5)

    def test_every_encoded_yoga_carries_a_per_verse_cite(self) -> None:
        """Every registered combination cites its own source line (BPHS-83:<n> for the father
        list, BPHS-83-ii:<n> for the recovered mother list) — no pooled or heading cites."""
        for _num, cite, _text in pd._FATHER_CURSE_YOGAS:
            assert cite.startswith("BPHS-83:")
        for _num, cite, _text in pd._MOTHER_CURSE_YOGAS:
            assert cite.startswith("BPHS-83-ii:")
        assert len(pd._FATHER_CURSE_YOGAS) == 9      # of 11 (2 on record: hemming)
        assert len(pd._MOTHER_CURSE_YOGAS) == 11     # of 13 (2 on record: hemming/garble)

    def test_recovered_source_file_backs_the_mother_cites(self) -> None:
        """The BPHS-83-ii cites resolve into the RECOVERED source fragment on disk: each cited
        line of vol2_chapter_083_ii.md actually starts that verse's numbered combination.
        (Skipped where the knowledge library is not vendored — data/ is gitignored, so CI has
        no corpus; the established corpus-skip pattern.)"""
        src = (Path(__file__).resolve().parents[3] / "data" / "knowledge_library" / "sources"
               / "bphs" / "vol2_chapter_083_ii.md")
        if not src.exists():
            pytest.skip("bphs corpus not vendored on this machine")
        lines = src.read_text(encoding="utf-8").splitlines()
        for num, cite, _text in pd._MOTHER_CURSE_YOGAS:
            n = int(cite.split(":")[1])
            assert lines[n - 1].lstrip().startswith(f"({num})"), (cite, lines[n - 1])


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
        """The layering note must name both House-by-house reading and Your Reading as the
        sections carrying the native's own father/mother significations, state coexistence
        without contradiction, and never claim the layers are 'independent' (a reviewer-flagged
        overstatement in an early draft). Since the faithful re-encoding, the curse-yogas test
        BPHS's own 5th/Ascendant (father) and 4th/5th/Moon (mother) chains — a genuinely
        different region from the House 9/4 significations — and the note says so."""
        r = pd.build_pitru_dosha_reading(cast_chart(_BASELINE, ayanamsa="raman"))
        note = next((n for n in r.notes if "DIFFERENT LAYER" in n.text), None)
        assert note is not None, [n.text for n in r.notes]
        assert "House-by-house reading" in note.text and "Your Reading" in note.text
        assert "coexist" in note.text
        assert "5th house/Ascendant" in note.text      # BPHS's own father-curse region
        assert "independent" not in note.text.lower()  # the overstated framing the reviewer flagged

    def test_notes_disclose_the_encoding_scope(self) -> None:
        """The scope note names what is encoded (9 of 11 father, 11 of 13 mother), what is on
        record and why (hemming primitive, OCR garble, Gulika), and that the old editorial
        proxy was retired."""
        r = pd.build_pitru_dosha_reading(cast_chart(_BASELINE, ayanamsa="raman"))
        note = next((n for n in r.notes if "verse-combinations" in n.text), None)
        assert note is not None, [n.text for n in r.notes]
        assert "9 of 11" in note.text and "11 of 13" in note.text
        assert "hemming" in note.text and "Gulika" in note.text
        assert "RETIRED" in note.text
