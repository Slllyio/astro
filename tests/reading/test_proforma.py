"""Tests for `app.reading.proforma` orchestrator.

The two-function pattern (private `_run_core_pipeline`, public `compute`) is
the seam that prevents Tier-3 enrichment recursion (spec Section 5). These
tests lock that contract before any sequence module can violate it. Per the
TDD discipline in CLAUDE.md, each test asserts one structural fact:

- The pipeline emits a dict that round-trips through `ReadingOutput`.
- `Meta.schema_version` and `Meta.stability` carry the locked defaults.
- `DoctrineConfig` defaults match the 16 lockfile decisions (D-1..D-16) and
  the open-Q5 consensus thresholds.
- `compute(enrich=False)` returns the exact same dict as the bare core
  pipeline (no Tier-3 mutation).
- `compute(enrich=True)` is the reachable path through `_apply_tier3_enrichments`
  (Phase 1 stub: identity).
"""
from __future__ import annotations

from app.reading.proforma import (
    _apply_tier3_enrichments,
    _run_core_pipeline,
    compute,
)
from app.reading.schema import ChartInput, ReadingOutput


CANONICAL_INPUT = ChartInput(
    dob="1990-07-15",
    time="12:00",
    tz="+05:30",
    lat=12.97,
    lon=77.59,
)


class TestRunCorePipeline:
    """`_run_core_pipeline` is the private deterministic Stages-1..7 entry."""

    def test_returns_dict_matching_reading_output_shape(self):
        """Output dict must validate against ReadingOutput Pydantic model."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        # Round-trip through Pydantic asserts the full structural contract.
        validated = ReadingOutput.model_validate(output)
        assert validated.meta.schema_version == "1.2.0"
        assert validated.meta.stability == "experimental"

    def test_meta_chart_input_echoes_user_envelope(self):
        """Meta.chart_input must echo the user-supplied ChartInput verbatim."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        ci_dict = output["meta"]["chart_input"]
        assert ci_dict["dob"] == "1990-07-15"
        assert ci_dict["time"] == "12:00"
        assert ci_dict["tz"] == "+05:30"
        assert ci_dict["lat"] == 12.97
        assert ci_dict["lon"] == 77.59

    def test_meta_doctrine_config_has_locked_defaults(self):
        """DoctrineConfig in output must match the 16 lockfile decisions."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        dc = output["meta"]["doctrine_config"]
        # D-1: 8-karaka (PVR Narasimha Rao)
        assert dc["karaka_mode"] == 8
        # D-2: 1/7 -> 10 arudha exception
        assert dc["arudha_exception"] == "1_7_to_10"
        # D-3: Shodashavarga 16-varga vimsopaka
        assert dc["vimsopaka_scheme"] == "shodashavarga"
        # D-4: BPHS Ch.47 v.3 Ishta formula
        assert dc["ishta_formula"] == "bphs_47_3"
        # D-8: Sripati cusps
        assert dc["bhava_chalit_system"] == "sripati"
        # D-10: Sanjay-Rath karaka triangulation
        assert dc["karaka_triangulation_reading"] == "sanjay_rath"
        # D-11: BPHS 39.10 Neech Bhanga
        assert dc["neech_bhanga_rule"] == "bphs_39_10"
        # D-12: Strict 180-degree Rahu-leading Kala Sarpa
        assert dc["kala_sarpa_definition"] == "strict_180_rahu_leading"
        # D-13: Northern-latitude Graha Yuddha winner
        assert dc["graha_yuddha_winner"] == "northern_latitude"
        # Open-Q5 resolution: consensus thresholds
        assert dc["consensus_min_sources"] == 3
        assert dc["consensus_agreement_threshold"] == 0.66

    def test_enrichment_flags_default_to_false_in_core(self):
        """Core pipeline must report enrichment_enabled=False (no Tier-3 ran)."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        assert output["meta"]["enrichment_enabled"] is False
        assert output["meta"]["robustness_enabled"] is False

    def test_all_required_stage_blocks_present(self):
        """The 9 top-level keys per spec Section 6 must all be present."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        required = {
            "meta",
            "chart",
            "primitives",
            "foundations",
            "practitioner",
            "sequences",
            "domains",
            "contradictions",
            "warnings",
        }
        assert required <= set(output.keys())

    def test_classical_yogas_surfaced_with_citations(self):
        """The core 88-detector yoga library is surfaced in the reading as
        `classical_yogas`, each carrying a name + classical reference. This
        guards the modern-life re-assembly, which must carry the field through
        (it rebuilds a fresh ReadingOutput and previously dropped it)."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        assert "classical_yogas" in output
        cy = output["classical_yogas"]
        # a real natal chart lights up several classical yogas
        assert len(cy) >= 3, len(cy)
        for y in cy:
            assert y["name"] and y["reference"]
        # enrich=True (through Tier-3) must not drop them either
        enriched = compute(CANONICAL_INPUT, enrich=True)
        assert len(enriched["classical_yogas"]) == len(cy)


class TestCompute:
    """`compute` is the public orchestrator with optional Tier-3 wrapping."""

    def test_compute_with_enrich_false_skips_tier3(self):
        """enrich=False MUST take the bare deterministic path (no Tier-3).

        Asserts that Tier-3 enrichment never fires when ``enrich=False``:
        ``Meta.enrichment_enabled`` and ``Meta.robustness_enabled`` both
        stay False, no contradictions are computed top-level. (Direct
        dict-equality with a second `_run_core_pipeline` call would
        compare two independent timestamps and become flaky once Phase 7
        wiring causes the pipeline to take real wall-clock time.)
        """
        result = compute(CANONICAL_INPUT, enrich=False)
        assert result["meta"]["enrichment_enabled"] is False
        assert result["meta"]["robustness_enabled"] is False
        # The contradictions list is only populated by the Tier-3
        # afterpass; with enrich=False it MUST stay empty.
        assert result["contradictions"] == []

    def test_compute_default_enrich_true_is_reachable(self):
        """Default enrich=True path is reachable and round-trips schema.

        Phase 7: with the real Tier-3 chain wired, the result still
        validates against the schema and reports ``enrichment_enabled=True``
        on its Meta envelope.
        """
        result = compute(CANONICAL_INPUT)
        # Round-trip validation proves the enriched payload still conforms.
        validated = ReadingOutput.model_validate(result)
        assert validated.meta.schema_version == "1.2.0"
        assert validated.meta.enrichment_enabled is True

    def test_compute_explicit_enrich_true_validates(self):
        """Passing enrich=True explicitly produces a schema-valid result."""
        explicit_result = compute(CANONICAL_INPUT, enrich=True)
        validated = ReadingOutput.model_validate(explicit_result)
        assert validated.meta.schema_version == "1.2.0"
        assert validated.meta.enrichment_enabled is True

    def test_apply_tier3_enrichments_flips_enrichment_flag(self):
        """Phase 7: Tier-3 afterpass flips ``Meta.enrichment_enabled``.

        Pre-Phase-7 this test asserted identity (the stub returned `base`
        unchanged). Post-Phase-7 the real Tier-3 chain runs and the only
        invariant we can lock structurally (without coupling to specific
        finding contents) is that ``enrichment_enabled`` transitions
        False -> True.
        """
        bare = _run_core_pipeline(CANONICAL_INPUT)
        assert bare["meta"]["enrichment_enabled"] is False
        enriched = _apply_tier3_enrichments(bare, CANONICAL_INPUT)
        assert enriched["meta"]["enrichment_enabled"] is True


class TestPresentTenseAndDoctrineEnrichments:
    """Phase 0/1: compute() attaches present-tense + real-doctrine blocks under
    chart.extras — the daśā running TODAY (not birth), live transits, the
    encoded Raman per-house verdicts, and the executive summary."""

    def test_dasha_now_is_present_day_not_birth(self):
        """extras.dasha_now.md must be the MD covering TODAY, distinct from the
        birth balance — the fix for the impossible 'Current Mahadasha' window."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        dn = extras.get("dasha_now") or {}
        md = dn.get("md") or {}
        bb = dn.get("birth_balance") or {}
        assert md.get("md_lord"), "dasha_now.md must carry a running mahādaśā lord"
        # The running MD must cover the present moment: age_now falls inside the window.
        assert md["age_at_start_years"] <= md["age_now_years"] < md["age_at_end_years"]
        # And it must be labelled distinctly from the birth balance.
        assert bb.get("md_lord"), "birth_balance must be surfaced separately"
        assert bool(md.get("is_at_birth")) is False

    def test_house_doctrine_grades_all_twelve_houses(self):
        """extras.house_doctrine.houses carries a real Raman verdict per house,
        each with a 0..8 grade index and the evidence findings (the 'why')."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        hd = extras.get("house_doctrine") or {}
        houses = hd.get("houses") or {}
        assert len(houses) == 12
        for h in range(1, 13):
            hv = houses[str(h)]
            assert hv["verdict_label"] in hd["scale"]
            assert hv["verdict_index"] is None or 0 <= hv["verdict_index"] <= 8
            # Confidence is a real N-of-3 vote, never a fabricated probability.
            conf = hv["confidence"]
            assert conf["graded"] <= 3
            assert 0 <= conf["agreement"] <= conf["graded"]

    def test_executive_summary_is_populated(self):
        """extras.executive_summary is a deterministic list of lay-language
        lines built from the real engine output."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        summary = extras.get("executive_summary") or []
        assert isinstance(summary, list) and summary
        assert all(isinstance(line, str) and line for line in summary)

    def test_planet_strength_carries_real_numbers(self):
        """extras.planet_strength surfaces the bundle's real Vimsopaka (0–20)
        and Ṣaḍbala ratios — measured, not fabricated."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        ps = extras.get("planet_strength") or {}
        planets = ps.get("planets") or []
        assert len(planets) == 9  # 7 visible + Rahu + Ketu
        for r in planets:
            assert r["planet"]
            if r["vimsopaka"] is not None:
                assert 0.0 <= r["vimsopaka"] <= 20.0

    def test_tensions_are_bounded_and_derived(self):
        """extras.tensions is a capped list of real D1/D9 or lord-vs-kāraka
        splits from house_doctrine (never fabricated, never floods)."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        tensions = extras.get("tensions")
        # May be empty for a harmonious chart, but must never exceed the cap.
        assert tensions is None or (isinstance(tensions, list) and len(tensions) <= 6)
        for t in tensions or []:
            assert t["kind"] in ("d1d9", "factor_clash")
            assert 1 <= t["house"] <= 12 and t["text"]

    def test_domain_decisions_are_question_centric_and_honest(self):
        """extras.domain_decisions gives per-domain potential + timing +
        confidence — a transparent roll-up, ranked strongest-first, with a
        0–100 doctrine potential (never a fabricated probability)."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        dd = extras.get("domain_decisions") or []
        assert len(dd) == 8  # the eight life domains
        keys = {d["key"] for d in dd}
        assert {"career", "wealth", "marriage", "health"} <= keys
        scores = [d["score"] for d in dd]
        assert scores == sorted(scores, reverse=True)  # strongest-first
        for d in dd:
            assert 0 <= d["score"] <= 100
            assert d["potential"] in (
                "Excellent", "Strong", "Good", "Moderate", "Challenging")
            assert d["timing"] in ("Active now", "Warming up", "Quiet")
            assert d["confidence"] in (
                "Very high", "High", "Medium", "Low", "Conflicting indications")
            assert d["verdict"]

    def test_master_synthesis_is_the_governing_judgement(self):
        """extras.master reduces every block into ONE coherent judgement — a
        dominant planet cross-checked with its functional role, core
        strengths/weaknesses from the real domain grades, the running daśā
        phase, a life theme, and the ≤10 decisive factors (anti-rule-dumping).
        Every field is real engine output, never a fabricated probability."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        master = extras.get("master") or {}
        assert master, "the master synthesis block must be present"

        # --- dominant planet is drawn from the REAL composite + functional role.
        dp = master["dominant_planet"]
        assert dp and dp["planet"] and dp["reason"]
        ps_planets = {r["planet"] for r in
                      (extras.get("planet_strength") or {}).get("planets", [])}
        assert dp["planet"] in ps_planets
        assert 0 <= dp["composite"] <= 100

        # --- core strengths/weaknesses come from the ranked domain decisions.
        dd_keys = {d["key"] for d in (extras.get("domain_decisions") or [])}
        for cap in master["core_strengths"] + master["core_weaknesses"]:
            assert cap["domain"] in dd_keys
            assert 0 <= cap["score"] <= 100

        # --- decisive factors: the anti-rule-dumping cap (≤10), each real.
        decisive = master["decisive_factors"]
        assert isinstance(decisive, list) and len(decisive) <= 10
        # ranked by |contrib| descending (the strongest evidence leads).
        mags = [abs(f["contrib"]) for f in decisive]
        assert mags == sorted(mags, reverse=True)
        for f in decisive:
            assert f["text"] and f["polarity"] in ("positive", "negative")
            assert f["domain"]

        # --- current phase is the daśā running NOW, not a probability.
        phase = master.get("current_phase")
        if phase:
            assert phase["md_lord"] and phase["summary"]
            dn_lord = ((extras.get("dasha_now") or {}).get("md") or {}).get("md_lord")
            assert phase["md_lord"] == dn_lord

        # --- life theme is a single synthesised sentence.
        assert isinstance(master["life_theme"], str)

    def test_native_profile_reads_who_you_are(self):
        """extras.native_profile is eight behavioural styles reasoned from the
        real planet-strength table (shared lexicon), plus an honest internal
        clarity figure — never a probability."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        np_ = extras.get("native_profile") or {}
        assert np_, "native profile must be present"
        styles = np_["styles"]
        keys = {s["key"] for s in styles}
        assert {"decision_making", "emotional", "leadership", "communication",
                "risk_tolerance", "learning", "financial", "relationship"} == keys
        # each style is reasoned from a real graha in the strength table.
        ps_planets = {r["planet"] for r in
                      (extras.get("planet_strength") or {}).get("planets", [])}
        for s in styles:
            assert s["planet"] in ps_planets
            assert s["text"] and s["condition"] in ("well placed", "under strain", "mixed")
        # clarity is a bounded internal-signal percentage.
        assert 0 <= np_["clarity_pct"] <= 100
        assert np_["clear"] + np_["strained"] <= np_["total"] == len(styles)

    def test_domain_confidence_is_an_honest_percentage(self):
        """Each domain decision carries a confidence PERCENTAGE with a reason —
        internal agreement of independent signals, never an event probability."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        for d in (extras.get("domain_decisions") or []):
            assert 0 <= d["confidence_pct"] <= 100
            assert d["confidence_reason"]

    def test_shared_lexicon_is_single_source(self):
        """The classical narrative and the native profile read the same
        vocabulary from _planet_lexicon (no drift between the two readings)."""
        from app.reading import _planet_lexicon as lex
        from app.reading import classical_narrative as cn
        assert cn._PLANET_QUALITY is lex.PLANET_QUALITY
        assert cn._SIGN_TEMPERAMENT is lex.SIGN_TEMPERAMENT
        # the shared predicate behaves as documented.
        assert lex.well_placed("exalted", None, False) is True
        assert lex.well_placed("debilitated", 90, False) is False
        assert lex.well_placed(None, 50, False) is None

    def test_narrative_and_risk_opportunity_are_derived(self):
        """extras.narrative/risks/opportunities are deterministic lay-language
        derived from the decision layer — cohesive, honest, no invented events."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        narrative = extras.get("narrative") or []
        assert isinstance(narrative, list)
        # A chart with decisions must yield a cohesive multi-sentence narrative.
        if extras.get("domain_decisions"):
            assert len(narrative) >= 2
            assert all(isinstance(p, str) and p for p in narrative)
        # Risks/opportunities are bounded lists of strings when present.
        for key in ("risks", "opportunities"):
            vals = extras.get(key)
            assert vals is None or (
                isinstance(vals, list) and len(vals) <= 6
                and all(isinstance(v, str) and v for v in vals))

    def test_classical_factors_are_computed(self):
        """extras.classical_factors surfaces the advanced doctrine layers (#12)
        from real chart data — functional nature for all 7 visible planets,
        maraka/badhaka, and the reversal-yoga detectors."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        cf = extras.get("classical_factors") or {}
        assert cf, "classical_factors should be populated for a valid chart"
        assert len(cf["functional"]) == 7  # the 7 visible planets
        for f in cf["functional"]:
            assert f["nature"] in ("benefic", "malefic", "neutral")
        assert isinstance(cf["marakas"], list)
        assert cf["badhaka"]["house"] in (7, 9, 11)  # dual/fixed/movable lagna
        for group in ("retrograde", "graha_yuddha", "vipareeta", "neecha_bhanga"):
            assert isinstance(cf[group], list)

    def test_raman_doctrine_is_cited_and_safe(self):
        """extras.raman_doctrine surfaces the B. V. Raman knowledge base applied
        to the chart — favourable, cited combinations only; blunt fatalistic /
        longevity text (refuted by Track B) must never leak in."""
        import re as _re
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        rd = extras.get("raman_doctrine") or {}
        assert rd, "raman_doctrine should be populated for a valid chart"
        assert rd["total_applicable"] > 0
        # Every source book is one of B. V. Raman's works.
        raman_books = {
            "How to Judge a Horoscope, Vol. I", "How to Judge a Horoscope, Vol. II",
            "Hindu Predictive Astrology", "Three Hundred Important Combinations",
            "Studies in Jaimini Astrology", "A Manual of Hindu Astrology",
            "Graha and Bhava Balas", "Muhurtha (Electional Astrology)", "Prasna Marga",
        }
        for b in rd["books"]:
            assert b["label"] in raman_books
        unsafe = _re.compile(r"death|\bdie\b|mortal|balarish|fatal|\bkill", _re.I)
        for f in rd["favorable"]:
            assert f["text"] and f["book_label"] in raman_books
            assert not unsafe.search(f["text"]), f["text"]

    def test_judgements_are_conflict_resolved_and_weighted(self):
        """extras.judgements: one reconciled verdict per domain plus the weighted
        positive/negative evidence that produced it (no raw contradictions)."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        j = extras.get("judgements") or {}
        assert j, "judgements should be populated"
        for key, d in j.items():
            assert d["verdict"] and isinstance(d["verdict"], str)
            assert d["dominant"] in ("positive", "negative")
            assert d["weighted_positive"] >= 0 and d["weighted_negative"] >= 0
            # evidence carries a signed weighted contribution, deduped
            texts = [e["text"] for e in d["positive"]]
            assert len(texts) == len(set(texts))  # no double-counted evidence
            for e in d["positive"]:
                assert e["contrib"] > 0 and e["weight"] in (1, 2, 3, 5)
            for e in d["negative"]:
                assert e["contrib"] < 0

    def test_classical_narrative_follows_ramans_hierarchy(self):
        """extras.classical_narrative is the ten-chapter judicial reading in
        Raman's sequence — connected prose derived from the real engine output,
        no scores in the text."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        narrative = extras.get("classical_narrative") or []
        assert len(narrative) == 10
        titles = [c["title"] for c in narrative]
        # The Raman hierarchy: general → ascendant → lord → Moon → Sun → ...
        assert "General estimate" in titles[0]
        assert "Ascendant" in titles[1] and "lord" in titles[2].lower()
        assert "Moon" in titles[3] and "Sun" in titles[4]
        assert "yoga" in titles[7].lower() and "Timing" in titles[9]
        for c in narrative:
            assert c["paras"]
            for p in c["paras"]:
                # Judicial prose must not leak raw numeric scores like "(+1.2)".
                assert "+0." not in p and "/100" not in p
