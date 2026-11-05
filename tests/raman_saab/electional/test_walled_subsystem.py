"""The firewall-lift scope rule (DOCTRINE_BACKLOG 2026-08-03): the electional package is a
WALLED subsystem — natal verdict code must never import it."""
from __future__ import annotations

import inspect


class TestWalledSubsystem:
    def test_natal_verdict_path_never_imports_electional(self):
        """Extends the VERDICT-AUTHORITY invariant: the ratchet is untouchable by anything
        this subsystem computes."""
        from app.raman_saab import detailed_report, proforma, synthesis
        from app.raman_saab.judges import house_judge, house_template

        for mod in (house_template, house_judge, proforma, synthesis, detailed_report):
            assert "electional" not in inspect.getsource(mod), mod.__name__

    def test_electional_never_imports_the_judges(self):
        """The wall holds in the other doctrinally-relevant direction too: election verdicts
        come from MUHURTHA/ASP-15 rules, never from the natal judges' house verdicts."""
        from app.raman_saab.electional import (asp_transit_elections, day_scanner,
                                               negative_windows, panchanga_suitability,
                                               tarabala, window_scorer)
        for mod in (tarabala, negative_windows, panchanga_suitability,
                    asp_transit_elections, window_scorer, day_scanner):
            src = inspect.getsource(mod)
            assert "judges" not in src and "synthesis_rules" not in src, mod.__name__
