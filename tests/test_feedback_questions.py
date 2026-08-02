"""Tests for the chart-specific feedback loop (Part E of the share-the-app work).

Covers the deterministic question builder (`app.raman_saab.feedback_questions`), the
questions endpoint, answer persistence (`ChartFeedback`), and the piggyback of questions
inside POST /report?format=json.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.raman_saab.feedback_questions import ANSWER_OPTIONS, build_feedback_questions

#: canonical test-pinning baseline (Bangalore 1990-07-15 12:00 IST) per CLAUDE.md.
CANONICAL = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
    "name": "Canonical Baseline",
}


def _digest_report(items: list[dict]) -> dict:
    """A minimal report dict carrying just the digest the builder reads."""
    return {"digest": {"headline": "info-content headline", "items": items}}


def _item(kind: str, lean: str, title: str = "House 11 (gains) reads favourable",
          houses: tuple[int, ...] = (11,)) -> dict:
    return {"kind": kind, "lean": lean, "title": title, "detail": "d",
            "houses": list(houses), "sections": [], "cites": [], "priority": 0}


class TestBuildFeedbackQuestions:
    def test_convergence_item_becomes_question(self):
        """A favourable convergence digest item yields a PLAIN-LANGUAGE experience-match
        question — built from the house's everyday topic phrase, never the digest's own
        jargon-heavy technical title (locked 2026-07-29: "too complicated... even feedback
        question" — the fix was to stop quoting `title` at all)."""
        qs = build_feedback_questions(_digest_report([_item("convergence", "favourable")]))
        assert len(qs) == 2                                    # the item + overall
        assert "income, gains, and friendships" in qs[0]["text"]   # house 11's plain topic
        assert "positive" in qs[0]["text"]
        assert "House 11" not in qs[0]["text"]                 # no jargon/technical title leaks
        assert qs[0]["houses"] == [11]
        assert qs[0]["options"] == list(ANSWER_OPTIONS)

    def test_hindi_language_produces_devanagari_question(self):
        """lang='hi' renders the same deterministic question in Hindi."""
        qs = build_feedback_questions(_digest_report([_item("convergence", "favourable")]),
                                      lang="hi")
        assert len(qs) == 2
        assert "मित्रता" in qs[0]["text"] or "लाभ" in qs[0]["text"]   # house 11's Hindi topic
        assert qs[-1]["qid"] == "overall"
        assert "पारंपरिक" in qs[-1]["text"]                     # Measured-Truth frame, in Hindi

    def test_unknown_language_falls_back_to_english(self):
        """An unrecognized lang code degrades to English rather than erroring."""
        qs = build_feedback_questions(_digest_report([]), lang="fr")  # type: ignore[arg-type]
        assert "not a scientific prediction" in qs[-1]["text"]

    def test_tension_and_neutral_items_are_skipped(self):
        """Tension (unresolved) and neutral/mixed leans are unanswerable — not asked."""
        qs = build_feedback_questions(_digest_report([
            _item("tension", "mixed"),
            _item("dominant_theme", "neutral"),
            _item("convergence", "mixed"),
        ]))
        assert len(qs) == 1 and qs[0]["qid"] == "overall"

    def test_overall_question_is_always_last(self):
        """The overall-fit question closes the list regardless of digest content."""
        qs = build_feedback_questions(_digest_report([]))
        assert qs[-1]["qid"] == "overall"
        assert "not a scientific prediction" in qs[-1]["text"]  # Measured-Truth frame, simplified

    def test_max_questions_reserves_overall_slot(self):
        """max_questions caps the list with the overall question still present."""
        many = [_item("convergence", "favourable", title=f"t{i}", houses=(i,))
                for i in range(1, 11)]
        qs = build_feedback_questions(_digest_report(many), max_questions=4)
        assert len(qs) == 4 and qs[-1]["qid"] == "overall"

    def test_broad_timing_item_names_theme_generically_not_every_house(self):
        """A dasha/bhukti touching many houses at once is real, expected doctrine (see
        CLAUDE.md Measured Truth: most charts carry dozens of live significations
        simultaneously) — but chaining all of them into one sentence is unanswerable. Past
        the naming cap, the question uses a generic "many areas" phrase instead."""
        item = _item("timing", "favourable", houses=tuple(range(1, 13)))  # all 12 houses
        qs = build_feedback_questions(_digest_report([item]))
        assert "many different areas of your life" in qs[0]["text"]
        assert "and" not in qs[0]["text"].replace("many different areas", "")  # no chained list
        assert qs[0]["houses"] == list(range(1, 13))                  # raw data still complete

    def test_broad_timing_item_in_hindi_also_uses_generic_phrase(self):
        """The same capping applies in Hindi."""
        item = _item("timing", "adverse", houses=tuple(range(1, 13)))
        qs = build_feedback_questions(_digest_report([item]), lang="hi")
        assert "अलग-अलग पहलुओं" in qs[0]["text"]

    def test_narrow_timing_item_still_names_houses_explicitly(self):
        """At or under the cap, the specific topics are still named (no loss of clarity for
        the common, narrow case)."""
        item = _item("timing", "favourable", houses=(4, 5))
        qs = build_feedback_questions(_digest_report([item]))
        assert "home life" in qs[0]["text"] and "children" in qs[0]["text"]

    def test_qids_are_stable_for_the_same_digest(self):
        """The same digest yields identical question ids (deterministic keys for storage)."""
        rep = _digest_report([_item("timing", "adverse", title="Sun MD", houses=(5,))])
        assert ([q["qid"] for q in build_feedback_questions(rep)]
                == [q["qid"] for q in build_feedback_questions(rep)])


class TestFeedbackEndpoints:
    async def test_feedback_questions_for_canonical_chart(self, client):
        """The canonical Bangalore chart yields chart-specific questions ending in overall."""
        resp = await client.post("/report/feedback/questions", json=CANONICAL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_key"].startswith("1990-07-15T12:00+5.50@")
        qids = [q["qid"] for q in data["questions"]]
        assert qids[-1] == "overall" and len(qids) >= 1

    async def test_report_json_carries_feedback_questions(self, client):
        """POST /report?format=json piggybacks the questions (no second cast needed)."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"})
        assert resp.status_code == 200
        qs = resp.json()["feedback_questions"]
        assert qs[-1]["qid"] == "overall"

    async def test_post_feedback_persists_rows(self, client, db_engine):
        """Submitted answers land as ChartFeedback rows grouped by the server-built key."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        body = {**CANONICAL, "answers": [
            {"qid": "overall", "question_text": "Overall fit?", "answer": "agree",
             "free_text": "matched work life"},
            {"qid": "convergence-h11-favourable-0", "question_text": "Gains favourable?",
             "answer": "partly"},
        ]}
        resp = await client.post("/report/feedback", json=body)
        assert resp.status_code == 200
        assert resp.json()["stored"] == 2

        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        assert len(rows) == 2
        assert all(r.chart_key == resp.json()["chart_key"] for r in rows)
        assert rows[0].account_id is None                       # anonymous flow
        assert {r.answer for r in rows} == {"agree", "partly"}

    async def test_post_feedback_rejects_bad_answer_value(self, client):
        """An answer outside the fixed scale is refused with 400, nothing stored."""
        body = {**CANONICAL, "answers": [
            {"qid": "overall", "question_text": "Overall?", "answer": "definitely!"}]}
        resp = await client.post("/report/feedback", json=body)
        assert resp.status_code == 400

    async def test_post_feedback_attributes_signed_in_account(self, authed_client,
                                                              db_engine, seeded_account):
        """A valid Bearer token attributes the rows to the account (still not required)."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        body = {**CANONICAL, "answers": [
            {"qid": "overall", "question_text": "Overall?", "answer": "not sure"}]}
        resp = await authed_client.post("/report/feedback", json=body)
        assert resp.status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            row = (await s.execute(select(ChartFeedback))).scalars().one()
        assert row.account_id == seeded_account.id
