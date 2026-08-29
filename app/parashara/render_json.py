"""Structured JSON serializer for the Parashara reading — the machine-readable surface.

`to_json_dict(reading)` turns the frozen `ParasharaReading` (a deep nest of dataclasses, `Sloka`
objects, frozensets and tuple/int-keyed maps) into a plain JSON-safe dict that an API response or a
frontend can bind to field-by-field, rather than parsing `to_markdown`'s prose. `to_json(reading)`
is the `json.dumps` string.

Complete by construction (CLAUDE.md REPORT COMPLETENESS): a single generic recursion serializes
EVERY field the reading holds — so a new reading field is machine-readable automatically, never
silently dropped. Non-JSON leaves are normalized: dataclasses -> objects (incl. `Sloka` ->
{work, number, topic, text, source:{work, line}}), (frozen)sets -> sorted lists, and tuple/frozenset
dict keys -> stable joined strings ("Sun|10", "Jupiter+Sun+Venus"). No verdict is recomputed; this
is a pure re-read of an already-built reading.

Usage:
    from app.parashara.render_json import to_json_dict, to_json
    d = to_json_dict(read(chart))     # json.dumps(d) is safe
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any

from app.parashara.reading import ParasharaReading


def _key(k: Any) -> str:
    """A stable string form for a dict key (JSON keys must be strings)."""
    if isinstance(k, tuple):
        return "|".join(str(_jsonify(x)) if not isinstance(x, (str, int)) else str(x) for x in k)
    if isinstance(k, (frozenset, set)):
        return "+".join(sorted(str(x) for x in k))
    return str(k)


def _jsonify(obj: Any) -> Any:
    """Recursively convert any reading value into a JSON-safe structure."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _jsonify(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, dict):
        return {_key(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (frozenset, set)):
        return [_jsonify(x) for x in sorted(obj, key=str)]
    if isinstance(obj, (list, tuple)):
        return [_jsonify(x) for x in obj]
    if isinstance(obj, float):
        return round(obj, 6)          # tame ephemeris float noise in the payload
    return obj                        # str / int / bool / None pass through


def to_json_dict(reading: ParasharaReading) -> dict:
    """The whole reading as a JSON-safe dict, plus the deterministic synthesis under `synthesis`."""
    from app.parashara.synthesis import synthesize
    from app.parashara.synthesis.render_synthesis import to_dict as _synthesis_dict
    d = _jsonify(reading)
    d["synthesis"] = _synthesis_dict(synthesize(reading))
    return d


def to_json(reading: ParasharaReading, *, indent: int | None = None) -> str:
    """The reading serialized to a JSON string (json.dumps is guaranteed safe on the dict)."""
    return json.dumps(to_json_dict(reading), indent=indent, ensure_ascii=False)
