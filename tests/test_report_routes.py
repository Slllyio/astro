"""Integration tests for the /report/* endpoints — the FastAPI surface over
`detailed_report.build_detailed_report`. Uses the app-bound httpx client fixture. The birth
is the canonical Bangalore 1990 baseline (CLAUDE.md), so the response must reproduce its
pinned facts (Virgo lagna, Mercury/Sun ruler) end to end over HTTP.
"""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

_BIRTH = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5, "ayanamsa": "lahiri",
}


class TestSections:
    @pytest.mark.asyncio
    async def test_lists_the_section_contract(self, client):
        resp = await client.get("/report/sections")
        assert resp.status_code == 200
        body = resp.json()
        ids = [s["id"] for s in body["sections"]]
        assert body["count"] == len(ids)
        # the synthesis sections added this arc are present, in document order
        for sid in ("ruler", "house_strength", "preponderance", "life_chapters", "nichod"):
            assert sid in ids
        assert ids.index("ruler") < ids.index("preponderance") < ids.index("nichod")


class TestReport:
    @pytest.mark.asyncio
    async def test_markdown_report_reproduces_canonical_facts(self, client):
        """End-to-end over HTTP: the Markdown report carries the pinned canonical facts and the
        structured summary agrees with the prose."""
        resp = await client.post("/report", json=_BIRTH)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "markdown" and body["ayanamsa"] == "lahiri"
        assert "# Detailed reading" in body["report"]
        assert "## Ruler of the nativity" in body["report"]
        assert "## Preponderance of testimonies" in body["report"]
        s = body["summary"]
        assert s["lagna"] == "Virgo"
        assert s["ruler_of_nativity"]["lagna_lord"] == "Mercury"
        assert s["ruler_of_nativity"]["strongest_planet"] == "Sun"
        assert s["longevity"]["class"] in {"alpa", "madhya", "purna"}

    @pytest.mark.asyncio
    async def test_html_format_returns_a_standalone_document(self, client):
        resp = await client.post("/report", json={**_BIRTH, "format": "html"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "html"
        assert "<!doctype html>" in body["report"].lower() or "<html" in body["report"].lower()
        assert 'id="ruler"' in body["report"]

    @pytest.mark.asyncio
    async def test_window_params_are_accepted(self, client):
        resp = await client.post("/report", json={**_BIRTH, "years_back": 5, "years_forward": 5})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rejects_unsupported_ayanamsa(self, client):
        resp = await client.post("/report", json={**_BIRTH, "ayanamsa": "kp"})
        assert resp.status_code == 422        # pydantic Literal rejects before the handler

    @pytest.mark.asyncio
    async def test_rejects_unknown_field(self, client):
        resp = await client.post("/report", json={**_BIRTH, "bogus": 1})
        assert resp.status_code == 422        # extra="forbid"

    @pytest.mark.asyncio
    async def test_json_format_returns_the_structured_report(self, client):
        """format=json returns the structured grounding contract, not a rendered string."""
        resp = await client.post("/report", json={**_BIRTH, "format": "json"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "json"
        rep = body["report"]
        assert isinstance(rep, dict)
        assert rep["ruler"]["lagna_lord"] == "Mercury"
        assert len(rep["house_strength"]) == 12
        assert rep["yogas"][0]["source"].keys() >= {"work", "line"}


class TestPage:
    @pytest.mark.asyncio
    async def test_report_page_serves_the_interactive_shell(self, client):
        """GET /report/page returns the static shell wired to POST /report?format=json and the
        /report/source click-to-source backend."""
        resp = await client.get("/report/page")
        assert resp.status_code == 200
        html = resp.text
        assert "<!DOCTYPE html>" in html
        assert "fetch('/report'" in html          # client fetches the JSON report
        assert "/report/source" in html            # click-to-source wiring
        assert "format:'json'" in html or 'format:"json"' in html
        # the page must render EVERY section of the full report — not a curated subset
        for heading in ("Your Reading", "Chart signature", "Ruler of the nativity",
                        "Planetary positions", "Yogas", "Ashtakavarga", "House-by-house",
                        "House strength cross-check", "Preponderance of testimonies",
                        "The twelve matters", "Longevity", "Life-narrative", "Life-chapters",
                        "Transits", "Divisional deep-reads", "Soul & destiny", "Pitru dosha",
                        "Integrated insights", "What stands out", "Information content",
                        "Nichod"):
            assert heading in html, f"interactive page dropped section: {heading}"
        # the grounded explainer + Q&A wiring is present
        assert "/report/explain" in html and "/report/ask" in html
        assert "never a prediction" in html
        # the "What matters most" digest panel + its grounded synthesis wiring
        assert "What matters most" in html
        assert "/report/insights" in html
        assert "Read this as one story" in html
        # the Pothi-manuscript book design: shared engine + 13 leaves + labels + cover
        assert "/static/css/manuscript.css" in html and "/static/js/manuscript.js" in html
        assert 'data-page="0"' in html and 'data-page="12"' in html   # cover..colophon
        assert "MANUSCRIPT_LABELS" in html
        assert "cover-deva-title" in html                              # the brushed-gold cover


class TestSource:
    @needs_corpus
    @pytest.mark.asyncio
    async def test_resolves_a_canon_citation_to_verbatim_lines(self, client):
        """A Raman-canon citation token returns the exact source lines (click-to-source)."""
        resp = await client.get("/report/source", params={"cite": "HTJAH-I:468-478"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["resolved"] is True
        assert body["work"] == "HTJAH-I" and body["start"] == 468 and body["end"] == 478
        assert "strength of the house" in body["text"].lower()

    @pytest.mark.asyncio
    async def test_classical_noncitable_is_deferred_not_shown(self, client):
        """A CLASSICAL_NONCITABLE token (BPHS) is not resolved — the firewall holds — and the
        response says so truthfully rather than returning the verse."""
        resp = await client.get("/report/source", params={"cite": "BPHS-83-iii:70"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["resolved"] is False
        assert "classical" in body["note"].lower()

    @pytest.mark.asyncio
    async def test_malformed_cite_is_handled(self, client):
        resp = await client.get("/report/source", params={"cite": "not-a-citation"})
        assert resp.status_code == 200 and resp.json()["resolved"] is False


class TestExplainAndAsk:
    """The grounded LLM endpoints. In CI the LLM is disabled (no key), so both must serve the
    truthful deterministic fallback — never a fabricated explanation, always the honesty note."""

    @pytest.mark.asyncio
    async def test_explain_falls_back_to_engine_prose_without_a_key(self, client):
        resp = await client.post("/report/explain", json={**_BIRTH, "scope": "house:1"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert "not a validated prediction" in body["honesty_note"].lower()
        assert "House 1 reads" in body["text"]

    @pytest.mark.asyncio
    async def test_explain_summary_scope(self, client):
        resp = await client.post("/report/explain", json={**_BIRTH, "scope": "summary"})
        assert resp.status_code == 200
        assert resp.json()["source"] == "fallback"
        assert resp.json()["text"]

    @pytest.mark.asyncio
    async def test_ask_falls_back_and_carries_the_honesty_note(self, client):
        resp = await client.post("/report/ask",
                                 json={**_BIRTH, "question": "why is my career contested?"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert body["honesty_note"]

    @pytest.mark.asyncio
    async def test_ask_requires_a_question(self, client):
        resp = await client.post("/report/ask", json={**_BIRTH})
        assert resp.status_code == 422        # question is required

    @pytest.mark.asyncio
    async def test_insights_falls_back_to_the_ranked_digest(self, client):
        """The prioritized whole-chart synthesis. With no key it must serve the engine's OWN ranked
        digest as prose — the honesty headline plus the ranked items — never a fabricated reading."""
        resp = await client.post("/report/insights", json={**_BIRTH})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert "not a validated prediction" in body["honesty_note"].lower()
        assert "readings" in body["text"]            # the info-content headline is present
        assert len(body["text"]) > 100               # the ranked items, not an empty stub


class TestGroundedReportSurfaces:
    """/report/insights and /report/explain write in the grounded LLM voice again as of
    2026-07-29 — the earlier deterministic-only cost cut existed only because the Anthropic
    API cost money; now the app's own fine-tuned model (astro-analyst, served free by the
    local Ollama backend) writes them, so there's no longer a reason to keep them
    deterministic-only. All three LLM surfaces (insights/explain/ask) must still degrade
    gracefully to the engine's own deterministic prose when the model is disabled/unavailable
    — never a 500."""

    @pytest.mark.asyncio
    async def test_insights_and_explain_attempt_a_model_call(self, client, monkeypatch):
        """With the LLM enabled, both endpoints now DO construct a model client (the reverse
        of the old cost-cut pin) — proven by a client factory that raises when touched."""
        import app.api.report_routes as rr
        from app.core.config import settings
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)

        calls = []

        def _spy(system, **kwargs):  # noqa: ANN001
            calls.append(system)
            raise RuntimeError("stop before any real network call")

        monkeypatch.setattr(rr, "_make_client", _spy)
        r1 = await client.post("/report/insights", json=_BIRTH)
        r2 = await client.post("/report/explain", json={**_BIRTH, "scope": "summary"})
        assert len(calls) == 2                          # both endpoints reached the client factory
        # a client-construction failure still degrades to the deterministic fallback, not a 500
        assert r1.status_code == 200 and r1.json()["source"] == "fallback"
        assert r2.status_code == 200 and r2.json()["source"] == "fallback"

    @pytest.mark.asyncio
    async def test_insights_and_explain_degrade_when_ollama_is_down(self, client, monkeypatch):
        """The default local backend with no Ollama daemon: both endpoints degrade to the
        deterministic fallback (200 + engine prose), never a 500 — same contract as /report/ask."""
        from app.core.config import settings
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        monkeypatch.setattr(settings, "REPORT_LLM_BACKEND", "ollama")
        monkeypatch.setattr(settings, "OLLAMA_HOST", "http://127.0.0.1:9")   # nothing listens
        r1 = await client.post("/report/insights", json=_BIRTH)
        r2 = await client.post("/report/explain", json={**_BIRTH, "scope": "summary"})
        assert r1.status_code == 200 and r1.json()["source"] == "fallback"
        assert r2.status_code == 200 and r2.json()["source"] == "fallback"

    @pytest.mark.asyncio
    async def test_ask_with_ollama_backend_down_degrades_to_fallback(self, client, monkeypatch):
        """The default local backend with no Ollama daemon: /report/ask degrades to the
        deterministic fallback (200 + engine prose), never a 500."""
        from app.core.config import settings
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        monkeypatch.setattr(settings, "REPORT_LLM_BACKEND", "ollama")
        monkeypatch.setattr(settings, "OLLAMA_HOST", "http://127.0.0.1:9")   # nothing listens
        resp = await client.post("/report/ask", json={**_BIRTH, "question": "career?"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["source"] == "fallback"

    def test_system_prompt_wrapper_prepends_system(self):
        """SystemPromptWrapper carries the pipeline system prompt into system-less clients."""
        from app.llm.client import StubClient, SystemPromptWrapper
        stub = StubClient("ok")
        w = SystemPromptWrapper(stub, "SYSTEM RULES")
        assert w.complete("the prompt") == "ok"
        assert stub.last_prompt is not None
        assert stub.last_prompt.startswith("SYSTEM RULES\n\n")
        assert stub.last_prompt.endswith("the prompt")


class TestHindiLanguage:
    """lang='hi' (2026-07-29): the grounded surfaces translate an already safety-approved
    English answer into Hindi — they never generate fresh Hindi analysis. Covers the wiring
    in `_grounded`, not `translate_to_hindi` itself (see test_report_explainer.py)."""

    @pytest.mark.asyncio
    async def test_lang_hi_without_llm_notes_hindi_needs_the_model(self, client):
        """LLM disabled entirely: no client exists to translate with, so the response stays
        English and says so explicitly rather than silently ignoring the language request."""
        resp = await client.post("/report/insights", json={**_BIRTH, "lang": "hi"})
        assert resp.status_code == 200
        assert resp.json()["source"] == "fallback"
        assert "Hindi needs the LLM enabled" in resp.json()["note"]

    @pytest.mark.asyncio
    async def test_lang_hi_translates_a_served_answer(self, client, monkeypatch):
        """A clean, guard-passing English answer gets ONE more pass through
        translate_to_hindi before being served — proven with a client that recognizes
        translate_to_hindi's own prompt shape ("ENGLISH TEXT:") and returns a fixed Hindi
        string carrying the SAME fact-marker count as the English draft. Content-based (not
        call-count-based): the explainer and translation clients are now separate instances
        (_translation_client builds its own, unbound-system client — see its docstring for
        why reusing the explainer's client broke real Hindi translation), so a test that
        distinguished them by shared call order would no longer reflect reality."""
        import app.api.report_routes as rr
        from app.core.config import settings
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)

        english = "The ruler is Mercury [Fact 1]."
        hindi = "स्वामी ग्रह बुध है [Fact 1]।"

        class PromptAwareClient:
            model = "stub"
            def complete(self, prompt):  # noqa: ANN001
                return hindi if "ENGLISH TEXT:" in prompt else english

        monkeypatch.setattr(rr, "_make_client", lambda system, **kwargs: PromptAwareClient())
        resp = await client.post("/report/explain",
                                 json={**_BIRTH, "scope": "summary", "lang": "hi"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["text"] == hindi

    @pytest.mark.asyncio
    async def test_translation_client_is_built_without_the_explainer_system_prompt(
            self, client, monkeypatch):
        """Regression pin for the exact bug caught live against the real fine-tuned model:
        translate_to_hindi must run on a client built with an EMPTY system prompt, not the
        explainer's bound client (`_make_client(EXPLAINER_SYSTEM)`). Stacking "write grounded
        chart analysis" underneath "translate this to Hindi" made a real local model just write
        more English — text that still carried matching [Fact N] markers, so the marker-count
        check alone didn't catch it. Asserts `_make_client` is invoked at least once with an
        empty system string (the translation client) alongside the non-empty EXPLAINER_SYSTEM
        call (the explain client)."""
        import app.api.report_routes as rr
        from app.core.config import settings
        from app.llm.client import StubClient
        from app.llm.report_explainer import EXPLAINER_SYSTEM
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)

        hindi = "स्वामी ग्रह बुध है [Fact 1]।"
        seen_systems: list[str] = []

        def fake_make_client(system, **kwargs):
            seen_systems.append(system)
            return StubClient(hindi if system == "" else "The ruler is Mercury [Fact 1].")

        monkeypatch.setattr(rr, "_make_client", fake_make_client)
        resp = await client.post("/report/explain",
                                 json={**_BIRTH, "scope": "summary", "lang": "hi"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["text"] == hindi
        assert "" in seen_systems, "translate_to_hindi's client was never built with an empty system"
        assert EXPLAINER_SYSTEM in seen_systems, "the explain call itself should still bind EXPLAINER_SYSTEM"

    @pytest.mark.asyncio
    async def test_lang_hi_leaves_refused_fallback_translatable(self, client, monkeypatch):
        """A refused (prediction-language) LLM answer still serves the deterministic
        fallback — and the code path attempts to translate that fallback too when
        lang='hi', using the same (already-constructed) client the refused answer came
        from. A StubClient always returns its one canned reply regardless of the prompt
        it's given, so the "translation" it returns here carries a DIFFERENT fact-marker
        count than the fallback text — proving translate_to_hindi's safety net rejects it
        and the response still degrades cleanly to the engine's own English text, not a
        500 or a corrupted answer."""
        import app.api.report_routes as rr
        from app.core.config import settings
        from app.llm.client import StubClient
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        monkeypatch.setattr(rr, "_make_client",
                            lambda system, **kwargs: StubClient("You will marry in 2027 [Fact 1]."))
        resp = await client.post("/report/ask",
                                 json={**_BIRTH, "question": "career?", "lang": "hi"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "fallback" and body.get("refused_llm") is True
        assert isinstance(body["text"], str) and len(body["text"]) > 0
        # honesty rule (CLAUDE.md report-completeness: "no silent approximation"): Hindi was
        # requested but the served text is still English, so that must be disclosed, not
        # silently absorbed into an English answer with no indication anything was skipped.
        assert "Hindi translation wasn't available" in body.get("note", "")

    @pytest.mark.asyncio
    async def test_lang_hi_success_path_notes_when_translation_silently_fails(
            self, client, monkeypatch):
        """Mirrors the refused-fallback case above, but for a CLEAN (non-refused) LLM answer:
        if translate_to_hindi's safety nets reject the translation, the served text stays
        English — and the response must say so, not stay silent about the mismatch between
        what was requested (Hindi) and what was served (English)."""
        import app.api.report_routes as rr
        from app.core.config import settings
        from app.llm.client import StubClient
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        english = "The ruler is Mercury [Fact 1]."
        # Always returns the SAME text regardless of prompt — the "translation" call gets the
        # identical English string back, which is neither a marker-count mismatch (same text,
        # same markers) nor obviously not-Hindi-shaped in a way marker-count alone would catch,
        # but IS caught by _looks_like_hindi (no Devanagari at all).
        monkeypatch.setattr(rr, "_make_client", lambda system, **kwargs: StubClient(english))
        resp = await client.post("/report/explain",
                                 json={**_BIRTH, "scope": "summary", "lang": "hi"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["text"] == english
        assert "Hindi translation wasn't available" in body.get("note", "")

    def test_report_request_accepts_lang_field(self):
        """lang defaults to 'en' and only accepts the two supported values."""
        from app.api.report_routes import ReportRequest
        assert ReportRequest(**_BIRTH).lang == "en"
        assert ReportRequest(**{**_BIRTH, "lang": "hi"}).lang == "hi"
        with pytest.raises(Exception):
            ReportRequest(**{**_BIRTH, "lang": "fr"})
