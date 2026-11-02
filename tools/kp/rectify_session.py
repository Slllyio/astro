"""Birth-time rectification session: chart-chosen questions in, a time band and KP hand-off out.

Anyone with a birth date, place and an approximate time can run this. It works in rounds:

1. Round 0 (no answers yet): the tool casts every minute of the window, maps what changes where
   (lagna sign, navamsa, each cusp sub-lord), and prints a FIRST QUESTIONNAIRE chosen for this
   chart: the set of questions that together are expected to split the window most
   (batch selection by simulated conditional information gain, so two questions that test the
   same boundary are not both asked).
2. The person writes answers into the session file and runs it again. The tool updates the
   posterior over minutes, shows what each answer did, stress-tests the result by leaving each
   answer out, and prints the NEXT best questions under the current posterior.
3. When the 90 % band is narrow enough, the hand-off block gives a ``Birth`` for the KP engine
   with an uncertainty window covering the whole band, and the cusp sub-lords that are stable
   across it.

Session file (JSON):

    {"name": "example", "date": [1990, 7, 15], "time": [12, 0], "tz": 5.5, "lat": 12.97, "lon": 77.59,
     "window": [-30, 30], "today": [2026, 11, 2], "engines": ["kp", "raman"], "marks": false,
     "answers": [{"fact": "married", "answer": true},
                 {"fact": "date_marriage", "answer": [2016, 5, 20]},
                 {"fact": "date_move", "answer": [[2008, 7], [2014, 3, 1]]},
                 {"fact": "date_abroad", "answer": null},
                 {"fact": "speech_style", "answer": "speaks little"}]}

An answer of null means "does not apply / don't know": it is recorded as asked and carries no evidence.

``marks: true`` adds the two classical marks with no question behind them (Kunda trine Moon,
vargottama lagna) as evidence, reported separately as well.

Usage:
    python -m tools.kp.rectify_session --session my_session.json --out session.md
    python -m tools.kp.rectify_session --session s.json --out s.md --questions 12
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from typing import Optional

import numpy as np

from app.kp.chart import Birth, cast
from app.kp.rect_questions import (FACT_BY_KEY, Built, answer_probs, boundaries, build, credible, explain,
                                   info_gain, likelihood, rank, resolution_classes, runs, uniform)

logger = logging.getLogger(__name__)

BATCH_SIMS = 300
SEED = 20261102


def clock(b: Birth, o: int) -> str:
    s = b.shifted(o)
    return f"{s.hour:02d}:{s.minute:02d}"


def band_text(b: Birth, rs: list[tuple[int, int]]) -> str:
    return ", ".join(clock(b, a) if a == z else f"{clock(b, a)}-{clock(b, z)}" for a, z in rs)


def _H(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _ig(post: np.ndarray, mat: np.ndarray) -> float:
    return _H(post @ mat) - float(sum(pi * _H(row) for pi, row in zip(post, mat)))


def batch_questions(q: Built, prior: np.ndarray, n: int, skip: set[str], seed: int = SEED) -> list[tuple[str, float]]:
    """Pick n questions to ask together: each step adds the question with the highest expected
    information gain AFTER the ones already picked, averaged over simulated answers."""
    rng = np.random.default_rng(seed)
    P = {f.key: answer_probs(q, f.key) for f in q.facts() if f.key not in skip}
    M = len(q.offsets)
    truths = rng.choice(M, size=BATCH_SIMS, p=prior)
    posts = np.tile(prior, (BATCH_SIMS, 1))
    picked: list[tuple[str, float]] = []
    for _ in range(min(n, len(P))):
        best, bits = None, -1.0
        for k, mat in P.items():
            if k in dict(picked):
                continue
            v = float(np.mean([_ig(posts[s], mat) for s in range(BATCH_SIMS)]))
            if v > bits:
                best, bits = k, v
        picked.append((best, bits))
        mat = P[best]
        for s in range(BATCH_SIMS):
            row = mat[truths[s]]
            a = rng.choice(len(row), p=row / row.sum())
            posts[s] = posts[s] * mat[:, a]
            posts[s] /= posts[s].sum()
    return picked


def marks_likelihood(birth: Birth, offsets: list[int]) -> dict[str, np.ndarray]:
    from tools.kp.rect_intersect import classical_evidence
    out = {}
    for e in classical_evidence(birth, offsets):
        out[e.key] = np.array([math.exp(e.llr(o)) for o in offsets])
    return out


def stable_csl(birth: Birth, offs: list[int]) -> dict[int, Optional[str]]:
    lords = [{h: cast(birth.shifted(o)).cusp(h).sub_lord for h in range(1, 13)} for o in offs]
    return {h: (lords[0][h] if all(l[h] == lords[0][h] for l in lords) else None) for h in range(1, 13)}


def run(S: dict, n_questions: int) -> str:
    birth = Birth(*S["date"], *S["time"], tz=S["tz"], lat=S["lat"], lon=S["lon"])
    w0, w1 = S.get("window", [-30, 30])
    offsets = list(range(w0, w1 + 1))
    today = tuple(S["today"])
    q = build(birth, offsets, today=today, engines=S.get("engines", ("kp", "raman")))
    answers = S.get("answers", [])
    for a in answers:
        if a["fact"] not in FACT_BY_KEY:
            raise KeyError(f"unknown fact {a['fact']!r}")
    # answer null = "does not apply / don't know": recorded as asked, carries no evidence
    L = {i: likelihood(q, a["fact"], a["answer"]) for i, a in enumerate(answers) if a["answer"] is not None}
    marks = marks_likelihood(birth, offsets) if S.get("marks") else {}

    def post_of(skip_ans: set[int] = frozenset(), with_marks: bool = True) -> np.ndarray:
        p = uniform(q).copy()
        for i, l in L.items():
            if i not in skip_ans:
                p *= l
        if with_marks:
            for l in marks.values():
                p *= l
        return p / p.sum()

    post = post_of()
    name = S.get("name", "native")
    out = [f"# Rectification session: {name}", "",
           f"Stated {birth.year:04d}-{birth.month:02d}-{birth.day:02d} {clock(birth, 0)} (tz {birth.tz:+g}), "
           f"lat {birth.lat}, lon {birth.lon}. Window {clock(birth, w0)} to {clock(birth, w1)} "
           f"({len(offsets)} candidate minutes). Engines: {', '.join(S.get('engines', ('kp', 'raman')))}. "
           f"Answers so far: {len(answers)}.", ""]

    # 1. chart map
    bd = boundaries(q)
    out += ["## 1. What changes inside this window", "",
            f"{len(bd)} change points. Each is a place a question can split the window.", "",
            "| from | change |", "|---|---|"]
    out += [f"| {clock(birth, o)} | {t} |" for o, t in bd]
    cls = resolution_classes(q, dates=False)
    out += ["", f"Without date questions, the yes/no and choice facts split the window into {len(cls)} classes "
            f"(widest {max(z - a + 1 for a, z in cls)} min). Date answers can separate minutes inside a class.", ""]

    # 2. posterior
    order = np.argsort(-post)
    pk = q.offsets[int(order[0])]
    out += ["## 2. Where the answers point", ""]
    if not answers and not marks:
        out += ["No answers yet: every minute is equally likely. Answer the questionnaire in section 4.", ""]
    else:
        out += [f"Peak {clock(birth, pk)} ({post[order[0]]:.0%}). 50 % band: {band_text(birth, credible(q, post, 0.5))}. "
                f"90 % band: {band_text(birth, credible(q, post, 0.9))}. "
                f"Stated time {clock(birth, 0)}: {post[offsets.index(0)]:.1%} (uniform {1 / len(offsets):.1%}).", ""]
        if marks:
            p2 = post_of(with_marks=False)
            o2 = np.argsort(-p2)
            out += [f"Answers only, without the classical marks: peak {clock(birth, q.offsets[int(o2[0])])} "
                    f"({p2[o2[0]]:.0%}); 90 % band {band_text(birth, credible(q, p2, 0.9))}.", ""]
        out += ["Posterior by minute (%, minutes at 1 % or more): " +
                " ".join(f"{clock(birth, o)}:{100 * p:.0f}" for o, p in zip(offsets, post) if p >= 0.01), ""]

        # 3. answers
        out += ["## 3. What each answer did", "",
                "| answer | fact | strongest support | weakest | ratio | peak without it |", "|---|---|---|---|---|---|"]
        for i, a in enumerate(answers):
            if i not in L:
                out.append(f"| (does not apply) | {a['fact']} | - | - | - | - |")
                continue
            l = L[i]
            hi, lo = int(np.argmax(l)), int(np.argmin(l))
            p_wo = post_of({i})
            out.append(f"| {json.dumps(a['answer'])} | {a['fact']} | {clock(birth, offsets[hi])} | {clock(birth, offsets[lo])} | "
                       f"{l[hi] / l[lo]:.1f} | {clock(birth, q.offsets[int(np.argmax(p_wo))])} |")
        for k, l in marks.items():
            out.append(f"| (mark) | {k} | {clock(birth, offsets[int(np.argmax(l))])} | {clock(birth, offsets[int(np.argmin(l))])} | "
                       f"{l.max() / l.min():.1f} | - |")
        out += ["", "Ratio = how much more this answer favours its best minute over its worst. "
                "'Peak without it' shows whether the result hangs on that one answer.", ""]

    # 4. questions
    # a repeatable event (moves) can be asked again for more dates; everything else is asked once
    asked = {a["fact"] for a in answers if a["fact"] != "date_move" or a["answer"] is None}
    # Everyone can answer the yes/no and choice facts and list their moves; the other dated events
    # apply only to some lives, so they are ranked separately and asked only if they apply.
    universal = {f.key for f in q.facts() if f.kind != "date" or f.key == "date_move"}
    conditional = {f.key for f in q.facts()} - universal
    picks = batch_questions(q, post, n_questions, asked | conditional)
    cond = [r for r in rank(q, post, skip=asked | universal) if r.bits > 0.005][:n_questions]
    total = sum(b for _, b in picks)
    H0 = _H(post)
    out += ["## 4. Questions to ask next (chosen for this chart)", "",
            f"Current uncertainty {H0:.2f} bits (a single known minute is 0; {math.log2(len(offsets)):.2f} = no idea).", "",
            "### 4a. Ask everyone", "",
            f"Chosen together, so two questions testing the same change point are not both asked. Expected to remove "
            f"about {min(total, H0):.2f} bits between them if the rules are right.", "",
            "| # | question | expected bits | which minutes expect which answer | ask only if | note |", "|---|---|---|---|---|---|"]
    for n, (k, bits) in enumerate(picks, 1):
        f = FACT_BY_KEY[k]
        txt = f.text + (f" Options: {', '.join(f.options)}." if f.options else "")
        out.append(f"| {n} | {txt} (`{k}`) | {bits:.2f} | {explain(q, k, post)} | {f.ask_if or '-'} | {f.note or '-'} |")
    out += ["", "### 4b. Ask only if it happened in your life", "",
            "Ranked one by one (bits if answered alone). An event that did not happen is answered 'does not apply' and "
            "carries no evidence.", "",
            "| # | question | expected bits | which minutes expect which answer | ask only if |", "|---|---|---|---|---|"]
    for n, r in enumerate(cond, 1):
        out.append(f"| {n} | {r.fact.text} (`{r.fact.key}`) | {r.bits:.2f} | {r.split} | {r.fact.ask_if or '-'} |")
    picks = picks + [(r.fact.key, r.bits) for r in cond]
    rest = [r for r in rank(q, post, skip=asked | {k for k, _ in picks}) if r.bits > 0.005]
    if rest:
        out += ["", "Other questions that still carry information here: " +
                ", ".join(f"`{r.fact.key}` ({r.bits:.2f})" for r in rest[:10]) + "."]
    dead = [f.key for f in q.facts() if info_gain(q, f.key, post) < 0.001]
    if dead:
        out += ["", "Questions that cannot split this window at all (same predicted answer at every minute): " +
                ", ".join(f"`{k}`" for k in dead) + ". Do not ask them for this chart."]
    out.append("")

    # 5. hand-off
    if answers or marks:
        band = [o for a, z in credible(q, post, 0.9) for o in range(a, z + 1)]
        lo, hi = min(band), max(band)
        mid = (lo + hi) / 2
        st = stable_csl(birth, list(range(lo, hi + 1)))
        rb = birth.shifted(mid)
        ready = hi - lo <= 10
        out += ["## 5. Hand-off to the KP engine", "",
                ("The 90 % band is 10 minutes or less: the hand-off below is usable." if ready else
                 f"Not ready: the 90 % band spans {hi - lo + 1} minutes. Keep the stated time and its stability band, "
                 "or answer more questions. The block below is shown for completeness only."), "",
                f"Centre {rb.hour:02d}:{rb.minute:02d}, uncertainty +/- {math.ceil((hi - lo) / 2)} min "
                f"(covers the whole 90 % band {clock(birth, lo)} to {clock(birth, hi)}).",
                f"`Birth({rb.year}, {rb.month}, {rb.day}, {rb.hour}, {rb.minute}, tz={birth.tz}, lat={birth.lat}, lon={birth.lon}, "
                f"uncertainty_minutes={math.ceil((hi - lo) / 2)})`", "",
                "Cusp sub-lords stable across that span: " +
                (", ".join(f"{h}: {l}" for h, l in st.items() if l) or "none") +
                ". Read only these cusps with confidence; the rest change inside the band.", ""]

    out += ["## 6. How to read this", "",
            "- The bits and bands assume the rules work as written (reliability 0.8 for facts and dates, 0.65 for "
            "self-descriptions). The validation program found KP and Raman dasa timing null on real lives, and the "
            "research run (docs/kp/RECTIFICATION_QUESTIONS_RESEARCH.md) shows that answers carrying no truth still "
            "narrow the band. A narrow band is the rules agreeing with the answers, not proof of the minute.",
            "- Each answer is weighed by how rare its fit is. A date inside a window that covers half of life earns "
            "little; a date inside a rare window earns a lot.",
            "- When KP and Raman both predict a fact, their likelihoods are averaged, so one answer is never counted twice. "
            "Several dates for one repeatable event (moves) each count, which over-counts their shared dasa.",
            "- A recorded birth time from a hospital or municipal record beats all of this."]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--questions", type=int, default=10)
    a = ap.parse_args(argv)
    with open(a.session) as fh:
        S = json.load(fh)
    md = run(S, a.questions)
    with open(a.out, "w") as fh:
        fh.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
