"""field_case_01 — the first REAL-OUTCOME golden (a confirmed real nativity, owner-elicited).

Distinct from the Raman worked-chart corpus (raman_goldens.jsonl): this pins the engine
against a living person's actual life on two axes — the STATIC per-signification verdict
(must stay within one ordinal step of the owner's real verdict) and the dynamic TIMING
(each dated life event's house must be ACTIVATED in the period running at its date). Both
are ratchet floors: fixes raise them, regressions are caught. The 6 documented static
gaps (catastrophic/binary over-afflictions) are the current fix targets — as they are
closed, bump ``baseline.static_within1`` toward 50 in the same commit.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification.events import EVENT_TAXONOMY, LifeEvent

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "field_case_01.json"
_POS = {"afflicted": 0, "mixed": 1, "favourable": 2}


def _ordinal_distance(got: str | None, truth: str) -> int:
    if got == truth:
        return 0
    if got in _POS and truth in _POS:
        return abs(_POS[got] - _POS[truth])
    return 2


@pytest.fixture(scope="module")
def case() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def chart(case):
    b = case["birth"]
    return cast_chart(BirthData(name="field_case_01", year=b["year"], month=b["month"],
                                day=b["day"], hour=b["hour"], minute=b["minute"],
                                tz_offset=b["tz_offset"], latitude=b["latitude"],
                                longitude=b["longitude"]), ayanamsa=case["ayanamsa"])


def _static_scoreboard(chart, case) -> tuple[int, int, list[str]]:
    within1 = total = 0
    misses: list[str] = []
    for hstr, sigs in case["confirmed_verdicts"].items():
        pf = ht.judge_house(chart, int(hstr))
        engine = {sv.signification: sv.verdict for sv in pf.significations}
        for key, truth in sigs.items():
            got = engine.get(key)
            d = _ordinal_distance(got, truth)
            total += 1
            if d <= 1:
                within1 += 1
            else:
                misses.append(f"H{hstr}.{key}: engine={got} truth={truth} (dist {d})")
    return within1, total, misses


def _timing_scoreboard(chart, case) -> tuple[int, int, list[str]]:
    hits = total = 0
    misses: list[str] = []
    for e in case["events"]:
        ev = LifeEvent(e["event_type"], e["year"], e["month"], e.get("day"))
        spec = ev.spec
        acts = {a.house: a.grade for a in vim.active_houses(chart, ev.jd_point())}
        houses = (spec.house, *spec.aux_houses)
        total += 1
        if any(h in acts for h in houses):
            hits += 1
        else:
            misses.append(f"{e['event_type']} {e['year']}-{e['month']:02d} houses{houses}")
    return hits, total, misses


class TestStaticAxis:
    def test_within_one_ratchet(self, chart, case) -> None:
        """The engine's per-signification verdict stays within one ordinal step of the
        owner's real verdict for at least the committed floor — a real-outcome ratchet."""
        within1, total, misses = _static_scoreboard(chart, case)
        floor = case["baseline"]["static_within1"]
        report = (f"static within-1: {within1}/{total} (floor {floor}); "
                  f"distance>=2:\n" + "\n".join("  " + m for m in misses))
        assert within1 >= floor, report
        assert total == case["baseline"]["static_total"]

    def test_documented_gaps_are_the_known_fix_targets(self, chart, case) -> None:
        """The current distance>=2 misses are exactly the 6 catastrophic/binary
        over-afflictions the feedback loop identified — no NEW real-life divergences
        have crept in (any new one would be a regression to investigate)."""
        _, _, misses = _static_scoreboard(chart, case)
        keys = {m.split(":")[0] for m in misses}
        expected = {"H3.siblings", "H3.courage", "H4.mother", "H6.accidents",
                    "H12.incarceration", "H12.left_eye"}
        assert keys <= expected, f"unexpected new real-life miss: {keys - expected}"


class TestTimingAxis:
    def test_every_event_activates_its_house(self, chart, case) -> None:
        """The fructification engine: each dated life event's house (or an aux house) is
        active in the daśā period running at its date — the timing ratchet."""
        hits, total, misses = _timing_scoreboard(chart, case)
        floor = case["baseline"]["timing_hits"]
        assert hits >= floor, (f"timing hits {hits}/{total} (floor {floor}); "
                               f"dormant: {misses}")
        assert total == case["baseline"]["timing_total"]
