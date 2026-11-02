"""Chart-chosen rectification questions: ask what splits THIS chart's candidate minutes.

A birth-time window (say stated time +/- 30 min) is a set of candidate minutes. Every engine rule
that reads the chart predicts something about the native's life, and at each candidate minute
that prediction may differ. A question is worth asking for a given chart only when its predicted
answer changes inside that chart's window; how much it is worth is the expected information gain
(mutual information, in bits) between the answer and the true minute. Ranking questions by that
number, asking the best one, updating, and ranking again is the noisy "twenty questions" policy
(Jedynak, Frazier & Sznitman 2012: greedy entropy reduction is Bayes-optimal for entropy loss).

Three answer kinds:

* ``yesno``  -- a life fact. Each engine predicts yes / no / no-opinion at each minute.
* ``choice`` -- pick one of k descriptions (e.g. speech style from the 2nd cusp sub-lord).
* ``date``   -- when something happened. KP event windows (``app.kp.events``) at each minute
  define where in life the date should fall.

Likelihoods (named, frozen design choices; see docs/kp/RECTIFICATION_QUESTIONS_RESEARCH.md):

* yes/no with reliability r: P(yes | predicts yes) = r, P(yes | predicts no) = 1 - r,
  P(yes | no opinion) = 0.5. r = ``R_FACT`` (0.8) for checkable facts, ``R_SELF`` (0.65) for
  self-descriptions.
* choice: P(predicted option) = r, the other options share 1 - r; no opinion = uniform.
* date interval I inside the life span L, KP windows W(m) at minute m:
  P(I | m) = r * |I & W(m)| / |L & W(m)| + (1 - r) * |I - W(m)| / |L - W(m)|.
  A wide window (KP's windows often cover half of life) earns little; a narrow one that the
  date falls in earns a lot; a date outside a narrow window costs little.
* when two engines predict the same fact, the likelihood is their AVERAGE (mixture), never the
  product, so one answer is never counted twice.

These r values are what the rules would deliver IF they were right. The validation program
measured KP and Raman dasa timing as null on real lives, so on real people the true r may be
close to chance and the posterior narrower than it deserves. The research tool simulates that
null case so the user can see how much false narrowing it produces.

Usage:
    from app.kp.chart import Birth
    from app.kp.rect_questions import build, rank, update, uniform
    b = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
    q = build(b, range(-30, 31), today=(2026, 11, 2))
    post = uniform(q)
    for r in rank(q, post)[:5]:
        print(r.fact.key, round(r.bits, 3), r.fact.text)
    post = update(q, post, "married", True)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Callable, Final, Optional, Sequence

import numpy as np
import swisseph as swe

from app.kp.chart import Birth, KPChart, cast
from app.kp.events import EVENTS, event_windows
from app.kp.indications import INDICATIONS, indications
from app.kp.judgment import DENIED, MATTERS, MIXED, NOT_SIGNIFIED, PROMISED, _core, generic_matter

logger = logging.getLogger(__name__)

YEAR: Final = 365.2425
R_FACT: Final = 0.8
R_SELF: Final = 0.65
R_DATE: Final = 0.8
YES, NO, EITHER = 1, 0, -1


@dataclass(frozen=True, slots=True)
class Predictor:
    """One engine's rule for one fact: a function from a cast chart to YES / NO / EITHER (or option)."""

    engine: str      # kp | raman
    rule: str        # what is read, e.g. "CSL7 verdict (R7)" or "Raman H5 'children'"
    source: str      # citation ids / ruling
    fn: Callable


@dataclass(frozen=True, slots=True)
class Fact:
    """Something the native is asked."""

    key: str
    kind: str                     # yesno | choice | date
    text: str
    reliability: float
    predictors: tuple[Predictor, ...] = ()
    options: tuple[str, ...] = ()
    event: str = ""               # KP event key for date facts
    min_age: float = 0.0
    ask_if: str = ""
    note: str = ""


# ---------------------------------------------------------------------------------------------
# Predictors

def _kp_matter(matter: str) -> Callable:
    m = MATTERS[matter] if matter in MATTERS else generic_matter(int(matter[5:]))

    def f(ctx: "_Ctx") -> int:
        v = _core(ctx.kp, m)[0]
        return YES if v == PROMISED else NO if v in (DENIED, NOT_SIGNIFIED) else EITHER
    return f


def _kp_fires(*keys: str, polarity: int = YES) -> Callable:
    """An indication that fires predicts ``polarity``; one that does not fire has no opinion."""
    def f(ctx: "_Ctx") -> int:
        return polarity if ctx.fired & set(keys) else EITHER
    return f


def _raman(house: int, sig: str, flip: bool = False) -> Callable:
    def f(ctx: "_Ctx") -> int:
        v = ctx.raman(house).get(sig)
        if v is None or v == "mixed":
            return EITHER
        yes = v == "favourable"
        return (NO if yes else YES) if flip else (YES if yes else NO)
    return f


def _csl_is(cusp: int, mapping: dict[str, int]) -> Callable:
    def f(ctx: "_Ctx") -> int:
        return mapping.get(ctx.kp.cusp(cusp).sub_lord, EITHER)
    return f


def _P(engine: str, rule: str, source: str, fn: Callable) -> Predictor:
    return Predictor(engine, rule, source, fn)


def _kpm(matter: str, ruling: str) -> Predictor:
    m = MATTERS[matter] if matter in MATTERS else generic_matter(int(matter[5:]))
    return _P("kp", f"CSL{m.cusp} verdict for {m.key} (favourable {sorted(m.favourable)}, "
              f"denial {sorted(m.denial)})", f"{ruling}; " + ", ".join(m.citations), _kp_matter(matter))


def _rm(house: int, sig: str, flip: bool = False) -> Predictor:
    return _P("raman", f"Raman H{house} '{sig}' verdict" + (" (inverted: afflicted = yes)" if flip else ""),
              "judge_house (HTJAH-I house template)", _raman(house, sig, flip))


def _ind(*keys: str) -> Predictor:
    return _P("kp", "KP indication fires: " + ", ".join(keys),
              ", ".join(INDICATIONS[k].citation for k in keys), _kp_fires(*keys))


SPEECH: Final = ("talks a lot", "blunt and outspoken", "speaks little", "wise, measured talk",
                 "light, charming talk", "none of these")

#: The fact bank. Order is presentation order only; ranking decides what is asked.
FACTS: Final[tuple[Fact, ...]] = (
    Fact("married", "yesno", "Are you married (or have you ever been)?", R_FACT,
         (_kpm("marriage", "R7/R18"),), ask_if="age 30+, or already married",
         note="'Not yet' under 30 is not a no; skip the question."),
    Fact("children", "yesno", "Do you have children (born to you)?", R_FACT,
         (_kpm("children", "R19"), _rm(5, "children")), ask_if="married and age 30+, or has children"),
    Fact("salaried_job", "yesno", "Have you held a salaried job (employment, not your own business)?", R_FACT,
         (_kpm("service", "R15"),)),
    Fact("good_health", "yesno", "Has your health been generally good (no chronic illness, rarely ill)?", R_SELF,
         (_kpm("health", "R13"), _rm(1, "health")), note="Judgment call: one controlled condition may still be 'yes'."),
    Fact("money_gains", "yesno", "Has your income grown steadily, with regular money gains?", R_SELF,
         (_kpm("wealth", "R14"), _rm(2, "wealth"))),
    Fact("siblings_good", "yesno", "Do you have siblings, and have relations with them been good?", R_SELF,
         (_kpm("house3", "R16 general principle"), _rm(3, "siblings"))),
    Fact("own_property", "yesno", "Do you own a house or land in your own name?", R_FACT,
         (_kpm("house4", "R16 general principle"), _rm(4, "property"))),
    Fact("father_well", "yesno", "Has your father been well and supportive through your life?", R_SELF,
         (_kpm("house9", "R16 general principle"), _rm(9, "father"))),
    Fact("wishes_fulfilled", "yesno", "Have your main wishes mostly been fulfilled (gains, friends, elders' help)?", R_SELF,
         (_kpm("house11", "R16 general principle"), _rm(11, "gains"))),
    Fact("lived_abroad", "yesno", "Have you lived abroad for a year or more?", R_FACT,
         (_kpm("house12", "R16 general principle"), _rm(12, "foreign_residence"))),
    Fact("higher_education", "yesno", "Did you complete a university degree?", R_FACT,
         (_rm(4, "education"), _ind("asc_1_4"))),
    Fact("mother_well", "yesno", "Has your mother been well and close to you?", R_SELF, (_rm(4, "mother"),)),
    Fact("happy_marriage", "yesno", "Is your married life happy?", R_SELF,
         (_rm(7, "marital_happiness"), _ind("asc_1_7", "asc_7_r4")), ask_if="married"),
    Fact("status_authority", "yesno", "Do you hold a position of authority or public respect?", R_SELF,
         (_rm(10, "status_honour"), _ind("asc_1_10", "asc_10_r4"))),
    Fact("borrowed_hardship", "yesno", "Have you had to borrow from friends or family in hard times?", R_FACT,
         (_rm(6, "debts", flip=True), _ind("eighth_debt"))),
    Fact("more_than_one_marriage", "yesno", "Have you married more than once?", R_FACT,
         (_ind("plural_marriage", "second_marriage_2nd"),), ask_if="married"),
    Fact("uniformed_career", "yesno", "Is your work in the army, police, fire service, or with fire/metal?", R_FACT,
         (_ind("tenth_aries"),)),
    Fact("spouse_works", "yesno", "Does your spouse have a career of their own?", R_FACT,
         (_ind("career_partner"),), ask_if="married"),
    Fact("serious_danger", "yesno", "Have you faced a serious accident or danger to life?", R_FACT,
         (_ind("asc_1_8"),)),
    Fact("frequent_illness", "yesno", "Have you had frequent illness or hospital stays?", R_FACT,
         (_ind("asc_1_6", "asc_6_r4", "asc_star_6_8_12"),)),
    Fact("musician", "yesno", "Are you a well-known musician or performer?", R_FACT, (_ind("fifth_musician"),)),
    Fact("speech_style", "choice", "Which best describes how you speak?", R_SELF,
         (_P("kp", "CSL2 is Mercury/Mars/Saturn/Jupiter/Venus",
             "KPR3-IND-SECOND_IS_MERCURY, KPR3-IND-SECOND_IS_MARS",
             _csl_is(2, {"Mercury": 0, "Mars": 1, "Saturn": 2, "Jupiter": 3, "Venus": 4})),),
         options=SPEECH),
    # dated events (KP R19 windows)
    Fact("date_marriage", "date", "Date of your (first) marriage?", R_DATE, event="marriage", min_age=16, ask_if="married"),
    Fact("date_child", "date", "Birth date of each child?", R_DATE, event="childbirth", min_age=16, ask_if="has children"),
    Fact("date_job", "date", "Date you started your first job (joining date)?", R_DATE, event="service_start", min_age=15),
    Fact("date_job_end", "date", "Date you left a job or retired?", R_DATE, event="service_end", min_age=18, ask_if="has left a job or retired"),
    Fact("date_business", "date", "Date you started a business?", R_DATE, event="business", min_age=16, ask_if="has started a business"),
    Fact("date_property", "date", "Date you bought a house or land in your own name?", R_DATE, event="building", min_age=16, ask_if="owns property in own name",
         note="Property bought in another person's name does not count."),
    Fact("date_property_sold", "date", "Date you sold a property?", R_DATE, event="disposal", min_age=16, ask_if="has sold property"),
    Fact("date_move", "date", "Dates you changed residence or were transferred?", R_DATE, event="transfer", min_age=3),
    Fact("date_abroad", "date", "Date you went to live or work abroad?", R_DATE, event="overseas", min_age=3,
         ask_if="has lived or worked abroad (a short tour does not count)"),
    Fact("date_study_abroad", "date", "Date you went away for higher study or research?", R_DATE, event="study_abroad", min_age=15,
         ask_if="went away from home to study"),
    Fact("date_scholarship", "date", "Date you won a scholarship?", R_DATE, event="scholarship", min_age=8, ask_if="won one"),
    Fact("date_deputation", "date", "Date of a deputation or posting with higher pay?", R_DATE, event="deputation", min_age=18, ask_if="has had one"),
)
FACT_BY_KEY: Final = {f.key: f for f in FACTS}


# ---------------------------------------------------------------------------------------------
# Per-minute context

class _Ctx:
    """Lazily cast charts for one candidate minute."""

    def __init__(self, birth: Birth, engines: frozenset[str]):
        self.birth = birth
        self.kp: KPChart = cast(birth)
        self.fired = {f.indication.key for f in indications(self.kp)}
        self._engines = engines
        self._raman_chart = None
        self._raman_cache: dict[int, dict[str, str]] = {}

    def raman(self, house: int) -> dict[str, str]:
        if "raman" not in self._engines:
            return {}
        if house not in self._raman_cache:
            from app.raman_saab.chart.adapter import cast_chart
            from app.raman_saab.chart.model import BirthData
            from app.raman_saab.judges.house_template import judge_house
            if self._raman_chart is None:
                b = self.birth
                self._raman_chart = cast_chart(BirthData(name="x", year=b.year, month=b.month, day=b.day,
                                                         hour=b.hour, minute=b.minute, tz_offset=b.tz,
                                                         latitude=b.lat, longitude=b.lon), ayanamsa="raman")
            r = judge_house(self._raman_chart, house)
            self._raman_cache[house] = {s.signification: s.verdict for s in r.significations}
        return self._raman_cache[house]


# ---------------------------------------------------------------------------------------------
# Built question set for one chart

@dataclass
class Built:
    """Predictions for every fact at every candidate minute of one native's window."""

    birth: Birth
    offsets: list[int]
    life: tuple[float, float]                       # jd span [birth, today)
    preds: dict[str, dict[str, list[int]]]          # fact -> engine-rule -> per-offset prediction
    windows: dict[str, list[list[tuple[float, float]]]] = field(default_factory=dict)  # date facts
    bins: Optional[np.ndarray] = None               # month bin edges (jd)
    month_mass: dict[str, np.ndarray] = field(default_factory=dict)   # fact -> (M x B) P(bin | m)

    def facts(self) -> list[Fact]:
        return [FACT_BY_KEY[k] for k in self.preds] + [FACT_BY_KEY[k] for k in self.windows]


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(y, m, d, 0.0)


def build(birth: Birth, offsets: Sequence[int], *, today: tuple[int, int, int],
          engines: Sequence[str] = ("kp", "raman"), facts: Sequence[Fact] = FACTS) -> Built:
    """Cast every candidate minute and record every fact's prediction there."""
    eng = frozenset(engines)
    offsets = list(offsets)
    ctxs = [_Ctx(birth.shifted(o), eng) for o in offsets]
    j_birth = ctxs[0].kp.jd_ut
    j_today = _jd(*today)
    preds: dict[str, dict[str, list[int]]] = {}
    windows: dict[str, list[list[tuple[float, float]]]] = {}
    for f in facts:
        if f.kind == "date":
            if "kp" not in eng:
                continue
            lo = j_birth + f.min_age * YEAR
            if lo >= j_today:
                continue
            age_now = (j_today - j_birth) / YEAR
            windows[f.key] = [[(max(w.period.start_jd, lo), min(w.period.end_jd, j_today))
                               for w in event_windows(c.kp, f.event, from_age=f.min_age, to_age=age_now)
                               if w.period.end_jd > lo and w.period.start_jd < j_today] for c in ctxs]
            continue
        ps = [p for p in f.predictors if p.engine in eng]
        if ps:
            preds[f.key] = {f"{p.engine}: {p.rule}": [p.fn(c) for c in ctxs] for p in ps}
    out = Built(birth, offsets, (j_birth, j_today), preds, windows)
    out.bins = np.arange(j_birth, j_today + 30.4375, 30.4375)
    for k in windows:
        out.month_mass[k] = _month_mass(out, k)
    return out


# ---------------------------------------------------------------------------------------------
# Likelihoods

def _yes_prob(pred: int, r: float) -> float:
    return r if pred == YES else (1 - r) if pred == NO else 0.5


def answer_probs(b: Built, key: str) -> np.ndarray:
    """(M x A) matrix: P(answer a | minute m), mixture over engines. A = 2 for yes/no (no, yes)."""
    f = FACT_BY_KEY[key]
    if f.kind == "date":
        return b.month_mass[key]
    rows = list(b.preds[key].values())
    if f.kind == "yesno":
        p = np.mean([[_yes_prob(v, f.reliability) for v in row] for row in rows], axis=0)
        return np.stack([1 - p, p], axis=1)
    k = len(f.options)
    mats = []
    for row in rows:
        m = np.full((len(row), k), 1.0 / k)
        for i, v in enumerate(row):
            if v != EITHER:
                m[i, :] = (1 - f.reliability) / (k - 1)
                m[i, v] = f.reliability
        mats.append(m)
    return np.mean(mats, axis=0)


def _cover(ws: list[tuple[float, float]], a: float, z: float) -> float:
    return sum(max(0.0, min(e, z) - max(s, a)) for s, e in ws)


def interval_likelihood(b: Built, key: str, a: float, z: float) -> np.ndarray:
    """P(answer interval [a, z) | m) for a date fact (formula in the module docstring)."""
    f = FACT_BY_KEY[key]
    lo = b.life[0] + f.min_age * YEAR
    L = b.life[1] - lo
    a, z = max(a, lo), min(z, b.life[1])
    out = []
    for ws in b.windows[key]:
        S = _cover(ws, lo, b.life[1])
        inn = _cover(ws, a, z)
        p_in = f.reliability * inn / S if S > 0 else 0.0
        p_out = (1 - f.reliability if S > 0 else 1.0) * ((z - a) - inn) / (L - S) if L - S > 0 else 0.0
        out.append(max(p_in + p_out, 1e-12))
    return np.array(out)


def _month_mass(b: Built, key: str) -> np.ndarray:
    """(M x B) P(month bin | m): the date likelihood over month bins, normalised per minute."""
    f = FACT_BY_KEY[key]
    lo = b.life[0] + f.min_age * YEAR
    e = np.clip(b.bins, lo, b.life[1])
    width = np.diff(e)
    rows = []
    lo_e, hi_e = e[:-1], e[1:]
    for ws in b.windows[key]:
        if ws:
            arr = np.array(ws)
            inn = np.clip(np.minimum(arr[:, 1:2], hi_e) - np.maximum(arr[:, 0:1], lo_e), 0.0, None).sum(axis=0)
        else:
            inn = np.zeros(len(width))
        S, L = inn.sum(), width.sum()
        p = (R_DATE * inn / S if S > 0 else 0.0) + ((1 - R_DATE) if S > 0 else 1.0) * (width - inn) / max(L - S, 1e-9)
        rows.append(np.clip(p, 1e-12, None))
    m = np.array(rows)
    return m / m.sum(axis=1, keepdims=True)


# ---------------------------------------------------------------------------------------------
# Information gain, ranking, updating

def _H(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def info_gain(b: Built, key: str, prior: np.ndarray) -> float:
    """Expected entropy reduction (bits) of the minute posterior from asking ``key``."""
    P = answer_probs(b, key)
    marg = prior @ P
    return _H(marg) - float(sum(pi * _H(row) for pi, row in zip(prior, P)))


def uniform(b: Built) -> np.ndarray:
    return np.full(len(b.offsets), 1.0 / len(b.offsets))


@dataclass(frozen=True, slots=True)
class Ranked:
    fact: Fact
    bits: float
    split: str     # chart-specific explanation: which minutes expect which answer


def runs(xs: Sequence[int]) -> list[tuple[int, int]]:
    out: list[list[int]] = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return [(a, z) for a, z in out]


def _clock(b: Built, o: int) -> str:
    s = b.birth.shifted(o)
    return f"{s.hour:02d}:{s.minute:02d}"


def _runs_text(b: Built, offs: list[int]) -> str:
    return ", ".join(_clock(b, a) if a == z else f"{_clock(b, a)}-{_clock(b, z)}" for a, z in runs(offs)) or "none"


def explain(b: Built, key: str, post: Optional[np.ndarray] = None) -> str:
    """Which candidate minutes expect which answer, in clock time."""
    f = FACT_BY_KEY[key]
    if f.kind == "date":
        post = uniform(b) if post is None else post
        top = [int(i) for i in np.argsort(-post)]
        picks: list[int] = []
        for i in top:
            if all(abs(b.offsets[i] - b.offsets[j]) >= 4 for j in picks):
                picks.append(i)
            if len(picks) == 3:
                break
        parts = []
        span = b.life[1] - b.life[0] - f.min_age * YEAR
        for i in picks:
            ws = _merge(b.windows[key][i])
            cov = _cover(ws, b.life[0] + f.min_age * YEAR, b.life[1]) / span
            others = [_merge(b.windows[key][j]) for j in picks if j != i]
            own = [(s, e) for s, e in _minus(ws, [w for o in others for w in o]) if e - s >= 15]
            shown = "; ".join(f"{_ymd(s)} to {_ymd(e)}" for s, e in own[:4]) + (" ..." if len(own) > 4 else "")
            if cov >= 0.95:
                parts.append(f"at {_clock(b, b.offsets[i])} the windows cover all of life, so any date fits "
                             "and the answer says little about this minute")
                continue
            parts.append(f"at {_clock(b, b.offsets[i])} windows cover {cov:.0%} of the span"
                         + (f"; only this time: {shown}" if own else "; no window unique to this time"))
        return " | ".join(parts)
    P = answer_probs(b, key)
    if f.kind == "yesno":
        yes = [o for o, p in zip(b.offsets, P[:, 1]) if p > 0.55]
        no = [o for o, p in zip(b.offsets, P[:, 1]) if p < 0.45]
        return f"yes expected at {_runs_text(b, yes)}; no expected at {_runs_text(b, no)}"
    parts = []
    for k, name in enumerate(f.options):
        offs = [o for o, row in zip(b.offsets, P) if row[k] > 1.5 / len(f.options)]
        if offs:
            parts.append(f"'{name}' at {_runs_text(b, offs)}")
    return "; ".join(parts) or "no prediction in this window"


def _merge(ws: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[list[float]] = []
    for s, e in sorted(ws):
        if out and s <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def _minus(ws: list[tuple[float, float]], cut: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Parts of ``ws`` not covered by any interval in ``cut``."""
    out = list(ws)
    for cs, ce in _merge(cut):
        nxt = []
        for s, e in out:
            if ce <= s or cs >= e:
                nxt.append((s, e))
                continue
            if s < cs:
                nxt.append((s, cs))
            if ce < e:
                nxt.append((ce, e))
        out = nxt
    return out


def _ymd(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{y:04d}-{m:02d}-{d:02d}"


def rank(b: Built, prior: np.ndarray, *, skip: Sequence[str] = ()) -> list[Ranked]:
    """Every fact ranked by expected information gain under the current posterior."""
    out = []
    for f in b.facts():
        if f.key in skip:
            continue
        out.append(Ranked(f, info_gain(b, f.key, prior), explain(b, f.key, prior)))
    return sorted(out, key=lambda r: -r.bits)


def date_interval(y: int, m: Optional[int] = None, d: Optional[int] = None) -> tuple[float, float]:
    """The JD interval a date answer of given precision covers."""
    if d:
        a = _jd(y, m, d)
        return a, a + 1.0
    if m:
        return _jd(y, m, 1), _jd(y + (m == 12), m % 12 + 1, 1)
    return _jd(y, 1, 1), _jd(y + 1, 1, 1)


def likelihood(b: Built, key: str, answer) -> np.ndarray:
    """P(this answer | m) for every candidate minute.

    yesno: True/False. choice: option index or text. date: (y, m, d) with m/d optional, or a list of them
    (several occurrences of a repeatable event; each counts, which over-counts their shared dasa)."""
    f = FACT_BY_KEY[key]
    if f.kind == "yesno":
        return answer_probs(b, key)[:, 1 if answer else 0]
    if f.kind == "choice":
        idx = f.options.index(answer) if isinstance(answer, str) else int(answer)
        return answer_probs(b, key)[:, idx]
    dates = answer if answer and isinstance(answer[0], (list, tuple)) else [answer]
    out = np.ones(len(b.offsets))
    for d in dates:
        a, z = date_interval(*d)
        out *= interval_likelihood(b, key, a, z)
    return out


def update(b: Built, prior: np.ndarray, key: str, answer) -> np.ndarray:
    p = prior * likelihood(b, key, answer)
    return p / p.sum()


def credible(b: Built, post: np.ndarray, mass: float) -> list[tuple[int, int]]:
    order = np.argsort(-post)
    acc, keep = 0.0, []
    for i in order:
        keep.append(b.offsets[i])
        acc += post[i]
        if acc >= mass:
            break
    return runs(sorted(keep))


def resolution_classes(b: Built, *, dates: bool = True) -> list[tuple[int, int]]:
    """Runs of adjacent minutes no fact in the bank can tell apart: the resolution floor.

    Date windows are compared at month precision (which months they mostly cover), since an answer
    is rarely finer than that; ``dates=False`` compares the yes/no and choice facts only."""
    sig = []
    for i in range(len(b.offsets)):
        row = [tuple(v[i] for v in b.preds[k].values()) for k in b.preds]
        if dates:
            row += [tuple(np.flatnonzero(b.month_mass[k][i] > 1.0 / b.month_mass[k].shape[1])) for k in b.windows]
        sig.append(tuple(map(str, row)))
    out: list[list[int]] = []
    for i, o in enumerate(b.offsets):
        if out and sig[i] == sig[i - 1]:
            out[-1][1] = o
        else:
            out.append([o, o])
    return [(a, z) for a, z in out]


def boundaries(b: Built) -> list[tuple[int, str]]:
    """Where in the window something changes: cusp sub-lords, lagna sign and navamsa (chart map)."""
    out = []
    prev = None
    for o in b.offsets:
        c = cast(b.birth.shifted(o))
        asc = c.cusp(1).longitude
        cur = {"lagna sign": int(asc // 30), "navamsa": int(((asc % 30) * 9) // 30),
               **{f"CSL{h}": c.cusp(h).sub_lord for h in range(1, 13)}}
        if prev is not None:
            ch = [f"{k} {prev[k]}->{v}" for k, v in cur.items() if prev[k] != v]
            if ch:
                out.append((o, ", ".join(ch)))
        prev = cur
    return out


__all__ = ["FACTS", "FACT_BY_KEY", "Fact", "Predictor", "Built", "Ranked", "build", "rank", "info_gain",
           "answer_probs", "likelihood", "update", "uniform", "credible", "explain", "resolution_classes",
           "boundaries", "date_interval", "R_FACT", "R_SELF", "R_DATE"]
