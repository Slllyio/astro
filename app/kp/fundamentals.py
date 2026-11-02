"""Reader 2's sign classes and the few definite rules it builds on them (ruling R29).

*KP Reader 2, Fundamental Principles of Astrology* is mostly signification lists and
philosophy. Its chapter on the classes of signs (KPR2 pp.105-115) is the one place where it
states rules a chart can be checked against: the qualities (movable, fixed, common) on the
angles and on single cusps, fruitful and barren signs on the cusps for marriage and children,
mute and voice signs for speech. This module encodes the classes and those rules exactly as
printed and only DESCRIBES which of them a chart meets. Nothing here feeds a KP verdict,
window or selection: Krishnamurti presents these as the general background his sub-lord
method later refines, and he hedges the marriage rule himself ("provided other testimonies
also point to the same view").

Ruling R29 (``docs/kp/KP_RULINGS.md``) fixes how each phrase is read:

* "Cusp of the Nth house" is the KP (Placidus) cusp; "lord" of a house is the lord of the sign
  on its cusp; a planet "in the Nth house" is in that KP bhava.
* Sign classes are Reader 2's own lists. Where it lists a class twice with different members,
  the definition in its section on signs is used (barren: Aries, Gemini, Leo, Virgo; the
  5th-house chapter omits Gemini). Semi-fruitful signs are not "fruitful".
* "Fruitful planet": the planets Reader 2 itself calls fruitful, the Moon ("hence Moon is a
  fruitful planet") and Jupiter ("a fiery, noble, benevolent, fruitful ... planet").
* "Majority of the planets": at least five of the nine KP bodies.
* "Opposition" (Mercury and Moon): the Moon in the 7th sign from Mercury, the traditional
  sign frame of the same paragraph.
* Three rules cannot fire as printed. The 5th and 11th cusps are always opposite signs, and no
  sign opposite a fruitful (watery) sign is watery, nor any opposite a barren sign barren. So
  "fruitful signs covering the 11th and 5th" (progeny promised), "barren signs on the cusps of
  the 5th and 11th" (no children) and the all-barren arm of "barren signs in the cusps of the
  1st, 5th and 11th" never hold. They are kept as printed, not repaired. The 5th-house chapter
  states the promise with "or" ("on the cusp of the 5th or the 11th", KPR2 p.287), encoded as
  ``progeny.promised_either``. "Fruitful signs in the cusps of the 5th and 7th" needs those
  cusps 120 degrees apart and almost never holds.
* Left out, and listed in ``EXCLUDED``: every condition resting on "afflicted", "bad aspect",
  "harmonious aspect" or "free from affliction", which Reader 2 does not define, and the
  common-sign rule's "a number of planets", which gives no count.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.fundamentals import fundamentals
    for f in fundamentals(cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))):
        print(f.key, f.met, f.detail)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import KPChart, sign_index
from app.kp.subs import SIGN_LORDS

# Sign numbers, 0 = Aries ... 11 = Pisces. KPR2 pp.105-115.
MOVABLE: Final[frozenset[int]] = frozenset({0, 3, 6, 9})
FIXED: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
COMMON: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
FRUITFUL: Final[frozenset[int]] = frozenset({3, 7, 11})
SEMI_FRUITFUL: Final[frozenset[int]] = frozenset({1, 6, 8, 9})
BARREN: Final[frozenset[int]] = frozenset({0, 2, 4, 5})
MUTE: Final[frozenset[int]] = frozenset({3, 7, 11})
VIOLENT: Final[frozenset[int]] = frozenset({0, 7})
VOICE: Final[frozenset[int]] = frozenset({2, 6, 10})
DUAL: Final[frozenset[int]] = frozenset({2, 8, 11})
QUALITIES: Final[dict[str, frozenset[int]]] = {"movable": MOVABLE, "fixed": FIXED, "common": COMMON}
FRUITFUL_PLANETS: Final[frozenset[str]] = frozenset({"Moon", "Jupiter"})
BODIES: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                                  "Rahu", "Ketu")
FRAMING: Final[str] = ("Reader 2's general sign rules, before the sub-lord method: what the text "
                       "says the configuration indicates, not a KP verdict or a prediction.")


def human_sign(longitude: float) -> bool:
    """Gemini, Virgo, Aquarius and the first half of Sagittarius (KPR2 p.115)."""
    s = sign_index(longitude)
    return s in (2, 5, 10) or (s == 8 and longitude % 30 < 15)


def bestial_sign(longitude: float) -> bool:
    """Aries, Taurus, Leo, Capricorn and the second half of Sagittarius (KPR2 p.115)."""
    s = sign_index(longitude)
    return s in (0, 1, 4, 9) or (s == 8 and longitude % 30 >= 15)


@dataclass(frozen=True, slots=True)
class Fundamental:
    key: str
    citation: str
    indication: str   # what Reader 2 says the configuration shows, abridged from the quote
    met: bool
    detail: str

    def to_dict(self) -> dict:
        return {"key": self.key, "citation": self.citation, "indication": self.indication,
                "met": self.met, "detail": self.detail, "framing": FRAMING}


#: Conditions in the same passages that are not encoded, with the reason (ruling R29).
EXCLUDED: Final[dict[str, str]] = {
    "speech.lord6_afflicted": "the lord of 6 in the 2nd in a mute sign 'afflicted by Mars or Saturn': affliction undefined",
    "speech.mercury_saturn": "Mercury in a mute sign 'afflicted by Saturn': affliction undefined",
    "speech.mars_bad_aspect": "Mars adding 'his influence by bad aspect': bad aspect undefined",
    "voice.free_from_affliction": "Venus or Mercury in the 2nd 'free from affliction': only the bare placement is checked",
    "voice.jupiter_mars_saturn": "Jupiter, Mars and Saturn as speakers: no placement is named",
    "partnership.harmonious_aspect": "1st and 7th lords 'in harmonious aspect': aspect undefined (the exchange arm is encoded)",
    "angles.common_number": "'a number of planets' in common signs: no count is given (the cusp arm is encoded)",
    "human.predominant": "'predominant planets' and 'principal significators' in human signs: neither is defined",
    "afflictions.by_quality": "afflictions from movable or fixed signs: affliction undefined",
}


class _Ctx:
    def __init__(self, chart: KPChart) -> None:
        self.c = chart

    def cusp(self, h: int) -> int:
        return sign_index(self.c.cusp(h).longitude)

    def lord(self, h: int) -> str:
        return SIGN_LORDS[self.cusp(h)]

    def sign(self, body: str) -> int:
        return sign_index(self.c.planets[body].longitude)

    def bhava(self, body: str) -> int:
        return self.c.planets[body].bhava

    def majority(self, cls: frozenset[int]) -> int:
        return sum(self.sign(b) in cls for b in BODIES)


_SIGN = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _cusps(x: _Ctx, hs: tuple[int, ...]) -> str:
    return ", ".join(f"cusp {h} {_SIGN[x.cusp(h)]}" for h in hs)


def _lords(x: _Ctx, hs: tuple[int, ...]) -> str:
    return ", ".join(f"lord of {h} {x.lord(h)} in {_SIGN[x.sign(x.lord(h))]}" for h in hs)


def fundamentals(chart: KPChart) -> tuple[Fundamental, ...]:
    x = _Ctx(chart)
    out: list[Fundamental] = []

    def add(key: str, cit: str, ind: str, met: bool, detail: str) -> None:
        out.append(Fundamental(key, cit, ind, bool(met), detail))

    ang = (1, 4, 7, 10)
    for q, cls, cit, ind in (
        ("movable", MOVABLE, "KPR2-ANGLES-MOVABLE",
         "a prominent position; ambition and enterprise; many changes"),
        ("fixed", FIXED, "KPR2-ANGLES-FIXED",
         "firm, determined, self-reliant; slow and plodding but succeeds eventually"),
        ("common", COMMON, "KPR2-ANGLES-COMMON",
         "a fickle, wavering, versatile mind; succeeds by others' aid"),
    ):
        on_angles = all(x.cusp(h) in cls for h in ang)
        add(f"angles.{q}", cit, ind, on_angles, _cusps(x, ang))
        if q != "common":
            n = x.majority(cls)
            add(f"majority.{q}", cit, ind, n >= 5, f"{n} of 9 bodies in {q} signs")

    asc_q = next(q for q, c in QUALITIES.items() if x.cusp(1) in c)
    add("ascendant.movable", "KPR2-ASC-MOVABLE",
        "ailments of the head, stomach, kidneys; movable or functional disorders",
        asc_q == "movable", _cusps(x, (1,)))
    add("second.movable", "KPR2-SECOND-MOVABLE",
        "money through name, fame and public recognition; fluctuating fortune",
        x.cusp(2) in MOVABLE, _cusps(x, (2,)))
    third = next(q for q, c in QUALITIES.items() if x.cusp(3) in c)
    for q, cit, ind in (("movable", "KPR2-THIRD-MOVABLE", "an aspiring, active, changeable mind; travel"),
                        ("fixed", "KPR2-THIRD-FIXED", "a fixed, rigid, persevering attitude; dislikes travelling"),
                        ("common", "KPR2-THIRD-COMMON", "a receptive, methodical mind, easily affected by surroundings")):
        add(f"third.{q}", cit, ind, third == q, _cusps(x, (3,)))

    ju11 = x.bhava("Jupiter") == 11
    for q, ind in (("movable", "executive ability and progress"),
                   ("fixed", "jealousy and pride among friends"),
                   ("common", "friends scientific or religious-minded; friends may prove unreliable")):
        add(f"jupiter11.{q}", "KPR2-ELEVENTH-JUPITER", ind, ju11 and x.sign("Jupiter") in QUALITIES[q],
            f"Jupiter in house {x.bhava('Jupiter')}, {_SIGN[x.sign('Jupiter')]}")
    sa11 = x.bhava("Saturn") == 11
    add("saturn11.fixed", "KPR2-ELEVENTH-SATURN", "delay and hindrance through friends",
        sa11 and x.sign("Saturn") in FIXED, f"Saturn in house {x.bhava('Saturn')}, {_SIGN[x.sign('Saturn')]}")
    add("saturn11.common", "KPR2-ELEVENTH-SATURN", "may not achieve one's hopes; sorrow through friends",
        sa11 and x.cusp(11) in COMMON, f"Saturn in house {x.bhava('Saturn')}; {_cusps(x, (11,))}")

    l1, l7 = x.lord(1), x.lord(7)
    exch = l1 != l7 and SIGN_LORDS[x.sign(l1)] == l7 and SIGN_LORDS[x.sign(l7)] == l1
    add("partnership.exchange", "KPR2-PARTNERSHIP", "partnership advisable; a good mutual working arrangement",
        exch, _lords(x, (1, 7)))
    add("friends.common11", "KPR2-PARTNERSHIP", "doubtful friendships",
        x.cusp(11) in COMMON and x.sign(x.lord(11)) in COMMON, f"{_cusps(x, (11,))}; {_lords(x, (11,))}")

    add("marriage.early", "KPR2-FRUITFUL-RULES", "an early union",
        all(x.cusp(h) in FRUITFUL for h in (5, 7)) and all(x.sign(x.lord(h)) in FRUITFUL for h in (5, 7)),
        f"{_cusps(x, (5, 7))}; {_lords(x, (5, 7))}")
    add("marriage.late", "KPR2-FRUITFUL-RULES",
        "not likely to marry in time (provided other testimonies agree)",
        all(x.cusp(h) in BARREN for h in (5, 1)), _cusps(x, (1, 5)))
    add("progeny.promised", "KPR2-FRUITFUL-RULES", "progeny promised",
        all(x.cusp(h) in FRUITFUL for h in (5, 11)) and all(x.sign(x.lord(h)) in FRUITFUL for h in (5, 11)),
        f"{_cusps(x, (5, 11))}; {_lords(x, (5, 11))}")
    add("progeny.promised_either", "KPR2-FIFTH-HOUSE", "children promised (if other testimonies support)",
        x.cusp(5) in FRUITFUL or x.cusp(11) in FRUITFUL, _cusps(x, (5, 11)))
    three = (1, 5, 11)
    add("progeny.lessened", "KPR2-FRUITFUL-RULES", "lessened chances of children",
        all(x.cusp(h) in BARREN for h in three) or all(x.sign(x.lord(h)) in BARREN for h in three),
        f"{_cusps(x, three)}; {_lords(x, three)}")
    in_5_11 = [b for b in FRUITFUL_PLANETS if x.bhava(b) in (5, 11)]
    none = (all(x.cusp(h) in BARREN for h in (5, 11))
            and all(x.sign(x.lord(h)) not in FRUITFUL for h in (5, 11))
            and x.sign("Moon") not in FRUITFUL
            and x.cusp(1) not in FRUITFUL
            and x.sign(x.lord(1)) not in FRUITFUL
            and not in_5_11)
    add("progeny.none", "KPR2-NO-CHILDREN", "indications of no children", none,
        f"{_cusps(x, (1, 5, 11))}; {_lords(x, (1, 5, 11))}; Moon in {_SIGN[x.sign('Moon')]}; "
        f"fruitful planets in 5/11: {', '.join(sorted(in_5_11)) or 'none'}")

    me = x.sign("Mercury")
    add("speech.mercury6", "KPR2-SPEECH", "perceptible stammer, lisp or other impediment",
        6 in chart.owned_houses("Mercury") and x.bhava("Mercury") == 2 and me in MUTE,
        f"Mercury owns {chart.owned_houses('Mercury')}, in house {x.bhava('Mercury')}, {_SIGN[me]}")
    add("speech.mercury_moon", "KPR2-SPEECH-2", "a defect in speech",
        me in MUTE and (x.sign("Moon") - me) % 12 == 6, f"Mercury in {_SIGN[me]}, Moon in {_SIGN[x.sign('Moon')]}")
    add("speech.saturn_lagna", "KPR2-SPEECH-2", "an impediment in speech",
        x.bhava("Saturn") == 1 and x.sign("Saturn") in MUTE,
        f"Saturn in house {x.bhava('Saturn')}, {_SIGN[x.sign('Saturn')]}")
    voice2 = x.cusp(2) in VOICE
    in2 = [b for b in ("Venus", "Mercury") if x.bhava(b) == 2]
    add("voice.second", "KPR2-SPEECH-2", "eloquence or some vocal gift", voice2, _cusps(x, (2,)))
    add("voice.second_venus_mercury", "KPR2-SPEECH-2", "eloquence or some vocal gift (the stronger case)",
        voice2 and bool(in2), f"{_cusps(x, (2,))}; Venus/Mercury in the 2nd: {', '.join(in2) or 'none'}")
    return tuple(out)


__all__ = ["BARREN", "COMMON", "DUAL", "EXCLUDED", "FIXED", "FRAMING", "FRUITFUL", "FRUITFUL_PLANETS",
           "Fundamental", "MOVABLE", "MUTE", "QUALITIES", "SEMI_FRUITFUL", "VIOLENT", "VOICE",
           "bestial_sign", "fundamentals", "human_sign"]
