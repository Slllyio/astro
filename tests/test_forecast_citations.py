"""Unit tests for app.medini.forecast_citations.

Verifies per-event query construction + the silent-failure contract
(forecast must continue to work if the RAG index is missing).
"""
from __future__ import annotations

from app.medini.forecast_citations import (
    _build_query,
    annotate_events,
    citations_for_event,
)
from app.medini.services.knowledge_search import SearchResult


def _fake_result(chunk_id: str, score: float = 0.5) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id, score=score, source="bphs",
        title=f"BPHS chunk {chunk_id}", snippet="x" * 280,
        source_url=f"http://x/{chunk_id}", local_path=f"/local/{chunk_id}.md",
        artefact_id=f"art-{chunk_id}", topics=("dasha.vimshottari",), n_tokens=100,
    )


class StubService:
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.calls: list[dict] = []
        self.results = results or [_fake_result("c0", 0.9), _fake_result("c1", 0.7)]

    def search(self, query: str, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return tuple(self.results[:kwargs.get("top", 10)])


class RaisingService:
    def search(self, *args, **kwargs):
        raise RuntimeError("index broken")


# --------------------------------------------------------------------------- #
# Query construction                                                           #
# --------------------------------------------------------------------------- #

class TestQueryConstruction:
    def test_ingress_query_names_planet_and_target_sign(self) -> None:
        ev = {"type": "INGRESS", "planet": "Saturn", "to_sign": "Aquarius"}
        q, topic = _build_query(ev)
        assert "Saturn" in q
        assert "Aquarius" in q
        assert "mundane" in q.lower()

    def test_station_query_names_planet_and_target_state(self) -> None:
        ev = {"type": "STATION", "planet": "Mars", "to_state": "retrograde"}
        q, _ = _build_query(ev)
        assert "Mars" in q
        assert "retrograde" in q

    def test_conjunction_query_names_both_planets(self) -> None:
        ev = {"type": "CONJUNCTION", "planet_a": "Jupiter", "planet_b": "Saturn"}
        q, _ = _build_query(ev)
        assert "Jupiter" in q
        assert "Saturn" in q

    def test_new_moon_query_uses_panchanga_topic(self) -> None:
        ev = {"type": "NEW_MOON", "sign": "Aries"}
        q, topic = _build_query(ev)
        assert "new moon" in q.lower() or "amavasya" in q.lower()
        assert topic == "primitives.panchanga"

    def test_full_moon_query_uses_panchanga_topic(self) -> None:
        ev = {"type": "FULL_MOON", "sign": "Libra"}
        q, topic = _build_query(ev)
        assert "purnima" in q.lower() or "full moon" in q.lower()
        assert topic == "primitives.panchanga"

    def test_eclipse_query_names_family_and_nakshatra(self) -> None:
        ev = {"type": "ECLIPSE", "family": "SOLAR", "luminary_nakshatra": "Pushya"}
        q, _ = _build_query(ev)
        assert "solar" in q.lower()
        assert "Pushya" in q
        assert "grahana" in q.lower() or "eclipse" in q.lower()


# --------------------------------------------------------------------------- #
# citations_for_event                                                          #
# --------------------------------------------------------------------------- #

class TestCitationsForEvent:
    def test_returns_list_of_dict_envelopes(self) -> None:
        stub = StubService()
        out = citations_for_event(
            {"type": "INGRESS", "planet": "Saturn", "to_sign": "Aquarius"},
            top=2, service=stub,
        )
        assert isinstance(out, list)
        assert len(out) == 2
        for c in out:
            assert {"source", "title", "snippet", "score"} <= set(c)

    def test_snippet_truncated_to_250_chars(self) -> None:
        stub = StubService()
        out = citations_for_event(
            {"type": "STATION", "planet": "Mars", "to_state": "retrograde"},
            service=stub,
        )
        for c in out:
            assert len(c["snippet"]) <= 260  # 250 + ellipsis padding

    def test_silent_failure_returns_empty(self) -> None:
        """RuntimeError from the service must NOT propagate — forecast page
        keeps rendering with empty citations."""
        out = citations_for_event(
            {"type": "ECLIPSE", "family": "SOLAR"},
            service=RaisingService(),
        )
        assert out == []

    def test_top_propagates_to_service(self) -> None:
        stub = StubService(
            results=[_fake_result(f"c{i}", 0.5) for i in range(5)],
        )
        citations_for_event(
            {"type": "INGRESS", "planet": "Saturn", "to_sign": "Pisces"},
            top=3, service=stub,
        )
        assert stub.calls[0]["top"] == 3


# --------------------------------------------------------------------------- #
# annotate_events                                                              #
# --------------------------------------------------------------------------- #

class TestAnnotateEvents:
    def test_attaches_citations_field(self) -> None:
        stub = StubService()
        events = [
            {"type": "INGRESS", "planet": "Saturn", "to_sign": "Pisces"},
            {"type": "STATION", "planet": "Mars", "to_state": "direct"},
        ]
        out = annotate_events(events, service=stub)
        assert all("citations" in e for e in out)
        assert all(isinstance(e["citations"], list) for e in out)

    def test_one_search_call_per_event(self) -> None:
        stub = StubService()
        events = [
            {"type": "INGRESS", "planet": "Saturn", "to_sign": "Pisces"},
            {"type": "INGRESS", "planet": "Jupiter", "to_sign": "Cancer"},
            {"type": "NEW_MOON", "sign": "Capricorn"},
        ]
        annotate_events(events, service=stub)
        assert len(stub.calls) == 3

    def test_does_not_mutate_inputs(self) -> None:
        stub = StubService()
        orig = {"type": "INGRESS", "planet": "Saturn", "to_sign": "Pisces"}
        annotate_events([orig], service=stub)
        assert "citations" not in orig

    def test_does_not_raise_when_service_broken(self) -> None:
        events = [{"type": "INGRESS", "planet": "Saturn", "to_sign": "Pisces"}]
        out = annotate_events(events, service=RaisingService())
        assert out[0]["citations"] == []
