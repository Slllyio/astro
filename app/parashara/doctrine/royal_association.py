"""Royal-association (Raja-sabha) yogas — BPHS ch.40, the crisp chara-karaka combinations.

The yogas that make one a king's minister / royally favoured, encoded where the condition is crisp
and built on the chara karakas already computed (Atmakaraka, Amatyakaraka — ch.32). Each cites its
own sloka:

  sl.1 — the 10th lord conjunct/aspected by the Amatyakaraka or the Amatyakaraka's dispositor.
  sl.3 — the Amatyakaraka together with the Atmakaraka's dispositor.
  sl.5 — the Amatyakaraka in the ascendant, the 5th, or the 9th.
  sl.6 — the Amatyakaraka or the Atmakaraka in a kendra or trikona from the ascendant.

DEFERRED (not faked): the "Amatyakaraka is strong" clause (sl.4) — a Shadbala judgment; and the
Arudha-Lagna / compound frames (sl.7-9) — kept in `yoga_catalogue`. Conjunction is same-sign; aspects
use graha drishti. The chara karakas are the strict 7-karaka set (no nodes).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.chara_karaka import chara_karakas
from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

_WORK: Final[str] = "BPHS-40"
SOURCE: Final[Citation] = Citation(_WORK, 25)          # sl.1
_KENDRA_TRIKONA: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10})


@dataclass(frozen=True)
class RoyalYoga:
    name: str
    reason: str
    source: Citation


def _house_sign(asc_sign: int, house: int) -> int:
    return ((asc_sign + house - 2) % 12) + 1


def detect(longitudes: Mapping[str, float], *, asc_sign: int) -> tuple[RoyalYoga, ...]:
    """Every crisp ch.40 royal-association yoga present, each cited to its own sloka."""
    signs = {p: int(l % 360.0 // 30) + 1 for p, l in longitudes.items()}
    ck = chara_karakas(longitudes)
    ak, amk = ck.get("AK"), ck.get("AmK")
    if ak is None or amk is None:
        return ()

    def house_of(planet: str) -> int:
        return ((signs[planet] - asc_sign) % 12) + 1

    def conjunct_or_aspects(planet: str, target_sign: int) -> bool:
        return signs.get(planet) == target_sign or (
            planet in signs and aspects_sign(planet, signs[planet], target_sign))

    out: list[RoyalYoga] = []
    tenth_lord = SIGN_LORDS[_house_sign(asc_sign, 10)]
    amk_dispositor = SIGN_LORDS[signs[amk]]
    ak_dispositor = SIGN_LORDS[signs[ak]]

    # sl.1 — 10th lord touched by the Amatyakaraka or its dispositor
    if tenth_lord in signs and (conjunct_or_aspects(amk, signs[tenth_lord])
                                or conjunct_or_aspects(amk_dispositor, signs[tenth_lord])):
        out.append(RoyalYoga("Raja-sabha (10th lord touched by Amatyakaraka)",
                             "the 10th lord conjunct or aspected by the Amatyakaraka or its "
                             "dispositor", Citation(_WORK, 25)))

    # sl.3 — Amatyakaraka together with the Atmakaraka's dispositor
    if amk != ak_dispositor and signs[amk] == signs.get(ak_dispositor):
        out.append(RoyalYoga("Raja-sabha (Amatyakaraka with the Atmakaraka's dispositor)",
                             "the Amatyakaraka conjunct the Atmakaraka's dispositor",
                             Citation(_WORK, 63)))

    # sl.5 — Amatyakaraka in the ascendant, 5th or 9th
    if house_of(amk) in (1, 5, 9):
        out.append(RoyalYoga("Raja-sabha (Amatyakaraka in the 1st/5th/9th)",
                             f"the Amatyakaraka ({amk}) in the {house_of(amk)}th from the ascendant",
                             Citation(_WORK, 81)))

    # sl.6 — Amatyakaraka or Atmakaraka in a kendra or trikona
    in_kt = [k for k in ((amk, "Amatyakaraka"), (ak, "Atmakaraka")) if house_of(k[0]) in _KENDRA_TRIKONA]
    if in_kt:
        who = " / ".join(f"{name} ({p})" for p, name in in_kt)
        out.append(RoyalYoga("Raja-sabha (chara karaka in a kendra/trikona)",
                             f"{who} in a kendra or trikona from the ascendant", Citation(_WORK, 87)))

    return tuple(out)
