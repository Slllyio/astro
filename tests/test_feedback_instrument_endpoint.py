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
    """A Part C item: the only kind that carries a confidence rating."""
    inst = _instrument()
    return next(q for p in inst["parts"] for q in p["questions"]
                if q["kind"] == "choice" and q["confidence"])


def _by_maps_to(name: str) -> dict:
    inst = _instrument()
    return next(q for p in inst["parts"] for q in p["questions"]
                if q.get("maps_to") == name)


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
        body = {**CANONICAL, "answers": [{"qid": "inst.v2.NOPE", "answer": "opt1"}]}
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
            {"qid": _by_maps_to("h6.debts")["qid"]},
            {"qid": _by_maps_to("h9.father")["qid"], "free_text": "   "},
        ]}
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        stored = {r.question_id for r in rows}
        assert _by_maps_to("h6.debts")["qid"] not in stored
        assert _by_maps_to("h9.father")["qid"] not in stored

    async def test_the_response_never_tells_the_submitter_how_they_scored(self, client):
        """An endpoint that scored back would turn the instrument into a quiz, and the answer
        would spread to the next person who takes it for the same chart."""
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": q["options"][0]["value"]}]}
        data = (await client.post("/report/feedback/instrument", json=body)).json()
        assert set(data) == {"stored", "chart_key", "context", "note"}
        assert "not scored back to you" in data["note"]


class TestClosedAnswerKinds:
    async def test_a_multi_select_round_trips_as_joined_codes(self, client, db_engine):
        """Body regions are stored as the codes the reader picked, comma-joined, because the
        scorer compares them against the engine's own region codes directly."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _by_maps_to("medical.regions")
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": "throat_neck,skin"}]}
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            row = (await s.execute(
                select(ChartFeedback).where(ChartFeedback.question_id == q["qid"]))
            ).scalars().one()
        assert row.answer == "throat_neck,skin"

    async def test_a_code_the_instrument_never_offered_is_refused(self, client):
        q = _by_maps_to("medical.regions")
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": "throat_neck,nose"}]}
        resp = await client.post("/report/feedback/instrument", json=body)
        assert resp.status_code == 400 and "nose" in resp.json()["detail"]

    async def test_dated_events_post_one_row_each(self, client, db_engine):
        """A turning point per row, `qid#n`, so the scorer reads them individually instead of
        unpacking a blob nobody would ever query again."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.models.domain import ChartFeedback
        q = _by_maps_to("spine.events")
        body = {**CANONICAL, "answers": [
            {"qid": q["qid"] + "#1", "answer": "2019-03:job_start"},
            {"qid": q["qid"] + "#2", "answer": "2021:marriage"}]}
        assert (await client.post("/report/feedback/instrument", json=body)).status_code == 200
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        stored = {r.question_id: r.answer for r in rows}
        assert stored[q["qid"] + "#1"] == "2019-03:job_start"
        assert stored[q["qid"] + "#2"] == "2021:marriage"

    async def test_a_malformed_event_is_refused(self, client):
        q = _by_maps_to("spine.events")
        body = {**CANONICAL, "answers": [{"qid": q["qid"] + "#1", "answer": "March 2019"}]}
        assert (await client.post("/report/feedback/instrument",
                                  json=body)).status_code == 400

    async def test_a_year_answer_must_be_a_year(self, client):
        q = _by_maps_to("marriage.year")
        ok = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": "2021"}]}
        bad = {**CANONICAL, "answers": [{"qid": q["qid"], "answer": "two thousand"}]}
        assert (await client.post("/report/feedback/instrument", json=ok)).status_code == 200
        assert (await client.post("/report/feedback/instrument", json=bad)).status_code == 400


class TestAMultiSelectSurvivesTheWire:
    """Ticking several boxes must not be rejected, and must not be silently shortened.

    `InstrumentAnswer.answer` was capped at 40 characters and the row was additionally stored
    as `answer[:40]`. The instrument's own closed vocabularies are longer than that: three
    trade families join to 50 characters, three work modes to 54, four body regions to 51, and
    all nineteen trades to 236. So a reader ticking three trades in the real UI got a 422
    before validation ever ran — and any answer that did squeak past would have been truncated
    mid-code on the way into the database, turning a real answer into an unparseable one.

    Both halves are checked here: the request must be ACCEPTED, and what comes back out of the
    database must be byte-identical to what went in.
    """

    @staticmethod
    def _longest(q: dict, n: int) -> str:
        """The n longest codes — the realistic worst case, not the first n alphabetically."""
        return ",".join(sorted((o["value"] for o in q["options"]), key=len, reverse=True)[:n])

    async def test_three_trades_are_accepted_rather_than_rejected(self, client):
        q = _by_maps_to("career.trades")
        picks = self._longest(q, 3)
        assert len(picks) > 40, "pick three that actually exceed the old cap"
        resp = await client.post("/report/feedback/instrument", json={
            **CANONICAL, "answers": [{"qid": q["qid"], "answer": picks}]})
        assert resp.status_code == 200, resp.text

    async def test_the_stored_answer_is_not_truncated(self, client, db_session):
        """A code cut in half scores as nothing and reads as a wrong answer."""
        from app.models.domain import ChartFeedback
        q = _by_maps_to("medical.regions")
        picks = self._longest(q, 4)
        assert len(picks) > 40
        resp = await client.post("/report/feedback/instrument", json={
            **CANONICAL, "answers": [{"qid": q["qid"], "answer": picks}]})
        assert resp.status_code == 200, resp.text
        rows = (await db_session.execute(
            select(ChartFeedback).where(ChartFeedback.question_id == q["qid"]))).scalars().all()
        assert rows and any(r.answer == picks for r in rows), \
            f"stored {[r.answer for r in rows]!r}, expected {picks!r}"

    async def test_every_option_at_once_still_fits(self, client):
        """The widest legal answer the instrument can itself produce — all nineteen trades,
        236 characters. The limit is derived from the vocabularies, so this is the bound."""
        q = _by_maps_to("career.trades")
        picks = ",".join(o["value"] for o in q["options"])
        resp = await client.post("/report/feedback/instrument", json={
            **CANONICAL, "answers": [{"qid": q["qid"], "answer": picks}]})
        assert resp.status_code == 200, resp.text

    async def test_an_absurd_answer_is_still_refused(self, client):
        """Raising the cap must not remove it — the field is still bounded."""
        q = _by_maps_to("career.trades")
        resp = await client.post("/report/feedback/instrument", json={
            **CANONICAL, "answers": [{"qid": q["qid"], "answer": "x" * 5000}]})
        assert resp.status_code == 422


class TestAFreeTextRowIsCheckedLikeAnyOther:
    """The endpoint's promise is that a client cannot invent a question. That promise was
    only kept for rows carrying an `answer`: the validation payload filtered on
    `a.answer is not None`, so a row with free text and no answer skipped validation
    entirely and was stored under whatever qid the client sent, with the qid itself
    standing in for the question text.
    """

    async def test_an_invented_qid_carrying_only_free_text_is_refused(self, client):
        """A qid the instrument never asked is rejected whether or not it has an answer."""
        body = {**CANONICAL, "answers": [
            {"qid": "inst.v2.NOT_A_QUESTION", "free_text": "stored under a made-up question"}]}
        resp = await client.post("/report/feedback/instrument", json=body)
        assert resp.status_code == 400, resp.text
        assert "unknown question" in resp.text

    async def test_a_real_question_answered_only_in_prose_is_still_accepted(self, client,
                                                                           db_engine):
        """Refusing the invented qid must not refuse the legitimate case: a reader who writes
        a sentence against a real question without ticking any option."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from sqlalchemy import select
        from app.models.domain import ChartFeedback
        q = _first_scored_choice()
        body = {**CANONICAL, "answers": [{"qid": q["qid"], "free_text": "no option fits me"}]}
        resp = await client.post("/report/feedback/instrument", json=body)
        assert resp.status_code == 200, resp.text
        sm = async_sessionmaker(db_engine, expire_on_commit=False)
        async with sm() as s:
            rows = (await s.execute(select(ChartFeedback))).scalars().all()
        stored = {r.question_id: r for r in rows}[q["qid"]]
        assert stored.free_text == "no option fits me"
        assert stored.question_text == q["text_en"]      # server's text, not the bare qid
