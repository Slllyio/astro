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


def test_cli_reading_format(capsys):
    rc = main(["--name", "T", "--date", "1990-07-15", "--time", "12:00",
               "--tz", "5.5", "--lat", "12.97", "--lon", "77.59", "--format", "reading"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "RAMAN SAAB" in out and "Lagna:" in out and "HTJAH-" in out
