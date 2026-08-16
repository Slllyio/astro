"""Research test: does the chart context actually help an LLM predict
biographical events?

After Round-9 closed the population-statistics doctrine claim as null,
the natural follow-up question is: does the chart carry semantic
content that helps an LLM read a life, even if it doesn't carry
population-statistics signal?

## Design

For each of N test subjects with documented events:

  1. Compute their chart (signs of 9 planets + MD lord).
  2. Generate an LLM prediction WITH the real chart context:
     "Given this chart, score the likelihood (0-10) of each event
     category for this person's life."
  3. Generate an LLM prediction WITH a SHUFFLED chart (planet signs
     randomly permuted — preserves "having a chart" but destroys
     the structural information).
  4. Score both: AUC of predicted scores vs actual event categories
     present in the person's documented life.

## Hypothesis

* H0 (null): real-chart AUC = shuffled-chart AUC. The LLM extracts no
  doctrinal information from chart structure.
* H1 (alt): real-chart AUC > shuffled-chart AUC. Chart structure
  carries semantic content the LLM can exploit.

If H0, the cross-corpus null verdict is confirmed at the semantic
level: even an LLM with classical-doctrine training cannot decode
the chart into events.

If H1, the doctrine has individual-reading-level signal that
population statistics missed — interesting positive result.

## Implementation

Uses the production ``chart_reader`` synthesis path for the with-chart
condition and a custom shuffle-helper for the shuffled-chart condition.
Output is a structured JSON report + per-subject CSV.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

from app.core.config import settings
from app.llm.client import LLMClient, OllamaClient, OllamaUnavailable

logger = logging.getLogger(__name__)


# 14 event categories — same set as our doctrine scorer.
EVENT_CATEGORIES = (
    "marriage", "relationship", "career", "work", "fame",
    "death", "health", "education", "finance", "legal",
    "personal", "family", "accidents", "crime",
)


# --------------------------------------------------------------------------- #
# Map event_root strings to our 14 categories                                  #
# --------------------------------------------------------------------------- #

_ROOT_TO_CATEGORY: dict[str, str] = {
    "Marriage": "marriage",
    "Relationship": "relationship",
    "career": "career", "New Career": "career", "Career change": "career",
    "Work": "work", "New Job": "work", "Lose social status": "work",
    "fame": "fame", "Prize": "fame", "Awards": "fame", "Published/ Exhibited/ Released": "fame",
    "Death, Cause unspecified": "death", "Death by Disease": "death",
    "Death by Accident": "death", "Death by Suicide": "death",
    "Death by Heart Attack": "death", "Death by War or terrorism": "death",
    "Health": "health", "Major Diseases": "health", "Body Part Problems": "health",
    "Education": "education",
    "Financial": "finance", "Wealth large": "finance", "Wealth Less than wealthy": "finance",
    "Legal": "legal",
    "Family": "family",
    "Accidents": "accidents",
    "Crime": "crime",
}


def _category_for_event_root(root: str) -> str | None:
    """Best-effort map of event_root → one of our 14 categories."""
    if root in _ROOT_TO_CATEGORY:
        return _ROOT_TO_CATEGORY[root]
    rl = (root or "").lower()
    for k, v in _ROOT_TO_CATEGORY.items():
        if k.lower() in rl:
            return v
    return None


# --------------------------------------------------------------------------- #
# Subject selection                                                            #
# --------------------------------------------------------------------------- #

def select_subjects(
    event_df: pd.DataFrame,
    *,
    n: int = 50,
    min_event_classes: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """Select N people with ≥ min_event_classes distinct documented
    event categories. Returns one row per person with: name, birth_jd,
    a list of (event_class, year) tuples, and a set of unique
    event_classes."""
    rng = random.Random(seed)
    grouped = event_df.groupby("name")
    candidates: list[dict] = []
    for name, group in grouped:
        cats = set()
        events = []
        for _, row in group.iterrows():
            cat = _category_for_event_root(row.get("event_root", ""))
            if cat:
                cats.add(cat)
                events.append((cat, row["event_jd"]))
        if len(cats) >= min_event_classes:
            candidates.append({
                "name": name,
                "birth_jd": float(group.iloc[0]["birth_jd"]),
                "event_categories": sorted(cats),
                "n_events": len(events),
                "events": events,
                "moon_longitude": float(group.iloc[0].get("lon_moon", 0.0)),
            })
    rng.shuffle(candidates)
    return pd.DataFrame(candidates[:n])


# --------------------------------------------------------------------------- #
# Chart compute + shuffle                                                      #
# --------------------------------------------------------------------------- #

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu")
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _real_chart(birth_jd: float, person_natal: pd.Series) -> dict:
    """Pull real planet signs from the natal-lord-houses parquet row."""
    return {
        p: int(person_natal.get(f"sign_{p.lower()}", 0))
        for p in _PLANETS
    }


def _shuffle_chart(real: dict[str, int], rng: random.Random) -> dict[str, int]:
    """Random permutation: keep each planet present, shuffle its sign.

    This preserves the planet set but destroys the structural information
    (which sign each planet is in). The LLM still sees a "valid-looking"
    chart but the doctrine-determined relationships are scrambled.
    """
    signs = list(real.values())
    rng.shuffle(signs)
    return {p: s for p, s in zip(real.keys(), signs)}


# --------------------------------------------------------------------------- #
# LLM prediction prompt                                                        #
# --------------------------------------------------------------------------- #

def _build_prompt(planet_signs: dict[str, int]) -> str:
    """Single prompt asking LLM to score 14 categories from chart."""
    sign_lines = "\n".join(
        f"  {planet}: {_SIGNS[s - 1]}"
        for planet, s in planet_signs.items() if 1 <= s <= 12
    )
    cat_list = ", ".join(EVENT_CATEGORIES)
    return (
        "CHART (planet signs)\n"
        f"{sign_lines}\n\n"
        "TASK\n"
        "  This person's life is documented. Predict which life-event "
        "  categories appear in their biography. For EACH category in "
        "  the list below, output a single line:\n"
        "    <category>: <score 0-10>\n"
        "  where 10 = certain to appear, 0 = certain NOT to appear. "
        "  Use the chart's structural information to inform your scores.\n\n"
        f"CATEGORIES: {cat_list}\n\n"
        "OUTPUT (one line per category, format 'category: score'):"
    )


_SCORE_LINE = __import__("re").compile(
    r"\b(" + "|".join(EVENT_CATEGORIES) + r")\b[:\s]+(\d+(?:\.\d+)?)",
    flags=__import__("re").IGNORECASE,
)


def _parse_scores(text: str) -> dict[str, float]:
    """Extract {category: score} from LLM output. Robust to formatting."""
    out: dict[str, float] = {}
    for m in _SCORE_LINE.finditer(text):
        cat = m.group(1).lower()
        try:
            s = float(m.group(2))
        except ValueError:
            continue
        if cat in EVENT_CATEGORIES and cat not in out:
            out[cat] = max(0.0, min(10.0, s))
    return out


def predict_scores(
    planet_signs: dict[str, int], client: LLMClient,
) -> dict[str, float]:
    """Returns a {category: score} prediction. Empty dict on LLM failure."""
    prompt = _build_prompt(planet_signs)
    try:
        text = client.complete(prompt)
    except OllamaUnavailable:
        return {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM call failed: %s", exc)
        return {}
    return _parse_scores(text)


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    event_path: Path, natal_path: Path, out_dir: Path,
    *, n_subjects: int = 50, min_event_classes: int = 3, seed: int = 42,
) -> dict:
    event_df = pd.read_parquet(event_path)
    natal_df = pd.read_parquet(natal_path)
    natal_df["name_norm"] = natal_df["name_norm"].astype(str)
    natal_idx = natal_df.set_index("name_norm")

    subjects = select_subjects(
        event_df, n=n_subjects, min_event_classes=min_event_classes, seed=seed,
    )
    logger.info("selected %d subjects (min event classes = %d)",
                len(subjects), min_event_classes)

    client = OllamaClient(
        host=settings.OLLAMA_HOST,
        model=settings.OLLAMA_MODEL,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
    )

    rng = random.Random(seed)
    per_subject: list[dict] = []
    for i, subj in subjects.iterrows():
        name = subj["name"]
        name_norm = name.lower().strip()
        if name_norm not in natal_idx.index:
            continue
        nat = natal_idx.loc[name_norm]
        if isinstance(nat, pd.DataFrame):
            nat = nat.iloc[0]
        real_chart = _real_chart(subj["birth_jd"], nat)
        shuf_chart = _shuffle_chart(real_chart, rng)
        scores_real = predict_scores(real_chart, client)
        scores_shuf = predict_scores(shuf_chart, client)
        if not (scores_real and scores_shuf):
            logger.warning("[%d/%d] %s — LLM returned empty for one condition; skipping",
                           i, len(subjects), name)
            continue
        # Build ground-truth label vector: 1 if person has any event in
        # this category, 0 otherwise.
        truth_cats = set(subj["event_categories"])
        y_true = [1 if c in truth_cats else 0 for c in EVENT_CATEGORIES]
        y_real = [scores_real.get(c, 0.0) for c in EVENT_CATEGORIES]
        y_shuf = [scores_shuf.get(c, 0.0) for c in EVENT_CATEGORIES]
        if 0 < sum(y_true) < len(y_true):
            try:
                auc_real = float(roc_auc_score(y_true, y_real))
                auc_shuf = float(roc_auc_score(y_true, y_shuf))
            except ValueError:
                continue
        else:
            continue
        per_subject.append({
            "name": name,
            "n_true_cats": int(sum(y_true)),
            "auc_real_chart": auc_real,
            "auc_shuffled_chart": auc_shuf,
            "lift": auc_real - auc_shuf,
            "y_true": y_true, "y_real_scores": y_real, "y_shuf_scores": y_shuf,
        })
        if (i + 1) % 10 == 0:
            logger.info("[%d/%d] processed", i + 1, len(subjects))

    # Aggregate
    df = pd.DataFrame(per_subject)
    if df.empty:
        return {"error": "no valid subjects processed"}
    aucs_real = df["auc_real_chart"].to_numpy()
    aucs_shuf = df["auc_shuffled_chart"].to_numpy()
    lifts = aucs_real - aucs_shuf
    # Paired Wilcoxon: does real_chart_AUC exceed shuf_chart_AUC?
    try:
        stat, p_two = wilcoxon(aucs_real, aucs_shuf, alternative="greater")
    except ValueError:
        stat, p_two = float("nan"), float("nan")

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "per_subject_scores.csv", index=False)
    summary = {
        "n_subjects": int(len(df)),
        "mean_auc_real": float(aucs_real.mean()),
        "mean_auc_shuf": float(aucs_shuf.mean()),
        "mean_lift": float(lifts.mean()),
        "std_lift": float(lifts.std()),
        "wilcoxon_p_one_sided_greater": float(p_two),
        "n_lift_positive": int((lifts > 0).sum()),
        "n_lift_zero": int((lifts == 0).sum()),
        "n_lift_negative": int((lifts < 0).sum()),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.chart_reading_research",
    )
    parser.add_argument(
        "--event-corpus", type=Path,
        default=Path("app/medini/data/event_corpus_all.parquet"),
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/natal_lord_houses.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/chart_reading_research"),
    )
    parser.add_argument("--n-subjects", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(
        args.event_corpus, args.natal, args.out,
        n_subjects=args.n_subjects, seed=args.seed,
    )
    print()
    print("=== Chart-reading research test ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
