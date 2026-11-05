"""Evidence packets for the distance-2 rows in golden_accuracy_baseline.json `real_errors`.

Read-only: imports the engine and the study tool, changes nothing. The decide-clause trace uses
sys.settrace around judge_signification, so no engine code is touched.

Two outputs, one renderer:
  * this folder (committed): golden record, engine view, exact book line pointers;
  * data/opposite_verdicts_2026-11-05/packets_with_text (gitignored): the same packets plus the
    verbatim book lines. Book text stays out of git, as data/knowledge_library does.

Usage:
    PYTHONIOENCODING=utf-8 py -3.12 docs/raman_saab/opposite_verdicts_2026-11-05/packets/_build_packets.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from app.raman_saab import house_audit as ha  # noqa: E402
from app.raman_saab.cited import corpus, study as st  # noqa: E402
from app.raman_saab.cited.reading import chart_rows  # noqa: E402
from app.raman_saab.doctrine.conditions import EvalContext  # noqa: E402
from app.raman_saab.judges import house_template as ht  # noqa: E402

OUT = Path(__file__).resolve().parent
LOCAL = ROOT / "data" / "opposite_verdicts_2026-11-05" / "packets_with_text"
MAX_LINES = 250
SRC = Path(ht.__file__).read_text(encoding="utf-8").splitlines()
STAGES = {"_decide_clauses", "_navamsa_modulate", "_decide", "_decisive_affliction",
          "_catastrophic_severity_gate", "_yoga_modulate", "_dhana_floor", "_blemishless_venus_floor",
          "_saptamsa_gate", "_fertility_gate", "_longevity_span", "_marital_bond_gate",
          "_malefic_occupancy_gate", "_marginal_karaka_gate", "_yogakaraka_lagna_gate",
          "_powerful_dhana_kendra_floor", "_event_timing"}
HEADER_HTJAH = re.compile(r"^\s*Chart\s+No\.?\s*(\d+)[\s.\-—–:]*(?:Born|Bom|born|horn)")
HEADER_NH = re.compile(r"^\s*No\.\s*(\d+)[\s.\-—–]*[A-Z]{2}")


def _mention(n: int) -> re.Pattern[str]:
    return re.compile(rf"Charts?\s+Nos?\.?\s*{n}\b")


def _para_start(lines: tuple[str, ...], ln: int, floor: int) -> int:
    while ln > floor and lines[ln - 2].strip():
        ln -= 1
    return ln


def _chart_no(rec: dict) -> int | None:
    m = re.search(r"(?:^|Chart )(\d+)\b", rec.get("name", ""))
    if m:
        return int(m.group(1))
    m = re.search(r"chart_(\d+)$", rec["id"])
    return int(m.group(1)) if m else None


def _cited(rec: dict, work: str) -> list[tuple[int, int]]:
    return [(p[1], p[2]) for p in map(corpus.parse_cite, rec.get("citations") or ()) if p and p[0] == work]


def writeup_span(rec: dict) -> dict:
    """The chart's write-up: heading (or the paragraph first naming the chart) to the next chart."""
    work = corpus._book_prefix(rec)
    lines = corpus.lines_of(corpus.file_for(work).path)
    cited = _cited(rec, work)
    anchor = cited[0][0]
    n = _chart_no(rec)
    notes: list[str] = []
    regex = HEADER_NH if work == "NH" else HEADER_HTJAH
    heads = [(i, int(m.group(1))) for i, l in enumerate(lines, 1) if (m := regex.match(l))]
    same = [i for i, k in heads if k == n]
    if same:
        h = min(same, key=lambda i: abs(i - anchor))
    else:
        h = max((i for i, _ in heads if i <= anchor), default=anchor)
        notes.append(f"no heading numbered {n}; used the last heading before the cited line")
    prev = max((i for i, _ in heads if i < h), default=0)
    nxt = min(((i, k) for i, k in heads if i > h and k != n), default=None)
    if work == "NH":
        start = h
        end = (nxt[0] - 1) if nxt else min(len(lines), h + 400)
    else:
        first = next((i for i in range(prev + 1, h + 1) if _mention(n).search(lines[i - 1])), h)
        near = [a for a, _ in cited if prev < a < h]
        start = _para_start(lines, min([first, *near]), prev + 1)
        last_cited = max([h, *(b for a, b in cited if a >= h and (not nxt or a < nxt[0]))])
        end = (nxt[0] - 1) if nxt else min(len(lines), h + 150)
        if nxt:
            lead = next((i for i in range(last_cited + 1, nxt[0]) if _mention(nxt[1]).search(lines[i - 1])), None)
            if lead:
                end = _para_start(lines, lead, last_cited + 1) - 1
    if not same:
        start = min(start, anchor)
    outside = [(a, b) for a, b in cited if a < start or b > end]
    return {"work": work, "n": n, "heading": h, "start": start, "end": end, "outside": outside,
            "notes": notes, "path": corpus.file_for(work).path}


def _excerpt(span: dict, keep: list[tuple[int, int]]) -> list[tuple[int, int, str]]:
    """Line ranges to show: all of it, or the 250 lines around the cited lines plus the conclusion."""
    s, e = span["start"], span["end"]
    if e - s + 1 <= MAX_LINES:
        return [(s, e, "full write-up")]
    inside = [x for x in keep if s <= x[0] <= e]
    mid = sum(a + b for a, b in inside) // (2 * len(inside)) if inside else (s + e) // 2
    lo = max(s, min(mid - MAX_LINES // 2, e - MAX_LINES + 1))
    hi = lo + MAX_LINES - 1
    lines = corpus.lines_of(span["path"])
    rem = [i for i in range(s, e + 1) if re.match(r"^\s*Remarks?\b", lines[i - 1])]
    c = rem[-1] if rem else e - 29
    if c <= hi:
        return [(lo, hi, "lines around the citations")] + ([(hi + 1, e, "to the end of the write-up")] if e > hi else [])
    return [(lo, hi, "lines around the citations"),
            (c, e, "Remarks paragraph" if rem else "closing lines (no 'Remarks' heading)")]


def _numbered(path: Path, a: int, b: int) -> str:
    lines = corpus.lines_of(path)
    return "\n".join(f"{i:>6}  {lines[i - 1]}" for i in range(a, min(b, len(lines)) + 1))


def trace_decision(chart, house: int, key: str):
    """Judge one signification with a tracer: every pipeline stage's result and return line."""
    sig = next(s for s in ht.significations_of(house) if s.key == key)
    events: list[tuple[str, int, str, int | None]] = []
    file = ht.__file__
    last_base: dict[int, int] = {}

    def local(frame, event, arg):
        name = frame.f_code.co_name
        if event == "line" and name == "_decide_clauses" and "base = " in SRC[frame.f_lineno - 1]:
            last_base[id(frame)] = frame.f_lineno
        if event == "return":
            val = arg[0] if isinstance(arg, tuple) and arg else arg
            events.append((name, frame.f_lineno, str(val), last_base.get(id(frame))))
        return local

    def tracer(frame, event, arg):
        if event == "call" and frame.f_code.co_filename == file and frame.f_code.co_name in STAGES:
            return local
        return None

    sys.settrace(tracer)
    try:
        sv = ht.judge_signification(chart, house, sig, EvalContext(chart))
    finally:
        sys.settrace(None)
    return sv, events


def _clause_label(ln: int) -> str:
    for i in range(ln - 1, max(0, ln - 80), -1):
        m = re.match(r"\s*# (\d+(?:\.\d+)?\.? .*)", SRC[i])
        if m:
            return m.group(1).strip()
    return ""


def _ledger_md(L, title: str) -> list[str]:
    rows = [("frame", L.frame), ("lord", L.lord), ("lord_strong", L.lord_strong), ("karaka", L.karaka),
            ("karaka_strong", L.karaka_strong), ("bhava_bala", L.bhava_bala),
            ("bhava_bala_strong", L.bhava_bala_strong), ("navamsa_status", L.navamsa_status),
            ("karaka_intact", L.karaka_intact), ("maraka_active", L.maraka_active),
            ("parivartana_resilient", L.parivartana_resilient),
            ("lord_karaka_identical", L.lord_karaka_identical),
            ("lord_hard_afflicted", L.lord_hard_afflicted), ("flags", ", ".join(L.flags) or "none"),
            ("fired counts", f"benefic {len(L.fired_benefic)}, malefic {len(L.fired_malefic)}, "
                             f"neutral {len(L.fired_neutral)}, blemish {len(L.fired_blemish)}")]
    return [f"**{title}**", "", "| field | value |", "|---|---|",
            *(f"| {k} | {v} |" for k, v in rows), ""]


def _rule_md(fr, label: str, with_text: bool) -> list[str]:
    r = fr.rule
    cite = corpus.rule_cite(r)
    cond = re.sub(r"\s+", " ", repr(r.condition))
    out = [f"- **{r.id}** ({label}; polarity {r.polarity}; {r.kind}/{r.group}; signification "
           f"{r.signification}; frame {r.frame}; branch {fr.branch}) cite `{cite}`",
           f"  - reading: {(fr.text or '').strip()}",
           f"  - condition: `{cond[:500]}{'...' if len(cond) > 500 else ''}`"]
    p = corpus.passage(cite, context=3)
    if p is None:
        out.append("  - cited lines: not resolvable on this machine")
    elif with_text:
        f = corpus.file_for(p["work"])
        out += [f"  - cited lines {p['lo']}-{p['hi']} of {f.path.parent.name}/{f.path.name} ({p['scope']}):",
                "", "```", _numbered(f.path, p["lo"], p["hi"]), "```", ""]
    else:
        out.append(f"  - cited lines: `{p['work']}:{p['lo']}-{p['hi']}` (±3, {p['scope']}); text in the local packet")
    return out


def packet(key: str, rec: dict, with_text: bool) -> tuple[str, dict]:
    head, tail = key.split(" ")
    htag, sig = tail.split("/")
    house = int(htag[1:])
    ent = rec["expected_verdicts"][htag]
    if ent["signification"] != sig:
        raise ValueError(f"{key}: golden holds {ent['signification']}")
    chart = ha._golden_chart(rec)
    sv, events = trace_decision(chart, house, sig)
    s = st.study(rec)
    hc = next(h for h in s.houses if h.house == house and h.sig == sig)
    if str(sv.verdict) != str(hc.engine_verdict):
        raise ValueError(f"{key}: trace {sv.verdict} != study {hc.engine_verdict}")
    span = writeup_span(rec)
    keep = _cited(rec, span["work"])
    where = corpus.parse_cite(hc.raman_where) if hc.raman_where else None
    if where:
        keep.append((where[1], where[2]))
    shown = _excerpt(span, keep)
    b = rec.get("birth") or {}
    o = [f"# {key}", "",
         f"Engine **{hc.engine_verdict}** vs Raman **{hc.raman_verdict}**: {hc.agreement}. "
         f"House rollup: {hc.engine_rollup}.", "", "## a. Golden record", "",
         f"- id: `{rec['id']}`; name: {rec.get('name')}; book: {rec.get('book')}; "
         f"case_type: {rec.get('case_type')}; confidence: {rec.get('confidence')}",
         f"- birth: {json.dumps(b) if b else 'none in the golden (cast from stated positions)'}",
         f"- cast: {s.cast_from}", f"- lagna_sign: {rec.get('lagna_sign')}",
         "- stated_positions: " + ("; ".join(
             f"{k} sign {v.get('sign')} bhava {v.get('bhava')}" + (f" lon {v['lon']}" if v.get("lon") is not None else "")
             for k, v in (rec.get("stated_positions") or {}).items()) or "none"),
         f"- expected verdict: **{ent['verdict']}** ({ent['signification']}; review {ent.get('verdict_review')})",
         f"- verdict_prose: {ent.get('verdict_prose', '')}",
         f"- citations: {', '.join(rec.get('citations') or ())}",
         f"- located in the book by the study tool: {hc.raman_where or 'not located (prose is a summary or the words are not near the cited lines)'}",
         "", "Chart as the engine casts it:", "",
         "| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |", "|---|---|---|---|---|---|",
         *("| " + " | ".join(r) + " |" for r in chart_rows(chart)), "",
         "## b. Raman's write-up", "",
         f"File: `{span['path'].parent.name}/{span['path'].name}`. Chart number {span['n']}; heading at line "
         f"{span['heading']}; write-up span lines {span['start']}-{span['end']} "
         f"({span['end'] - span['start'] + 1} lines)."]
    o += [f"\nNote: {x}" for x in span["notes"]]
    if not with_text:
        o += ["", "Book text is not committed (data/knowledge_library is gitignored). The verbatim, "
              "line-numbered text is in the local packet of the same name under "
              "`data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.", "",
              "Ranges in the local packet: " + "; ".join(f"{a}-{z} ({lbl})" for a, z, lbl in shown)]
    else:
        for a, z, lbl in shown:
            o += ["", f"Lines {a}-{z} ({lbl}):", "", "```", _numbered(span["path"], a, z), "```"]
    if span["outside"]:
        o += ["", "Cited lines outside the span: " + ", ".join(f"{a}-{z}" for a, z in span["outside"])]
        if with_text:
            for a, z in span["outside"]:
                lo, hi = max(1, a - 3), z + 3
                o += ["", "```", _numbered(span["path"], lo, min(hi, lo + MAX_LINES - 1)), "```"]
    o += ["", "## c. The engine's view", "",
          f"Verdict **{sv.verdict}**; degree {sv.degree}; lead frame {sv.lead_frame}; karaka {sv.karaka}; "
          f"borderline_shifted {sv.borderline_shifted}.", "", f"Count: {st.sp.sentence(hc.spread)}", "",
          "### How the verdict was decided", "",
          "Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):", "",
          "| stage | result | return line | clause / branch |", "|---|---|---|---|"]
    final_clause = ""
    for name, ln, val, base in events:
        lab = ""
        if name == "_decide_clauses":
            at = base or ln
            lab = f"{_clause_label(at)} (`{SRC[at - 1].strip()}`)".replace("|", "\\|")
            final_clause = final_clause or lab
        o.append(f"| {name} | {val} | {ln} | {lab} |")
    o += ["", f"Metadata: {'; '.join(f'{k}={v}' for k, v in sv.metadata) or 'none'}", "",
          "### Pillars", "", *_ledger_md(sv.ledger, "Lead frame")]
    for alt in sv.alt_ledgers:
        o += _ledger_md(alt, f"Alternate frame ({alt.frame}, does not set the verdict)")
    o += ["### Fired rules (lead frame)", ""]
    groups = [("benefic", sv.ledger.fired_benefic), ("malefic", sv.ledger.fired_malefic),
              ("neutral", sv.ledger.fired_neutral), ("blemish, set aside", sv.ledger.fired_blemish)]
    any_rule = False
    for label, fired in groups:
        seen: set[str] = set()
        for fr in fired:
            if fr.rule.id in seen:
                continue
            seen.add(fr.rule.id)
            any_rule = True
            o += _rule_md(fr, label, with_text)
    if not any_rule:
        o.append("No rule fired for this matter on the lead frame.")
    return "\n".join(o) + "\n", {"key": key, "engine": str(sv.verdict), "raman": hc.raman_verdict,
                                 "agreement": hc.agreement, "where": hc.raman_where,
                                 "span": f"{span['work']}:{span['start']}-{span['end']}",
                                 "lines": span["end"] - span["start"] + 1,
                                 "outside": span["outside"], "notes": span["notes"], "chart": span["n"],
                                 "heading": span["heading"], "clause": final_clause, "shown": shown}


GENERAL = (
    ("1. Beeja/Kshetra sphuta, the fertility test, charts 88-90", "HTJAH-I", ((5480, 5640),)),
    ("2. 7th lord / Kalatrakaraka afflictions", "HTJAH-II", ((255, 300), (340, 460), (1760, 1790))),
    ("3. Ketu in the 12th from Karakamsa", "HTJAH-II", ((16515, 16535),)),
    ("4. 10th lord in the 12th; Ketu in the 10th", "HTJAH-II", ((9555, 9580), (9890, 9910))),
)
GENERAL_GREP = (
    ("5. House position by Bhava or by Rasi", r"bhava chart|bhava madhya|rasi chart|sandhi|house and not the sign", 15, 10),
    ("6. A house's lord in the 6th, 8th or 12th from that house", r"6th, 8th or 12th from|8th from the", 10, 8),
    ("7. Neechabhanga and a lord's strength", r"neechabhanga", 10, 6),
)


def general_passages(with_text: bool) -> tuple[str, list[str]]:
    """The coordinator's addendum passages; returns the markdown and a one-line summary per item."""
    o = ["# General passages", ""]
    if not with_text:
        o += ["Book text is not committed. These are the line ranges; the verbatim, line-numbered text is in "
              "`data/opposite_verdicts_2026-11-05/packets_with_text/GENERAL_PASSAGES.md` on the project PC.", ""]
    summary: list[str] = []

    def emit(work: str, a: int, b: int, label: str = "") -> None:
        f = corpus.file_for(work)
        o.append(f"- `{work}:{a}-{b}`{label}")
        if with_text:
            o.extend(["", "```", _numbered(f.path, a, b), "```", ""])

    for title, work, ranges in GENERAL:
        o += [f"## {title}", ""]
        for a, b in ranges:
            emit(work, a, b)
        o.append("")
        summary.append(f"{title}: {work} {ranges}")
    f = corpus.file_for("HTJAH-I")
    lines = corpus.lines_of(f.path)
    for title, pattern, ctx, cap in GENERAL_GREP:
        rx = re.compile(pattern, re.I)
        hits = [i for i, l in enumerate(lines, 1) if rx.search(l)]
        o += [f"## {title}", "", f"Pattern `{pattern}`, case-insensitive: {len(hits)} hits in HTJAH-I, "
              f"showing the first {min(cap, len(hits))} with {ctx} lines of context.", ""]
        for i in hits[:cap]:
            emit("HTJAH-I", max(1, i - ctx), min(len(lines), i + ctx), f" (hit at line {i})")
        o.append("")
        summary.append(f"{title}: {len(hits)} hits, kept {[*hits[:cap]]}")
    return "\n".join(o) + "\n", summary


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    pinned = json.loads((ROOT / "tests/fixtures/golden_accuracy_baseline.json").read_text(encoding="utf-8"))
    keys = pinned["real_errors"]
    studies = st.all_studies()
    total: Counter = Counter()
    for s in studies:
        total.update(s.tally())
    opp = {f"{s.id} H{h.house}/{h.sig}" for s in studies for h in s.houses if h.agreement == st.OPPOSITE}
    recs = {r["id"]: r for r in corpus.worked_examples()}
    LOCAL.mkdir(parents=True, exist_ok=True)
    rows, failed = [], []
    for key in keys:
        rid, tail = key.split(" ")
        name = f"{rid}__{tail.replace('/', '_')}.md"
        try:
            text, meta = packet(key, recs[rid], False)
            full, _ = packet(key, recs[rid], True)
        except Exception as exc:  # report the row and keep extracting the rest
            failed.append(f"{key}: {type(exc).__name__}: {exc}")
            continue
        (OUT / name).write_text(text, encoding="utf-8")
        (LOCAL / name).write_text(full, encoding="utf-8")
        rows.append({**meta, "file": name})
    n = sum(total.values())
    idx = ["# Evidence packets: the opposite verdicts", "",
           f"Study-tool totals on this tree: {len(studies)} charts, {n} conclusions: "
           f"agree {total[st.AGREE]}, one step apart {total[st.NEAR]}, opposite {total[st.OPPOSITE]}.", "",
           f"Baseline `real_errors`: {len(keys)} rows. Study-tool opposites equal that list: "
           f"{opp == set(keys)} (only in study: {sorted(opp - set(keys)) or 'none'}; "
           f"only in baseline: {sorted(set(keys) - opp) or 'none'}). Baseline track_b "
           f"{pinned['track_b']['correct']}/{pinned['track_b']['total']}, within-one "
           f"{pinned['track_b_ordinal']['correct']}/{pinned['track_b_ordinal']['total']}.", "",
           "Book text is not committed; each packet gives the exact line ranges, and the verbatim text "
           "is in `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC. "
           "Regenerate with `_build_packets.py`.", "",
           "| row | engine | Raman | write-up | lines | located | decide clause | packet |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        idx.append(f"| {r['key']} | {r['engine']} | {r['raman']} | {r['span']} | {r['lines']} | "
                   f"{r['where'] or '-'} | {r['clause']} | [{r['file']}]({r['file']}) |")
    if failed:
        idx += ["", "Rows not extracted:", *(f"- {x}" for x in failed)]
    (OUT / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"totals charts={len(studies)} n={n} {dict(total)} match={opp == set(keys)}")
    for r in rows:
        print(r["key"], "|", r["engine"], "vs", r["raman"], "|", r["span"], r["lines"], "| head", r["heading"],
              "| chart", r["chart"], "| where", r["where"], "| outside", r["outside"], "|", r["notes"], "| shown",
              [(a, z) for a, z, _ in r["shown"]])
    (OUT / "GENERAL_PASSAGES.md").write_text(general_passages(False)[0], encoding="utf-8")
    full, summary = general_passages(True)
    (LOCAL / "GENERAL_PASSAGES.md").write_text(full, encoding="utf-8")
    print("\n".join(summary))
    print("FAILED", failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
