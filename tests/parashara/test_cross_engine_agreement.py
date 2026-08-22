"""Cross-engine agreement — where BPHS and Raman corroborate, and where they consciously differ.

The two engines follow the same tradition (Raman IS Parashari), so on shared doctrine their
agreement is real corroboration: two independently-sourced encodings reaching the same answer is
stronger evidence than either alone. Their *divergences* are the interesting product surface — they
mark where Raman deliberately revised or simplified Parashara.

This test lives in `tests/` (not an engine module), so it may import both engines to compare them —
that is its whole purpose, and the `app/`-scoped isolation guard is unaffected.

The rule for this file: **agreement is asserted; divergence is documented and attributed, never
silently averaged.** A divergence that is a known doctrinal difference is pinned as such, so if
either engine later changes, the test says which and why.
"""
from __future__ import annotations

from app.parashara.primitives import functional_nature as p_fn
from app.raman_saab.primitives import functional_nature as r_fn

#: Grahas whose natural nature is UNCONDITIONAL in both engines — both trace to BPHS ch.3 sl.11.
_FIXED = ("Sun", "Mars", "Saturn", "Rahu", "Ketu", "Jupiter", "Venus")


class TestAgreementOnFixedNature:
    def test_the_five_fixed_malefics_agree(self):
        """Sun, Mars, Saturn, Rahu, Ketu are malefic in BOTH engines — corroboration on the part of
        BPHS ch.3 Raman did not revise."""
        for g in ("Sun", "Mars", "Saturn", "Rahu", "Ketu"):
            assert p_fn.natural_benefic(g) is False
            assert g in r_fn.NATURAL_MALEFICS

    def test_the_two_fixed_benefics_agree(self):
        """Jupiter and Venus are benefic in both — the uncontested core."""
        for g in ("Jupiter", "Venus"):
            assert p_fn.natural_benefic(g) is True
            assert g in r_fn.NATURAL_BENEFICS

    def test_no_fixed_graha_disagrees(self):
        """Belt-and-braces over the whole fixed set, so a future edit to either engine that breaks
        this corroboration is caught."""
        for g in _FIXED:
            parashara_benefic = p_fn.natural_benefic(g)
            raman_benefic = g in r_fn.NATURAL_BENEFICS
            assert parashara_benefic == raman_benefic, g


class TestDocumentedDivergences:
    """Mercury and Moon differ BY DOCTRINE, not by accident. Pinned so the difference stays visible
    and any future change to either engine surfaces here with its reason."""

    def test_mercury_is_conditional_in_bphs_but_fixed_benefic_in_raman(self):
        """BPHS-3:187 — Mercury 'is a malefic if he joins a malefic'; benefic otherwise. Raman's
        avastha set treats him as an UNCONDITIONAL natural benefic (a deliberate simplification)."""
        # Parashara: depends on company.
        assert p_fn.natural_benefic("Mercury") is True                       # alone -> benefic
        assert p_fn.natural_benefic("Mercury", companions=["Saturn"]) is False  # with a malefic
        # Raman: unconditional benefic.
        assert "Mercury" in r_fn.NATURAL_BENEFICS

    def test_moon_is_conditional_in_bphs_but_fixed_benefic_in_raman(self):
        """BPHS-3:187 — the waning Moon is a malefic; the waxing Moon a benefic. Raman's avastha set
        treats the Moon as an unconditional natural benefic."""
        assert p_fn.natural_benefic("Moon", moon_waxing=True) is True
        assert p_fn.natural_benefic("Moon", moon_waxing=False) is False      # waning -> malefic
        assert "Moon" in r_fn.NATURAL_BENEFICS

    def test_the_divergence_set_is_exactly_mercury_and_moon(self):
        """The two engines' natural-benefic sets differ on EXACTLY the two conditional grahas — no
        more, no fewer. If a third graha ever diverges, it is unexplained and this fails."""
        # Raman's unconditional benefics minus the two BPHS also holds unconditionally benefic.
        raman_only = set(r_fn.NATURAL_BENEFICS) - p_fn.FIXED_BENEFICS
        assert raman_only == {"Mercury", "Moon"}
