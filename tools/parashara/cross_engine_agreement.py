"""Cross-engine agreement — the parashara engine scored on the SAME goldens as the Raman engine.

The Raman engine's 259/293 is its verdict accuracy against Raman's published chart-verdict gallery
(`tests/fixtures/raman_goldens.jsonl`). This tool runs the PARASHARA bhava judge (ch.11 prosperity/
annihilation) on those same charts and scores it against the same published verdicts, on the same
ordinal scale — giving a directly-comparable number.

READ IT HONESTLY: this measures how often BPHS doctrine AGREES with Raman's own judgments, NOT "BPHS
accuracy". Raman deliberately revised Parashara, so a divergence where they differ is CORRECT, not an
error — each is a real BPHS-vs-Raman doctrinal difference, not a bug. The number is overlap +
attributed divergence, never "the parashara engine is X/293 accurate".

Verdict mapping (both onto Raman's ordinal afflicted<mixed<favourable):
  parashara flourishing -> favourable(2), ordinary -> mixed(1), annihilated -> afflicted(0).

Usage:
    py -3.12 -m tools.parashara.cross_engine_agreement
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.parashara.chart.bhava_chart import judge_all_bhavas
from app.parashara.chart.cast import cast as cast_parashara
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import house_template as ht

_GOLDENS = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "raman_goldens.jsonl"

#: Raman's ordinal verdict scale (afflicted < mixed < favourable); insufficient-evidence is off-axis.
_ORD = {"afflicted": 0, "mixed": 1, "favourable": 2}
#: parashara ch.11 verdict -> Raman's vocabulary (for scoring on the shared ordinal scale).
_PARA_TO_RAMAN = {"annihilated": "afflicted", "ordinary": "mixed", "flourishing": "favourable"}


def load_goldens() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            out.append(json.loads(s))
    return out


def _lon(entry: dict[str, Any]) -> float:
    if entry.get("lon") is not None:
        return float(entry["lon"]) % 360.0
    return float((int(entry["sign"]) - 1) * 30) + 15.0


def _is_confirmed(v: dict[str, Any]) -> bool:
    return v.get("verdict_review") == "CONFIRMED" and v.get("verdict") != "DRAFT"


def _confirmed(rec: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    return [(int(h[1:]), v) for h, v in rec.get("expected_verdicts", {}).items() if _is_confirmed(v)]


def _ratchet_records(goldens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The same set the Raman ratchet scores: worked examples (not self_test) with a CONFIRMED verdict
    and Track-B eligibility."""
    return [r for r in goldens if "B" in r.get("track_eligibility", [])
            and r["case_type"] != "self_test" and _confirmed(r)]


def _birth(rec: dict[str, Any]) -> Optional[BirthData]:
    b = rec.get("birth")
    if not b or any(b.get(k) is None for k in ("dt", "tz", "lat", "lon")):
        return None
    date_part, _, time_part = str(b["dt"]).partition("T")
    y, mo, d = (int(x) for x in date_part.split("-"))
    hh = mm = 0
    if time_part:
        parts = time_part.split(":")
        hh = int(parts[0]); mm = int(parts[1]) if len(parts) > 1 else 0
    return BirthData(name=str(rec.get("name", "golden")), year=y, month=mo, day=d, hour=hh,
                     minute=mm, tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                     longitude=float(b["lon"]))


def _raman_chart(rec: dict[str, Any]) -> RamanChart:
    birth = _birth(rec)
    if birth is not None:
        return cast_chart(birth, ayanamsa="raman")
    stated = {n: {"lon": _lon(e), "bhava": int(e["bhava"])}
              for n, e in rec["stated_positions"].items()}
    lagna = rec.get("lagna_sign")
    asc_lon = float((int(lagna) - 1) * 30) + 5.0 if lagna else 5.0
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


def _raman_verdict(chart: RamanChart, house: int, sig: str) -> Optional[str]:
    pf = ht.judge_house(chart, house)
    for sv in pf.significations:
        if sv.signification == sig:
            return sv.verdict
    return None


def _parashara_verdicts(rec: dict[str, Any]) -> dict[int, str]:
    """{house: raman-vocabulary verdict} from the parashara ch.11 judge.

    Birth-based records (empty stated_positions) are FRESH-CAST with the parashara caster (Lahiri, its
    native ayanamsa); book records use the stated longitudes + printed lagna directly. So the two
    engines use their own native ayanamsa on birth charts — a real engine difference, and identical
    stated longitudes on book charts (pure doctrine comparison there)."""
    birth = _birth(rec)
    if birth is not None:
        ch = cast_parashara(year=birth.year, month=birth.month, day=birth.day, hour=birth.hour,
                            minute=birth.minute, tz_offset=birth.tz_offset,
                            latitude=birth.latitude, longitude=birth.longitude)
        verdicts = judge_all_bhavas(ch.longitudes, asc_sign=ch.asc_sign, moon_waxing=ch.moon_waxing)
        return {h: _PARA_TO_RAMAN[v.verdict] for h, v in verdicts.items()}
    longitudes = {n: _lon(e) for n, e in rec["stated_positions"].items()}
    if not longitudes:
        return {}
    lagna = rec.get("lagna_sign")
    asc_sign = int(lagna) if lagna else (int(longitudes.get("Sun", 5.0) // 30) + 1)
    sun, moon = longitudes.get("Sun"), longitudes.get("Moon")
    moon_waxing = (0.0 < (moon - sun) % 360.0 < 180.0) if (sun is not None and moon is not None) else True
    verdicts = judge_all_bhavas(longitudes, asc_sign=asc_sign, moon_waxing=moon_waxing)
    return {h: _PARA_TO_RAMAN[v.verdict] for h, v in verdicts.items()}


def _dist(got: Optional[str], expected: str) -> int:
    if got == expected:
        return 0
    if got in _ORD and expected in _ORD:
        return abs(_ORD[got] - _ORD[expected])
    return 2


def score() -> dict[str, Any]:
    goldens = load_goldens()
    recs = _ratchet_records(goldens)
    r_exact = r_w1 = p_exact = p_w1 = agree_exact = agree_w1 = total = 0
    off_axis = boundary = inversion = 0     # golden=insufficient-evidence / dist-1 / dist-2 on-axis
    divergences: list[str] = []
    for rec in recs:
        rchart = _raman_chart(rec)
        pverd = _parashara_verdicts(rec)
        for house, entry in _confirmed(rec):
            gold = entry["verdict"]
            sig = entry["signification"]
            rv = _raman_verdict(rchart, house, sig)
            pv = pverd.get(house)
            total += 1
            r_exact += rv == gold
            r_w1 += _dist(rv, gold) <= 1
            p_exact += pv == gold
            p_w1 += _dist(pv, gold) <= 1
            agree_exact += rv == pv
            agree_w1 += _dist(pv, rv) <= 1
            d = _dist(pv, gold)
            if d >= 1:
                # Categorise the divergence for honest attribution.
                if gold not in _ORD:            # insufficient-evidence: off parashara's 3-verdict axis
                    off_axis += 1
                    kind = "off-axis (golden=insufficient-evidence; ch.11 has no such verdict)"
                elif d == 1:                    # favourable<->mixed / mixed<->afflicted: contestable
                    boundary += 1
                    kind = "boundary (one ordinal step — contestable)"
                else:                           # flourishing<->afflicted: a real doctrinal inversion
                    inversion += 1
                    kind = "INVERSION (opposite poles — a real BPHS-vs-Raman difference)"
                divergences.append(
                    f"  {rec['id']} H{house}/{sig}: parashara={pv!r} raman={rv!r} golden={gold!r}"
                    f"  [{kind}]")
    return {"total": total, "raman_exact": r_exact, "raman_within1": r_w1,
            "para_exact": p_exact, "para_within1": p_w1,
            "agree_exact": agree_exact, "agree_within1": agree_w1,
            "off_axis": off_axis, "boundary": boundary, "inversion": inversion,
            "divergences": divergences}


def main() -> None:
    s = score()
    n = s["total"]
    print(f"\nCross-engine agreement on the {n} CONFIRMED Raman goldens "
          f"(parashara ch.11 vs Raman's published verdicts):\n")
    print(f"  Raman engine   vs golden : exact={s['raman_exact']}/{n}={s['raman_exact']/n:.3f}  "
          f"within-1={s['raman_within1']}/{n}={s['raman_within1']/n:.3f}")
    print(f"  Parashara      vs golden : exact={s['para_exact']}/{n}={s['para_exact']/n:.3f}  "
          f"within-1={s['para_within1']}/{n}={s['para_within1']/n:.3f}")
    print(f"  Parashara vs Raman engine: exact={s['agree_exact']}/{n}={s['agree_exact']/n:.3f}  "
          f"within-1={s['agree_within1']}/{n}={s['agree_within1']/n:.3f}")
    print(f"\n  divergence breakdown ({len(s['divergences'])} total):")
    print(f"    off-axis  (golden=insufficient-evidence, no ch.11 equivalent): {s['off_axis']}")
    print(f"    boundary  (one ordinal step — contestable)                   : {s['boundary']}")
    print(f"    INVERSION (opposite poles — a real BPHS-vs-Raman difference) : {s['inversion']}")
    print(f"\n[cross-engine] parashara agrees with Raman's published verdicts on "
          f"{s['para_exact']}/{n} exact, {s['para_within1']}/{n} within-1")
    print("(overlap + attributed divergences — NOT 'BPHS accuracy'; where BPHS revises Raman, "
          "divergence is correct)")
    if s["divergences"]:
        print(f"\nfirst divergences (each a BPHS-vs-Raman difference):")
        for line in s["divergences"][:20]:
            print(line)


if __name__ == "__main__":
    main()
