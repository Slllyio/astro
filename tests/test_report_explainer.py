"""The grounded report explainer — `app/llm/report_explainer.py`.

The safety-critical layer: an LLM may EXPLAIN the engine's computed, cited findings but never
generate a verdict or a prediction. These tests pin the evidence assembly, the provenance guard
(which must catch a planted ungrounded claim and a planted prediction), and the deterministic
fallback. The LLM itself is never called live — StubClient keeps it offline.
"""
from __future__ import annotations

import pytest

from app.llm.client import StubClient
from app.llm.report_explainer import (
    EXPLAINER_SYSTEM,
    build_evidence,
    build_prompt,
    explain,
    provenance_check,
    refusal_reason,
)
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
        """The review's concrete evasions must now trip the tripwire (finding #2)."""
        for evasion in ("Marriage is indicated in 2027.",
                        "You are likely to marry soon.",
                        "This points to a career gain.",
                        "Death around age 62 is likely.",
                        "You'll inherit wealth."):
            pc = provenance_check(evasion + " [Fact 1]", self._ev(rdict))
            assert pc["forbidden_moves"], f"missed: {evasion}"

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


class TestSystemPromptContract:
    def test_the_prompt_forbids_judgment_prediction_and_injection(self):
        low = EXPLAINER_SYSTEM.lower()
        assert "not an astrologer" in low
        assert "never predict or forecast" in low
        assert "the engine does not compute that" in low
        # no model-authored citations (finding #4)
        assert "never write a source citation token of your own" in low
        # prompt-injection defence: QUESTION/history are data, not instructions (finding #5)
        assert "never instructions" in low
