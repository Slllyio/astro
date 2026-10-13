"""Write user-approved decisions into the golden fixture, line by line, then re-base."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
GOLDENS: Final = ROOT / "tests/fixtures/raman_goldens.jsonl"
BASELINE: Final = ROOT / "tests/fixtures/golden_accuracy_baseline.json"
BACKLOG: Final = ROOT / "docs/raman_saab/DOCTRINE_BACKLOG.md"
_WRITABLE: Final = {"CONFIRMED", "REJECTED", "CONTESTED"}


class DirtyTree(RuntimeError):
    """Refuse to apply over uncommitted changes."""


def _git_status() -> str:
    return subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                          text=True, check=True, cwd=ROOT).stdout


def require_clean_tree() -> None:
    if _git_status().strip():
        raise DirtyTree("working tree is not clean; commit or move other edits first")


def _note(dec: dict[str, Any], run_id: str) -> str:
    quotes = "; ".join(f"{r}: '{q}' (line {ln})" for r, (q, ln) in dec.get("quotes", {}).items())
    if dec["outcome"] == "REJECTED":
        return f"REJECTED by engine-blind review (golden_pipeline run {run_id}). {quotes}"
    if dec["outcome"] == "CONTESTED":
        return f"CONTESTED by engine-blind review (golden_pipeline run {run_id}): no 2-of-3 majority."
    kind = "REVISE" if dec.get("revised") else "CONFIRM"
    return f"{kind} by engine-blind review (golden_pipeline run {run_id}). {quotes}"


def _apply_one(entry: dict[str, Any], dec: dict[str, Any], run_id: str) -> dict[str, Any]:
    prior = entry.get("review_note") or ""
    if entry.get("verdict_review") != "DRAFT" or prior.startswith("REJECTED"):
        raise ValueError(f"{dec['item_id']}: target is not a live DRAFT "
                         f"(verdict_review={entry.get('verdict_review')!r}, note={prior[:30]!r})")
    note = _note(dec, run_id)
    extra: dict[str, Any] = {}
    if dec["outcome"] == "CONFIRMED":  # user decision: store Raman's verified quoted conclusion
        quotes = [q for q, _ln in dec.get("quotes", {}).values()]
        if not quotes:
            raise ValueError(f"{dec['item_id']}: CONFIRMED without a verified quote")
        note += f' prior extracted prose: "{entry.get("verdict_prose", "")}"'
        extra = {"verdict_review": "CONFIRMED", "verdict": dec["verdict"],
                 "signification": dec["signification"], "verdict_prose": max(quotes, key=len)}
    new = {**entry, "review_note": f"{prior} | {note}" if prior else note, **extra}
    if dec["outcome"] == "CONTESTED":
        new["verdict_review"] = "CONTESTED"
    return new  # REJECTED: stays DRAFT, note added


def edit_goldens_lines(lines: list[str], decisions: list[dict[str, Any]],
                       run_id: str) -> list[str]:
    bad = [d["item_id"] for d in decisions if d["outcome"] not in _WRITABLE]
    if bad:
        raise ValueError(f"refusing unscorable outcomes: {bad}")
    ids = [d["item_id"] for d in decisions]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"duplicate item_id in decisions: {dup}")
    matched: set[str] = set()
    by_rec: dict[str, list[dict[str, Any]]] = {}
    for d in decisions:
        by_rec.setdefault(d["record_id"], []).append(d)
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            out.append(line)
            continue
        rec = json.loads(s)
        decs = by_rec.get(rec.get("id"))
        if not decs:
            out.append(line)
            continue
        ev = dict(rec["expected_verdicts"])
        for d in decs:
            tag = f"H{d['house']}"
            if tag not in ev:
                continue  # reported as unmatched below
            ev[tag] = _apply_one(ev[tag], d, run_id)
            matched.add(d["item_id"])
        out.append(json.dumps({**rec, "expected_verdicts": ev}, ensure_ascii=False))
    missing = [i for i in ids if i not in matched]
    if missing:
        raise ValueError(f"decisions matched no golden line/house: {missing}")
    return out


def append_lineage(base: dict[str, Any], exact: tuple[int, int], within1: tuple[int, int],
                   run_id: str, date: str) -> dict[str, Any]:
    tag = f" | {date} golden_pipeline run {run_id}, user-signed:"
    return {**base,
            "track_b": {"correct": exact[0], "total": exact[1]},
            "track_b_ordinal": {"correct": within1[0], "total": within1[1]},
            "_comment": base.get("_comment", "") + f"{tag} {exact[0]}/{exact[1]} exact.",
            "_comment_ordinal": base.get("_comment_ordinal", "")
            + f"{tag} {within1[0]}/{within1[1]} within-1."}


# No tests/__init__.py exists and site-packages ships its own `tests` package, so import the
# module the way pytest does (prepend mode): put tests/ on sys.path.
_MEASURE: Final = (f"import sys, json; sys.path.insert(0, {str(ROOT / 'tests')!r}); "
                   "import raman_saab.test_goldens as G; "
                   "c,t,_=G.track_b_scoreboard(); w,_t,_r=G.track_b_ordinal_scoreboard(); "
                   "print(json.dumps([c,t,w,_t]))")


def measure() -> tuple[tuple[int, int], tuple[int, int]]:
    out = subprocess.run([sys.executable, "-c", _MEASURE], capture_output=True, text=True,
                         check=True, cwd=ROOT).stdout.strip().splitlines()[-1]
    c, t, w, wt = json.loads(out)
    return (c, t), (w, wt)


def _pytest(*args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run([sys.executable, "-m", "pytest", "-q", *args], check=True,
                   env={**os.environ, **(env or {})}, cwd=ROOT)


def run_apply(decisions: list[dict[str, Any]], run_id: str, date: str) -> None:
    """Order matters: confirming engine MISSES lowers the floor (expected under the amended
    confirmation rule), so re-base BEFORE any ratchet test runs. On any failure, restore both
    files so the fixture and baseline never disagree."""
    if not decisions:
        raise ValueError("no decisions to apply; refusing before touching anything")
    require_clean_tree()
    goldens_before = GOLDENS.read_text(encoding="utf-8")
    baseline_before = BASELINE.read_text(encoding="utf-8")
    try:
        lines = goldens_before.split("\n")
        GOLDENS.write_text("\n".join(edit_goldens_lines(lines, decisions, run_id)),
                           encoding="utf-8")
        exact, within1 = measure()
        base = json.loads(baseline_before)
        BASELINE.write_text(json.dumps(append_lineage(base, exact, within1, run_id, date),
                                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _pytest("tests/raman_saab/test_goldens.py",
                "tests/raman_saab/test_golden_verdict_uniqueness.py",
                "tests/raman_saab/doctrine/test_rule_liveness.py")
    except BaseException:
        GOLDENS.write_text(goldens_before, encoding="utf-8")
        BASELINE.write_text(baseline_before, encoding="utf-8")
        raise  # missing snapshots written by the verification run show up in `git status`; discard by hand
    with BACKLOG.open("a", encoding="utf-8") as f:
        f.write(backlog_entry(decisions, run_id, date, exact, within1))


def backlog_entry(decisions: list[dict[str, Any]], run_id: str, date: str,
                  exact: tuple[int, int], within1: tuple[int, int]) -> str:
    rows = "\n".join(
        f"| {d['item_id']} | {d['outcome']}{' (REVISE)' if d.get('revised') else ''} | "
        f"{d.get('verdict', '')} | {d.get('signification', '')} |" for d in decisions)
    return (f"\n\n## golden_pipeline run {run_id} ({date}) — user-signed\n\n"
            f"Re-based to {exact[0]}/{exact[1]} exact, {within1[0]}/{within1[1]} within-1 "
            f"(both axes, side by side).\n\n| item | outcome | verdict | signification |\n"
            f"|---|---|---|---|\n{rows}\n")
