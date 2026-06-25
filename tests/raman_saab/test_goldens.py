"""The golden-harness — the accuracy ratchet for the Raman Saab engine.

Loads ``tests/fixtures/raman_goldens.jsonl`` once and runs a 3-tier check over it:

* **Track A (astronomy)** — only for records with a full ``birth`` AND
  ``track_eligibility`` containing ``"A"``: cast a fresh ephemeris chart and assert
  the computed Rashi + Navamsa sign of each printed planet matches Raman's printed
  sign. Planets within +-2 deg of a bhava sandhi (cusp) are logged to an audit list,
  not hard-failed. (Most book charts lack a time -> few Track-A cases; that is fine.)
* **Track B (doctrine — the north star)** — build the chart (fresh-cast if ``birth``
  present, else ``from_stated_positions``), ``judge_house``, and assert each
  per-signification verdict equals the expected one — but ONLY for verdicts whose
  ``verdict_review == "CONFIRMED"``.
* **Tier 3 (evidence snapshot)** — capture fired-rule ids + citations + a ledger
  summary as a stable dict and JSON-compare it against a committed snapshot file. The
  snapshot is NEVER auto-overwritten; set ``UPDATE_RAMAN_SNAPSHOTS=1`` to refresh.

Plus GUARD tests: (a) every JSONL line conforms to the schema; (b) a DRAFT-gate that
SKIPS any worked_example/rule_level record still carrying a DRAFT verdict from Track B;
and a separate informational reporter that prints DRAFT vs CONFIRMED counts (never
fails on the DRAFT count).

The loader + helpers here are imported by ``tools/raman_saab/tune_thresholds.py``.

Run:
    py -3.12 -m pytest tests/raman_saab/test_goldens.py -q
    UPDATE_RAMAN_SNAPSHOTS=1 py -3.12 -m pytest tests/raman_saab/test_goldens.py -q
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.chart import varga
from app.raman_saab.judges import house_template as ht

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
GOLDENS_PATH = _FIXTURES / "raman_goldens.jsonl"
SNAPSHOT_DIR = _FIXTURES / "golden_snapshots"

_CASE_TYPES = {"worked_example", "rule_level", "doctrine_statement", "self_test"}
_VERDICTS = {"favourable", "mixed", "afflicted", "insufficient-evidence", "DRAFT"}
_REVIEWS = {"DRAFT", "CONFIRMED"}
_TRACKS = {"A", "B", "3"}
_POSITION_SOURCES = {"printed_degree", "sign_midpoint", "synthetic_minimal", "fresh_cast"}
_SANDHI_ORB_DEG = 2.0


# ---------------------------------------------------------------------------
# Loader (comment/blank-aware JSONL)
# ---------------------------------------------------------------------------

def load_goldens(path: Path = GOLDENS_PATH) -> list[dict[str, Any]]:
    """Parse the JSONL fixture, skipping blank lines and ``#`` comment lines."""
    out: list[dict[str, Any]] = []
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(json.loads(s))
    return out


_GOLDENS: list[dict[str, Any]] = load_goldens()


def _id(rec: dict[str, Any]) -> str:
    return str(rec.get("id", "<no-id>"))


# ---------------------------------------------------------------------------
# Chart building (shared by tracks + the tuner)
# ---------------------------------------------------------------------------

def _materialise_lon(entry: dict[str, Any]) -> float:
    """Resolve a stated-position entry to a longitude: explicit ``lon``, else the
    sign midpoint of ``sign``."""
    if "lon" in entry and entry["lon"] is not None:
        return float(entry["lon"]) % 360.0
    sign = int(entry["sign"])
    return float((sign - 1) * 30) + 15.0


def _birth_from(rec: dict[str, Any]) -> Optional[BirthData]:
    """A BirthData if the record carries a full birth block, else None."""
    b = rec.get("birth")
    if not b:
        return None
    if any(b.get(k) is None for k in ("dt", "tz", "lat", "lon")):
        return None
    dt = str(b["dt"])
    date_part, _, time_part = dt.partition("T")
    y, mo, d = (int(x) for x in date_part.split("-"))
    hh, mm = 0, 0
    if time_part:
        parts = time_part.split(":")
        hh = int(parts[0]); mm = int(parts[1]) if len(parts) > 1 else 0
    return BirthData(name=str(rec.get("name", "golden")), year=y, month=mo, day=d,
                     hour=hh, minute=mm, tz_offset=float(b["tz"]),
                     latitude=float(b["lat"]), longitude=float(b["lon"]))


def build_chart(rec: dict[str, Any]) -> RamanChart:
    """Track-B chart for a record: fresh ephemeris cast when ``birth`` is present,
    else ``from_stated_positions`` from the printed table."""
    birth = _birth_from(rec)
    if birth is not None:
        return cast_chart(birth, ayanamsa="raman")
    stated = {
        name: {"lon": _materialise_lon(entry), "bhava": int(entry["bhava"])}
        for name, entry in rec["stated_positions"].items()
    }
    lagna = rec.get("lagna_sign")
    asc_lon = float((int(lagna) - 1) * 30) + 5.0 if lagna else 5.0
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


# ---------------------------------------------------------------------------
# Verdict gating
# ---------------------------------------------------------------------------

def _is_confirmed(verdict_entry: dict[str, Any]) -> bool:
    """A verdict is asserted only if reviewed CONFIRMED and not a bare DRAFT literal."""
    return (verdict_entry.get("verdict_review") == "CONFIRMED"
            and verdict_entry.get("verdict") != "DRAFT")


def confirmed_verdicts(rec: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """[(house_number, verdict_entry), ...] for every CONFIRMED verdict in a record."""
    out: list[tuple[int, dict[str, Any]]] = []
    for htag, entry in rec.get("expected_verdicts", {}).items():
        if _is_confirmed(entry):
            out.append((int(htag[1:]), entry))
    return out


def _signification_verdict(chart: RamanChart, house: int, sig_key: str) -> Optional[str]:
    """The engine's verdict for one signification of a house (None if absent)."""
    pf = ht.judge_house(chart, house)
    for sv in pf.significations:
        if sv.signification == sig_key:
            return sv.verdict
    return None


# Records that may run Track B at all: those with >=1 CONFIRMED verdict.
_TRACK_B_RECORDS = [r for r in _GOLDENS
                    if "B" in r.get("track_eligibility", []) and confirmed_verdicts(r)]
# Anchors (synthetic self_test records) hard-assert per record — they are regression
# canaries with deterministic verdicts. Worked examples instead feed the accuracy RATCHET:
# the engine is measured against Raman's confirmed verdicts and must never regress below
# the committed baseline (plan: "golden accuracy up or flat"), but is not required to be
# 100% before the combinations/tuning phases land.
_TRACK_B_ANCHORS = [r for r in _TRACK_B_RECORDS if r["case_type"] == "self_test"]
_TRACK_B_RATCHET = [r for r in _TRACK_B_RECORDS if r["case_type"] != "self_test"]
_BASELINE_PATH = _FIXTURES / "golden_accuracy_baseline.json"
# Records eligible for Track A.
_TRACK_A_RECORDS = [r for r in _GOLDENS
                    if "A" in r.get("track_eligibility", []) and _birth_from(r) is not None]
# Records eligible for Tier-3 snapshot.
_TIER3_RECORDS = [r for r in _GOLDENS if "3" in r.get("track_eligibility", [])]


# ===========================================================================
# GUARD A — schema conformance (every JSONL line is well-formed).
# ===========================================================================

@pytest.mark.parametrize("rec", _GOLDENS, ids=[_id(r) for r in _GOLDENS] or ["<empty>"])
def test_golden_line_conforms_to_schema(rec: dict[str, Any]) -> None:
    """Every golden line matches docs/raman_saab/golden_schema.md (the JSONL contract)."""
    for fld in ("id", "book", "name", "case_type", "birth", "lagna_sign",
                "stated_positions", "expected_verdicts", "expected_longevity",
                "track_eligibility", "confidence", "citations"):
        assert fld in rec, f"{_id(rec)}: missing required field {fld!r}"

    assert rec["case_type"] in _CASE_TYPES, f"{_id(rec)}: bad case_type {rec['case_type']!r}"
    assert rec["book"] in {"HTJAH-I", "HTJAH-II"}, f"{_id(rec)}: bad book"

    lagna = rec["lagna_sign"]
    assert lagna is None or (isinstance(lagna, int) and 1 <= lagna <= 12), \
        f"{_id(rec)}: lagna_sign must be 1..12 or null"

    # birth: null or a {dt,tz,lat,lon} object (fields nullable).
    b = rec["birth"]
    assert b is None or isinstance(b, dict), f"{_id(rec)}: birth must be object|null"
    if isinstance(b, dict):
        for k in ("dt", "tz", "lat", "lon"):
            assert k in b, f"{_id(rec)}: birth missing {k!r}"

    # stated_positions: each entry has exactly one of lon/sign, a bhava, a source.
    for name, entry in rec["stated_positions"].items():
        has_lon = entry.get("lon") is not None
        has_sign = entry.get("sign") is not None
        assert has_lon != has_sign, f"{_id(rec)}.{name}: need exactly one of lon/sign"
        assert isinstance(entry.get("bhava"), int) and 1 <= entry["bhava"] <= 12, \
            f"{_id(rec)}.{name}: bhava must be 1..12"
        assert entry.get("position_source") in _POSITION_SOURCES, \
            f"{_id(rec)}.{name}: bad position_source"
        if has_sign:
            assert 1 <= int(entry["sign"]) <= 12, f"{_id(rec)}.{name}: sign 1..12"

    # expected_verdicts
    for htag, entry in rec["expected_verdicts"].items():
        assert htag[0] == "H" and 1 <= int(htag[1:]) <= 12, f"{_id(rec)}: bad house tag {htag!r}"
        assert entry.get("verdict") in _VERDICTS, f"{_id(rec)}: bad verdict {entry.get('verdict')!r}"
        assert entry.get("verdict_review") in _REVIEWS, f"{_id(rec)}: bad verdict_review"
        assert "signification" in entry, f"{_id(rec)}: verdict missing signification"

    # track_eligibility
    te = rec["track_eligibility"]
    assert te and set(te) <= _TRACKS, f"{_id(rec)}: bad track_eligibility {te!r}"

    # confidence
    assert isinstance(rec["confidence"], (int, float)) and 0.0 <= rec["confidence"] <= 1.0, \
        f"{_id(rec)}: confidence must be 0..1"

    # expected_longevity: null | {years,months,days} | {death_date}
    el = rec["expected_longevity"]
    if el is not None:
        assert isinstance(el, dict), f"{_id(rec)}: expected_longevity must be object|null"
        if "death_date" in el:
            assert isinstance(el["death_date"], str)
        else:
            for k in ("years", "months", "days"):
                assert isinstance(el.get(k), int), f"{_id(rec)}: longevity {k} must be int"

    # self_test must always be CONFIRMED (it is a regression anchor).
    if rec["case_type"] == "self_test":
        for entry in rec["expected_verdicts"].values():
            assert _is_confirmed(entry), f"{_id(rec)}: self_test verdicts must be CONFIRMED"

    # SCHEMA GUARD #5 (validation rule #11): case_type structural invariants.
    # A doctrine_statement is a prose claim with NO chart to judge -> it must carry
    # empty stated_positions AND empty expected_verdicts (nothing is asserted).
    if rec["case_type"] == "doctrine_statement":
        assert rec["expected_verdicts"] == {}, \
            f"{_id(rec)}: doctrine_statement must have empty expected_verdicts"
        assert rec["stated_positions"] == {}, \
            f"{_id(rec)}: doctrine_statement must have empty stated_positions"
    # A rule_level golden pins ONE combination on a minimal synthesised chart, so it
    # may assert at most its single rule house (one expected_verdicts key).
    if rec["case_type"] == "rule_level":
        assert len(rec["expected_verdicts"]) <= 1, \
            f"{_id(rec)}: rule_level pins at most its single rule house, got " \
            f"{sorted(rec['expected_verdicts'])}"


def test_at_least_one_golden_loaded() -> None:
    """The fixture is non-empty (the loader saw at least the self-test anchor)."""
    assert _GOLDENS, "no goldens loaded from raman_goldens.jsonl"


# ===========================================================================
# TRACK A — astronomy (sign-level Rashi + Navamsa equality; cusp drift audited).
# ===========================================================================

# Module-level audit log of cusp-proximate placements (logged, never hard-failed).
TRACK_A_AUDIT: list[dict[str, Any]] = []


@pytest.mark.skipif(not _TRACK_A_RECORDS, reason="no Track-A goldens (need full birth)")
@pytest.mark.parametrize("rec", _TRACK_A_RECORDS,
                         ids=[_id(r) for r in _TRACK_A_RECORDS] or ["<none>"])
def test_track_a_lagna_sign_matches_printed(rec: dict[str, Any]) -> None:
    """The FRESH-CAST Lagna (Ascendant) sign equals Raman's printed ``lagna_sign``.

    This operationalises the locked rule "computed degrees must match Raman printed
    positions" without transcribing full planet tables — it leans only on the
    already-populated ``lagna_sign``. A record whose ``lagna_sign`` is ``null`` (the
    book gave no Lagna) is skipped. An Ascendant within +-2 deg of a sign boundary
    (bhava sandhi) is AUDIT-LOGGED rather than hard-failed (a one-sign cusp drift from
    Raman's printed label is doctrinally acceptable); a >1-sign mismatch, or a
    one-sign mismatch away from a cusp, IS a hard failure."""
    printed_lagna = rec.get("lagna_sign")
    if printed_lagna is None:
        pytest.skip(f"{_id(rec)}: no printed lagna_sign to check")
    chart = build_chart(rec)
    computed = int(chart.asc_sign)
    printed = int(printed_lagna)
    if computed == printed:
        return
    # One-sign-off near a cusp -> audit, never hard-fail. Distance of the Ascendant
    # to the nearest sign boundary (cusp at every 30 deg).
    deg_in_sign = chart.asc_lon % 30.0
    dist_to_cusp = min(deg_in_sign, 30.0 - deg_in_sign)
    sign_gap = min((computed - printed) % 12, (printed - computed) % 12)
    if sign_gap == 1 and dist_to_cusp <= _SANDHI_ORB_DEG:
        TRACK_A_AUDIT.append({
            "id": _id(rec), "planet": "Lagna", "lon": round(chart.asc_lon, 4),
            "computed_sign": computed, "printed_sign": printed,
            "dist_to_cusp": round(dist_to_cusp, 4),
        })
        return
    raise AssertionError(
        f"{_id(rec)}: fresh-cast Lagna sign {computed} != printed {printed} "
        f"(asc_lon={chart.asc_lon:.4f}, dist_to_cusp={dist_to_cusp:.4f}, "
        f"sign_gap={sign_gap}) -- not a within-sandhi one-sign drift")


@pytest.mark.skipif(not _TRACK_A_RECORDS, reason="no Track-A goldens (need full birth)")
@pytest.mark.parametrize("rec", _TRACK_A_RECORDS,
                         ids=[_id(r) for r in _TRACK_A_RECORDS] or ["<none>"])
def test_track_a_signs_match_printed(rec: dict[str, Any]) -> None:
    """Computed Rashi AND Navamsa sign equal Raman's printed sign for each planet;
    a planet within +-2 deg of a bhava sandhi is audited, not failed."""
    chart = build_chart(rec)
    for name, entry in rec["stated_positions"].items():
        printed_sign = (int(entry["sign"]) if entry.get("sign") is not None
                        else int(_materialise_lon(entry) // 30) + 1)
        p = chart.planets.get(name)
        assert p is not None, f"{_id(rec)}: {name} absent from cast chart"
        near_cusp = p.bhava_sandhi or _near_sandhi(p.lon, chart)
        if near_cusp:
            TRACK_A_AUDIT.append({
                "id": _id(rec), "planet": name, "lon": round(p.lon, 4),
                "computed_sign": p.sign, "printed_sign": printed_sign,
                "computed_navamsa": p.navamsa_sign,
                "navamsa_of_printed": varga.navamsa_sign(_materialise_lon(entry)),
            })
            continue
        assert p.sign == printed_sign, \
            f"{_id(rec)}: {name} Rashi {p.sign} != printed {printed_sign}"
        printed_nav = varga.navamsa_sign(_materialise_lon(entry))
        assert p.navamsa_sign == printed_nav, \
            f"{_id(rec)}: {name} Navamsa {p.navamsa_sign} != printed {printed_nav}"


def _near_sandhi(lon: float, chart: RamanChart) -> bool:
    """True if `lon` is within +-2 deg of any bhava sandhi (cusp)."""
    for s in chart.bhava_sandhis:
        diff = abs(lon - s) % 360.0
        if min(diff, 360.0 - diff) <= _SANDHI_ORB_DEG:
            return True
    return False


# ===========================================================================
# TRACK B — doctrine (the north star). Only CONFIRMED verdicts assert.
# ===========================================================================

@pytest.mark.skipif(not _TRACK_B_ANCHORS, reason="no self_test anchor records")
@pytest.mark.parametrize("rec", _TRACK_B_ANCHORS,
                         ids=[_id(r) for r in _TRACK_B_ANCHORS] or ["<none>"])
def test_track_b_anchor_verdicts(rec: dict[str, Any]) -> None:
    """self_test anchors hard-assert per record (deterministic regression canaries)."""
    chart = build_chart(rec)
    for house, entry in confirmed_verdicts(rec):
        sig_key = entry["signification"]
        got = _signification_verdict(chart, house, sig_key)
        assert got is not None, f"{_id(rec)}: H{house} has no signification {sig_key!r}"
        assert got == entry["verdict"], (
            f"{_id(rec)}: H{house}/{sig_key} engine={got!r} != golden={entry['verdict']!r}\n"
            f"  prose: {entry.get('verdict_prose', '')}")


def track_b_scoreboard() -> tuple[int, int, list[str]]:
    """(correct, total, mismatch_lines) across every CONFIRMED worked-example verdict.

    Deterministic: records in ledger order, houses in confirmed_verdicts() order.
    Shared by the ratchet test and tools/raman_saab/tune_thresholds.py.
    """
    correct, total, mismatches = 0, 0, []
    for rec in _TRACK_B_RATCHET:
        chart = build_chart(rec)
        for house, entry in confirmed_verdicts(rec):
            sig_key = entry["signification"]
            got = _signification_verdict(chart, house, sig_key)
            total += 1
            if got == entry["verdict"]:
                correct += 1
            else:
                mismatches.append(
                    f"  {_id(rec)} H{house}/{sig_key}: engine={got!r} golden={entry['verdict']!r}")
    return correct, total, mismatches


# ---------------------------------------------------------------------------
# Ordinal-tolerance metric (Layer B) — the fairer second headline.
# The verdict is an ordinal afflicted < mixed < favourable. A within-1 "near-hit"
# recognises that the favourable-vs-mixed / mixed-vs-afflicted boundary is genuinely
# contestable (Raman's readings are graded), separating SUBJECTIVE boundary calls
# (distance 1) from REAL doctrinal errors (distance >=2 — the cited-fix targets).
# insufficient-evidence is OFF the graded axis, so any mismatch with it is a real miss.
# The strict exact-match ratchet above is unchanged; this is purely additive.
# ---------------------------------------------------------------------------
_ORD_POS: dict[str, int] = {"afflicted": 0, "mixed": 1, "favourable": 2}


def _ordinal_distance(got: Optional[str], expected: str) -> int:
    if got == expected:
        return 0
    if got in _ORD_POS and expected in _ORD_POS:
        return abs(_ORD_POS[got] - _ORD_POS[expected])
    return 2  # insufficient-evidence vs a graded verdict -> a real miss, not a near-hit


def track_b_ordinal_scoreboard() -> tuple[int, int, list[str]]:
    """(within1, total, real_error_lines) across every CONFIRMED worked-example verdict.
    within1 counts ordinal distance <= 1; real_error_lines are the distance >= 2 genuine
    doctrinal errors (the Layer-C cited-fix targets). Deterministic; same record order as
    track_b_scoreboard()."""
    within1, total, real = 0, 0, []
    for rec in _TRACK_B_RATCHET:
        chart = build_chart(rec)
        for house, entry in confirmed_verdicts(rec):
            sig_key = entry["signification"]
            got = _signification_verdict(chart, house, sig_key)
            total += 1
            d = _ordinal_distance(got, entry["verdict"])
            if d <= 1:
                within1 += 1
            if d >= 2:
                real.append(f"  {_id(rec)} H{house}/{sig_key}: engine={got!r} "
                            f"golden={entry['verdict']!r} (dist {d})")
    return within1, total, real


@pytest.mark.skipif(not _TRACK_B_RATCHET, reason="no CONFIRMED worked-example records")
def test_track_b_accuracy_ratchet() -> None:
    """Engine accuracy vs Raman's confirmed verdicts must never drop below the
    committed baseline (tests/fixtures/golden_accuracy_baseline.json).

    The baseline is bumped by a HUMAN, in the same commit as the change that earned
    the improvement (or that legitimately re-bases it, e.g. newly confirmed goldens).
    A failure means either (a) an engine change regressed doctrine accuracy — fix the
    change, or (b) new goldens were confirmed and the measured floor moved — re-base
    the baseline file deliberately in this commit.
    """
    correct, total, mismatches = track_b_scoreboard()
    accuracy = correct / total if total else 1.0
    baseline = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))["track_b"]
    base_acc = baseline["correct"] / baseline["total"]
    report = (f"Track-B accuracy: {correct}/{total} = {accuracy:.3f} "
              f"(baseline {baseline['correct']}/{baseline['total']} = {base_acc:.3f})")
    if mismatches:
        report += "\nmismatches:\n" + "\n".join(mismatches)
    assert accuracy >= base_acc - 1e-9, report
    # Improvement is reported (visible with -s / on failure elsewhere) but never auto-saved.


@pytest.mark.skipif(not _TRACK_B_RATCHET, reason="no CONFIRMED worked-example records")
def test_track_b_ordinal_ratchet() -> None:
    """Within-1 ordinal accuracy must never drop below the committed ordinal baseline
    (golden_accuracy_baseline.json track_b_ordinal). The fairer headline: a verdict within one
    ordinal step of Raman's counts as a near-hit (the favourable-vs-mixed boundary is graded and
    contestable). The distance>=2 cases printed on failure are the REAL doctrinal errors — the
    cited-fix targets. Like the strict ratchet, the baseline is bumped by a HUMAN in the same
    commit as the change that earns it."""
    within1, total, real = track_b_ordinal_scoreboard()
    accuracy = within1 / total if total else 1.0
    baseline = json.loads(_BASELINE_PATH.read_text(encoding="utf-8")).get("track_b_ordinal")
    if baseline is None:
        pytest.skip("no track_b_ordinal baseline yet")
    base_acc = baseline["correct"] / baseline["total"]
    report = (f"Track-B ordinal (within-1): {within1}/{total} = {accuracy:.3f} "
              f"(baseline {baseline['correct']}/{baseline['total']} = {base_acc:.3f})")
    if real:
        report += "\nREAL doctrinal errors (distance>=2):\n" + "\n".join(real)
    assert accuracy >= base_acc - 1e-9, report


@pytest.mark.skipif(not _TRACK_B_RATCHET, reason="no CONFIRMED worked-example records")
def test_avastha_modulates_degree_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Layer-A avastha pin: the avastha deepening modulates DEGREE only. Forcing the avastha
    demotion ON for EVERY signification must not change a single verdict bucket (Phaladeepika
    Sl.20 — avastha scales intensity, never polarity). This guards the degree-only invariant:
    if a future change let avastha touch the verdict, this fails loudly."""
    import app.raman_saab.judges.house_template as ht

    baseline: dict[tuple, Optional[str]] = {}
    for rec in _TRACK_B_RATCHET:
        chart = build_chart(rec)
        for house, entry in confirmed_verdicts(rec):
            key = (_id(rec), house, entry["signification"])
            baseline[key] = _signification_verdict(chart, house, entry["signification"])

    changed = []
    for forced in (-1, 1):  # force demotion AND promotion everywhere
        monkeypatch.setattr(ht, "_avastha_combined", lambda *a, **k: forced)
        for rec in _TRACK_B_RATCHET:
            chart = build_chart(rec)
            for house, entry in confirmed_verdicts(rec):
                key = (_id(rec), house, entry["signification"])
                got = _signification_verdict(chart, house, entry["signification"])
                if got != baseline[key]:
                    changed.append(f"  av={forced} {key}: {baseline[key]!r} -> {got!r}")
    assert not changed, "avastha changed verdict buckets (must be degree-only):\n" + "\n".join(changed)


# ===========================================================================
# TIER 3 — evidence snapshot (stable fired-rule ids + citations + ledger summary).
# ===========================================================================

def evidence_snapshot(chart: RamanChart, houses: tuple[int, ...] = tuple(range(1, 13)),
                      ) -> dict[str, Any]:
    """A stable, JSON-serialisable evidence dict for a chart: per house, the sorted
    fired-rule ids + citations + the per-signification verdict + lead frame."""
    snap: dict[str, Any] = {}
    for h in houses:
        pf = ht.judge_house(chart, h)
        hv = pf.as_house_verdict()
        fired_ids = sorted({fr.rule.id for fr in (hv.benefic + hv.malefic + hv.neutral)})
        citations = sorted({f"{fr.rule.source.work}:{fr.rule.source.line}"
                            for fr in (hv.benefic + hv.malefic + hv.neutral)})
        sigs = {sv.signification: {"verdict": sv.verdict, "degree": sv.degree,
                                    "lead_frame": sv.lead_frame}
                for sv in pf.significations}
        snap[f"H{h}"] = {
            "rollup": pf.rollup,
            "fired_rule_ids": fired_ids,
            "citations": citations,
            "significations": sigs,
        }
    return snap


def _snapshot_path(rec: dict[str, Any]) -> Path:
    safe = _id(rec).replace("/", "_").replace(":", "_")
    return SNAPSHOT_DIR / f"{safe}.json"


def _compare_or_write_snapshot(rec: dict[str, Any], snap: dict[str, Any]) -> None:
    """Minimal JSON-on-disk snapshot: compare against the committed file, or write it
    when missing / when UPDATE_RAMAN_SNAPSHOTS is set. NEVER auto-overwrites a
    mismatching committed snapshot."""
    path = _snapshot_path(rec)
    update = os.environ.get("UPDATE_RAMAN_SNAPSHOTS") == "1"
    serialised = json.dumps(snap, indent=2, sort_keys=True, ensure_ascii=True)
    if not path.exists() or update:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(serialised + "\n", encoding="utf-8")
        if not update:
            pytest.skip(f"wrote new snapshot {path.name} (re-run to assert against it)")
        return
    committed = path.read_text(encoding="utf-8").strip()
    assert committed == serialised, (
        f"{_id(rec)}: evidence snapshot drift vs {path.name}. "
        f"If intended, re-run with UPDATE_RAMAN_SNAPSHOTS=1.")


@pytest.mark.skipif(not _TIER3_RECORDS, reason="no Tier-3 goldens")
@pytest.mark.parametrize("rec", _TIER3_RECORDS,
                         ids=[_id(r) for r in _TIER3_RECORDS] or ["<none>"])
def test_tier3_evidence_snapshot(rec: dict[str, Any]) -> None:
    """The chart's fired-rule/citation/ledger evidence matches its committed snapshot."""
    chart = build_chart(rec)
    # snapshot only the houses the record actually pins, to keep the file small/stable.
    houses = tuple(sorted({int(h[1:]) for h in rec.get("expected_verdicts", {})})) \
        or tuple(range(1, 13))
    snap = evidence_snapshot(chart, houses)
    _compare_or_write_snapshot(rec, snap)


# ===========================================================================
# DRAFT-GATE + reporting (informational; never fails on the DRAFT count).
# ===========================================================================

def _count_reviews() -> tuple[int, int]:
    draft = confirmed = 0
    for rec in _GOLDENS:
        for entry in rec.get("expected_verdicts", {}).values():
            if _is_confirmed(entry):
                confirmed += 1
            else:
                draft += 1
    return draft, confirmed


def test_draft_gate_skips_unreviewed_worked_examples() -> None:
    """DRAFT-gate proof: no worked_example/rule_level record with an un-CONFIRMED
    verdict leaks into the Track-B asserting set."""
    leaked = []
    track_b_ids = {_id(r) for r in _TRACK_B_RECORDS}
    for rec in _GOLDENS:
        if rec["case_type"] not in {"worked_example", "rule_level"}:
            continue
        all_draft = all(not _is_confirmed(e) for e in rec.get("expected_verdicts", {}).values())
        if all_draft and _id(rec) in track_b_ids:
            leaked.append(_id(rec))
    assert not leaked, f"DRAFT records leaked into Track B: {leaked}"


def test_report_draft_vs_confirmed(capsys: pytest.CaptureFixture[str]) -> None:
    """Informational: print DRAFT vs CONFIRMED counts. NEVER fails on the DRAFT count
    (a large DRAFT backlog is expected mid-extraction)."""
    draft, confirmed = _count_reviews()
    total = len(_GOLDENS)
    exact, etot, _ = track_b_scoreboard() if _TRACK_B_RATCHET else (0, 0, [])
    w1, wtot, _real = track_b_ordinal_scoreboard() if _TRACK_B_RATCHET else (0, 0, [])
    with capsys.disabled():
        print(f"\n[goldens] records={total}  verdicts: CONFIRMED={confirmed} DRAFT={draft}"
              f"  TrackA={len(_TRACK_A_RECORDS)} TrackB={len(_TRACK_B_RECORDS)} "
              f"Tier3={len(_TIER3_RECORDS)}")
        if etot:
            print(f"[ratchet] exact={exact}/{etot}={exact/etot:.3f}  "
                  f"within-1(ordinal)={w1}/{wtot}={w1/wtot:.3f}  "
                  f"real-errors(dist>=2)={wtot - w1}")
    assert confirmed >= 0  # tautology — this test reports, it does not gate on DRAFT
