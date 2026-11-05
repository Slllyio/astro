"""The cited reading: one chart, every house, read the way a verdict is defended.

For each house it shows, without changing any verdict:

1. the verdict per matter and the plain count of Raman's rules for and against it
   (``for_against``: the form that agreed with him most often on unseen conclusions);
2. every rule that fired, with Raman's reading, its citation and the verbatim lines of the book;
3. whether each rule's condition survives Raman's Bhava and sandhi devices (``house_audit``);
4. how the matter was weighed (which clause decided it) and whether it rests on a doubtful rule;
5. Raman's own conclusions on comparable charts, each with the line where he wrote it;
6. birth-time stability (the house re-judged at -20 .. +20 minutes).

It is framed as "what Raman's books say about this chart, and why". It is not a forecast, and
the honesty notice at the top gives the measured figures that say so.

Usage:
    python -m app.raman_saab.cited read --name "Native" --date 1989-10-12 --time 10:02 \
        --tz 5.5 --lat 27.23 --lon 79.03 --out reading.html     # or --format md
    python -m app.raman_saab.cited read --golden NH.chart_47 --out fdr.html
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.raman_saab import house_audit as ha
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.cited import corpus, spread as sp
from app.raman_saab.cited.html import e, page, src_block, v
from app.raman_saab.for_against import Reason, lean_of
from app.raman_saab.judges import house_template as ht
from app.raman_saab.ordinals import ordinal

SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")
NAKSHATRAS = ("Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Aridra", "Punarvasu",
              "Pushya", "Aslesha", "Makha", "Pubba", "Uttara", "Hasta", "Chitta", "Swati",
              "Visakha", "Anuradha", "Jyeshta", "Moola", "Poorvashadha", "Uttarashadha",
              "Sravana", "Dhanishta", "Satabhisha", "Poorvabhadra", "Uttarabhadra", "Revati")

#: Every figure is a measured one; the documents named hold the receipts.
HONESTY = (
    "This reading sets out what B. V. Raman's books say about this chart and why: every rule "
    "that applies, the line of the book it comes from, how the rules were weighed, and what "
    "Raman himself concluded on similar charts. It is not a forecast. On Raman's own 389 worked "
    "conclusions, which the engine was built against, it agrees with him 263 times (68%). On "
    "his conclusions it was not built on, it agrees far less often: 23 of 36, 55 of 134 and 29 "
    "of 64 in three sealed hold-outs. A plain count of the rules for and against agreed with "
    "him 131 of 198 times. On real lives (22,177 charts with 47,000 dated events, and 47,036 "
    "people from Astro-Databank) no verdict, rule or timing method predicted better than chance. "
    "Raman's verdicts on famous charts also drew on what he knew of the life. Read this as his "
    "reasoning applied faithfully, not as what will happen.")
SOURCES_OF_FIGURES = ("CLAUDE.md (current figure), docs/raman_saab/FIDELITY_FIXES_PREREG.md "
                      "(hold-outs), REASON_CODING_RESULTS_2026-10-31.md (count), "
                      "REAL_OUTCOME_GENERALIZATION.md and PREDICTIVE_RESULTS_2026-11-03.md (real lives)")


@dataclass(frozen=True)
class MatterCount:
    matter: str
    verdict: str
    n_for: int
    n_against: int
    lean: str
    spread: Optional[sp.Spread] = None         # the same counts, with descriptive rules

    @property
    def spread_line(self) -> str:
        return sp.sentence(self.spread) if self.spread is not None else ""


@dataclass(frozen=True)
class HouseReading:
    audit: ha.HouseAudit
    counts: tuple[MatterCount, ...]
    raman: Optional[tuple[str, str, Optional[str]]] = None   # his (verdict, words, where)


@dataclass(frozen=True)
class CitedReading:
    title: str
    birth_line: str
    chart: RamanChart
    houses: tuple[HouseReading, ...]
    golden_id: str = ""
    discussion: Optional[str] = None          # his whole write-up, when the chart is his


def _counts(chart: RamanChart, house: int) -> tuple[MatterCount, ...]:
    pf = ht.judge_house(chart, house)
    return tuple(MatterCount(s.matter.replace("_", " "), s.verdict, s.n_for, s.n_against,
                             lean_of(s.n_for, s.n_against), s)
                 for s in sp.spreads_for_house(pf))


def spread_summary(r: "CitedReading") -> str:
    """The chart-level uncertainty line (``spread.summary``) for this reading."""
    return sp.summary(tuple(c.spread for h in r.houses for c in h.counts if c.spread is not None))


def build(chart: RamanChart, *, title: str, birth_line: str = "", stability: bool = True,
          golden: Optional[dict[str, Any]] = None,
          houses: tuple[int, ...] = tuple(range(1, 13))) -> CitedReading:
    """Assemble the reading. ``golden`` is one of Raman's worked-example records, when the chart
    is his: his own conclusion is then shown beside each house he judged, and his chart is left
    out of its own precedents."""
    gid = golden["id"] if golden else ""
    audits = ha.audit_chart(chart, houses, stability=stability, exclude_record=gid)
    raman: dict[int, tuple[str, str, Optional[str]]] = {}
    if golden:
        for htag, ent in golden.get("expected_verdicts", {}).items():
            if corpus.is_confirmed(ent):
                raman[int(htag[1:])] = (ent["verdict"], ent.get("verdict_prose", ""),
                                        corpus.locate(ent.get("verdict_prose", ""), golden))
    span = corpus.discussion_span(golden) if golden else None
    return CitedReading(title, birth_line, chart,
                        tuple(HouseReading(a, _counts(chart, a.house), raman.get(a.house))
                              for a in audits), gid, span)


def from_birth(name: str, date: str, time: str, tz: float, lat: float, lon: float, *,
               ayanamsa: str = "raman", stability: bool = True) -> CitedReading:
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    y, mo, d = (int(x) for x in date.split("-"))
    hh, mm = (int(x) for x in time.split(":"))
    birth = BirthData(name, y, mo, d, hh, mm, tz, lat, lon)
    chart = cast_chart(birth, ayanamsa=ayanamsa)
    line = (f"Born {date} at {time} (UTC{tz:+g}), latitude {lat:g}, longitude {lon:g}; "
            f"{ayanamsa.title()} ayanamsa")
    return build(chart, title=name, birth_line=line, stability=stability)


def from_golden(record_id: str, *, stability: bool = True) -> CitedReading:
    rec = corpus.example(record_id)
    chart = ha._golden_chart(rec)
    b = rec.get("birth") or {}
    line = (f"Born {b['dt'].replace('T', ' at ')} (UTC{float(b['tz']):+g}), latitude {b['lat']}, "
            f"longitude {b['lon']}; Raman's ayanamsa" if b.get("dt") else
            "Cast from the positions Raman printed (no birth time in the book)")
    return build(chart, title=f"{rec.get('name', record_id)} ({record_id})", birth_line=line,
                 stability=stability, golden=rec)


# -- shared pieces ----------------------------------------------------------------------------

def _where(record_id: str, words: str) -> Optional[str]:
    try:
        rec = corpus.example(record_id)
    except KeyError:
        return None
    return corpus.locate(words, rec) or corpus.discussion_span(rec)


def chart_rows(chart: RamanChart) -> list[tuple[str, str, str, str, str, str]]:
    rows = [("Lagna", f"{chart.asc_lon % 30:.2f}° {SIGNS[chart.asc_sign - 1]}", "1", "1", "", "")]
    for n, p in chart.planets.items():
        rows.append((n + (" (R)" if p.retrograde else ""), f"{p.lon % 30:.2f}° {SIGNS[p.sign - 1]}",
                     str(p.rasi_house), str(p.bhava) + (" (sandhi)" if p.bhava_sandhi else ""),
                     f"{NAKSHATRAS[p.nakshatra - 1]} {p.pada}" if 1 <= p.nakshatra <= 27 else "",
                     SIGNS[p.navamsa_sign - 1]))
    return rows


# -- HTML -------------------------------------------------------------------------------------

def _rule_html(r: ha.RuleCheck) -> str:
    cond = ("condition holds" if not r.doubts else "condition doubtful: " + "; ".join(r.doubts))
    p = corpus.passage(r.citation, context=1)
    return (f"<div class=rule><div class=head>{e(r.id)} <span class=pill>{e(r.polarity)}</span> "
            f"<span class=pill>{e(r.citation)}</span></div>"
            f"<div>{e(r.text)}</div>"
            f"<div><small>For: {e(', '.join(sorted(set(m.replace('_', ' ') for m in r.matters))))}. "
            f"{e(cond)}.</small></div>{src_block(p, r.citation, label='Raman')}</div>")


def _house_html(hr: HouseReading) -> str:
    a = hr.audit
    out = [f"<h2 id=h{a.house}>The {ordinal(a.house)} house <small>(lord {e(a.lord)})</small></h2>"]
    out.append(f"<p>{(e(a.matter_breakdown) + '.') if a.matter_breakdown else ''} "
               f"Worst matter: {v(a.verdict)}."
               + (f" Without the doubtful rules: {v(a.robust_verdict)}." if a.robust_verdict != a.verdict else "")
               + "</p>")
    if hr.raman:
        rv, words, where = hr.raman
        out.append(f"<div class=notice><b>Raman's own conclusion on this chart:</b> {v(rv)}"
                   f"<blockquote>{e(words)}</blockquote>"
                   + (src_block(corpus.passage(where, context=3), where, label="where he wrote it")
                      if where else "<p class=mute><small>This label is a reviewer's summary, not a "
                      "verbatim quote; his full write-up is at the top of the reading.</small></p>")
                   + "</div>")
    out.append("<ul>" + "".join(f"<li>{e(f)}</li>" for f in a.facts) + "</ul>")
    out.append("<h3>For and against, matter by matter</h3><div class=wrap><table><tr><th>Matter</th>"
               "<th>Rules for</th><th>Rules against</th><th>Descriptive</th><th>The count</th>"
               "<th>Engine verdict</th><th>How sure the books are</th></tr>")
    for c in hr.counts:
        nd = c.spread.n_descriptive if c.spread is not None else ""
        out.append(f"<tr><td>{e(c.matter)}</td><td>{c.n_for}</td><td>{c.n_against}</td><td>{nd}</td>"
                   f"<td>{e(c.lean)}</td><td>{v(c.verdict)}</td><td><small>{e(c.spread_line)}</small></td></tr>")
    out.append("</table></div>")
    order = {"benefic": 0, "malefic": 1}
    rules = sorted(a.rules, key=lambda r: (order.get(r.polarity, 2), r.id))
    out.append(f"<h3>The rules ({len(rules)})</h3>")
    out += [_rule_html(r) for r in rules] or ["<p class=mute>No rule fired for this house.</p>"]
    out.append("<h3>How it was weighed</h3><ul>")
    for t in a.matters:
        line = (f"{e(t.matter.replace('_', ' '))}: {v(t.verdict)} ({e(t.frame)} frame; lord "
                f"{e(t.lord)}, karaka {e(t.karaka)}). {e(t.clause)}")
        if t.clause_verdict != t.verdict:
            line += f" The clause gave {v(t.clause_verdict)}; a later gate moved it ({e('; '.join(t.later_gates) or 'see metadata')})."
        if t.robust_verdict != t.verdict:
            line += f" Without the doubtful rules: {v(t.robust_verdict)}."
        out.append(f"<li>{line}</li>")
    out.append("</ul>")
    if a.precedents or a.similar:
        out.append("<h3>What Raman concluded on comparable charts</h3>")
    if a.precedents:
        out.append("<p class=mute><small>His confirmed conclusions on this house, for his charts "
                   "sharing one feature with this one. Associations in his printed verdicts, not a "
                   "causal test.</small></p><div class=wrap><table><tr><th>Shared feature</th>"
                   "<th>Charts</th><th>Favourable</th><th>Mixed</th><th>Afflicted</th></tr>")
        for p in a.precedents:
            out.append(f"<tr><td>{e(p.feature)}</td><td>{p.n}</td><td>{p.favourable}</td>"
                       f"<td>{p.mixed}</td><td>{p.afflicted}</td></tr>")
        out.append("</table></div>")
    for s in a.similar:
        where = _where(s.record, s.words)
        out.append(f"<div class=card><b>{e(s.record)}</b> <small>({s.shared} shared features)"
                   f"</small>: Raman {v(s.verdict)}<blockquote>{e(s.words)}</blockquote>"
                   + src_block(corpus.passage(where, context=2) if where else None,
                               where or s.record, label="in his book") + "</div>")
    if a.stability:
        cells = "".join(f"<td>{m:+d} min<br>{v(x)}</td>" for m, x in a.stability)
        moved = sum(1 for _, x in a.stability if x != a.verdict)
        out.append(f"<h3>Birth-time stability</h3><div class=wrap><table><tr>{cells}</tr></table></div>"
                   f"<p><small>The worst-matter verdict changes at {moved} of {len(a.stability)} "
                   f"shifted times.</small></p>")
    return "\n".join(out)


def _writeup(r: CitedReading) -> str:
    if not r.discussion:
        return ""
    p = corpus.passage(r.discussion)
    return ("<h2>Raman's own write-up of this chart</h2>"
            + src_block(p, r.discussion, label="his text"))


def to_html(r: CitedReading) -> str:
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>"
                   for row in chart_rows(r.chart))
    toc = " · ".join(f"<a href='#h{h.audit.house}'>{ordinal(h.audit.house)}</a>" for h in r.houses)
    body = [f"<h1>What Raman's books say about this chart, and why</h1>",
            f"<p><b>{e(r.title)}</b><br><small>{e(r.birth_line)}</small></p>",
            f"<div class=notice>{e(HONESTY)}<br><small>Sources of these figures: "
            f"{e(SOURCES_OF_FIGURES)}.</small></div>",
            "<h2>The chart</h2><div class=wrap><table><tr><th>Body</th><th>Longitude</th>"
            "<th>Sign from Lagna</th><th>Bhava</th><th>Nakshatra</th><th>Navamsa</th></tr>"
            f"{rows}</table></div>",
            f"<p><small>Houses: {toc}</small></p>",
            f"<div class=notice><b>How sure the books are.</b> {e(spread_summary(r))} Each house "
            f"below says, matter by matter, whether the rules point one way or both.</div>",
            _writeup(r),
            "<p class=mute><small>" + e(ha.ROBUSTNESS_NOTE) + " Each rule opens to the lines of the "
            "book it cites, when the books are on this machine.</small></p>"]
    body += [_house_html(h) for h in r.houses]
    return page(f"Cited reading: {r.title}", "\n".join(body))


# -- Markdown ---------------------------------------------------------------------------------

def to_markdown(r: CitedReading, *, quotes: bool = True) -> str:
    out = [f"# What Raman's books say about this chart, and why", "", f"**{r.title}**  ",
           r.birth_line, "", f"> {HONESTY}", ">", f"> Sources of these figures: {SOURCES_OF_FIGURES}.",
           "", "| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |",
           "|---|---|---|---|---|---|"]
    out += ["| " + " | ".join(row) + " |" for row in chart_rows(r.chart)]
    out += ["", f"**How sure the books are.** {spread_summary(r)}"]
    for hr in r.houses:
        a = hr.audit
        out += ["", f"## The {ordinal(a.house)} house (lord {a.lord})", "",
                f"{a.matter_breakdown}. Worst matter: **{a.verdict}**."
                + (f" Without the doubtful rules: **{a.robust_verdict}**." if a.robust_verdict != a.verdict else "")]
        if hr.raman:
            rv, words, where = hr.raman
            out += ["", f"**Raman's own conclusion:** {rv}. \"{words}\" ({where or 'not located verbatim'})"]
        out += [""] + [f"- {f}" for f in a.facts]
        out += ["", "| Matter | For | Against | Descriptive | Count | Engine | How sure the books are |",
                "|---|---|---|---|---|---|---|"]
        out += [f"| {c.matter} | {c.n_for} | {c.n_against} | "
                f"{c.spread.n_descriptive if c.spread else ''} | {c.lean} | {c.verdict} | {c.spread_line} |"
                for c in hr.counts]
        out += ["", "**Rules**", ""]
        for x in sorted(a.rules, key=lambda x: ({"benefic": 0, "malefic": 1}.get(x.polarity, 2), x.id)):
            cond = "holds" if not x.doubts else "doubtful: " + "; ".join(x.doubts)
            out.append(f"- **{x.id}** ({x.polarity}, {x.citation}; condition {cond}): {x.text}")
            p = corpus.passage(x.citation) if quotes else None
            if p:
                out.append("  > " + " ".join(p["text"].split()))
        out += ["", "**How it was weighed**", ""]
        out += [f"- {t.matter.replace('_', ' ')}: {t.verdict}. {t.clause}" for t in a.matters]
        if a.similar:
            out += ["", "**Raman on the most similar of his charts**", ""]
            for s in a.similar:
                out.append(f"- {s.record}: {s.verdict}. \"{s.words}\" ({_where(s.record, s.words) or s.record})")
        if a.stability:
            out += ["", "Birth-time stability: " + ", ".join(f"{m:+d} min {x}" for m, x in a.stability)]
    return "\n".join(out) + "\n"
