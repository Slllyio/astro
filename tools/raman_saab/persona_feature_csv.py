"""Per-feature results table for the persona study — one row per persona x per feature.

BUILD-TIME tool — lives OUTSIDE app/. REPORT-ONLY: reads collected answers and re-derives each
chart's scoring key; it never writes into the engine or changes a verdict.

`score` reports the study's aggregate numbers. This emits the evidence UNDER those numbers: for
every persona, every forced-choice feature the engine chose to be tested on, what the engine
claimed, how rare that claim is in the 16,450-chart population, what each arm answered, and
whether that answer agreed with the chart. That is the table you read to see WHERE a null came
from — an aggregate of 0.500 can hide twelve coin-flips or six confident hits and six confident
misses, and only the row level tells them apart.

One row per (run, persona, feature). Runs are given as `label=directory`, so several collections
of the same roster land in one file with a `run` column to separate them.

Usage:
    py -3.12 -m tools.raman_saab.persona_feature_csv \
        deep=tests/fixtures/astrobank_persona_pilot_deep \
        --out data/astrobank_persona_pilot/features.csv

    py -3.12 -m tools.raman_saab.persona_feature_csv \
        shallow=tests/fixtures/astrobank_persona_pilot \
        deep=tests/fixtures/astrobank_persona_pilot_deep \
        --out data/astrobank_persona_pilot/features.csv --summary data/.../summary.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Optional

from tools.raman_saab import persona_study as ps

#: Written for every feature row. `_blind_*` / `_contaminated_*` / `_coinflip_*` repeat per arm
#: so one row carries the whole comparison for that feature and needs no join to be read.
COLUMNS = (
    "run", "persona", "qid", "house", "feature", "topic",
    "engine_verdict", "degree", "population_share", "rarity", "favourability_percentile",
    "inverted_channel", "engine_claim", "opposite_claim", "key_option",
    "blind_answer", "blind_agrees", "blind_confidence",
    "contaminated_answer", "contaminated_agrees", "contaminated_confidence",
    "coinflip_answer", "coinflip_agrees",
)


def _answers(path: Path) -> dict[str, str]:
    """One arm's answers for one persona, or empty when that arm was not collected."""
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("answers") or {}


def _agrees(given: dict[str, str], qid: str, expected: str) -> Optional[bool]:
    """Did this arm pick the chart's own option? None when the arm never answered the item —
    which is not the same as a miss, and must not be counted as one."""
    return None if qid not in given else given[qid] == expected


def _cell(value: Any) -> Any:
    """True/False as 1/0 so a spreadsheet can sum a column; None stays empty."""
    if value is None:
        return ""
    return int(value) if isinstance(value, bool) else value


def rows_for_run(label: str, out_dir: Path, *, seed: str) -> list[dict[str, Any]]:
    """Every feature row for one collected run, in roster then question order."""
    from app.raman_saab.feedback_instrument import instrument_key

    roster = json.loads((out_dir / "roster.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []

    for rec in roster["admitted"]:
        slug = rec["slug"]
        report = ps._report_for(rec)
        key = instrument_key(report)
        payload = json.loads((out_dir / "payloads" / f"{slug}.json").read_text(encoding="utf-8"))
        by_qid = {q["qid"]: q for part in payload["instrument"]["parts"]
                  for q in part["questions"]}

        blind = _answers(out_dir / "answers" / f"{slug}.json")
        contam = _answers(out_dir / "answers_contaminated" / f"{slug}.json")
        coin = ps.coinflip_answers(payload, seed=seed)

        for qid, expected in key["answers"].items():
            meta = key["meta"].get(qid, {})
            if meta.get("kind") != "forced_choice":
                continue
            question = by_qid.get(qid, {})
            opts = {o["value"]: o["text_en"] for o in question.get("options", ())}
            other = next((v for v in opts if v != expected), "")
            rows.append({
                "run": label,
                "persona": rec["name"],
                "qid": qid.rsplit(".", 1)[-1],
                "house": meta.get("house", ""),
                "feature": meta.get("signification", ""),
                "topic": question.get("text_en", "").split(" — ")[0],
                "engine_verdict": meta.get("verdict", ""),
                "degree": meta.get("degree", ""),
                "population_share": meta.get("band_share", ""),
                "rarity": meta.get("rarity", ""),
                "favourability_percentile": meta.get("favourability_percentile", ""),
                "inverted_channel": _cell(bool(meta.get("inverted_warning"))),
                "engine_claim": opts.get(expected, ""),
                "opposite_claim": opts.get(other, ""),
                "key_option": expected,
                "blind_answer": blind.get(qid, ""),
                "blind_agrees": _cell(_agrees(blind, qid, expected)),
                "blind_confidence": blind.get(f"{qid}.confidence", ""),
                "contaminated_answer": contam.get(qid, ""),
                "contaminated_agrees": _cell(_agrees(contam, qid, expected)),
                "contaminated_confidence": contam.get(f"{qid}.confidence", ""),
                "coinflip_answer": coin.get(qid, ""),
                "coinflip_agrees": _cell(_agrees(coin, qid, expected)),
            })
    return rows


def summarise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per (run, persona) hit counts — the aggregate the feature rows add up to.

    Denominators are per-arm because an arm that skipped an item has a smaller n on that
    persona, and dividing every arm by the same total would quietly penalise the one that
    declined to answer rather than guess.
    """
    out: dict[tuple, dict[str, Any]] = {}
    for r in rows:
        bucket = out.setdefault((r["run"], r["persona"]), {
            "run": r["run"], "persona": r["persona"], "features": 0,
            "blind_hits": 0, "blind_n": 0, "contaminated_hits": 0, "contaminated_n": 0,
            "coinflip_hits": 0, "coinflip_n": 0, "inverted_features": 0})
        bucket["features"] += 1
        bucket["inverted_features"] += int(r["inverted_channel"] or 0)
        for arm in ("blind", "contaminated", "coinflip"):
            cell = r[f"{arm}_agrees"]
            if cell != "":
                bucket[f"{arm}_n"] += 1
                bucket[f"{arm}_hits"] += int(cell)
    for bucket in out.values():
        for arm in ("blind", "contaminated", "coinflip"):
            n = bucket[f"{arm}_n"]
            bucket[f"{arm}_rate"] = round(bucket[f"{arm}_hits"] / n, 4) if n else ""
    return list(out.values())


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Per-feature persona-study results as CSV.")
    ap.add_argument("runs", nargs="+", metavar="LABEL=DIR",
                    help="one or more collected study directories, each with a label")
    ap.add_argument("--out", type=Path, required=True, help="feature-level CSV to write")
    ap.add_argument("--summary", type=Path, default=None, help="optional per-persona CSV")
    ap.add_argument("--seed", default="astrobank-persona-pilot",
                    help="coin-flip control seed; must match the seed used at score time")
    args = ap.parse_args(argv)

    rows: list[dict[str, Any]] = []
    for spec in args.runs:
        if "=" not in spec:
            raise SystemExit(f"[persona-csv] expected LABEL=DIR, got {spec!r}")
        label, _, path = spec.partition("=")
        rows += rows_for_run(label, Path(path), seed=args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[persona-csv] {len(rows)} feature rows -> {args.out}")

    if args.summary:
        summary = summarise(rows)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
            writer.writeheader()
            writer.writerows(summary)
        print(f"[persona-csv] {len(summary)} persona rows -> {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
