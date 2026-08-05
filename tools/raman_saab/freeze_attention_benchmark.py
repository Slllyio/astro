"""Freeze the salience benchmark — Raman's own attention, split tune/holdout, before scoring.

The split is written NOW, deliberately, before any salience model exists and before anyone has
seen a score. Holdout charts are not to be inspected during development; they are the only
honest evidence that a faculty generalises rather than being fitted to 41 charts we stared at.

The split is deterministic (sorted by chart number, alternating) so it can be regenerated and
audited, and it is recorded inside the artefact itself.

Usage:
    py -3.12 tools/raman_saab/freeze_attention_benchmark.py \
        --out tests/fixtures/notable_attention.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from tools.raman_saab.extract_notable_attention import extract

SOURCE = "data/Notable Horoscopes BV Raman.txt"


def _usable(r) -> bool:
    """Castable (lat+long printed) AND Raman actually flagged something in it."""
    return (r.latitude is not None and r.longitude is not None
            and bool(r.emphasised_houses or r.emphasised_grahas))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="tests/fixtures/notable_attention.json")
    args = ap.parse_args()

    recs = extract(Path(SOURCE))
    usable = sorted([r for r in recs if _usable(r)], key=lambda r: (r.name or ""))

    # deterministic alternating split — no randomness to reproduce, no seed to lose
    for i, r in enumerate(usable):
        setattr(r, "split", "tune" if i % 2 == 0 else "holdout")

    counter = Counter(h for r in usable for h in r.emphasised_houses)
    total = sum(counter.values()) or 1
    top_house, top_n = counter.most_common(1)[0]
    top3 = [h for h, _ in counter.most_common(3)]

    payload = {
        "_about": (
            "Raman's OWN attention per worked chart, from Notable Horoscopes. The target is "
            "EXPERT ATTENTION, never life outcomes — this sits clear of the astrobank firewall "
            "and does not relitigate the measured-null generalization axis."),
        "_source": SOURCE,
        "_split": ("deterministic: usable charts sorted by name, alternating tune/holdout. "
                   "Frozen before any salience model existed or any score was seen."),
        "_usable_rule": "printed lat+long (castable) AND at least one emphasised factor",
        "_trivial_baselines": {
            "_why": ("Raman genuinely emphasises Lagna, the 10th and the 9th most often, so a "
                     "constant guess already scores well. A salience model that does not BEAT "
                     "these numbers has demonstrated nothing."),
            "always_top_house": {"house": top_house,
                                 "precision_at_1": round(top_n / len(usable), 3)},
            "always_top_3_houses": {
                "houses": top3,
                "recall_at_3": round(
                    sum(1 for r in usable if set(top3) & set(r.emphasised_houses))
                    / len(usable), 3)},
            "top_house_share_of_all_emphasis": round(top_n / total, 3),
        },
        "_counts": {
            "sections_parsed": len(recs),
            "usable": len(usable),
            "tune": sum(1 for r in usable if getattr(r, "split") == "tune"),
            "holdout": sum(1 for r in usable if getattr(r, "split") == "holdout"),
        },
        "_caveat": ("n is small. Every number computed against this benchmark must be reported "
                    "with a confidence interval, and a difference inside the interval is not a "
                    "result."),
        "charts": [asdict(r) | {"split": getattr(r, "split")} for r in usable],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"parsed {len(recs)} sections -> {len(usable)} usable")
    print(f"  tune {payload['_counts']['tune']} / holdout {payload['_counts']['holdout']}")
    print(f"  trivial p@1 (always H{top_house}) = "
          f"{payload['_trivial_baselines']['always_top_house']['precision_at_1']:.0%}")
    print(f"  trivial recall@3 (always {top3}) = "
          f"{payload['_trivial_baselines']['always_top_3_houses']['recall_at_3']:.0%}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
