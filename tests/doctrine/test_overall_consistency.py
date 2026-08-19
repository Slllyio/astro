"""Track 2 drift-guard: pin the synthesize_house consistency spot-measurement + the low-yield fact.

Raman's OVERALL house verdicts are narrative and don't map to the 9-grade scale (3/168), so the
fusion is measured against the central tendency of his crisp factor verdicts instead. N is small
(6 all-3-factor charts, 14 with >=2) — floors, not exact pins.
"""
from __future__ import annotations

from app.medini.doctrine.validation import overall_consistency as OC


def test_synthesize_house_fusion_is_consistent_with_raman_factor_central_tendency():
    rows = OC.run()["rows"]
    all3 = [r for r in rows if r["n_factors"] >= 3]
    two = [r for r in rows if r["n_factors"] >= 2]
    assert len(all3) == 6 and len(two) == 14, (len(all3), len(two))

    def within1(sel, key):
        return sum(1 for r in sel if abs(r[key]) <= 1)

    # the fusion FORMULA applied to Raman's own grades stays near their central tendency (sane):
    assert within1(two, "d_fusion") >= 11, within1(two, "d_fusion")
    # end-to-end (engine factors → fusion) tracks Raman's central tendency in line with per-factor
    # accuracy — the fusion does not degrade the signal:
    assert within1(two, "d_end2end") >= 6, within1(two, "d_end2end")
