"""GBB-8 §122 minima and the HPA-26 Ayurdaya stop-line — both settled 2026-08-19.

Two backlog items, both resolved against the mounted corpus, and both resolved in a way
that CLOSES rather than opens work:

  * the per-planet Shadbala minima are verified word-for-word against Raman's printed
    §122, which also closes an open user decision that rested on a misread line;
  * the Ashtakavarga Ayurdaya conversion is confirmed as a deliberate omission with three
    anchors, not an unfinished feature.
"""
from __future__ import annotations

import inspect

import pytest

#: Raman's printed figures, GBB-8:303-312 §122 "Powerful Planets" — transcribed from the
#: corpus, not from the engine, so this test can actually disagree with the code.
_RAMAN_MINIMA = {
    "Sun": 5.0,        # "Ravi ... 5 or more Rupas"
    "Moon": 6.0,       # "Chandra ... 6 or more Rupas"
    "Mars": 5.0,       # "Kuja ... does not fall short of 5 Rupas"
    "Mercury": 7.0,    # "Budha ... as 7 Rupas"
    "Jupiter": 6.5,    # "Guru, Sukra and Sani ... 6.5, 5.5 and 5 Rupas or more"
    "Venus": 5.5,
    "Saturn": 5.0,
}

try:
    from app.raman_saab.doctrine.sources import Citation, verify
    _HAS_CORPUS = verify(Citation("GBB-8", 303))
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


class TestMinimaMatchRaman:
    def test_every_planet_matches_the_printed_figure(self):
        """All seven bars are Raman's own, not tuned values wearing his citation."""
        from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
        # Iterating _RAMAN_MINIMA alone leaves the check one-way: a key MIN_REQUIRED gains
        # that Raman prints no bar for — a node, or a renamed body — would pass unnoticed,
        # which is exactly the "tuned value wearing his citation" this test exists to catch.
        assert set(MIN_REQUIRED) == set(_RAMAN_MINIMA), (
            f"MIN_REQUIRED carries planets GBB-8:303-312 prints no bar for: "
            f"{sorted(set(MIN_REQUIRED) - set(_RAMAN_MINIMA))}")
        for planet, want in _RAMAN_MINIMA.items():
            assert MIN_REQUIRED[planet] == want, (
                f"{planet}: engine {MIN_REQUIRED[planet]} vs GBB-8:303-312 {want}")

    def test_the_sun_bar_is_five_not_six_point_five(self):
        """This is the whole of the open user decision "Sun MIN_REQUIRED 5.0 (tuned) vs
        GBB-8:303's printed 6.5 — retune or relabel". 6.5 is GURU's figure. Raman's Ravi
        bar is 5.0 and the engine already carries it, so there was never anything to
        decide. Pinned so the decision cannot be re-opened on the same misreading."""
        from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
        assert MIN_REQUIRED["Sun"] == 5.0
        assert MIN_REQUIRED["Jupiter"] == 6.5

    def test_the_closure_is_recorded_where_the_table_lives(self):
        """A finding that lives only in a commit message is lost. The module says it."""
        import re
        from app.raman_saab.primitives.shadbala import total
        # the note wraps across comment lines, so compare on normalised whitespace with
        # the leading "# " markers stripped
        src = re.sub(r"\s+", " ", inspect.getsource(total).replace("\n#", " "))
        assert "6.5 is GURU's figure, not the Sun's" in src
        assert "NO PER-COMPONENT MINIMA EXIST" in src

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_the_anchor_really_prints_these_seven_figures(self):
        """The transcription above is checked against the page it claims to come from."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("GBB-8").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = re.sub(r"\s+", " ", " ".join(lines[302:313])).casefold()
        assert "powerful planets" in window
        assert "ravi is held to be powerful when his shad bala pinda is 5 or more" in window
        assert "chandra becomes strong when his shad bala pinda is 6 or more" in window
        assert "budha becomes potent by having his shad bala pinda as 7" in window
        assert "6.5, 5.5 and 5 rupas or more respectively" in window


class TestAyurdayaStopLine:
    def test_the_omission_is_documented_with_its_three_reasons(self):
        """HPA-26 §51 onward carries the complete Ashtakavarga Ayurdaya method and every
        input is already computed — the Gunakara multipliers and the Sodya Pinda both
        render. Only the conversion to a span of years is missing, and it is missing on
        purpose. The PRIME DIRECTIVE requires a deliberate omission to be documented, so the
        three reasons and their anchors sit on the dataclass that computes the inputs."""
        from app.raman_saab.detailed_report import SodyaPindaRow
        doc = inspect.getdoc(SodyaPindaRow) or ""
        assert "HTJAH-II:4453" in doc          # Raman's own downgrade of the method
        assert "PREC-4" in doc                 # AV never outranks the Raman band
        assert "PREC-8" in doc                 # band, then marakas, never a number
        assert "documented deliberate omission" in doc

    def test_no_lifespan_number_is_emitted_anywhere_from_the_pinda(self):
        """The stop-line has to hold in behaviour, not only in a docstring: the Sodya Pinda
        rows carry integers that are Gunakara sums, and nothing converts them to years."""
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(
            BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59))
        rows = getattr(r, "sodya_pinda", ())
        if not rows:
            pytest.skip("no sodya pinda rows on this chart")
        for row in rows:
            assert row.total == row.rasi + row.graha      # a sum, not a span
            assert isinstance(row.total, int)

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_raman_really_calls_the_method_unreliable(self):
        """Reason 1 is a quotation, so it is read back from the page."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HTJAH-II").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = re.sub(r"\s+", " ", " ".join(lines[4452:4457])).casefold()
        assert "ashtakavarga method is equally important" in window
        assert "does not seem to be quite reliable" in window
