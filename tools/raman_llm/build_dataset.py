"""Build the engine-output -> Raman-reading dataset for the Raman reader LLM.

Prereg: docs/raman_llm/RAMAN_READER_LLM_PREREG_2026-10-31.md (committed before any model is
trained or scored).

One row per Raman conclusion (a matter of a chart on which he gives a verdict):
  - pool: the 389 CONFIRMED conclusions on 237 charts (the engine was tuned on these)
  - H1..H5: the 262 sealed hold-out conclusions (the engine was not tuned on these)

prompt  = what the engine says, and nothing from Raman's verdict on that chart:
          chart facts, the rules that fire FOR and AGAINST the matter with their reading and
          line, the plain count, and the generic chart-factor tally (tools/raman_saab/tally_judge).
          The clause judge's own verdict is deliberately left OUT (prereg section 3).
target  = Raman's verdict, then his stated reasons where the reason coding has them
          (docs/raman_saab/reason_coding, pool only), then his own words of conclusion.

Folds: 5 folds by chart (all conclusions on one chart sit in one fold), seeded, so a chart
is never in training and test at once.

Usage: python -m tools.raman_llm.build_dataset    (writes data/raman_llm/dataset.jsonl)
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

OUT = Path("data/raman_llm/dataset.jsonl")
HOLDOUTS = {"H1": "tests/fixtures/raman_holdout_sealed.jsonl",
            "H2": "tests/fixtures/raman_holdout2_sealed.jsonl",
            "H3": "tests/fixtures/raman_holdout3_sealed.jsonl",
            "H4": "tests/fixtures/raman_holdout4_sealed.jsonl",
            "H5": "tests/fixtures/raman_holdout5_sealed.jsonl"}
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")
N_FOLDS = 5
SEED = 20261031
MAX_RULES = 18          # per side, to keep prompts under ~1k tokens
MAX_RULE_CHARS = 170

SYSTEM = ("You are a reader trained on the worked charts of B.V. Raman. You are given what a "
          "rule engine built from his books says about one matter of a horoscope. Give the "
          "verdict Raman would give (favourable, mixed or afflicted), then his reasons and his "
          "conclusion in his manner.")


def _load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def _dedup(fired):
    out = {}
    for fr in fired:
        src = fr.rule.source
        txt = " ".join((fr.text or "").split())
        if len(txt) > MAX_RULE_CHARS:
            txt = txt[:MAX_RULE_CHARS].rstrip() + "..."
        out.setdefault(fr.rule.id, f"[{src.work}:{src.line}] {txt}")
    return list(out.values())


def chart_facts(ch) -> str:
    from app.raman_saab.primitives.dignity import dignity
    lines = [f"Lagna: {SIGNS[ch.asc_sign - 1]}"]
    for name, p in ch.planets.items():
        bits = [f"{name}: {SIGNS[p.sign - 1]}, house {p.rasi_house}"]
        if name not in ("Rahu", "Ketu"):
            try:
                d = dignity(name, ch)
                if d:
                    bits.append(str(d))
            except Exception:   # sparse charts: dignity may be unreadable
                pass
        if getattr(p, "retrograde", False):
            bits.append("retrograde")
        if getattr(p, "combust_fraction", 0):
            bits.append("combust")
        if getattr(p, "navamsa_sign", None):
            bits.append(f"navamsa {SIGNS[p.navamsa_sign - 1]}")
        lines.append(", ".join(bits))
    return "\n".join(lines)


def prompt_for(ch, house, sig, sv, fx) -> str:
    pro = _dedup(sv.ledger.fired_benefic) if sv else []
    con = _dedup(sv.ledger.fired_malefic) if sv else []
    nb = len(sv.ledger.fired_benefic) if sv else 0
    nm = len(sv.ledger.fired_malefic) if sv else 0
    lean = "for" if nb > nm else "against" if nm > nb else ("even" if nb else "silent")
    parts = [f"MATTER: house {house}, {sig.replace('_', ' ')}"
             + (f" (karaka {sv.karaka})" if sv and sv.karaka else ""),
             "CHART:\n" + chart_facts(ch),
             f"RULES FOR ({len(pro)}):\n" + ("\n".join("+ " + x for x in pro[:MAX_RULES]) or "none"),
             f"RULES AGAINST ({len(con)}):\n" + ("\n".join("- " + x for x in con[:MAX_RULES]) or "none"),
             f"COUNT: {nb} for, {nm} against; lean {lean}",
             "FACTOR TALLY: " + ", ".join(f"{k} {v:+d}" for k, v in fx.items()) + f"; total {sum(fx.values()):+d}"]
    return "\n\n".join(parts)


def target_for(verdict, prose, reasons) -> str:
    out = [f"VERDICT: {verdict}"]
    if reasons:
        out.append("REASONS:\n" + "\n".join(
            f"{f['direction']} {f['detail']}" + (" (decisive)" if f.get("decisive") else "")
            for f in reasons))
    out.append("CONCLUSION: " + " ".join((prose or "").split()))
    return "\n".join(out)


def main():
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    from tools.raman_saab.tally_judge import factors

    coded = json.load(open("docs/raman_saab/reason_coding/raman_reasons_coded.json"))
    mkey = json.load(open("docs/raman_saab/reason_coding/matter_key.json"))
    by_key = {(v["chart"], v["house"], v["sig"]): coded.get(k) for k, v in mkey.items()}

    sources = [("pool", tg._TRACK_B_RATCHET, True)] + [(s, _load(p), False) for s, p in HOLDOUTS.items()]
    charts = sorted({r["id"] for _, recs, _ in sources for r in recs})
    rng = random.Random(SEED)
    order = charts[:]
    rng.shuffle(order)
    fold_of = {c: i % N_FOLDS for i, c in enumerate(order)}

    rows = []
    for split, recs, confirmed_only in sources:
        for r in recs:
            ch = tg.build_chart(r)
            pfs = {}
            for h, e in r["expected_verdicts"].items():
                if confirmed_only and not tg._is_confirmed(e):
                    continue
                hn = int(h[1:])
                pf = pfs.setdefault(hn, ht.judge_house(ch, hn))
                sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
                fx = factors(ch, hn, e["signification"], sv.karaka if sv else "")
                c = by_key.get((r["id"], hn, e["signification"])) if split == "pool" else None
                reasons = c["factors"] if c and c.get("found") else []
                rows.append({
                    "key": f"{r['id']} {h}/{e['signification']}", "chart": r["id"], "split": split,
                    "fold": fold_of[r["id"]], "gold": e["verdict"],
                    "nb": len(sv.ledger.fired_benefic) if sv else 0,
                    "nm": len(sv.ledger.fired_malefic) if sv else 0,
                    "engine_verdict": sv.verdict if sv else None,   # kept for baselines only, NOT in prompt
                    "system": SYSTEM,
                    "prompt": prompt_for(ch, hn, e["signification"], sv, fx),
                    "target": target_for(e["verdict"], e.get("verdict_prose"), reasons),
                    "raman_words": " ".join((e.get("verdict_prose") or "").split()),
                })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    by = {}
    for row in rows:
        by.setdefault(row["split"], 0)
        by[row["split"]] += 1
    print(len(rows), "rows", by, "charts", len(charts), "sha256", sha)


if __name__ == "__main__":
    main()
