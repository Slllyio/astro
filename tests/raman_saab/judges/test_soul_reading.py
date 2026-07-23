"""Soul-destiny reading — `judges/soul_reading.py`.

Split into: (a) the Ketu-kaivalya predicate on Track-B synthetic charts (fast); (b) the report-only
verdict-authority invariant; (c) the citation-unlock proof (JAIMINI/JS cites resolve on disk); and
(d) a public-baseline smoke (CLAUDE.md Bangalore 1990 — never private birth data). Each test states
the fact it checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart import varga
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine import sources
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.judges import soul_reading as sr

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


def _lon_with_navamsa(target: int) -> float:
    """A sidereal longitude whose navamsa sign is `target` (1..12)."""
    for step in range(720):
        lon = step * 0.5
        if varga.navamsa_sign(lon) == target:
            return lon
    raise AssertionError(f"no lon found for navamsa {target}")


class TestKetuKaivalyaPredicate:
    def test_fires_when_ketu_navamsa_is_12th_from_karakamsa(self) -> None:
        """Jupiter (sole visible) is AK → Karakamsa = its navamsa; placing Ketu's navamsa in the
        12th from there makes the Kaivalya combination fire (H12.C.G2, HTJAH-II:16527)."""
        jup_lon = 29.0
        ks = varga.navamsa_sign(jup_lon)
        twelfth = ((ks - 1 + 11) % 12) + 1
        c = _chart({"Jupiter": jup_lon, "Ketu": _lon_with_navamsa(twelfth)})
        assert sr._ketu_kaivalya(c) is True

    def test_does_not_fire_otherwise(self) -> None:
        """Ketu's navamsa in the SAME sign as the Karakamsa (not the 12th) → no Kaivalya."""
        jup_lon = 29.0
        ks = varga.navamsa_sign(jup_lon)
        c = _chart({"Jupiter": jup_lon, "Ketu": _lon_with_navamsa(ks)})
        assert sr._ketu_kaivalya(c) is False


class TestIshtaDevata:
    def test_deity_from_occupant_of_12th_from_karakamsa(self) -> None:
        """Jupiter (sole visible) is AK → Karakamsa; the Sun placed (by navamsa) in the 12th from
        there names the Iṣṭa-Devatā as Śiva/Sūrya (the Sun's deity)."""
        jup_lon = 29.0
        ks = varga.navamsa_sign(jup_lon)
        twelfth = ((ks - 1 + 11) % 12) + 1
        c = _chart({"Jupiter": jup_lon, "Sun": _lon_with_navamsa(twelfth)})
        assert sr.special_points.atmakaraka(c) == "Jupiter"     # precondition: Jupiter is AK
        deity, basis = sr._ishta_devata(c)
        assert "Śiva" in deity and "Sun" in basis


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_soul_surface(self) -> None:
        """VERDICT-AUTHORITY INVARIANT: the D1 verdict path imports nothing from this surface, so
        the golden ratchet is untouched by construction."""
        import app.raman_saab.judges.house_template as ht
        src = Path(ht.__file__).read_text(encoding="utf-8")
        assert "soul_reading" not in src


class TestCitationUnlock:
    def test_jaimini_and_js_cites_resolve(self) -> None:
        """Every Jaimini/JS citation the surface can emit resolves on disk (the unlock works)."""
        for work in ("JAIMINI-49", "JS-1"):
            if sources._resolve_file(work) is None:
                pytest.skip(f"corpus for {work} not vendored")
            assert sources.verify(Citation(work, 1))


class TestSoulReadingSmoke:
    @pytest.fixture(scope="class")
    def reading(self) -> sr.SoulReading:
        return sr.build_soul_reading(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_assembles_all_three_regimes(self, reading: sr.SoulReading) -> None:
        """Parashari core + Jaimini overlay + nakshatra signature all build on a real chart."""
        assert isinstance(reading.core, sr.SoulCore)
        assert 1 <= reading.jaimini_overlay.karakamsa_sign <= 12
        assert 1 <= reading.jaimini_overlay.arudha_lagna_sign <= 12
        assert reading.jaimini_overlay.chara_karakas  # AK..DK roster non-empty
        assert reading.jaimini_overlay.ishta_devata   # moksha-deity resolved

    def test_chara_dasha_script_is_twelve_signs(self, reading: sr.SoulReading) -> None:
        """The Chara Dasha 'script' is the full 12-period sequence, every sign valid."""
        seq = reading.jaimini_overlay.chara_dasha
        assert len(seq) == 12
        assert all(1 <= s <= 12 and y > 0 for s, y in seq)

    def test_overlay_lines_are_all_tagged(self, reading: sr.SoulReading) -> None:
        """Every Jaimini overlay + nakshatra line carries a provenance tag (honesty invariant)."""
        for line in reading.jaimini_overlay.lines:
            assert isinstance(line, sr.SoulTagged) and line.provenance
        for e in reading.nakshatra_signature.entries:
            assert e.provenance in ("CLASSICAL_NONCITABLE", "EDITORIAL_SYNTHESIS")

    def test_narrative_weaves_the_soul_purpose(self, reading: sr.SoulReading) -> None:
        """The soul-purpose narrative is a readable paragraph naming the soul-significator."""
        assert reading.narrative and "soul-significator" in reading.narrative

    def test_argala_lines_if_present_are_cited(self, reading: sr.SoulReading) -> None:
        """Karakāṁśa argala lines (when they fire) carry the JS-1 Jaimini citation."""
        for line in reading.jaimini_overlay.lines:
            if "argala on the soul-seat" in line.text:
                assert line.cite == "JS-1" and line.provenance == "JAIMINI_EXPLICIT"

    def test_not_fatalism_caveat_present(self, reading: sr.SoulReading) -> None:
        """The 'not a fixed fate' honesty note must always be emitted (ABSENT_IN_RAMAN)."""
        assert any(n.provenance == "ABSENT_IN_RAMAN" for n in reading.notes)
