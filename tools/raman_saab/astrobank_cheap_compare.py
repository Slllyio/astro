"""Zero-agent, corpus-scale version of the wide feature comparison.

No research, no LLM calls at all. Real-life verdicts come from tags ALREADY scraped into
`data/astro_databank/raw_holos_full.csv` (the AstroDatabank/holos categories field) — this
script only parses strings and runs the engine. Engine verdicts are computed directly from
each chart, same as always.

Honesty limits, stated once here rather than per row:
* These category tags were assigned by astrology researchers cataloguing notable charts. Hard
  counts (marriages, kids, awards) are just facts and safe to trust. Softer trait tags
  ("Courageous", "Aggressive") were chosen by someone who may already know the chart — treat
  agreement on those with more skepticism than the factual ones.
* `career`, `status_honour`, `wealth`, `profession_authority`, `profession_trade`,
  `profession_learned`, `profession_labour`, `gains`, `acquisitions` are left out entirely
  (removed after the 500-person pilot found career/status/wealth worthless): this corpus is
  AstroDatabank, which only contains notable people, so `Notable: Famous` / `Awards` /
  `Vocation:*` tags just restate corpus membership. Any "match" on a success-shaped feature
  here is circular, not a finding about the engine.
* `siblings`, `elder_siblings`, `friends`, `debts`, `expenditure`, `vehicles`, `vision`,
  `ear_throat`, `speech`, `short_journeys`, `long_journeys`, `dharma`, `moksha`, `loss_moksha`,
  `sudden_gains` have NO usable tag in this corpus at all and are skipped — forcing a verdict
  from nothing would manufacture false precision. `courage` keeps only its favourable tag
  (`Personality: Courageous`); there is no ethical, non-reductive way to code a negative
  signal for it from this corpus (the closest tag is suicide, and treating that as a
  personality-trait miss is not something this project will do).
* SHARED-SOURCE GROUPS — these features reuse the SAME underlying tags because no more
  specific tag exists, so their results move together and are NOT independent confirmations
  of each other:
    - marriage group (spouse, marital_happiness, virility, coverture, partnership,
      wealth_through_marriage) — all read off the same Family:Relationship marriage/divorce
      tags. The house differs per signification; the ground truth does not.
    - childhood-family group (father, mother, education, home_comforts, happiness) — all
      read off the same Family:Childhood tags. Same caveat.
    - health group (health, disease_chronic, enemies_disease) — all read off the same
      Diagnoses tag.

Usage:
    py -3.12 -m tools.raman_saab.astrobank_cheap_compare --limit 500 \
        --out data/astrobank_persona_pilot/corpus_wide_features.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

_SRC = Path("data/astro_databank/raw_holos_full.csv")

#: feature -> {"favourable": [tag substrings], "afflicted": [tag substrings]}
#: A tag is matched by substring, case-sensitive to the source's own casing.
TAG_RULES: dict[str, dict[str, list[str]]] = {
    "health": {
        "afflicted": ["Diagnoses :", "Personal : Death : Illness/ Disease",
                      "Personal : Birth : Defects, Handicaps", "Personal : Birth : Premature"],
        "favourable": ["Traits : Body : Constitution hardy"],
    },
    "children": {
        "afflicted": ["Family : Parenting : Kids none", "Family : Parenting : Kids -Traumatic event"],
        "favourable": ["Family : Parenting : Kids 1-3", "Family : Parenting : Kids more than 3"],
    },
    "foreign_residence": {
        "afflicted": [],
        "favourable": ["Lifestyle : Home : Expatriate"],
    },
    "higher_learning": {
        "afflicted": ["Traits : Mind : Education limited"],
        "favourable": ["Traits : Mind : Education extensive", "Traits : Mind : I.Q. high/ Mensa level",
                       "Traits : Mind : Exceptional mind", "Traits : Mind : Child prodigy"],
    },
    "courage": {
        "afflicted": [],
        "favourable": ["Traits : Personality : Courageous"],
    },
    "legacies": {
        "afflicted": [],
        "favourable": ["Lifestyle : Financial : Gain - Inheritance"],
    },
    "poorvapunya": {
        "afflicted": [],
        "favourable": ["Lifestyle : Financial : Gain - Grant, Scholarship, etc."],
    },
    "incarceration": {
        "afflicted": ["Passions : Criminal Perpetrator : Prison sentence",
                      "Passions : Criminal Victim : Concentration camp"],
        "favourable": [],
    },
    "enemies": {
        "afflicted": ["Passions : Criminal Victim :"],
        "favourable": [],
    },
    "accidents": {
        "afflicted": ["Personal : Death : Accidental"],
        "favourable": [],
    },
}

#: Marriage group — spouse/marital_happiness/virility/coverture/partnership/wealth_through_marriage
#: all read off the SAME marriage tags (no more specific tag exists per signification).
_MARRIAGE_TAGS = {
    "afflicted": ["Family : Relationship : Number of Divorces",
                  "Family : Relationship : Marriage less than 3 Yrs",
                  "Family : Relationship : Married late/never",
                  "Family : Relationship : Stress - Extramarital affairs",
                  "Family : Relationship : Widowed"],
    "favourable": ["Family : Relationship : Marriage more than 15 Yrs"],
}
for _sig in ("spouse", "marital_happiness", "virility", "coverture", "partnership",
             "wealth_through_marriage"):
    TAG_RULES[_sig] = _MARRIAGE_TAGS

#: Childhood-family group — father/mother/education/home_comforts/happiness all read off the
#: SAME childhood tags (the data does not distinguish which parent or which specific matter).
_FAMILY_TAGS = {
    "afflicted": ["Family : Childhood : Family traumatic event", "Family : Childhood : Parents divorced",
                  "Family : Childhood : Disadvantaged", "Family : Childhood : Memories Bad"],
    "favourable": ["Family : Childhood : Family close", "Family : Childhood : Family supportive",
                   "Family : Childhood : Advantaged"],
}
for _sig in ("father", "mother", "education", "home_comforts", "happiness"):
    TAG_RULES[_sig] = _FAMILY_TAGS

#: Health group — health/disease_chronic/enemies_disease all read off the SAME diagnosis tag.
_HEALTH_TAGS = {
    "afflicted": ["Diagnoses :", "Personal : Death : Illness/ Disease",
                  "Personal : Birth : Defects, Handicaps", "Personal : Birth : Premature"],
    "favourable": ["Traits : Body : Constitution hardy"],
}
for _sig in ("health", "disease_chronic", "enemies_disease"):
    TAG_RULES[_sig] = _HEALTH_TAGS

#: Which features share a ground-truth source with which others — for reporting, not scoring.
SHARED_SOURCE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("spouse", "marital_happiness", "virility", "coverture", "partnership", "wealth_through_marriage"),
    ("father", "mother", "education", "home_comforts", "happiness"),
    ("health", "disease_chronic", "enemies_disease"),
)

FEATURES = list(TAG_RULES)


def classify(categories: str) -> dict[str, str]:
    """Feature -> favourable/afflicted/mixed/(absent from dict = not scored).

    'mixed' when both directions' tags are present on the same person (e.g. a long marriage
    AND a divorce from an earlier one) — a real split, not an unknown.
    """
    tags = [c.strip() for c in categories.split(";") if c.strip()]
    out: dict[str, str] = {}
    for feature, rules in TAG_RULES.items():
        hit_fav = any(any(s in t for s in rules["favourable"]) for t in tags)
        hit_afl = any(any(s in t for s in rules["afflicted"]) for t in tags)
        if hit_fav and hit_afl:
            out[feature] = "mixed"
        elif hit_fav:
            out[feature] = "favourable"
        elif hit_afl:
            out[feature] = "afflicted"
    return out


def select_rows(limit: int, min_features: int = 4) -> list[dict]:
    """AA/A rated, real time, and enough tag coverage to be worth scoring — first N found in
    file order, not cherry-picked for favourable outcomes."""
    rows = list(csv.DictReader(_SRC.open(encoding="utf-8")))
    picked = []
    for r in rows:
        if r["rodden_rating"] not in ("AA", "A"):
            continue
        if r["time_of_birth"] in ("12:00:00", "00:00:00"):
            continue
        if not (r["latitude"] and r["longitude"] and r["tz_offset"]):
            continue
        classified = classify(r["categories"])
        if len(classified) < min_features:
            continue
        picked.append(r)
        if len(picked) >= limit:
            break
    return picked


def engine_verdicts(row: dict) -> dict[str, str]:
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.judges import house_template as ht

    y, m, d = row["date_of_birth"].split("-")
    hh, mm, _ = row["time_of_birth"].split(":")
    birth = BirthData(row["name"], int(y), int(m), int(d), int(hh), int(mm),
                       float(row["tz_offset"]), float(row["latitude"]), float(row["longitude"]))
    chart = cast_chart(birth, ayanamsa="raman")
    out: dict[str, str] = {}
    for h in range(1, 13):
        for sv in ht.judge_house(chart, h).significations:
            if sv.signification in TAG_RULES:
                out[sv.signification] = sv.verdict
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--min-features", type=int, default=4)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rows = select_rows(args.limit, min_features=args.min_features)
    print(f"[cheap-compare] {len(rows)} people selected (AA/A rated, real time, "
          f">=4 features tagged)")

    fieldnames = ["name"] + [f"{f}_{s}" for f in FEATURES for s in ("engine", "real", "match")]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    hits = n = 0
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            real = classify(row["categories"])
            try:
                engine = engine_verdicts(row)
            except Exception as exc:                          # noqa: BLE001 — bad ephemeris input
                print(f"  skip {row['name']!r}: {exc}")
                continue
            out_row = {"name": row["name"]}
            for f in FEATURES:
                e = engine.get(f, "?")
                r = real.get(f, "")
                out_row[f"{f}_engine"] = e
                out_row[f"{f}_real"] = r
                if r in ("favourable", "afflicted") and e in ("favourable", "afflicted"):
                    match = int(e == r)
                    out_row[f"{f}_match"] = match
                    hits += match
                    n += 1
                else:
                    out_row[f"{f}_match"] = ""
            writer.writerow(out_row)
            if i % 100 == 0:
                print(f"  {i}/{len(rows)}...")
    print(f"[cheap-compare] wrote {args.out}")
    print(f"[cheap-compare] overall: {hits}/{n} = {hits/n:.4f}" if n else "[cheap-compare] no scoreable cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
