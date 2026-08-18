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
        """chart/timeline are display-trimmed (planet table / bhukti rows), not full-model dumps.
        (Conscious append-only amendment 2026-08-17, Wave-1: asc_lon + ascendant joined the
        trimmed chart so the cast is externally checkable — still a whitelist, not a raw dump.)"""
        assert set(rjson["chart"]) == {"asc_sign", "planets", "asc_lon", "ascendant"}
        sun = rjson["chart"]["planets"]["Sun"]
        assert {"sign", "rasi_house", "shadbala_rupas"} <= set(sun)
        assert isinstance(rjson["timeline"], list) and rjson["timeline"]
        assert {"maha", "antar", "activated"} <= set(rjson["timeline"][0])

    def test_timeline_activated_houses_carry_the_four_tier_grade(self, rjson):
        """Each bhukti serializes WHICH houses it lights and their FOUR-tier fructification grade
        (par excellence / ordinary / limited / feeble) + the AD-associated flag — so the interactive
        page shows the same grading as the standalone report, not a bare count (a real regression
        that dropped the houses-lit detail to a length)."""
        tiers = {a.get("tier") for t in rjson["timeline"] for a in t["activated"]}
        assert tiers <= {"par excellence", "ordinary", "limited", "feeble"}
        assert tiers - {None}                                 # at least one house is graded
        row = next(t for t in rjson["timeline"] if t["activated"])
        assert "associated" in row
        a = row["activated"][0]
        assert {"house", "tier", "natal_verdict"} <= set(a)


class TestAshtakavargaCompletenessJson:
    """AV completeness (2026-08-17): the serializer ships the BAV matrix, the HPA-26 reduced
    tables and the Sodya Pinda as append-only keys, matching the report's own rows."""

    def test_new_av_keys_present_and_structured(self, report, rjson):
        """bav_matrix / bav_reduced / sodya_pinda carry 7 typed rows each, values intact."""
        assert len(rjson["bav_matrix"]) == len(rjson["bav_reduced"]) == 7
        assert len(rjson["sodya_pinda"]) == 7
        row = rjson["bav_matrix"][0]
        assert {"planet", "bindus", "total", "seat_sign", "seat_bindus"} <= set(row)
        assert len(row["bindus"]) == 12 and sum(row["bindus"]) == row["total"]
        assert sum(r["total"] for r in rjson["bav_matrix"]) == 337
        red = rjson["bav_reduced"][0]
        assert {"planet", "trikona", "reduced"} <= set(red)
        assert len(red["trikona"]) == len(red["reduced"]) == 12
        sp = rjson["sodya_pinda"][0]
        assert sp["total"] == sp["rasi"] + sp["graha"]
        assert [r["planet"] for r in rjson["sodya_pinda"]] == [
            x.planet for x in report.sodya_pinda]


class TestWave1CompletenessJson:
    """Wave-1 (2026-08-17) append-only keys: exact longitudes + Ascendant + nakshatra lords
    on the chart, the maraka scheme with per-unit reasons, Baladi/Jagradadi states, and the
    confluence score addends."""

    def test_chart_carries_longitudes_ascendant_and_nak_lords(self, report, rjson):
        """Planets gain lon/longitude/nakshatra_lord; the Ascendant ships as its own row
        (canonical pins: asc ~173.99 -> 23 Vi 59'.., Moon Revati -> Mercury)."""
        moon = rjson["chart"]["planets"]["Moon"]
        assert {"lon", "longitude", "nakshatra_lord"} <= set(moon)
        assert moon["nakshatra_lord"] == "Mercury"
        assert abs(moon["lon"] - report.chart.planets["Moon"].lon) < 1e-5
        asc = rjson["chart"]["ascendant"]
        assert asc["sign"] == 6 and asc["longitude"].startswith("23 Vi 59'")
        assert abs(rjson["chart"]["asc_lon"] - report.chart.asc_lon) < 1e-5

    def test_maraka_scheme_and_reasons_serialized(self, rjson):
        """The 'maraka' key carries the tiered units WITH their qualifying clauses."""
        mk = rjson["maraka"]
        assert mk is not None and mk["units"]
        assert all(u["reasons"] for u in mk["units"])
        assert {"drekkana22_lord", "navamsa64_lord"} <= set(mk)
        venus = next(u for u in mk["units"] if u["graha"] == "Venus")
        assert "lord of the 2nd" in venus["reasons"]

    def test_baladi_jagradadi_states_serialized(self, rjson):
        """Per-planet Baladi/Jagradadi via the judge's read-only accessor — canonical pin
        Saturn = Mrita/Swapna."""
        bj = rjson["baladi_jagradadi"]
        assert bj["Saturn"] == {"baladi": "Mrita", "jagradadi": "Swapna"}
        assert len(bj) == 9

    def test_maraka_saturn_rows_carry_score_parts(self, rjson):
        """Each confluence row's tier addends are present and reproduce the score."""
        assert rjson["maraka_saturn"]
        for row in rjson["maraka_saturn"]:
            assert row["score_parts"]
            terms = row["score_parts"].split(" + ")
            assert sum(int(t.rsplit(" ", 1)[1]) for t in terms) == row["score"]


class TestWave1TimingKeys:
    """Wave-1 (2026-08-17): the appended timing keys and the per-row delivery quality."""

    def test_new_timing_keys_appended_and_serializable(self, rjson):
        """pratyantar_now / sade_sati_phases / chara_sequence are present, structured and
        JSON-safe — the same objects the markdown renders."""
        assert len(rjson["pratyantar_now"]) == 9
        assert {"maha", "antar", "pratyantar", "start_jd",
                "end_jd"} <= set(rjson["pratyantar_now"][0])
        assert rjson["sade_sati_phases"]
        assert {"phase", "house_from_moon", "sign", "start_jd", "end_jd",
                "current"} <= set(rjson["sade_sati_phases"][0])
        assert rjson["chara_sequence"]
        assert sum(1 for c in rjson["chara_sequence"] if c["current"]) == 1
        json.dumps({k: rjson[k] for k in ("pratyantar_now", "sade_sati_phases",
                                          "chara_sequence")})

    def test_timeline_activated_rows_carry_delivery_quality(self, rjson):
        """Every activated house row ships its md_quality/antar_quality LordQuality objects
        (HTJAH-II:10004-10008) — previously computed but absent from the JSON contract."""
        row = rjson["timeline"][0]["activated"][0]
        assert row["md_quality"]["tag"] in ("well", "poorly", "mixed", "unknown")
        assert row["md_quality"]["lord"] == rjson["timeline"][0]["maha"]
        assert "antar_quality" in row
        for tp in rjson["timeline"]:
            for a in tp["activated"]:
                assert {"md_quality", "antar_quality"} <= set(a)
