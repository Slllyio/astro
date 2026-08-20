"""Bhangas: cancellation and exchange primitives for the Raman Saab engine.

Covers neecha-bhanga (cancellation of debilitation), effective_dignity,
parivartana (exchange), and kemadruma (Moon isolation yoga) + cancellation.

Usage:
    python -m app.raman_saab.primitives.bhangas  # (no CLI; import only)

Citation note
-------------
Kemadruma is defined in Raman's *Hindu Predictive Astrology*, Special Yogas
(HPA-20:208, ``hindu_predictive_astrology_raman/chapter_020_special-yogas.md``);
its cancellation is printed at 3HC:2182-2185 (see :func:`kemadruma_bhanga`).
Raman references neecha-bhanga at HPA-33:308
(``hindu_predictive_astrology_raman/chapter_033_annual-horoscopes.md``) but does
not enumerate the cancellation conditions there; the neecha-bhanga 4-condition
list (dispositor/planet-exalted-here in kendra from lagna/moon; conjunction with
dispositor; navamsa exaltation/vargottama) is the **standard
Parashari/Phaladeepika doctrine** that Raman's method accepts. It is anchored to
the 8-Considerations principle (HTJAH-I:474-493, consideration 5:
exaltation/debilitation of the lords; consideration 4: whether a yoga alters the
influence).

Phase-2 deferral: conditions that classically use *aspect* (dispositor
aspecting the debilitated planet; benefic aspecting the Moon for kemadruma
cancellation) are deferred to Phase 2 (drishti engine) and marked below.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

# Planet exalted in each sign (inverse of relationships.EXALTATION), for neecha-bhanga cond 2.
_EXALTED_IN_SIGN: Final[dict[int, str]] = {sign: p for p, (sign, _deg) in r.EXALTATION.items()}


def _in_kendra_from(planet: str, ref_house: int, chart: RamanChart) -> bool:
    """Is `planet` in a kendra (1/4/7/10) counted from rasi-house `ref_house`?"""
    if planet not in chart.planets:
        return False
    dist = ((chart.planets[planet].rasi_house - ref_house) % 12) + 1
    return dist in _KENDRA


def exchange(a: str, b_: str, chart: RamanChart) -> bool:
    """Parivartana between two planets: each occupies a sign owned by the other."""
    if a not in chart.planets or b_ not in chart.planets:
        return False
    return (SIGN_LORDS[chart.planets[a].sign] == b_ and
            SIGN_LORDS[chart.planets[b_].sign] == a)


def parivartana(h1: int, h2: int, chart: RamanChart) -> bool:
    """Exchange between the LORDS of houses h1 and h2 (rasi-house lords from the Lagna)."""
    lord1 = SIGN_LORDS[((chart.asc_sign - 1) + (h1 - 1)) % 12 + 1]
    lord2 = SIGN_LORDS[((chart.asc_sign - 1) + (h2 - 1)) % 12 + 1]
    if lord1 == lord2 or lord1 not in chart.planets or lord2 not in chart.planets:
        return False
    return (chart.planets[lord1].rasi_house == h2 and
            chart.planets[lord2].rasi_house == h1)


def neecha_bhanga(planet: str, chart: RamanChart) -> bool:
    """Cancellation of debilitation (neecha-bhanga raja yoga).

    Raman references neecha-bhanga at HPA-33:308 but does not enumerate the
    conditions; the 4-condition set below is the standard
    Parashari/Phaladeepika cancellation-of-debilitation doctrine Raman's method
    accepts, anchored to the exaltation/debilitation principle at HTJAH-I:474-493
    (consideration 5). See the module docstring.

    Computable conditions implemented here (Phase 1b):
      (1) dispositor of the debilitation sign is in a kendra from Lagna or Moon
      (2) the planet exalted in that sign is in a kendra from Lagna or Moon
      (3) conjunct its dispositor (same rasi-house)
      (4) exalted in navamsa, or vargottama

    Deferred to Phase 2 (drishti engine):
      aspect-by-dispositor on the debilitated planet.
    """
    if planet in ("Rahu", "Ketu") or planet not in chart.planets:
        return False
    if dignity(planet, chart) != "debil":
        return False
    p = chart.planets[planet]
    lagna_h = 1
    moon_h = chart.planets["Moon"].rasi_house if "Moon" in chart.planets else 1
    dispositor = SIGN_LORDS[p.sign]                      # lord of the debilitation sign
    exalted_here = _EXALTED_IN_SIGN.get(p.sign)          # planet exalted in that sign
    # (1) dispositor in a kendra from Lagna or Moon
    if _in_kendra_from(dispositor, lagna_h, chart) or _in_kendra_from(dispositor, moon_h, chart):
        return True
    # (2) the planet exalted in this sign is in a kendra from Lagna or Moon
    if exalted_here and (_in_kendra_from(exalted_here, lagna_h, chart)
                         or _in_kendra_from(exalted_here, moon_h, chart)):
        return True
    # (3) conjunct OR aspected by its dispositor (Phase 2: drishti now available)
    if dispositor in chart.planets and (
            chart.planets[dispositor].rasi_house == p.rasi_house
            or drishti.aspects_planet(dispositor, planet, chart)):
        return True
    # (4) exalted in navamsa. (A vargottama-but-debilitated planet is debilitated in D9 TOO -> doubly
    # afflicted, NOT cancelled; the classical clause is specifically navamsa-exaltation.)
    if p.navamsa_sign == r.EXALTATION[planet][0]:
        return True
    return False


def effective_dignity(planet: str, chart: RamanChart) -> str:
    """Dignity with neecha-bhanga applied: a cancelled debilitation reports
    'neecha_bhanga' rather than 'debil'."""
    d = dignity(planet, chart)
    if d == "debil" and neecha_bhanga(planet, chart):
        return "neecha_bhanga"
    return d


def kemadruma(chart: RamanChart) -> bool:
    """Kemadruma yoga: the Moon has no planet (excluding Sun and nodes) in the
    2nd or 12th from it and none conjunct it.

    Raman's definition: HPA-20:208 ("Kemadruma yoga. —No planets in the..."),
    Special Yogas chapter. This implements the standard doctrine: the Moon is
    isolated from all planets except Sun/Rahu/Ketu in the adjacent houses (2nd,
    12th) and in conjunction.

    NOTE: The aspect-based cancellation condition (benefic aspecting the Moon)
    is deferred to Phase 2 (drishti engine).
    """
    if "Moon" not in chart.planets:
        return False
    mh = chart.planets["Moon"].rasi_house
    neighbours = {(mh % 12) + 1, ((mh - 2) % 12) + 1, mh}   # 2nd, 12th, conjunct
    for name, pl in chart.planets.items():
        if name in ("Moon", "Sun", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in neighbours:
            return False
    return True


def kemadruma_bhanga(chart: RamanChart) -> bool:
    """Kemadruma cancellation per 3HC:2182-2185, plus one EXTENDED branch.

    3HC:2182-2185 (Remarks, verbatim — "m" is the corpus OCR for "in"):
    "Some authors say that if planets are m a kendra from birth or from the
    Moon or if the Moon is in conjunction with a planet there is no
    Kemadruma." Branches encoded from that line:

      (a) any planet (the Moon included) in a kendra (1/4/7/10) from birth
          (the Lagna);
      (b) any planet other than the Moon in a kendra counted from the Moon's
          rasi-house (the Moon itself is trivially its own 1st and is excluded);
      (c) the Moon in conjunction with a planet (same rasi, whole-sign — the
          convention of :mod:`app.raman_saab.primitives.relationships`).
          Subsumed by (b) since the 1st-from-Moon is a kendra, but kept as an
          explicit branch for textual fidelity.

    Sun policy: the cited line says "planets" / "a planet" with NO exception,
    so the Sun counts in every branch. Nodes are excluded per the project
    chaya-graha convention (3HC names no nodes here).

    Branch (c) is PROVABLY REDUNDANT (measured 2026-08-20, Track 4b). It is
    kept for textual fidelity to the quoted line and for no other reason. The
    docstring used to claim it earned its keep through the Sun — that a
    conjunction can still cancel where :func:`kemadruma` has already excluded
    every other planet — and that was simply wrong: `_in_kendra_from` scores
    the same house as distance 1, the 1st is a kendra, and the Sun is not
    excluded from branch (b). So every conjunction (c) can see, (b) has
    already seen. Removing it changes nothing by construction, not merely on
    a sample.

    EXTENDED bhanga — NOT attributable to 3HC:2182-2185: a natural benefic
    casting drishti on the Moon also cancels. This branch comes from the
    Phase-2 aspect backfill (standard doctrine) and is kept distinct so the
    corpus citation is not over-claimed.

    THE QUOTED REMARK DOES NOT END WHERE THIS DOCSTRING USED TO STOP (found
    2026-08-19, corpus mounted). The full Remarks run to 3HC:2188:

        "Some authors say that if planets are m a kendra from birth or from the
        Moon or if the Moon is in conjunction with a planet there is no
        Kemadruma. Theie are yet other authors who say that these yogas arise
        from kendras and navamsas BUT THESE OBSERVATIONS ARE NOT GENERALLY
        ACCEPTABLE."

    Two things follow, and both matter:

      * Raman ATTRIBUTES the cancellation to "some authors". He never states in
        his own voice that there is no Kemadruma in these cases. Citing
        3HC:2182-2185 as if it were his assertion over-claims the anchor, which
        is what this docstring did.
      * His dismissal at :2188 is grammatically ambiguous. "these observations"
        attaches most immediately to the SECOND group ("yet other authors ...
        kendras and navamsas"), but it can be read as covering both reported
        opinions, since he is reporting rather than endorsing throughout.

    The BEHAVIOUR here is deliberately unchanged: `kemadruma_bhanga` feeds the
    yoga layer and therefore the verdict path, so narrowing it would move the
    golden ratchet and needs the doctrine-review + user-sign-off path. Logged in
    DOCTRINE_BACKLOG "Kemadruma bhanga attribution". What IS fixed here is the
    claim: the anchor is now quoted in full, including the dismissal.

    RESOLVED 2026-08-20 (Track 4b): the ambiguity is settled by the mounted
    text itself, and in FAVOUR of branches (a) and (b). Raman applies them in
    his own voice, on worked charts, immediately after the Remarks:

        3HC:2263-2268 — "Here you will see that Kemadruma is present because
        the houses on either side of the Moon are vacant. But there is distinct
        cancellation of the Kemadruma because (a) the kendras from the Moon are
        occupied and (b) kendras from the Lagna are also occupied."

        3HC:2255-2261 — the converse, on Chart No. 8: "The above is a typically
        Kemadruma Yoga horoscope. No planets are placed on either side of
        Chandra and no planets are to be found in kendras either from Lagna or
        from the Moon."

    A man does not demonstrate a cancellation twice, once each way, and mean it
    to be "not generally acceptable". :2187-2188 therefore attaches to the
    SECOND reported group only ("yet other authors ... these yogas arise from
    kendras and navamsas"). Branches (a) and (b) are Raman's own applied
    doctrine, not merely "some authors"; branch (c) is still only attributed,
    and it is redundant anyway (above).

    Why the earlier pass concluded a printed page was needed: it searched for
    "Kemadruma" and these two passages are OCR'd as "Kemadiuma" and
    "Kemidiumi s". A spelling-tolerant search finds exactly six mentions in the
    whole book — :2170, :2173, :2185, :2255, :2263, :2266 — and the last three
    are the ones that settle it.

    The extended benefic-drishti branch is still NOT Raman's; he states it
    nowhere in 3HC, and the label stays NOT-3HC. Unlike (c) it is not provably
    redundant — Jupiter in the 5th or 9th from the Moon aspects it from outside
    every kendra — though across the 225 golden charts it never once supplies a
    cancellation that (a) or (b) had not already made.
    """
    if "Moon" not in chart.planets:
        return False
    moon_h = chart.planets["Moon"].rasi_house
    # (a) the Moon itself in a kendra from the Lagna
    if moon_h in _KENDRA:
        return True
    for name, pl in chart.planets.items():
        if name in ("Moon", "Rahu", "Ketu"):
            continue
        # (a) planet in a kendra from birth (Lagna)
        if pl.rasi_house in _KENDRA:
            return True
        # (b) planet in a kendra from the Moon
        if _in_kendra_from(name, moon_h, chart):
            return True
        # (c) the Moon in conjunction with a planet (same rasi)
        if pl.rasi_house == moon_h:
            return True
    # EXTENDED (not 3HC:2182-2185): a benefic aspecting the Moon breaks kemadruma
    for name in NATURAL_BENEFICS:
        if name != "Moon" and drishti.aspects_planet(name, "Moon", chart):
            return True
    return False
