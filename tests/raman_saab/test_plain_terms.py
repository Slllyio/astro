"""The plain-terms layer — coverage, Raman-threshold bands, guard safety."""
from __future__ import annotations

from app.raman_saab.plain_terms import (TERM_GLOSS, band_rupas, gloss_dict,
                                        plain_avastha)


class TestPlainTerms:
    def test_the_user_named_terms_all_have_four_field_entries(self):
        """Ishta, Kashta, Muditha, Deepta(=Deeptha), Deena, Shadbala, Avastha, Karaka."""
        for term in ("Ishta", "Kashta", "Muditha", "Deeptha", "Deena", "Shadbala",
                     "Avastha", "Karaka"):
            t = TERM_GLOSS[term]
            assert t.plain and t.analogy and t.why_it_matters

    def test_bands_come_from_ramans_own_thresholds(self):
        """GBB-8:303 minimums — a planet exactly at its requirement reads Strong; well
        above reads Very strong; below requirement says so."""
        from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
        req = MIN_REQUIRED["Jupiter"]
        assert band_rupas("Jupiter", req).startswith("Strong")
        assert band_rupas("Jupiter", req * 1.6).startswith("Very strong")
        assert band_rupas("Jupiter", req * 0.5).startswith("Below requirement")
        assert band_rupas("Jupiter", None) == "unmeasured on this chart"

    def test_bands_carry_the_consequence_never_a_bare_word(self):
        for v in (10.0, 7.0, 5.0, 3.0):
            band = band_rupas("Jupiter", v)
            assert "—" in band or "unmeasured" in band

    def test_plain_avastha_leads_with_the_icon_and_keeps_the_word(self):
        s = plain_avastha("Deeptha")
        assert "Deeptha" in s and "radiant" in s
        assert plain_avastha("NotAState") == "NotAState"

    def test_every_gloss_string_passes_the_guard(self):
        from app.llm.report_explainer import _FORBIDDEN_RE
        for term, t in TERM_GLOSS.items():
            for s in (t.plain, t.analogy, t.why_it_matters, t.example):
                m = _FORBIDDEN_RE.search(s)
                assert m is None, (term, m.group(0) if m else None)

    def test_gloss_dict_ships_every_entry(self):
        d = gloss_dict()
        assert set(d) == set(TERM_GLOSS)
        assert all({"plain", "analogy", "why_it_matters", "example"} <= set(v)
                   for v in d.values())

    def test_the_report_renders_the_layer(self):
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown
        from app.raman_saab.report_html import to_html
        from app.raman_saab.report_json import to_report_dict
        r = build_detailed_report(
            BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59))
        md = to_markdown(r)
        assert "think of it as horsepower" in md
        assert "### In plain terms (every technical word, with why it matters)" in md
        assert "| in plain terms |" in md
        html = to_html(r)
        assert "horsepower" in html and "aria-label=\"Shadbala strength bars\"" in html
        assert to_report_dict(r)["plain_terms"]["Shadbala"]["analogy"]