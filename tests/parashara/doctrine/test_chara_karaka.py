"""Chara karakas + Karakamsa — BPHS ch.32-33, the 7-karaka fork settled toward Parashara's primary.

Pins that the engine uses 7 karakas (not the "some say" 8th with Rahu), that the Atmakaraka can
never be a node (structural), the degree-within-sign descending ranking with its minutes/seconds
tie-break, the canonical chart's karakas, and that every citation — including the one marking the
rejected 8th-karaka variant — resolves to real doctrine.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.doctrine.chara_karaka import (
    AK_RULE_SOURCE,
    EIGHTH_KARAKA_REJECTED,
    KARAKAMSA_SOURCE,
    ROLE_NAMES,
    SEVEN_SCHOOL_SOURCE,
    SOURCE,
    atmakaraka,
    chara_karakas,
    karakamsa,
)
from app.parashara.doctrine.sources import verify


def _canonical():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestSevenKarakaScheme:
    def test_exactly_seven_karakas(self):
        ck = chara_karakas(_canonical().longitudes)
        assert len(ck) == 7
        assert set(ck) == {"AK", "AmK", "BK", "MK", "PiK", "GK", "DK"}

    def test_atmakaraka_is_never_a_node(self):
        # the whole point of the fork: nodes are not in the ranked set, so AK cannot be Rahu/Ketu
        for lon_rahu in (5.0, 29.9, 200.0):     # even a near-30 Rahu must not win
            lons = {"Sun": 10.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 15.0,
                    "Jupiter": 20.0, "Venus": 3.0, "Saturn": 6.0,
                    "Rahu": lon_rahu, "Ketu": (lon_rahu + 180) % 360}
            assert atmakaraka(lons) not in ("Rahu", "Ketu")

    def test_ranked_by_degree_within_sign_descending(self):
        ck = chara_karakas(_canonical().longitudes)
        lons = _canonical().longitudes
        order = ["AK", "AmK", "BK", "MK", "PiK", "GK", "DK"]
        degs = [lons[ck[r]] % 30.0 for r in order]
        assert degs == sorted(degs, reverse=True)

    def test_tie_break_uses_minutes_then_seconds(self):
        # same integer degree, different fractional part -> the finer one ranks higher
        lons = {"Sun": 10.50, "Moon": 10.20, "Mars": 1.0, "Mercury": 2.0,
                "Jupiter": 3.0, "Venus": 4.0, "Saturn": 5.0}
        ck = chara_karakas(lons)
        assert ck["AK"] == "Sun" and ck["AmK"] == "Moon"

    def test_canonical_atmakaraka_is_the_sun(self):
        assert atmakaraka(_canonical().longitudes) == "Sun"


class TestKarakamsa:
    def test_is_a_valid_sign(self):
        assert 1 <= karakamsa(_canonical().longitudes) <= 12


class TestCitations:
    def test_all_sources_resolve(self):
        for c in (SOURCE, AK_RULE_SOURCE, SEVEN_SCHOOL_SOURCE, EIGHTH_KARAKA_REJECTED, KARAKAMSA_SOURCE):
            assert verify(c), c

    def test_rejected_eighth_marks_the_some_say_line(self):
        from app.parashara.doctrine.sources import passage
        text = (passage(f"{EIGHTH_KARAKA_REJECTED.work}:{EIGHTH_KARAKA_REJECTED.line}") or {}).get("text", "")
        assert "8 karaka" in text.lower() or "advocate" in text.lower()

    def test_role_names_cover_all_seven(self):
        assert set(ROLE_NAMES) == {"AK", "AmK", "BK", "MK", "PiK", "GK", "DK"}
