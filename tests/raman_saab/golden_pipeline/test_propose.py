from __future__ import annotations

from tools.raman_saab.golden_pipeline import propose as PR

DECS = [
    {"item_id": "X#H4", "record_id": "X", "house": 4, "outcome": "CONFIRMED",
     "verdict": "afflicted", "signification": "mother", "revised": False,
     "quotes": {"A": ["lost his mother early", 6]}},
    {"item_id": "Y#H5", "record_id": "Y", "house": 5, "outcome": "REJECTED", "quotes": {}},
]


class TestProposal:
    def test_projection_reports_both_axes_side_by_side(self):
        """Exact and within-1 are reported separately, never averaged."""
        md = PR.render(DECS, engine=lambda d: "favourable", current=((286, 397), (362, 397)))
        assert "287/398" not in md          # engine disagrees -> exact numerator unchanged
        assert "286/398" in md              # exact: total +1
        assert "362/398" in md              # within-1: afflicted vs favourable is distance 2

    def test_every_decision_listed_with_quote(self):
        """The reviewer's evidence is shown for each row the user signs."""
        md = PR.render(DECS, engine=lambda d: "afflicted", current=((286, 397), (362, 397)))
        assert "X#H4" in md and "lost his mother early" in md and "Y#H5" in md
