"""The Master Synthesis Layer — the reading's single coherent judgement.

An experienced astrologer does not read a chart factor by factor and stop; he
first forms ONE governing picture — the planet that runs the horoscope, the
combination that colours the life, the fault-line that keeps recurring, the
theme it all points to, the phase now unfolding — and then lets every particular
verdict hang off that spine. This module is that spine.

It is a **pure, deterministic reducer** over blocks the engine has ALREADY
computed (`planet_strength`, `classical_factors`, `judgements`,
`domain_decisions`, `dasha_now`, `classical_yogas`). It invents no astrology and
generates no free text beyond stitching real engine output into plain sentences.
It runs LAST, so every input exists, and produces ``extras.master``:

    dominant_planet   — who runs the chart, and why
    dominant_yoga     — the combination that most colours the life
    dominant_challenge— the recurring fault-line (planet / pair)
    core_strengths    — the top life-capacities (by real domain grades)
    core_weaknesses   — the areas asking for care
    life_theme        — one synthesised line the whole reading serves
    current_phase     — the daśā now running and what it lights up
    decisive_factors  — the ≤10 pieces of evidence that actually decide the
                        verdict (the anti-rule-dumping selector) — the report
                        LEADS with these and collapses the rest.

Fail-soft: any error yields an empty (or partial) block, never a broken reading.
Nothing here is a probability — grades are Raman-doctrine grades, the phase is a
real daśā window, the strengths are the engine's own composites.
"""
from __future__ import annotations

from typing import Any, Mapping

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu")


def _functional_index(cf: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """planet -> its functional-role summary, from classical_factors."""
    out: dict[str, dict[str, Any]] = {}
    for f in (cf.get("functional") or []):
        if isinstance(f, dict) and f.get("planet"):
            out[f["planet"]] = f
    return out


def _dominant_planet(ps: Mapping[str, Any],
                     fx: Mapping[str, dict[str, Any]]) -> dict[str, Any] | None:
    """The strongest graha by the real composite, read together with its
    functional role for the ascendant. Sun/Moon/lagna-lord get a nudge only as a
    tie-break within a hair of the top (they run the chart when co-equal)."""
    planets = (ps.get("planets") or []) if isinstance(ps, Mapping) else []
    scored = [p for p in planets if isinstance(p, dict) and p.get("composite") is not None]
    if not scored:
        return None
    # yogakāraka is decisive for the ascendant, so break near-ties in its favour.
    def rank(p: dict[str, Any]) -> tuple[float, int]:
        comp = float(p["composite"])
        yk = 1 if fx.get(p["planet"], {}).get("is_yogakaraka") else 0
        return (comp, yk)

    top = max(scored, key=rank)
    planet = top["planet"]
    comp = int(top["composite"])
    role = fx.get(planet) or {}
    tags = role.get("tags") or []
    ruled = role.get("houses_ruled") or []
    # a one-line, honest reason.
    bits = [f"the strongest graha (composite {comp}/100)"]
    if role.get("is_yogakaraka"):
        bits.append("and a yogakāraka for your ascendant")
    elif role.get("nature") == "benefic":
        bits.append("and a functional benefic")
    elif role.get("nature") == "malefic":
        bits.append("though a functional malefic — its power cuts both ways")
    if ruled:
        houses = ", ".join(_ordinal(h) for h in sorted(ruled))
        bits.append(f"ruling your {houses} house{'s' if len(ruled) > 1 else ''}")
    return {
        "planet": planet,
        "composite": comp,
        "is_yogakaraka": bool(role.get("is_yogakaraka")),
        "nature": role.get("nature", ""),
        "houses_ruled": sorted(ruled),
        "dignity": top.get("dignity"),
        "reason": f"{planet} is {', '.join(bits)}.",
    }


def _dominant_yoga(reading: Mapping[str, Any]) -> dict[str, Any] | None:
    """The most intense classical combination present — the one that most
    colours the life, named with its effect and its Raman citation."""
    yogas = [y for y in (reading.get("classical_yogas") or []) if isinstance(y, dict)]
    if not yogas:
        return None
    top = max(yogas, key=lambda y: float(y.get("intensity", 0.0)))
    if not top.get("name"):
        return None
    return {
        "name": top.get("name", ""),
        "sanskrit": top.get("sanskrit", ""),
        "effect": top.get("description", ""),
        "reference": top.get("reference", ""),
        "intensity": round(float(top.get("intensity", 0.0)), 3),
    }


def _dominant_challenge(ps: Mapping[str, Any], cf: Mapping[str, Any],
                        judgements: Mapping[str, Any]) -> dict[str, Any] | None:
    """The chart's recurring fault-line — the planet (or pair) carrying the most
    affliction, corroborated across the concrete classical factors and the
    weighted negative evidence. Concrete planets first (a war, a debilitation, a
    combustion, a maraka), then the worst-graded domain as the felt effect."""
    planets = {p["planet"]: p for p in (ps.get("planets") or [])
               if isinstance(p, dict) and p.get("planet")}
    label: str | None = None
    subjects: list[str] = []
    kind = ""
    # 1) a planetary war is the sharpest single-pair affliction.
    wars = cf.get("graha_yuddha") or []
    if wars:
        w = wars[0]
        subjects = [w.get("a", ""), w.get("b", "")]
        label = f"the {w.get('a')}–{w.get('b')} planetary war"
        kind = "graha_yuddha"
    # 2) else a debilitated (un-cancelled) planet.
    if label is None:
        nb = {n.get("planet") for n in (cf.get("neecha_bhanga") or [])
              if isinstance(n, dict)}
        debil = [p for p, row in planets.items()
                 if str(row.get("dignity", "")).lower() == "debilitated" and p not in nb]
        if debil:
            worst = min(debil, key=lambda p: planets[p].get("composite") or 0)
            subjects = [worst]
            label = f"a debilitated {worst}"
            kind = "debilitation"
    # 3) else a combust planet.
    if label is None:
        combust = [p for p, row in planets.items() if row.get("combust")]
        if combust:
            worst = min(combust, key=lambda p: planets[p].get("composite") or 0)
            subjects = [worst]
            label = f"a combust {worst}"
            kind = "combustion"
    # 4) else the weakest significant graha overall.
    if label is None and planets:
        worst = min(planets.values(), key=lambda r: r.get("composite") or 999)
        if (worst.get("composite") or 100) < 45:
            subjects = [worst["planet"]]
            label = f"a weak {worst['planet']} (composite {int(worst['composite'])}/100)"
            kind = "weak_planet"
    if label is None:
        return None
    # the felt effect: the worst-graded domain from the reconciled judgements.
    felt = None
    worst_dom = None
    worst_score = None
    for key, jd in (judgements or {}).items():
        if not isinstance(jd, dict):
            continue
        sc = jd.get("score")
        if sc is None:
            continue
        if worst_score is None or sc < worst_score:
            worst_score, worst_dom = sc, jd
    if worst_dom is not None and worst_dom.get("negative"):
        felt = worst_dom["negative"][0].get("text")
    return {
        "label": label,
        "subjects": [s for s in subjects if s],
        "kind": kind,
        "felt_in": (worst_dom or {}).get("label"),
        "felt_detail": felt,
        "reason": _challenge_reason(label, worst_dom),
    }


def _challenge_reason(label: str, worst_dom: Mapping[str, Any] | None) -> str:
    if worst_dom and worst_dom.get("label"):
        return (f"The recurring strain is {label}; it is felt most in "
                f"{worst_dom['label'].lower()}.")
    return f"The recurring strain is {label}."


def _capacities(decisions: list, judgements: Mapping[str, Any]
                ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Top and bottom life-domains by the real doctrine grade — the chart's
    core strengths and the areas asking for care, phrased as capacities."""
    rows = [d for d in (decisions or []) if isinstance(d, dict) and d.get("score") is not None]
    if not rows:
        return [], []
    rows.sort(key=lambda d: d["score"], reverse=True)

    def cap(d: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain": d.get("key"),
            "label": d.get("label", ""),
            "score": d.get("score"),
            "potential": d.get("potential", ""),
            "modern": d.get("modern", ""),
        }

    strengths = [cap(d) for d in rows if (d.get("score") or 0) >= 55][:3]
    weaknesses = [cap(d) for d in reversed(rows) if (d.get("score") or 0) <= 45][:3]
    # ensure we always show at least the extremes even in a flat chart.
    if not strengths:
        strengths = [cap(rows[0])]
    if not weaknesses and len(rows) > 1:
        weaknesses = [cap(rows[-1])]
    return strengths, weaknesses


def _current_phase(dasha_now: Mapping[str, Any],
                   decisions: list) -> dict[str, Any] | None:
    """The daśā running now and which domains it lights up (Active now)."""
    md = (dasha_now or {}).get("md") or {}
    lord = md.get("md_lord")
    if not lord:
        return None
    span = ""
    if md.get("start_date") and md.get("end_date"):
        span = f"{md['start_date'][:4]}–{md['end_date'][:4]}"
    ad = (dasha_now or {}).get("ad") or {}
    active = [d.get("label", "") for d in (decisions or [])
              if isinstance(d, dict) and d.get("timing") == "Active now"]
    return {
        "md_lord": lord,
        "span": span,
        "ad_lord": ad.get("ad_lord"),
        "active_domains": [a for a in active if a],
        "summary": _phase_summary(lord, span, ad.get("ad_lord"), active),
    }


def _phase_summary(lord: str, span: str, ad_lord: str | None,
                   active: list[str]) -> str:
    span_bit = f" ({span})" if span else ""
    ad_bit = f", {ad_lord} antardaśā" if ad_lord else ""
    if active:
        areas = ", ".join(a.lower() for a in active[:3])
        return f"{lord} mahādaśā{span_bit}{ad_bit} — currently activating {areas}."
    return (f"{lord} mahādaśā{span_bit}{ad_bit} — a quieter, consolidating "
            f"stretch rather than a headline period.")


def _decisive_factors(judgements: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The ≤10 pieces of evidence that actually decide the verdict — the top
    signed contributions across ALL reconciled domains by |contrib|, de-duped by
    text. This is the anti-rule-dumping selector (#15): the report leads with
    these and collapses the rest into the per-domain breakdowns."""
    pool: list[dict[str, Any]] = []
    for key, jd in (judgements or {}).items():
        if not isinstance(jd, dict):
            continue
        dom = jd.get("label", "")
        for sign, items in (("+", jd.get("positive") or []),
                            ("-", jd.get("negative") or [])):
            for it in items:
                if not isinstance(it, dict) or not it.get("text"):
                    continue
                pool.append({
                    "text": it["text"],
                    "contrib": it.get("contrib", 0),
                    "role": it.get("role", ""),
                    "domain": dom,
                    "polarity": "positive" if sign == "+" else "negative",
                })
    # de-dup by text, keeping the strongest instance.
    best: dict[str, dict[str, Any]] = {}
    for it in pool:
        k = it["text"].lower()
        if k not in best or abs(it["contrib"]) > abs(best[k]["contrib"]):
            best[k] = it
    ranked = sorted(best.values(), key=lambda it: abs(it["contrib"]), reverse=True)
    return ranked[:10]


def _life_theme(dom_planet: Mapping[str, Any] | None,
                strengths: list, weaknesses: list,
                challenge: Mapping[str, Any] | None,
                phase: Mapping[str, Any] | None) -> str:
    """One synthesised line the whole reading serves — the strongest capacity,
    the dominant challenge, and the current tone, stitched from real output."""
    parts: list[str] = []
    if strengths:
        s = strengths[0]
        parts.append(f"your chart's real strength is {s['label'].lower()}"
                     f" ({s.get('potential', '').lower()} potential)")
    if dom_planet and dom_planet.get("planet"):
        parts.append(f"carried above all by {dom_planet['planet']}")
    if challenge and challenge.get("label"):
        parts.append(f"while {challenge['label']} is the fault-line to manage")
    if weaknesses:
        parts.append(f"and {weaknesses[0]['label'].lower()} asks for patience")
    if not parts:
        return ""
    line = ", ".join(parts)
    if phase and phase.get("md_lord"):
        line += (f" — the running {phase['md_lord']} period sets the present tone")
    return line[0].upper() + line[1:] + "."


def _ordinal(n: int) -> str:
    if 10 <= (int(n) % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(int(n) % 10, "th")
    return f"{n}{suffix}"


def build_master(reading: Mapping[str, Any],
                 extras: Mapping[str, Any]) -> dict[str, Any]:
    """Reduce the already-computed reading blocks into ONE governing judgement.

    Reads ``extras`` (planet_strength, classical_factors, judgements,
    domain_decisions, dasha_now) + ``reading.classical_yogas``. Returns the
    ``master`` block, or ``{}`` on any failure. Every sub-field is independently
    fail-soft, so a partial block is preferred over none.
    """
    try:
        ps = extras.get("planet_strength") or {}
        cf = extras.get("classical_factors") or {}
        judgements = extras.get("judgements") or {}
        decisions = extras.get("domain_decisions") or []
        dasha_now = extras.get("dasha_now") or {}
        fx = _functional_index(cf)

        dom_planet = _safe(_dominant_planet, ps, fx)
        dom_yoga = _safe(_dominant_yoga, reading)
        challenge = _safe(_dominant_challenge, ps, cf, judgements)
        strengths, weaknesses = _safe(_capacities, decisions, judgements) or ([], [])
        phase = _safe(_current_phase, dasha_now, decisions)
        decisive = _safe(_decisive_factors, judgements) or []
        theme = _safe(_life_theme, dom_planet, strengths, weaknesses, challenge, phase) or ""

        master: dict[str, Any] = {
            "dominant_planet": dom_planet,
            "dominant_yoga": dom_yoga,
            "dominant_challenge": challenge,
            "core_strengths": strengths,
            "core_weaknesses": weaknesses,
            "life_theme": theme,
            "current_phase": phase,
            "decisive_factors": decisive,
            "note": (
                "One governing judgement the whole reading derives from — the "
                "strongest planet, the defining combination, the recurring "
                "challenge, and the phase now running. Every figure is real "
                "engine output (Raman-doctrine grades and the actual daśā "
                "window), never a probability of events."
            ),
        }
        # only return if we have at least the spine.
        if any([dom_planet, strengths, decisive, phase]):
            return master
        return {}
    except Exception:  # noqa: BLE001 — never block a reading
        return {}


def _safe(fn, *args):
    """Run a sub-reducer, swallowing any error to keep the master fail-soft."""
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001
        return None
