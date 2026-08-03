"""The firewall-lift scope rules for the horary package: walls + citation resolution."""
from __future__ import annotations

import inspect

from app.raman_saab.doctrine.sources import verify
from app.raman_saab.horary import CITED_ANCHORS


class TestWalledSubsystem:
    def test_natal_verdict_path_never_imports_horary(self):
        from app.raman_saab import detailed_report, proforma, synthesis
        from app.raman_saab.judges import house_judge, house_template

        for mod in (house_template, house_judge, proforma, synthesis, detailed_report):
            assert "horary" not in inspect.getsource(mod), mod.__name__

    def test_horary_never_imports_the_judges(self):
        from app.raman_saab.horary import prasna_judge, sahams, tajika_aspects
        for mod in (tajika_aspects, sahams, prasna_judge):
            src = inspect.getsource(mod)
            assert "judges" not in src and "synthesis_rules" not in src, mod.__name__

    def test_every_cited_anchor_verifies(self):
        for cit in CITED_ANCHORS:
            assert verify(cit), f"{cit.work}:{cit.line} does not resolve"
