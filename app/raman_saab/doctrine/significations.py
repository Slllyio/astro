"""Per-house signification→karaka routing table for the Raman Saab engine.

Each ``Signification`` encodes one sub-matter of a Bhava (e.g. H4 mother, H7 spouse)
together with:
  - its primary karaka and optional secondary karakas
  - per-karaka Shadbala weights for multi-karaka houses (H4, H9, H10)
  - the ``alternate_frame_core`` / ``derived_lagna`` needed for karaka-as-Lagna frames
    (methodology overview §6.2 — Matru-Sthana-as-Lagna for H4 mother; Venus-as-Lagna
    for H7 spouse, etc.)
  - a ``Citation`` pointing to the exact HTJAH-I/II line that establishes this routing
  - ``rule_tags`` linking to the matching ``signification=`` buckets in rule_sets/

Data source:
  ``docs/raman_saab/methodology/house_NN_*.md`` for all 12 houses.
  Citations are HTJAH-I (houses 1-6) and HTJAH-II (houses 7-12).

Usage:
    from app.raman_saab.doctrine.significations import (
        SIGNIFICATIONS, significations_of, karaka_for
    )
    sigs = significations_of(4)          # all H4 sub-matters
    k = karaka_for(4, "mother")          # "Moon"
    k = karaka_for(4, "happiness")       # "Jupiter"
    k = karaka_for(4, "unknown_key")     # falls back to BHAVA_KARAKA[4] = "Moon"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.doctrine.sources import Citation

# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Signification:
    """One sub-matter of a Bhava with its karaka routing and citation.

    Fields
    ------
    key : str
        Snake_case identifier for the sub-matter (e.g. ``"mother"``, ``"spouse"``).
    house : int
        Bhava number 1-12.
    primary_karaka : str
        The single most important significator for this sub-matter (title-case).
    secondary_karakas : tuple[str, ...]
        Additional significators in priority order (empty for single-karaka matters).
    karaka_weights : tuple[float, ...]
        Relative Shadbala weights for multi-karaka routing (parallel to
        ``(primary_karaka,) + secondary_karakas``). Empty tuple = equal weight.
    alternate_frame_core : str | None
        Planet to treat as the Lagna for the karaka-as-Lagna frame (e.g. ``"Moon"``
        for H4 mother longevity). ``None`` when this frame is not invoked.
    derived_lagna : str | None
        Label for the derived frame: ``"karaka"`` = treat alternate_frame_core as a
        rising sign; ``None`` = no special frame.
    rule_tags : tuple[str, ...]
        ``signification=`` bucket names in rule_sets/ that encode rules for this
        sub-matter. Must be a subset of the real values found in rule_sets/house_*.py.
    source : Citation
        The HTJAH-I/II line that explicitly names this karaka for this sub-matter.
    """
    key: str
    house: int
    primary_karaka: str
    secondary_karakas: tuple[str, ...] = field(default_factory=tuple)
    karaka_weights: tuple[float, ...] = field(default_factory=tuple)
    alternate_frame_core: str | None = None
    derived_lagna: str | None = None
    rule_tags: tuple[str, ...] = field(default_factory=tuple)
    source: Citation = field(default_factory=lambda: Citation("HTJAH-I", 1))


# ---------------------------------------------------------------------------
# Helper aliases for brevity
# ---------------------------------------------------------------------------

def _c1(line: int) -> Citation:
    """HTJAH-I citation."""
    return Citation("HTJAH-I", line)


def _c2(line: int) -> Citation:
    """HTJAH-II citation."""
    return Citation("HTJAH-II", line)


# ---------------------------------------------------------------------------
# House 1 — Lagna / Tanu Bhava
# Primary karaka: Sun (Thanu-Karaka, body/vitality)   HTJAH-I:992
# ---------------------------------------------------------------------------

_H1: tuple[Signification, ...] = (
    Signification(
        key="self",
        house=1,
        primary_karaka="Sun",
        rule_tags=("self",),
        source=_c1(992),
    ),
    Signification(
        key="body",
        house=1,
        primary_karaka="Sun",
        rule_tags=("self",),
        source=_c1(991),
    ),
    Signification(
        key="health",
        house=1,
        primary_karaka="Sun",
        rule_tags=("self",),
        source=_c1(983),
    ),
)

# ---------------------------------------------------------------------------
# House 2 — Dhana Bhava
# Primary karaka: Jupiter (Dhana-Karaka)        HTJAH-I:2754
# Secondary: Mercury (speech/literary gift)      HTJAH-I:2734
# ---------------------------------------------------------------------------

_H2: tuple[Signification, ...] = (
    Signification(
        key="wealth",
        house=2,
        primary_karaka="Jupiter",
        rule_tags=("wealth",),
        source=_c1(2754),
    ),
    Signification(
        key="family",
        house=2,
        primary_karaka="Jupiter",
        rule_tags=("wealth", "family"),     # own rules + the general 2nd-house testimony
        source=_c1(2316),
    ),
    Signification(
        key="speech",
        house=2,
        primary_karaka="Jupiter",
        secondary_karakas=("Mercury",),
        rule_tags=("wealth", "speech"),
        source=_c1(2316),
    ),
    Signification(
        key="vision",
        house=2,
        primary_karaka="Jupiter",  # Netra-Karaka per HTJAH-I:2734
        rule_tags=("wealth", "vision"),
        source=_c1(2734),
    ),
)

# ---------------------------------------------------------------------------
# House 3 — Sahaja Bhava
# Primary karaka: Mars (Bhratru-Karaka, siblings/courage)  HTJAH-I:3428
# ---------------------------------------------------------------------------

_H3: tuple[Signification, ...] = (
    Signification(
        key="siblings",
        house=3,
        primary_karaka="Mars",
        rule_tags=("siblings",),
        source=_c1(3428),
    ),
    Signification(
        key="courage",
        house=3,
        primary_karaka="Mars",
        rule_tags=("siblings", "courage"),
        source=_c1(3324),
    ),
    Signification(
        key="short_journeys",
        house=3,
        primary_karaka="Mars",
        rule_tags=("siblings",),
        source=_c1(3324),
    ),
    # Throat / ears / deafness — a real 3rd-house karya (HTJAH-I:3325 "throat, ears
    # and father's death"); Mercury is the throat/speech significator (HTJAH-I:3466).
    # Routes the deafness combinations (#28/#29) and worked-charts 55/56/57.
    Signification(
        key="ear_throat",
        house=3,
        primary_karaka="Mercury",
        rule_tags=("ear_throat",),
        source=_c1(3325),
    ),
)

# ---------------------------------------------------------------------------
# House 4 — Sukha / Matru Bhava  (MULTI-KARAKA — dispatch by sub-matter)
#
# Sub-matter routing (HTJAH-I:4386-4388):
#   happiness    → Jupiter          HTJAH-I:4386
#   mother       → Moon             HTJAH-I:4387
#   education    → Jupiter (primary), Mercury (secondary)  HTJAH-I:4701-4702
#   vehicles     → Venus            HTJAH-I:4934
#   property     → Mars             HTJAH-I:4969-4970
#
# Mandatory karaka-as-Lagna frame for mother longevity:
#   alternate_frame_core="Moon", derived_lagna="karaka"   HTJAH-I:4395-4397
#   (treat 4th/Moon as mother's Lagna; judge 8th therefrom for her longevity)
# ---------------------------------------------------------------------------

_H4: tuple[Signification, ...] = (
    Signification(
        key="mother",
        house=4,
        primary_karaka="Moon",
        alternate_frame_core="Moon",
        derived_lagna="karaka",
        # Aggregate bridge (Stage-4 fine-tag): shared placements (mother_home) + own combos.
        rule_tags=("mother", "mother_home"),
        source=_c1(4387),
    ),
    Signification(
        key="happiness",
        house=4,
        primary_karaka="Jupiter",
        rule_tags=("happiness", "mother_home"),
        source=_c1(4386),
    ),
    Signification(
        key="education",
        house=4,
        primary_karaka="Jupiter",
        secondary_karakas=("Mercury",),
        karaka_weights=(0.65, 0.35),
        rule_tags=("education", "mother_home"),
        source=_c1(4701),
    ),
    Signification(
        key="vehicles",
        house=4,
        primary_karaka="Venus",
        rule_tags=("vehicles", "mother_home"),
        source=_c1(4934),
    ),
    Signification(
        key="property",
        house=4,
        primary_karaka="Mars",
        rule_tags=("property", "mother_home"),
        source=_c1(4969),
    ),
    Signification(
        key="home_comforts",
        house=4,
        primary_karaka="Moon",
        # No dedicated combos route to home_comforts; it aggregates the shared
        # placements only (keep the bare bridge — see test_rule_tags_match_existing_buckets).
        rule_tags=("mother_home",),
        source=_c1(4125),
    ),
)

# ---------------------------------------------------------------------------
# House 5 — Putra Bhava
# Primary karaka: Jupiter (Putra-Karaka, children/intellect)  HTJAH-I:5018
# ---------------------------------------------------------------------------

_H5: tuple[Signification, ...] = (
    Signification(
        key="children",
        house=5,
        primary_karaka="Jupiter",
        rule_tags=("children",),
        source=_c1(5018),
    ),
    Signification(
        key="intellect",
        house=5,
        primary_karaka="Jupiter",
        # Intellect aggregates only its OWN brain/intellect combos — NOT the shared
        # children placements. (Bridging to "children" would double-count Jupiter-in-5,
        # which is both H5.P.Jupiter [children placement] and H5.C.35 [intellect combo];
        # unlike H4/H8, "children" is a live matter, not a dedicated placement tag.)
        rule_tags=("intellect",),
        source=_c1(5012),
    ),
    Signification(
        key="poorvapunya",
        house=5,
        primary_karaka="Jupiter",
        rule_tags=("children",),
        source=_c1(5019),
    ),
)

# ---------------------------------------------------------------------------
# House 6 — Ari / Roga Bhava  (DUAL KARAKA)
# Mars = RogaKaraka (disease/enemies/accidents)   HTJAH-I:6667
# Saturn = AyushKaraka (disease longevity/debts)  HTJAH-I:6641
# ---------------------------------------------------------------------------

_H6: tuple[Signification, ...] = (
    Signification(
        key="enemies_disease",
        house=6,
        primary_karaka="Mars",
        secondary_karakas=("Saturn",),
        rule_tags=("enemies_disease",),
        source=_c1(5984),
    ),
    Signification(
        key="accidents",
        house=6,
        primary_karaka="Mars",
        rule_tags=("accidents", "enemies_disease"),
        source=_c1(6667),
    ),
    Signification(
        key="debts",
        house=6,
        primary_karaka="Saturn",
        rule_tags=("debts", "enemies_disease"),
        source=_c1(6641),
    ),
    Signification(
        key="enemies",
        house=6,
        primary_karaka="Mars",
        secondary_karakas=("Saturn",),
        rule_tags=("enemies", "enemies_disease"),
        source=_c1(5985),
    ),
    Signification(
        key="disease_chronic",
        house=6,
        primary_karaka="Saturn",
        rule_tags=("disease_chronic", "enemies_disease"),
        source=_c1(6187),
    ),
)

# ---------------------------------------------------------------------------
# House 7 — Kalatra / Yuvati Bhava
# Primary karaka: Venus (Kalatra-Karaka)          HTJAH-II:225
# Mandatory karaka-as-Lagna frame for spouse quality/longevity:
#   alternate_frame_core="Venus", derived_lagna="karaka" HTJAH-II:374-376
# ---------------------------------------------------------------------------

_H7: tuple[Signification, ...] = (
    Signification(
        key="spouse",
        house=7,
        primary_karaka="Venus",
        alternate_frame_core="Venus",
        derived_lagna="karaka",
        rule_tags=("spouse", "marital_happiness"),
        source=_c2(225),
    ),
    Signification(
        key="marital_happiness",
        house=7,
        primary_karaka="Venus",
        alternate_frame_core="Venus",
        derived_lagna="karaka",
        rule_tags=("marital_happiness",),
        source=_c2(200),
    ),
    Signification(
        key="virility",
        house=7,
        primary_karaka="Venus",
        rule_tags=("virility",),
        source=_c2(415),
    ),
    Signification(
        key="coverture",
        house=7,
        primary_karaka="Venus",
        rule_tags=("coverture",),
        source=_c2(2047),
    ),
    Signification(
        key="wealth_through_marriage",
        house=7,
        primary_karaka="Venus",
        rule_tags=("wealth_through_marriage",),
        source=_c2(244),
    ),
    Signification(
        key="partnership",
        house=7,
        primary_karaka="Venus",
        rule_tags=("spouse",),
        source=_c2(535),
    ),
)

# ---------------------------------------------------------------------------
# House 8 — Ayur / Randhra / Mrityu Bhava
# Primary karaka: Saturn (AyushKaraka + MrutyuKaraka dual role)  HTJAH-II:4606
# ---------------------------------------------------------------------------

_H8: tuple[Signification, ...] = (
    Signification(
        key="longevity",
        house=8,
        primary_karaka="Saturn",
        rule_tags=("longevity",),
        source=_c2(4606),
    ),
    Signification(
        key="death",
        house=8,
        primary_karaka="Saturn",
        # Aggregate bridge: the death matter pulls the shared longevity placements
        # AND its own manner/cause/place-of-death combinations (signification="death").
        # Both still LONGEVITY_GUARD-clamped (key=="death" and "longevity" in tags).
        rule_tags=("longevity", "death"),
        source=_c2(2886),
    ),
    Signification(
        key="legacies",
        house=8,
        primary_karaka="Saturn",
        # Re-tagged off the "longevity" bridge (Stage-4 H8): legacies/inheritance is
        # a NON-death matter, so it must NOT trip LONGEVITY_GUARD — the combination
        # layer (H8.C.28/30/31) needs to move its verdict. HTJAH-II:2886 ("legacies,
        # gifts and unearned wealth").
        rule_tags=("legacies",),
        source=_c2(2886),
    ),
    Signification(
        key="sudden_gains",
        house=8,
        primary_karaka="Saturn",
        # Re-tagged off "longevity" (Stage-4 H8): sudden gains is a non-death matter
        # (H8.C.29/32 speculation + 8th-lord-in-10th). HTJAH-II:3068 ("the 8th
        # signifies sudden gains of money").
        rule_tags=("sudden_gains",),
        source=_c2(3068),
    ),
)

# ---------------------------------------------------------------------------
# House 9 — Bhagya / Dharma / Pitru Bhava  (DUAL KARAKA)
#
# Sub-matter routing (HTJAH-II:7291-7292):
#   father       → Sun  (PitruKaraka)      HTJAH-II:7291-7292
#   fortune      → Jupiter                 HTJAH-II:7481-7482
#   dharma       → Jupiter                 HTJAH-II:7285
#
# Mandatory karaka-as-Lagna frame for father:
#   alternate_frame_core="Sun"  — judge maraka houses from Sun  HTJAH-II:7916-7917
# ---------------------------------------------------------------------------

_H9: tuple[Signification, ...] = (
    Signification(
        key="father",
        house=9,
        primary_karaka="Sun",
        alternate_frame_core="Sun",
        derived_lagna="karaka",
        rule_tags=("father", "fortune"),
        source=_c2(7291),
    ),
    Signification(
        key="fortune",
        house=9,
        primary_karaka="Jupiter",
        secondary_karakas=("Venus",),
        rule_tags=("fortune",),
        source=_c2(7481),
    ),
    Signification(
        key="dharma",
        house=9,
        primary_karaka="Jupiter",
        rule_tags=("dharma", "fortune"),
        source=_c2(7285),
    ),
    Signification(
        key="higher_learning",
        house=9,
        primary_karaka="Jupiter",
        secondary_karakas=("Mercury",),
        rule_tags=("higher_learning", "fortune"),
        source=_c2(7499),
    ),
    Signification(
        key="long_journeys",
        house=9,
        primary_karaka="Jupiter",
        rule_tags=("long_journeys", "fortune"),
        source=_c2(7287),
    ),
)

# ---------------------------------------------------------------------------
# House 10 — Karma / Rajya Bhava  (QUAD KARAKA — profession routing)
#
# Four karma-karakas dispatched by matter (HTJAH-II:9446-9452):
#   Sun       → authority/government                HTJAH-II:9620-9622
#   Mercury   → trade/commerce/documentation        HTJAH-II:9589-9593
#   Jupiter   → learned/intellectual avocations     HTJAH-II:9671-9672
#   Saturn    → labour/industry/humble professions  HTJAH-II:9673-9674
#
# alternate_frame_core="Sun" (primary karma-karaka for authority/status)
# karaka_weights encode Raman's descending usage frequency across examples
# ---------------------------------------------------------------------------

_H10: tuple[Signification, ...] = (
    Signification(
        key="career",
        house=10,
        primary_karaka="Sun",
        secondary_karakas=("Mercury", "Jupiter", "Saturn"),
        karaka_weights=(0.35, 0.25, 0.25, 0.15),
        alternate_frame_core="Sun",
        rule_tags=("career",),
        source=_c2(9620),
    ),
    Signification(
        key="profession_authority",
        house=10,
        primary_karaka="Sun",
        rule_tags=("career",),
        source=_c2(9622),
    ),
    Signification(
        key="profession_trade",
        house=10,
        primary_karaka="Mercury",
        # Aggregate bridge: career placements + own nature-of-profession combos.
        rule_tags=("career", "profession_trade"),
        source=_c2(9689),
    ),
    Signification(
        key="profession_learned",
        house=10,
        primary_karaka="Jupiter",
        rule_tags=("career", "profession_learned"),
        source=_c2(9860),
    ),
    Signification(
        key="profession_labour",
        house=10,
        primary_karaka="Saturn",
        rule_tags=("career",),
        source=_c2(10267),
    ),
    Signification(
        key="status_honour",
        house=10,
        primary_karaka="Sun",
        # Aggregate bridge: career placements + own Rajayoga/dishonour/vice combos.
        rule_tags=("career", "status_honour"),
        source=_c2(9442),
    ),
)

# ---------------------------------------------------------------------------
# House 11 — Labha / Aya Bhava
# Primary karaka: Jupiter (Dhanakaraka for gains)   HTJAH-II:15155
# Secondary: Mars (karaka for elder brothers per Vaidyanatha Dikshitar)
#            HTJAH-II:14742-14744
# ---------------------------------------------------------------------------

_H11: tuple[Signification, ...] = (
    Signification(
        key="gains",
        house=11,
        primary_karaka="Jupiter",
        rule_tags=("gains",),
        source=_c2(15155),
    ),
    Signification(
        key="elder_siblings",
        house=11,
        primary_karaka="Jupiter",
        secondary_karakas=("Mars",),
        rule_tags=("elder_siblings", "gains"),
        source=_c2(14742),
    ),
    Signification(
        key="friends",
        house=11,
        primary_karaka="Jupiter",
        rule_tags=("gains",),
        source=_c2(14236),
    ),
    Signification(
        key="acquisitions",
        house=11,
        primary_karaka="Jupiter",
        rule_tags=("gains",),
        source=_c2(15151),
    ),
)

# ---------------------------------------------------------------------------
# House 12 — Vyaya / Moksha Bhava
# Primary karaka: Saturn (loss/sorrow/after-life/renunciation)  HTJAH-II:16667-16669
# Ketu = kaivalya/moksha karaka (via karakamsa, Jaimini overlay) HTJAH-II:16527
# ---------------------------------------------------------------------------

_H12: tuple[Signification, ...] = (
    Signification(
        key="loss_moksha",
        house=12,
        primary_karaka="Saturn",
        rule_tags=("loss_moksha",),
        source=_c2(16667),
    ),
    Signification(
        key="expenditure",
        house=12,
        primary_karaka="Saturn",
        rule_tags=("expenditure", "loss_moksha"),
        source=_c2(16250),
    ),
    Signification(
        key="foreign_residence",
        house=12,
        primary_karaka="Saturn",
        rule_tags=("foreign_residence", "loss_moksha"),
        source=_c2(16134),
    ),
    Signification(
        key="moksha",
        house=12,
        primary_karaka="Saturn",  # Saturn = karaka of renunciation/emancipation
        rule_tags=("moksha", "loss_moksha"),
        source=_c2(16669),
    ),
    Signification(
        key="incarceration",
        house=12,
        primary_karaka="Saturn",
        rule_tags=("incarceration", "loss_moksha"),
        source=_c2(16426),
    ),
    Signification(
        key="left_eye",
        house=12,
        primary_karaka="Venus",
        secondary_karakas=("Moon",),
        rule_tags=("left_eye", "loss_moksha"),
        source=_c2(16456),
    ),
)


# ---------------------------------------------------------------------------
# Master lookup
# ---------------------------------------------------------------------------

SIGNIFICATIONS: Final[dict[int, tuple[Signification, ...]]] = {
    1: _H1,
    2: _H2,
    3: _H3,
    4: _H4,
    5: _H5,
    6: _H6,
    7: _H7,
    8: _H8,
    9: _H9,
    10: _H10,
    11: _H11,
    12: _H12,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def significations_of(house: int) -> tuple[Signification, ...]:
    """Return all Signification records for *house* (1-12).

    Returns an empty tuple for an unknown house number; callers should not
    receive a ``KeyError`` from engine routing code.
    """
    return SIGNIFICATIONS.get(house, ())


def karaka_for(house: int, key: str) -> str:
    """Return the primary karaka planet name for a specific sub-matter.

    Looks up *key* in the Signification records for *house*; falls back to
    ``BHAVA_KARAKA[house]`` if not found.

    Examples
    --------
    >>> karaka_for(4, "mother")
    'Moon'
    >>> karaka_for(4, "education")
    'Jupiter'
    >>> karaka_for(4, "happiness")
    'Jupiter'
    >>> karaka_for(7, "spouse")
    'Venus'
    """
    for sig in significations_of(house):
        if sig.key == key:
            return sig.primary_karaka
    return BHAVA_KARAKA.get(house, "Sun")
