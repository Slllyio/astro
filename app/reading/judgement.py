"""The conflict-resolution / weighted-synthesis engine.

Raman never judged a horoscope placement by placement — he weighed all the
evidence bearing on a matter and delivered ONE reconciled verdict. This module
does exactly that on top of the engine's real computed evidence:

  1. gather every signed piece of evidence for a domain (the house, its lord,
     the kāraka — their occupants, aspects, conjunctions, dignity, combustion);
  2. WEIGHT each by Raman's hierarchy of importance (lagna / lagna-lord / Moon /
     9th & 10th lords rank highest; dignities/aspects are middling; single
     aphorisms lowest);
  3. RESOLVE the positive and negative weight into a dominant influence and a
     single synthesised verdict ("fundamentally strong but delayed by Saturn —
     progress after sustained effort"), never a list of raw contradictions;
  4. keep the evidence so the score can EXPLAIN ITSELF (+contrib / −contrib).

Deterministic, fail-soft, reasons only from real engine output. The verdict it
produces feeds both the domain dashboard and the classical narrative's
synthesis chapter, so the two can never disagree.
"""
from __future__ import annotations

import re as _re
from typing import Any, Mapping

_ORD = {"1th": "1st", "2th": "2nd", "3th": "3rd"}

# ── Raman's hierarchy of evidential weight ──────────────────────────────────
W_VERY_HIGH, W_HIGH, W_MEDIUM, W_LOW = 5, 3, 2, 1
_STRONG_HOUSES = {1, 9, 10}  # a lord of these ranks Very High (kendra/trikoṇa axis)


def _role_weight(role: str, house: int) -> int:
    if role == "lord":
        return W_VERY_HIGH if house in _STRONG_HOUSES else W_HIGH
    if role == "karaka":
        return W_HIGH
    return W_MEDIUM  # the bhāva's own occupants / aspects


def _band(idx: float) -> str:
    if idx >= 6.0:
        return "excellent"
    if idx >= 4.5:
        return "strong"
    if idx >= 3.5:
        return "good"
    if idx >= 2.0:
        return "moderate"
    return "weak"


def _clean(text: str) -> str:
    """Shorten a finding to its essence, in readable prose, for a verdict clause."""
    t = str(text).split("(")[0].split("[")[0].strip().rstrip(".")
    if t.lower().startswith("sutra:"):
        t = t[6:].strip()
        # a sutra reads "10th lord in the 11th: immense riches…" — keep the effect
        if ":" in t:
            t = t.split(":", 1)[1].strip()
    for cut in (";", " — "):
        if cut in t:
            t = t.split(cut)[0].strip()
    # readability fixes on the engine's terse finding grammar
    t = t.replace("in a own sign", "in its own sign")
    t = t.replace("in a inimical sign", "in an inimical sign")
    t = t.replace("in a exalted sign", "exalted")
    t = t.replace("in a debilitated sign", "debilitated")
    for bad, good in _ORD.items():
        t = _re.sub(rf"\b{bad}\b", good, t)
    return t


def _synthesise(label: str, band: str, pos: list, neg: list,
                wp: int, wn: int, timing: str | None) -> str:
    """Reconcile the weighted evidence into one judicial verdict."""
    lab = label.lower()
    top_pos = _clean(pos[0]["text"]) if pos else ""
    top_neg = _clean(neg[0]["text"]) if neg else ""
    # timing modifier — the daśā MODIFIES the natal promise, never replaces it.
    if timing == "Active now":
        tim = "and the period now running brings it forward"
    elif timing == "Warming up":
        tim = "and the current period touches it only mildly"
    else:
        tim = "though the present period does little to advance it"

    strong_neg = bool(neg) and wn >= 0.4 * max(wp, 1)
    strong_pos = bool(pos) and wp >= 0.4 * max(wn, 1)

    if band in ("excellent", "strong"):
        if strong_neg:
            return (f"{label} is fundamentally strong, but {top_neg} holds it "
                    f"back, so its promise ripens through effort rather than at "
                    f"once — {tim}.")
        return f"{label} is strong and well supported, {tim}."
    if band == "good":
        if strong_neg:
            return (f"{label} is favourable on the whole, tempered by {top_neg}; "
                    f"good results come with some delay, {tim}.")
        return f"{label} is favourable, {tim}."
    if band == "moderate":
        if strong_pos and strong_neg:
            return (f"{label} is finely balanced — {top_pos} supports it while "
                    f"{top_neg} works against it — so outcomes fluctuate rather "
                    f"than settle, {tim}.")
        if strong_pos:
            return (f"{label} is of a middling order, though {top_pos} lends it "
                    f"real support, {tim}.")
        return (f"{label} is of an ordinary character and asks for patience, "
                f"{tim}.")
    # weak
    if strong_pos:
        return (f"{label} is the weaker side of the horoscope, yet {top_pos} "
                f"offers some relief; progress is limited rather than denied, "
                f"{tim}.")
    return (f"{label} is poorly supported and calls for realistic expectation, "
            f"{tim}.")


def _dedup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse repeated evidence (same text) to its strongest instance so the
    weighted totals are not double-counted."""
    best: dict[str, dict[str, Any]] = {}
    for it in items:
        k = it["text"].lower()
        if k not in best or abs(it["contrib"]) > abs(best[k]["contrib"]):
            best[k] = it
    return list(best.values())


def build_judgements(extras: Mapping[str, Any]) -> dict[str, Any]:
    """Per domain: the weighted evidence + the single reconciled verdict.

    Returns ``{domain_key: {label, score, confidence, band, verdict, positive,
    negative, weighted_positive, weighted_negative, dominant}}``. Fail-soft → {}.
    """
    try:
        hd = (extras.get("house_doctrine") or {}).get("houses") or {}
        decisions = extras.get("domain_decisions") or []
        if not hd or not decisions:
            return {}
        out: dict[str, Any] = {}
        for d in decisions:
            houses = d.get("houses") or []
            if not houses:
                continue
            h = int(houses[0])
            hv = hd.get(str(h)) or {}
            pos: list[dict[str, Any]] = []
            neg: list[dict[str, Any]] = []
            for role, key in (("bhava", "lagna"), ("lord", "lord"),
                              ("karaka", "karaka")):
                fv = hv.get(key) or {}
                w = _role_weight(role, h)
                for f in fv.get("findings", []) or []:
                    delta = float(f.get("delta", 0.0))
                    if delta == 0:
                        continue
                    contrib = round(w * delta * 1.8)
                    if contrib == 0:
                        contrib = 1 if delta > 0 else -1
                    item = {"text": _clean(f.get("text", "")), "weight": w,
                            "contrib": contrib, "role": role}
                    (pos if contrib > 0 else neg).append(item)
            pos = _dedup(pos)
            neg = _dedup(neg)
            pos.sort(key=lambda x: -x["contrib"])
            neg.sort(key=lambda x: x["contrib"])
            wp = sum(i["contrib"] for i in pos)
            wn = -sum(i["contrib"] for i in neg)
            idx = float(d.get("potential_index") or 0.0)
            band = _band(idx)
            verdict = _synthesise(d.get("label", ""), band, pos, neg, wp, wn,
                                  d.get("timing"))
            out[d["key"]] = {
                "label": d.get("label", ""),
                "score": d.get("score"),
                "confidence": d.get("confidence"),
                "band": band,
                "verdict": verdict,
                "positive": pos[:5],
                "negative": neg[:5],
                "weighted_positive": wp,
                "weighted_negative": wn,
                "dominant": "positive" if wp >= wn else "negative",
            }
        return out
    except Exception:  # noqa: BLE001
        return {}
