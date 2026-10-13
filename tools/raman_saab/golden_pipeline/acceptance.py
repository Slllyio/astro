"""Rebuild the 2026-08-23 adjudication answer key from git and compare pipeline decisions.

Usage:
    py -3.12 -m tools.raman_saab.golden_pipeline.acceptance prepare --out before.jsonl
        (then run the pipeline with --input before.jsonl)
    py -3.12 -m tools.raman_saab.golden_pipeline.acceptance score --run R
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.raman_saab.golden_pipeline import runs as R
from tools.raman_saab.golden_pipeline.apply import ROOT

COMMIT = "6517390"
FIXTURE = "tests/fixtures/raman_goldens.jsonl"


def _at(rev: str) -> list[dict[str, Any]]:
    text = subprocess.run(["git", "show", f"{rev}:{FIXTURE}"], capture_output=True,
                          text=True, encoding="utf-8", check=True, cwd=ROOT).stdout
    return [json.loads(s) for s in text.splitlines() if s.strip() and not s.startswith("#")]


def _sig(v: dict[str, Any]) -> tuple[str, str]:
    return (v["verdict"], str(v["signification"]).strip().casefold())


def answer_key(before: list[dict], after: list[dict]) -> dict[str, str]:
    post = {r["id"]: r for r in after}
    key: dict[str, str] = {}
    for rec in before:
        for tag, v in (rec.get("expected_verdicts") or {}).items():
            if v.get("verdict_review") != "DRAFT":
                continue
            w = (post.get(rec["id"], {}).get("expected_verdicts") or {}).get(tag, {})
            if (w.get("verdict_review") == v.get("verdict_review")
                    and w.get("review_note") == v.get("review_note")):
                continue  # commit never touched it (e.g. insufficient-evidence rows)
            if (w.get("verdict_review") != "CONFIRMED"
                    and str(w.get("review_note") or "").lstrip().startswith("HELD")):
                key[f"{rec['id']}#{tag}"] = "CONTESTED"  # HELD = contested, not rejected
            elif w.get("verdict_review") != "CONFIRMED":
                key[f"{rec['id']}#{tag}"] = "REJECT"
            elif _sig(w) == _sig(v):
                key[f"{rec['id']}#{tag}"] = "CONFIRM"
            else:
                key[f"{rec['id']}#{tag}"] = "REVISE"
    return key


def compare(key: dict[str, str], got: dict[str, str]) -> tuple[int, list[tuple[str, str, str]]]:
    div = [(k, key[k], got.get(k, "MISSING")) for k in sorted(key) if got.get(k) != key[k]]
    return len(key) - len(div), div


def _pipeline_label(d: dict[str, Any]) -> str:
    # UNVERIFIED/INCOMPLETE/TIEBREAK/CONTESTED/NOT_FOUND map to themselves: divergences to read by hand.
    if d["outcome"] == "CONFIRMED":
        return "REVISE" if d.get("revised") else "CONFIRM"
    return {"REJECTED": "REJECT"}.get(d["outcome"], d["outcome"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["prepare", "score"])
    ap.add_argument("--out", type=Path, default=Path("before.jsonl"))
    ap.add_argument("--run")
    ap.add_argument("--runs-root", type=Path, default=R.RUNS_ROOT)
    a = ap.parse_args(argv)
    if a.action == "prepare":
        R.write_jsonl(a.out, _at(f"{COMMIT}^"))
        print(f"[acceptance] pre-adjudication fixture -> {a.out}")
        return 0
    key = answer_key(_at(f"{COMMIT}^"), _at(COMMIT))
    got = {d["item_id"]: _pipeline_label(d)
           for d in R.read_jsonl(a.runs_root / a.run / "decisions.jsonl")}
    agree, div = compare(key, got)
    print(f"[acceptance] {agree}/{len(key)} agree with the 2026-08-23 adjudication")
    for k, want, have in div:
        print(f"  {k}: august={want} pipeline={have}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
