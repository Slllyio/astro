from __future__ import annotations

import pytest

from tools.raman_saab.golden_pipeline import answers as A

GOOD = {"decision": "CONFIRM", "kind": "conclusion", "verdict": "afflicted",
        "signification": "mother", "decisive_quote": "lost his mother very early in life",
        "quote_line": 6, "reason": "Explicit conclusion."}


class TestParse:
    def test_plain_json_parses(self):
        """A bare JSON reply parses."""
        import json
        assert A.parse(json.dumps(GOOD)) == GOOD

    def test_fenced_json_with_chatter_parses(self):
        """Subagents sometimes wrap JSON in a fence or a sentence."""
        import json
        assert A.parse("Here:\n```json\n" + json.dumps(GOOD) + "\n```") == GOOD

    def test_no_json_raises(self):
        """A reply with no object is invalid, not guessed."""
        with pytest.raises(A.InvalidAnswer):
            A.parse("I think it is afflicted.")


class TestValidate:
    @pytest.mark.parametrize("field,bad", [
        ("decision", "MAYBE"), ("kind", "vibe"), ("verdict", "great"),
        ("signification", ""), ("quote_line", "six"), ("reason", 3)])
    def test_bad_field_rejected(self, field, bad):
        """Each schema field is enforced."""
        with pytest.raises(A.InvalidAnswer):
            A.validate({**GOOD, field: bad})

    def test_quote_over_40_words_rejected(self):
        """Long 'quotes' are paraphrase cover; cap at 40 words."""
        with pytest.raises(A.InvalidAnswer):
            A.validate({**GOOD, "decisive_quote": "word " * 41})

    def test_reject_may_omit_verdict(self):
        """A REJECT need not assert a verdict."""
        A.validate({**GOOD, "decision": "REJECT", "kind": "observation", "verdict": None})


class TestValidateHardening:
    @pytest.mark.parametrize("decision", ["CONFIRM", "REVISE"])
    def test_accept_requires_conclusion_kind(self, decision):
        """Only a CONCLUSION may be confirmed; an observation is not a verdict."""
        with pytest.raises(A.InvalidAnswer):
            A.validate({**GOOD, "decision": decision, "kind": "observation"})

    def test_bool_quote_line_rejected(self):
        """bool is an int subclass but never a line number."""
        with pytest.raises(A.InvalidAnswer):
            A.validate({**GOOD, "quote_line": True})

    @pytest.mark.parametrize("q", ["", "   "])
    def test_blank_quote_rejected(self, q):
        """An empty quote cannot be source-verified."""
        with pytest.raises(A.InvalidAnswer):
            A.validate({**GOOD, "decisive_quote": q})
