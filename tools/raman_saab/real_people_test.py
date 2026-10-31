"""Blind test of the For-and-against reader on real people the user knows.

Protocol: docs/raman_saab/REAL_PEOPLE_PREREG_2026-10-31.md (fixed before any person is entered).

Two steps, run at different times:

  seal  PEOPLE.json  OUT_DIR   Cast every chart, record the reader's lean (plain count) and the
                               clause judge's verdict for each questionnaire matter, write
                               OUT_DIR/sealed.json and print its SHA-256. Commit the hash to the
                               prereg log BEFORE any facts are collected or looked at.
  score SEALED.json FACTS.json Check the hash, then score each person's confirmed facts against
                               (a) their own chart, (b) every other person's chart in the batch
                               (the shuffled-chart control) and (c) "always good".

Birth data and facts of real people stay out of the repository (keep them under
/mnt/project-files/astro/real_people/). Only hashes and aggregate results are committed.

PEOPLE.json: [{"id": "P01", "year": 1989, "month": 10, "day": 12, "hour": 10, "minute": 2,
               "tz": 5.5, "lat": 27.23, "lon": 79.02, "sex": "m", "time_quality": "exact"}, ...]
FACTS.json:  {"P01": {"Q01": "good", "Q02": "bad", "Q05": "na", ...}, ...}
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

#: Questionnaire item -> (house, matter key in the For-and-against section). Fixed by the prereg.
QUESTIONS: dict[str, tuple[int, str]] = {
    "Q01": (1, "health"),
    "Q02": (2, "wealth"),
    "Q03": (2, "speech"),
    "Q04": (3, "siblings"),
    "Q05": (4, "mother"),
    "Q06": (4, "education"),
    "Q07": (4, "property"),
    "Q08": (5, "children"),
    "Q09": (6, "disease chronic"),
    "Q10": (6, "accidents"),
    "Q11": (7, "marital happiness"),
    "Q12": (9, "father"),
    "Q13": (10, "career"),
    "Q14": (11, "gains"),
    "Q15": (11, "elder siblings"),
}

_LEAN = {"leans favourable": "good", "leans afflicted": "bad"}
_JUDGE = {"favourable": "good", "afflicted": "bad"}
REFERENCE_DATE = (2026, 10, 31)


def _predict(p: dict) -> dict:
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.detailed_report import build_detailed_report

    b = BirthData(p["id"], p["year"], p["month"], p["day"], p["hour"], p["minute"],
                  float(p["tz"]), float(p["lat"]), float(p["lon"]))
    fa = build_detailed_report(b, on=REFERENCE_DATE).for_against
    by = {(m.house, m.matter): m for m in fa.matters}
    out = {}
    for q, key in QUESTIONS.items():
        m = by.get(key)
        out[q] = {
            "count": _LEAN.get(m.lean) if m else None,  # None = abstains
            "judge": _JUDGE.get(m.judge_verdict) if m else None,
            "n_for": len(m.reasons_for) if m else 0,
            "n_against": len(m.reasons_against) if m else 0,
        }
    return out


def seal(people_path: str, out_dir: str) -> int:
    people = json.loads(Path(people_path).read_text(encoding="utf-8"))
    sealed = {"reference_date": REFERENCE_DATE, "questions": QUESTIONS,
              "predictions": {p["id"]: _predict(p) for p in people}}
    blob = json.dumps(sealed, sort_keys=True, ensure_ascii=False).encode()
    out = Path(out_dir) / "sealed.json"
    out.write_bytes(blob)
    print(f"sealed {len(people)} people -> {out}\nsha256 {hashlib.sha256(blob).hexdigest()}")
    return 0


def _hits(pred: dict, facts: dict, reader: str) -> tuple[int, int]:
    """(correct, scored) over answered items where this reader commits to good/bad."""
    c = n = 0
    for q, f in facts.items():
        if f not in ("good", "bad") or q not in pred:
            continue
        guess = "good" if reader == "always_good" else pred[q][reader]
        if guess is None:
            continue
        n += 1
        c += guess == f
    return c, n


def _rate(c: int, n: int) -> float | None:
    return c / n if n else None


def score(sealed_path: str, facts_path: str, expected_sha: str | None = None) -> int:
    blob = Path(sealed_path).read_bytes()
    sha = hashlib.sha256(blob).hexdigest()
    if expected_sha and sha != expected_sha:
        print(f"HASH MISMATCH: {sha} != {expected_sha}")
        return 2
    preds = json.loads(blob)["predictions"]
    facts = json.loads(Path(facts_path).read_text(encoding="utf-8"))
    ids = [i for i in facts if i in preds]
    res: dict = {"sha256": sha, "n_people": len(ids), "per_person": {}}
    for reader in ("count", "judge"):
        diffs = []
        tot = {"own": [0, 0], "shuffled": [0, 0], "always_good": [0, 0]}
        for i in ids:
            oc, on = _hits(preds[i], facts[i], reader)
            others = [_rate(*_hits(preds[j], facts[i], reader)) for j in preds if j != i]
            others = [x for x in others if x is not None]
            gc, gn = _hits(preds[i], facts[i], "always_good")
            tot["own"][0] += oc; tot["own"][1] += on
            tot["always_good"][0] += gc; tot["always_good"][1] += gn
            if on and others:
                sh = statistics.mean(others)
                diffs.append(oc / on - sh)
                tot["shuffled"][0] += sh * on; tot["shuffled"][1] += on
            res["per_person"].setdefault(i, {})[reader] = {"own": [oc, on], "always_good": [gc, gn]}
        # person-level sign-flip permutation (one-sided: own better than shuffled)
        rng = random.Random(20261031)
        obs = statistics.mean(diffs) if diffs else 0.0
        perm = [statistics.mean(d * rng.choice((1, -1)) for d in diffs) for _ in range(20000)] if diffs else []
        p = (sum(x >= obs for x in perm) + 1) / (len(perm) + 1) if perm else None
        boots = []
        for _ in range(5000):
            s = [rng.choice(diffs) for _ in diffs] if diffs else []
            boots.append(statistics.mean(s) if s else 0.0)
        boots.sort()
        ci = (boots[int(0.05 * len(boots))], boots[int(0.95 * len(boots)) - 1]) if diffs else (None, None)
        if not diffs:
            verdict = "UNDERPOWERED"
        elif p is not None and p < 0.05 and len(ids) >= 20:
            verdict = "SIGNAL"
        elif len(ids) >= 30 and ci[1] < 0.10:
            verdict = "BOUNDED_NULL"
        else:
            verdict = "UNDERPOWERED"
        res[reader] = {
            "own_accuracy": _rate(*tot["own"]), "shuffled_accuracy": _rate(*tot["shuffled"]),
            "always_good_accuracy": _rate(*tot["always_good"]), "items_scored": tot["own"][1],
            "mean_own_minus_shuffled": obs, "ci90": ci, "p_one_sided": p, "verdict": verdict,
        }
    print(json.dumps({k: v for k, v in res.items() if k != "per_person"}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "seal":
        return seal(argv[1], argv[2])
    if len(argv) >= 3 and argv[0] == "score":
        return score(argv[1], argv[2], argv[3] if len(argv) > 3 else None)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
