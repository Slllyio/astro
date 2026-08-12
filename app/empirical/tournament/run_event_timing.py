"""Event timing — the within-person transit test.

This is the tournament's second target, and the one the Gauquelin corpus could
never reach: **does the sky at the moment something happened look different from
the sky at moments when it did not?**

The design is within-person by construction, which is what makes it worth
running. Each person supplies their own controls: their real death date, plus
several counterfactual dates drawn from their own adult life. Because every
candidate belongs to the *same person* with the *same natal chart*, birth era,
birthplace, nationality and selection into Wikidata are all held exactly fixed.
The confound that killed every population-scale test in this repo — chart
features proxying for birth epoch — cannot operate here at all: the natal chart
is identical across a person's candidates.

What varies between candidates is only the transiting sky and the person's age.

**Age is therefore the whole battle.** Death is overwhelmingly predicted by being
older, and a true death date is later in life than a uniformly-sampled control.
The chartless twin is built to exploit that fully — age, age², and the calendar
harmonics — so the transit bank has to beat a baseline that already knows the
single most predictive fact about dying. Anything less would be a rigged
comparison.

Birth times are absent (tier C), so this uses noon UT for the natal cast. That is
honest for the slow planets — Jupiter moves ~0.08°/day, Saturn ~0.03° — and
would not be for the Moon or the angles, which is why neither appears here.

Usage:
    python -m app.empirical.tournament.run_event_timing \
        --persons data/empirical/wikidata_persons.csv \
        --events data/empirical/wikidata_events.csv \
        --out data/empirical/event_timing_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.empirical.tournament.controls import sham_tolerance_for
from app.empirical.tournament.holdout import assign_holdout, check_person_leak
from app.empirical.western.angles import separation
from app.empirical.western.tropical import julian_day_ut, tropical_position

logger = logging.getLogger(__name__)

__all__ = ["CandidateSet", "build_matrix", "run_event_timing", "within_person_sham"]

_SALT: Final[str] = "wikidata-death-timing-v1"

#: Only the slow movers. With no birth time, a noon-UT cast places these to well
#: under a degree; the Moon would be anywhere in a 13° arc and is excluded.
_TRANSIT_BODIES: Final[tuple[str, ...]] = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
_NATAL_BODIES: Final[tuple[str, ...]] = ("Sun", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")

#: Harmonics of the transit-to-natal separation. k=1 peaks at conjunction, k=2 at
#: conjunction and opposition, k=4 adds the squares. Encoding the angle this way
#: rather than as raw degrees means the model sees 359° and 1° as adjacent.
_HARMONICS: Final[tuple[int, ...]] = (1, 2, 4)

#: Counterfactual dates per person.
_N_CONTROLS: Final[int] = 4

#: Controls are never drawn within this many days of the real death date — a
#: control that lands a week before death is not a counterfactual, it is a
#: near-duplicate of the event and would wash out any real effect.
_EXCLUSION_DAYS: Final[float] = 180.0

#: Candidates start here. Before adulthood the transit sky and the age variable
#: are both far from the event, which inflates the baseline's job rather than
#: testing the chart.
_MIN_AGE: Final[float] = 20.0

#: Controls are drawn from a narrow band ending at the event, NOT from the whole
#: adult life. This is the fix for a degenerate first version.
#:
#: Death is terminal, so every control necessarily precedes it — which meant a
#: whole-life window made the real date the person's LATEST candidate every time,
#: and age identified it by construction. The chartless baseline scored 0.9877,
#: leaving 1.2% of headroom: the transits could not have demonstrated anything
#: even if they carried signal.
#:
#: Confining controls to the final few years puts every candidate at a similar
#: age, so age can no longer separate them and the transiting sky gets a fair
#: test. The cost is honest and stated: this now asks "why THIS month rather than
#: a nearby one", not "why this year of life".
_CONTROL_WINDOW_YEARS: Final[float] = 3.0


@dataclass(frozen=True, slots=True)
class CandidateSet:
    """One person's real event date plus their own counterfactuals."""

    person_id: str
    natal_jd: float
    true_jd: float
    control_jds: tuple[float, ...]


def _read_corpus(
    persons_path: str | Path,
    events_path: str | Path,
) -> dict[str, tuple[float, float]]:
    """person_id -> (natal_jd, death_jd), for quality-ok rows only."""
    persons: dict[str, float] = {}
    with Path(persons_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["data_quality"] != "ok":
                continue
            try:
                # Noon UT: no birth time exists, and noon minimises the maximum
                # error against the unknown true time.
                persons[row["person_id"]] = julian_day_ut(
                    int(row["birth_year"]), int(row["birth_month"]), int(row["birth_day"]), 12.0
                )
            except (ValueError, KeyError):
                continue

    out: dict[str, tuple[float, float]] = {}
    with Path(events_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            person_id = row["person_id"]
            if person_id not in out and person_id in persons and row["event_class"] == "death":
                try:
                    death_jd = julian_day_ut(
                        int(row["event_year"]), int(row["event_month"]), int(row["event_day"]), 12.0
                    )
                except (ValueError, KeyError):
                    continue
                out[person_id] = (persons[person_id], death_jd)
    return out


def build_candidates(
    corpus: dict[str, tuple[float, float]],
    *,
    sample: int,
    seed: int = 7,
) -> list[CandidateSet]:
    """Draw each person's counterfactual dates from their own adult life."""
    rng = np.random.default_rng(seed)
    person_ids = sorted(corpus)
    if sample and sample < len(person_ids):
        person_ids = [person_ids[i] for i in rng.choice(len(person_ids), sample, replace=False)]

    out: list[CandidateSet] = []
    for person_id in person_ids:
        natal_jd, true_jd = corpus[person_id]
        adulthood = natal_jd + _MIN_AGE * 365.25
        window_start = max(adulthood, true_jd - _CONTROL_WINDOW_YEARS * 365.25)
        if true_jd - window_start < 2 * _EXCLUSION_DAYS:
            continue  # too short a window to hold distinct controls

        controls: list[float] = []
        for _ in range(_N_CONTROLS * 8):
            if len(controls) == _N_CONTROLS:
                break
            candidate = float(rng.uniform(window_start, true_jd))
            if abs(candidate - true_jd) < _EXCLUSION_DAYS:
                continue
            controls.append(candidate)
        if len(controls) < _N_CONTROLS:
            continue
        out.append(CandidateSet(person_id, natal_jd, true_jd, tuple(controls)))
    return out


def _natal_longitudes(natal_jd: float) -> dict[str, float]:
    return {b: tropical_position(natal_jd, b).longitude for b in _NATAL_BODIES}


def _features(
    jd: float,
    natal: dict[str, float],
    natal_jd: float,
) -> tuple[list[float], list[float]]:
    """``(chartless, transit)`` feature vectors for one candidate date."""
    age = (jd - natal_jd) / 365.25
    decimal_year = 1900.0 + (jd - 2415020.5) / 365.25

    chartless = [
        age,
        age * age,
        math.sin(2 * math.pi * decimal_year),
        math.cos(2 * math.pi * decimal_year),
        math.sin(2 * math.pi * decimal_year / 11.862),
        math.cos(2 * math.pi * decimal_year / 11.862),
        math.sin(2 * math.pi * decimal_year / 29.457),
        math.cos(2 * math.pi * decimal_year / 29.457),
    ]

    transit: list[float] = []
    for body in _TRANSIT_BODIES:
        transit_lon = tropical_position(jd, body).longitude
        for natal_body in _NATAL_BODIES:
            sep = separation(transit_lon, natal[natal_body])
            radians = math.radians(sep)
            for k in _HARMONICS:
                transit.append(math.cos(k * radians))
    return chartless, transit


def build_matrix(
    candidates: list[CandidateSet],
    *,
    progress_every: int = 2000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``(chartless, transit, y, person_index)`` over every candidate date."""
    chartless_rows: list[list[float]] = []
    transit_rows: list[list[float]] = []
    labels: list[int] = []
    person_index: list[int] = []

    for i, candidate in enumerate(candidates):
        natal = _natal_longitudes(candidate.natal_jd)
        for jd, is_true in [(candidate.true_jd, 1)] + [(c, 0) for c in candidate.control_jds]:
            chartless, transit = _features(jd, natal, candidate.natal_jd)
            chartless_rows.append(chartless)
            transit_rows.append(transit)
            labels.append(is_true)
            person_index.append(i)
        if progress_every and (i + 1) % progress_every == 0:
            logger.info("  %d/%d persons", i + 1, len(candidates))

    return (
        np.asarray(chartless_rows, dtype=float),
        np.asarray(transit_rows, dtype=float),
        np.asarray(labels, dtype=int),
        np.asarray(person_index, dtype=int),
    )


def within_person_sham(
    y: np.ndarray,
    person_index: np.ndarray,
    *,
    seed: int,
) -> np.ndarray:
    """Permute the event label WITHIN each person, not across the corpus.

    A within-person design carries exactly one true date per person. A global
    permutation does not preserve that: measured on a 5-candidate design it
    leaves 32% of people with no true date and 25% with two or more, and the
    resulting structural distortion — not any pipeline leak — pushes the sham
    statistic off 0.500.

    Permuting inside each person's own block keeps the design intact and
    destroys only what the sham is meant to destroy: the association between the
    sky and which of that person's dates was the real one.
    """
    rng = np.random.default_rng(seed)
    out = np.zeros_like(y)
    for person in np.unique(person_index):
        mask = person_index == person
        out[mask] = rng.permutation(y[mask])
    return out


def _within_person_auc(
    scores: np.ndarray,
    labels: np.ndarray,
    person_index: np.ndarray,
) -> float:
    """Share of (true, control) pairs where the true date scores higher.

    This is the statistic that matters: it asks whether the real event outranks
    that same person's own counterfactuals. Ties count as half, so a model with
    no information scores exactly 0.5.
    """
    wins = 0.0
    total = 0
    for person in np.unique(person_index):
        mask = person_index == person
        person_scores, person_labels = scores[mask], labels[mask]
        true_scores = person_scores[person_labels == 1]
        control_scores = person_scores[person_labels == 0]
        if not len(true_scores) or not len(control_scores):
            continue
        for true_score in true_scores:
            wins += float((true_score > control_scores).sum())
            wins += 0.5 * float((true_score == control_scores).sum())
            total += len(control_scores)
    return wins / total if total else 0.5


def _fit_score(
    features: np.ndarray,
    y: np.ndarray,
    train_rows: np.ndarray,
    seed: int,
    y_override: np.ndarray | None = None,
) -> np.ndarray:
    target = y if y_override is None else y_override
    scaler = StandardScaler().fit(features[train_rows])
    model = LogisticRegression(max_iter=2000, random_state=seed)
    model.fit(scaler.transform(features[train_rows]), target[train_rows])
    return model.predict_proba(scaler.transform(features))[:, 1]


def run_event_timing(
    persons_path: str | Path,
    events_path: str | Path,
    *,
    sample: int = 20000,
    seed: int = 7,
    n_sham: int = 5,
) -> dict[str, object]:
    """Screen the transit bank against the chartless twin, within person."""
    corpus = _read_corpus(persons_path, events_path)
    logger.info("corpus: %d persons with a day-precision death", len(corpus))

    candidates = build_candidates(corpus, sample=sample, seed=seed)
    logger.info("candidates: %d persons x (1 true + %d controls)", len(candidates), _N_CONTROLS)

    # Freeze a holdout of persons and drop it: this is screening.
    holdout = assign_holdout([c.person_id for c in candidates], salt=_SALT)
    screening = [c for c in candidates if c.person_id not in holdout]
    logger.info("holdout frozen: %d persons withheld, %d screened", len(holdout), len(screening))

    chartless, transit, y, person_index = build_matrix(screening)
    logger.info("matrix: %d rows, %d chartless + %d transit features",
                len(y), chartless.shape[1], transit.shape[1])

    # Split by PERSON, never by row — a person's true date and their own controls
    # must never straddle the boundary.
    ids = [screening[i].person_id for i in range(len(screening))]
    eval_ids = assign_holdout(ids, salt=_SALT + "-inner")
    train_person = np.array([pid not in eval_ids for pid in ids])
    check_person_leak([p for p, t in zip(ids, train_person) if t],
                      [p for p, t in zip(ids, train_person) if not t])
    train_rows = train_person[person_index]
    eval_rows = ~train_rows

    combined = np.hstack([chartless, transit])
    n_pos = int(y[eval_rows].sum())
    n_neg = int(eval_rows.sum() - n_pos)

    # Sham first.
    tolerance = sham_tolerance_for(n_pos, n_neg, n_permutations=n_sham)
    sham_scores = []
    for k in range(n_sham):
        shuffled = within_person_sham(y, person_index, seed=seed + 101 + k)
        scores = _fit_score(combined, y, train_rows, seed, y_override=shuffled)
        sham_scores.append(_within_person_auc(scores[eval_rows], shuffled[eval_rows],
                                              person_index[eval_rows]))
    sham_auc = float(np.mean(sham_scores))
    sham_ok = abs(sham_auc - 0.5) <= tolerance
    logger.info("sham within-person AUC: %.4f (tolerance %.4f) -> %s",
                sham_auc, tolerance, "PASS" if sham_ok else "FAIL")
    if not sham_ok:
        return {"verdict": "SHAM FAILED — pipeline carries signal on a permuted target",
                "sham_auc": sham_auc, "tolerance": tolerance}

    chartless_scores = _fit_score(chartless, y, train_rows, seed)
    combined_scores = _fit_score(combined, y, train_rows, seed)
    chartless_auc = _within_person_auc(chartless_scores[eval_rows], y[eval_rows],
                                       person_index[eval_rows])
    combined_auc = _within_person_auc(combined_scores[eval_rows], y[eval_rows],
                                      person_index[eval_rows])
    delta = combined_auc - chartless_auc

    logger.info("")
    logger.info("chartless (age + date harmonics) : %.4f", chartless_auc)
    logger.info("chartless + transits             : %.4f", combined_auc)
    logger.info("delta                            : %+.4f", delta)

    return {
        "stage": "screening",
        "exploratory": True,
        "target": "death_date_vs_own_control_dates",
        "design": "within-person: each person's real death date against their own counterfactuals",
        "n_persons_screened": len(screening),
        "n_persons_holdout": len(holdout),
        "n_candidate_rows": int(len(y)),
        "n_controls_per_person": _N_CONTROLS,
        "transit_bodies": list(_TRANSIT_BODIES),
        "natal_bodies": list(_NATAL_BODIES),
        "sham_within_person_auc": sham_auc,
        "sham_tolerance": tolerance,
        "chartless_within_person_auc": chartless_auc,
        "combined_within_person_auc": combined_auc,
        "delta": delta,
        "verdict": (
            f"transits beat the age baseline by {delta:+.4f}"
            if delta > 0
            else f"NULL — transits add nothing over age and calendar ({delta:+.4f})"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Within-person event-timing screening.")
    parser.add_argument("--persons", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sample", type=int, default=20000)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = run_event_timing(args.persons, args.events, sample=args.sample)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    logger.info("")
    logger.info("=== %s ===", report["verdict"])
    logger.info("wrote %s", out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
