"""read_chart -> RamanReading -> rendered worksheet, and the CLI `reading` format."""
from __future__ import annotations

from app.raman_saab import render
from app.raman_saab.chart.model import BirthData
from app.raman_saab.cli import main
from app.raman_saab.proforma import RamanReading, read_chart

_BLR = BirthData("Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


def test_read_chart_returns_12_house_verdicts():
    reading = read_chart(_BLR, ayanamsa="raman")
    assert isinstance(reading, RamanReading)
    assert len(reading.houses) == 12
    assert [h.house for h in reading.houses] == list(range(1, 13))
    for hv in reading.houses:
        assert hv.verdict in ("favourable", "mixed", "afflicted", "insufficient-evidence")


def test_render_text_is_ascii_safe_and_cites():
    text = render.to_text(read_chart(_BLR, ayanamsa="raman"))
    text.encode("cp1252")                       # must not raise (renders on Windows console)
    assert "RAMAN SAAB" in text and "House 7" in text
    assert "HTJAH-" in text                      # citations present


def test_render_markdown():
    md = render.to_markdown(read_chart(_BLR, ayanamsa="raman"))
    assert md.startswith("# Raman Saab reading")
    assert md.count("## House") == 12


def test_render_surfaces_dasha_timing_and_metadata():
    """The render-gap fix: the reading now flows through the MODERN judge, so the Dasha
    event-timing and the formerly-stranded metadata reach the worksheet."""
    txt = render.to_text(read_chart(_BLR, ayanamsa="raman"))
    assert "active Dasha" in txt          # significator event-timing windows
    assert "death-prone Dasha" in txt     # H8 death_window
    assert "longevity span" in txt        # ayurdaya span (was stranded before)


def test_read_chart_carries_proformas_with_metadata():
    """`proformas` carries the modern per-house result incl. metadata; verdicts stay valid
    (the timing layer is metadata-only — the strict ratchet, tested elsewhere, is unchanged)."""
    reading = read_chart(_BLR, ayanamsa="raman")
    assert len(reading.proformas) == 12
    h8 = next(p for p in reading.proformas if p.house == 8)
    keys = {k for k, _ in h8.metadata}
    assert {"ayurdaya", "death_window", "active_periods"} <= keys
    for p in reading.proformas:
        assert p.rollup in ("favourable", "mixed", "afflicted", "insufficient-evidence")


def test_cli_reading_format(capsys):
    rc = main(["--name", "T", "--date", "1990-07-15", "--time", "12:00",
               "--tz", "5.5", "--lat", "12.97", "--lon", "77.59", "--format", "reading"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "RAMAN SAAB" in out and "Lagna:" in out and "HTJAH-" in out
