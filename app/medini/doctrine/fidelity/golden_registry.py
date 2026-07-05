"""Golden cases for the fidelity harness.

Two kinds:

* **Constructed cases** (``CONSTRUCTED``): a chart hand-built to satisfy (or
  deliberately violate) a rule's PROSE definition, with the rule it targets
  and whether it should fire. Built from the prose, never from the encoded
  antecedent, so a mismatch is a real encoding bug. Persisted to
  ``data/raman_doctrine/golden_cases.json``.

* **Printed cases** (``PRINTED``): B. V. Raman's own worked horoscopes with
  printed positions and the mechanisms he names — reused from the frozen
  run-5 casebook (``app/medini/ml/raman_saab/fidelity.py``) for the
  printed-chart smoke + mechanism-overlap check.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from app.medini.doctrine.raman_chart import RamanChart, from_positions

GOLDEN_PATH = Path("data/raman_doctrine/golden_cases.json")
GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
          "Rahu", "Ketu")
# A parking sign for grahas a case doesn't constrain — chosen so it does not
# accidentally satisfy the targeted antecedents (no case targets sign 11 /
# the 11th-from-Aries house in a way the parking would complete).
_PARK = 11

# Base longitudes for karakamsa cases: distinct degrees so the Atmakaraka is
# unambiguous (the Sun, highest deg-in-sign 29°) and the Karakamsa sign is
# fixed. A target planet is then moved to 108.0 (navamsa Sagittarius = kk
# house 1, "in Karakamsa") for a positive, or 6.0 (kk house 6) for a control.
_KK_BASE = {"Sun": 29.0, "Moon": 40.0, "Mars": 70.0, "Mercury": 100.0,
            "Jupiter": 130.0, "Venus": 160.0, "Saturn": 190.0, "Rahu": 5.0,
            "Ketu": 220.0}
_KK_IN = 108.0    # -> karakamsa house 1
_KK_OUT = 6.0     # -> karakamsa house 6 (control)


@dataclasses.dataclass(frozen=True)
class ConstructedCase:
    rule_id: str
    label: str
    lagna_sign: int                 # 1..12
    placements: dict[str, int]      # graha -> sign 1..12
    expected_fire: bool
    verdict_polarity: str | None = None  # Raman's verdict for a firing chart
    longitudes: dict[str, float] | None = None  # graha -> absolute lon; for
    # frame rules (karakamsa/navamsa) that need real degrees, not sign midpoints

    def chart(self) -> RamanChart:
        lons = {}
        for g in GRAHAS:
            sign = self.placements.get(g, _PARK)
            lons[g] = (sign - 1) * 30 + 15.0
        if self.longitudes:
            lons.update(self.longitudes)
        lagna_lon = (self.lagna_sign - 1) * 30 + 5.0
        return from_positions(lons, lagna_lon, birth_jd=2451545.0)


def load_constructed(path: Path = GOLDEN_PATH) -> list[ConstructedCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ConstructedCase(**c) for c in data["cases"]]


def save_constructed(cases: list[ConstructedCase], path: Path = GOLDEN_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "Charts hand-built from Raman's prose to test that the encoded "
                "antecedent reproduces the stated mechanism (fires when it "
                "should, stays quiet on controls).",
        "cases": [dataclasses.asdict(c) for c in cases],
    }
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ cases

# Each positive case is a chart built to match the yoga/rule's prose; each
# control violates one clause so the rule must NOT fire.
CONSTRUCTED: tuple[ConstructedCase, ...] = (
    # Gajakesari (y001): Jupiter in a kendra (1/4/7/10) from the Moon.
    ConstructedCase("raman.three_hundred.y001.gajakesari",
                    "Jupiter in the 4th from the Moon (kendra)",
                    lagna_sign=1, placements={"Moon": 1, "Jupiter": 4},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.three_hundred.y001.gajakesari",
                    "control: Jupiter in the 2nd from the Moon (not a kendra)",
                    lagna_sign=1, placements={"Moon": 1, "Jupiter": 2},
                    expected_fire=False),
    # Adhi (y007): benefics in the 6th, 7th and 8th from the Moon.
    ConstructedCase("raman.three_hundred.y007.adhi",
                    "benefic in the 7th from the Moon",
                    lagna_sign=1,
                    placements={"Moon": 1, "Jupiter": 7, "Venus": 6, "Mercury": 8},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.three_hundred.y007.adhi",
                    "control: no benefic in the 6/7/8 from the Moon",
                    lagna_sign=1,
                    placements={"Moon": 1, "Jupiter": 2, "Venus": 3, "Mercury": 4},
                    expected_fire=False),
    # Sunapha (y002): a planet (not Sun/nodes) in the 2nd from the Moon.
    ConstructedCase("raman.three_hundred.y002.sunapha",
                    "Mars in the 2nd from the Moon",
                    lagna_sign=1, placements={"Moon": 1, "Mars": 2},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.three_hundred.y002.sunapha",
                    "control: no planet in the 2nd from the Moon",
                    lagna_sign=1,
                    placements={"Moon": 1, "Mars": 3, "Mercury": 4, "Jupiter": 5,
                                "Venus": 6, "Saturn": 7, "Sun": 8},
                    expected_fire=False),

    # HPA Ch. XVII key-planets — functional role by lagna sign.
    ConstructedCase("raman.hpa.xvii.aries_key_planets",
                    "Aries lagna",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="neutral"),
    ConstructedCase("raman.hpa.xvii.aries_key_planets",
                    "control: Taurus lagna",
                    lagna_sign=2, placements={}, expected_fire=False),
    ConstructedCase("raman.hpa.xvii.virgo_key_planets",
                    "Virgo lagna",
                    lagna_sign=6, placements={}, expected_fire=True,
                    verdict_polarity="neutral"),

    # HTJAH Vol 1 lord placements — lord_of_house_in_house.
    # Aries lagna (lord Mars); Mars in the 7th house = sign 7.
    ConstructedCase("raman.htjah_vol1.ch4.lagna_lord_in_7",
                    "Aries lagna, its lord Mars in the 7th",
                    lagna_sign=1, placements={"Mars": 7},
                    expected_fire=True, verdict_polarity="unfavorable"),
    ConstructedCase("raman.htjah_vol1.ch4.lagna_lord_in_7",
                    "control: Aries lagna, Mars in the 1st",
                    lagna_sign=1, placements={"Mars": 1},
                    expected_fire=False),
    # 2nd-lord in the 11th: Aries lagna -> 2nd is Taurus (lord Venus); Venus
    # in the 11th house = sign 11.
    ConstructedCase("raman.htjah_vol1.ch5.lord2_in_11",
                    "Aries lagna, 2nd lord Venus in the 11th",
                    lagna_sign=1, placements={"Venus": 11},
                    expected_fire=True, verdict_polarity="favorable"),

    # HPA Ch. XV maraka functional role (Sun/Venus by lordship). Cancer lagna:
    # 2nd is Leo (Sun) -> Sun is a sure maraka by 2nd lordship.
    ConstructedCase("raman.hpa.xv.sun_venus_kendradhipatya_maraka",
                    "Cancer lagna: the Sun owns the 2nd (Leo) -> sure maraka",
                    lagna_sign=4, placements={}, expected_fire=True,
                    verdict_polarity="unfavorable"),

    # ----- Prasna Marga Part 2: marriage & progeny (lagna frame) -----
    # Benefics in the 7th (Aries lagna -> 7th = sign 7).
    ConstructedCase("raman.prasna_marga_2.ch17.benefics_in_7th_good",
                    "a benefic (Jupiter) in the 7th house",
                    lagna_sign=1, placements={"Jupiter": 7},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.prasna_marga_2.ch17.benefics_in_7th_good",
                    "control: no benefic in the 7th",
                    lagna_sign=1,
                    placements={"Jupiter": 11, "Venus": 11, "Mercury": 11},
                    expected_fire=False),
    # Venus and the 7th lord in Upachayas. Taurus lagna: 7th = Scorpio (lord
    # Mars); Upachaya houses 3/6/10/11 = signs 4/7/11/12. Venus in the 3rd
    # (sign 4), Mars (7th lord) in the 6th (sign 7).
    ConstructedCase("raman.prasna_marga_2.ch17.venus_lord7_upachaya_happy",
                    "Venus and the 7th lord (Mars) both in Upachayas",
                    lagna_sign=2, placements={"Venus": 4, "Mars": 7},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.prasna_marga_2.ch17.venus_lord7_upachaya_happy",
                    "control: the 7th lord (Mars) in the 4th (not an Upachaya)",
                    lagna_sign=2, placements={"Venus": 4, "Mars": 5},
                    expected_fire=False),
    # Malefic in the 5th (Aries lagna -> 5th = sign 5).
    ConstructedCase("raman.prasna_marga_2.ch18.malefics_afflict_5th_no_children",
                    "a malefic (Saturn) in the 5th house",
                    lagna_sign=1, placements={"Saturn": 5},
                    expected_fire=True, verdict_polarity="unfavorable"),
    ConstructedCase("raman.prasna_marga_2.ch18.malefics_afflict_5th_no_children",
                    "control: Saturn in the 6th, not the 5th",
                    lagna_sign=1, placements={"Saturn": 6}, expected_fire=False),
    # Mars in a fiery 5th aspected by Jupiter. Aries lagna: 5th = Leo (fiery);
    # Jupiter in the 1st aspects the 5th (its 5th aspect).
    ConstructedCase("raman.prasna_marga_2.ch18.mars_5th_fiery_jupiter_aspect_children",
                    "Mars in the 5th (Leo, fiery), Jupiter aspecting from the 1st",
                    lagna_sign=1, placements={"Mars": 5, "Jupiter": 1},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.prasna_marga_2.ch18.mars_5th_fiery_jupiter_aspect_children",
                    "control: Jupiter in the 2nd, not aspecting the 5th",
                    lagna_sign=1, placements={"Mars": 5, "Jupiter": 2},
                    expected_fire=False),

    # ----- Studies in Jaimini: Arudha wealth (arudha frame) -----
    # Aries lagna, lord Mars in the 1st -> Arudha Lagna = sign 10; a benefic
    # (Jupiter) in sign 10 sits in the Arudha Lagna (arudha house 1).
    ConstructedCase("raman.jaimini_studies.financial.arudha_benefics_wealthy",
                    "benefic (Jupiter) in the Arudha Lagna",
                    lagna_sign=1,
                    placements={"Mars": 1, "Jupiter": 10, "Venus": 10, "Mercury": 10},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.jaimini_studies.financial.arudha_benefics_wealthy",
                    "control: benefics in the 2nd from Arudha, not on it",
                    lagna_sign=1,
                    placements={"Mars": 1, "Jupiter": 11, "Venus": 11, "Mercury": 11},
                    expected_fire=False),
    # 2nd from the Arudha Lagna (sign 11) holds Venus, Moon and Jupiter.
    ConstructedCase("raman.jaimini_studies.financial.venus_moon_jupiter_2nd_arudha_wealth",
                    "Venus, Moon and Jupiter together in the 2nd from Arudha",
                    lagna_sign=1,
                    placements={"Mars": 1, "Venus": 11, "Moon": 11, "Jupiter": 11},
                    expected_fire=True, verdict_polarity="favorable"),
    ConstructedCase("raman.jaimini_studies.financial.venus_moon_jupiter_2nd_arudha_wealth",
                    "control: Jupiter not in the 2nd from Arudha",
                    lagna_sign=1,
                    placements={"Mars": 1, "Venus": 11, "Moon": 11, "Jupiter": 10},
                    expected_fire=False),

    # ----- Studies in Jaimini: Karakamsa education (karakamsa frame) -----
    ConstructedCase("raman.jaimini_studies.education.jupiter_karakamsa_grammar_vedas",
                    "Jupiter in the Karakamsa",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Jupiter": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.jupiter_karakamsa_grammar_vedas",
                    "control: Jupiter not in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Jupiter": _KK_OUT}),
    ConstructedCase("raman.jaimini_studies.education.mercury_karakamsa_meemamsa",
                    "Mercury in the Karakamsa",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Mercury": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.mercury_karakamsa_meemamsa",
                    "control: Mercury not in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Mercury": _KK_OUT}),
    ConstructedCase("raman.jaimini_studies.education.mars_karakamsa_legal",
                    "Mars in the Karakamsa",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Mars": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.mars_karakamsa_legal",
                    "control: Mars not in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Mars": _KK_OUT}),
    ConstructedCase("raman.jaimini_studies.education.moon_karakamsa_music_literature",
                    "the Moon in the Karakamsa",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Moon": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.moon_karakamsa_music_literature",
                    "control: the Moon not in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Moon": _KK_OUT}),
    ConstructedCase("raman.jaimini_studies.education.ketu_karakamsa_mathematics",
                    "Ketu in the Karakamsa",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Ketu": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.ketu_karakamsa_mathematics",
                    "control: Ketu not in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Ketu": _KK_OUT}),
    ConstructedCase("raman.jaimini_studies.education.karakamsa_edu_jupiter_aspect_genius",
                    "an education combination present (Jupiter in the Karakamsa)",
                    lagna_sign=1, placements={}, expected_fire=True,
                    verdict_polarity="favorable",
                    longitudes={**_KK_BASE, "Jupiter": _KK_IN}),
    ConstructedCase("raman.jaimini_studies.education.karakamsa_edu_jupiter_aspect_genius",
                    "control: none of the five in the Karakamsa or the 5th from it",
                    lagna_sign=1, placements={}, expected_fire=False,
                    longitudes={**_KK_BASE, "Jupiter": _KK_OUT, "Mercury": _KK_OUT,
                                "Mars": _KK_OUT, "Moon": _KK_OUT, "Ketu": _KK_OUT}),
)
