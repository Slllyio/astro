"""Plain-text rendering of a ``ProcedureReading``, house by house in Raman's order.

Every field the reader computes is printed: each factor's items with their weights and
citations, the Navamsa step, the conclusion with its rule, and every candidate period with the
reason each lord qualifies. Nothing is collapsed to a count.

Usage:
    from app.raman_saab.procedure.render import to_text
    print(to_text(reading))
"""
from __future__ import annotations

from app.raman_saab.ordinals import ordinal
from app.raman_saab.procedure.model import MatterReading, ProcedureReading, TimingRule

_HEAD = {"house": "The {n} House", "lord": "The {n} Lord", "karaka": "Karaka",
         "moon": "Considered from the Moon"}


def _w(weight: int) -> str:
    return {1: "+", -1: "-", 0: "o"}.get(weight, str(weight))


def _matter(m: MatterReading) -> list[str]:
    n = ordinal(m.house)
    out = [f"## {n} house: {m.label}", ""]
    if m.karaka_note:
        out.append(f"(karaka: {m.karaka or 'none'}. {m.karaka_note})")
        out.append("")
    for f in m.factors:
        out.append(f"{_HEAD[f.step].format(n=n)}: {f.subject}")
        if f.merged_with:
            out.append(f"  {f.note}")
        for it in f.items:
            tag = " [convention]" if it.basis == "convention" else ""
            out.append(f"  [{_w(it.weight)}] {it.substep}: {it.text} ({it.cite}){tag}")
        out.append(f"  Navamsa: {f.navamsa_note}")
        nav = "" if f.navamsa_shift == 0 else f" (Rasi grade {f.rasi_grade})"
        out.append(f"  Grade: {f.grade}{nav}")
        out.append("")
    c = m.conclusion
    votes = ", ".join(f"{s} {v}" for s, v in c.votes)
    out.append(f"Conclusion: {c.sentence}")
    out.append(f"  votes: {votes}; plain tally: {c.tally}")
    tag = " [convention]" if c.rule_basis == "convention" else ""
    out.append(f"  rule: {c.rule} ({c.rule_cite}){tag}")
    for k, v in c.sub_answers:
        out.append(f"  {k}: {v}")
    out.append("")
    for t in m.timing:
        out += _timing(t)
    return out


def _timing(t: TimingRule) -> list[str]:
    out = [f"Timing: {t.event} [{t.kind}] ({t.cite}); window {t.window}"]
    for p, why in t.qualifiers:
        out.append(f"  qualifies: {p}: {why}")
    for p in t.pruned:
        out.append(f"  struck out: {p}")
    for nt in t.notes:
        out.append(f"  note: {nt}")
    if not t.candidates:
        out.append("  candidate periods: none")
    for c in t.candidates:
        st = f"; maraka strength {c.strength}" if c.strength else ""
        out.append(f"  {c.maha} / {c.antar}  {c.start} to {c.end}  (age {c.start_age}{st})")
        out.append(f"    {c.maha}: {c.maha_reason}")
        if c.antar != c.maha:
            out.append(f"    {c.antar} (bhukti lord, carries the event): {c.antar_reason}")
        if c.relation:
            out.append(f"    relation: {c.relation}")
        if c.transit:
            out.append(f"    transit (last): {c.transit}")
        if c.engine_tier:
            out.append(f"    [{c.engine_tier}; Raman never applies these words in a chart]")
    out.append("")
    return out


def to_text(r: ProcedureReading) -> str:
    """The whole reading as text."""
    s = r.stage_zero
    out = [f"# Procedure reading{': ' + r.name if r.name else ''}  [ayanamsa={r.ayanamsa}]", "",
           "## Before any house", f"Lagna: {s.lagna}",
           "Functional nature: " + ", ".join(f"{p} {n}" for p, n in s.functional),
           "Yogakarakas: " + (", ".join(s.yogakarakas) or "none"),
           f"Reference: the {s.stronger_reference} ({s.stronger_note})"]
    if s.span_years is not None:
        out.append(f"Span of life: about {s.span_years} years ({s.span_class}, {s.span_method})")
    if s.balarishta is not None:
        out.append(f"Balarishta: {s.balarishta}")
    for lord, a, b, status in s.dasas:
        out.append(f"  {lord} Mahadasha {a} to {b}: {status}")
    out.append("Citations: " + ", ".join(s.cites))
    out.append("")
    for m in r.matters:
        out += _matter(m)
    out.append("## Conventions (the reader's own, where Raman gives no mechanical rule)")
    out += [f"- {c}" for c in r.conventions]
    return "\n".join(out)
