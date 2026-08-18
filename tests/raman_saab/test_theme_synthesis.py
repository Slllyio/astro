"""QC harness for the integrated-interpretation (theme-synthesis) layer.

These are the item-22 quality-control checks from the architecture spec
(docs/raman_saab/SYNTHESIS_LAYER_ARCHITECTURE.md §K), turned into assertions. The load-
bearing invariant is that the layer SYNTHESIZES the authoritative verdicts and judges
nothing anew — proved by (a) headline verdicts byte-equalling their source rollups, (b) no
non-verdict axis carrying a direction, and (c) the golden ratchet staying byte-identical
(that last is enforced by tests/raman_saab/test_goldens.py; here we assert the layer never
imports into the verdict path and never fabricates evidence)."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab import theme_synthesis as thm
from app.raman_saab.theme_synthesis import build_theme_synthesis

_MAINPURI = BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)
_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_BANGALORE_EVENING = BirthData("BLR-eve", 1988, 3, 21, 18, 30, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def mainpuri():
    r = build_detailed_report(_MAINPURI)
    return r, build_theme_synthesis(r)


@pytest.fixture(scope="module")
def canonical():
    r = build_detailed_report(_CANONICAL)
    return r, build_theme_synthesis(r)


class TestThemeSynthesisContract:
    """The 13 QC checks from the architecture spec."""

    def test_produces_ranked_themes_and_a_spine(self, mainpuri):
        """The layer discovers several life-themes and names a 3-7 dominant spine."""
        r, ts = mainpuri
        assert len(ts.themes) >= 4
        assert 3 <= len(ts.spine) <= 7
        # spine ids are real theme ids, ranked (weight non-increasing)
        ids = {t.theme_id for t in ts.themes}
        assert set(ts.spine) <= ids
        weights = [t.evidence_weight for t in ts.themes]
        assert weights == sorted(weights, reverse=True)

    def test_headline_verdict_is_a_passthrough(self, mainpuri, canonical):
        """K2 — every theme's headline byte-equals its primary house rollup; NO re-judgment."""
        from app.raman_saab.detailed_report import _MATTER_HOUSE
        for r, ts in (mainpuri, canonical):
            proformas = {pf.house: pf for pf in r.proformas}
            for t in ts.themes:
                prim = t.houses[0]
                assert t.headline_verdict == proformas[prim].rollup, (
                    f"{t.theme_id}: headline {t.headline_verdict!r} != rollup "
                    f"{proformas[prim].rollup!r} — the layer must not re-judge")

    def test_only_verdict_axis_carries_direction(self, mainpuri, canonical):
        """K3 — magnitude/state/dasha/transit/citation links never assert favourable/adverse
        as if they were a verdict; their lean is corroboration only, and the direction of the
        theme comes solely from the passthrough headline."""
        for r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for lk in t.links:
                    if lk.axis in ("magnitude", "state", "dasha", "transit"):
                        assert lk.lean in ("neutral", "mixed"), (
                            f"{t.theme_id}: a {lk.axis} link carries direction {lk.lean!r} — "
                            f"a support metric must never become a second direction axis")

    def test_every_link_is_traceable(self, mainpuri):
        """K1 — every evidence link names the accessor it came from (auditability)."""
        r, ts = mainpuri
        for t in ts.themes:
            assert t.links, f"{t.theme_id} has no supporting evidence"     # K5
            for lk in t.links:
                assert lk.accessor and "@" in lk.accessor, (
                    f"{t.theme_id}: link {lk.label!r} has no file:line accessor")
                assert lk.provenance in (thm.RAMAN_EXPLICIT, thm.RAMAN_GENERAL,
                                         thm.CLASSICAL_NONCITABLE, thm.STATISTICAL,
                                         thm.MODERN_SYNTHESIS)

    def test_no_statistical_link_in_a_doctrine_claim(self, mainpuri, canonical):
        """K4 — population/statistical material is never stamped as a Raman/verdict link."""
        for r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for lk in t.links:
                    if lk.provenance == thm.STATISTICAL:
                        assert lk.axis not in ("verdict", "varga"), (
                            "a statistical finding must not masquerade as a doctrine verdict")

    def test_the_layer_authors_no_citation(self, mainpuri, canonical):
        """K11 — the layer never mints a WORK:line; a cite is only ever an object it inherited
        from the source finding (never a string it composed)."""
        for r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for lk in t.links:
                    if lk.cite is not None:
                        # a real Citation object carries .work/.line — never a bare authored string
                        assert hasattr(lk.cite, "work") or hasattr(lk.cite, "line") or \
                            not isinstance(lk.cite, str)

    def test_contradictions_cite_a_governing_rule(self, mainpuri, canonical):
        """K6 — every contradiction is classified and resolved by an existing precedence id."""
        seen = 0
        for r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for c in t.contradictions:
                    seen += 1
                    assert c.governing, f"{t.theme_id} contradiction has no governing rule"
                    assert c.kind and c.resolution
                    assert len(c.poles) == 2 and all(c.poles)
        assert seen >= 1, "the contradiction engine never fired across two real charts"

    def test_convergence_reports_both_poles(self, mainpuri, canonical):
        """K — convergence is evidentiary and always states agreement AND opposition (never a
        cherry-picked single pole; the median chart carries both at all times)."""
        for r, ts in (mainpuri, canonical):
            for t in ts.themes:
                assert t.convergence in ("VERY_HIGH", "HIGH", "MODERATE", "MIXED", "WEAK")
                assert "agree" in t.convergence_why and "oppose" in t.convergence_why
                assert "probability" in t.convergence_why  # explicitly says it is NOT one

    def test_three_axes_stay_separate(self, mainpuri):
        """K/item-7 — direction, magnitude and state are distinct axes, not one collapsed score.
        A well-evidenced theme carries at least a verdict axis plus a magnitude or state axis."""
        r, ts = mainpuri
        rich = [t for t in ts.themes if len(t.links) >= 6]
        assert rich, "expected at least one richly-evidenced theme on Mainpuri"
        for t in rich:
            axes = {lk.axis for lk in t.links}
            assert "verdict" in axes
            assert axes & {"magnitude", "state"}, f"{t.theme_id} collapses the strength axes"

    def test_dasha_and_transit_are_engine_sourced(self, mainpuri):
        """K7/K9/K10 — dasha links come from the tier grader, transit links only from the
        subordinated dasha-x-transit confluence (never an independent transit prediction)."""
        r, ts = mainpuri
        for t in ts.themes:
            for lk in t.links:
                if lk.axis == "dasha":
                    assert "house_current_tiers" in lk.accessor or "period" in lk.accessor.lower()
                if lk.axis == "transit":
                    assert "dasha_transit" in lk.accessor

    def test_prose_passes_the_decree_guard(self, mainpuri, canonical):
        """K10 — no theme prose trips the decree tripwire (_FORBIDDEN_RE); timed indications in
        the classical idiom are allowed, the decree voice is refused."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for r, ts in (mainpuri, canonical):
            blobs = [ts.portrait.principal_tension, ts.portrait.temperament, ts.portrait.next_chapter]
            for t in ts.themes:
                blobs.append(t.final_interpretation)
                blobs.append(t.convergence_why)
                blobs.extend(c.resolution for c in t.contradictions)
            for b in blobs:
                m = _FORBIDDEN_RE.search(b or "")
                assert m is None, f"decree-guard hit: {m.group(0)!r} in {b!r}"

    def test_portrait_is_populated_and_honest(self, mainpuri):
        """The Executive Portrait re-reads real report state and carries the honesty frame."""
        r, ts = mainpuri
        p = ts.portrait
        assert p.dominant_actors                      # census-dominant grahas
        assert p.current_chapter                      # running MD/AD
        # dominant actors agree with the census-ranked biographies (planet_bios[0] is dominant)
        if r.planet_bios:
            assert p.dominant_actors[0][0] == r.planet_bios[0].planet

    def test_layer_never_imports_into_the_verdict_path(self):
        """K13 — theme_synthesis is on the overlay side: the D1 verdict modules must not import
        it (that is what keeps the golden ratchet byte-identical)."""
        import ast
        import pathlib
        verdict_path = [
            "app/raman_saab/judges/house_template.py",
            "app/raman_saab/proforma.py",
            "app/raman_saab/judges/rule_firing.py",
        ]
        for rel in verdict_path:
            src = pathlib.Path(rel).read_text(encoding="utf-8")
            assert "theme_synthesis" not in src, (
                f"{rel} imports theme_synthesis — the overlay must never enter the verdict path")
