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
from app.raman_saab.doctrine import drishti
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

    def test_serpent_1_rahu_in_5th_aspected_by_mars(self) -> None:
        """Serpent #1 (BPHS-83-iii:70): Rahu in the 5th, aspected by Mars. Aries asc, 5th =
        Leo: Rahu in Leo; Mars in Aries (1st) casts its 5th-house-reaching aspect? Mars aspects
        the 4th and 8th from itself — from Aries(1) that is Cancer(4) and Scorpio(8), not Leo.
        Put Mars where it aspects Leo(5): Mars in Aquarius(11) aspects the 4th (Taurus) and 8th
        (Virgo)... use the 7th aspect — Mars in Aquarius(11) aspects Leo(5) by the 7th. So Mars
        in Aquarius, Rahu in Leo."""
        c = _chart({"Rahu": 130.0, "Mars": 310.0})   # Leo(5th), Aquarius(11th) — 7th aspect
        assert drishti.aspects_house("Mars", 5, c)
        fired = pd._bphs_curse_yogas(c)
        assert any("#1" in t.text and "serpent's curse" in t.text for t in fired)

    def test_serpent_7_the_crowded_fifth(self) -> None:
        """Serpent #7 (BPHS-83-iii:94): the 5th holds Sun, Saturn, Mars, Rahu, Mercury and
        Jupiter together, and the 5th and Ascendant lords are devoid of strength. Track-B
        charts have no Shadbala, so _devoid_of_strength reads False and the yoga cannot fire —
        the structural (six-in-the-5th) precondition is checked directly instead."""
        leo = {p: 125.0 + i for i, p in enumerate(
            ("Sun", "Saturn", "Mars", "Rahu", "Mercury", "Jupiter"))}
        c = _chart(leo)
        assert all(pd._in_h(c, p, 5) for p in leo)     # the six-in-the-5th precondition holds
        assert not pd._serpent_curse_fires(c, 7)        # but no Shadbala -> devoid-of-strength False

    def test_serpent_5_stays_on_record_gulika(self) -> None:
        """Serpent #5 needs Gulika (Ascendant occupied by Rahu AND Gulika) — not computed, so
        it is absent from the encoded list."""
        assert 5 not in {num for num, _c, _t in pd._SERPENT_CURSE_YOGAS}
        assert len(pd._SERPENT_CURSE_YOGAS) == 7        # of 8 (only #5, Gulika, on record)

    def test_no_yoga_fires_on_a_clean_chart(self) -> None:
        """A lone benefic chart fires none of the encoded verse-combinations."""
        c = _chart({"Jupiter": 5.0})
        assert pd._bphs_curse_yogas(c) == ()

    def test_father_1_hemmed_sun_in_5th(self) -> None:
        """Father #1 (BPHS-83:33): Sun in the 5th, debilitated, in Saturn's navamsa, hemmed
        between malefics. Aries asc, 5th = Leo. The Sun is not debilitated in Leo — use a
        sign where Sun IS debilitated AND lands in the 5th: Libra ascendant makes the 5th
        Aquarius; the Sun in Libra (debilitation) is the 1st, not the 5th. So this needs the
        Sun debilitated (Libra, sign 7) sitting in house 5 -> ascendant sign 3 (Gemini): 5th
        = Libra. Sun at Libra with a Saturn-ruled navamsa, flanked by malefics in Virgo (4th)
        and Scorpio (6th)."""
        # Gemini asc (asc_lon ~65°): house of a planet = ((sign-3)%12)+1. Libra(7) -> house 5.
        sun_lon = 190.0            # Libra ~10°; navamsa of Libra 10° is Gemini... adjust below
        # find a Libra longitude whose navamsa sign is Saturn-ruled (Capricorn/Aquarius)
        from app.raman_saab.chart import varga
        sun_lon = next(l for l in (180 + 0.5 * k for k in range(60))
                       if varga.navamsa_sign(l) in (10, 11))
        c = _chart({"Sun": sun_lon, "Mars": 160.0, "Saturn": 220.0}, asc_lon=65.0)
        # Virgo(6)=4th, Scorpio(8)=6th flank Libra(7)=5th; Mars in Virgo, Saturn in Scorpio
        assert pd.hemming.hemmed_planet(c, "Sun")
        fired = pd._bphs_curse_yogas(c)
        assert any("#1" in t.text and "father's curse" in t.text for t in fired)

    def test_mother_9_ascendant_house_hemming(self) -> None:
        """Mother #9 (BPHS-83-ii:144): the (empty) Ascendant hemmed between malefics, a waning
        Moon in the 7th, Rahu in the 4th and Saturn in the 5th. Aries asc: malefics in Pisces
        (12th) and Taurus (2nd) hem the empty Lagna; a waning Moon (>=180° from the Sun) in
        Libra (7th); Rahu in Cancer (4th); Saturn in Leo (5th)."""
        c = _chart({"Sun": 5.0, "Ketu": 345.0, "Mars": 45.0,   # Ketu Pisces(12), Mars Taurus(2)
                    "Moon": 195.0,                              # Libra, and 190° behind... waning
                    "Rahu": 100.0, "Saturn": 130.0})
        assert pd.hemming.hemmed_house(c, 1)       # Lagna is empty yet hemmed — the house form
        assert pd._waning_moon(c)
        fired = pd._bphs_curse_yogas(c)
        assert any("#9" in t.text and "mother's curse" in t.text for t in fired)

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
        for _num, cite, _text in pd._SERPENT_CURSE_YOGAS:
            assert cite.startswith("BPHS-83-iii:")
        assert len(pd._FATHER_CURSE_YOGAS) == 11     # all 11 (hemming now encoded)
        assert len(pd._MOTHER_CURSE_YOGAS) == 12     # of 13 (#10 OCR-garbled, on record)
        assert len(pd._SERPENT_CURSE_YOGAS) == 7     # of 8 (#5 needs Gulika, on record)

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
        """The scope note names what is encoded (all 11 father, 12 of 13 mother since the
        hemming primitive closed the gap), what is still on record and why (OCR garble,
        Gulika), and that the old editorial proxy was retired."""
        r = pd.build_pitru_dosha_reading(cast_chart(_BASELINE, ayanamsa="raman"))
        note = next((n for n in r.notes if "verse-combinations" in n.text), None)
        assert note is not None, [n.text for n in r.notes]
        assert "11 of 11" in note.text and "12 of 13" in note.text
        assert "7 of 8" in note.text                      # the recovered serpent block
        assert "hemming" in note.text and "Gulika" in note.text
        assert "RETIRED" in note.text
