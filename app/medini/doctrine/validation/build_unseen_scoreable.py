"""Assemble the Tier-2 fresh-strength corpus (`unseen_scoreable.json`) from the
vision-extracted sign grids + Raman's verbatim per-factor verdicts.

Every chart here is GENUINELY UNSEEN (de-duped by (vol, chart_no) against every tuned/
held-out corpus, see catalog_unseen) and was hand-verified against Raman's own prose
(the relative placements he states -- e.g. "the 4th is Cancer", "the 8th lord Sun is in
a kendra with ...") before inclusion. Grids that could not be reconciled with the prose
(ch65) or whose verdict could not be attributed unambiguously (ch91, a floated-diagram
offset) were DROPPED, not guessed. Charts whose Navamsa failed the reachability gate but
whose Rasi is prose-verified (ch35) are scored Rasi-axis-only.

The verdict phrases are Raman's verbatim words; grading is the pre-registered map. The
records feed the standard `worked_chart_validate.run` -- no engine change, measurement only.
"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_OUT = _ROOT / "docs/raman_doctrine/validation/corpora/unseen_scoreable.json"

# Vision-extracted sign grids, each hand-verified against Raman's own prose placements
# (see the per-chart cross-checks in REPORT_unseen_corpus.md). Embedded here so the corpus
# is reproducible without the (ephemeral) render artifacts. ch80 is Rasi-only (Navamsa not
# re-read); ch35's Navamsa failed the reachability gate so it is scored Rasi-axis-only.
_GRID = {
    68: {"lagna_rasi": "Libra", "lagna_navamsa": "Gemini", "rasi": {"Sun": "Virgo", "Moon": "Sagittarius", "Mars": "Gemini", "Mercury": "Virgo", "Jupiter": "Leo", "Venus": "Libra", "Saturn": "Libra", "Rahu": "Aquarius", "Ketu": "Leo"}, "navamsa": {"Sun": "Virgo", "Moon": "Libra", "Mars": "Scorpio", "Mercury": "Cancer", "Jupiter": "Cancer", "Venus": "Taurus", "Saturn": "Gemini", "Rahu": "Libra", "Ketu": "Aries"}},
    87: {"lagna_rasi": "Libra", "lagna_navamsa": "Capricorn", "rasi": {"Sun": "Leo", "Moon": "Capricorn", "Mars": "Pisces", "Mercury": "Virgo", "Jupiter": "Leo", "Venus": "Virgo", "Saturn": "Aries", "Rahu": "Taurus", "Ketu": "Scorpio"}, "navamsa": {"Sun": "Virgo", "Moon": "Capricorn", "Mars": "Scorpio", "Mercury": "Capricorn", "Jupiter": "Sagittarius", "Venus": "Taurus", "Saturn": "Aries", "Rahu": "Cancer", "Ketu": "Capricorn"}},
    52: {"lagna_rasi": "Capricorn", "lagna_navamsa": "Cancer", "rasi": {"Sun": "Libra", "Moon": "Taurus", "Mars": "Libra", "Mercury": "Libra", "Jupiter": "Aquarius", "Venus": "Libra", "Saturn": "Scorpio", "Rahu": "Leo", "Ketu": "Aquarius"}, "navamsa": {"Sun": "Libra", "Moon": "Leo", "Mars": "Taurus", "Mercury": "Aries", "Jupiter": "Sagittarius", "Venus": "Sagittarius", "Saturn": "Cancer", "Rahu": "Libra", "Ketu": "Aries"}},
    93: {"lagna_rasi": "Sagittarius", "lagna_navamsa": "Libra", "rasi": {"Sun": "Aries", "Moon": "Virgo", "Mars": "Virgo", "Mercury": "Aries", "Jupiter": "Aquarius", "Venus": "Cancer", "Saturn": "Capricorn", "Rahu": "Virgo", "Ketu": "Pisces"}, "navamsa": {"Sun": "Cancer", "Moon": "Aquarius", "Mars": "Pisces", "Mercury": "Cancer", "Jupiter": "Gemini", "Venus": "Scorpio", "Saturn": "Gemini", "Rahu": "Cancer", "Ketu": "Capricorn"}},
    92: {"lagna_rasi": "Aquarius", "lagna_navamsa": "Capricorn", "rasi": {"Sun": "Virgo", "Moon": "Taurus", "Mars": "Virgo", "Mercury": "Virgo", "Jupiter": "Scorpio", "Venus": "Libra", "Saturn": "Taurus", "Rahu": "Pisces", "Ketu": "Virgo"}, "navamsa": {"Sun": "Taurus", "Moon": "Capricorn", "Mars": "Virgo", "Mercury": "Aries", "Jupiter": "Sagittarius", "Venus": "Sagittarius", "Saturn": "Aries", "Rahu": "Capricorn", "Ketu": "Cancer"}},
    80: {"lagna_rasi": "Capricorn", "rasi": {"Sun": "Leo", "Moon": "Scorpio", "Mars": "Scorpio", "Mercury": "Virgo", "Jupiter": "Pisces", "Venus": "Virgo", "Saturn": "Gemini", "Rahu": "Pisces", "Ketu": "Virgo"}},
    35: {"lagna_rasi": "Sagittarius", "rasi": {"Sun": "Capricorn", "Moon": "Cancer", "Mars": "Sagittarius", "Mercury": "Aquarius", "Jupiter": "Cancer", "Venus": "Sagittarius", "Saturn": "Scorpio", "Rahu": "Aquarius", "Ketu": "Leo"}},
}

# per-chart: house judged, axis, and Raman's verbatim per-factor verdicts (+ karaka planet
# when he judges a named significator rather than the house's default karaka).
_META = {
    68: {"house": 4, "axis": "full", "verdicts": [
        {"factor": "lord", "phrase": "The fourth lord is moderately strong"},
        {"factor": "karaka", "phrase": "Matrukaraka is feebly strong", "karaka": "Moon"},
        {"factor": "bhava", "phrase": "The fourth house is considerably afflicted"}]},
    87: {"house": 4, "axis": "full", "verdicts": [
        {"factor": "lord", "phrase": "The fourth lord is considerably afflicted"},
        {"factor": "karaka", "phrase": "Grihakaraka is weak", "karaka": "Mars"}]},
    52: {"house": 8, "axis": "full", "verdicts": [
        {"factor": "lord", "phrase": "the 8th lord is fairly strong"},
        {"factor": "bhava", "phrase": "The 8th house is afflicted by Rahu"}]},
    93: {"house": 5, "axis": "full", "verdicts": [
        {"factor": "lord", "phrase": "Mars the 5th lord is considerably afflicted"}]},
    92: {"house": 5, "axis": "full", "verdicts": [
        {"factor": "bhava", "phrase": "The 5th house is unafflicted"},
        {"factor": "lord", "phrase": "Mercury the lord is considerably afflicted"},
        {"factor": "karaka", "phrase": "the karaka is moderately blemished", "karaka": "Jupiter"}]},
    80: {"house": 4, "axis": "rasi", "verdicts": [
        {"factor": "bhava", "phrase": "The fourth house is unafflicted"},
        {"factor": "karaka", "phrase": "Vidyakaraka is considerably afflicted", "karaka": "Jupiter"}]},
    35: {"house": 8, "axis": "rasi", "verdicts": [
        {"factor": "lord", "phrase": "the 8th lord is full and very powerful"}]},
}

_BIRTH = {68: "Born on 13-10-1896 at 7-56 a.m.", 87: "Born on 28-8-1909 at 9-52 a.m.",
          52: "Born 17-10-1867 at 2-30 p.m.", 93: "Born on 3-6-1903 at 4-45 p.m.",
          92: "Born on 30-9-1912 at 5-15 p.m.", 80: "Born on 7-9-1856 at 4 p.m.",
          35: "Born 30/31-1-1896 at 4-30 a.m."}


# which HTJAH volume each chart lives in (for provenance; house<=6 -> Vol I else Vol II).
_VOL = {68: "htjah_vol1", 87: "htjah_vol1", 80: "htjah_vol1", 92: "htjah_vol1",
        93: "htjah_vol1", 52: "htjah_vol2", 35: "htjah_vol2"}


def build() -> dict:
    charts = []
    for cn, meta in _META.items():
        g = _GRID[cn]
        rec = {"chart_no": cn, "vol": _VOL[cn], "birth_line": _BIRTH[cn],
               "house_judged": meta["house"], "verdicts": meta["verdicts"],
               "rasi": g["rasi"], "lagna_rasi": g["lagna_rasi"]}
        if meta["axis"] == "rasi":
            rec["axis"] = "rasi"
        else:
            rec.update({"navamsa": g["navamsa"], "lagna_navamsa": g["lagna_navamsa"]})
        charts.append(rec)
    return {
        "source": "HTJAH Vol I & II -- FRESH (engine-unseen) worked charts, Tier-2. Sign grids "
                  "vision-extracted and hand-verified against Raman's own prose placements; "
                  "verdicts are his verbatim phrases. ch35 is Rasi-axis-only (Navamsa failed the "
                  "reachability gate). Charts 65/91 were dropped (unreconcilable grid / ambiguous "
                  "verdict). Measurement-only; the engine was never tuned on these.",
        "charts": charts,
    }


if __name__ == "__main__":
    corpus = build()
    _OUT.write_text(json.dumps(corpus, indent=1))
    print(f"wrote {_OUT} with {len(corpus['charts'])} charts")
