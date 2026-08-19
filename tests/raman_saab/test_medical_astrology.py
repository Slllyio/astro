"""HPA-29 medical astrology — the tables and the 6th-house reader that applies them.

Each test states the doctrinal fact it verifies. The citation tests are corpus-gated the
same way the rest of the doctrine suite is: they verify against Raman's printed text when
it is mounted and skip when it is not.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine import medical_astrology as ma
from app.raman_saab.judges.medical_reading import build_medical_reading

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

try:
    from app.raman_saab.doctrine.sources import verify
    _HAS_CORPUS = verify(ma.CITE_SIGN_ANATOMY)
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


#: Gemini rising, so the 6th SIGN (Scorpio, 8) and the 6th HOUSE (6) are different numbers —
#: and both are occupied by different grahas. Saturn and Ketu stand in the 6th house; Jupiter
#: stands in house 8. Any code that asks an occupancy question with the sign number answers
#: "Jupiter" here, which is how the frame confusion below is caught rather than argued about.
_OCCUPIED_SIXTH = BirthData("Occupied 6th", 1985, 1, 10, 18, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def chart():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL).chart


@pytest.fixture(scope="module")
def occupied_chart():
    from app.raman_saab.chart.adapter import cast_chart
    return cast_chart(_OCCUPIED_SIXTH, ayanamsa="lahiri")


class TestTables:
    def test_every_rasi_has_anatomy_and_diseases(self):
        """HPA-29 §6 and §7 are complete tables over the twelve rasis — a missing sign
        would silently drop a whole body region from every chart rising against it."""
        assert set(ma.SIGN_ANATOMY) == set(range(1, 13))
        assert set(ma.SIGN_DISEASES) == set(range(1, 13))
        for s in range(1, 13):
            assert ma.SIGN_ANATOMY[s], s
            assert ma.SIGN_DISEASES[s], s

    def test_the_tables_cover_the_seven_grahas_and_no_more(self):
        """Raman's §8/§9 tables are of the seven VISIBLE planets. Rahu and Ketu own no
        row, and the engine must not invent one — they are chayagrahas and the directive
        forbids minting doctrine from memory."""
        for table in (ma.PLANET_ORGANS, ma.PLANET_STRUCTURES, ma.PLANET_DISEASES):
            assert set(table) == set(_SEVEN)
        assert ma.planet_diseases("Rahu") == ()
        assert ma.planet_diseases("Ketu") == ()
        assert ma.planet_organs("Rahu") == ()

    def test_no_sign_name_leaked_into_an_anatomy_row(self):
        """The corpus reads 'Pisces.—Taurus, blood circulation, meta-tarsus' — a sign name
        standing where a body part belongs (HPA-29:337). Encoding 'Taurus' as an anatomical
        structure would put visible OCR damage into a reading, so it is dropped, and this
        test stops it or any like it from creeping back in."""
        signs = {n.casefold() for n in
                 ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                  "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")}
        for s, parts in ma.SIGN_ANATOMY.items():
            for part in parts:
                assert part.casefold() not in signs, f"sign {s}: {part!r}"

    def test_the_ocr_damage_is_registered_not_silently_repaired(self):
        """The PRIME DIRECTIVE forbids silent approximation. Every departure from a literal
        reading is recorded in OCR_NOTES with the literal text, including the Pisces row and
        the editorial structures/diseases split for the Sun and Saturn."""
        blob = " ".join(note for _k, note in ma.OCR_NOTES)
        assert "HPA-29:337" in blob                      # the Pisces line is named
        assert "DROPPED" in blob or "dropped" in blob
        assert "EDITORIAL" in blob                       # the Sun/Saturn split is owned
        keys = " ".join(k for k, _n in ma.OCR_NOTES)
        assert "Pisces" in keys and "Saturn" in keys

    def test_the_caveat_refuses_the_medical_register(self):
        """These are correspondence tables. The caveat that travels with them must say so
        and must not read as diagnosis or as a forecast of illness."""
        assert "not a medical statement" in ma.CAVEAT.casefold()
        assert "diagnos" in ma.CAVEAT.casefold()
        assert "prediction" in ma.CAVEAT.casefold()

    def test_the_provenance_note_states_ramans_own_pedigree_claim(self):
        """Raman himself answers the objection that the ancients could not have known these
        disease names (HPA-29:353-362). The report states that pedigree rather than
        presenting a compiled table as revelation."""
        assert "Ayurvedic" in ma.PROVENANCE_NOTE
        assert "compiled" in ma.PROVENANCE_NOTE
        assert "HPA-29:353" in ma.PROVENANCE_NOTE


@pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
class TestCitationsResolve:
    def test_every_anchor_resolves(self):
        """Each table cites its own block, so a consumer quotes the lines it actually used."""
        from app.raman_saab.doctrine.sources import verify
        for c in (ma.CITE_SIGN_ANATOMY, ma.CITE_SIGN_DISEASES, ma.CITE_PLANET_ORGANS,
                  ma.CITE_PLANET_RULERSHIP, ma.CITE_APPLICATION,
                  ma.CITE_PROVENANCE_CAUTION):
            assert verify(c), f"{c.work}:{c.line}"

    def test_the_application_rule_is_quoted_verbatim_from_the_anchor(self):
        """`APPLICATION` is Raman's sentence, not a paraphrase — the whole reader is built
        on it, so it is checked word-for-word against the printed text at its own anchor."""
        from app.raman_saab.doctrine.sources import _resolve_file
        import re
        path = _resolve_file("HPA-29")
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        window = " ".join(lines[ma.CITE_APPLICATION.line - 1:ma.CITE_APPLICATION.line + 12])
        norm = re.sub(r"\s+", " ", window.replace("¬ ", "")).casefold()
        for fragment in ("the house of diseases is the sixth from",
                         "the navamsa",
                         "the particular part of the body governed by the sign"):
            assert fragment in norm, fragment


class TestReader:
    def test_all_four_of_ramans_testimonies_are_read(self, occupied_chart):
        """HPA-29 §10 names four things to consider: the planets in the 6th, the lord of
        the 6th, the aspects on the 6th, and the navamsa the 6th lord occupies. The reader
        follows the sentence literally, and each clause is surfaced separately so a reader
        can see which one produced which line. Read on a chart whose 6th house is occupied,
        because the occupant clause cannot fire on an empty one."""
        m = build_medical_reading(occupied_chart)
        assert m is not None
        clauses = {t.clause for t in m.testimonies}
        assert "the sign on the 6th — the body regions marked" in clauses
        assert "the lord of the 6th" in clauses
        assert "the navamsa the 6th lord occupies" in clauses
        assert any(c.startswith("a planet in the 6th") for c in clauses)

    def test_the_three_unconditional_clauses_read_on_an_empty_sixth(self, chart):
        """The canonical chart's 6th house is EMPTY — Virgo rising puts Aquarius on it and
        no graha stands there. The occupant clause is then correctly silent, and the three
        clauses that do not depend on occupancy still read. A reader must be able to tell an
        empty 6th from an unread one."""
        m = build_medical_reading(chart)
        assert m.occupants == ()
        clauses = {t.clause for t in m.testimonies}
        assert "the sign on the 6th — the body regions marked" in clauses
        assert "the lord of the 6th" in clauses
        assert "the navamsa the 6th lord occupies" in clauses
        assert not any(c.startswith("a planet in the 6th") for c in clauses)

    def test_occupancy_and_drishti_are_asked_of_the_house_not_the_sign(self, occupied_chart):
        """Regression. `sixth` is a SIGN number — it indexes HPA-29's anatomy tables — while
        occupancy and drishti are HOUSE questions. Asking them with the sign number reads a
        different house entirely, and the two frames coincide only for an Aries lagna, so the
        error is invisible on exactly one chart in twelve. Here Gemini rises: the 6th house
        holds Saturn and Ketu, while sign 8 read as a house holds Jupiter."""
        m = build_medical_reading(occupied_chart)
        assert m.sixth_sign == 8                    # Scorpio — the anatomy-table frame
        assert "Saturn" in m.occupants              # the real 6th HOUSE
        assert "Jupiter" not in m.occupants         # what the sign-as-house frame returned
        assert "Jupiter" not in m.aspecting
        houses = {n: p.rasi_house for n, p in occupied_chart.planets.items()}
        assert set(m.occupants) | set(m.unlisted_bodies) >= {
            n for n, h in houses.items() if h == 6}

    def test_the_sixth_is_taken_from_the_ascendant(self, chart):
        """'The house of diseases is the sixth FROM THE ASCENDANT' — Virgo rising on the
        canonical chart puts the 6th in Aquarius, and Saturn owns it."""
        m = build_medical_reading(chart)
        assert m.sixth_sign_name == "Aquarius"
        assert m.sixth_lord == "Saturn"

    def test_a_node_in_the_testimony_is_disclosed_not_dropped(self, occupied_chart):
        """Ketu occupies the 6th house on this chart and Rahu aspects it. Raman's tables have
        no node row, so they contribute nothing — but a silent skip would let a reader believe
        the 6th was empty of them. They are reported as present-but-unlisted."""
        m = build_medical_reading(occupied_chart)
        assert "Ketu" in m.occupants
        assert set(m.unlisted_bodies) == {"Ketu", "Rahu"}
        assert not any(t.actor in ("Rahu", "Ketu") for t in m.testimonies)

    def test_regions_and_complaints_are_deduplicated_but_order_stable(self, chart):
        """Two testimonies naming 'consumption' say it once — a repeated complaint is not
        extra evidence, and this reading takes no vote. Order follows Raman's own clause
        order so the strongest testimony (the sign on the 6th) reads first."""
        m = build_medical_reading(chart)
        assert len(m.regions_marked) == len(set(x.casefold() for x in m.regions_marked))
        assert len(m.complaints_indicated) == len(
            set(x.casefold() for x in m.complaints_indicated))
        first = m.testimonies[0]
        assert m.regions_marked[:len(first.regions)] == first.regions

    def test_an_aspecting_planet_contributes_complaints_but_not_regions(self, chart):
        """Raman's last clause ties the BODY PART to the sign and the planet in it: 'The
        planet in the 6th house affect the particular part of the body governed by the
        sign.' An aspect is not occupancy, so an aspecting graha lends its diseases without
        claiming a region of its own."""
        m = build_medical_reading(chart)
        asp = [t for t in m.testimonies if t.clause == "a planet aspecting the 6th"]
        assert asp, "the canonical chart has Mars aspecting the 6th"
        for t in asp:
            assert t.regions == ()
            assert t.complaints

    def test_every_testimony_carries_its_own_citation_and_reason(self, chart):
        """No line of a reading may appear without saying where it came from and why it
        applies to THIS chart."""
        m = build_medical_reading(chart)
        for t in m.testimonies:
            assert t.citation.startswith("HPA-29:"), t.clause
            assert t.why and len(t.why) > 20, t.clause
            assert t.regions or t.complaints, t.clause

    def test_a_chart_with_no_resolvable_ascendant_returns_none(self):
        """Sparse Track-B charts decline rather than invent a 6th house."""
        class _Stub:
            asc_sign = 0
            planets: dict = {}
        assert build_medical_reading(_Stub()) is None


class TestVerdictAuthorityInvariant:
    def test_the_verdict_path_does_not_import_the_medical_layer(self):
        """The golden ratchet must be untouchable by this addition. `house_template` and
        the modules it judges through may never import either the tables or the reader —
        this is the same wall `varga_judge` and the matter-varga readings stand behind."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2] / "app" / "raman_saab"
        verdict_path = (
            root / "judges" / "house_template.py",
            root / "judges" / "total.py",
            root / "judges" / "conditions.py",
        )
        for f in verdict_path:
            if not f.exists():
                continue
            src = f.read_text(encoding="utf-8")
            assert "medical_astrology" not in src, f
            assert "medical_reading" not in src, f
