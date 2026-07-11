"""P0 — build the LIVE ch. IV anchor corpus (htjah_anchor_live.json).

The frozen anchor (`htjah_anchor_calibration.json`) is hand-decoded typed findings in a
retired weight vocabulary, gated through the old audit harness — increment 15b showed the
LIVE engine drifted to 2/8 on these very charts without any guard noticing. This builder
produces the authoritative live-engine anchor: the three ch. IV example charts (Nos. 12-14)
cast from their printed birth data in Raman's ayanamsa, hard-gated for faithfulness against
the mechanical facts Raman states in his own walkthrough prose, with his eight graded
verdicts as the expected labels.

Chart 14's printed birth year "1878" is an OCR digit transposition: a constrained ephemeris
search over Raman's stated facts (Sun+Mercury+Saturn+Rahu in Cancer, Mars in Gemini, Scorpio
lagna vargottama, Mars navamsa Taurus, Sun ~18 deg from Saturn) identifies **7-8-1887**
uniquely (increment 16 in HOUSE_SCHEME_AUDIT.md). The corpus records both the printed and
repaired data.

Positions are stored POST-CAST in the Raman frame so the validator/test never needs the
ephemeris (the nh_strength_validate pattern: deterministic, byte-stable).

Run:  PYTHONPATH=. python3 docs/raman_doctrine/audit/builders/build_anchor_live_corpus.py
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.doctrine import raman_chart as rc

SIGN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
        "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_OUT = Path(__file__).resolve().parents[1] / "corpora" / "htjah_anchor_live.json"
_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# Each chart: printed birth data (OCR-cited), the mechanical facts Raman states in the
# ch. IV walkthrough (the faithfulness gate — placements only; interpretive navamsa-aspect
# remarks are notes, not gates), and his graded verdicts (the expected labels).
CHARTS = [
    {
        "chart": 12,
        "birth": {"y": 1918, "m": 10, "d": 16, "hh": 14, "mm": 20,
                  "tz": 5.5, "lat": 13.0, "lon": 77.5833},
        "birth_note": "Born on 16-10-1918 at 2-20 p.m. (I.S.T.) Lat. 13 N., Long. 5h.10m.20s. E.",
        "facts": [  # (kind, args, expected, prose)
            ("lagna_sign", (), "Capricorn", "Lagna is Makara or Capricorn"),
            ("rasi_sign", ("Saturn",), "Leo", "Lord of the Lagna Saturn is in the 8th in the sign of a bitter enemy"),
            ("house", ("Saturn",), 8, "Saturn is in the 8th"),
            ("nav_sign", ("Saturn",), "Taurus", "In the Navamsha ... Saturn is with Jupiter in the sign of Venus"),
            ("nav_sign", ("Jupiter",), "Taurus", "Saturn is with Jupiter in the sign of Venus"),
            ("vargottama", ("Sun",), True, "He [the Sun] occupies a vargottama position"),
            ("rasi_sign", ("Sun",), "Libra", "in a sign owned by an enemy"),
        ],
        "verdicts": [
            {"factor": "bhava", "raman": "moderate",
             "quote": "Thus the ascendant is moderate in strength."},
            {"factor": "lord", "raman": "fairly good",
             "quote": "Hence the strength of the ascendant lord is also fairly good."},
            {"factor": "karaka", "raman": "moderately good",
             "quote": "The Karaka is therefore inclining towards good."},
        ],
    },
    {
        "chart": 13,
        "birth": {"y": 1935, "m": 11, "d": 2, "hh": 5, "mm": 20,
                  "tz": 77.5833 / 15.0, "lat": 13.0, "lon": 77.5833},
        "birth_note": "Born on 2-11-1935 at 5-20 a.m (L.M.T.) Lat. 13 N., Long. 5h.10m.20s. E.",
        "facts": [
            ("lagna_sign", (), "Libra", "Lagna is Thula"),
            ("rasi_sign", ("Sun",), "Libra", "The Sun, lord of 11, is in Lagna in neecha"),
            ("house", ("Sun",), 1, "is in Lagna"),
            ("rasi_sign", ("Venus",), "Virgo", "Lord of Lagna Venus is in the 12th in debilitation"),
            ("house", ("Venus",), 12, "Venus is in the 12th"),
            ("rasi_sign", ("Mercury",), "Virgo", "Venus is with exalted Mercury"),
            ("nav_sign", ("Venus",), "Capricorn", "In the Navamsha, Venus is in a friendly sign, with Saturn"),
            ("nav_sign", ("Saturn",), "Capricorn", "with Saturn a malefic"),
            # nav lagna hemmed between Saturn and Rahu (Papakarthari): occupants of the
            # adjacent navamsa signs
            ("nav_lagna_sign", (), "Sagittarius",
             "in the Navamsha ... Lagna is hemmed in between Saturn and Rahu"),
            ("nav_sign", ("Rahu",), "Scorpio", "hemmed in between Saturn and Rahu"),
        ],
        "verdicts": [
            {"factor": "bhava", "raman": "fairly strong",
             "quote": "The Lagna therefore is fairly strong on the whole."},
            {"factor": "lord", "raman": "fairly powerful",
             "quote": "Therefore the ascendant lord is also fairly powerful."},
            {"factor": "karaka", "raman": "fairly powerful",
             "quote": "The Sun is therefore fairly powerful."},
        ],
    },
    {
        "chart": 14,
        # Printed: "7-8-1878 at 1-30 p.m. (L.T.)" -- 1878 is an OCR digit transposition.
        # Constrained search over Raman's stated facts uniquely selects 7-8-1887 (see
        # module docstring); no date in 1878 puts Saturn+Rahu in Cancer.
        "birth": {"y": 1887, "m": 8, "d": 7, "hh": 13, "mm": 30,
                  "tz": 77.0333 / 15.0, "lat": 11.0, "lon": 77.0333},
        "birth_note": ("Printed: Born on 7-8-1878 at 1-30 p.m. (L.T.) Lat. 11 N., Long. "
                       "5h.8m.8s. E. — repaired to 7-8-1887 (OCR transposition; see docstring)"),
        "facts": [
            ("lagna_sign", (), "Scorpio", "Lagna is the same both in Rashi and Navamsha (Vargottamamsa)"),
            ("nav_lagna_sign", (), "Scorpio", "it goes under the name of Vargottamamsa"),
            ("rasi_sign", ("Mars",), "Gemini", "Mars is lord of Lagna and he is in the 9th house (8th Rashi)"),
            ("nav_sign", ("Mars",), "Taurus", "In the Navamsha, Mars is in Taurus"),
            ("rasi_sign", ("Sun",), "Cancer", "The Sun is in the 9th with Mercury, Saturn and Rahu"),
            ("rasi_sign", ("Mercury",), "Cancer", "with Mercury, Saturn and Rahu"),
            ("rasi_sign", ("Saturn",), "Cancer", "with Mercury, Saturn and Rahu"),
            ("rasi_sign", ("Rahu",), "Cancer", "with Mercury, Saturn and Rahu"),
        ],
        "notes": [
            "Raman counts Mars 'in the 9th house (8th Rashi)' -- bhava counting; the engine's "
            "whole-sign map reads Gemini as the 8th from Scorpio. Recorded confound.",
            "Sun-Saturn separation casts to 15.9 deg vs prose 'about 18 degrees' (tolerant).",
            "Two navamsa-ASPECT prose remarks (Mars aspected by Saturn; Sun aspected by the "
            "Moon in amsa) do not match whole-sign from-navamsa aspects; interpretive, not "
            "placement facts -- not gated.",
        ],
        "verdicts": [
            {"factor": "lord", "raman": "very strong",
             "quote": "Excepting for this feeble evil, Lagnadhipati is indeed very strong."},
            {"factor": "karaka", "raman": "moderate",
             "quote": "The Sun therefore is moderate in strength."},
            # structural: vargottama-lagna override, always "very powerful" by decode
            {"factor": "bhava", "raman": "very powerful", "structural": True,
             "quote": "Hence the Lagna is very powerful."},
        ],
    },
]


def _cast(b: dict):
    ac = calculate_all_charts(b["y"], b["m"], b["d"], b["hh"], b["mm"],
                              b["tz"], b["lat"], b["lon"])
    lons = {g: ac["d1"][g]["longitude"] for g in ac["d1"]}
    sl, sg = rc.lahiri_to_raman(lons, ac["ascendant"]["longitude"], ac["jd"])
    chart = rc.from_positions(sl, sg, birth_jd=ac["jd"], ayanamsa="raman",
                              degree_resolved=True)
    return chart, sl, sg, ac["jd"]


def _check(chart, sl, sg, facts) -> list[str]:
    errs = []
    signs = chart.bundle.chart.planet_signs
    for kind, args, want, prose in facts:
        if kind == "lagna_sign":
            got = SIGN[chart.bundle.kundali.lagna_sign - 1]
        elif kind == "nav_lagna_sign":
            got = SIGN[chart.bundle.navamsa_lagna - 1]
        elif kind == "rasi_sign":
            got = SIGN[signs[args[0]] - 1]
        elif kind == "nav_sign":
            got = SIGN[chart.varga_signs[args[0]][9] - 1]
        elif kind == "house":
            got = chart.bundle.kundali.planet_house[args[0]]
        elif kind == "vargottama":
            got = signs[args[0]] == chart.varga_signs[args[0]][9]
        else:
            raise ValueError(kind)
        if got != want:
            errs.append(f"  {kind}{args}: cast={got!r} vs Raman={want!r}  [{prose}]")
    return errs


def main() -> None:
    out = {"house": 1,
           "note": ("LIVE ch. IV anchor: Charts 12-14 cast from printed birth data in "
                    "Raman's ayanamsa, faithfulness-gated against his walkthrough prose. "
                    "The authoritative anchor for the live engine (the frozen "
                    "htjah_anchor_calibration.json gates only the old audit harness)."),
           "charts": []}
    for spec in CHARTS:
        chart, sl, sg, jd = _cast(spec["birth"])
        errs = _check(chart, sl, sg, spec["facts"])
        if errs:
            raise SystemExit(f"Chart {spec['chart']} FAILED faithfulness gate:\n"
                             + "\n".join(errs))
        out["charts"].append({
            "chart": spec["chart"], "birth": spec["birth"],
            "birth_note": spec["birth_note"],
            "birth_jd": round(jd, 6), "ayanamsa": "raman", "degree_resolved": True,
            "planet_lons": {g: round(sl[g], 4) for g in _GRAHAS if g in sl},
            "lagna_lon": round(sg, 4),
            "expected_rasi_signs": {g: chart.bundle.chart.planet_signs[g] for g in _GRAHAS},
            "expected_navamsa_signs": {g: chart.varga_signs[g][9] for g in _GRAHAS},
            "facts_gated": [{"kind": k, "args": list(a), "want": w, "prose": p}
                            for k, a, w, p in spec["facts"]],
            "notes": spec.get("notes", []),
            "verdicts": spec["verdicts"],
        })
        print(f"Chart {spec['chart']}: faithfulness gate PASSED "
              f"({len(spec['facts'])} prose facts)")
    _OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {_OUT} ({sum(len(c['verdicts']) for c in out['charts'])} verdict rows)")


if __name__ == "__main__":
    main()
