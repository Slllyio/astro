"""The structured JSON serializer — `report_json.to_report_dict`. Every section round-trips to a
JSON-safe dict with its structured hooks intact, and the object-backed citations survive. No
verdict is recomputed (pure re-read of an already-built report)."""
from __future__ import annotations

import json

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.report_json import to_report_dict

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def rjson(report):
    return to_report_dict(report)


class TestSerializer:
    def test_is_json_serializable(self, rjson):
        """The whole dict must round-trip through json.dumps — no dataclass/enum leaks."""
        s = json.dumps(rjson)
        assert len(s) > 10000
        assert json.loads(s)["ruler"]["lagna_lord"] == "Mercury"

    def test_every_major_section_is_present(self, rjson):
        """The serializer surfaces every section a consumer (frontend / LLM) needs."""
        for key in ("chart", "plain_reading", "nichod", "synthesis", "ruler", "proformas",
                    "calibration", "house_strength", "preponderance", "dashboard", "yogas",
                    "insights", "longevity", "timeline", "ishta_kashta", "life_chapters",
                    "gochara", "sav", "divisional", "soul", "pitru"):
            assert key in rjson, key

    def test_structured_hooks_survive(self, report, rjson):
        """The typed drill-down data an interactive UI binds to is preserved with real values."""
        # ruler
        assert rjson["ruler"]["strongest"] == report.ruler.strongest
        # preponderance: per-testimony leans
        h1 = rjson["preponderance"]["houses"][0]
        assert h1["house"] == 1 and len(h1["testimonies"]) == len(report.preponderance.houses[0].testimonies)
        assert all("lean" in t for t in h1["testimonies"])
        # house strength rank/band
        assert len(rjson["house_strength"]) == 12
        assert {"house", "bhava_bala_rank", "sav_band", "verdict"} <= set(rjson["house_strength"][0])
        # calibration percentiles + inverted flag
        e0 = rjson["calibration"]["1"]["entries"][0]
        assert {"favourability_percentile", "inverted_warning", "verdict"} <= set(e0)

    def test_citations_are_objects_not_only_strings(self, report, rjson):
        """Yogas and insights carry their Citation as a {work, line} object, so a consumer can
        click-to-source without regexing prose."""
        assert rjson["yogas"], "canonical chart fires yogas"
        assert set(rjson["yogas"][0]["source"]) == {"work", "line"}
        cited = [i for i in rjson["insights"] if i["source"] is not None]
        assert cited and set(cited[0]["source"]) == {"work", "line"}

    def test_verdict_column_matches_the_engine(self, report, rjson):
        """The house rollup verdicts in the JSON are the engine's own, verbatim — never
        re-decided by the serializer."""
        for pf, row in zip(report.proformas, rjson["proformas"]):
            assert row["rollup"] == str(pf.rollup)
            assert row["house"] == pf.house

    def test_chart_and_timeline_are_trimmed_not_raw(self, rjson):
        """chart/timeline are display-trimmed (planet table / bhukti rows), not full-model dumps."""
        assert set(rjson["chart"]) == {"asc_sign", "planets"}
        sun = rjson["chart"]["planets"]["Sun"]
        assert {"sign", "rasi_house", "shadbala_rupas"} <= set(sun)
        assert isinstance(rjson["timeline"], list) and rjson["timeline"]
        assert {"maha", "antar", "activated"} <= set(rjson["timeline"][0])
