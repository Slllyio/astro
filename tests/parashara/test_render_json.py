"""JSON serializer for the Parashara reading — the machine-readable surface.

Pins that the whole reading serializes to JSON-safe output (json.dumps never raises), that non-JSON
leaves are normalized (frozenset keys/values, tuple keys, Sloka -> object), and that it is complete
(the same sections the markdown carries are present as structured fields).
"""
from __future__ import annotations

import json

from app.parashara.chart.cast import cast
from app.parashara.reading import read
from app.parashara.render_json import to_json, to_json_dict


def _reading():
    return read(cast(year=1990, month=7, day=15, hour=12, minute=0,
                     tz_offset=5.5, latitude=12.97, longitude=77.59))


def test_json_dumps_is_safe():
    d = to_json_dict(_reading())
    s = json.dumps(d)                      # must not raise
    assert json.loads(s) == d              # round-trips

    parsed = json.loads(to_json(_reading()))
    assert isinstance(parsed, dict) and len(parsed) >= 40


def test_non_json_leaves_are_normalized():
    d = to_json_dict(_reading())
    # int-keyed map -> str keys
    assert set(d["arudhas"]) == {str(h) for h in range(1, 13)}
    # Sloka -> object with a citation
    house, sloka = d["planet_house_effects"]["Sun"]
    assert isinstance(house, int) and sloka["source"]["work"] == "SARAVALI-30"
    # frozenset conjunction key -> list of planet names
    if d["conjunctions"]:
        pair, eff = d["conjunctions"][0]
        assert isinstance(pair, list) and eff["source"]["work"] == "SARAVALI-15"


def test_key_structured_sections_present():
    d = to_json_dict(_reading())
    for field in ("chart", "bhavas", "shodasavarga", "sudarshana", "drekkanas", "arudhas",
                  "pada_finance", "spouse_from_upapada", "nisargayu_full", "chara_karakas",
                  "upagrahas", "upagraha_house_effects"):
        assert field in d, field
    assert d["nisargayu_full"]["total_years"] > 0
    assert d["chara_karakas"]["AK"] not in ("Rahu", "Ketu")
