"""The grounded report explainer — `app/llm/report_explainer.py`.

The safety-critical layer: an LLM may EXPLAIN the engine's computed, cited findings but never
generate a verdict or a prediction. These tests pin the evidence assembly, the provenance guard
(which must catch a planted ungrounded claim and a planted prediction), and the deterministic
fallback. The LLM itself is never called live — StubClient keeps it offline.
"""
from __future__ import annotations

import re

import pytest

from app.llm.client import StubClient
from app.llm.report_explainer import (
    CRITIC_SYSTEM,
    EXPLAINER_SYSTEM,
    _FACTREF_RE,
    _answer_from_text,
    _parse_critique,
    build_evidence,
    build_prompt,
    critique,
    explain,
    explain_with_critic,
    provenance_check,
    refusal_reason,
    translate_to_hindi,
)


class SeqStub:
    """A client double that returns a sequence of responses across successive calls (the last one
    repeats) — lets one test drive a draft->refine flow where the SAME client is called twice."""

    def __init__(self, *responses: str):
        self._responses = list(responses)
        self.model = "seqstub"
        self.last_prompt = ""

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]
from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.report_json import to_report_dict

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def rdict():
    return to_report_dict(build_detailed_report(_CANONICAL))


class TestEvidence:
    def test_summary_evidence_names_the_ruler(self, rdict):
        ev = build_evidence(rdict, "summary")
        assert ev.facts
        assert any("ruler of the nativity" in f.text.lower() for f in ev.facts)
        assert all(f.n == i + 1 for i, f in enumerate(ev.facts))   # contiguous numbering

    def test_house_evidence_carries_the_verdict_and_citations(self, rdict):
        ev = build_evidence(rdict, "house:5")
        assert any("House 5" in f.text for f in ev.facts)
        assert any(f.cite for f in ev.facts)                        # at least one cited fact

    def test_whole_evidence_spans_houses_and_yogas(self, rdict):
        ev = build_evidence(rdict, "whole")
        txt = " ".join(f.text for f in ev.facts)
        assert "House 1" in txt and "House 12" in txt
        assert "yoga" in txt.lower()

    def test_prompt_injects_only_evidence(self, rdict):
        ev = build_evidence(rdict, "house:5")
        prompt = build_prompt(ev, question="why is this house afflicted?")
        assert "[Fact 1]" in prompt
        assert "anchoring every factual sentence" in prompt or "[Fact N]" in prompt


class TestRicherExplains:
    """Phase C: a section/house explanation now carries the CONNECTIVE facts the engine already
    holds — the individual testimony witnesses, the reading's information content, and the
    cross-feature insights that bridge into the section — so the explanation is deeper and
    connected, without any new judgment."""

    def test_house_evidence_surfaces_its_individual_witnesses(self, rdict):
        ev = build_evidence(rdict, "house:5")
        assert any("individual witnesses" in f.text.lower() for f in ev.facts)

    def test_house_evidence_states_information_content_for_distinctive_readings(self, rdict):
        target = next((h for h, e in rdict["distinctive"]
                       if e.get("rarity") and e["rarity"] != "common"), None)
        if target is None:
            pytest.skip("no rare/notable reading on this chart")
        ev = build_evidence(rdict, f"house:{target}")
        info = [f for f in ev.facts if "information content" in f.text.lower()]
        assert info
        assert info[0].cite is None          # population data carries NO Raman citation

    def test_section_explain_surfaces_linked_cross_feature_insights(self, rdict):
        links_yogas = any("yogas" in link.lower()
                          for ins in rdict["insights"] for link in ins.get("links", []))
        if not links_yogas:
            pytest.skip("no insight links into the Yogas section on this chart")
        ev = build_evidence(rdict, "section:yogas")
        assert any("cross-feature insight" in f.text.lower() for f in ev.facts)

    def test_nichod_section_reuses_summary_facts_not_the_bundled_essence(self, rdict):
        """2026-07-30: section:nichod used to fall through to the generic per-key dict loop,
        which cites nichod's own `caution`/`essence` fields — each a SINGLE string still
        bundling multiple houses'/yogas' numbers together (the exact shape _summary_facts()
        was fixed away from). It must now reuse the already-decomposed _summary_facts()
        instead, so a house's tenor-split fact never shares a citation with a different
        house's, or with the whole essence blob."""
        ev_nichod = build_evidence(rdict, "section:nichod")
        ev_summary = build_evidence(rdict, "summary")
        assert [f.text for f in ev_nichod.facts] == [f.text for f in ev_summary.facts]
        assert not any(f.text.startswith("essence:") or f.text.startswith("caution:")
                      for f in ev_nichod.facts)

    def test_distinctive_fact_quotes_band_share_not_the_percentile(self, rdict):
        """A calibration entry carries TWO population numbers with opposite senses: `band_share`
        ('X% of charts share this exact reading', small = rare) and `favourability_percentile`
        ('more favourable than X% of the population', large = good). The summary evidence printed
        the percentile inside band_share's sentence (2026-07-30 — 08-02), asserting that 95% of
        charts shared a reading only 10% actually share, contradicting the digest's own fact for
        the same signification. Both numbers must appear, each with its own wording."""
        ev = build_evidence(rdict, "summary")
        facts = [f.text for f in ev.facts if "share this exact reading" in f.text]
        assert facts, "summary evidence surfaces no distinctive reading for the canonical chart"
        for h, entry in rdict["distinctive"][:3]:
            if entry.get("band_share") is None or entry.get("rarity") == "common":
                continue
            hit = next((t for t in facts
                        if t.startswith(f"House {h}'s '{entry['signification']}'")), None)
            assert hit, f"no distinctive fact for House {h} {entry['signification']}"
            assert f"{entry['band_share']:.0%} of charts share this exact reading" in hit
            assert (f"more favourably than "
                    f"{entry['favourability_percentile']:.0%} of the population") in hit


class TestProvenanceGuard:
    def _ev(self, rdict):
        return build_evidence(rdict, "summary")

    def test_anchored_paragraph_scores_full(self, rdict):
        """Grounding is scored per PARAGRAPH (the claim-cluster unit) — a paragraph whose
        connective and evidence sentences share one anchor is fully grounded (the live-model
        fix: a per-sentence metric false-refused genuinely cited answers)."""
        text = ("Your chart's ruler is Mercury, which shapes the overall temperament. The "
                "strongest planet is the Sun [Fact 1] [Fact 2].")
        pc = provenance_check(text, self._ev(rdict))
        assert pc["grounding_ratio"] == 1.0
        assert not pc["forbidden_moves"] and not pc["bad_anchors"]
        assert "[Fact 1]" in pc["anchors_used"]

    def test_unanchored_paragraph_is_not_rescued_by_gloss(self, rdict):
        """SAFETY: a [gloss] tag does NOT ground a paragraph that carries no valid [Fact N]/
        [Ref N] — the guard cannot tell a real paraphrase from a fabricated claim wearing the
        tag (the review's finding #1). Two paragraphs: one cited, one gloss-only."""
        text = ("Your ruler is Mercury [Fact 1].\n\n"
                "You have a pleasant disposition and a fine mind [gloss].")
        pc = provenance_check(text, self._ev(rdict))
        assert pc["grounding_ratio"] == 0.5      # the gloss-only paragraph is not grounded
        assert pc["gloss_ratio"] > 0.0

    def test_bad_anchor_referencing_nonexistent_fact(self, rdict):
        """An anchor whose N is not in the evidence is flagged (not counted as grounded)."""
        pc = provenance_check("A fortune awaits you [Fact 99].", self._ev(rdict))
        assert "[Fact 99]" in pc["bad_anchors"]
        assert pc["grounding_ratio"] == 0.0

    def test_claim_no_fact_supports_is_refused(self, rdict):
        """SAFETY (2026-08-02): citing a REAL fact while asserting an entity the evidence never
        computed passes every presence-based check — grounding is 100%, the anchor is valid — so
        only citation SUPPORT catches it. Nowhere does this chart's evidence name Pluto."""
        ev = self._ev(rdict)
        pc = provenance_check("Your ruler is shadowed by Pluto [Fact 1].", ev)
        assert pc["grounding_ratio"] == 1.0 and not pc["bad_anchors"]
        assert any("Pluto" in c for c in pc["unsupported_claims"])
        ans = _answer_from_text("Your ruler is shadowed by Pluto [Fact 1].", ev, model="t")
        assert "no fact in the evidence supports" in (refusal_reason(ans, 0.6) or "")

    def test_a_claim_that_belongs_to_another_fact_is_reported_but_still_served(self, rdict):
        """Mis-attribution is a quality problem, not a safety one: the claim IS true of the
        evidence, only the pointer is wrong (78% of the corpus's citation errors). Measured and
        surfaced, never refused — refusing it would drop a correct reading to engine prose."""
        ev = self._ev(rdict)
        other = next(f for f in ev.facts if "longevity" in f.text.lower())
        years = re.search(r"\b(\d{2,3})\b", other.text).group(1)
        text = f"The engine reads a lifespan of about {years} years [Fact 1]."
        pc = provenance_check(text, ev)
        assert any(f"#{years}" in c for c in pc["mis_attributed"])
        assert not pc["unsupported_claims"]
        assert refusal_reason(_answer_from_text(text, ev, model="t"), 0.6) is None

    def test_model_authored_citation_is_flagged(self, rdict):
        """SAFETY: a WORK:line token the model wrote (not in the evidence) is a fabricated
        citation — the frontend would render it as a clickable 'Raman source' (finding #4)."""
        pc = provenance_check("This is per the scripture HTJAH-I:99999 [Fact 1].", self._ev(rdict))
        assert "HTJAH-I:99999" in pc["fabricated_citations"]

    def test_unanchored_paragraph_is_flagged(self, rdict):
        text = ("Your ruler is Mercury [Fact 1].\n\n"
                "You have a secret talent for painting that the chart clearly reveals.")
        pc = provenance_check(text, self._ev(rdict))
        assert pc["grounding_ratio"] == 0.5
        assert any("painting" in s for s in pc["ungrounded_sentences"])

    def test_deferral_is_always_safe(self, rdict):
        """The prescribed out-of-scope reply must never be refused (it has no anchor by
        nature) — the live-model test showed Sonnet returns exactly this to a prediction ask."""
        ev = build_evidence(rdict, "summary")
        ans = explain(ev, None, StubClient("The engine does not compute that."))
        assert ans.is_deferral is True
        assert refusal_reason(ans, 0.8) is None

    def test_prediction_verb_is_caught(self, rdict):
        text = "Because the 7th is strong [Fact 1], you will marry in 2027 and inherit wealth."
        pc = provenance_check(text, self._ev(rdict))
        assert pc["forbidden_moves"]                                # a forbidden move detected
        assert any("will" in m for m in pc["forbidden_moves"])      # prediction language caught

    def test_destined_and_predict_are_caught(self, rdict):
        pc = provenance_check("You are destined to great wealth. I predict success.",
                              self._ev(rdict))
        moves = " ".join(pc["forbidden_moves"])
        assert "destined" in moves and "predict" in moves

    def test_paraphrased_predictions_are_caught(self, rdict):
        """Decree evasions still trip the tripwire. (2026-08-17 prediction-unblock,
        user decision: DATED INDICATIONS in classical idiom are now allowed — see
        test_timed_indications_now_pass; decree voice and decree-dated death stay refused.)"""
        for evasion in ("You are going to gain a promotion.",
                        "Death around age 62 is likely.",
                        "You'll inherit wealth."):
            pc = provenance_check(evasion + " [Fact 1]", self._ev(rdict))
            assert pc["forbidden_moves"], f"missed: {evasion}"

    def test_doctrine_review_evasions_are_caught(self, rdict):
        """Third-person futures and certainty-decree verbs must still refuse (the arms
        the 2026-08-17 unblock deliberately kept). The 2026-07-28 dated-indication and
        promises/brings/foretells arms were lifted by user decision — those phrasings
        are classical indication idiom and now pass; see the allowed-list test."""
        for evasion in ("The native will attain great wealth.",
                        "She will face a serious upheaval.",
                        "He shall prosper greatly.",
                        "He is bound to inherit property."):
            pc = provenance_check(evasion + " [Fact 1]", self._ev(rdict))
            assert pc["forbidden_moves"], f"missed: {evasion}"

    def test_timed_indications_now_pass(self, rdict):
        """The 2026-08-17 prediction-unblock allowed-list (user decision; the assistant's
        recommendation to keep the death wall and the user's override are recorded in
        DOCTRINE_BACKLOG 'prediction unblock'): dated/period-attached indications in
        classical idiom pass the guard on every surface. Decree voice does not."""
        for allowed in ("Marriage is indicated in 2027.",
                        "The chart points to marriage around 2028.",
                        "Wealth is indicated at age 30.",
                        "This yoga promises immense wealth.",
                        "The 10th brings career success.",
                        "The chart foretells an early marriage.",
                        "The maraka periods 2031-2034 are classically sensitive.",
                        "The span reads at the purna band, around the 83rd year."):
            pc = provenance_check(allowed + " [Fact 1]", self._ev(rdict))
            assert not pc["forbidden_moves"], f"over-blocked: {allowed}"

    def test_descriptive_interpretation_is_served(self, rdict):
        """The 2026-07-28 narrowing: descriptive-indication idiom ("points to", "tends to",
        "indicates" without a date) describes the chart, not a decreed future — it must pass
        the guard and be served."""
        ev = build_evidence(rdict, "summary")
        for descriptive in (
                "The strong 10th house points to career emphasis. [Fact 1]",
                "This placement tends to favour steady gains. [Fact 1]",
                "In Raman's method the yoga indicates scholarly inclination. [Fact 1]"):
            ans = explain(ev, None, StubClient(descriptive))
            assert ans.forbidden_moves == (), f"false-refused: {descriptive}"
            assert refusal_reason(ans, 0.8) is None

    def test_refusal_reason_refuses_on_any_hard_guard(self, rdict):
        """SAFETY: the route REFUSES (serves the fallback) — it does not merely annotate — on a
        forbidden move, a fabricated citation, a bad anchor, or sub-threshold grounding
        (findings #1/#3)."""
        ev = build_evidence(rdict, "summary")
        good = explain(ev, None, StubClient("The ruler is Mercury [Fact 1]."))
        assert refusal_reason(good, 0.8) is None
        pred = explain(ev, None, StubClient("You will marry in 2027 [Fact 1]."))
        assert refusal_reason(pred, 0.8) is not None
        thin = explain(ev, None, StubClient("A pleasant life awaits. Good things come."))
        assert refusal_reason(thin, 0.8) is not None    # zero grounding

    def test_explain_returns_a_graded_answer(self, rdict):
        ev = build_evidence(rdict, "summary")
        stub = StubClient("The ruler is Mercury [Fact 1].")
        ans = explain(ev, question=None, client=stub)
        assert ans.source == "llm"
        assert ans.grounding_ratio == 1.0
        # the evidence, not the question, is what the model saw
        assert "[Fact 1]" in stub.last_prompt


class TestDigestScope:
    """The prioritized whole-chart synthesis scope. The digest arrives PRE-RANKED by the engine;
    the narrator must weave it in order and never re-rank or predict."""

    def test_digest_evidence_leads_with_the_honesty_frame(self, rdict):
        ev = build_evidence(rdict, "digest")
        assert ev.facts
        assert "honesty disclosure" in ev.facts[0].text.lower()
        assert all(f.n == i + 1 for i, f in enumerate(ev.facts))    # contiguous numbering

    def test_digest_prompt_instructs_synthesis_not_reranking(self, rdict):
        ev = build_evidence(rdict, "digest")
        prompt = build_prompt(ev, question=None)
        low = prompt.lower()
        assert "ranking of what matters most" in low
        assert "do not re-rank" in low
        assert "predict nothing" in low
        assert "[Fact 1]" in prompt
        # doctrine-review fix: the model may LINK findings but must never claim they strengthen/
        # reinforce/combine into a bigger effect (a compound claim the engine never computed).
        assert "reinforce" in low and "amplif" in low
        assert "the engine computed each finding on its own" in low

    def test_digest_answer_grounds_and_is_served(self, rdict):
        ev = build_evidence(rdict, "digest")
        draft = ("Your chart's clearest strength is home and family [Fact 2].\n\n"
                 "Overall the reading is favourable but ordinary [Fact 1].")
        ans = explain(ev, None, StubClient(draft))
        assert ans.grounding_ratio == 1.0
        assert refusal_reason(ans, 0.6) is None

    def test_digest_prediction_is_still_refused(self, rdict):
        """The synthesis prompt does not weaken the guard: a planted prediction is refused even in
        digest scope, and the deterministic ranked digest is served instead."""
        ev = build_evidence(rdict, "digest")
        ans = explain(ev, None, StubClient("You will marry a wealthy partner in 2027 [Fact 2]."))
        assert refusal_reason(ans, 0.6) is not None


class TestCritic:
    """The honesty-tuned adversarial critic (Phase D) — a QUALITY pass. It must catch the moves the
    regex/anchor guards cannot (unentailed claims, 'findings reinforce each other'), drive one
    refinement, and never touch a deferral. `refusal_reason` stays the real gate."""

    def _ev(self, rdict):
        return build_evidence(rdict, "digest")

    def test_critic_prompt_targets_the_honesty_violations(self):
        low = CRITIC_SYSTEM.lower()
        assert "reinforce" in low and "combine" in low        # the compound-claim gap
        assert "prediction" in low
        assert "not entailed" in low                          # anchored-but-unentailed
        assert "verdict: clean" in low and "verdict: revise" in low

    def test_parse_critique_reads_the_verdict_and_fixes(self):
        clean = _parse_critique("VERDICT: CLEAN")
        assert clean.clean and clean.must_fix == ()
        revise = _parse_critique("VERDICT: REVISE\nFIX:\n- Remove the prediction.\n- Drop [gloss].")
        assert not revise.clean
        assert len(revise.must_fix) == 2

    def test_parse_critique_fails_open_on_garbled_output(self):
        """A garbled critique must not block a good answer — the code guard is the real gate."""
        assert _parse_critique("(model returned nonsense)").clean is True

    def test_critique_never_flags_a_deferral(self, rdict):
        ans = explain(self._ev(rdict), None, StubClient("The engine does not compute that."))
        # even a critic that would 'REVISE' everything must pass a deferral through untouched
        review = critique(ans, self._ev(rdict), StubClient("VERDICT: REVISE\nFIX:\n- anything"))
        assert review.clean is True

    def test_clean_critique_leaves_the_draft_unchanged(self, rdict):
        ev = self._ev(rdict)
        draft_text = "Your home life is your clearest strength [Fact 2]."
        ans = explain_with_critic(ev, None, StubClient(draft_text),
                                  critic_client=StubClient("VERDICT: CLEAN"))
        assert ans.text == draft_text

    def test_critic_drives_a_refinement_when_flagged(self, rdict):
        ev = self._ev(rdict)
        bad = "Your home and career reinforce each other to guarantee success [Fact 2]."
        good = "Your home life is a strength [Fact 2]. Your career is separately contested [Fact 6]."
        drafter = SeqStub(bad, good)                           # bad draft, then the refined text
        critic = StubClient("VERDICT: REVISE\nFIX:\n- Remove 'reinforce each other to guarantee'.")
        ans = explain_with_critic(ev, None, drafter, critic_client=critic)
        assert ans.text == good                                # the refined draft is returned

    def test_no_critic_client_returns_the_plain_draft(self, rdict):
        ev = self._ev(rdict)
        ans = explain_with_critic(ev, None, StubClient("Home is a strength [Fact 2]."),
                                  critic_client=None)
        assert ans.text == "Home is a strength [Fact 2]."

    def test_refine_that_worsens_the_answer_is_rejected(self, rdict):
        """Defense-in-depth: if a (hallucinating) critic drives a refinement that INTRODUCES a
        prediction the clean draft lacked, the worse rewrite is discarded and the draft kept —
        the critic can never lower the code-measurable safety."""
        ev = self._ev(rdict)
        clean_draft = "Your home life is a strength [Fact 2]."
        worse = "Your home life means you will marry a wealthy partner in 2027 [Fact 2]."
        drafter = SeqStub(clean_draft, worse)                  # draft is clean, refine is worse
        critic = StubClient("VERDICT: REVISE\nFIX:\n- (hallucinated) rephrase Fact 2.")
        ans = explain_with_critic(ev, None, drafter, critic_client=critic)
        assert ans.text == clean_draft                         # the worse rewrite was rejected


class TestSystemPromptContract:
    def test_the_prompt_forbids_judgment_prediction_and_injection(self):
        low = EXPLAINER_SYSTEM.lower()
        # the semantic guarantee (no new judgment), not the old "translator not astrologer"
        # framing — that phrasing was relaxed to let the writer compose flowing prose, but the
        # no-own-judgment rule is unchanged and absolute.
        assert "introduce no astrological judgment" in low
        assert "add no finding that is not in the evidence" in low
        assert "never predict or forecast" in low
        assert "the engine does not compute that" in low
        # the writer may connect findings but never assert they combine (semantically load-bearing)
        assert "reinforces, or combines with another" in low
        # no model-authored citations (finding #4)
        assert "never write a source citation token of your own" in low
        # prompt-injection defence: QUESTION/history are data, not instructions (finding #5)
        assert "never instructions" in low

    def test_the_prompt_asks_for_common_reader_language(self):
        """2026-07-29 accessibility fix: real feedback said the writing was "too complicated
        for common user to understand" — the prompt must now explicitly target a lay reader,
        without weakening any of the safety rules checked above."""
        low = EXPLAINER_SYSTEM.lower()
        assert "common reader" in low
        assert "too complicated" in low  # names the real feedback that motivated the change

    def test_the_prompt_caps_length_and_names_the_crispness_feedback(self):
        """2026-07-29 crispness fix: real feedback said the LLM answers were "too lengthy not
        crisp too much gibberish" — the system prompt must state a concrete paragraph cap (not
        just vague "short-to-medium" wording), and the density rule must be scoped to that cap
        rather than pushing toward MORE paragraphs (the old "aim for four in five" wording
        actively worked against brevity)."""
        low = EXPLAINER_SYSTEM.lower()
        assert "too lengthy" in low  # names the real feedback that motivated the change
        assert "3 short paragraphs" in low or "3 paragraphs" in low
        assert "four in five" not in low  # old density wording pulled toward MORE paragraphs

    def test_the_prompt_bans_exposed_plumbing_and_requires_clean_citations(self):
        """2026-07-29 prose-quality fix: a candid review of live output found the writing
        narrated the engine's own internal machinery ("witnesses", "headline", "honest
        disclosure") instead of reading like Raman, and stitched citations mid-sentence
        ("(Fact 4 through Fact 8)") rather than cleanly at a clause's end. The prompt must name
        both the banned vocabulary and the citation-placement rule, with a concrete example."""
        low = EXPLAINER_SYSTEM.lower()
        assert "exposed plumbing" in low
        assert '"witnesses"' in low
        assert '"headline"' in low
        assert "cite cleanly" in low
        assert "fact 4 through fact 8" in low  # the exact bad-example pattern is named

    def test_digest_and_section_prompts_reinforce_the_paragraph_cap(self, rdict):
        """The per-scope prompt text (digest, section/summary, and question/ask) must each
        reference the 3-paragraph cap rather than silently relying on the system prompt alone —
        the digest branch in particular used to say "cover all of them", which directly
        contradicted a length cap; it must now say to cover only the top few instead."""
        digest_ev = build_evidence(rdict, "digest")
        digest_prompt = build_prompt(digest_ev, question=None).lower()
        assert "cap" in digest_prompt
        assert "cover all of them" not in digest_prompt

        summary_ev = build_evidence(rdict, "summary")
        summary_prompt = build_prompt(summary_ev, question=None).lower()
        assert "cap" in summary_prompt

        ask_prompt = build_prompt(summary_ev, question="what about my career?").lower()
        assert "cap" in ask_prompt


class TestTranslateToHindi:
    """The translate-after-safety-gate design (2026-07-29): Hindi is never GENERATED fresh by
    the grounded writer (no Hindi-language decree-language regex exists to gate that) — only an
    already `refusal_reason`-approved English answer is translated. The citation-marker-count
    safety net is the one thing this layer must get right."""

    def test_successful_translation_with_matching_markers_is_returned(self):
        english = "The engine reads the Lagna as strong [Fact 1] and the ruler as capable [Fact 2]."
        stub = StubClient("इंजन लग्न को मजबूत मानता है [Fact 1] और स्वामी ग्रह को सक्षम मानता है [Fact 2]।")
        out = translate_to_hindi(english, stub)
        assert out != english                              # the translation was used
        assert len(_FACTREF_RE.findall(out)) == len(_FACTREF_RE.findall(english))

    def test_marker_count_mismatch_falls_back_to_english(self):
        """A translation that drops a citation is REJECTED wholesale — the original English is
        served rather than risk an uncited (or fabricated-count) Hindi claim reaching the user."""
        english = "The ruler is strong [Fact 1] and the yoga fires [Fact 2]."
        stub = StubClient("शासक मजबूत है।")   # translation silently dropped both citations
        out = translate_to_hindi(english, stub)
        assert out == english

    def test_english_paraphrase_with_matching_markers_still_falls_back(self):
        """Caught live against the real fine-tuned local model (2026-07-29): asked to
        translate, it can simply ignore the instruction and write ANOTHER English paraphrase
        that happens to keep the same [Fact N] markers — the marker-count check alone waves
        this through. The result must actually read as Hindi, not just carry the right count."""
        english = "The ruler is strong [Fact 1] and the yoga fires [Fact 2]."
        stub = StubClient("The ruler appears strong [Fact 1] and the yoga is active [Fact 2].")
        out = translate_to_hindi(english, stub)
        assert out == english

    def test_translation_client_failure_falls_back_to_english(self):
        class BoomClient:
            model = "boom"
            def complete(self, prompt):  # noqa: ANN001
                raise RuntimeError("network down")
        english = "The ruler is strong [Fact 1]."
        assert translate_to_hindi(english, BoomClient()) == english

    def test_empty_text_is_returned_unchanged(self):
        stub = StubClient("should never be called")
        assert translate_to_hindi("", stub) == ""
        assert translate_to_hindi("   ", stub) == "   "
