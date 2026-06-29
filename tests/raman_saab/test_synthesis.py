"""Synthesis layer — the unified per-matter reading that fuses D1 + navamsa + varga + Ashtakavarga
+ dasha activation + transits. Pure assembly over already-computed data (verdict-invariant)."""
from __future__ import annotations

from app.raman_saab.chart.model import BirthData
from app.raman_saab.proforma import read_chart
from app.raman_saab.synthesis import synthesize, to_text

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_synthesize_has_twelve_matters_and_header():
    s = synthesize(_MAINPURI, on=(2026, 6, 28))
    assert len(s.matters) == 12
    assert s.lagna == "Scorpio" and s.atmakaraka == "Sun" and s.arudha_lagna == "Cancer"
    assert s.navamsa_lagna == "Scorpio"            # vargottama
    assert s.karakamsa == "Leo" and s.upapada == "Sagittarius" and s.spouse_significator == "Venus"
    assert s.karakamsa_reading and all("JS 1.2" in line for line in s.karakamsa_reading)
    assert len(s.deeptadi) >= 7 and any("Deeptha" in d or "Vikala" in d for d in s.deeptadi)
    assert s.career and "navamsa-dispositor" in s.career
    assert s.running_md == "Saturn" and s.running_ad == "Jupiter"
    assert s.chara == "Pisces"
    assert s.sade_sati and "setting" in s.sade_sati
    assert all(mr.reading for mr in s.matters)


def test_synthesis_verdicts_match_read_chart():
    """The synthesis must REPORT the D1 verdicts, never alter them."""
    s = synthesize(_MAINPURI, on=(2026, 6, 28))
    r = read_chart(_MAINPURI, ayanamsa="lahiri")
    assert [mr.verdict for mr in s.matters] == [pf.rollup for pf in r.proformas]


def test_to_text_renders():
    txt = to_text(synthesize(_MAINPURI, on=(2026, 6, 28)))
    assert "SYNTHESIS" in txt and "Lagna Scorpio" in txt
    assert "Ashtakavarga" in txt and "navamsa" in txt
