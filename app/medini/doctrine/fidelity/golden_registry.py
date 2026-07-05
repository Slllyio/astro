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


@dataclasses.dataclass(frozen=True)
class ConstructedCase:
    rule_id: str
    label: str
    lagna_sign: int                 # 1..12
    placements: dict[str, int]      # graha -> sign 1..12
    expected_fire: bool
    verdict_polarity: str | None = None  # Raman's verdict for a firing chart

    def chart(self) -> RamanChart:
        lons = {}
        for g in GRAHAS:
            sign = self.placements.get(g, _PARK)
            lons[g] = (sign - 1) * 30 + 15.0
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
)
