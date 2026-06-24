"""Tests for app.medini.forecast (multi-day scanner + aggregator).

Pin events at a known JD via stubbed planet positions. The real ephemeris
is deterministic for a fixed JD so we don't have to mock swisseph — but to
keep tests fast we use small horizons (3-5 days) and only verify the
shape + invariants (event ordering, dedup of consecutive same-sign days,
no spam of 30 ingresses for one slow planet).

Anchor JD for sanity: 2026-01-01 00:00 UT = JD 2460676.5
"""
from __future__ import annotations

import datetime as dt

import pytest
import swisseph as swe

from app.medini.forecast import (
    DEFAULT_HORIZON_DAYS,
    multi_day_forecast,
    scan_conjunctions,
    scan_eclipses,
    scan_ingresses,
    scan_lunations,
    scan_stations,
)


def _jd(year: int, month: int, day: int) -> float:
    """Helper: deterministic JD-UT for a date at 00:00."""
    return swe.julday(year, month, day, 0.0, swe.GREG_CAL)


JD_2026_01_01 = _jd(2026, 1, 1)


# --------------------------------------------------------------------------- #
# Aggregator                                                                   #
# --------------------------------------------------------------------------- #

class TestMultiDayForecast:
    """Top-level invariants on the aggregated payload."""

    def test_payload_shape_and_keys(self) -> None:
        """Contract: forecast returns these top-level keys with these types."""
        out = multi_day_forecast(jd_start=JD_2026_01_01, horizon_days=7)
        assert set(out) >= {
            "jd_start", "date_start_utc", "horizon_days",
            "events", "by_day", "summary",
        }
        assert out["horizon_days"] == 7
        assert isinstance(out["events"], list)
        assert isinstance(out["by_day"], dict)

    def test_events_sorted_by_jd_ascending(self) -> None:
        """Calendar relies on time-ordered events; verify the sort."""
        out = multi_day_forecast(jd_start=JD_2026_01_01, horizon_days=30)
        jds = [e["jd"] for e in out["events"]]
        assert jds == sorted(jds)

    def test_by_day_keys_match_event_dates(self) -> None:
        """Every event date must have a key in by_day."""
        out = multi_day_forecast(jd_start=JD_2026_01_01, horizon_days=10)
        for e in out["events"]:
            assert e["date_utc"] in out["by_day"]

    def test_summary_counts_match_event_list(self) -> None:
        """Summary counts must equal len(filter by type)."""
        out = multi_day_forecast(jd_start=JD_2026_01_01, horizon_days=14)
        events = out["events"]
        for t in ("INGRESS", "STATION", "CONJUNCTION",
                  "NEW_MOON", "FULL_MOON", "ECLIPSE"):
            assert out["summary"]["by_type"][t] == sum(
                1 for e in events if e["type"] == t
            )

    def test_horizon_zero_or_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="horizon_days"):
            multi_day_forecast(jd_start=JD_2026_01_01, horizon_days=0)

    def test_default_horizon_is_30(self) -> None:
        """Locked default so memory + docs stay accurate."""
        assert DEFAULT_HORIZON_DAYS == 30


# --------------------------------------------------------------------------- #
# Scanners                                                                      #
# --------------------------------------------------------------------------- #

class TestIngressDeduplication:
    """One INGRESS event per actual sign change — not one per day-detected."""

    def test_no_duplicate_ingress_for_slow_planets(self) -> None:
        """Saturn / Jupiter / Rahu / Ketu / Mars are slow enough that each
        ingresses at most twice in a 30-day window (e.g. Mars only every
        ~45 days). Faster movers (Moon ~13/mo, Mercury ~3/mo) naturally
        have many ingresses — testing slow planets isolates dedup bugs."""
        events = scan_ingresses(JD_2026_01_01, 30)
        slow = {"Saturn", "Jupiter", "Rahu", "Ketu", "Mars"}
        for planet in slow:
            n = sum(1 for e in events
                    if e["type"] == "INGRESS" and e["planet"] == planet)
            assert n <= 2, (
                f"{planet} has {n} ingresses in 30d — suggests dedup bug"
            )

    def test_no_consecutive_day_ingress_for_same_planet(self) -> None:
        """A real ingress fires on one scan-day boundary. If we get two
        ingresses for the same planet on adjacent days, it's a dedup bug
        regardless of planet speed."""
        events = scan_ingresses(JD_2026_01_01, 30)
        from collections import defaultdict
        by_planet: dict[str, list[float]] = defaultdict(list)
        for e in events:
            by_planet[e["planet"]].append(e["jd"])
        for planet, jds in by_planet.items():
            jds_sorted = sorted(jds)
            for prev, cur in zip(jds_sorted, jds_sorted[1:]):
                assert (cur - prev) > 1.5, (
                    f"{planet} has consecutive-day ingresses at "
                    f"jd={prev:.2f}, {cur:.2f} — dedup bug"
                )

    def test_each_ingress_records_from_and_to_sign(self) -> None:
        events = scan_ingresses(JD_2026_01_01, 60)
        for e in events:
            assert "from_sign" in e
            assert "to_sign" in e
            assert e["from_sign"] != e["to_sign"]


class TestStationScanner:
    def test_sun_and_moon_excluded_from_stations(self) -> None:
        """Sun + Moon never station — must not appear in STATION events."""
        events = scan_stations(JD_2026_01_01, 90)
        planets = {e["planet"] for e in events}
        assert "Sun" not in planets
        assert "Moon" not in planets

    def test_station_event_records_state_transition(self) -> None:
        events = scan_stations(JD_2026_01_01, 180)
        for e in events:
            assert e["from_state"] in {"direct", "retrograde"}
            assert e["to_state"] in {"direct", "retrograde"}
            assert e["from_state"] != e["to_state"]

    def test_rahu_hysteresis_suppresses_wobble(self) -> None:
        """The earlier smoke test (May/Jun 2026) produced 3 Rahu stations in
        12 days because true-node velocity oscillates near zero. Hysteresis
        should cap Rahu/Ketu stations at <= 2 per 30 days (one real station
        each at most). Pin a window known to wobble in true-node mode."""
        # Anchor on 2026-05-25 ± 30 days where the original wobble appeared
        wobble_anchor = swe.julday(2026, 5, 25, 0.0, swe.GREG_CAL)
        events = scan_stations(wobble_anchor, 30)
        for node in ("Rahu", "Ketu"):
            n = sum(1 for e in events if e["planet"] == node)
            assert n <= 2, (
                f"{node} has {n} stations in 30d at the known-wobble anchor — "
                f"hysteresis regression"
            )


class TestConjunctionDeduplication:
    """One CONJUNCTION per pair, at the minimum-orb JD."""

    def test_at_most_one_conjunction_per_pair(self) -> None:
        events = scan_conjunctions(JD_2026_01_01, 30, orb_degrees=3.0)
        pairs = [(e["planet_a"], e["planet_b"]) for e in events]
        assert len(pairs) == len(set(pairs)), (
            "duplicate conjunction events for the same pair"
        )

    def test_conjunction_orb_below_threshold(self) -> None:
        """The reported orb_degrees must be <= the threshold."""
        thresh = 1.5
        events = scan_conjunctions(JD_2026_01_01, 30, orb_degrees=thresh)
        for e in events:
            assert e["orb_degrees"] <= thresh + 1e-9


class TestLunations:
    """New + full moon detection — exactly ~1 of each per ~29.5 days."""

    def test_one_or_two_new_moons_in_30_days(self) -> None:
        """Synodic month is ~29.53d → 1 or 2 new moons in any 30-day window."""
        events = scan_lunations(JD_2026_01_01, 30)
        new_count = sum(1 for e in events if e["type"] == "NEW_MOON")
        assert 1 <= new_count <= 2

    def test_one_or_two_full_moons_in_30_days(self) -> None:
        events = scan_lunations(JD_2026_01_01, 30)
        full_count = sum(1 for e in events if e["type"] == "FULL_MOON")
        assert 1 <= full_count <= 2


class TestEclipseScanner:
    """Eclipse pull is a re-shaping of the existing module — verify the
    envelope normalization rather than the underlying astronomy."""

    def test_eclipse_events_have_required_envelope(self) -> None:
        events = scan_eclipses(JD_2026_01_01, 365)
        for e in events:
            assert e["type"] == "ECLIPSE"
            assert "jd" in e and "date_utc" in e
            assert e["family"] in {"SOLAR", "LUNAR"}
            assert "kurma" in e
