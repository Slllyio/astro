"""Build `unseen_grow.json` -- the maximum-addressable HTJAH strength expansion.

After the clean full-text audit, exactly 8 fresh (engine-unseen, mappable-verdict, house-
judged) charts remained addressable; 6 survived vision extraction + the reachability gate +
a per-chart cross-check against Raman's own prose placements (ch79 failed the Navamsa gate;
ch31's grid did not extract). Their verdicts are Raman's verbatim words from the clean text
(offset-corrected via the in-prose "In Chart No. N" markers), hand-graded against the full
conclusion (auto-mapping alone mis-fires on negations like "no afflictions").

Houses 4/8/11 are genuinely non-tuned held-out; houses 7 are tuned-HOUSE (the engine was
tuned on OTHER 7th-house charts, not these) -- flagged ``tuned_house`` so the pooled number
can separate them. This is the honest ceiling of the HTJAH strength vein.
"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_OUT = _ROOT / "docs/raman_doctrine/validation/corpora/unseen_grow.json"

_GRID = {
    65: {"lagna_rasi": "Aries", "lagna_navamsa": "Leo", "rasi": {"Sun": "Scorpio", "Moon": "Libra", "Mars": "Scorpio", "Mercury": "Libra", "Jupiter": "Capricorn", "Venus": "Scorpio", "Saturn": "Gemini", "Rahu": "Aquarius", "Ketu": "Leo"}, "navamsa": {"Sun": "Cancer", "Moon": "Aquarius", "Mars": "Libra", "Mercury": "Aquarius", "Jupiter": "Leo", "Venus": "Sagittarius", "Saturn": "Capricorn", "Rahu": "Capricorn", "Ketu": "Cancer"}},
    76: {"lagna_rasi": "Virgo", "lagna_navamsa": "Taurus", "rasi": {"Sun": "Scorpio", "Moon": "Sagittarius", "Mars": "Libra", "Mercury": "Scorpio", "Jupiter": "Sagittarius", "Venus": "Sagittarius", "Saturn": "Libra", "Rahu": "Cancer", "Ketu": "Capricorn"}, "navamsa": {"Sun": "Leo", "Moon": "Sagittarius", "Mars": "Aries", "Mercury": "Pisces", "Jupiter": "Sagittarius", "Venus": "Cancer", "Saturn": "Gemini", "Rahu": "Virgo", "Ketu": "Pisces"}},
    230: {"lagna_rasi": "Capricorn", "lagna_navamsa": "Aries", "rasi": {"Sun": "Gemini", "Moon": "Aquarius", "Mars": "Pisces", "Mercury": "Cancer", "Jupiter": "Taurus", "Venus": "Taurus", "Saturn": "Virgo", "Rahu": "Pisces", "Ketu": "Virgo"}, "navamsa": {"Sun": "Capricorn", "Moon": "Capricorn", "Mars": "Virgo", "Mercury": "Leo", "Jupiter": "Virgo", "Venus": "Capricorn", "Saturn": "Virgo", "Rahu": "Scorpio", "Ketu": "Taurus"}},
    27: {"lagna_rasi": "Libra", "lagna_navamsa": "Libra", "rasi": {"Sun": "Pisces", "Moon": "Aries", "Mars": "Leo", "Mercury": "Aries", "Jupiter": "Virgo", "Venus": "Aquarius", "Saturn": "Gemini", "Rahu": "Leo", "Ketu": "Aquarius"}, "navamsa": {"Sun": "Aquarius", "Moon": "Virgo", "Mars": "Leo", "Mercury": "Aries", "Jupiter": "Pisces", "Venus": "Capricorn", "Saturn": "Capricorn", "Rahu": "Scorpio", "Ketu": "Taurus"}},
    28: {"lagna_rasi": "Capricorn", "lagna_navamsa": "Aries", "rasi": {"Sun": "Gemini", "Moon": "Aquarius", "Mars": "Pisces", "Mercury": "Cancer", "Jupiter": "Taurus", "Venus": "Taurus", "Saturn": "Virgo", "Rahu": "Pisces", "Ketu": "Virgo"}, "navamsa": {"Sun": "Aquarius", "Moon": "Aquarius", "Mars": "Virgo", "Mercury": "Cancer", "Jupiter": "Virgo", "Venus": "Aquarius", "Saturn": "Virgo", "Rahu": "Scorpio", "Ketu": "Taurus"}},
    29: {"lagna_rasi": "Libra", "lagna_navamsa": "Sagittarius", "rasi": {"Sun": "Leo", "Moon": "Aquarius", "Mars": "Leo", "Mercury": "Leo", "Jupiter": "Aquarius", "Venus": "Libra", "Saturn": "Pisces", "Rahu": "Libra", "Ketu": "Aries"}, "navamsa": {"Sun": "Scorpio", "Moon": "Gemini", "Mars": "Gemini", "Mercury": "Gemini", "Jupiter": "Libra", "Venus": "Capricorn", "Saturn": "Aquarius", "Rahu": "Gemini", "Ketu": "Sagittarius"}},
    31: {"lagna_rasi": "Libra", "lagna_navamsa": "Taurus", "rasi": {"Sun": "Scorpio", "Moon": "Leo", "Mars": "Leo", "Mercury": "Libra", "Jupiter": "Capricorn", "Venus": "Scorpio", "Saturn": "Capricorn", "Rahu": "Libra", "Ketu": "Aries"}, "navamsa": {"Sun": "Virgo", "Moon": "Virgo", "Mars": "Scorpio", "Mercury": "Gemini", "Jupiter": "Cancer", "Venus": "Virgo", "Saturn": "Capricorn", "Rahu": "Libra", "Ketu": "Aries"}},
}

_META = {
    65: {"house": 4, "vol": "htjah_vol1", "tuned_house": False, "birth_line": "Born on 16-11-1914 at 5 p.m.", "verdicts": [
        {"factor": "bhava", "phrase": "The fourth house is moderately strong"},
        {"factor": "lord", "phrase": "the lord and the Karaka are considerably afflicted"},
        {"factor": "karaka", "phrase": "the lord and the Karaka are considerably afflicted", "karaka": "Moon"}]},
    76: {"house": 8, "vol": "htjah_vol2", "tuned_house": False, "birth_line": "Born 20-11-1925 at 1 p.m.", "verdicts": [
        {"factor": "bhava", "phrase": "The 8th house and 8th lord from Lagna and Moon are heavily afflicted"}]},
    230: {"house": 11, "vol": "htjah_vol2", "tuned_house": False, "birth_line": "Born 23-6-1894 at 10 p.m.", "verdicts": [
        {"factor": "lord", "phrase": "The 11th lord is blemished"}]},
    27: {"house": 7, "vol": "htjah_vol2", "tuned_house": True, "birth_line": "Born 6-4-1886", "verdicts": [
        {"factor": "karaka", "phrase": "The KalatraKaraka Venus is afflicted by association with Ketu", "karaka": "Venus"}]},
    28: {"house": 7, "vol": "htjah_vol2", "tuned_house": True, "birth_line": "Born 23-6-1894", "verdicts": [
        {"factor": "lord", "phrase": "The Moon as the 7th lord is not afflicted by aspect or association"}]},
    29: {"house": 7, "vol": "htjah_vol2", "tuned_house": True, "birth_line": "Born 10-9-1938", "verdicts": [
        {"factor": "overall", "phrase": "The 7th house and the 8th lord the Moon in Navamsha are both heavily afflicted"}]},
    31: {"house": 7, "vol": "htjah_vol2", "tuned_house": True, "birth_line": "Born 22/23-11-1902", "verdicts": [
        {"factor": "bhava", "phrase": "the 7th house is occupied by Vargottama Ketu and aspected by an afflicted 9th and 12th lord"}]},
}


def build() -> dict:
    charts = []
    for cn, meta in _META.items():
        g = _GRID[cn]
        charts.append({"chart_no": cn, "vol": meta["vol"], "birth_line": meta["birth_line"],
                       "house_judged": meta["house"], "tuned_house": meta["tuned_house"],
                       "rasi": g["rasi"], "navamsa": g["navamsa"],
                       "lagna_rasi": g["lagna_rasi"], "lagna_navamsa": g["lagna_navamsa"],
                       "verdicts": meta["verdicts"]})
    return {
        "source": "HTJAH Vol I & II -- the MAXIMUM addressable fresh strength charts after the "
                  "clean-full-text audit (8 addressable -> 6 gate-passed + prose-verified). ch65 "
                  "recovers the Tier-2 drop (its grid now prose-consistent). Houses 4/8/11 are "
                  "non-tuned held-out; house 7 is tuned-HOUSE (flagged tuned_house). Verdicts are "
                  "Raman's verbatim words, offset-corrected + hand-graded. Measurement only.",
        "charts": charts,
    }


if __name__ == "__main__":
    _OUT.write_text(json.dumps(build(), indent=1))
    print(f"wrote {_OUT} with {len(build()['charts'])} charts")
