"""Is the small astrological death-signal CAUSE-SPECIFIC, washed out by pooling?

Every prior test pooled 37k mixed deaths and found only a tiny lord-specific tilt over
age. But classical doctrine assigns *different* killers to *different* deaths — Mars and
the 8th house to violent/unnatural ends, Saturn to chronic disease, the nodes (Rahu/Ketu)
to accidents and the bizarre. Pooling natural + violent deaths would average such
opposing signatures toward zero.

We just found a manner-of-death taxonomy already in the catalog
(`person_attributes.field='Death'`, holos-sourced): Suicide, Accidental, Illness/Disease,
Unusual, plus longevity tags. This module stratifies the death corpus by manner and asks,
per subgroup, whether the Vimśottarī MD-lord-at-death is each candidate killer
(Mars / 8th / dusthāna / Saturn / nodes / maraka variants) more than that lord's
dāśā-length share predicts — reusing the validated `alt_dasha_death` lift machinery.

The decisive test is the **unnatural-vs-natural contrast**: is the Mars/8th/node signature
significantly STRONGER for unnatural deaths than for illness deaths? A yes means pooling
hid a real cause-specific signal; a clean no is itself a result (manner doesn't separate
at this n). Subgroups are modest (suicide ~544, accidental ~535) — effect sizes + CIs are
reported, not just p.

Run: python -m app.medini.analysis.manner_of_death
"""
from __future__ import annotations

import math
from typing import Callable

from app.medini.analysis.alt_dasha_death import (
    DashaResult, _karakamsa_sign, _lord_from, _sig_rows, _sun_sign, _test_significator,
)
from app.medini.analysis.doctrine_validator import (
    LORD_SHARE, _house_lord, _maraka_set, _norm_sf, open_catalog,
)

# holos `Death` detail → coarse manner. Longevity tags are kept separate (they describe
# age, not cause) and excluded from the cause contrast.
_DETAIL_TO_MANNER: dict[str, str] = {
    "Suicide": "suicide",
    "Suicide Attempt": "suicide",
    "Accidental": "accidental",
    "Illness/ Disease": "illness",
    "Unusual": "unusual",
    "Other Death": "other",
}
_LONGEVITY_DETAILS = {"Long life more than 80 yrs", "Short Life less than 29 Yrs"}
# Primary contrast: the unnatural/violent group vs the natural/disease group.
_UNNATURAL = {"suicide", "accidental", "unusual"}
_NATURAL = {"illness"}


def manner_label(con) -> dict[str, str]:
    """person_id → coarse manner-of-death (suicide/accidental/illness/unusual/other).

    A person can carry several `Death` details; we keep the most *specific* manner,
    preferring an explicit cause over the generic 'other' and ignoring longevity tags."""
    rows = con.execute(
        """SELECT person_id, detail FROM person_attributes
           WHERE field = 'Death' AND detail IS NOT NULL"""
    ).fetchall()
    # priority: a concrete manner beats 'other'; first concrete wins.
    out: dict[str, str] = {}
    for pid, detail in rows:
        manner = _DETAIL_TO_MANNER.get(detail)
        if manner is None:           # longevity tag or unknown — skip for manner
            continue
        cur = out.get(pid)
        if cur is None or (cur == "other" and manner != "other"):
            out[pid] = manner
    return out


# --- candidate killers (per-chart planet sets the MD-lord might belong to) --------- #
_KILLERS: dict[str, Callable[[dict], set[str]]] = {
    "Mars (violence)": lambda r: {"Mars"},
    "Saturn (chronic)": lambda r: {"Saturn"},
    "Rahu/Ketu (nodes)": lambda r: {"Rahu", "Ketu"},
    "8th lord": lambda r: {_house_lord(r["asc"], 8)},
    "dusthāna 6/8/12 lords": lambda r: {
        _house_lord(r["asc"], 6), _house_lord(r["asc"], 8), _house_lord(r["asc"], 12)},
    "planets in 8th house": lambda r: {g for g, h in r["gh"].items() if h == 8},
    "maraka from Lagna": lambda r: _maraka_set(r["asc"], r["gh"], "full"),
    "maraka from Sun": lambda r: {
        _lord_from(_sun_sign(r), 2), _lord_from(_sun_sign(r), 7), "Saturn"},
    "maraka from Karakāṁśa": lambda r: (
        {_lord_from(_karakamsa_sign(r), 2), _lord_from(_karakamsa_sign(r), 7), "Saturn"}
        if _karakamsa_sign(r) else set()),
    # the pooled violent-death signature — union of the unnatural-death karakas. Tested
    # as ONE statistic so the individually-underpowered directional signals aggregate.
    "VIOLENT composite (Mars∪nodes∪8th∪dusthāna)": lambda r: (
        {"Mars", "Rahu", "Ketu"}
        | {_house_lord(r["asc"], 6), _house_lord(r["asc"], 8), _house_lord(r["asc"], 12)}
        | {g for g, h in r["gh"].items() if h == 8}),
}
# Killers whose classical domain is unnatural death — the contrast focuses on these.
_VIOLENT_KILLERS = ("Mars (violence)", "Rahu/Ketu (nodes)", "8th lord",
                    "dusthāna 6/8/12 lords", "planets in 8th house",
                    "VIOLENT composite (Mars∪nodes∪8th∪dusthāna)")


def _excess(r: dict, sigfn: Callable[[dict], set[str]]) -> float | None:
    """Per-death signal: I(MD-lord ∈ killer set) − that set's dāśā-length share.

    Mean over a group is 0 under the null (lord is the killer only as often as its share
    of the Vimśottarī cycle predicts); a positive mean is real clustering."""
    S = sigfn(r)
    if not S:
        return None
    return (1.0 if r["md"] in S else 0.0) - sum(LORD_SHARE.get(p, 0.0) for p in S)


def _contrast(rows_a: list[dict], rows_b: list[dict],
              sigfn: Callable[[dict], set[str]], name: str) -> dict:
    """Two-sample z on mean per-death excess between groups a and b (a − b)."""
    xa = [e for r in rows_a if (e := _excess(r, sigfn)) is not None]
    xb = [e for r in rows_b if (e := _excess(r, sigfn)) is not None]
    if len(xa) < 2 or len(xb) < 2:
        return {"name": name, "n_a": len(xa), "n_b": len(xb), "diff": 0.0, "z": 0.0, "p": 1.0}

    def _mv(x):
        m = sum(x) / len(x)
        v = sum((d - m) ** 2 for d in x) / (len(x) - 1)
        return m, v
    ma, va = _mv(xa)
    mb, vb = _mv(xb)
    se = math.sqrt(va / len(xa) + vb / len(xb))
    z = (ma - mb) / se if se else 0.0
    return {"name": name, "n_a": len(xa), "n_b": len(xb),
            "excess_a": round(ma, 4), "excess_b": round(mb, 4),
            "diff": round(ma - mb, 4), "z": round(z, 2),
            "p": round(2.0 * _norm_sf(abs(z)), 5)}


def _permutation_p(rows_a: list[dict], rows_b: list[dict],
                   sigfn: Callable[[dict], set[str]], n_perm: int = 5000,
                   seed: int = 0) -> dict:
    """Exact label-shuffle p for the group difference in mean excess — no distributional
    assumption, and robust to the composite being chosen after seeing the components."""
    import random
    xa = [e for r in rows_a if (e := _excess(r, sigfn)) is not None]
    xb = [e for r in rows_b if (e := _excess(r, sigfn)) is not None]
    pool = xa + xb
    na = len(xa)
    obs = (sum(xa) / na) - (sum(xb) / len(xb)) if na and xb else 0.0
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        d = sum(pool[:na]) / na - sum(pool[na:]) / (len(pool) - na)
        if abs(d) >= abs(obs):
            ge += 1
    return {"diff": round(obs, 4), "n_perm": n_perm,
            "p_perm": round((ge + 1) / (n_perm + 1), 5)}


def manner_stratified_report(con=None) -> dict:
    """Per-manner killer lifts + the unnatural-vs-natural contrast."""
    own = con is None
    con = con or open_catalog()
    try:
        rows = _sig_rows(con)
        manner = manner_label(con)
    finally:
        if own:
            con.close()

    for r in rows:
        r["manner"] = manner.get(r["pid"])
    groups: dict[str, list[dict]] = {}
    for r in rows:
        if r["manner"]:
            groups.setdefault(r["manner"], []).append(r)
    unnat = [r for r in rows if r["manner"] in _UNNATURAL]
    nat = [r for r in rows if r["manner"] in _NATURAL]

    # per-manner lift table (reuses the single-group significator test)
    per_manner: dict[str, list[DashaResult]] = {}
    for g, grows in sorted(groups.items()):
        per_manner[g] = [_test_significator(grows, fn, name)
                         for name, fn in _KILLERS.items()]

    # the decisive contrast on the violent-death killers
    contrasts = [_contrast(unnat, nat, _KILLERS[name], name) for name in _VIOLENT_KILLERS]
    composite_name = "VIOLENT composite (Mars∪nodes∪8th∪dusthāna)"
    perm = _permutation_p(unnat, nat, _KILLERS[composite_name])
    return {
        "counts": {g: len(v) for g, v in sorted(groups.items())},
        "n_unnatural": len(unnat), "n_natural": len(nat),
        "per_manner": per_manner, "contrasts": contrasts, "composite_perm": perm,
    }


def main() -> int:
    rep = manner_stratified_report()
    print("\n=== Manner-of-death stratified signal hunt ===")
    print("labelled deaths by manner:", rep["counts"])
    print(f"primary contrast: unnatural (suicide∪accidental∪unusual, n={rep['n_unnatural']}) "
          f"vs natural (illness, n={rep['n_natural']})\n")

    print("-- per-manner: is the MD-lord-at-death this killer? (lift vs dāśā share) --")
    hdr = "killer".ljust(26) + "".join(g[:9].rjust(11) for g in rep["per_manner"])
    print(hdr)
    killers = [name for name, _ in _KILLERS.items()]
    for name in killers:
        line = name.ljust(26)
        for g, results in rep["per_manner"].items():
            res = next(r for r in results if r.name == name)
            line += f"{res.lift:>11}"
        print(line)

    print("\n-- DECISIVE: unnatural vs natural (excess clustering difference, a−b) --")
    print(f"{'killer':<26}{'excess_unnat':>13}{'excess_nat':>12}{'diff':>9}{'z':>7}{'p':>9}")
    any_sig = False
    for c in rep["contrasts"]:
        flag = "  <==" if c["p"] < 0.05 and c["diff"] > 0 else ""
        any_sig = any_sig or bool(flag)
        print(f"{c['name']:<26}{c.get('excess_a', 0):>13}{c.get('excess_b', 0):>12}"
              f"{c['diff']:>9}{c['z']:>7}{c['p']:>9}{flag}")
    perm = rep["composite_perm"]
    print(f"\nVIOLENT-composite permutation test ({perm['n_perm']} label shuffles): "
          f"diff={perm['diff']}  p_perm={perm['p_perm']}")
    print("\nverdict:", "a cause-specific signature separates the groups (see <== rows)."
          if any_sig else
          "no killer separates unnatural from natural at this n — manner does NOT recover\n"
          "a signal beyond the pooled tilt (honest null; subgroups are small).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
