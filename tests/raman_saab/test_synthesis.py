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
    assert s.panchanga and "Tithi" in s.panchanga and "Vara" in s.panchanga
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


_CANONICAL = BirthData(name="C", year=1990, month=7, day=15, hour=12, minute=0,
                       tz_offset=5.5, latitude=12.97, longitude=77.59)


def test_navamsa_clause_names_both_frames_when_they_differ():
    """Canonical chart H3: the LEAD ledger is the MOON frame (navamsa 'confirms') while the
    LAGNA ledger — which the report's pillar line prints as 'Navamsa neutral' — differs. The
    reading line must DISCLOSE the frame so both lines are true statements about named frames
    (REPORT_CRITIQUE_2026-08-17 P0: the H3 self-contradiction)."""
    s = synthesize(_CANONICAL, on=(2026, 8, 17))
    h3 = next(mr for mr in s.matters if mr.house == 3)
    assert "and the navamsa confirms it (delivered)" in h3.reading
    assert "read from the Moon-frame" in h3.reading
    assert "from the Lagna the navamsa is neutral" in h3.reading


def test_navamsa_clause_undisclosed_when_frames_agree_or_lead_is_lagna():
    """No disclosure tail when the lead IS the lagna frame, or when both frames' navamsa
    testimonies agree — the original wording is byte-identical."""
    from app.raman_saab.synthesis import _compose
    base = _compose("favourable", "confirms", None, None, None)
    assert base == _compose("favourable", "confirms", None, None, None,
                            lead_frame="lagna", lagna_navamsa="neutral")
    assert base == _compose("favourable", "confirms", None, None, None,
                            lead_frame="moon", lagna_navamsa="confirms")
    assert "frame" not in base


def test_frame_disclosure_is_ascii():
    """The disclosure tail must survive the ASCII fold (CP1252 consoles)."""
    from app.raman_saab.synthesis import _compose
    line = _compose("afflicted", "confirms", None, None, None,
                    lead_frame="moon", lagna_navamsa="neutral")
    assert line == line.encode("ascii", "ignore").decode()
