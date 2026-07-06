"""LLM interpretation layer over the executed HTJAH doctrine.

The doctrine engine (:mod:`app.medini.doctrine.domains.house_judgment`) produces a
fully *grounded* judgment for a house: the Lagna / lord / karaka verdicts with the
signed findings that produced them, the sutras (verbatim) that fired, the named
combinations Raman states for the house, and the dasa windows in which they
fructify. That is structured doctrine — it is not prose a person reads.

This module turns that structure into a reading by asking Claude to *interpret*
it. The single design constraint is **grounding**: Claude is given only the
encoded evidence and is instructed to interpret nothing beyond it — every claim in
the reading must trace back to a verdict label, a listed finding, a fired sutra
quote, a stated combination, or a dasa window. It reads the chart Raman's engine
already judged; it does not re-judge the chart, and it does not invent placements,
aspects, or predictions the engine never derived. This is what keeps the reading a
faithful interpretation of *How to Judge a Horoscope* rather than free astrology.

Auth follows the standard Anthropic SDK: set ``ANTHROPIC_API_KEY`` (or pass a
configured ``client``). No key is read from any other source.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid importing anthropic at module import time
    from anthropic import Anthropic

from app.medini.doctrine.domains.house_judgment import (
    HouseJudgment,
    judge_all_houses_doctrine,
    judge_house_doctrine,
)

# Per the claude-api guidance: default to Opus 4.8 with adaptive thinking, and
# stream so a long grounded reading never trips a request timeout.
DEFAULT_MODEL = "claude-opus-4-8"

_SYSTEM = """\
You are an interpreter of an *already-computed* judgment from B. V. Raman's \
"How to Judge a Horoscope" (HTJAH). A deterministic doctrine engine has already \
executed Raman's method on this chart. Your job is to render its structured \
verdict as a reading a person can follow — NOT to cast or judge the chart yourself.

GROUNDING IS ABSOLUTE. You may state only what the supplied doctrine evidence \
supports. Concretely:
- Every interpretive claim must trace to one of: a verdict label (e.g. "fairly \
  good"), a listed finding (with its signed contribution), a fired sutra quoted \
  verbatim, a named combination, the Chandra-Lagna (from-Moon) testimony, or a \
  dasa/antardasa window.
- Do NOT introduce any planetary placement, sign, aspect, conjunction, or \
  prediction that is not present in the evidence. If the evidence does not speak \
  to something, say the doctrine is silent on it — do not fill the gap.
- Do NOT recompute or second-guess a verdict. The labels and scores are given; \
  treat them as settled and explain what they mean.
- Use Raman's own vocabulary. When you lean on a finding or sutra, name it (its \
  verdict label, or a short verbatim fragment of the sutra) so the reading stays \
  auditable against the engine.
- Distinguish the three testimonies Raman weighs — the bhava (house) itself, its \
  lord, and its karaka — and let the headline verdict govern the tone.
- Timing comes only from the dasa windows: name the period, its activation tier, \
  and the age span, and never predict a date the windows do not give.

Write with the measured, classical register of the source. Be concrete and \
economical; no hedging boilerplate, no invented specificity."""


# --------------------------------------------------------------- serialization

def _finding(f) -> dict[str, Any]:
    return {"observation": f.text, "contribution": round(f.delta, 3),
            "frame": f.frame, "criterion": f.criterion}


def _verdict(v) -> dict[str, Any]:
    return {
        "role": v.role,
        "subject": v.subject,
        "verdict": v.label,
        "score": round(v.score, 3),
        "rasi_score": round(v.rasi_score, 3),
        "navamsa_score": round(v.navamsa_score, 3),
        "findings": [_finding(f) for f in v.findings],
    }


def _fired_sutras(hj: HouseJudgment) -> list[dict[str, Any]]:
    """The verbatim doctrine text that fired for this house, across method steps."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in hj.steps:
        for ev in step.evidence:
            if ev.rule_id in seen:
                continue
            seen.add(ev.rule_id)
            out.append({
                "id": ev.rule_id,
                "aspect_of_house": step.label,
                "polarity": ev.polarity,
                "magnitude": ev.magnitude,
                "text": ev.text,
            })
    return out


def _combinations(hj: HouseJudgment) -> list[dict[str, Any]]:
    return [{
        "text": c.text,
        "polarity": c.polarity,
        "magnitude": c.magnitude,
        "fructifies_in_dasa_of": c.dasha_lord,
        "period_running_now": c.active_now,
    } for c in hj.combinations]


def _timing(hj: HouseJudgment) -> dict[str, Any]:
    t = hj.timing
    windows = [{
        "maha_lord": w.lord,
        "age_span": [round(w.start_age, 2), round(w.end_age, 2)],
        "lord_activates_house": w.influences,
        "running_now": w.is_current,
        "antardasas": [{
            "sub_lord": a.lord,
            "age_span": [round(a.start_age, 2), round(a.end_age, 2)],
            "activation_tier": a.tier,
            "running_now": a.is_current,
        } for a in w.antardashas],
    } for w in t.windows]
    return {
        "influencing_planets": list(t.influencers),
        "current_maha_lord": t.current_md,
        "current_antar_lord": t.current_ad,
        "current_activation_tier": t.current_tier,
        "influence_by_factor": {k: list(v) for k, v in t.influence_by_factor.items()},
        "windows": windows,
    }


def build_grounding(hj: HouseJudgment) -> dict[str, Any]:
    """Serialize a :class:`HouseJudgment` into the grounded evidence packet the
    interpreter is allowed to read. Pure — no network, no key required — so it can
    be inspected and tested on its own."""
    packet: dict[str, Any] = {
        "house": hj.house,
        "domain": hj.domain,
        # Raman's house verdict is the synthesis of the three testimonies (Lagna,
        # lord, karaka). The raw sutra-polarity blend is reported separately so the
        # interpreter never mistakes it for the headline.
        "headline_verdict": hj.conclusion.label,
        "headline_score": round(hj.conclusion.score, 3),
        "sutra_polarity_blend": {"label": hj.blend_label,
                                 "score": round(hj.blend_score, 3)},
        "sutras_fired": hj.n_fired,
        "sutras_evaluated": hj.n_evaluable,
        "bhava": _verdict(hj.lagna_verdict),
        "lord": _verdict(hj.lord_verdict),
        "karaka": _verdict(hj.karaka_verdict),
        "synthesis": {
            "label": hj.conclusion.label,
            "prose": hj.conclusion.synthesis,
            "influencers": [{
                "planet": i.planet,
                "tier": i.tier,
                "is_benefic": i.is_benefic,
                "factors": list(i.factors),
                "nature": i.nature,
            } for i in hj.conclusion.influencers],
            "afflicted_activators": list(hj.conclusion.afflicted_activators),
        },
        "fired_sutras": _fired_sutras(hj),
        "combinations": _combinations(hj),
        "timing": _timing(hj),
    }
    if hj.chandra is not None:
        packet["from_moon"] = {
            "reference": hj.chandra.reference,
            "bhava_verdict": hj.chandra.bhava.label,
            "lord": hj.chandra.lord_planet,
            "lord_verdict": hj.chandra.lord.label,
            "note": hj.chandra.note,
        }
    if hj.first_house is not None:
        fh = hj.first_house
        packet["first_house_testimony"] = {
            "mind_verdict": fh.mind_verdict,
            "mind_note": fh.mind_note,
            "health_afflicted": fh.health_flag,
            "health_note": fh.health_note,
            "afflicting_malefics": list(fh.afflicting_malefics),
            "citation": fh.citation,
        }
    return packet


# ------------------------------------------------------------------- rendering

def _packet_to_text(packet: dict[str, Any]) -> str:
    """Render the evidence packet as a stable, readable block for the prompt.
    (A block reads better to the model than raw JSON and keeps the verbatim sutra
    text intact.)"""
    import json
    return json.dumps(packet, indent=2, ensure_ascii=False)


def _client(client: "Anthropic | None") -> "Anthropic":
    if client is not None:
        return client
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover - env guard
        raise RuntimeError(
            "The 'anthropic' package is required for interpretation. "
            "Install it with: pip install anthropic"
        ) from e
    # Standard SDK auth: reads ANTHROPIC_API_KEY. We deliberately do not source a
    # credential from anywhere else.
    return anthropic.Anthropic()


def _complete(client: "Anthropic", model: str, user_block: str,
              max_tokens: int) -> str:
    # Stream (per claude-api guidance for long output) and collect the final
    # message; adaptive thinking for the synthesis reasoning.
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_block}],
    ) as stream:
        final = stream.get_final_message()
    return "".join(
        b.text for b in final.content if getattr(b, "type", None) == "text"
    ).strip()


def interpret_house(
    hj: HouseJudgment,
    *,
    client: "Anthropic | None" = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
) -> str:
    """Produce a grounded reading of one house from its executed judgment."""
    packet = build_grounding(hj)
    user_block = (
        f"Interpret the {_ordinal(hj.house)} house for this native. Read only the "
        "encoded doctrine below; every statement you make must trace to it.\n\n"
        "=== DOCTRINE EVIDENCE (the engine's executed judgment) ===\n"
        f"{_packet_to_text(packet)}"
    )
    return _complete(_client(client), model, user_block, max_tokens)


def interpret_chart(
    judgments: Sequence[HouseJudgment],
    *,
    client: "Anthropic | None" = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8192,
) -> str:
    """Produce a whole-chart synthesis across the twelve houses' judgments.

    The per-house packets are compacted (headline verdict, the three testimonies'
    labels, the strongest findings, and the running dasa) so the synthesis stays
    grounded without overflowing the prompt."""
    houses = [_compact_grounding(build_grounding(hj)) for hj in judgments]
    import json
    user_block = (
        "Synthesize a whole-life reading from the twelve houses the engine judged "
        "below. Weigh the houses against each other, name the running dasa and what "
        "it activates, and keep every claim traceable to a house's verdict, its "
        "findings, or a dasa window. Do not introduce anything not encoded here.\n\n"
        "=== TWELVE-HOUSE DOCTRINE SUMMARY ===\n"
        f"{json.dumps(houses, indent=2, ensure_ascii=False)}"
    )
    return _complete(_client(client), model, user_block, max_tokens)


def _compact_grounding(packet: dict[str, Any]) -> dict[str, Any]:
    """A whole-chart-sized slice of a house packet: verdicts, the top findings, the
    synthesis prose, active combinations, and the current period."""
    def top_findings(v: dict[str, Any]) -> list[dict[str, Any]]:
        fs = sorted(v["findings"], key=lambda f: abs(f["contribution"]), reverse=True)
        return fs[:3]
    t = packet["timing"]
    return {
        "house": packet["house"],
        "domain": packet["domain"],
        "headline_verdict": packet["headline_verdict"],
        "bhava_verdict": packet["bhava"]["verdict"],
        "lord_verdict": packet["lord"]["verdict"],
        "karaka_verdict": packet["karaka"]["verdict"],
        "key_findings": {
            "bhava": top_findings(packet["bhava"]),
            "lord": top_findings(packet["lord"]),
            "karaka": top_findings(packet["karaka"]),
        },
        "synthesis": packet["synthesis"]["prose"],
        "active_combinations": [
            c["text"] for c in packet["combinations"] if c["period_running_now"]
        ],
        "current_period": {
            "maha": t["current_maha_lord"],
            "antar": t["current_antar_lord"],
            "activation_tier": t["current_activation_tier"],
        },
    }


# ------------------------------------------------------------------- utilities

_ORDINALS = ("zeroth", "first", "second", "third", "fourth", "fifth", "sixth",
             "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth")


def _ordinal(n: int) -> str:
    return _ORDINALS[n] if 0 <= n < len(_ORDINALS) else f"{n}th"


def interpret_house_of_chart(chart, house: int, **kw) -> str:
    """Convenience: judge ``house`` of ``chart`` and interpret it in one call."""
    return interpret_house(judge_house_doctrine(chart, house), **kw)


def interpret_whole_chart(chart, **kw) -> str:
    """Convenience: judge all twelve houses of ``chart`` and synthesize a reading."""
    judgments = judge_all_houses_doctrine(chart)
    if isinstance(judgments, dict):
        judgments = [judgments[h] for h in sorted(judgments)]
    return interpret_chart(judgments, **kw)
