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

#: A FIXED reference date. ``build_detailed_report`` defaults ``on=None``, which makes ``ref_jd``
#: today — and the timing assertions below are all measured FORWARD from ``ref_jd``: that every
#: theme has a forward window, that at least two distinct windows exist, that H7 never reaches the
#: top tier ahead, and that a nodal chapter falls inside the shown span. Left on a moving "today"
#: each of those can flip on a date unrelated to any code change, so the suite would rot silently.
_ON = (2026, 8, 18)


@pytest.fixture(scope="module")
def mainpuri():
    r = build_detailed_report(_MAINPURI, on=_ON)
    return r, build_theme_synthesis(r)


@pytest.fixture(scope="module")
def canonical():
    r = build_detailed_report(_CANONICAL, on=_ON)
    return r, build_theme_synthesis(r)


class TestThemeSynthesisContract:
    """The 13 QC checks from the architecture spec."""

    def test_produces_ranked_themes_and_a_spine(self, mainpuri):
        """The layer discovers several life-themes and names a 3-7 dominant spine."""
        _r, ts = mainpuri
        assert len(ts.themes) >= 4
        assert 3 <= len(ts.spine) <= 5
        # spine ids are real theme ids, ranked (weight non-increasing)
        ids = {t.theme_id for t in ts.themes}
        assert set(ts.spine) <= ids
        weights = [t.evidence_weight for t in ts.themes]
        assert weights == sorted(weights, reverse=True)

    def test_headline_verdict_is_a_passthrough(self, mainpuri, canonical):
        """K2 — every theme's headline byte-equals its primary house rollup; NO re-judgment."""
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
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for lk in t.links:
                    if lk.provenance == thm.STATISTICAL:
                        assert lk.axis not in ("verdict", "varga"), (
                            "a statistical finding must not masquerade as a doctrine verdict")

    def test_the_layer_authors_no_citation(self, mainpuri, canonical):
        """K11 — the layer never mints a WORK:line; a cite is only ever an object it inherited
        from the source finding (never a string it composed)."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for lk in t.links:
                    if lk.cite is not None:
                        # a real Citation object carries .work/.line — never a bare authored string
                        assert hasattr(lk.cite, "work") or hasattr(lk.cite, "line") or \
                            not isinstance(lk.cite, str)

    def test_contradictions_cite_a_governing_rule(self, mainpuri, canonical):
        """K6 — every contradiction is classified and resolved by an existing precedence id."""
        seen = 0
        for _r, ts in (mainpuri, canonical):
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
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                assert t.convergence in ("VERY_HIGH", "HIGH", "MODERATE", "MIXED", "WEAK")
                assert "agree" in t.convergence_why and "oppose" in t.convergence_why
                assert "probability" in t.convergence_why  # explicitly says it is NOT one

    def test_three_axes_stay_separate(self, mainpuri):
        """K/item-7 — direction, magnitude and state are distinct axes, not one collapsed score.
        A well-evidenced theme carries at least a verdict axis plus a magnitude or state axis."""
        _r, ts = mainpuri
        rich = [t for t in ts.themes if len(t.links) >= 6]
        assert rich, "expected at least one richly-evidenced theme on Mainpuri"
        for t in rich:
            axes = {lk.axis for lk in t.links}
            assert "verdict" in axes
            assert axes & {"magnitude", "state"}, f"{t.theme_id} collapses the strength axes"

    def test_dasha_and_transit_are_engine_sourced(self, mainpuri):
        """K7/K9/K10 — dasha links come from the tier grader, transit links only from the
        subordinated dasha-x-transit confluence (never an independent transit prediction)."""
        _r, ts = mainpuri
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

    def test_connections_dasha_evolution_and_varga_matrix(self, mainpuri):
        """Stage-3 consolidated views: the cross-theme fabric, the time-axis evolution, and the
        varga matrix — all re-reads, all present on a rich chart."""
        _r, ts = mainpuri
        # connections: at least one pair shares a mechanism, and the shared factor is real
        assert ts.connections, "no cross-theme connection discovered on Mainpuri"
        names = {t.name for t in ts.themes}
        for c in ts.connections:
            assert c.theme_a in names and c.theme_b in names and c.shared and c.note
        # dasha evolution: chapters with year spans, emerging/continuing split, one 'now'
        assert ts.dasha_evolution
        assert sum(1 for ch in ts.dasha_evolution if ch.is_current) <= 1
        for ch in ts.dasha_evolution:
            assert "-" in ch.span                       # 'YYYY-YYYY'
            # emerging + continuing are subsets of the chapter's activated themes
            assert set(ch.emerging) | set(ch.continuing) <= set(ch.activates)
            assert not (set(ch.emerging) & set(ch.continuing))   # disjoint

    def test_dasha_spans_match_the_life_chapter_engine(self, mainpuri):
        """K7/K9 — the evolution spans are the life-chapters' own JD bounds, not new math."""
        import swisseph as swe
        r, ts = mainpuri
        chapters = {ch.maha: ch for ch in r.life_chapters.chapters}
        for de in ts.dasha_evolution:
            src = chapters.get(de.maha)
            if src is not None:
                lo = int(swe.revjul(src.start_jd, swe.GREG_CAL)[0])
                hi = int(swe.revjul(src.end_jd, swe.GREG_CAL)[0])
                assert de.span == f"{lo}-{hi}"

    def test_mainpuri_integration_proof(self, mainpuri):
        """Item-23 — the layer must DISCOVER (not be told) the chart's recurring structures.
        On Mainpuri: Jupiter/Saturn among the dominant actors, a wealth network on H2+H11, a
        career theme on H10, and the current chapter naming the running Mahadasha. These are
        asserted from the structured object, never hardcoded into the engine."""
        r, ts = mainpuri
        actors = {a[0] for a in ts.portrait.dominant_actors}
        assert {"Jupiter", "Saturn"} <= actors, f"expected Jupiter+Saturn dominant, got {actors}"
        by = {t.theme_id: t for t in ts.themes}
        wealth = by.get("wealth")
        assert wealth and 2 in wealth.houses and 11 in wealth.houses, \
            "the wealth theme did not discover the H2/H11 network"
        career = by.get("career")
        assert career and 10 in career.houses
        # the current chapter names the running MD (from the report's own running_md)
        assert r.synthesis.running_md and r.synthesis.running_md in ts.portrait.current_chapter

    def test_generic_across_charts(self, mainpuri, canonical):
        """The architecture is generic, not tuned to one chart: both charts yield themes, a
        spine, a portrait with actors, and at least one contradiction somewhere."""
        for _r, ts in (mainpuri, canonical):
            assert ts.themes and ts.spine and ts.portrait.dominant_actors
            assert any(t.contradictions for t in ts.themes) or ts.portrait.principal_tension

    def test_section_facts_are_grounded_and_guard_clean(self, mainpuri):
        """Stage-5 prose pipeline — the themes section decomposes one-claim-per-Fact and every
        Fact passes the decree guard (so /report/explain can narrate it grounded)."""
        from app.raman_saab.report_json import to_report_dict
        from app.llm.report_explainer import _section_facts, _FORBIDDEN_RE
        r, _ = mainpuri
        R = to_report_dict(r)
        facts = _section_facts(R, "themes")
        assert len(facts) >= 4, "the themes section produced too few grounded facts"
        for f in facts:
            assert _FORBIDDEN_RE.search(f.text) is None, f"decree-guard hit in a themes fact: {f.text!r}"

    def test_portrait_identity_is_the_real_chart(self, mainpuri):
        """The Executive Portrait names WHO the chart is — Lagna/lord, Atmakaraka+Karakamsa and
        the Moon's nakshatra — re-read from the synthesis, and it passes the decree guard."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        r, ts = mainpuri
        idn = ts.portrait.identity
        assert idn, "the portrait carries no identity line"
        assert r.synthesis.lagna in idn and r.synthesis.atmakaraka in idn
        assert _FORBIDDEN_RE.search(idn) is None

    def test_principal_tension_names_a_real_structural_pull(self, mainpuri):
        """The principal tension is the chart's own favourable-vs-strained pull (or the single
        most load-bearing contradiction), never a bare method note about the layer itself."""
        _r, ts = mainpuri
        pt = ts.portrait.principal_tension
        assert pt and "contradiction is flagged" not in pt   # the old placeholder is gone

    def test_theme_facets_carry_each_matters_own_verdict(self, mainpuri):
        """A house theme exposes its facets (the dashboard matters that live in it), each with
        its own dedicated-reader verdict — this is where a house-vs-matter grain split is told
        ONCE, inside the theme (e.g. H4 mother favourable while property afflicted)."""
        _r, ts = mainpuri
        by = {t.theme_id: t for t in ts.themes}
        foundations = by.get("foundations")
        assert foundations is not None, "the house-based foundations theme did not build"
        assert foundations.sub_matters, "foundations exposes no facets"
        matters = {m for m, _v in foundations.sub_matters}
        assert "mother" in matters and "property" in matters   # several matters share H4
        for _m, v in foundations.sub_matters:
            assert v, "a facet carries no verdict"

    def test_convergence_label_is_reader_facing(self, mainpuri, canonical):
        """Every theme carries a reader-facing convergence phrase distinct from the raw tier
        (e.g. 'aligned, but lightly evidenced' for a WEAK-but-unopposed theme)."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                assert t.convergence_label
                if t.convergence == "WEAK":
                    assert "convergence" not in t.convergence_label   # not the misleading 'weak convergence'

    def test_dasha_evolution_is_differential_not_flooding(self, mainpuri):
        """K/item-10 — a chapter foregrounds ONLY the themes its Mahadasha lord drives (or, for a
        node, the themes its disclosed agents drive), so a single period never lights every theme
        at once. At least one chapter must foreground a proper subset."""
        r, ts = mainpuri
        by = {t.name: t for t in ts.themes}
        saw_subset = False
        for ch in ts.dasha_evolution:
            keys = {ch.maha} | set(ch.acts_through)
            for name in ch.activates:
                assert keys & set(by[name].dominant_planets), (
                    f"{ch.maha} MD foregrounds {name!r} but neither it nor its agents drive it")
            if ch.activates and len(ch.activates) < len(ts.themes):
                saw_subset = True
        assert saw_subset, "no chapter foregrounded a proper subset — flooding is back"

    def test_every_theme_gets_a_forward_timing_window(self, mainpuri, canonical):
        """The WHEN axis must not be silent: each theme names the bhukti ahead that best supports
        its bhava, graded on Raman's four-tier fructification scheme (HTJAH-I:1592-1596)."""
        from app.raman_saab.theme_synthesis import _TIER_ORDER
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                assert t.activation_span, f"{t.theme_id} carries no timing window"
                assert "bhukti" in t.activation_span
                assert any(tier in t.activation_span for tier in _TIER_ORDER), (
                    f"{t.theme_id} timing names no fructification grade")

    def test_timing_windows_are_forward_looking_and_differential(self, mainpuri):
        """The window is drawn from bhuktis AHEAD of the reference moment (not a historical
        high-water mark), and the themes do not all collapse onto one identical window."""
        import re
        r, ts = mainpuri
        ref_year = int(__import__("swisseph").revjul(r.ref_jd, __import__("swisseph").GREG_CAL)[0])
        windows = set()
        for t in ts.themes:
            m = re.search(r"\((\d{4})-(\d{4})\)", t.activation_span)
            assert m, f"{t.theme_id}: no year span in {t.activation_span!r}"
            assert int(m.group(2)) >= ref_year, "a timing window closed before the present"
            windows.add(m.group(0))
        assert len(windows) >= 2, "every theme collapsed onto one window — not differential"

    def test_timing_discloses_a_theme_never_reaching_the_top_tier(self, mainpuri):
        """A bhava the coming years support only weakly says so — that is a finding, not an
        absence to hide. On Mainpuri, H7 (marriage) never reaches par excellence ahead."""
        _r, ts = mainpuri
        marriage = next((t for t in ts.themes if t.theme_id == "marriage"), None)
        assert marriage is not None
        assert "not carried to the top tier" in marriage.activation_span

    def test_a_nodal_chapter_routes_through_its_agents(self, mainpuri):
        """Rahu/Ketu own no sign and can never be a theme's driver, so without routing every
        nodal Mahadasha would foreground nothing (a quarter of the 120-year cycle). A node
        chapter must name the planets it acts for, and they must be real chart agents."""
        from app.raman_saab.theme_synthesis import _node_agents
        r, ts = mainpuri
        agents = _node_agents(r)
        assert agents, "no node agency computed"
        nodal = [c for c in ts.dasha_evolution if c.maha in ("Rahu", "Ketu")]
        for c in nodal:
            assert c.acts_through, f"{c.maha} chapter discloses no routing"
            assert set(c.acts_through) == set(agents[c.maha])
            # anything it foregrounds is driven by one of those agents, never by the node itself
            by = {t.name: t for t in ts.themes}
            for name in c.activates:
                assert set(c.acts_through) & set(by[name].dominant_planets)

    def test_node_agents_are_dispositor_and_co_tenants(self, mainpuri):
        """The routing is the classical one: the lord of the sign the node occupies, plus any
        planet joined with it (conjunction = sign membership, the project's locked convention)."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.theme_synthesis import _node_agents
        r, _ts = mainpuri
        for node, agents in _node_agents(r).items():
            p = r.chart.planets[node]
            assert SIGN_LORDS[p.sign] in agents, f"{node}'s dispositor is missing"
            for other, op in r.chart.planets.items():
                if other not in ("Rahu", "Ketu") and op.sign == p.sign:
                    assert other in agents, f"{other} shares {node}'s sign but is not an agent"

    def test_every_bhava_is_a_theme_in_its_own_right(self, mainpuri, canonical):
        """REPORT COMPLETENESS — all twelve bhavas carry a theme. H1 (the self), H8 (longevity
        and crisis) and H12 (loss and withdrawal) used to appear only as SUPPORT houses inside
        other themes, so the reading never stated what the chart says about them directly."""
        for _r, ts in (mainpuri, canonical):
            primaries = {t.houses[0] for t in ts.themes}
            assert primaries == set(range(1, 13)), (
                f"bhavas with no theme of their own: {sorted(set(range(1, 13)) - primaries)}")

    def test_a_bhava_without_a_classical_division_says_so(self, mainpuri):
        """No silent approximation — H8 and H12 have no varga assigned to them in the domain
        table, so their themes must carry NO karakas and NO citation borrowed from some other
        division, and must disclose that they are read from the rasi."""
        _r, ts = mainpuri
        for tid in ("gains", "longevity", "liberation"):
            t = next(x for x in ts.themes if x.theme_id == tid)
            assert not t.karakas, f"{tid} borrowed karakas from a division it was not assigned"
            assert "no classical division" in t.domain
            for lk in t.links:
                assert lk.cite is None or lk.axis != "varga", (
                    f"{tid} carries a divisional citation for a bhava with no division")

    def test_the_self_theme_uses_the_rasi_domain(self, mainpuri):
        """H1 DOES have an explicit division — D1 Rasi, 'the body and the whole horoscope' —
        so the self theme carries that domain and its karaka rather than a plain description."""
        _r, ts = mainpuri
        self_t = next(x for x in ts.themes if x.theme_id == "self")
        assert "body" in self_t.domain and self_t.karakas

    def test_narrative_and_heading_agree_on_convergence(self, mainpuri, canonical):
        """The sentence and the heading must never disagree — both use convergence_label."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                if t.convergence not in ("VERY_HIGH", "HIGH") and not t.contradictions:
                    assert t.convergence_label in t.final_interpretation, (
                        f"{t.theme_id}: narrative disagrees with the heading label")

    def test_the_spine_is_a_genuine_minority_cut_at_a_real_break(self, mainpuri, canonical):
        """A spine that names most of the roster names nothing. It must stay a clear minority of
        the themes, and the cut must land on an actual drop in the ranking — not on a constant
        ceiling (the old rule returned its maximum of 7 on every chart measured)."""
        for _r, ts in (mainpuri, canonical):
            assert len(ts.spine) < len(ts.themes) / 2, "the spine is not a minority"
            ranked = list(ts.themes)
            cut = len(ts.spine)
            if cut < len(ranked):
                drop = ranked[cut - 1].evidence_weight - ranked[cut].evidence_weight
                inside = [ranked[i - 1].evidence_weight - ranked[i].evidence_weight
                          for i in range(3, cut)]
                assert all(drop >= g for g in inside), (
                    "the spine was cut somewhere other than the largest available break")

    def test_evidence_weight_terms_all_discriminate(self, mainpuri):
        """Ranking inputs must carry information. The weight must actually separate the themes
        (a near-constant term dressed up as a signal is what made the old spine degenerate)."""
        _r, ts = mainpuri
        weights = [t.evidence_weight for t in ts.themes]
        assert len(set(round(w, 2) for w in weights)) >= len(weights) // 2, (
            "evidence weights are too clustered to rank on")
        assert max(weights) - min(weights) >= 1.0, "weights carry almost no spread"

    def test_theme_names_cannot_hijack_a_pinned_section_marker(self):
        """A theme renders as ``#### <name>``, whose text CONTAINS ``## <name>``. So a theme
        named for a pinned section label silently hijacks every ``find("## <label>")`` and
        ``_section(md, "## <label>")`` lookup in the report suite — the theme heading appears
        earlier in the document than the real section and wins the search. "Longevity, crisis &
        the hidden" did exactly this to the real "## Longevity" section, breaking four tests in
        two files. Names must not collide in either direction."""
        from app.raman_saab.detailed_report import SECTION_CONTRACT
        from app.raman_saab.theme_synthesis import _THEME_ROSTER
        labels = [s.md_marker[3:] for s in SECTION_CONTRACT
                  if (s.md_marker or "").startswith("## ")]
        assert labels, "no pinned markers found — the guard would be vacuous"
        for spec in _THEME_ROSTER:
            for lab in labels:
                assert not spec.name.startswith(lab) and not lab.startswith(spec.name), (
                    f"theme {spec.theme_id!r} named {spec.name!r} collides with the pinned "
                    f"section marker '## {lab}' — rename the theme")

    def test_the_transit_axis_actually_fires(self, mainpuri):
        """Regression: ``ConfluenceWindow`` carries ``planet``/``role``/JD bounds and has NO
        ``houses`` or ``label`` field, so probing for those matched nothing and the transit axis
        emitted ZERO links on every chart while looking implemented. Confluences are matched by
        planet, and each planet+role appears at most once (r.dasha_transit holds a row per
        bhukti-and-segment overlap, so one period lord otherwise repeats identically)."""
        r, ts = mainpuri
        assert r.dasha_transit, "fixture carries no confluence rows to match against"
        links = [lk for t in ts.themes for lk in t.links if lk.axis == "transit"]
        assert links, "the transit axis emitted nothing despite available confluence rows"
        for t in ts.themes:
            vals = [lk.value for lk in t.links if lk.axis == "transit"]
            assert len(vals) == len(set(vals)), f"{t.theme_id} repeats an identical transit row"
        planets = {getattr(c, "planet", None) for c in r.dasha_transit}
        for lk in links:
            assert any(p and lk.value.startswith(p) for p in planets), (
                f"transit link {lk.value!r} names no planet from r.dasha_transit")

    def test_a_mixed_headline_is_reported_as_undecided(self, mainpuri):
        """Regression: a non-directional ('mixed') rollup gives the counting loop nothing to
        compare, so it fell through to WEAK and printed 'aligned, but lightly evidenced' beside
        '0 of 0 independent axes agree' — claiming an alignment that was never tested."""
        r, ts = mainpuri
        mixed = [t for t in ts.themes if t.headline_verdict == "mixed"]
        assert mixed, "no mixed-headline theme on this fixture to exercise the branch"
        for t in mixed:
            assert t.convergence == "MIXED"
            assert "aligned" not in t.convergence_label
            assert "undecided" in t.convergence_label
            assert "agree" in t.convergence_why and "oppose" in t.convergence_why

    def test_markdown_table_cells_escape_pipes(self):
        """A literal '|' in an interpolated cell splits the row and shifts every later cell, and
        these cells carry free prose (an insight's detail, a yoga name)."""
        from app.raman_saab.detailed_report import _md_cell
        assert _md_cell("a|b") == "a\\|b"
        assert _md_cell("plain") == "plain"

    def test_contradiction_parties_are_data_not_parsed_prose(self, mainpuri, canonical):
        """The narrative names the differing facets from ``Contradiction.parties``; recovering
        them by slicing the pole prose breaks silently when the wording changes."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for c in t.contradictions:
                    if c.governing == "PREC-1":
                        assert c.parties, "a PREC-1 grain tension carries no structured parties"
                        for name in c.parties:
                            assert name in c.poles[1], "parties disagree with the prose pole"

    def test_bhava_concordance_consumes_the_engines_own_ledger(self, mainpuri, canonical):
        """INTEGRATION, not reimplementation. ``r.preponderance`` already encodes Raman's
        three-fold method — a matter judged from the BHAVA, its LORD and its KARAKA (core), with
        Bhava Bala / SAV / matter-varga / yogas as overlay — and grades each house corroborated or
        contested. The layer must re-read that ledger verbatim, never recompute a rival one."""
        for r, ts in (mainpuri, canonical):
            rows = {h.house: h for h in r.preponderance.houses}
            for t in ts.themes:
                c = t.concordance
                assert c is not None, f"{t.theme_id} carries no bhava concordance"
                src = rows[t.houses[0]]
                assert c.verdict == src.verdict == t.headline_verdict
                assert c.preponderance == src.preponderance
                assert c.status == src.status
                names = {x.name for x in src.testimonies}
                for entry in c.core_for + c.core_against + c.overlay_for + c.overlay_against:
                    assert any(entry.startswith(n) for n in names), (
                        f"{entry!r} is not a testimony the engine actually recorded")

    def test_contested_bhavas_are_the_verdict_vs_weight_divergences(self, mainpuri):
        """The interesting output: a house whose verdict runs against the weight of its own
        testimony. On Mainpuri H4/H5/H8 all read afflicted while their testimony is benefic —
        a genuinely different reading from a house where the two concur, and one the report
        never stated before. The verdict itself must be untouched."""
        r, ts = mainpuri
        contested = {c.house for c in ts.contested_bhavas}
        assert contested, "no divergence found on a chart that has three"
        rows = {h.house: h for h in r.preponderance.houses}
        for c in ts.contested_bhavas:
            src = rows[c.house]
            assert c.divergence, "a contested bhava carries no divergence sentence"
            assert (src.verdict, src.preponderance) in (
                ("afflicted", "benefic"), ("favourable", "adverse"))
            # the passthrough is intact — concordance discloses, it never re-judges
            assert c.verdict == src.verdict

    def test_graha_concordance_separates_force_from_intent(self, mainpuri, canonical):
        """Shadbala (magnitude) and Ishta/Kashta (benefic vs malefic potency) are DIFFERENT axes.
        A graha may be strong and harmful — Raman's strength-is-not-direction rule (PREC-2,
        GBB-9). Strength is graded against each planet's OWN required minimum (GBB-8:303), never
        against a cross-chart median, which would misgrade the naturally strong and weak alike."""
        from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED, is_powerful
        for r, ts in (mainpuri, canonical):
            assert ts.graha_concordance, "no graha concordance computed"
            for g in ts.graha_concordance:
                p = r.chart.planets[g.planet]
                # every number is a passthrough of the chart's own measures
                if p.shadbala_rupas is not None:
                    assert abs(g.rupas - p.shadbala_rupas.total / 60.0) < 1e-9
                assert g.ishta == p.ishta and g.kashta == p.kashta
                if g.ishta is None or g.kashta is None:      # the nodes carry neither
                    assert g.agreement == "not applicable"
                    continue
                strong = is_powerful(g.planet, g.rupas)
                benefic = g.ishta > g.kashta
                assert ("strong" in g.pattern) == strong or "harmful" in g.pattern
                if strong != benefic:
                    assert g.agreement == "split", (
                        f"{g.planet}: force and intent disagree but agreement is {g.agreement!r}")
                else:
                    assert g.agreement == "unanimous"
                assert MIN_REQUIRED.get(g.planet) is not None

    def test_concordance_note_reports_agreement_honestly(self, mainpuri):
        """The portrait owes the reader a confidence statement counted from the ledgers, not an
        impression: how many bhavas agree with themselves, which are contested, which grahas
        split force from intent."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        r, ts = mainpuri
        note = ts.portrait.concordance_note
        assert note and _FORBIDDEN_RE.search(note) is None
        for c in ts.contested_bhavas:
            assert f"H{c.house}" in note, "a contested bhava is missing from the portrait note"

    def test_each_theme_reads_its_own_division(self, mainpuri, canonical):
        """The engine casts and reads FIFTEEN vargas, each with its own verdict and citations, and
        the roster names the division that belongs to each bhava — yet the layer consulted only the
        D9 relation. A theme whose roster varga has a deep-read must now carry it, matched from the
        engine's own headline text and never recomputed."""
        for r, ts in (mainpuri, canonical):
            heads = [h for h, _b in r.divisional]
            by = {t.theme_id: t for t in ts.themes}
            for tid, varga in (("wealth", 2), ("career", 10), ("children", 7), ("siblings", 3)):
                t = by[tid]
                own = [d for d in t.divisional_checks if d.varga.startswith(f"D-{varga} ")]
                assert own, f"{tid}: its own D-{varga} deep-read was not consulted"
                assert any(own[0].varga in h for h in heads), "the label is not the engine's own"
                assert own[0].relation in ("concurs", "diverges", "reads its own matter")

    def test_a_division_reading_against_the_rasi_is_disclosed(self, mainpuri):
        """A varga is the classical confirmation device, so its dissent is the finding. On Mainpuri
        the D-30 Trimsamsa reads health FAVOURABLE while H6 reads afflicted. The rasi verdict must
        be untouched — a division modulates confidence, it never overturns (PREC-11: the D1
        Raman core decides and the varga corroborates. PREC-5 governs Laghu Parashari timing
        bands, not divisionals, and this test accepted the mis-citation as a fallback)."""
        r, ts = mainpuri
        assert ts.divisional_divergences, "the D-30/H6 divergence was not caught"
        for nm, d in ts.divisional_divergences:
            assert d.relation == "diverges"
            assert "PREC-11" in d.note
            theme = next(t for t in ts.themes if t.name == nm)
            # the passthrough is intact: disclosure only
            pf = {p.house: p for p in r.proformas}[theme.houses[0]]
            assert theme.headline_verdict == pf.rollup

    def test_divisional_checks_never_invent_a_reading(self, mainpuri, canonical):
        """Every check quotes a verdict the engine actually printed for that division."""
        for r, ts in (mainpuri, canonical):
            printed = {h for h, _b in r.divisional}
            for t in ts.themes:
                for d in t.divisional_checks:
                    assert any(h.startswith(d.varga) and d.verdict in h for h in printed), (
                        f"{d.varga}: {d.verdict!r} is not a verdict the engine printed")

    def test_distinctiveness_keeps_the_concordance_honest(self, mainpuri):
        """Techniques agreeing means little when the thing agreed on is what most charts show. The
        calibration layer already measures rarity per signification; each theme now reports it for
        its own houses, re-read verbatim (CLAUDE.md Measured Truth)."""
        r, ts = mainpuri
        src = {(h, e.signification): e for h, e in r.distinctive}
        seen = 0
        for t in ts.themes:
            for x in t.distinctive:
                seen += 1
                assert x.house in t.houses
                e = src[(x.house, x.signification)]
                assert x.rarity == e.rarity and x.population_note == e.note
                assert x.verdict == e.verdict
        assert seen, "no distinctiveness surfaced on a chart that has 22 entries"

    def test_karmic_lens_is_walled_and_never_corroborates(self, mainpuri, canonical):
        """r.soul reads poorvapunya (5th), dharma (9th) and moksha (12th) independently of the
        Parashari verdict on the same bhavas. r.karmic.frame states the wall explicitly: nothing
        in the Jaimini layer feeds or alters the natal verdicts. So the lens is recorded for the
        reader, carries the wall in its own note, and must NOT enter the evidence links or the
        convergence count — otherwise a walled layer would be quietly corroborating a verdict."""
        for r, ts in (mainpuri, canonical):
            core = r.soul.core
            seen = 0
            for t in ts.themes:
                k = t.karmic_lens
                if k is None:
                    continue
                seen += 1
                assert k.house == t.houses[0]
                # verbatim passthrough of the soul layer's own verdict
                assert k.karmic_verdict == str(getattr(core, f"{k.aspect}_verdict"))
                assert k.natal_verdict == t.headline_verdict
                assert k.relation == ("concurs" if k.karmic_verdict == k.natal_verdict
                                      else "differs")
                assert "WALLED" in k.note or "walled" in k.note
                # the wall in force: no evidence link carries the karmic reading
                for lk in t.links:
                    assert k.aspect not in lk.label.lower()
            assert seen >= 2, "the karmic lens attached to fewer bhavas than the soul layer reads"

    def test_karmic_difference_is_not_treated_as_a_contradiction(self, mainpuri):
        """A walled lens differing from the rasi is NOT a contradiction to resolve — the two
        answer different questions. It must never appear in `contradictions`, which is reserved
        for genuine precedence conflicts inside the Parashari reading."""
        _r, ts = mainpuri
        for t in ts.themes:
            k = t.karmic_lens
            if k is None or k.relation != "differs":
                continue
            for c in t.contradictions:
                assert k.aspect not in c.kind.lower()
                assert k.aspect not in c.resolution.lower()

    def test_yogas_are_read_whole_not_as_a_bare_name(self, mainpuri, canonical):
        """A yoga IS a combination — the classical integrative unit. The engine computes it across
        three fields (r.yogas fired it, r.yoga_deep carries participants/strength/cancellation/rank,
        r.yoga_timing carries the periods its participants run) and the layer had been using a
        fragment of the first. Each bearing yoga must now arrive whole, every part a passthrough."""
        for r, ts in (mainpuri, canonical):
            deep = {d.name: d for d in r.yoga_deep}
            fired = {y.name: y for y in r.yogas}
            seen = 0
            for t in ts.themes:
                for y in t.yogas:
                    seen += 1
                    assert y.name in fired, "a yoga was reported that never fired"
                    assert y.effect == fired[y.name].effect     # the promise, verbatim
                    d = deep.get(y.name)
                    if d is not None:
                        assert y.rank == d.comparison_rank
                        assert y.strength_note == (d.strength_note or "")
                        assert y.cancellation == (d.cancellation_note or "")
            assert seen, "no yoga reached any theme"

    def test_yoga_operating_windows_come_from_the_timing_engine(self, mainpuri):
        """A yoga promises; the dasha of its participants is when it delivers. Every window must
        be one r.yoga_timing actually produced for that yoga, naming that period lord."""
        r, ts = mainpuri
        by_name: dict[str, set[str]] = {}
        for tm in r.yoga_timing:
            by_name.setdefault(tm.yoga_name, set()).add(tm.planet)
        for t in ts.themes:
            for y in t.yogas:
                for w in y.windows:
                    lord = w.split()[0]
                    assert lord in by_name.get(y.name, set()), (
                        f"{y.name}: window {w!r} names a lord the timing engine never gave it")

    def test_a_cancelled_yoga_is_never_presented_as_active(self, mainpuri, canonical):
        """The bhanga note is carried VERBATIM rather than summarised away — a cancelled yoga
        presented as an active promise would be the worst kind of silent overstatement."""
        for r, ts in (mainpuri, canonical):
            deep = {d.name: d for d in r.yoga_deep}
            for t in ts.themes:
                for y in t.yogas:
                    d = deep.get(y.name)
                    if d is not None and d.cancellation_note:
                        assert y.cancellation == d.cancellation_note

    def test_each_chapter_grades_its_own_lord(self, mainpuri, canonical):
        """A period run by a strong, vargottama lord is not the same chapter as one run by a weak
        one. r.md_condition grades exactly that and was never attached to the period's narrative."""
        for r, ts in (mainpuri, canonical):
            cond = {c.maha: c for c in r.md_condition}
            graded = 0
            for ch in ts.dasha_evolution:
                mc = cond.get(ch.maha)
                if mc is None:
                    continue
                graded += 1
                assert ch.lord_condition, f"{ch.maha} chapter does not grade its own lord"
                # `==` binds tighter than `or`, so the old one-liner passed whenever the text
                # contained "not strong", whatever mc.strong said. Compare the arms explicitly.
                if mc.strong:
                    assert "strong" in ch.lord_condition
                    assert "not strong" not in ch.lord_condition
                else:
                    assert "not strong" in ch.lord_condition
                assert ("vargottama" in ch.lord_condition) == bool(mc.vargottama)
            assert graded, "no chapter matched an md_condition row"

    def test_ashtakavarga_backs_the_driver_in_the_right_sign(self, mainpuri, canonical):
        """Ashtakavarga is an independent measurement system, and the synthesis read none of it.
        The question is narrow: how many bindus does THIS theme's driving graha hold in the sign
        THIS theme's bhava occupies. BavMatrixRow.bindus is indexed by sign — verified here
        against the row's own seat_sign/seat_bindus so the indexing can never drift."""
        for r, ts in (mainpuri, canonical):
            bav = {row.planet: row for row in r.bav_matrix}
            for row in r.bav_matrix:            # the indexing contract itself
                assert row.bindus[row.seat_sign - 1] == row.seat_bindus
            seen = 0
            for t in ts.themes:
                sign = ((r.chart.asc_sign - 1 + t.houses[0] - 1) % 12) + 1
                for a in t.av_support:
                    seen += 1
                    assert a.sign == sign and a.house == t.houses[0]
                    assert a.bindus == bav[a.planet].bindus[sign - 1]
                    assert a.planet in t.dominant_planets
                    assert a.verdict in ("well supported", "about average", "poorly supported")
            assert seen, "no Ashtakavarga backing reached any theme"

    def test_a_nodal_chapter_has_no_bindu_reading(self, mainpuri):
        """Rahu and Ketu contribute no Ashtakavarga, so a nodal Mahadasha has no seat reading —
        an honest absence, never a neutral verdict dressed as data."""
        r, ts = mainpuri
        seats = {sc.maha: sc for sc in r.av_dasha_seats}
        for ch in ts.dasha_evolution:
            sc = seats.get(ch.maha)
            if sc is not None and getattr(sc, "bindus", None) is None:
                assert "no bindu reading" in ch.av_seat
                assert "adverse" not in ch.av_seat and "auspicious" not in ch.av_seat

    def test_chapter_carries_three_independent_readings(self, mainpuri):
        """A chapter now states its Ishta/Kashta lean, its lord's own condition, AND Ashtakavarga's
        seat verdict — three systems that can disagree. On Mainpuri the Saturn Mahadasha reads
        `good` by lean with a strong lord while Ashtakavarga reads the seat adverse; the point of
        the integration is that the reader sees all three, not a blended score."""
        r, ts = mainpuri
        cur = next(c for c in ts.dasha_evolution if c.is_current)
        assert cur.lean and cur.lord_condition and cur.av_seat
        seats = {sc.maha: sc for sc in r.av_dasha_seats}
        assert seats[cur.maha].read in cur.av_seat      # verbatim, not re-derived

    def test_transits_stay_subordinate(self, mainpuri, canonical):
        """Raman: transits are catalytic, all conclusions rest primarily on Dasa-vichara
        (HTJAH-II:4679-4687). A transit note reports the engine's own net_good (which already
        applies vedha) and must never become a direction the theme carries."""
        for r, ts in (mainpuri, canonical):
            rows = {(g.planet, g.house_from_moon) for g in r.gochara}
            for t in ts.themes:
                for tr in t.transits:
                    assert (tr.planet, tr.house_from_moon) in rows
                    assert "catalytic" in tr.note        # the subordination is stated every time
                    # and it never enters the direction-bearing evidence links
                    for lk in t.links:
                        if lk.axis == "transit":
                            assert lk.lean in ("neutral", "mixed")

    def test_report_survives_a_synthesis_failure(self, monkeypatch):
        """REGRESSION. build_detailed_report wraps the synthesis in try/except precisely so a
        sparse or Track-B chart degrades to the 'not available' fallback instead of taking the
        whole report down. A debug-log line added to that handler referenced a `logger` the module
        never defined — so the handler ITSELF raised NameError, converting graceful degradation
        into a crash. It only fires when synthesis raises, which no fixture chart does, so the
        suite stayed green and it shipped. This test exercises the failure path directly."""
        from app.raman_saab import detailed_report as dr
        import app.raman_saab.theme_synthesis as ths

        def _boom(_r):
            raise RuntimeError("synthesis blew up")

        monkeypatch.setattr(ths, "build_theme_synthesis", _boom)
        rep = dr.build_detailed_report(_CANONICAL, on=_ON)     # must NOT raise
        assert rep is not None
        assert rep.themes is None                              # degraded, as designed
        assert "not available" in dr.to_markdown(rep)          # and the fallback prose renders

    def test_the_reading_states_how_firm_the_cast_moment_is(self, mainpuri):
        """Every verdict rests on the cast moment, so its stability qualifies all of them. The
        engine measures it (r.rect_confidence) and the synthesis never said it."""
        r, ts = mainpuri
        st = ts.portrait.reading_stability
        assert st and r.rect_confidence.label in st
        assert str(r.rect_confidence.stable_count) in st

    def test_protections_carry_their_counterweight(self, mainpuri, canonical):
        """The Arishta chapter's cited protections are surfaced — and so is any UNCANCELLED
        debility, because a protection list without its counterweight is selective."""
        for r, ts in (mainpuri, canonical):
            pf = ts.portrait.protective_factors
            for prot in r.arishta.protections:
                assert any(str(prot) in x for x in pf), "a cited protection went unreported"
            for deb in r.arishta.uncancelled_debilities:
                assert any(str(deb) in x for x in pf), "an uncancelled debility was hidden"

    def test_chara_dasha_is_walled_like_the_karmic_lens(self, mainpuri):
        """The Jaimini chara dasha runs beside the Vimshottari chapter but is never a second
        timing authority — the wall must be stated wherever it appears."""
        _r, ts = mainpuri
        if ts.portrait.chara_now:
            assert "walled" in ts.portrait.chara_now

    def test_cross_checks_sit_on_the_cited_ladder_not_on_a_tally(self, mainpuri, canonical):
        """Every cross-check is placed at its own CITED reliability tier and none is scored.

        Astronomical/doctrinal fact under test: Raman states no numeric N-testimonies rule —
        HTJAH-I:495 says only that "all these must be properly weighed" — and this project already
        measured head-counting influences against his own reasoning on all seven Type-A cases and
        found it held 0 of 7 (COMPARATIVE_WEIGHING.md). So the summary may inventory dissent but
        must never grade it."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                d = t.dissent
                assert d is not None, f"{t.theme_id} carries no dissent summary"
                # the invented arithmetic is GONE — no grade, no tally, no agree/disagree score
                for banned in ("confidence", "systems_checked", "agreeing", "score"):
                    assert not hasattr(d, banned), f"{banned} is invented arithmetic, not doctrine"
                assert "HTJAH-I:495" in d.method_note
                for ck in d.checks:
                    assert ck.tier and ck.governing.startswith("PREC-")
                    assert ck.relation in ("reads with", "reads against", "restates the verdict")
                    if ck.system == "the bhava's own testimony ledger":
                        # the lord, karaka and navamsa ARE the verdict's own inputs restated by
                        # name, so this check can never be an independent vote (PREC-3)
                        assert ck.independent is False and ck.governing == "PREC-3"
                        assert ck.relation == ("reads against" if t.concordance.divergence
                                               else "reads with")
                    if ck.system == "the assigned division":
                        # PREC-11: the D1 Raman core decides, the varga corroborates
                        assert ck.independent and ck.governing == "PREC-11"
                        assert ck.relation == ("reads against"
                                               if any(x.relation == "diverges"
                                                      for x in t.divisional_checks)
                                               else "reads with")
                    if ck.system == "Ashtakavarga":
                        # Raman's own caveat puts AV a tier below a Raman-band reading
                        assert ck.governing == "PREC-4" and "HTJAH-II:4453" in ck.citation
                        assert t.av_support
                assert d.dissenting == tuple(c.system for c in d.checks
                                             if c.relation == "reads against")

    def test_the_walled_lens_is_never_a_cross_check(self, mainpuri, canonical):
        """A walled layer must not move a Parashari reading — including by arithmetic. The Jaimini
        karmic lens is recorded OUTSIDE the cross-checks entirely, never as one of them."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                d = t.dissent
                for name in [c.system for c in d.checks] + list(d.dissenting):
                    assert "karmic" not in name.lower() and "jaimini" not in name.lower()
                if t.karmic_lens is not None:
                    assert d.walled_note
                    assert "never" in d.walled_note and "neither a cross-check" in d.walled_note

    def test_contested_themes_are_the_inventory_not_a_threshold(self, mainpuri):
        """Chart level: a theme is listed iff ANY cross-check reads against it. The old ">= 2
        systems" cutoff was an invented threshold of exactly the kind HTJAH-I:495 forbids."""
        _r, ts = mainpuri
        named = {n for n, _d in ts.contested_themes}
        for t in ts.themes:
            if t.dissent.dissenting:
                assert t.name in named
            else:
                assert t.name not in named
        for _n, d in ts.contested_themes:
            assert d.dissenting
            # the passthrough is never in question: dissent discloses, it never overturns
            assert "may overturn a bhava judgment" in d.reading

    def test_the_narrative_does_not_repeat_the_dissent_it_summarises(self, mainpuri, canonical):
        """The sentence used to chain a clause per dissenting system AND then summarise them,
        saying the same thing twice and reaching 667 characters. It states the count once."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                body = t.final_interpretation
                assert body.count("Reading against it") <= 1
                # the superseded per-system clauses are gone
                assert "Ashtakavarga does not back it in the same place" not in body
                assert "Its own testimonies do not sit where the verdict does" not in body
                # and the superseded arithmetic grade never reaches the prose
                for graded in ("seriously contested", "cross-checks read against"):
                    assert graded not in body

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

    def test_the_longevity_band_frames_the_reading(self, mainpuri, canonical):
        """PREC-8 restored: Raman establishes the SPAN first and the marakas second.

        Astronomical/doctrinal fact under test: HTJAH-II:4465-4472 — "first establish the band by
        combination, THEN fix the period by the marakas. The numeric span is a cross-check, never
        a prediction of death." The synthesis used to read forward windows out to the 2040s
        without ever setting them against the span the engine had already computed."""
        for r, ts in (mainpuri, canonical):
            lf = ts.longevity
            assert lf is not None, "the band was computed and the reading never stated it"
            # the band is the ENGINE's, passed through — never re-derived here
            assert r.longevity_class in lf.band
            assert lf.years == r.longevity_years and tuple(lf.ymd) == tuple(r.longevity_ymd)
            assert lf.maraka_now is bool(r.maraka_period_now)
            # Raman's ORDER is the load-bearing claim, so it must be stated, in his words
            frame = lf.frame.lower()
            assert "span" in frame and "maraka" in frame
            assert frame.index("span") < frame.index("maraka periods second")
            assert "HTJAH-II:4465-4472" in lf.citation and "PREC-8" in lf.citation
            # the numeric is a cross-check, and the reading says so every time
            assert "cross-check" in lf.honesty and "never a forecast" in lf.honesty

    def test_every_named_window_is_tested_against_the_span(self, mainpuri, canonical):
        """A window is only meaningful inside a lifetime. Each theme's forward bhukti is read at
        its ordinal year of life and placed inside or outside the band — never left as a bare
        calendar range the reader has to date against a birth year themselves."""
        for r, ts in (mainpuri, canonical):
            lf = ts.longevity
            born = r.birth.year
            for t in ts.themes:
                if not t.activation_span:
                    assert not t.activation_in_span
                    continue
                assert t.activation_in_span, f"{t.theme_id} names a window and never dates it"
                assert "year" in t.activation_in_span
                # the ordinal is computed off the ENGINE's birth year, not invented
                import re as _re
                m = _re.search(r"\((\d{4})(?:-(\d{4}))?\)", t.activation_span)
                assert m, "the timing clause must carry its own calendar window"
                y0 = int(m.group(1))
                assert f"{y0 - born}" in t.activation_in_span
            # the chart-level reach agrees with the per-theme windows
            if lf.reading_reaches:
                assert lf.within_span == (lf.reading_reaches <= lf.span_year)

    def test_maraka_windows_are_named_after_the_band_and_never_predict(self, mainpuri):
        """Raman's step TWO. Each maraka-tier bhukti carrying the classical Saturn signal
        (HTJAH-II:4846-4849) is named, deduplicated per bhukti, and placed against the band —
        including when the two methods disagree, which is disclosed rather than reconciled."""
        _r, ts = mainpuri
        lf = ts.longevity
        assert lf.maraka_windows, "the engine computed maraka x Saturn confluences; name them"
        bhuktis = [w[0] for w in lf.maraka_windows]
        assert len(bhuktis) == len(set(bhuktis)), "one bhukti, one window — not one per pass"
        for _bh, span, score, standing in lf.maraka_windows:
            assert score >= 0 and standing in ("inside the band", "beyond the band", "")
            y0 = int(span.split("-")[0])
            assert (standing == "beyond the band") == (y0 > lf.span_year)
        # every window is FORWARD of the reading's anchor — a past maraka period is not a window
        assert all(int(w[1].split("-")[0]) >= _ON[0] for w in lf.maraka_windows)

    def test_the_longevity_frame_never_speaks_in_decree(self, mainpuri, canonical):
        """The 2026-08-17 decision permits TIMED INDICATIONS in the classical idiom and still
        refuses the decree voice. Longevity is the highest-stakes surface for that line, so
        every string this frame emits is held to the engine's own guard."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for _r, ts in (mainpuri, canonical):
            lf = ts.longevity
            texts = [lf.frame, lf.honesty, lf.citation, lf.band]
            texts += [t.activation_in_span for t in ts.themes]
            for txt in texts:
                hit = _FORBIDDEN_RE.search(txt or "")
                assert hit is None, f"decree language in the longevity frame: {hit.group(0)!r}"
            # and the walled-off Measured-Truth disclosure is never dropped
            assert "REAL_OUTCOME_GENERALIZATION.md" in lf.honesty

    def test_a_connection_names_a_mechanism_not_a_join(self, mainpuri, canonical):
        """A tie must say what the shared thing DOES on each side, not that a join exists.

        The old note was a template — "A and B overlap at H6, tying the two areas together" —
        which restates the join and tells the reader nothing about the chart. Every connection now
        carries the two verdicts it spans, and a shared bhava names whose primary it is."""
        for _r, ts in (mainpuri, canonical):
            names = {t.name: t for t in ts.themes}
            for c in ts.connections:
                assert c.note and c.theme_a in c.note and c.theme_b in c.note
                # the dead template must not come back
                assert "tying the two areas together" not in c.note
                # the verdicts on both ends are always stated — that is the integration
                va = names[c.theme_a].headline_verdict
                vb = names[c.theme_b].headline_verdict
                assert (f"read {va}" in c.note or f"reads {va}" in c.note)
                assert (f"read {vb}" in c.note or f"reads {vb}" in c.note)
                if c.shared.startswith("H"):
                    h = int(c.shared[1:])
                    # a shared bhava is one bhava in two roles; the note says which is which
                    assert "own bhava" in c.note and "draws on it" in c.note
                    assert h in names[c.theme_a].houses and h in names[c.theme_b].houses
                else:
                    # a shared graha leads BOTH — and its own measured condition is reported
                    assert names[c.theme_a].dominant_planets[0] == c.shared
                    assert names[c.theme_b].dominant_planets[0] == c.shared
                    assert "leads both" in c.note

    def test_no_single_theme_crowds_out_the_connection_fabric(self, mainpuri, canonical):
        """The busiest theme has the widest network BY CONSTRUCTION, so an uncapped list reports
        its breadth rather than the chart's fabric. On Mainpuri, Career took 4 of 6 slots."""
        from collections import Counter
        from app.raman_saab.theme_synthesis import _CONN_PER_THEME
        for _r, ts in (mainpuri, canonical):
            seen = Counter()
            for c in ts.connections:
                seen[c.theme_a] += 1
                seen[c.theme_b] += 1
            assert not seen or max(seen.values()) <= _CONN_PER_THEME
            # and a shared chief graha outranks a bare structural overlap
            kinds = [not c.shared.startswith("H") for c in ts.connections]
            assert kinds == sorted(kinds, reverse=True), "graha ties must rank above house ties"

    def test_the_span_is_never_rendered_to_two_decimals(self, mainpuri):
        """Raman gives a BAND; the ayurdaya number is a cross-check, and printing it to 1/100th
        of a year claims a precision the method does not have. The report has banned that since
        v2 (test_longevity_is_band_first_and_not_false_precision) and the frame must not
        reintroduce it on any surface."""
        import re as _re
        from app.raman_saab.detailed_report import to_markdown
        from app.raman_saab.report_html import standalone_html
        r, ts = mainpuri
        precise = f"{ts.longevity.years:.2f}"
        for surface in (to_markdown(r), standalone_html(r)):
            i = surface.find("span this reading sits inside")
            assert i > 0
            assert precise not in surface[i:i + 4000]
        # the raw float still travels in the DATA — it is the RENDERING that must round
        assert _re.match(r"^\d+\.\d+$", str(ts.longevity.years))

    def test_the_weather_calendar_is_subordinate_by_citation(self, mainpuri, canonical):
        """Three schemes the engine ran in full and the reading never consulted.

        Astronomical/doctrinal fact under test: transits are "always secondary in importance…
        like catalytic agents" (PREC-6, HTJAH-II:4679), and the eightfold Dasha Kakshya split is
        "a timing lens, never a verdict" (PREC-7, ASP-12:174). So the calendar may qualify a
        window and may never grade a bhava — and every window carries the rule that says so."""
        for _r, ts in (mainpuri, canonical):
            cal = ts.calendar
            if cal is None:
                continue
            assert cal.windows and "SUBORDINATE" in cal.frame
            assert "PREC-6" in cal.frame and "PREC-7" in cal.frame
            assert "REAL_OUTCOME_GENERALIZATION.md" in cal.honesty
            ref_year = _ON[0]
            for w in cal.windows:
                assert w.kind in ("Sade Sati", "Dasha x adverse transit", "Dasha Kakshya",
                                  "Slow-mover gochara")
                assert w.governing in ("PREC-6", "PREC-7") and w.citation
                assert w.governing == ("PREC-7" if w.kind == "Dasha Kakshya" else "PREC-6")
                # FORWARD only — a stretch that closed before the anchor is not a window ahead
                assert w.end_year >= ref_year
                assert w.current == (w.start_year <= ref_year <= w.end_year)
                assert w.span == (f"{w.start_year}-{w.end_year}"
                                  if w.end_year != w.start_year else str(w.start_year))
            assert list(cal.windows) == sorted(cal.windows,
                                               key=lambda w: (w.start_year, w.kind))
            assert set(cal.now) == {f"{w.kind}: {w.label} ({w.span})"
                                    for w in cal.windows if w.current}

    def test_each_theme_window_is_read_against_the_weather(self, mainpuri, canonical):
        """The join the report never made: a bhukti that grades par excellence for a bhava while
        Sade Sati sits over the Moon is not the same window as one running clear. Both halves
        were computed and neither knew about the other."""
        for _r, ts in (mainpuri, canonical):
            cal = ts.calendar
            for t in ts.themes:
                if not t.activation_span:
                    assert not t.weather_on_window
                    continue
                assert t.weather_on_window
                # subordination travels with every statement, never just the section header
                assert "PREC-6" in t.weather_on_window and "PREC-7" in t.weather_on_window
                import re as _re
                m = _re.search(r"\((\d{4})(?:-(\d{4}))?\)", t.activation_span)
                y0 = int(m.group(1))
                y1 = int(m.group(2) or m.group(1))
                overlapping = [w for w in (cal.windows if cal else ())
                               if not (w.end_year < y0 or w.start_year > y1)]
                if overlapping:
                    for w in overlapping:
                        assert w.label in t.weather_on_window
                else:
                    assert "clear weather" in t.weather_on_window

    def test_the_ancestral_screen_is_a_separate_layer_not_a_dissent(self, mainpuri, canonical):
        """PREC-12 — non-Raman screens are a different layer, not a contradiction. The pitru
        reading is CLASSICAL_NONCITABLE (BPHS provenance), so it must carry its provenance on its
        face and must never reach the cross-checks, the evidence links or the convergence count."""
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                if not t.pitru_screen:
                    continue
                assert t.houses[0] in (5, 9)
                assert "NOT Raman" in t.pitru_screen and "PREC-12" in t.pitru_screen
                assert "never a contradiction" in t.pitru_screen
                # walled: it is not a cross-check, not a link, not a contradiction
                if t.dissent is not None:
                    for c in t.dissent.checks:
                        assert "pitru" not in c.system.lower()
                for lk in t.links:
                    assert "pitru" not in f"{lk.label} {lk.value} {lk.accessor}".lower()
                for c in t.contradictions:
                    assert "pitru" not in f"{c.poles} {c.resolution}".lower()

    def test_the_calendar_never_speaks_in_decree(self, mainpuri, canonical):
        """Every string the weather layer emits is held to the engine's own guard — a rough
        stretch is an indication in the classical idiom, never a decree that something occurs."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for _r, ts in (mainpuri, canonical):
            texts: list[str] = []
            if ts.calendar is not None:
                texts += [ts.calendar.frame, ts.calendar.honesty]
                texts += [w.detail for w in ts.calendar.windows]
            texts += [t.weather_on_window for t in ts.themes]
            texts += [t.pitru_screen for t in ts.themes]
            texts += [c.note for c in ts.connections]
            for txt in texts:
                hit = _FORBIDDEN_RE.search(txt or "")
                assert hit is None, f"decree language: {hit.group(0)!r}"

    def test_the_portrait_names_the_RUNNING_pratyantardasha(self, mainpuri, canonical):
        """The label reads "Current chapter", so the pratyantar in it must be the one running.

        Astronomical fact under test: ``pratyantar_now`` holds all NINE pratyantardashas of the
        current bhukti, each with its own start/end. Taking ``pn[0]`` named the FIRST of the nine,
        which is the running one for roughly one ninth of any bhukti — on both fixtures it named a
        PD that was not running (Mainpuri said Jupiter PD while Ketu PD ran). The row containing
        ``ref_jd`` is the only correct one, as ``report_html._pratyantar_block`` already knew."""
        for r, ts in (mainpuri, canonical):
            pn = getattr(r, "pratyantar_now", ()) or ()
            cur = ts.portrait.current_chapter
            if not pn or not cur:
                continue
            run = next((x for x in pn
                        if x.start_jd <= r.ref_jd < x.end_jd), None)
            assert run is not None, "the anchor date falls in no pratyantar of the current bhukti"
            assert f"{run.pratyantar} PD" in cur, (
                f"portrait names a pratyantar that is not running: {cur!r} "
                f"(running is {run.pratyantar})")
            # and it must not merely be pn[0] coinciding — assert the bug's own signature is gone
            if pn[0].pratyantar != run.pratyantar:
                assert f"{pn[0].pratyantar} PD" not in cur

    def test_convergence_never_claims_independence_it_lacks(self, mainpuri, canonical):
        """The counter used to print "N of M INDEPENDENT axes agree with the headline". An audit
        of the data flow showed the claim was false for three of the four families it counted, so
        the word is now forbidden and every axis carries its own remove from the headline."""
        from app.raman_saab.theme_synthesis import _RESTATES, _SHARES, _SEPARATE
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                assert "independent axes" not in t.convergence_why
                for ax in t.convergence_axes:
                    assert ax.remove in (_RESTATES, _SHARES, _SEPARATE)
                    assert ax.why_remove and ax.direction in (-1, 0, 1)

    def test_each_axis_sits_at_its_measured_remove(self, mainpuri, canonical):
        """The classification is not decorative — each family is placed by what the code does.

        A facet's "dedicated reader" verdict IS `judge_house(h).significations[sig]` and the
        headline is `_rollup()` over those same significations (house_template.py:1992-2005); the
        D9 link is `navamsa_status`, an input to `_decide` (house_template.py:387-395); a network
        house is admitted only when a driving graha of the primary house touches it. None of the
        three is a second opinion, and only the assigned division and Ashtakavarga stand apart."""
        from app.raman_saab.theme_synthesis import _RESTATES, _SHARES, _SEPARATE
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                for ax in t.convergence_axes:
                    if "dedicated reader" in ax.label or ax.label.startswith("D9 "):
                        assert ax.remove == _RESTATES
                    elif "(network)" in ax.label or "Yoga" in ax.label:
                        assert ax.remove == _SHARES
                    else:
                        assert ax.remove == _SEPARATE
                # the primary rollup is never its own witness (PREC-3) — it must not appear
                prim = f"House {t.houses[0]} rollup"
                assert not any(a.label == prim for a in t.convergence_axes)

    def test_the_separate_testimony_is_actually_counted(self, mainpuri, canonical):
        """The assigned division and Ashtakavarga are the only genuinely separate checks in this
        set — measured outside the house verdict entirely — and neither was ever admitted to the
        count. Without them the tier had no independent basis at all."""
        from app.raman_saab.theme_synthesis import _SEPARATE
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                sep = [a for a in t.convergence_axes if a.remove == _SEPARATE]
                own_div = [d for d in t.divisional_checks
                           if d.relation in ("concurs", "diverges")]
                for d in own_div:
                    assert any(d.varga in a.label for a in sep)
                # ...but only when AV has something to assert. Every driver reading "about
                # average" is a genuine abstention, not a missing axis (Canonical fortune).
                decisive = [a for a in t.av_support
                            if a.verdict in ("well supported", "poorly supported")]
                assert bool(decisive) == any("Ashtakavarga" in a.label for a in sep)

    def test_a_diverging_division_opposes_whatever_the_headline_says(self, mainpuri, canonical):
        """Sign check. 'concurs' means the varga agrees with the HEADLINE, in whichever direction
        the headline points — writing a flat +1 made a diverging varga *agree* with an afflicted
        rollup, an inversion on exactly the themes where the disagreement matters most."""
        from app.raman_saab.insight_digest import _lean_of
        from app.raman_saab.theme_synthesis import _dir
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                head = _dir(_lean_of(t.headline_verdict))
                if head == 0:
                    continue
                for d in t.divisional_checks:
                    if d.relation not in ("concurs", "diverges"):
                        continue
                    ax = next(a for a in t.convergence_axes if d.varga in a.label)
                    if d.relation == "concurs":
                        assert ax.direction == head
                    else:
                        assert ax.direction == -head

    def test_the_stated_breakdown_reconciles_with_the_count(self, mainpuri, canonical):
        """'N of M agree… of those M, a restate / b share / c stand apart' must add up — an
        earlier draft counted M over directional axes and the breakdown over ALL of them, so the
        sentence contradicted itself in print."""
        import re as _re
        from app.raman_saab.theme_synthesis import _SEPARATE, _RESTATES, _SHARES
        for _r, ts in (mainpuri, canonical):
            for t in ts.themes:
                m = _re.search(r"of those (\d+), ", t.convergence_why)
                if not m:
                    continue
                total = int(m.group(1))
                directional = [a for a in t.convergence_axes if a.direction != 0]
                assert total == len(directional)
                assert total == sum(1 for a in directional
                                    for _ in [0] if a.remove in (_RESTATES, _SHARES, _SEPARATE))
