"""Render the synthesis report as markdown — the reasoning layer's reader-facing surface.

Shows everything the layer computes (per the report-completeness contract): a summary table over the
twelve houses, the named-matter views, and then the FULL reasoning behind every topic — its verdict
and meaning, its doctrinal-convergence confidence (tally + tier + caveat), the genuine contradictions
reported side by side, the complete cited audit trail, and the dasha activation windows.
"""
from __future__ import annotations

from app.parashara.synthesis.activation import ActiveWindow
from app.parashara.synthesis.judgment import Judgment
from app.parashara.synthesis.synthesis import MatterView, SynthesisReport

_HEADER = "## Deterministic synthesis — reasoning across the rules (BPHS)"
_FRAME = ("*A doctrinal-convergence reading: how strongly Parashara's own cited rules concur for this "
          "chart — an audit of rule-agreement, never a probability that an event occurs. The birth "
          "chart decides; a division corroborates; a dasha only times.*")


def to_markdown(report: SynthesisReport) -> str:
    """The full synthesis section as markdown."""
    out: list[str] = [_HEADER, "", _FRAME, ""]

    out.append("### Verdict by house")
    out.append("")
    out.append("| House | Verdict | Confidence | Earliest strong window |")
    out.append("|---|---|---|---|")
    for h in sorted(report.houses):
        j = report.houses[h]
        out.append(f"| {j.topic} | **{j.verdict}** | {j.convergence.tier} — {j.convergence.tally} "
                   f"| {_earliest(j.windows)} |")
    out.append("")

    if report.matters:
        out.append("### Named-matter views (rolled up from the houses — parallel, never averaged)")
        out.append("")
        for name, m in report.matters.items():
            parts = ", ".join(f"{h}th: {v}" for h, v in sorted(m.component_verdicts.items()))
            line = f"- **{name}** — *{m.verdict}* ({parts})"
            if m.note:
                line += f" — {m.note}"
            out.append(line)
        out.append("")

    out.append("### Full reasoning, per topic")
    out.append("")
    for j in report.all_judgments:
        out.extend(_judgment_md(j))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


#: Dusthana framing — presentation-only prose so a flourishing house of adversity never renders as
#: good news for the native. The 8th's exception (longevity) is corpus-backed; the reversal cases
#: are the vipareeta yogas, wired as evidence where their conditions actually hold.
_DUSTHANA_NOTE = {
    6: ("Framing (BPHS ch.17): the 6th's indications ARE adversities — enemies, disease, "
        "obstacles. A flourishing 6th means those indications are prominent, not that they favour "
        "the native; an afflicted 6th can even favour him (Harsha yoga, BPHS-48:124)."),
    8: ("Framing (BPHS ch.19): the 8th is read for longevity — a strong 8th indicates LONG life "
        "(BPHS-19:23); its other indications (upheaval) remain adversities."),
    12: ("Framing (BPHS-11:138): the 12th's indications are loss and expense — prominence is not "
         "favour; cf. Vimala yoga (BPHS-48:140) for the reversal case."),
}


def _judgment_md(j: Judgment) -> list[str]:
    out = [f"#### {j.topic} — {j.verdict.upper()}",
           f"*{j.meaning}*", "",
           f"**Confidence ({j.convergence.tier}):** {j.convergence.tally}."]
    if j.convergence.split_note:
        out.append(f"*{j.convergence.split_note}*")
    note = _DUSTHANA_NOTE.get(j.houses[0]) if len(j.houses) == 1 else None
    if note:
        out.append(f"> {note}")
    if j.convergence.caveat:
        out.append(f"> {j.convergence.caveat}")
    if j.convergence.contradictions:
        out.append("")
        out.append("**Contradictions (reported, not averaged):**")
        out += [f"- {c}" for c in j.convergence.contradictions]
    out.append("")
    out.append("**Audit trail (sloka → rule → condition → evidence):**")
    out += [f"- {line}" for line in j.audit]
    out += _windows_md(j.windows)
    return out


def _windows_md(windows: tuple[ActiveWindow, ...]) -> list[str]:
    """Every quality group accounted for — the favourable ones listed, the rest counted with a
    sample line each, so no grade is ever silently dropped."""
    if not windows:
        return []
    out = ["", "**Activation windows (when it fructifies):**"]
    for quality in ("auspicious", "mixed", "neutral", "adverse"):
        group = [w for w in windows if w.quality == quality]
        if not group:
            continue
        if quality in ("auspicious", "mixed"):
            out += [f"- {w.label}" for w in group[:12]]
            if len(group) > 12:
                out.append(f"- …and {len(group) - 12} more {quality} windows")
        else:
            sample = min(group, key=lambda w: w.start_age)
            out.append(f"- ({len(group)} {quality} window{'s' if len(group) > 1 else ''}, "
                       f"earliest: {sample.label})")
    return out


def to_dict(report: SynthesisReport) -> dict:
    """The synthesis as a JSON-safe dict, including the computed surfaces (tally, audit lines, window
    labels) the generic serializer would miss. Complete: every judgment, its full evidence and windows."""
    return {
        "framing": ("A doctrinal-convergence reading — how strongly Parashara's cited rules concur "
                    "for this chart, an audit of rule-agreement, never a probability of an event."),
        "houses": {str(h): _judgment_dict(j) for h, j in sorted(report.houses.items())},
        "matters": {name: _matter_dict(m) for name, m in report.matters.items()},
    }


def _matter_dict(m: MatterView) -> dict:
    return {"name": m.name, "houses": list(m.houses), "verdict": m.verdict, "note": m.note,
            "component_verdicts": {str(h): v for h, v in sorted(m.component_verdicts.items())}}


def _judgment_dict(j: Judgment) -> dict:
    c = j.convergence
    framing = _DUSTHANA_NOTE.get(j.houses[0], "") if len(j.houses) == 1 else ""
    return {
        "topic": j.topic, "houses": list(j.houses), "verdict": j.verdict, "meaning": j.meaning,
        "framing": framing,
        "confidence": {
            "tier": c.tier, "tally": c.tally, "supporting": c.supporting,
            "contradicting": c.contradicting, "cancelled": c.cancelled, "net": c.net,
            "contradictions": list(c.contradictions), "caveat": c.caveat,
            "split_note": c.split_note},
        "evidence": [_evidence_dict(e) for e in j.evidence],
        "audit_trail": list(j.audit),
        "windows": [_window_dict(w) for w in j.windows],
    }


def _evidence_dict(e) -> dict:
    return {"tier": e.tier.name.lower(), "category": e.category, "polarity": e.polarity.name.lower(),
            "rule": e.rule, "condition": e.condition, "observed": e.observed,
            "citation": f"{e.source.work}:{e.source.line}", "antidoted": e.antidoted,
            "audit_line": e.audit_line}


def _window_dict(w: ActiveWindow) -> dict:
    return {"maha_lord": w.maha_lord, "antar_lord": w.antar_lord, "quality": w.quality,
            "md_quality": w.md_quality, "ad_from_md": w.ad_from_md,
            "maraka": w.maraka, "beyond_span": w.beyond_span,
            "start_age": round(w.start_age, 2), "end_age": round(w.end_age, 2), "label": w.label}


def _earliest(windows: tuple[ActiveWindow, ...]) -> str:
    """The earliest auspicious window (else the earliest window), for the summary table."""
    if not windows:
        return "—"
    ausp = [w for w in windows if w.quality == "auspicious"]
    pool = ausp or list(windows)
    w = min(pool, key=lambda x: x.start_age)
    lo, hi = round(w.start_age), round(w.end_age)
    age = f"age {lo}" if lo == hi else f"ages {lo}-{hi}"
    return f"{w.maha_lord} dasha ({age})"
