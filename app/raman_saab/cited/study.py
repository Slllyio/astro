"""The study tool: each of Raman's worked charts with the engine's reading and his own, side by
side, so the method can be learned the way he actually applied it.

For every worked example in the golden fixture it shows:

* the chart (cast as the scored harness casts it: from the birth data, or from his printed
  positions when the book gives no time);
* Raman's own write-up of the chart, verbatim from the book;
* for each house he pronounced on: his verdict and words, with the line where he wrote them;
  beside it the engine's verdict for the same matter, the plain count of rules for and against,
  and every rule with its citation and text;
* whether the two agree, are one step apart, or are opposite.

The agreement totals on the index page are the scored in-sample figure (these are the charts
the engine was built against), not an out-of-sample accuracy, and the page says so.

Usage:
    python -m app.raman_saab.cited study --out data/study            # static site
    python -m app.raman_saab.cited study --out data/study --only NH.chart_47
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.raman_saab import house_audit as ha
from app.raman_saab.cited import corpus
from app.raman_saab.cited.html import e, page, src_block, v
from app.raman_saab.cited.reading import chart_rows
from app.raman_saab.judges import house_template as ht
from app.raman_saab.ordinals import ordinal

_POS = {"afflicted": 0, "mixed": 1, "favourable": 2}
AGREE, NEAR, OPPOSITE = "agrees", "one step apart", "opposite"


def distance(got: Optional[str], expected: str) -> int:
    """Ordinal distance as the golden harness scores it (an abstention counts 2)."""
    if got == expected:
        return 0
    if got in _POS and expected in _POS:
        return abs(_POS[got] - _POS[expected])
    return 2


def agreement(got: Optional[str], expected: str) -> str:
    return (AGREE, NEAR, OPPOSITE)[distance(got, expected)]


@dataclass(frozen=True)
class Rule:
    id: str
    polarity: str
    cite: str
    text: str


@dataclass(frozen=True)
class HouseCompare:
    house: int
    matter: str
    raman_verdict: str
    raman_words: str
    raman_where: Optional[str]
    engine_verdict: Optional[str]
    engine_rollup: str
    rules_for: tuple[Rule, ...]
    rules_against: tuple[Rule, ...]
    rules_neutral: tuple[Rule, ...]

    @property
    def agreement(self) -> str:
        return agreement(self.engine_verdict, self.raman_verdict)


@dataclass(frozen=True)
class ChartStudy:
    id: str
    name: str
    book: str
    cast_from: str
    discussion: Optional[str]
    chart: Any
    houses: tuple[HouseCompare, ...]

    def tally(self) -> Counter:
        return Counter(h.agreement for h in self.houses)


def _rules(fired) -> tuple[Rule, ...]:
    seen: dict[str, Rule] = {}
    for fr in fired:
        seen.setdefault(fr.rule.id, Rule(fr.rule.id, fr.rule.polarity, corpus.rule_cite(fr.rule),
                                         (fr.text or "").strip()))
    return tuple(seen.values())


def study(rec: dict[str, Any]) -> ChartStudy:
    chart = ha._golden_chart(rec)
    houses = []
    for htag, ent in sorted(rec.get("expected_verdicts", {}).items(), key=lambda kv: int(kv[0][1:])):
        if not corpus.is_confirmed(ent):
            continue
        h = int(htag[1:])
        pf = ht.judge_house(chart, h)
        sv = next((s for s in pf.significations if s.signification == ent["signification"]), None)
        L = sv.ledger if sv is not None else None
        houses.append(HouseCompare(
            h, ent["signification"].replace("_", " "), ent["verdict"], ent.get("verdict_prose", ""),
            corpus.locate(ent.get("verdict_prose", ""), rec),
            str(sv.verdict) if sv is not None else None, str(pf.rollup),
            _rules(L.fired_benefic) if L else (), _rules(L.fired_malefic) if L else (),
            _rules(L.fired_neutral) if L else ()))
    b = rec.get("birth") or {}
    cast = (f"cast from the birth data {b['dt'].replace('T', ' ')} (UTC{float(b['tz']):+g})"
            if b.get("dt") else "cast from the positions Raman printed")
    return ChartStudy(rec["id"], rec.get("name", rec["id"]), rec.get("book", ""), cast,
                      corpus.discussion_span(rec), chart, tuple(houses))


def all_studies(only: tuple[str, ...] = ()) -> list[ChartStudy]:
    out = []
    for rec in corpus.worked_examples():
        if only and rec["id"] not in only:
            continue
        if any(corpus.is_confirmed(x) for x in rec.get("expected_verdicts", {}).values()):
            out.append(study(rec))
    return out


# -- HTML -------------------------------------------------------------------------------------

def _slug(rid: str) -> str:
    return rid.replace("/", "_") + ".html"


def _rule_list(rules: tuple[Rule, ...], label: str) -> str:
    if not rules:
        return f"<p class=mute><small>{e(label)}: none</small></p>"
    items = []
    for r in rules:
        items.append(f"<li><b>{e(r.id)}</b> <span class=pill>{e(r.cite)}</span> {e(r.text)}"
                     + src_block(corpus.passage(r.cite, context=1), r.cite, label="Raman") + "</li>")
    return f"<p><small><b>{e(label)} ({len(rules)})</b></small></p><ul>{''.join(items)}</ul>"


def chart_html(s: ChartStudy, *, reading_href: str = "", index_href: str = "index.html") -> str:
    t = s.tally()
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>" for row in chart_rows(s.chart))
    disc = corpus.passage(s.discussion) if s.discussion else None
    body = [f"<h1>{e(s.name)}</h1>",
            f"<p><small>{e(s.id)} · {e(s.book)} · {e(s.cast_from)}</small></p>",
            f"<p>Raman pronounced on {len(s.houses)} matters of this chart. The engine agrees "
            f"with him on {t[AGREE]}, is one step apart on {t[NEAR]} and opposite on {t[OPPOSITE]}."
            + (f" <a href='{e(reading_href)}'>Full cited reading of this chart</a>." if reading_href else "")
            + "</p>",
            "<div class=wrap><table><tr><th>Body</th><th>Longitude</th><th>Sign from Lagna</th>"
            f"<th>Bhava</th><th>Nakshatra</th><th>Navamsa</th></tr>{rows}</table></div>",
            "<h2>Raman's own write-up</h2>",
            (f"<details open><summary><small>{e(disc['work'])} lines {disc['lo']}-{disc['hi']}"
             f"</small></summary><pre class=src>{e(disc['text'])}</pre></details>") if disc else
            f"<p class=mute>{e(s.discussion or 'no citation')}: text not on this machine.</p>"]
    for h in s.houses:
        where = corpus.passage(h.raman_where, context=2) if h.raman_where else None
        body += [f"<h2>The {ordinal(h.house)} house: {e(h.matter)} "
                 f"<span class=pill>{e(h.agreement)}</span></h2>", "<div class=grid>",
                 f"<div class=card><h3>Raman</h3><p>{v(h.raman_verdict)}</p>"
                 f"<blockquote>{e(h.raman_words)}</blockquote>"
                 + (src_block(where, h.raman_where or "", label="where he wrote it") if where else
                    "<p class=mute><small>This label is a reviewer's summary, not a quote; read his "
                    "write-up above.</small></p>") + "</div>",
                 f"<div class=card><h3>The engine</h3><p>{v(h.engine_verdict or 'no verdict')} "
                 f"<small>(house as a whole: {e(h.engine_rollup)})</small></p>"
                 f"<p><small>{len(h.rules_for)} rules for, {len(h.rules_against)} against.</small></p>"
                 + _rule_list(h.rules_for, "For") + _rule_list(h.rules_against, "Against")
                 + _rule_list(h.rules_neutral, "Descriptive") + "</div>", "</div>"]
    return page(f"Study: {s.name}", "\n".join(body), nav=f"<a href='{e(index_href)}'>All worked charts</a>")


INDEX_NOTE = (
    "These are the charts the engine was built and tuned against, so the agreement here is its "
    "in-sample fidelity to Raman, not a measure of accuracy on new charts (on conclusions it was "
    "not built on it agrees far less often, and on real lives no verdict predicted better than "
    "chance). The value of this page is the comparison itself: where the books' rules lead to "
    "Raman's conclusion, and where he weighed something the rules do not hold.")


def index_html(studies: list[ChartStudy], *, href=_slug) -> str:
    total = Counter()
    for s in studies:
        total.update(s.tally())
    n = sum(total.values())
    rows = []
    for s in sorted(studies, key=lambda s: s.id):
        t = s.tally()
        rows.append(f"<tr><td><a href='{e(href(s.id))}'>{e(s.name)}</a></td><td>{e(s.id)}</td>"
                    f"<td>{len(s.houses)}</td><td>{t[AGREE]}</td><td>{t[NEAR]}</td><td>{t[OPPOSITE]}</td></tr>")
    body = ["<h1>Raman's worked charts, beside the engine</h1>",
            f"<p>{len(studies)} charts, {n} conclusions: the engine agrees on {total[AGREE]}, is one "
            f"step apart on {total[NEAR]}, opposite on {total[OPPOSITE]}.</p>",
            f"<div class=notice>{e(INDEX_NOTE)}</div>",
            "<div class=wrap><table><tr><th>Chart</th><th>Record</th><th>Matters</th><th>Agree</th>"
            "<th>One step</th><th>Opposite</th></tr>" + "".join(rows) + "</table></div>"]
    return page("Raman's worked charts", "\n".join(body))


def write_site(out: Path, *, only: tuple[str, ...] = (), readings: bool = False) -> dict[str, int]:
    """Write the static study site to ``out``. With ``readings``, also a full cited reading per
    chart (slow: about two seconds a chart)."""
    out.mkdir(parents=True, exist_ok=True)
    studies = all_studies(only)
    for s in studies:
        rhref = ""
        if readings:
            from app.raman_saab.cited import reading as R
            rhref = "reading-" + _slug(s.id)
            (out / rhref).write_text(R.to_html(R.from_golden(s.id)), encoding="utf-8")
        (out / _slug(s.id)).write_text(chart_html(s, reading_href=rhref), encoding="utf-8")
    (out / "index.html").write_text(index_html(studies), encoding="utf-8")
    total = Counter()
    for s in studies:
        total.update(s.tally())
    return {"charts": len(studies), **{k: total[k] for k in (AGREE, NEAR, OPPOSITE)}}
