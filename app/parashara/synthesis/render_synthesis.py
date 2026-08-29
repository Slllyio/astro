"""Render the synthesis report as markdown — the reasoning layer's reader-facing surface.

Shows everything the layer computes (per the report-completeness contract): a summary table over the
twelve houses, the named-matter views, and then the FULL reasoning behind every topic — its verdict
and meaning, its doctrinal-convergence confidence (tally + tier + caveat), the genuine contradictions
reported side by side, the complete cited audit trail, and the dasha activation windows.
"""
from __future__ import annotations

from app.parashara.synthesis.activation import ActiveWindow
from app.parashara.synthesis.judgment import Judgment
from app.parashara.synthesis.synthesis import SynthesisReport

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
        out.append("### Named-matter views")
        out.append("")
        for name, j in report.matters.items():
            out.append(f"- **{name}** — *{j.verdict}*: {j.convergence.tier} — {j.convergence.tally}")
        out.append("")

    out.append("### Full reasoning, per topic")
    out.append("")
    for j in report.all_judgments:
        out.extend(_judgment_md(j))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _judgment_md(j: Judgment) -> list[str]:
    out = [f"#### {j.topic} — {j.verdict.upper()}",
           f"*{j.meaning}*", "",
           f"**Confidence ({j.convergence.tier}):** {j.convergence.tally}."]
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
    if not windows:
        return []
    strong = [w for w in windows if w.tier in ("par excellence", "limited")]
    rest = len(windows) - len(strong)
    out = ["", "**Activation windows (when it fructifies):**"]
    out += [f"- {w.label}" for w in strong[:12]]
    if len(strong) > 12:
        out.append(f"- …and {len(strong) - 12} more par-excellence/limited windows")
    if rest:
        out.append(f"- ({rest} ordinary/feeble windows omitted)")
    return out


def to_dict(report: SynthesisReport) -> dict:
    """The synthesis as a JSON-safe dict, including the computed surfaces (tally, audit lines, window
    labels) the generic serializer would miss. Complete: every judgment, its full evidence and windows."""
    return {
        "framing": ("A doctrinal-convergence reading — how strongly Parashara's cited rules concur "
                    "for this chart, an audit of rule-agreement, never a probability of an event."),
        "houses": {str(h): _judgment_dict(j) for h, j in sorted(report.houses.items())},
        "matters": {name: _judgment_dict(j) for name, j in report.matters.items()},
    }


def _judgment_dict(j: Judgment) -> dict:
    c = j.convergence
    return {
        "topic": j.topic, "houses": list(j.houses), "verdict": j.verdict, "meaning": j.meaning,
        "confidence": {
            "tier": c.tier, "tally": c.tally, "supporting": c.supporting,
            "contradicting": c.contradicting, "cancelled": c.cancelled, "net": c.net,
            "contradictions": list(c.contradictions), "caveat": c.caveat},
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
    return {"maha_lord": w.maha_lord, "antar_lord": w.antar_lord, "tier": w.tier,
            "start_age": round(w.start_age, 2), "end_age": round(w.end_age, 2), "label": w.label}


def _earliest(windows: tuple[ActiveWindow, ...]) -> str:
    """The earliest par-excellence window (else the earliest window), for the summary table."""
    if not windows:
        return "—"
    par = [w for w in windows if w.tier == "par excellence"]
    pool = par or list(windows)
    w = min(pool, key=lambda x: x.start_age)
    lo, hi = round(w.start_age), round(w.end_age)
    age = f"age {lo}" if lo == hi else f"age {lo}-{hi}"
    return f"{w.maha_lord} dasha ({age})"
