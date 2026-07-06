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

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.medini.doctrine.domains.house_judgment import (
    HouseJudgment,
    _antardasha_spans,
    _birth_elapsed_into_md,
    _maha_sequence,
    judge_all_houses_doctrine,
    judge_house_doctrine,
)

# Model split (the user's explicit choice): the engine has already done the
# astrological reasoning, so a cheap tier renders the twelve grounded per-house
# readings; the whole-chart synthesis — where prose quality matters most — uses Opus.
READING_MODEL = "claude-haiku-4-5"
SYNTHESIS_MODEL = "claude-opus-4-8"
DEFAULT_MODEL = SYNTHESIS_MODEL  # back-compat for interpret_house

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
        system=[{"type": "text", "text": _SYSTEM,
                 "cache_control": {"type": "ephemeral"}}],
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


# ------------------------------------------------- dasha timing resolution

def _jd_to_iso(jd: float) -> str:
    """Julian Day -> 'YYYY-MM' (Fliegel/Van Flandern; pure, no swe dependency)."""
    z = int(jd + 0.5)
    a = z
    if z >= 2299161:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return f"{year:04d}-{month:02d}"


def resolve_current_dasha(chart, birth_jd: float, target_jd: float) -> dict[str, Any]:
    """Resolve the Vimshottari period running at ``target_jd`` and the full window
    geometry, so an interpretation can say *when* a house activates. The engine does
    not infer this from a date — it must be handed a ``dasha={"md":..,"ad":..}`` dict.

    Returns ``{"md","ad","age","windows":[{lord,age_span,start_date,end_date,
    is_current,antardashas:[...]}]}``. Feed ``{"md":..,"ad":..}`` straight into
    ``judge_all_houses_doctrine(chart, dasha=...)``."""
    moon_lon = chart.bundle.chart.planet_lons["Moon"]
    age = (target_jd - birth_jd) / DAYS_PER_VEDIC_YEAR
    elapsed0 = _birth_elapsed_into_md(moon_lon)
    md = ad = None
    windows: list[dict[str, Any]] = []
    for i, (lord, s, e) in enumerate(_maha_sequence(moon_lon)):
        elapsed = elapsed0 if i == 0 else 0.0
        md_current = s <= age < e
        if md_current:
            md = lord
        antars: list[dict[str, Any]] = []
        for al, as_, ae_ in _antardasha_spans(lord, s, e, elapsed):
            ad_current = md_current and as_ <= age < ae_
            if ad_current:
                ad = al
            antars.append({
                "lord": al, "age_span": [round(as_, 2), round(ae_, 2)],
                "start_date": _jd_to_iso(birth_jd + as_ * DAYS_PER_VEDIC_YEAR),
                "end_date": _jd_to_iso(birth_jd + ae_ * DAYS_PER_VEDIC_YEAR),
                "is_current": ad_current,
            })
        windows.append({
            "lord": lord, "age_span": [round(s, 2), round(e, 2)],
            "start_date": _jd_to_iso(birth_jd + s * DAYS_PER_VEDIC_YEAR),
            "end_date": _jd_to_iso(birth_jd + e * DAYS_PER_VEDIC_YEAR),
            "is_current": md_current, "antardashas": antars,
        })
    return {"md": md, "ad": ad, "age": round(age, 2), "windows": windows}


# --------------------------------------- lossless de-duplicated chart grounding

def _house_timing_summary(t: dict[str, Any]) -> dict[str, Any]:
    """The per-house timing the interpreter actually needs — the running period,
    its tier, and which dasa windows activate THIS house — not the full 81-window
    geometry (that is deterministic and identical across houses)."""
    return {
        "current_maha_lord": t["current_maha_lord"],
        "current_antar_lord": t["current_antar_lord"],
        "current_activation_tier": t["current_activation_tier"],
        "influencing_planets": t["influencing_planets"],
        "activating_windows": [
            {"maha_lord": w["maha_lord"], "age_span": w["age_span"],
             "tiers": sorted({a["activation_tier"] for a in w["antardasas"]})}
            for w in t["windows"] if w["lord_activates_house"]
        ],
    }


def build_chart_grounding(
    judgments: "Sequence[HouseJudgment] | dict[int, HouseJudgment]",
    *,
    dasha: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Whole-chart grounding, de-duplicated and lossless.

    The chart's ≤9 planets fill 36 lord/karaka slots (e.g. Jupiter as lord/karaka of
    houses 2, 5, 9, 11), and a planet's dignity/aspect/conjunction findings are the
    same wherever it rules. So each planet is serialized **once** into a ``planets``
    dossier (all findings retained), and each house references its lord/karaka by
    name — no information lost, ~4x fewer tokens than repeating every packet."""
    js = _as_judgment_list(judgments)
    planets: dict[str, Any] = {}
    houses: list[dict[str, Any]] = []
    for hj in js:
        p = build_grounding(hj)
        for role in ("lord", "karaka"):
            v = p[role]
            planets.setdefault(v["subject"], {
                "planet": v["subject"], "verdict": v["verdict"],
                "rasi_score": v["rasi_score"], "navamsa_score": v["navamsa_score"],
                "findings": v["findings"],
            })
        houses.append({
            "house": p["house"], "domain": p["domain"],
            "headline_verdict": p["headline_verdict"],
            "sutra_polarity_blend": p["sutra_polarity_blend"],
            "bhava": p["bhava"],                     # house-specific — inline
            "lord": p["lord"]["subject"],            # reference into `planets`
            "karaka": p["karaka"]["subject"],
            "synthesis": p["synthesis"]["prose"],
            "influencers": p["synthesis"]["influencers"],
            "afflicted_activators": p["synthesis"]["afflicted_activators"],
            "fired_sutras": p["fired_sutras"],       # verbatim, per house
            "combinations": p["combinations"],
            "from_moon": p.get("from_moon"),
            "first_house_testimony": p.get("first_house_testimony"),
            "timing": _house_timing_summary(p["timing"]),
        })
    out: dict[str, Any] = {"planets": planets, "houses": houses}
    if dasha is not None:
        out["dasha"] = dasha
    return out


def _as_judgment_list(judgments) -> list[HouseJudgment]:
    if isinstance(judgments, dict):
        return [judgments[h] for h in sorted(judgments)]
    return list(judgments)


# -------------------------------------------- structured reading output schema

from pydantic import BaseModel, Field  # noqa: E402  (kept near its sole use)


class _HouseReading(BaseModel):
    house: int = Field(ge=1, le=12)
    reading: str


class ChartReadings(BaseModel):
    """The twelve grounded per-house readings, one structured object."""
    readings: list[_HouseReading]


_READING_TASK = """\
Below is the engine's executed judgment for one chart: a `planets` dossier (each \
planet assessed once, with the signed findings behind its verdict) and twelve \
`houses` that reference their lord/karaka by name into that dossier. For EACH of the \
twelve houses, write one grounded paragraph: state the headline verdict and explain \
it from the bhava's own findings and its lord's/karaka's dossier entry, weigh the \
from-Moon testimony and any stated combination, and — if a running period is given \
in `dasha` or the house's timing — name it. Interpret only what is encoded; trace \
every claim to a verdict, a finding, a verbatim sutra, a combination, or a window."""

_SYNTHESIS_TASK = """\
You are given (1) a compact twelve-house summary the engine judged and (2) the twelve \
grounded per-house readings already written. Synthesize a whole-life reading: weigh \
the houses against each other, name the structures that recur across houses, identify \
the strongest and weakest departments, note where the Chandra-Lagna re-weights a \
house, and name the running dasa and what it activates. Keep every claim traceable to \
the encoded evidence; introduce nothing new."""


def interpret_chart(
    judgments: "Sequence[HouseJudgment] | dict[int, HouseJudgment]",
    *,
    dasha: dict[str, Any] | None = None,
    client: "Anthropic | None" = None,
    reading_model: str = READING_MODEL,
    synthesis_model: str = SYNTHESIS_MODEL,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """Hybrid, cached, structured whole-chart interpretation.

    Call 1 (cheap tier, structured): one request over the de-duplicated grounding
    returns all twelve grounded per-house readings. Call 2 (Opus, streamed): the
    whole-chart synthesis. The static system prompt and the planet dossier are marked
    cacheable, so repeat runs read the shared prefix at a fraction of the cost.

    Returns ``{"readings": {1..12: str}, "synthesis": str, "dasha": ...,
    "input_tokens": int}``."""
    import json
    cl = _client(client)
    grounding = build_chart_grounding(judgments, dasha=dasha)

    # Split the grounding so the (chart-stable) dossier is a cacheable prefix and the
    # houses are the varying tail.
    dossier_block = ("=== PLANET DOSSIER (each planet assessed once) ===\n"
                     + json.dumps(grounding["planets"], ensure_ascii=False, indent=1))
    houses_payload = {"houses": grounding["houses"]}
    if "dasha" in grounding:
        houses_payload["dasha"] = grounding["dasha"]
    houses_block = ("=== TWELVE HOUSES (lord/karaka reference the dossier) ===\n"
                    + json.dumps(houses_payload, ensure_ascii=False, indent=1))

    system_blocks = [{"type": "text", "text": _SYSTEM + "\n\n" + _READING_TASK,
                      "cache_control": {"type": "ephemeral"}}]
    user_content = [
        {"type": "text", "text": dossier_block,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": houses_block},
    ]

    # Measure the packet before sending (cost visibility; no message created).
    input_tokens = cl.messages.count_tokens(
        model=reading_model, system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
    ).input_tokens

    # Call 1 — twelve readings, structured, cheap tier.
    parsed = cl.messages.parse(
        model=reading_model, max_tokens=max_tokens,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        output_format=ChartReadings,
    ).parsed
    readings = {r.house: r.reading for r in parsed.readings}

    # Call 2 — whole-chart synthesis (Opus), grounded in the compact summary + the
    # readings just produced.
    compact = [_compact_grounding(build_grounding(hj))
               for hj in _as_judgment_list(judgments)]
    syn_block = (
        _SYNTHESIS_TASK + "\n\n=== TWELVE-HOUSE SUMMARY ===\n"
        + json.dumps(compact, ensure_ascii=False, indent=1)
        + "\n\n=== THE TWELVE READINGS ===\n"
        + json.dumps(readings, ensure_ascii=False, indent=1)
    )
    synthesis = _complete(cl, synthesis_model, syn_block, max_tokens)

    return {"readings": readings, "synthesis": synthesis,
            "dasha": dasha, "input_tokens": input_tokens}


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


def interpret_whole_chart(chart, *, birth_jd: float, target_jd: float | None = None,
                          **kw) -> dict[str, Any]:
    """Convenience: resolve the running dasa, judge all twelve houses time-anchored,
    and produce the twelve readings + synthesis in one call.

    ``birth_jd`` is required (the chart does not retain it); ``target_jd`` defaults to
    the caller-supplied 'now'. Pass ``target_jd`` explicitly for a deterministic run
    (the module never reads the wall clock)."""
    dasha = None
    if target_jd is not None:
        d = resolve_current_dasha(chart, birth_jd, target_jd)
        dasha = {"md": d["md"], "ad": d["ad"]}
    judgments = judge_all_houses_doctrine(chart, dasha=dasha)
    return interpret_chart(judgments, dasha=dasha, **kw)
