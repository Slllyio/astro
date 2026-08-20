"""The feedback-instrument endpoint: what it accepts, what it refuses, and what it never says.

The instrument is deterministic for a chart, which is what lets the server rebuild it and
validate a submission against what it would itself have asked. These tests defend that — and
the two things the endpoint must never do: trust the client's account of a question, or tell a
submitter how they scored.
"""
from __future__ import annotations

from sqlalchemy import select

#: canonical test-pinning baseline (Bangalore 1990-07-15 12:00 IST) per CLAUDE.md.
CANONICAL = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
    "name": "Canonical Baseline",
}


def _instrument() -> dict:
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.feedback_instrument import build_feedback_instrument
    from app.raman_saab.report_json import to_report_dict
    birth = BirthData(name=CANONICAL["name"], year=CANONICAL["year"], month=CANONICAL["month"],
                      day=CANONICAL["day"], hour=CANONICAL["hour"], minute=CANONICAL["minute"],
                      tz_offset=CANONICAL["tz_offset"], latitude=CANONICAL["latitude"],
                      longitude=CANONICAL["longitude"])
    return build_feedback_instrument(to_report_dict(build_detailed_report(birth)))


def _first_scored_choice() -> dict:
    inst = _instrument()
    return next(q for p in inst["parts"] for q in p["questions"]
                if q["kind"] == "choice" and q["confidence"])


class TestInstrumentRidesTheReport:
    async def test_report_json_carries_the_instrument(self, client):
        """The questionnaire is generated WITH the reading, from the same cast — a reader who
        has their report has their questions, with no second ephemeris run."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"})
        assert resp.status_code == 200
        inst = resp.json()["report"]["feedback_instrument"]
        assert [p["part"] for p in inst["parts"]] == ["A", "B", "C", "D"]
        assert inst["counts"]["C"] >= 1

    async def test_the_answer_key_is_not_in_the_response(self, client):
        """Shipping the key beside the questions would make every answer worthless."""
        import json
        resp = await client.post("/report", json={**CANONICAL, "format": "json"})
        blob = json.dumps(resp.json()["report"]["feedback_instrument"])
        for leak in ("band_share", "signification", "inverted_warning", "verdict"):
            assert leak not in blob, leak


class TestSubmission:
    async def test_a_completed_item_is_stored_with_its_confidence(self, client, db_engine):
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _first_scored_choice()
        body = {**CANONICAL, "context": "before_reading", "answers": [
            {"qid": q["qid"], "answer": q["options"][0]["value"], "free_text": "because X"},
            {"qid": q["qid"] + ".confidence", "answer": "4"},
        ]}
        resp = await client.post("/report/feedback/instrument", json=body)
        assert resp.status_code == 200, resp.text
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        by_qid = {r.question_id: r for r in rows}
        assert by_qid[q["qid"]].answer == q["options"][0]["value"]
        assert by_qid[q["qid"]].free_text == "because X"
        assert by_qid[q["qid"] + ".confidence"].answer == "4"

    async def test_the_reading_order_is_recorded_not_assumed(self, client, db_engine):
        """Whether Part A was answered before the reading was read is the difference between
        evidence and a satisfaction survey. It is stored as its own row, so a later query can
        split the two rather than pooling them."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _first_scored_choice()
        body = {**CANONICAL, "context": "before_reading",
                "answers": [{"qid": q["qid"], "answer": q["options"][0]["value"]}]}
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        meta = [r for r in rows if r.question_id.endswith(".meta.context")]
        assert len(meta) == 1 and meta[0].answer == "before_reading"

    async def test_the_question_text_comes_from_the_server_not_the_client(self, client,
                                                                         db_engine):
        """The older flow takes `question_text` from the request body, so a client can store
        any text it likes against any qid. This one never reads a client-supplied question: the
        text is looked up in the rebuilt instrument, and the request model has no field for it."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [
            {"qid": q["qid"], "answer": q["options"][0]["value"],
             "question_text": "something the client made up"}]}
        # extra="forbid" on the answer model rejects the smuggled field outright
        assert (await client.post("/report/feedback/instrument",
                                  json=body)).status_code == 422
        del body["answers"][0]["question_text"]
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            row = (await s.execute(
                select(ChartFeedback).where(ChartFeedback.question_id == q["qid"]))
            ).scalars().one()
        assert row.question_text == q["text_en"][:500]

    async def test_an_option_the_chart_never_offered_is_refused(self, client):
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": "opt9"}]}
        resp = await client.post("/report/feedback/instrument", json=body)
        assert resp.status_code == 400
        assert "opt" in resp.json()["detail"]

    async def test_an_unknown_question_is_refused(self, client):
        body = {**CANONICAL, "answers": [{"qid": "inst.v1.NOPE", "answer": "opt1"}]}
        assert (await client.post("/report/feedback/instrument",
                                  json=body)).status_code == 400

    async def test_untouched_questions_are_not_stored_as_answers(self, client, db_engine):
        """A form with 56 questions is normally part-filled. A blank is not an answer and must
        not become a row, or the stored set would look complete when it is not."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [
            {"qid": q["qid"], "answer": q["options"][0]["value"]},
            {"qid": "inst.v1.A5"},
            {"qid": "inst.v1.A6", "free_text": "   "},
        ]}
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        stored = {r.question_id for r in rows}
        assert "inst.v1.A5" not in stored and "inst.v1.A6" not in stored

    async def test_the_response_never_tells_the_submitter_how_they_scored(self, client):
        """An endpoint that scored back would turn the instrument into a quiz, and the answer
        would spread to the next person who takes it for the same chart."""
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": q["options"][0]["value"]}]}
        data = (await client.post("/report/feedback/instrument", json=body)).json()
        assert set(data) == {"stored", "chart_key", "context", "note"}
        assert "not scored back to you" in data["note"]
