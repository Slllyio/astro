"""One round of a birth-time rectification session, as plain data (for the web page and the CLI).

Stateless: the caller sends the birth, the window and every answer given so far; this returns the
posterior over candidate minutes, what each answer did, the next questions chosen for this chart,
and the KP hand-off when the band is narrow enough. Casting every candidate minute is the slow
part, so callers may pass a cached :class:`app.kp.rect_questions.Built`.

Usage:
    from app.kp.rect_session import session_result
    r = session_result({"date": [1990, 7, 15], "time": [12, 0], "tz": 5.5, "lat": 12.97,
                        "lon": 77.59, "window": [-30, 30], "today": [2026, 11, 2],
                        "answers": [{"fact": "married", "answer": True}]})
    r["bands"]["p90"], [q["key"] for q in r["ask_everyone"]]
"""

from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np

from app.kp.chart import Birth, cast
from app.kp.rect_questions import (FACT_BY_KEY, Built, answer_probs, boundaries, build, credible, explain,
                                   info_gain, likelihood, rank, resolution_classes, uniform)

logger = logging.getLogger(__name__)

SEED = 20261102
READY_MINUTES = 10
CAVEATS = (
    "The bands assume the rules work as written (reliability 0.8 for facts and dates, 0.65 for "
    "self-descriptions). KP and Raman dasa timing measured null on real lives, and in simulation answers "
    "that carry no truth still narrow the band. A narrow band means the rules agree with the answers, not "
    "that the minute is proven.",
    "Each answer is weighed by how rare its fit is: a date inside a window covering half of life earns "
    "little, a date inside a rare window earns a lot.",
    "When KP and Raman both predict a fact their likelihoods are averaged, so one answer never counts twice. "
    "Several dates for one repeatable event (moves) each count, which over-counts their shared dasa.",
    "A recorded birth time from a hospital or municipal record beats all of this.",
)


def birth_of(S: dict) -> Birth:
    return Birth(*S["date"], *S["time"], tz=S["tz"], lat=S["lat"], lon=S["lon"])


def built_for(S: dict) -> Built:
    w0, w1 = S.get("window", [-30, 30])
    return build(birth_of(S), list(range(w0, w1 + 1)), today=tuple(S["today"]),
                 engines=tuple(S.get("engines", ("kp",))))


def clock(b: Birth, o: float) -> str:
    s = b.shifted(o)
    return f"{s.hour:02d}:{s.minute:02d}"


def band(b: Birth, rs: list[tuple[int, int]]) -> list[dict]:
    return [{"from": a, "to": z, "text": clock(b, a) if a == z else f"{clock(b, a)}-{clock(b, z)}"} for a, z in rs]


def _H(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _ig(post: np.ndarray, mat: np.ndarray) -> float:
    return _H(post @ mat) - float(sum(pi * _H(row) for pi, row in zip(post, mat)))


def batch_questions(q: Built, prior: np.ndarray, n: int, skip: set[str], *, sims: int = 300,
                    seed: int = SEED) -> list[tuple[str, float]]:
    """Pick n questions to ask together: each step adds the question with the highest expected
    information gain AFTER the ones already picked, averaged over simulated answers."""
    rng = np.random.default_rng(seed)
    P = {f.key: answer_probs(q, f.key) for f in q.facts() if f.key not in skip}
    rowH = {k: np.array([_H(r) for r in m]) for k, m in P.items()}
    M = len(q.offsets)
    truths = rng.choice(M, size=sims, p=prior)
    posts = np.tile(prior, (sims, 1))
    picked: list[tuple[str, float]] = []
    for _ in range(min(n, len(P))):
        best, bits = None, -1.0
        for k, mat in P.items():
            if any(k == p for p, _ in picked):
                continue
            marg = posts @ mat
            with np.errstate(divide="ignore", invalid="ignore"):
                hm = -np.nansum(np.where(marg > 0, marg * np.log2(marg), 0.0), axis=1)
            v = float(np.mean(hm - posts @ rowH[k]))
            if v > bits:
                best, bits = k, v
        picked.append((best, bits))
        mat = P[best]
        cum = np.cumsum(mat[truths], axis=1)
        u = rng.random(sims)[:, None] * cum[:, -1:]
        ans = (cum < u).sum(axis=1)
        posts = posts * mat[:, ans].T
        posts /= posts.sum(axis=1, keepdims=True)
    return picked


def stable_csl(birth: Birth, offs: list[int]) -> dict[int, Optional[str]]:
    lords = [{h: cast(birth.shifted(o)).cusp(h).sub_lord for h in range(1, 13)} for o in offs]
    return {h: (lords[0][h] if all(l[h] == lords[0][h] for l in lords) else None) for h in range(1, 13)}


def _fact_dict(f) -> dict:
    return {"key": f.key, "kind": f.kind, "text": f.text, "options": list(f.options), "ask_if": f.ask_if,
            "note": f.note, "reliability": f.reliability,
            "rules": [{"engine": p.engine, "rule": p.rule, "source": p.source} for p in f.predictors]
            + ([{"engine": "kp", "rule": f"R19 event windows for '{f.event}'", "source": "app.kp.events"}] if f.event else [])}


def session_result(S: dict, *, built: Optional[Built] = None, n_questions: int = 8, sims: int = 300,
                   extra_likelihoods: Optional[dict[str, np.ndarray]] = None) -> dict:
    """Everything one round shows, as JSON-ready data."""
    birth = birth_of(S)
    q = built or built_for(S)
    offsets = q.offsets
    answers = S.get("answers", [])
    for a in answers:
        if a["fact"] not in FACT_BY_KEY:
            raise KeyError(f"unknown fact {a['fact']!r}")
    # answer None = "does not apply / don't know": recorded as asked, carries no evidence
    L = {i: likelihood(q, a["fact"], a["answer"]) for i, a in enumerate(answers) if a.get("answer") is not None}
    extra = extra_likelihoods or {}

    def post_of(skip: frozenset[int] = frozenset(), with_extra: bool = True) -> np.ndarray:
        p = uniform(q).copy()
        for i, l in L.items():
            if i not in skip:
                p *= l
        if with_extra:
            for l in extra.values():
                p *= l
        return p / p.sum()

    post = post_of()
    order = np.argsort(-post)
    pk = offsets[int(order[0])]
    effects = []
    for i, a in enumerate(answers):
        if i not in L:
            effects.append({"fact": a["fact"], "answer": a.get("answer"), "applies": False})
            continue
        l = L[i]
        hi, lo = int(np.argmax(l)), int(np.argmin(l))
        p_wo = post_of(frozenset({i}))
        effects.append({"fact": a["fact"], "answer": a["answer"], "applies": True,
                        "best": clock(birth, offsets[hi]), "worst": clock(birth, offsets[lo]),
                        "ratio": float(l[hi] / l[lo]), "peak_without": clock(birth, offsets[int(np.argmax(p_wo))])})

    asked = {a["fact"] for a in answers if a["fact"] != "date_move" or a.get("answer") is None}
    universal = {f.key for f in q.facts() if f.kind != "date" or f.key == "date_move"}
    conditional = {f.key for f in q.facts()} - universal
    picks = batch_questions(q, post, n_questions, asked | conditional, sims=sims)
    cond = [r for r in rank(q, post, skip=asked | universal) if r.bits > 0.005][:n_questions]
    dead = [f.key for f in q.facts() if f.key not in asked and info_gain(q, f.key, post) < 0.001]

    p90 = credible(q, post, 0.9)
    span = [o for a, z in p90 for o in range(a, z + 1)]
    lo, hi = min(span), max(span)
    ready = bool(L or extra) and hi - lo <= READY_MINUTES
    handoff = None
    if L or extra:
        mid = (lo + hi) / 2
        rb = birth.shifted(mid)
        unc = math.ceil((hi - lo) / 2)
        handoff = {"ready": ready, "centre": f"{rb.hour:02d}:{rb.minute:02d}", "uncertainty_minutes": unc,
                   "from": clock(birth, lo), "to": clock(birth, hi),
                   "birth": {"year": rb.year, "month": rb.month, "day": rb.day, "hour": rb.hour, "minute": rb.minute,
                             "tz": birth.tz, "lat": birth.lat, "lon": birth.lon, "uncertainty_minutes": unc},
                   "stable_cusps": {str(h): l for h, l in stable_csl(birth, list(range(lo, hi + 1))).items() if l}}
    cls = resolution_classes(q, dates=False)
    return {
        "stated": clock(birth, 0),
        "window": {"from": clock(birth, offsets[0]), "to": clock(birth, offsets[-1]), "minutes": len(offsets)},
        "engines": list(S.get("engines", ("kp",))),
        "posterior": [{"offset": o, "clock": clock(birth, o), "p": float(p)} for o, p in zip(offsets, post)],
        "peak": {"offset": pk, "clock": clock(birth, pk), "p": float(post[order[0]])},
        "stated_p": float(post[offsets.index(0)]) if 0 in offsets else None,
        "bands": {"p50": band(birth, credible(q, post, 0.5)), "p90": band(birth, p90)},
        "entropy_bits": _H(post), "max_bits": math.log2(len(offsets)),
        "answers_used": len(L), "effects": effects,
        "change_points": [{"offset": o, "clock": clock(birth, o), "change": t} for o, t in boundaries(q)],
        "classes_without_dates": len(cls), "widest_class": max(z - a + 1 for a, z in cls),
        "ask_everyone": [{**_fact_dict(FACT_BY_KEY[k]), "bits": bits, "split": explain(q, k, post)} for k, bits in picks],
        "ask_if_applies": [{**_fact_dict(r.fact), "bits": r.bits, "split": r.split} for r in cond],
        "not_worth_asking": dead,
        "handoff": handoff,
        "caveats": list(CAVEATS),
    }


__all__ = ["session_result", "built_for", "batch_questions", "stable_csl", "birth_of", "CAVEATS", "READY_MINUTES"]
