"""Golden-corpus pipeline CLI.

Usage:
    py -3.12 -m tools.raman_saab.golden_pipeline extract  --run R [--input FILE.jsonl] --sources-root DIR
    py -3.12 -m tools.raman_saab.golden_pipeline packets  --run R --sources-root DIR [--missing] [--tiebreak]
        (then, in a Claude Code session, dispatch one golden-reviewer subagent per packet and
         save each reply to answers/<same name>.json)
    py -3.12 -m tools.raman_saab.golden_pipeline ingest   --run R --sources-root DIR
    py -3.12 -m tools.raman_saab.golden_pipeline propose  --run R
    py -3.12 -m tools.raman_saab.golden_pipeline apply    --run R --ids ID[,ID...] | --all
    py -3.12 -m tools.raman_saab.golden_pipeline status   --run R
"""
from __future__ import annotations

import argparse
import datetime as _dt
import logging
import sys
from collections import Counter
from pathlib import Path

from tools.raman_saab.golden_pipeline import runs as R
from tools.raman_saab.golden_pipeline import sources as S
from tools.raman_saab.golden_pipeline.apply import GOLDENS, measure, run_apply
from tools.raman_saab.golden_pipeline.extract import select_pending
from tools.raman_saab.golden_pipeline.packets import answer_path, packet_path, render

logger = logging.getLogger(__name__)


def _lines_for(item, root: Path, cache: dict) -> list[str]:
    if item["book"] not in cache:
        cache[item["book"]] = S.read_lines(S.book_path(root, item["book"]))
    return cache[item["book"]]


def cmd_extract(a, run: Path) -> int:
    from tools.raman_saab.golden_pipeline.splice_check import flags
    items, cache = select_pending(R.load_goldens(Path(a.input))), {}
    for it in items:
        _b, start, _e = S.parse_citation(it["citation"])
        it["flags"] = flags(it["verdict_prose"], _lines_for(it, a.sources_root, cache), start)
    R.write_jsonl(run / "items.jsonl", items)
    print(f"[extract] {len(items)} pending items -> {run / 'items.jsonl'}")
    return 0


def cmd_packets(a, run: Path) -> int:
    items, cache = R.read_jsonl(run / "items.jsonl"), {}
    decisions = {d["item_id"]: d for d in R.read_jsonl(run / "decisions.jsonl")} \
        if (run / "decisions.jsonl").is_file() else {}
    # A schema-invalid answer file exists but must still be re-dispatched.
    invalid = {(d["item_id"], r) for d in decisions.values() for r in d.get("invalid", [])}
    for it in items:
        reviewers = "C" if a.tiebreak else "AB"
        if a.tiebreak and decisions.get(it["item_id"], {}).get("outcome") != "TIEBREAK":
            continue
        for r in reviewers:
            p = packet_path(run, it["item_id"], r)
            if a.missing:
                if p.is_file() and (not answer_path(run, it["item_id"], r).is_file()
                                    or (it["item_id"], r) in invalid):
                    print(p.name)
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(render(it, _lines_for(it, a.sources_root, cache), r, it["flags"]),
                         encoding="utf-8")
    return 0


def cmd_ingest(a, run: Path) -> int:
    from tools.raman_saab.golden_pipeline.ingest import ingest_item
    items, cache = R.read_jsonl(run / "items.jsonl"), {}
    decs = [ingest_item(run, it, _lines_for(it, a.sources_root, cache)) for it in items]
    R.write_jsonl(run / "decisions.jsonl", decs)
    print(f"[ingest] {dict(Counter(d['outcome'] for d in decs))}")
    return 0


def cmd_propose(a, run: Path) -> int:
    from tools.raman_saab.golden_pipeline import propose as PR
    decs = R.read_jsonl(run / "decisions.jsonl")
    md = PR.render(decs, PR.engine_lookup(R.load_goldens(Path(a.input))), measure())
    (run / "proposal.md").write_text(md, encoding="utf-8")
    print(f"[propose] -> {run / 'proposal.md'}")
    return 0


def cmd_apply(a, run: Path) -> int:
    decs = [d for d in R.read_jsonl(run / "decisions.jsonl")
            if d["outcome"] in {"CONFIRMED", "REJECTED", "CONTESTED"}]
    if not a.all:
        wanted = set(a.ids.split(","))
        decs = [d for d in decs if d["item_id"] in wanted]
    run_apply(decs, a.run, _dt.date.today().isoformat())
    print(f"[apply] wrote {len(decs)} decisions; review the diff, then commit")
    return 0


def cmd_status(a, run: Path) -> int:
    for name in ("items.jsonl", "decisions.jsonl", "proposal.md"):
        print(f"{name}: {'yes' if (run / name).is_file() else 'no'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["extract", "packets", "ingest", "propose", "apply", "status"])
    ap.add_argument("--run", default=None)
    ap.add_argument("--runs-root", type=Path, default=R.RUNS_ROOT)
    ap.add_argument("--sources-root", type=Path, default=S.DEFAULT_SOURCES_ROOT)
    ap.add_argument("--input", default=str(GOLDENS))
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--tiebreak", action="store_true")
    ap.add_argument("--ids", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    a.run = a.run or R.new_run_id()
    run = R.run_dir(a.run, a.runs_root)
    return globals()[f"cmd_{a.stage}"](a, run)


if __name__ == "__main__":
    sys.exit(main())
