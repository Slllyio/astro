"""v1.2.0 tests: llm_polish_master_reading.

Uses ScriptedLLM stub returning fixed paragraphs so tests stay
deterministic without requiring Ollama / Claude / OpenAI.
"""

from __future__ import annotations

import pytest

from app.integration.llm_master import (
    PolishedDomain,
    PolishedMasterReading,
    _scrub_banned_words,
    llm_polish_master_reading,
)
from app.integration.master_compose import compose_master_reading
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


class ScriptedLLM:
    """Deterministic LLM stub for tests."""

    def __init__(self, response: str = "Polished prose paragraph."):
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


@pytest.fixture(scope="module")
def mainpuri_master():
    reading = track_a_compute(
        ChartInput(dob="1989-10-12", time="10:02", tz="+05:30",
                   lat=27.23, lon=79.03),
        enrich=False,
    )
    return compose_master_reading(reading)


# ---------------------------------------------------------------------------
# Banned-word scrub
# ---------------------------------------------------------------------------

class TestScrubBannedWords:
    def test_will_replaced_with_may(self):
        out = _scrub_banned_words("The native will succeed")
        assert "will" not in out
        assert "may" in out

    def test_guaranteed_replaced_with_indicated(self):
        out = _scrub_banned_words("Success is guaranteed in this period")
        assert "guaranteed" not in out
        assert "indicated" in out

    def test_definitely_replaced(self):
        out = _scrub_banned_words("He will definitely become wealthy")
        assert "definitely" not in out
        assert "classically" in out

    def test_certainly_replaced(self):
        out = _scrub_banned_words("The marriage will certainly happen")
        assert "certainly" not in out
        assert "typically" in out

    def test_text_without_banned_words_unchanged(self):
        text = "The native shows analytical tendencies during this period."
        assert _scrub_banned_words(text) == text


# ---------------------------------------------------------------------------
# llm_polish_master_reading basics
# ---------------------------------------------------------------------------

class TestPolishStructure:
    def test_returns_polished_master_reading(self, mainpuri_master):
        llm = ScriptedLLM("Sample polished paragraph.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        assert isinstance(result, PolishedMasterReading)

    def test_version_pinned(self, mainpuri_master):
        llm = ScriptedLLM("Sample.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        assert result.integration_version == "1.2.0"

    def test_six_polished_domains(self, mainpuri_master):
        llm = ScriptedLLM("Sample.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        assert len(result.polished_domains) == 6

    def test_chart_basics_preserved(self, mainpuri_master):
        llm = ScriptedLLM("Sample.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        assert result.chart_basics["lagna_sign_name"] == "Scorpio"

    def test_default_llm_is_stub(self, mainpuri_master):
        """No llm passed -> StubClient is used, so result has provider StubClient."""
        result = llm_polish_master_reading(mainpuri_master)
        assert result.llm_provider == "StubClient"


# ---------------------------------------------------------------------------
# LLM is actually called
# ---------------------------------------------------------------------------

class TestLLMCalls:
    def test_overview_calls_llm(self, mainpuri_master):
        llm = ScriptedLLM("Overview.")
        llm_polish_master_reading(mainpuri_master, llm=llm)
        # 6 domains + overview + dasha + arudha + upapada = 10 calls
        assert len(llm.prompts) == 10

    def test_skip_polishing_reduces_calls(self, mainpuri_master):
        llm = ScriptedLLM("X.")
        llm_polish_master_reading(
            mainpuri_master, llm=llm,
            polish_domains=False, polish_dasha_triple=False,
            polish_arudha=False, polish_upapada=False,
            include_overview=False,
        )
        assert len(llm.prompts) == 0

    def test_total_prompt_chars_tracked(self, mainpuri_master):
        llm = ScriptedLLM("X.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        assert result.total_prompt_chars > 0


# ---------------------------------------------------------------------------
# Prompts include the ground truth
# ---------------------------------------------------------------------------

class TestPromptContent:
    def test_domain_prompt_includes_template_rough_draft(self, mainpuri_master):
        llm = ScriptedLLM("X.")
        llm_polish_master_reading(mainpuri_master, llm=llm)
        # Find the career prompt
        career_prompts = [p for p in llm.prompts if "CAREER" in p.upper()]
        assert len(career_prompts) >= 1
        # Should include the M8 rough-draft paragraph
        career_dp = next(dp for dp in mainpuri_master.domain_paragraphs if dp.domain == "career")
        # At least a substring of the rough draft should be in the prompt
        first_30_chars = career_dp.paragraph[:50]
        assert first_30_chars in career_prompts[0]

    def test_dasha_prompt_includes_master_dasha_paragraph(self, mainpuri_master):
        llm = ScriptedLLM("X.")
        llm_polish_master_reading(mainpuri_master, llm=llm)
        dasha_prompt = next(p for p in llm.prompts if "dasha" in p.lower())
        assert "SATURN" in dasha_prompt.upper() or "Saturn" in dasha_prompt

    def test_prompts_include_banned_word_rules(self, mainpuri_master):
        llm = ScriptedLLM("X.")
        llm_polish_master_reading(mainpuri_master, llm=llm)
        for p in llm.prompts:
            # Every prompt enforces the banned-word ban
            assert "will" in p.lower()  # in the rules text
            assert "guaranteed" in p.lower()


# ---------------------------------------------------------------------------
# Output preserves original template + polished
# ---------------------------------------------------------------------------

class TestPolishedDomainStructure:
    def test_template_preserved_alongside_polished(self, mainpuri_master):
        llm = ScriptedLLM("This is the polished version.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        for pd in result.polished_domains:
            assert isinstance(pd, PolishedDomain)
            # Both fields populated
            assert pd.template_paragraph != ""
            assert pd.polished_paragraph != ""

    def test_polished_text_matches_llm_response(self, mainpuri_master):
        llm = ScriptedLLM("Sample polished text.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        # All polished paragraphs should be the stub response (after scrub)
        for pd in result.polished_domains:
            assert "Sample polished text" in pd.polished_paragraph


# ---------------------------------------------------------------------------
# Banned-word scrubbing applied to LLM output
# ---------------------------------------------------------------------------

class TestBannedWordsScrubFromLLM:
    def test_llm_outputting_will_gets_scrubbed(self, mainpuri_master):
        """Even if LLM ignores the ban, the post-scrub catches it."""
        llm = ScriptedLLM("The native will achieve recognition.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        for pd in result.polished_domains:
            assert "will" not in pd.polished_paragraph

    def test_llm_outputting_definitely_gets_scrubbed(self, mainpuri_master):
        llm = ScriptedLLM("Career success is definitely indicated.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        for pd in result.polished_domains:
            assert "definitely" not in pd.polished_paragraph


# ---------------------------------------------------------------------------
# Error handling — LLM failures fall back to template
# ---------------------------------------------------------------------------

class FailingLLM:
    def complete(self, prompt: str) -> str:
        raise RuntimeError("simulated LLM failure")


class TestLLMFailureFallback:
    def test_domain_polish_falls_back_to_template_on_llm_error(self, mainpuri_master):
        """When LLM throws, polished_paragraph falls back to template_paragraph."""
        llm = FailingLLM()
        # Skip overview / dasha / arudha (they'd also fail, but currently raise);
        # ensure domain-level failure is handled gracefully.
        try:
            result = llm_polish_master_reading(
                mainpuri_master, llm=llm,
                polish_domains=True,
                polish_dasha_triple=False,
                polish_arudha=False,
                polish_upapada=False,
                include_overview=False,
            )
        except RuntimeError:
            # If the implementation doesn't catch at the domain level either,
            # that's a behaviour decision; current code DOES catch per-domain.
            pytest.fail("Expected per-domain LLM failure to fall back, not raise")
        for pd in result.polished_domains:
            assert pd.polished_paragraph == pd.template_paragraph


# ---------------------------------------------------------------------------
# JSON roundtrip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_json_roundtrip(self, mainpuri_master):
        import json
        llm = ScriptedLLM("Polished.")
        result = llm_polish_master_reading(mainpuri_master, llm=llm)
        text = json.dumps(result.model_dump(mode="json"))
        revived = PolishedMasterReading.model_validate(json.loads(text))
        assert revived.integration_version == "1.2.0"
        assert len(revived.polished_domains) == 6
