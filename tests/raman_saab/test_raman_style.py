"""The Raman Style Writer helpers — shapes + guard safety."""
from __future__ import annotations

from app.raman_saab.raman_style import because, conclusion, governed_list, weighed


class TestRamanStyle:
    def test_because_puts_the_cause_first(self):
        s = because("the lord reaches house 2", "the wealth readings carry its mark")
        assert s.startswith("Because the lord reaches house 2, ")
        assert s.endswith(".")

    def test_weighed_names_the_evidence_before_the_verdict(self):
        s = weighed("seven favourable witnesses against one",
                    "the favourable reading stands")
        assert s.index("witnesses") < s.index("stands")

    def test_governed_list_never_leaves_an_enumeration_bare(self):
        s = governed_list(("Sun", "Mars"), "Two grahas share the tier")
        assert s.startswith("Two grahas share the tier: ")

    def test_conclusion_shape(self):
        assert conclusion("the emphasis is administrative") == \
            "Conclusion: the emphasis is administrative."

    def test_every_helper_output_passes_the_guard(self):
        from app.llm.report_explainer import _FORBIDDEN_RE
        outputs = [
            because("Saturn aspects the house", "its readings run harder there"),
            weighed("the lord, the karaka and the bhava together",
                    "the reading is favourable"),
            governed_list(("house 2", "house 11"), "The gains cluster"),
            conclusion("the method's emphasis sits with Mercury"),
        ]
        for s in outputs:
            assert _FORBIDDEN_RE.search(s) is None, s
