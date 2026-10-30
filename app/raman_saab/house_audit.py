"""The house audit: every house of any chart examined the way a verdict is defended.

User request 2026-10-28, after the Mainpuri 10th/11th audit: "I want this level of analysis" for
every chart. For each house this module records, without changing any verdict:

1. **The rules.** Every Raman rule the scored judge fired for the house, with its polarity,
   citation and text, grouped by the sub-matter it was weighed for.
2. **The condition check.** Whether the occupancy each rule depends on survives Raman's own
   devices: a planet in the sign but another Bhava frees the house (HTJAH-I:1945-1946), and a
   planet in a Bhava-sandhi gives no Bhava result (HPA-24:98-100). Rules that depend on such a
   planet are flagged as *doubtful*. Only occupancy predicates are inspected (``InRashiHouse``,
   ``CountInHouse`` and the ``planet_in_house`` group); a doubt elsewhere is not detected.
3. **The weighing.** Which clause of ``house_template._decide_clauses`` decided each sub-matter,
   with the strength pillars it read, and whether a later gate moved the verdict.
4. **Robustness.** The house judged again with the doubtful rules removed
   (``house_template.EXCLUDED_RULES``), so a verdict that rests on a doubtful rule is visible.
   This is a sensitivity flag, never a correction (``ROBUSTNESS_NOTE``: on Raman's own charts
   the removal moves more verdicts away from him than toward him).
5. **Raman's precedents.** His own CONFIRMED conclusions for the same house in the golden
   fixture, on charts sharing a feature with this one (lord placement, lord dignity, lords
   together, occupants, malefic aspects), and the three most similar charts with his words.
   These are associations in his printed verdicts, not a causal test.
6. **Birth-time stability.** With birth data, the house re-judged at -20, -10, -5, +5, +10 and
   +20 minutes.

Usage:
    python -m app.raman_saab.house_audit --date 1989-10-12 --time 10:02 --tz 5.5 \
        --lat 27.23 --lon 79.03 [--houses 10,11] [--no-stability] [--format md|json]
    python -m app.raman_saab.house_audit --golden NH.chart_47     # one of Raman's own charts
"""
from __future__ import annotations

import argparse
import contextlib
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Optional

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges import house_template as ht
from app.raman_saab.ordinals import ordinal
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.shadbala import total as shadbala_total

logger = logging.getLogger(__name__)

GOLDENS_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "raman_goldens.jsonl"
STABILITY_MINUTES: tuple[int, ...] = (-20, -10, -5, 5, 10, 20)
_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
_NODES = frozenset({"Rahu", "Ketu"})


# -- records -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleCheck:
    """One fired rule, the sub-matters it was weighed for, and any doubt on its condition."""
    id: str
    polarity: str                    # "benefic" | "malefic" | "neutral"
    citation: str
    text: str
    matters: tuple[str, ...]
    doubts: tuple[str, ...]


@dataclass(frozen=True)
class MatterTrace:
    """How one sub-matter's verdict was reached."""
    matter: str
    verdict: str
    frame: str
    lord: str
    lord_strong: Optional[bool]
    karaka: str
    karaka_strong: Optional[bool]
    navamsa: str
    clause: str
    clause_verdict: str
    later_gates: tuple[str, ...]
    robust_verdict: str              # with the doubtful rules removed


@dataclass(frozen=True)
class Precedent:
    """Raman's CONFIRMED conclusions on this house for charts sharing one feature."""
    feature: str
    n: int
    favourable: int
    mixed: int
    afflicted: int
    against: tuple[tuple[str, str, str], ...]   # (record id, verdict, his words) not favourable


@dataclass(frozen=True)
class Similar:
    """One of the most similar charts in the goldens for this house."""
    record: str
    shared: int
    verdict: str
    words: str


@dataclass(frozen=True)
class HouseAudit:
    house: int
    lord: str
    verdict: str
    robust_verdict: str
    facts: tuple[str, ...]
    rules: tuple[RuleCheck, ...]
    matters: tuple[MatterTrace, ...]
    precedents: tuple[Precedent, ...]
    similar: tuple[Similar, ...]
    stability: tuple[tuple[int, str], ...]       # (minutes offset, house verdict)
    matter_breakdown: str = ""                   # the house told by its matters (2026-10-30)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# -- condition checks --------------------------------------------------------------------------

def _occupancy_doubt(chart: RamanChart, planet: str, house: int) -> Optional[str]:
    p = chart.planets.get(planet)
    if p is None or p.rasi_house != house:
        return None
    if p.bhava_sandhi:
        return (f"{planet} is in the {ordinal(house)} sign but in a Bhava-sandhi, which gives no "
                "Bhava result (HPA-24:98-100)")
    if p.bhava and p.bhava != house:
        return (f"{planet} is in the {ordinal(house)} sign but in the {ordinal(p.bhava)} Bhava, "
                "which frees the house of it (HTJAH-I:1945-1946)")
    return None


def _walk(cond: Any) -> Iterator[Any]:
    yield cond
    for child in getattr(cond, "conds", ()) or ():
        yield from _walk(child)
    inner = getattr(cond, "cond", None)
    if inner is not None:
        yield from _walk(inner)


def _firm(node: Any, chart: RamanChart, ctx: C.EvalContext) -> bool:
    """Whether ``node`` still holds once every doubtful occupant is treated as absent from its
    sign. Only occupancy leaves change; every other predicate keeps its own evaluation."""
    if isinstance(node, C.InRashiHouse):
        if not node.evaluate(ctx):
            return False
        return _occupancy_doubt(chart, C._resolve_planet(node.planet, chart), node.house) is None
    if isinstance(node, C.CountInHouse):
        if not node.evaluate(ctx):
            return False
        group = (C.NATURAL_MALEFICS if node.klass == "malefic"
                 else C.NATURAL_BENEFICS if node.klass == "benefic" else None)
        firm = [n for n, p in chart.planets.items()
                if p.rasi_house == node.house and (group is None or n in group)
                and _occupancy_doubt(chart, n, node.house) is None]
        return len(firm) >= node.n
    if isinstance(node, C.And):
        return all(_firm(c, chart, ctx) for c in node.conds)
    if isinstance(node, C.Or):
        return any(_firm(c, chart, ctx) for c in node.conds)
    return bool(node.evaluate(ctx))


def condition_doubts(rule: Any, chart: RamanChart, ctx: C.EvalContext) -> tuple[str, ...]:
    """Doubts on the occupancy a fired rule depends on (module docstring, point 2). Empty when
    the rule's condition still holds without the doubtful occupants (another arm of an ``Or``,
    or enough firm occupants for a count)."""
    if _firm(rule.condition, chart, ctx):
        return ()
    out: list[str] = []
    for node in _walk(rule.condition):
        if isinstance(node, (C.InRashiHouse, C.CountInHouse)) and node.evaluate(ctx):
            names = ([C._resolve_planet(node.planet, chart)] if isinstance(node, C.InRashiHouse)
                     else [n for n, p in chart.planets.items() if p.rasi_house == node.house])
            out += [d for n in names if (d := _occupancy_doubt(chart, n, node.house))]
    return tuple(dict.fromkeys(out))


# -- the weighing ------------------------------------------------------------------------------

def _pillars(L: ht.FrameLedger) -> str:
    named = {"lord": L.lord_strong, "karaka": L.karaka_strong, "Bhava Bala": L.bhava_bala_strong}
    return ", ".join(f"{k} {'strong' if v else 'weak'}" for k, v in named.items() if v is not None) \
        or "no pillar known"


def decide_clause(L: ht.FrameLedger) -> tuple[str, str]:
    """(clause in words, verdict of ``house_template._decide_clauses``). The branches mirror
    ``_decide_clauses`` one for one; ``tests/raman_saab/test_house_audit.py`` re-derives each
    branch's base verdict on every golden ledger and checks it against the judge."""
    verdict, shifted = ht._decide_clauses(L)
    guarded = "LONGEVITY_GUARD" in L.flags
    maraka = L.maraka_active and not guarded and "MARAKA_NON_DEATH_GUARD" not in L.flags
    nav = f"; the Navamsa then moved it to {verdict}" if shifted else ""
    if not L.karaka_intact:
        return "clause 1, karaka veto: the karaka is broken" + nav, verdict
    if "AFFLICTION_OWN_EVIDENCE" in L.flags and not guarded:
        return ("clause 1.5: an inherently evil matter with malefic evidence of its own and no "
                "benefic contradiction"), verdict
    pil = _pillars(L)
    if L.fired_benefic and L.fired_malefic:
        known = [p for p in (L.lord_strong, L.karaka_strong, L.bhava_bala_strong) if p is not None]
        weak, strong = known.count(False), known.count(True)
        head = f"clause 2, preponderance: benefic and malefic rules both fired, so the pillars decide ({pil})"
        if known and weak >= shadbala_total.CONTRA_PILLAR_AFFLICT:
            why = f"{weak} weak pillars afflict"
        elif known and strong >= shadbala_total.CONTRA_PILLAR_FAVOUR:
            if L.navamsa_status == "weakens":
                why = f"{strong} strong pillars would lift it, but the Navamsa weakens, so mixed"
            elif ht.B1_DOMINANT_FACTOR_GUARD and L.lord_hard_afflicted:
                why = (f"{strong} strong pillars would lift it, but the lord is combust or "
                       "debilitated (HTJAH-I:3788), so mixed")
            else:
                why = f"{strong} strong pillars lift it"
        else:
            why = "neither threshold met, so mixed"
        return f"{head}: {why}{nav}", verdict
    if L.lord_strong is None or L.karaka_strong is None:
        return ("clause 3: no Shadbala, so the polarity of the fired rules decides" + nav), verdict
    both = bool(L.lord_strong) and bool(L.karaka_strong)
    bhava_ok = L.bhava_bala_strong is not False
    weak_pillar = not L.lord_strong or not L.karaka_strong
    if both and bhava_ok and not L.fired_malefic:
        return f"clause 5: strong lord and karaka and no malefic rule ({pil})" + nav, verdict
    if weak_pillar and (L.fired_malefic or L.bhava_bala_strong is False or maraka):
        pressure = ("a malefic rule" if L.fired_malefic else
                    "a weak Bhava Bala" if L.bhava_bala_strong is False else "an active maraka")
        head = f"clause 6: a weak pillar under {pressure} ({pil})"
        if not L.lord_strong and L.fired_benefic and L.bhava_bala_strong is True:
            head += "; the Bhava rescues it to mixed (HTJAH-I:503-505)"
        elif L.karaka_strong and not L.lord_strong and L.fired_malefic and not L.fired_benefic:
            head += "; the strong karaka salvages it to mixed"
        return head + nav, verdict
    if not (L.fired_benefic or L.fired_malefic or L.fired_neutral):
        return "clause 7: no rule fired" + nav, verdict
    return f"clause 8: a borderline, neither clean strength nor a weak pillar under pressure ({pil})" + nav, verdict


@contextlib.contextmanager
def _excluding(ids: frozenset[str]) -> Iterator[None]:
    token = ht.EXCLUDED_RULES.set(ids)
    try:
        yield
    finally:
        ht.EXCLUDED_RULES.reset(token)


# -- precedents --------------------------------------------------------------------------------

def _lord(chart: RamanChart, house: int) -> str:
    return SIGN_LORDS[(chart.asc_sign - 1 + house - 1) % 12 + 1]


def house_features(chart: RamanChart, house: int) -> frozenset[str]:
    """The comparable features of ``house`` on ``chart`` (named by house numbers, so they
    compare across Lagnas)."""
    f: set[str] = set()
    lord = _lord(chart, house)
    lp = chart.planets.get(lord)
    if lp is not None:
        f.add(f"lord in the {ordinal(lp.rasi_house)}")
        d = dignity(lord, chart)
        if d in ("exalt", "own", "moolatrikona", "debil"):
            f.add(f"lord {'exalted' if d == 'exalt' else 'debilitated' if d == 'debil' else 'in own sign'}")
        if lp.combust_fraction >= 0.5:
            f.add("lord combust")
        for h in range(1, 13):
            other = _lord(chart, h)
            op = chart.planets.get(other)
            if h != house and other != lord and op is not None and op.rasi_house == lp.rasi_house:
                f.add(f"lord with the {ordinal(h)} lord")
        for m in _MALEFICS:
            if m != lord and m in drishti.aspecting_planets(lord, chart):
                f.add(f"{m} aspects the lord")
    for n, p in chart.planets.items():
        if p.rasi_house == house:
            f.add(f"{n} in the house (sign)")
    for m in _MALEFICS + ("Jupiter",):
        if m in drishti.aspecting_house(house, chart):
            f.add(f"{m} aspects the house")
    return frozenset(f)


def _birth_from(rec: dict[str, Any]) -> Optional[BirthData]:
    b = rec.get("birth")
    if not b or any(b.get(k) is None for k in ("dt", "tz", "lat", "lon")):
        return None
    date_part, _, time_part = str(b["dt"]).partition("T")
    y, mo, d = (int(x) for x in date_part.split("-"))
    parts = time_part.split(":") if time_part else ["0", "0"]
    return BirthData(str(rec.get("name", "golden")), y, mo, d, int(parts[0]),
                     int(parts[1]) if len(parts) > 1 else 0, float(b["tz"]),
                     float(b["lat"]), float(b["lon"]))


def _golden_chart(rec: dict[str, Any]) -> RamanChart:
    """The chart the golden harness scores (``tests/raman_saab/test_goldens.build_chart``)."""
    birth = _birth_from(rec)
    if birth is not None:
        return cast_chart(birth, ayanamsa="raman")
    stated = {}
    for name, e in rec["stated_positions"].items():
        lon = float(e["lon"]) % 360.0 if e.get("lon") is not None else (int(e["sign"]) - 1) * 30 + 15.0
        stated[name] = {"lon": lon, "bhava": int(e["bhava"])}
    lagna = rec.get("lagna_sign")
    asc = float((int(lagna) - 1) * 30) + 5.0 if lagna else 5.0
    return RamanChart.from_stated_positions(stated, asc_lon=asc, ayanamsa="raman")


@lru_cache(maxsize=1)
def precedent_index() -> tuple[tuple[str, int, str, str, frozenset[str]], ...]:
    """(record id, house, Raman's verdict, his words, features) for every CONFIRMED worked-example
    conclusion in the golden fixture. Built once per process."""
    out: list[tuple[str, int, str, str, frozenset[str]]] = []
    if not GOLDENS_PATH.exists():
        logger.warning("golden fixture not found at %s; no precedents", GOLDENS_PATH)
        return ()
    for line in GOLDENS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rec = json.loads(line)
        if rec.get("case_type") == "self_test" or "B" not in rec.get("track_eligibility", []):
            continue
        rows = [(int(k[1:]), e) for k, e in rec.get("expected_verdicts", {}).items()
                if e.get("verdict_review") == "CONFIRMED" and e.get("verdict") != "DRAFT"]
        if not rows:
            continue
        try:
            chart = _golden_chart(rec)
        except Exception:  # pragma: no cover - a malformed record must not stop the audit
            logger.exception("could not build golden %s", rec.get("id"))
            continue
        for house, e in rows:
            out.append((rec["id"], house, e["verdict"], e.get("verdict_prose", ""),
                        house_features(chart, house)))
    return tuple(out)


def precedents_for(chart: RamanChart, house: int, *, exclude: str = ""
                   ) -> tuple[tuple[Precedent, ...], tuple[Similar, ...]]:
    """Raman's conclusions for ``house`` on charts sharing each feature, and the closest three."""
    mine = house_features(chart, house)
    rows = [r for r in precedent_index() if r[1] == house and r[0] != exclude]
    precs: list[Precedent] = []
    for feat in sorted(mine):
        hit = [r for r in rows if feat in r[4]]
        if not hit:
            continue
        c = Counter(r[2] for r in hit)
        against = tuple((r[0], r[2], r[3][:220]) for r in hit if r[2] != "favourable")
        precs.append(Precedent(feat, len(hit), c["favourable"], c["mixed"], c["afflicted"], against))
    ranked = sorted(rows, key=lambda r: (-len(mine & r[4]), r[0]))[:3]
    sims = tuple(Similar(r[0], len(mine & r[4]), r[2], r[3][:300]) for r in ranked if mine & r[4])
    return tuple(precs), sims


# -- the audit ---------------------------------------------------------------------------------

def _facts(chart: RamanChart, house: int) -> tuple[str, ...]:
    lord = _lord(chart, house)
    out = []
    lp = chart.planets.get(lord)
    if lp is not None:
        sb = lp.shadbala_rupas.total / 60.0 if lp.shadbala_rupas else None
        out.append(f"Lord {lord}: {ordinal(lp.rasi_house)} sign, {ordinal(lp.bhava)} Bhava"
                   + (" (in the sandhi)" if lp.bhava_sandhi else "")
                   + f", {dignity(lord, chart)}"
                   + (f", combust" if lp.combust_fraction >= 0.5 else "")
                   + (f", Shadbala {sb:.2f} rupas" if sb is not None else ""))
    occ = [n for n, p in chart.planets.items() if p.rasi_house == house]
    for n in occ:
        d = _occupancy_doubt(chart, n, house)
        out.append(f"In the {ordinal(house)} sign: {n}" + (f"; {d}" if d else ""))
    asp = drishti.aspecting_house(house, chart)
    out.append("Aspecting the house: " + (", ".join(asp) or "none"))
    return tuple(out)


def _shift_birth(b: BirthData, minutes: int) -> BirthData:
    jd = swe.julday(b.year, b.month, b.day, b.hour + b.minute / 60.0, swe.GREG_CAL)
    y, m, d, h = swe.revjul(jd + minutes / 1440.0, swe.GREG_CAL)
    total = round(h * 60)
    return replace(b, year=int(y), month=int(m), day=int(d), hour=total // 60, minute=total % 60)


def audit_house(chart: RamanChart, house: int, *, stability: bool = True,
                exclude_record: str = "") -> HouseAudit:
    """The full audit of one house (module docstring, points 1-6)."""
    pf = ht.judge_house(chart, house)
    ctx = C.EvalContext(chart)
    rules: dict[str, dict[str, Any]] = {}
    for sv in pf.significations:
        L = sv.ledger
        for pol, group in (("benefic", L.fired_benefic), ("malefic", L.fired_malefic),
                           ("neutral", L.fired_neutral)):
            for fr in group:
                r = rules.setdefault(fr.rule.id, {"rule": fr.rule, "pol": pol, "text": fr.text,
                                                  "matters": []})
                r["matters"].append(sv.signification)
    checks = []
    for rid, r in rules.items():
        src = r["rule"].source
        cit = f"{src.work}:{src.line}" if hasattr(src, "work") else str(src)
        checks.append(RuleCheck(rid, r["pol"], cit, r["text"], tuple(r["matters"]),
                                condition_doubts(r["rule"], chart, ctx)))
    doubtful = frozenset(c.id for c in checks if c.doubts and c.polarity != "neutral")
    robust = pf
    if doubtful:
        with _excluding(doubtful):
            robust = ht.judge_house(chart, house)
    robust_by = {sv.signification: sv.verdict for sv in robust.significations}
    traces = []
    for sv in pf.significations:
        clause, cv = decide_clause(sv.ledger)
        gates = tuple(f"{k}: {v}" for k, v in sv.metadata
                      if k not in ("sav_bindus", "active_periods", "source_of_gains", "varga_D10"))
        L = sv.ledger
        traces.append(MatterTrace(sv.signification, sv.verdict, sv.lead_frame, L.lord,
                                  L.lord_strong, L.karaka, L.karaka_strong,
                                  str(L.navamsa_status), clause, cv,
                                  gates if cv != sv.verdict else (),
                                  robust_by.get(sv.signification, sv.verdict)))
    precs, sims = precedents_for(chart, house, exclude=exclude_record)
    stab: list[tuple[int, str]] = []
    if stability and chart.birth is not None:
        for mins in STABILITY_MINUTES:
            c2 = cast_chart(_shift_birth(chart.birth, mins), ayanamsa=chart.ayanamsa)
            stab.append((mins, ht.judge_house(c2, house).rollup))
    return HouseAudit(house, pf.lord, pf.rollup, robust.rollup, _facts(chart, house),
                      tuple(checks), tuple(traces), precs, sims, tuple(stab),
                      ht.matter_breakdown(pf))


def audit_chart(chart: RamanChart, houses: tuple[int, ...] = tuple(range(1, 13)), *,
                stability: bool = True, exclude_record: str = "") -> tuple[HouseAudit, ...]:
    return tuple(audit_house(chart, h, stability=stability, exclude_record=exclude_record)
                 for h in houses)


def golden_record(record_id: str) -> dict[str, Any]:
    for line in GOLDENS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rec = json.loads(line)
            if rec.get("id") == record_id:
                return rec
    raise KeyError(record_id)


# -- rendering ---------------------------------------------------------------------------------

#: Measured 2026-10-28 on Raman's 389 scored conclusions (``docs/raman_saab/HOUSE_AUDIT_2026-10-28.md``):
#: dropping the doubtful rules changes 14 house verdicts, 10 of them AWAY from Raman. So the
#: judge's verdict stands, and the robust verdict is a sensitivity flag, never a correction.
ROBUSTNESS_NOTE = ("A verdict 'without the doubtful rules' is a sensitivity check, not a "
                   "correction: on Raman's own 389 conclusions, dropping those rules moved 14 "
                   "verdicts, 10 of them away from his.")


def to_markdown(audits: tuple[HouseAudit, ...], title: str = "",
                raman: Optional[dict[int, tuple[str, str]]] = None) -> str:
    """Markdown for ``audits``. ``raman`` maps a house to Raman's own (verdict, words), when the
    chart is one of his worked examples."""
    out = [f"# House audit{': ' + title if title else ''}", "",
           "Every verdict below is the scored judge's. The audit adds the rules behind it, a check "
           "of their conditions against Raman's Bhava and sandhi devices, how they were weighed, "
           "Raman's own conclusions on comparable charts, and birth-time stability. Precedents "
           "are associations in his printed verdicts, not a causal test. " + ROBUSTNESS_NOTE, ""]
    for a in audits:
        head = (f"## The {ordinal(a.house)} house (lord {a.lord}): {a.matter_breakdown} "
                f"— worst matter **{a.verdict}**") if a.matter_breakdown else \
            f"## The {ordinal(a.house)} house (lord {a.lord}): **{a.verdict}**"
        if raman and a.house in raman:
            head += f" — Raman: **{raman[a.house][0]}**"
        if a.robust_verdict != a.verdict:
            head += f" — without the doubtful rules: **{a.robust_verdict}**"
        out += [head, ""]
        if raman and a.house in raman:
            out += [f"> Raman: \"{raman[a.house][1]}\"", ""]
        out += [f"- {f}" for f in a.facts] + [""]
        out += ["| Rule | Polarity | Citation | Text | Matters | Condition |", "|---|---|---|---|---|---|"]
        for r in sorted(a.rules, key=lambda r: ({"benefic": 0, "malefic": 1}.get(r.polarity, 2), r.id)):
            cond = "; ".join(r.doubts) if r.doubts else "holds"
            out.append(f"| {r.id} | {r.polarity} | {r.citation} | {r.text[:160]} | "
                       f"{', '.join(sorted(set(r.matters)))} | {cond} |")
        out += ["", "**How it was weighed**", ""]
        for t in a.matters:
            line = (f"- {t.matter}: **{t.verdict}** ({t.frame} frame; lord {t.lord}, karaka "
                    f"{t.karaka}). {t.clause}")
            if t.clause_verdict != t.verdict:
                line += f" gave {t.clause_verdict}; a later gate moved it ({'; '.join(t.later_gates) or 'see metadata'})"
            if t.robust_verdict != t.verdict:
                line += f". Without the doubtful rules: {t.robust_verdict}"
            out.append(line + ".")
        if a.precedents:
            out += ["", "**Raman's conclusions on this house, for charts sharing a feature**", "",
                    "| Feature | Charts | Favourable | Mixed | Afflicted |", "|---|---|---|---|---|"]
            for p in a.precedents:
                out.append(f"| {p.feature} | {p.n} | {p.favourable} | {p.mixed} | {p.afflicted} |")
        if a.similar:
            out += ["", "**The most similar charts in his books**", ""]
            for s in a.similar:
                out.append(f"- {s.record} ({s.shared} shared features): Raman **{s.verdict}**. "
                           f"\"{s.words}\"")
        if a.stability:
            out += ["", "**Birth-time stability:** " + ", ".join(
                f"{m:+d} min {v}" for m, v in a.stability)]
        out.append("")
    return "\n".join(out)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--golden", default="", help="audit one of Raman's worked charts by record id")
    ap.add_argument("--date")
    ap.add_argument("--time")
    ap.add_argument("--tz", type=float)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--name", default="")
    ap.add_argument("--houses", default="1,2,3,4,5,6,7,8,9,10,11,12")
    ap.add_argument("--ayanamsa", default="raman")
    ap.add_argument("--no-stability", action="store_true")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    a = ap.parse_args(argv)
    houses = tuple(int(h) for h in a.houses.split(","))
    raman: dict[int, tuple[str, str]] = {}
    if a.golden:
        rec = golden_record(a.golden)
        chart = _golden_chart(rec)
        raman = {int(k[1:]): (e["verdict"], e.get("verdict_prose", ""))
                 for k, e in rec.get("expected_verdicts", {}).items()
                 if e.get("verdict_review") == "CONFIRMED" and e.get("verdict") != "DRAFT"}
        if a.houses == ap.get_default("houses") and raman:
            houses = tuple(sorted(raman))
        title = a.name or f"{a.golden} ({rec.get('name', '')})"
    else:
        if None in (a.date, a.time, a.tz, a.lat, a.lon):
            ap.error("give --golden, or all of --date --time --tz --lat --lon")
        y, mo, d = (int(x) for x in a.date.split("-"))
        hh, mm = (int(x) for x in a.time.split(":"))
        chart = cast_chart(BirthData(a.name or "native", y, mo, d, hh, mm, a.tz, a.lat, a.lon),
                           ayanamsa=a.ayanamsa)
        title = a.name
    audits = audit_chart(chart, houses, stability=not a.no_stability, exclude_record=a.golden)
    if a.format == "json":
        print(json.dumps([x.to_dict() for x in audits], indent=1, default=str))
    else:
        print(to_markdown(audits, title, raman))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
