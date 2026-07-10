"""Integrity guard for the fresh unseen corpora: they must be genuinely UNSEEN.

The whole point of the fresh held-out set is that the engine (and this project) has not
touched it. These pin (a) the de-dup — no catalogued unseen chart shares a birth-date with
an already-extracted chart — and (b) that the NH timing corpus is disjoint from HTJAH.
"""
import json
import re
from pathlib import Path

_CORPORA = Path("docs/raman_doctrine/validation/corpora")
_DATE = re.compile(r"(\d{1,2}-\d{1,2}-\d{4})")


def _seen_keys_excluding(*exclude):
    keys = set()
    for f in list(_CORPORA.glob("*.json")) + list(
            Path("docs/raman_doctrine/audit/corpora").glob("*.json")):
        if f.name in exclude:
            continue
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        for r in (d.get("charts", d if isinstance(d, list) else d.get("rows", [])) or []):
            m = _DATE.search(r.get("birth_line", "") or "")
            if m:
                keys.add(m.group(1).replace(" ", ""))
    return keys


def test_unseen_catalog_is_disjoint_from_extracted():
    cat = json.loads((_CORPORA / "unseen_catalog.json").read_text())
    assert cat["n_fresh"] >= 150                       # ~164 fresh charts
    seen = _seen_keys_excluding("unseen_catalog.json")
    leaked = [c["key"] for c in cat["charts"] if c["key"] and c["key"] in seen]
    assert not leaked, f"already-seen charts leaked into the unseen catalog: {leaked[:5]}"


def test_nh_timing_is_a_distinct_source():
    nh = json.loads((_CORPORA / "nh_timing.json").read_text())
    assert len(nh["charts"]) == 50
    # NH names are famous figures (strings), never the anonymous HTJAH numeric chart_nos
    assert all(isinstance(c["chart_no"], str) for c in nh["charts"])
