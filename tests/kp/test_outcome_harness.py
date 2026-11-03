"""The real-outcome harness on synthetic data: lock, tamper check, and the three verdicts."""

from __future__ import annotations

import random

import pytest

from tools.kp import outcome_harness as h


def _births(n: int, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    return [{"id": f"s{i:02d}", "year": rng.randint(1950, 1995), "month": rng.randint(1, 12),
             "day": rng.randint(1, 28), "hour": rng.randint(0, 23), "minute": rng.randint(0, 59),
             "tz": 5.5, "lat": 20.0 + rng.random() * 8, "lon": 73.0 + rng.random() * 10,
             "time_source": "certificate", "uncertainty_minutes": 1} for i in range(n)]


@pytest.fixture(scope="module")
def locked() -> dict:
    return h.lock(_births(48))


def _iso(jd: float) -> str:
    return h._iso(jd)


class TestLock:
    def test_digest_detects_tampering(self, locked: dict) -> None:
        """Changing any locked window after locking voids the test."""
        h.verify(locked)
        bad = {**locked, "people": [dict(p) for p in locked["people"]]}
        bad["people"][0] = {**bad["people"][0], "primary": not bad["people"][0]["primary"]}
        with pytest.raises(SystemExit):
            h.verify(bad)

    def test_old_outcome_file_is_refused(self) -> None:
        """data/private/real_outcomes.json is never read by this harness."""
        with pytest.raises(SystemExit):
            h._guard("data/private/real_outcomes.json")

    def test_eligibility_needs_document_and_five_minutes(self) -> None:
        """Pre-registered primary set: documented time, uncertainty at most 5 minutes."""
        assert h.primary_eligible({"time_source": "certificate", "uncertainty_minutes": 5})
        assert not h.primary_eligible({"time_source": "family_memory", "uncertainty_minutes": 0})
        assert not h.primary_eligible({"time_source": "certificate", "uncertainty_minutes": 15})


class TestVerdicts:
    def test_events_inside_own_windows_give_signal(self, locked: dict) -> None:
        """If every event falls mid-window, the own-chart hit count beats the shuffled charts."""
        ev = []
        for p in locked["people"]:
            w = p["windows"]["marriage"]["r25"]
            if w:
                s, e = w[len(w) // 2]
                ev.append({"id": p["id"], "matter": "marriage", "date": _iso((s + e) / 2)})
        res = {(r.matter, r.rule): r for r in h.score(locked, ev)}
        assert len(ev) >= h.MIN_EVENTS
        assert res[("marriage", "r25")].verdict == "SIGNAL"

    def test_too_few_events_are_underpowered(self, locked: dict) -> None:
        """Below the registered 40 events a matter is UNDERPOWERED whatever the hits."""
        p = locked["people"][0]
        ev = [{"id": p["id"], "matter": "children", "date": _iso(p["birth_jd"] + 30 * 365.2425)}]
        res = {(r.matter, r.rule): r for r in h.score(locked, ev)}
        assert res[("children", "r25")].verdict == "UNDERPOWERED"

    def test_events_at_one_fixed_age_are_not_signal(self, locked: dict) -> None:
        """Events placed by age alone carry no chart information, so they must not read as SIGNAL."""
        ev = [{"id": p["id"], "matter": "marriage", "date": _iso(p["birth_jd"] + 26 * 365.2425)}
              for p in locked["people"]]
        res = {(r.matter, r.rule): r for r in h.score(locked, ev)}
        assert res[("marriage", "r25")].verdict == "BOUNDED_NULL"
        assert res[("marriage", "r25")].events == 48
