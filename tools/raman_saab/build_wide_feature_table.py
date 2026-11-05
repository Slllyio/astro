"""One-off: build the wide person x feature comparison table for the astrobank pilot roster.

Engine verdicts come straight from the chart judge (free, deterministic). Real-life verdicts
are hand-classified from well-documented public biography — much of it already gathered in
`tests/fixtures/astrobank_persona_pilot_deep/answers/*.json`, the rest from general knowledge
of these public figures. This is NOT the rigorous blind/forced-choice methodology
(`persona_study.py`) — it is the cheap, direct comparison requested as an alternative to it.
Treat REAL_LIFE as an informed judgment call, not independently re-sourced per cell; ambiguous
ones are marked "mixed" rather than forced to a side.

Usage:
    py -3.12 -m tools.raman_saab.build_wide_feature_table --out data/astrobank_persona_pilot/wide_features.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FEATURES = [
    "health", "spouse", "marital_happiness", "children", "career", "wealth",
    "father", "mother", "siblings", "elder_siblings", "friends", "courage",
    "expenditure", "foreign_residence", "higher_learning", "status_honour",
]

#: Hand-classified from public biography. "mixed" where the real record is genuinely split
#: (e.g. a happy second marriage after a failed first one), not where it is merely uncertain.
REAL_LIFE: dict[str, dict[str, str]] = {
    "Steve Jobs": dict(health="afflicted", spouse="favourable", marital_happiness="favourable",
        children="mixed", career="favourable", wealth="favourable", father="mixed",
        mother="mixed", siblings="favourable", elder_siblings="none_documented",
        friends="favourable", courage="favourable", expenditure="mixed",
        foreign_residence="afflicted", higher_learning="afflicted", status_honour="favourable"),
    "Michael Jackson": dict(health="afflicted", spouse="afflicted", marital_happiness="afflicted",
        children="favourable", career="favourable", wealth="mixed", father="afflicted",
        mother="favourable", siblings="mixed", elder_siblings="mixed", friends="mixed",
        courage="mixed", expenditure="afflicted", foreign_residence="mixed",
        higher_learning="afflicted", status_honour="mixed"),
    "John Lennon": dict(health="mixed", spouse="mixed", marital_happiness="afflicted",
        children="mixed", career="favourable", wealth="favourable", father="afflicted",
        mother="afflicted", siblings="mixed", elder_siblings="none_documented",
        friends="favourable", courage="favourable", expenditure="mixed",
        foreign_residence="favourable", higher_learning="afflicted", status_honour="favourable"),
    "David Bowie": dict(health="afflicted", spouse="favourable", marital_happiness="mixed",
        children="favourable", career="favourable", wealth="favourable", father="favourable",
        mother="afflicted", siblings="afflicted", elder_siblings="afflicted",
        friends="favourable", courage="favourable", expenditure="afflicted",
        foreign_residence="favourable", higher_learning="afflicted", status_honour="favourable"),
    "Madonna": dict(health="afflicted", spouse="afflicted", marital_happiness="afflicted",
        children="mixed", career="favourable", wealth="favourable", father="mixed",
        mother="afflicted", siblings="afflicted", elder_siblings="mixed", friends="favourable",
        courage="favourable", expenditure="mixed", foreign_residence="favourable",
        higher_learning="afflicted", status_honour="mixed"),
    "Muhammad Ali": dict(health="afflicted", spouse="afflicted", marital_happiness="mixed",
        children="favourable", career="favourable", wealth="favourable", father="afflicted",
        mother="favourable", siblings="favourable", elder_siblings="none_documented",
        friends="mixed", courage="favourable", expenditure="afflicted",
        foreign_residence="mixed", higher_learning="afflicted", status_honour="favourable"),
    "Mother Teresa": dict(health="afflicted", spouse="afflicted", marital_happiness="afflicted",
        children="afflicted", career="favourable", wealth="afflicted", father="afflicted",
        mother="favourable", siblings="mixed", elder_siblings="favourable", friends="favourable",
        courage="favourable", expenditure="favourable", foreign_residence="favourable",
        higher_learning="mixed", status_honour="favourable"),
    "Margaret Thatcher": dict(health="afflicted", spouse="favourable", marital_happiness="favourable",
        children="mixed", career="favourable", wealth="favourable", father="favourable",
        mother="mixed", siblings="mixed", elder_siblings="mixed", friends="mixed",
        courage="favourable", expenditure="mixed", foreign_residence="mixed",
        higher_learning="favourable", status_honour="favourable"),
    "Bill Clinton": dict(health="afflicted", spouse="mixed", marital_happiness="afflicted",
        children="favourable", career="favourable", wealth="favourable", father="afflicted",
        mother="favourable", siblings="mixed", elder_siblings="none_documented",
        friends="favourable", courage="mixed", expenditure="favourable",
        foreign_residence="favourable", higher_learning="favourable", status_honour="mixed"),
    "Justin Trudeau": dict(health="favourable", spouse="afflicted", marital_happiness="afflicted",
        children="favourable", career="mixed", wealth="favourable", father="favourable",
        mother="afflicted", siblings="afflicted", elder_siblings="none_documented",
        friends="mixed", courage="mixed", expenditure="mixed", foreign_residence="mixed",
        higher_learning="mixed", status_honour="mixed"),
    "Jacinda Ardern": dict(health="favourable", spouse="favourable", marital_happiness="favourable",
        children="mixed", career="favourable", wealth="favourable", father="favourable",
        mother="favourable", siblings="favourable", elder_siblings="favourable",
        friends="favourable", courage="favourable", expenditure="favourable",
        foreign_residence="mixed", higher_learning="favourable", status_honour="favourable"),
    "Emmanuel Macron": dict(health="favourable", spouse="favourable", marital_happiness="favourable",
        children="afflicted", career="mixed", wealth="favourable", father="favourable",
        mother="favourable", siblings="favourable", elder_siblings="none_documented",
        friends="mixed", courage="mixed", expenditure="favourable", foreign_residence="mixed",
        higher_learning="favourable", status_honour="mixed"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-json", type=Path,
                    default=Path("data/astrobank_persona_pilot/engine_verdicts_15.json"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    engine = {row["name"]: row for row in json.loads(args.engine_json.read_text(encoding="utf-8"))}

    fieldnames = ["name"]
    for f in FEATURES:
        fieldnames += [f"{f}_engine", f"{f}_real", f"{f}_match"]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for name, real in REAL_LIFE.items():
            row = {"name": name}
            for f in FEATURES:
                e = engine.get(name, {}).get(f, "?")
                r = real.get(f, "?")
                match = "" if r == "none_documented" else str(int(e == r))
                row[f"{f}_engine"] = e
                row[f"{f}_real"] = r
                row[f"{f}_match"] = match
            writer.writerow(row)
    print(f"[wide-features] {len(REAL_LIFE)} people x {len(FEATURES)} features -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
