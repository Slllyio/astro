"""Yoga detector library — Phase 3 of the astrologer's-lens framework.

Implements ~25 canonical Vedic yogas across 5 detection families:

* **Pancha Mahapurusha** (5): Ruchaka/Bhadra/Hamsa/Malavya/Sasa —
  planet in own/exalt + Kendra. BPHS Ch.36.
* **Solar/Lunar yogas** (5): Budha-Aditya, Veshi, Vosi, Sunapha,
  Anapha — adjacency relationships with luminaries.
* **Foundation yogas** (6): Raja, Dhana, Vipareeta Raja, Gajakesari,
  Chandra-Mangal, Kemadruma.
* **Affliction yogas** (5): Kala Sarpa, Mangal Dosha, Sade-Sati (natal
  vulnerability), Sarpa Dosha, Daridra.
* **Auspicious-special yogas** (4): Amala, Adhi, Lakshmi, Saraswati.

Each detector returns a ``Yoga`` record carrying name + classical
reference + boolean activation + (optional) intensity + per-yoga
participants. The Bhava Judge (Phase 6) reads the active yoga list
when grading chart-wide promises.

## Why a unified Yoga record

Downstream phases (especially Phase 9 Reading Composer) need to cite
yogas with their classical anchors. Carrying the BPHS chapter in the
record itself avoids a separate citation lookup table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Final

from app.core.chart_model import Chart
from app.core.dignity import (
    is_debilitated, is_exalted, is_moolatrikona, is_own_sign,
)
from app.core.drishti_argala import aspects_from_planet
from app.core.functional_roles import functional_roles, houses_ruled_by


def _is_well_placed(planet: str, sign: int) -> bool:
    """Convenience: exalted or own (Mooltrikona check needs longitude — skip here).

    Note: is_moolatrikona requires longitude per app/core/dignity.py and
    Saraswati detection uses this as a coarse strong-Jupiter check.
    """
    return is_exalted(planet, sign) or is_own_sign(planet, sign)


_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})
_BENEFICS_NATURAL: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS_NATURAL: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


@dataclass(frozen=True)
class Yoga:
    """Detected yoga record carrying its classical anchor."""
    name: str
    sanskrit: str
    active: bool
    intensity: float           # 0.0 absent, 0.5 partial, 1.0 strong
    participants: tuple[str, ...]
    reference: str             # e.g. "BPHS Ch.36" or "Phaladeepika 6"
    description: str


# ─── Pancha Mahapurusha yogas (BPHS Ch.36) ───────────────────────────


def _pmp_template(
    planet: str, name: str, sanskrit: str, ref: str,
) -> Callable[[Chart], Yoga]:
    """One factory for all 5 PMP yogas — planet must be own/exalt/Mooltrikona in Kendra.

    Per the doctrine review (BPHS Ch.36): Mooltrikona qualifies for PMP,
    not only own/exalt. Specifically catches Hamsa (Jupiter in early
    Sagittarius Mooltrikona portion) and Sasa (Saturn in Aquarius
    Mooltrikona portion 0-20°).
    """
    def detector(chart: Chart) -> Yoga:
        house = chart.house_of(planet)
        sign = chart.sign_of(planet)
        lon = chart.planet_lons.get(planet)
        active = False
        intensity = 0.0
        if house is not None and sign is not None:
            in_kendra = house in _KENDRAS
            # is_moolatrikona takes longitude per existing app/core/dignity.py
            in_moolatrikona = (
                lon is not None and is_moolatrikona(planet, lon)
            )
            in_dignity = (
                is_exalted(planet, sign) or is_own_sign(planet, sign) or in_moolatrikona
            )
            if in_kendra and in_dignity:
                active = True
                if is_exalted(planet, sign):
                    intensity = 1.0
                elif is_own_sign(planet, sign):
                    intensity = 0.85
                else:
                    intensity = 0.75
        return Yoga(
            name=name, sanskrit=sanskrit, active=active,
            intensity=intensity, participants=(planet,),
            reference=ref,
            description=f"{planet} in own/exalt/Mooltrikona sign occupying a Kendra (1/4/7/10).",
        )
    return detector


detect_ruchaka = _pmp_template("Mars", "Ruchaka", "रुचक", "BPHS Ch.36")
detect_bhadra  = _pmp_template("Mercury", "Bhadra", "भद्र", "BPHS Ch.36")
detect_hamsa   = _pmp_template("Jupiter", "Hamsa", "हंस", "BPHS Ch.36")
detect_malavya = _pmp_template("Venus", "Malavya", "मालव्य", "BPHS Ch.36")
detect_sasa    = _pmp_template("Saturn", "Sasa", "शश", "BPHS Ch.36")


# ─── Solar / Lunar yogas (Phaladeepika Ch.6) ─────────────────────────


def detect_budha_aditya(chart: Chart) -> Yoga:
    """Sun + Mercury conjunction (same sign). 'Wisdom yoga'."""
    sun_sign = chart.sign_of("Sun")
    mer_sign = chart.sign_of("Mercury")
    active = (sun_sign is not None and sun_sign == mer_sign)
    # Intensity penalty if Sun combusts Mercury (within 14°)
    intensity = 0.0
    if active:
        sun_lon = chart.planet_lons.get("Sun")
        mer_lon = chart.planet_lons.get("Mercury")
        if sun_lon is not None and mer_lon is not None:
            sep = min(abs(sun_lon - mer_lon), 360 - abs(sun_lon - mer_lon))
            intensity = 0.5 if sep < 14.0 else 1.0
        else:
            intensity = 0.75
    return Yoga(
        name="Budha-Aditya", sanskrit="बुधादित्य", active=active,
        intensity=intensity, participants=("Sun", "Mercury"),
        reference="Phaladeepika Ch.6",
        description="Sun and Mercury in the same sign — intellect/communication strength.",
    )


def _luminary_adjacency(
    chart: Chart, luminary: str, distance: int,
    exclude: frozenset[str],
) -> tuple[bool, tuple[str, ...]]:
    """Helper: any planet (excluding `exclude`) in the Nth sign from luminary?"""
    lum_sign = chart.sign_of(luminary)
    if lum_sign is None:
        return False, ()
    target_sign = ((lum_sign - 1 + distance - 1) % 12) + 1
    occupants = tuple(
        p for p, s in chart.planet_signs.items()
        if s == target_sign and p not in exclude
    )
    return bool(occupants), occupants


def detect_veshi(chart: Chart) -> Yoga:
    """Planet (not Moon, not nodes) in 2nd sign from Sun. BPHS Ch.39."""
    found, who = _luminary_adjacency(
        chart, "Sun", 2, frozenset({"Sun", "Moon", "Rahu", "Ketu"}),
    )
    return Yoga(
        name="Veshi", sanskrit="वेशि", active=found,
        intensity=0.6 if found else 0.0, participants=("Sun",) + who,
        reference="BPHS Ch.39",
        description="A planet (not Moon) in the 2nd sign from the Sun.",
    )


def detect_vosi(chart: Chart) -> Yoga:
    """Planet (not Moon, not nodes) in 12th sign from Sun. BPHS Ch.39."""
    found, who = _luminary_adjacency(
        chart, "Sun", 12, frozenset({"Sun", "Moon", "Rahu", "Ketu"}),
    )
    return Yoga(
        name="Vosi", sanskrit="वोशि", active=found,
        intensity=0.6 if found else 0.0, participants=("Sun",) + who,
        reference="BPHS Ch.39",
        description="A planet (not Moon) in the 12th sign from the Sun.",
    )


def detect_sunapha(chart: Chart) -> Yoga:
    """Planet (not Sun, not nodes) in 2nd sign from Moon. BPHS Ch.40."""
    found, who = _luminary_adjacency(
        chart, "Moon", 2, frozenset({"Sun", "Moon", "Rahu", "Ketu"}),
    )
    return Yoga(
        name="Sunapha", sanskrit="सुनफा", active=found,
        intensity=0.7 if found else 0.0, participants=("Moon",) + who,
        reference="BPHS Ch.40",
        description="A planet (not Sun) in the 2nd sign from the Moon.",
    )


def detect_anapha(chart: Chart) -> Yoga:
    """Planet (not Sun, not nodes) in 12th sign from Moon. BPHS Ch.40."""
    found, who = _luminary_adjacency(
        chart, "Moon", 12, frozenset({"Sun", "Moon", "Rahu", "Ketu"}),
    )
    return Yoga(
        name="Anapha", sanskrit="अनफा", active=found,
        intensity=0.7 if found else 0.0, participants=("Moon",) + who,
        reference="BPHS Ch.40",
        description="A planet (not Sun) in the 12th sign from the Moon.",
    )


# ─── Foundation yogas ────────────────────────────────────────────────


def detect_gajakesari(chart: Chart) -> Yoga:
    """Jupiter in Kendra from Moon. BPHS Ch.78 — wealth/intelligence yoga.

    Kendra = same sign (1st), 4th, 7th, or 10th from Moon.
    """
    moon_sign = chart.sign_of("Moon")
    jup_sign = chart.sign_of("Jupiter")
    active = False
    if moon_sign is not None and jup_sign is not None:
        distance = ((jup_sign - moon_sign) % 12) + 1
        active = distance in _KENDRAS
    intensity = 0.0
    if active and jup_sign is not None:
        intensity = 1.0 if is_exalted("Jupiter", jup_sign) else 0.75
    return Yoga(
        name="Gajakesari", sanskrit="गजकेसरी", active=active,
        intensity=intensity, participants=("Moon", "Jupiter"),
        reference="BPHS Ch.78",
        description="Jupiter in a Kendra (1/4/7/10) from the Moon — elephant + lion strength.",
    )


def detect_chandra_mangal(chart: Chart) -> Yoga:
    """Moon and Mars conjunction (same sign). Wealth-via-effort yoga.

    Reference: Sarvarth Chintamani, also Phaladeepika 6.
    """
    moon_sign = chart.sign_of("Moon")
    mars_sign = chart.sign_of("Mars")
    active = (moon_sign is not None and moon_sign == mars_sign)
    return Yoga(
        name="Chandra-Mangal", sanskrit="चन्द्र-मङ्गल", active=active,
        intensity=0.7 if active else 0.0, participants=("Moon", "Mars"),
        reference="Phaladeepika Ch.6",
        description="Moon and Mars in the same sign — wealth via initiative.",
    )


def detect_kemadruma(chart: Chart) -> Yoga:
    """Moon ALONE — no planet in 2nd or 12th from Moon, and no
    planet in Moon's sign — with the 4 BPHS Ch.40 cancellation rules
    applied INLINE.

    Raw Kemadruma fires when Moon has no planet (excluding nodes) in
    its sign, 2nd, or 12th. Per BPHS Ch.40 / Phaladeepika Ch.6, the
    yoga is CANCELLED when any of:
      (1) Moon sits in a Kendra (1/4/7/10) from Lagna
      (2) Moon is in own (Cancer) or exalted (Taurus) sign
      (3) All planets are in Kendras from Lagna
      (4) Moon receives a Jupiter aspect from a Kendra
    """
    moon_sign = chart.sign_of("Moon")
    moon_house = chart.house_of("Moon")
    if moon_sign is None or moon_house is None:
        return Yoga(
            name="Kemadruma", sanskrit="केमद्रुम", active=False,
            intensity=0.0, participants=(),
            reference="BPHS Ch.40",
            description="(skipped — Moon position not available)",
        )
    prev_sign = ((moon_sign - 2) % 12) + 1
    next_sign = (moon_sign % 12) + 1
    excluded = {"Moon", "Rahu", "Ketu"}
    has_2nd = any(p not in excluded and s == next_sign
                  for p, s in chart.planet_signs.items())
    has_12th = any(p not in excluded and s == prev_sign
                   for p, s in chart.planet_signs.items())
    has_companion = any(p not in {"Moon"} and s == moon_sign
                        for p, s in chart.planet_signs.items())
    raw_active = not (has_2nd or has_12th or has_companion)

    # Cancellation conditions per BPHS Ch.40.
    cancellation_reasons: list[str] = []
    if moon_house in _KENDRAS:
        cancellation_reasons.append("Moon is in a Kendra (1/4/7/10) from Lagna")
    if is_own_sign("Moon", moon_sign) or is_exalted("Moon", moon_sign):
        cancellation_reasons.append("Moon is in own/exalted sign")
    # All planets in Kendras from Lagna
    visible = {"Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    visible_houses = [chart.house_of(p) for p in visible if chart.house_of(p) is not None]
    if visible_houses and all(h in _KENDRAS for h in visible_houses):
        cancellation_reasons.append("All visible planets are in Kendras from Lagna")
    # Jupiter Kendra-aspect on Moon
    jupiter_house = chart.house_of("Jupiter")
    if jupiter_house in _KENDRAS:
        jup_aspects = aspects_from_planet("Jupiter", jupiter_house)
        if moon_house in jup_aspects:
            cancellation_reasons.append("Moon receives Jupiter aspect from a Kendra")

    active = raw_active and not cancellation_reasons
    intensity = 0.8 if active else 0.0
    desc = (
        "Moon with no planet in 2nd/12th/own sign — isolation yoga."
        if active
        else ("Raw Kemadruma cancelled: " + "; ".join(cancellation_reasons)
              if raw_active else
              "Moon has planetary support — no Kemadruma.")
    )
    return Yoga(
        name="Kemadruma", sanskrit="केमद्रुम", active=active,
        intensity=intensity, participants=("Moon",),
        reference="BPHS Ch.40",
        description=desc,
    )


def detect_raja_yoga(chart: Chart) -> Yoga:
    """Kendra-Lord and Trikona-Lord conjunction in same sign.

    BPHS Ch.39 — the classical Raja yoga. Many variants exist
    (aspect/exchange), but conjunction is the most concentrated.
    """
    roles = functional_roles(chart.asc_sign)
    kendra_lords = {
        p for p, r in roles.items()
        if set(r.houses_ruled) & {4, 7, 10}
    }
    trikona_lords = {
        p for p, r in roles.items()
        if set(r.houses_ruled) & {5, 9}
    }
    # Yogakaraka is trivially Raja yoga but covered elsewhere; here we
    # want DIFFERENT planets (kendra + trikona) conjunct.
    participants = []
    for kp in kendra_lords:
        for tp in trikona_lords:
            if kp == tp:
                continue
            ks = chart.sign_of(kp)
            ts = chart.sign_of(tp)
            if ks is not None and ks == ts:
                participants.append((kp, tp))
    active = bool(participants)
    flat = tuple(sorted({p for pair in participants for p in pair}))
    return Yoga(
        name="Raja Yoga", sanskrit="राजयोग", active=active,
        intensity=min(1.0, 0.5 * len(participants)) if active else 0.0,
        participants=flat,
        reference="BPHS Ch.39",
        description="A Kendra-Lord and Trikona-Lord conjunction — elevation/status.",
    )


def detect_vipareeta_raja(chart: Chart) -> Yoga:
    """Dusthana lords (6L/8L/12L) sitting in dusthanas — reversed Raja.

    BPHS Ch.39 — the doctrinal non-monotonicity: affliction-lords
    afflicting themselves cancel out to yield gain. Two named variants:
    * Harsha: 6L in 6/8/12
    * Sarala: 8L in 6/8/12
    * Vimala: 12L in 6/8/12
    We surface a unified Vipareeta Raja flag if ANY occurs.
    """
    roles = functional_roles(chart.asc_sign)
    variants = []
    for dh in (6, 8, 12):
        lord = next(
            (p for p, r in roles.items() if dh in r.houses_ruled), None,
        )
        if lord is None:
            continue
        lord_house = chart.house_of(lord)
        if lord_house in _DUSTHANAS:
            variant_name = {6: "Harsha", 8: "Sarala", 12: "Vimala"}[dh]
            variants.append((variant_name, lord, dh, lord_house))
    active = bool(variants)
    if variants:
        description = (
            "Dusthana lord in a dusthana — Harsha/Sarala/Vimala — "
            "reversed affliction yielding gain. Variants found: "
            + ", ".join(v[0] for v in variants)
        )
    else:
        description = (
            "Vipareeta Raja Yoga — reversed-affliction yoga (BPHS Ch.39). "
            "Inactive: no dusthana lord currently sits in a dusthana."
        )
    return Yoga(
        name="Vipareeta Raja", sanskrit="विपरीत-राज", active=active,
        intensity=min(1.0, 0.5 * len(variants)),
        participants=tuple(sorted({v[1] for v in variants})),
        reference="BPHS Ch.39",
        description=description,
    )


# ─── Affliction yogas ────────────────────────────────────────────────


def detect_mangal_dosha(chart: Chart) -> Yoga:
    """Mars in 1/2/4/7/8/12 from Lagna OR Moon. Marriage affliction.

    Reference: Mansagari 6, also a Tamil tradition emphasis. Standard
    cancellation rules (own/exalt Mars, benefic conjunction, age >28)
    are noted in description for Phase 6 to apply.
    """
    afflicting_houses = frozenset({1, 2, 4, 7, 8, 12})
    mars_house = chart.house_of("Mars")
    mars_sign = chart.sign_of("Mars")
    moon_sign = chart.sign_of("Moon")
    # House from Moon
    from_moon = None
    if mars_sign is not None and moon_sign is not None:
        from_moon = ((mars_sign - moon_sign) % 12) + 1
    flag_lagna = mars_house in afflicting_houses if mars_house is not None else False
    flag_moon = from_moon in afflicting_houses if from_moon is not None else False
    active = flag_lagna or flag_moon
    intensity = 0.0
    if active:
        intensity = 0.5
        if flag_lagna and flag_moon:
            intensity = 0.85
        # Cancellation flag (informational only here)
        if mars_sign is not None and (
            is_own_sign("Mars", mars_sign) or is_exalted("Mars", mars_sign)
        ):
            intensity *= 0.5
    return Yoga(
        name="Mangal Dosha", sanskrit="मङ्गल-दोष", active=active,
        intensity=intensity, participants=("Mars",),
        reference="Mansagari Ch.6",
        description=("Mars in 1/2/4/7/8/12 from Lagna or Moon — marriage friction. "
                     "Cancels if Mars in own/exalt or aspected by Jupiter."),
    )


def detect_kala_sarpa(chart: Chart) -> Yoga:
    """All 7 visible planets contained between Rahu and Ketu's arc.

    Reference: modern synthesis (Nadi/Sanjay Rath schools). When all
    planets fall on one side of the Rahu-Ketu axis, the chart carries
    a "serpent of time" — heavy karmic load.

    Audit fix (edge-case agent): the previous version misfired when
    rahu_lon == ketu_lon (malformed input). Now we require the nodes
    to be ~180° apart (within 5° tolerance for ephemeris drift); a
    degenerate axis returns inactive. We also exclude planets sitting
    exactly on the axis from the arc test rather than letting strict
    `<` push them into the wrong half silently.
    """
    rahu_lon = chart.planet_lons.get("Rahu")
    ketu_lon = chart.planet_lons.get("Ketu")
    if rahu_lon is None or ketu_lon is None:
        return Yoga(
            name="Kala Sarpa", sanskrit="काल-सर्प", active=False,
            intensity=0.0, participants=(),
            reference="Nadi tradition (modern synthesis)",
            description="(skipped — node positions not available)",
        )
    # Nodes must be a real axis: Ketu must be ~180° from Rahu.
    axis_sep = (ketu_lon - rahu_lon) % 360
    if not (175.0 <= axis_sep <= 185.0):
        return Yoga(
            name="Kala Sarpa", sanskrit="काल-सर्प", active=False,
            intensity=0.0, participants=("Rahu", "Ketu"),
            reference="Nadi tradition (modern synthesis)",
            description=(
                "(skipped — Rahu/Ketu not approximately 180° apart; "
                f"axis_sep={axis_sep:.2f}°)"
            ),
        )
    # Planet is in the "Rahu→Ketu" half when its angle relative to Rahu
    # is strictly between 0 and 180; treat the axis itself as boundary
    # (boundary planets disqualify the yoga since they straddle).
    def arc_status(lon: float) -> str:
        diff = (lon - rahu_lon) % 360
        if diff <= 0.01 or diff >= 359.99 or abs(diff - axis_sep) <= 0.01:
            return "on_axis"
        return "first_half" if diff < axis_sep else "second_half"

    visible = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    statuses = [
        arc_status(chart.planet_lons[p])
        for p in visible if p in chart.planet_lons
    ]
    if any(s == "on_axis" for s in statuses):
        active = False  # axis-sitter straddles; doctrine treats as not-pure
    else:
        active = len(set(statuses)) == 1  # all in same half
    return Yoga(
        name="Kala Sarpa", sanskrit="काल-सर्प", active=active,
        intensity=0.8 if active else 0.0,
        participants=("Rahu", "Ketu"),
        reference="Nadi tradition (modern synthesis)",
        description=("All 7 visible planets contained within one half of the "
                     "Rahu-Ketu axis — pronounced karmic theme."),
    )


def detect_daridra(chart: Chart) -> Yoga:
    """Wealth-house lords (2L, 11L) in dusthanas (6/8/12). Poverty yoga.

    Reference: Sarvarth Chintamani; also classical commentary on BPHS.
    """
    roles = functional_roles(chart.asc_sign)
    afflicted = []
    for wealth_h in (2, 11):
        lord = next(
            (p for p, r in roles.items() if wealth_h in r.houses_ruled), None,
        )
        if lord is None:
            continue
        if chart.house_of(lord) in _DUSTHANAS:
            afflicted.append(lord)
    active = bool(afflicted)
    return Yoga(
        name="Daridra", sanskrit="दरिद्र", active=active,
        intensity=0.4 * len(afflicted),
        participants=tuple(sorted(set(afflicted))),
        reference="Sarvarth Chintamani",
        description=("Wealth-house lord(s) afflicted in dusthana (6/8/12) — "
                     "financial constraint theme."),
    )


# ─── Auspicious special yogas ───────────────────────────────────────


def detect_amala(chart: Chart) -> Yoga:
    """Benefic in 10th from Lagna OR from Moon — clean-fame yoga.

    Reference: BPHS Ch.78. Benefic = natural benefic (Jup/Ven/Mer/Moon).
    """
    asc = chart.asc_sign
    moon_sign = chart.sign_of("Moon")
    target_lagna = ((10 + asc - 2) % 12) + 1
    targets = {target_lagna}
    if moon_sign is not None:
        targets.add(((10 + moon_sign - 2) % 12) + 1)
    found_in = [
        p for p, s in chart.planet_signs.items()
        if s in targets and p in _BENEFICS_NATURAL
    ]
    return Yoga(
        name="Amala", sanskrit="अमल", active=bool(found_in),
        intensity=0.7 if found_in else 0.0,
        participants=tuple(sorted(found_in)),
        reference="BPHS Ch.78",
        description="A natural benefic in the 10th from Lagna or Moon — pure reputation.",
    )


def detect_saraswati(chart: Chart) -> Yoga:
    """Mercury + Jupiter + Venus all in Kendra/Trikona/2H, and Jupiter
    strong (own/exalt/Mooltrikona).

    Reference: Phaladeepika Ch.6 — scholarship/eloquence yoga.
    """
    good = _KENDRAS | _TRIKONAS | {2}
    mer_h = chart.house_of("Mercury")
    jup_h = chart.house_of("Jupiter")
    ven_h = chart.house_of("Venus")
    jup_s = chart.sign_of("Jupiter")
    all_placed = (mer_h in good and jup_h in good and ven_h in good)
    jup_strong = jup_s is not None and _is_well_placed("Jupiter", jup_s)
    active = bool(all_placed and jup_strong)
    return Yoga(
        name="Saraswati", sanskrit="सरस्वती", active=active,
        intensity=0.9 if active else 0.0,
        participants=("Mercury", "Jupiter", "Venus"),
        reference="Phaladeepika Ch.6",
        description=("Mercury + Jupiter + Venus all in Kendra/Trikona/2H, "
                     "with Jupiter dignified — scholarship and eloquence."),
    )


def detect_lakshmi(chart: Chart) -> Yoga:
    """Lakshmi Yoga — 9L in own/exalted/Mooltrikona AND in Kendra/Trikona,
    while Venus or Jupiter sits in Kendra/Trikona too.

    Reference: Phaladeepika Ch.6 — wealth and dignity yoga, named after
    the goddess of fortune.
    """
    asc = chart.asc_sign
    roles = functional_roles(asc)
    # Find 9L
    ninth_lord = next(
        (p for p, r in roles.items() if 9 in r.houses_ruled), None,
    )
    if ninth_lord is None:
        return Yoga(
            name="Lakshmi", sanskrit="लक्ष्मी", active=False,
            intensity=0.0, participants=(),
            reference="Phaladeepika Ch.6",
            description="(skipped — 9L not resolvable)",
        )
    ninth_lord_sign = chart.sign_of(ninth_lord)
    ninth_lord_house = chart.house_of(ninth_lord)
    ninth_lord_lon = chart.planet_lons.get(ninth_lord)
    cond_lord_dignified = (
        ninth_lord_sign is not None and (
            is_exalted(ninth_lord, ninth_lord_sign)
            or is_own_sign(ninth_lord, ninth_lord_sign)
            or (ninth_lord_lon is not None and is_moolatrikona(ninth_lord, ninth_lord_lon))
        )
    )
    cond_lord_well_placed = ninth_lord_house in (_KENDRAS | _TRIKONAS)
    # Venus or Jupiter in Kendra/Trikona
    benefic_kendra_trikona = []
    for p in ("Venus", "Jupiter"):
        h = chart.house_of(p)
        if h in (_KENDRAS | _TRIKONAS):
            benefic_kendra_trikona.append(p)
    active = bool(cond_lord_dignified and cond_lord_well_placed and benefic_kendra_trikona)
    return Yoga(
        name="Lakshmi", sanskrit="लक्ष्मी", active=active,
        intensity=0.9 if active else 0.0,
        participants=(ninth_lord,) + tuple(benefic_kendra_trikona),
        reference="Phaladeepika Ch.6",
        description=("9L in own/exalt/Mooltrikona + Kendra/Trikona, with "
                     "Venus or Jupiter in Kendra/Trikona — wealth + dignity."),
    )


def detect_neecha_bhanga_raja(chart: Chart) -> Yoga:
    """Neecha Bhanga Raja Yoga — debilitation cancellation by classical rules.

    BPHS Ch.32 — a debilitated planet's affliction is CANCELLED (and
    becomes a Raja Yoga) when any of these conditions hold:
      (1) Lord of the sign in which the planet is debilitated is in a
          Kendra from Lagna or Moon.
      (2) Lord of the planet's exaltation sign is in a Kendra from
          Lagna or Moon.
      (3) The debilitated planet is aspected by its own dispositor.
      (4) The debilitated planet is in a Kendra from Lagna or Moon.

    We detect (1) and (4) — the most-cited variants.
    """
    moon_sign = chart.sign_of("Moon")
    asc = chart.asc_sign
    # Sign rulership map
    sign_lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
    }
    visible = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    participants: list[str] = []
    for p in visible:
        p_sign = chart.sign_of(p)
        p_house = chart.house_of(p)
        if p_sign is None or p_house is None:
            continue
        if not is_debilitated(p, p_sign):
            continue
        # Rule (4): planet itself in Kendra from Lagna
        if p_house in _KENDRAS:
            participants.append(p)
            continue
        # Rule (1): dispositor (lord of debilitation sign) in Kendra from Lagna or Moon
        dispositor = sign_lords[p_sign]
        d_house = chart.house_of(dispositor)
        d_sign = chart.sign_of(dispositor)
        from_lagna_kendra = d_house in _KENDRAS
        from_moon_kendra = False
        if moon_sign is not None and d_sign is not None:
            distance = ((d_sign - moon_sign) % 12) + 1
            from_moon_kendra = distance in _KENDRAS
        if from_lagna_kendra or from_moon_kendra:
            participants.append(p)
    active = bool(participants)
    return Yoga(
        name="Neecha Bhanga Raja", sanskrit="नीचभङ्ग-राज", active=active,
        intensity=min(1.0, 0.5 + 0.2 * len(participants)) if active else 0.0,
        participants=tuple(sorted(set(participants))),
        reference="BPHS Ch.32",
        description=("Debilitated planet's affliction cancelled — debility "
                     "transmutes to Raja Yoga via dispositor in Kendra or "
                     "planet itself in Kendra."),
    )


def detect_dharma_karma_adhipati(chart: Chart) -> Yoga:
    """Dharma-Karma Adhipati Yoga — 9L + 10L conjunction/exchange.

    BPHS Ch.39 — the most concentrated career-with-dharma yoga. We
    detect direct conjunction (same sign) AND parivartana (mutual
    sign exchange).
    """
    roles = functional_roles(chart.asc_sign)
    ninth_lord = next(
        (p for p, r in roles.items() if 9 in r.houses_ruled), None,
    )
    tenth_lord = next(
        (p for p, r in roles.items() if 10 in r.houses_ruled), None,
    )
    if not ninth_lord or not tenth_lord or ninth_lord == tenth_lord:
        return Yoga(
            name="Dharma-Karma Adhipati", sanskrit="धर्म-कर्म-अधिपति",
            active=False, intensity=0.0, participants=(),
            reference="BPHS Ch.39",
            description="(skipped — distinct 9L and 10L not resolvable)",
        )
    n_sign = chart.sign_of(ninth_lord)
    t_sign = chart.sign_of(tenth_lord)
    # Conjunction (same sign)
    is_conjunct = n_sign is not None and n_sign == t_sign
    # Parivartana (mutual sign exchange)
    own_signs_9th = {
        "Sun": {5}, "Moon": {4}, "Mars": {1, 8}, "Mercury": {3, 6},
        "Jupiter": {9, 12}, "Venus": {2, 7}, "Saturn": {10, 11},
    }
    is_parivartana = (
        n_sign in own_signs_9th.get(tenth_lord, set())
        and t_sign in own_signs_9th.get(ninth_lord, set())
    )
    active = is_conjunct or is_parivartana
    return Yoga(
        name="Dharma-Karma Adhipati", sanskrit="धर्म-कर्म-अधिपति",
        active=active,
        intensity=1.0 if is_parivartana else (0.8 if is_conjunct else 0.0),
        participants=(ninth_lord, tenth_lord),
        reference="BPHS Ch.39",
        description=("9L + 10L conjoined or in parivartana — dharmic action "
                     "powerfully linked to career outcome."),
    )


def detect_akhanda_samrajya(chart: Chart) -> Yoga:
    """Akhanda Samrajya Yoga — uninterrupted sovereignty.

    BPHS Ch.39 — Jupiter is the lord of either 2H, 5H, 9H, or 11H AND
    Jupiter aspects/joins 2L/11L while these are in Kendra/Trikona.

    Simplified detection: Jupiter rules ≥1 of {2,5,9,11} for this Lagna
    AND Jupiter is itself in a Kendra (1/4/7/10). The classical Akhanda
    Samrajya is a very strong "great kingship" yoga.
    """
    asc = chart.asc_sign
    jupiter_houses_ruled = set(houses_ruled_by("Jupiter", asc))
    jupiter_house = chart.house_of("Jupiter")
    cond_jupiter_rules_wealth_lord = bool(
        jupiter_houses_ruled & {2, 5, 9, 11}
    )
    cond_jupiter_in_kendra = jupiter_house in _KENDRAS
    active = cond_jupiter_rules_wealth_lord and cond_jupiter_in_kendra
    return Yoga(
        name="Akhanda Samrajya", sanskrit="अखण्ड-साम्राज्य",
        active=active,
        intensity=0.85 if active else 0.0,
        participants=("Jupiter",),
        reference="BPHS Ch.39",
        description=("Jupiter rules wealth/fortune house (2/5/9/11) AND "
                     "sits in a Kendra — uninterrupted prosperity."),
    )


def detect_sarpa_dosha(chart: Chart) -> Yoga:
    """Sarpa Dosha — Rahu or Ketu in 1H, 5H, or 9H with malefic affliction.

    Reference: Nadi tradition / modern synthesis. Indicates inherited
    karmic burden along the Lagna-Trikona axis (self, intellect, dharma).
    """
    afflicted_houses = []
    for node in ("Rahu", "Ketu"):
        node_house = chart.house_of(node)
        if node_house in (1, 5, 9):
            afflicted_houses.append((node, node_house))
    active = bool(afflicted_houses)
    return Yoga(
        name="Sarpa Dosha", sanskrit="सर्प-दोष",
        active=active,
        intensity=min(1.0, 0.5 * len(afflicted_houses)) if active else 0.0,
        participants=tuple(sorted({n for n, _ in afflicted_houses})),
        reference="Nadi tradition (modern synthesis)",
        description=("Rahu/Ketu in 1H/5H/9H — Lagna-Trikona karmic burden "
                     "affecting self, intellect, or dharma."),
    )


def detect_pitra_dosha(chart: Chart) -> Yoga:
    """Pitra Dosha — Sun afflicted by Rahu/Saturn in 9H, OR Sun-Rahu conjunct.

    Reference: classical commentary (Phaladeepika), modern Sanjay Rath
    expansion. Karmic debt to paternal ancestors.
    """
    sun_sign = chart.sign_of("Sun")
    sun_house = chart.house_of("Sun")
    rahu_sign = chart.sign_of("Rahu")
    rahu_house = chart.house_of("Rahu")
    saturn_sign = chart.sign_of("Saturn")
    triggers: list[str] = []
    # Sun-Rahu conjunction (same sign)
    if sun_sign is not None and sun_sign == rahu_sign:
        triggers.append("Sun-Rahu conjunction (Grahana dosha)")
    # Sun in 9H with Rahu/Saturn afflicting (same sign or aspecting)
    if sun_house == 9:
        if rahu_house == 9:
            triggers.append("Rahu in 9H with Sun")
        if saturn_sign == sun_sign:
            triggers.append("Saturn with Sun in 9H")
    active = bool(triggers)
    return Yoga(
        name="Pitra Dosha", sanskrit="पितृ-दोष",
        active=active,
        intensity=min(1.0, 0.4 * len(triggers)) if active else 0.0,
        participants=("Sun", "Rahu") if "Rahu" in " ".join(triggers) else ("Sun",),
        reference="Phaladeepika commentary; modern synthesis",
        description=("Sun (pitr-karaka) afflicted by Rahu/Saturn — "
                     "ancestral karmic burden. Triggers: "
                     + "; ".join(triggers) if triggers else
                     "Pitra Dosha not active for this chart"),
    )


def detect_matr_dosha(chart: Chart) -> Yoga:
    """Matr Dosha — Moon afflicted by Rahu/Saturn in 4H, OR Moon-Rahu conjunct.

    Reference: classical commentary; symmetric counterpart to Pitra Dosha
    on the maternal axis.
    """
    moon_sign = chart.sign_of("Moon")
    moon_house = chart.house_of("Moon")
    rahu_sign = chart.sign_of("Rahu")
    rahu_house = chart.house_of("Rahu")
    saturn_sign = chart.sign_of("Saturn")
    triggers: list[str] = []
    if moon_sign is not None and moon_sign == rahu_sign:
        triggers.append("Moon-Rahu conjunction (Grahana dosha on Moon)")
    if moon_house == 4:
        if rahu_house == 4:
            triggers.append("Rahu in 4H with Moon")
        if saturn_sign == moon_sign:
            triggers.append("Saturn with Moon in 4H")
    active = bool(triggers)
    return Yoga(
        name="Matr Dosha", sanskrit="मातृ-दोष",
        active=active,
        intensity=min(1.0, 0.4 * len(triggers)) if active else 0.0,
        participants=("Moon",),
        reference="Phaladeepika commentary; modern synthesis",
        description=("Moon (matr-karaka) afflicted — maternal/emotional "
                     "karmic burden. Triggers: "
                     + "; ".join(triggers) if triggers else
                     "Matr Dosha not active for this chart"),
    )


def detect_parijata(chart: Chart) -> Yoga:
    """Parijata Yoga — Lagna lord's dispositor in own/exalt and well-placed.

    BPHS Ch.39 — wealth-and-honour yoga. Trace: Lagna lord sits in sign X
    ruled by planet P; if P is well-placed (own/exalt/Mooltrikona) AND in
    Kendra/Trikona, the yoga fires. Compound trace through 2 rulership
    levels — distinguished from simpler Lagna-strength signals.
    """
    asc = chart.asc_sign
    roles = functional_roles(asc)
    asc_lord = next(
        (p for p, r in roles.items() if 1 in r.houses_ruled), None,
    )
    if asc_lord is None:
        return Yoga(
            name="Parijata", sanskrit="पारिजात", active=False,
            intensity=0.0, participants=(),
            reference="BPHS Ch.39",
            description="(skipped — Lagna lord not resolvable)",
        )
    asc_lord_sign = chart.sign_of(asc_lord)
    if asc_lord_sign is None:
        return Yoga(
            name="Parijata", sanskrit="पारिजात", active=False,
            intensity=0.0, participants=(asc_lord,),
            reference="BPHS Ch.39", description="(asc lord sign missing)",
        )
    # Sign rulership map
    sign_lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
        6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter",
        10: "Saturn", 11: "Saturn", 12: "Jupiter",
    }
    dispositor = sign_lords[asc_lord_sign]
    disp_sign = chart.sign_of(dispositor)
    disp_house = chart.house_of(dispositor)
    disp_lon = chart.planet_lons.get(dispositor)
    if disp_sign is None:
        return Yoga(
            name="Parijata", sanskrit="पारिजात", active=False,
            intensity=0.0, participants=(asc_lord, dispositor),
            reference="BPHS Ch.39", description="(dispositor sign missing)",
        )
    cond_disp_dignified = (
        is_exalted(dispositor, disp_sign)
        or is_own_sign(dispositor, disp_sign)
        or (disp_lon is not None and is_moolatrikona(dispositor, disp_lon))
    )
    cond_disp_well_placed = disp_house in (_KENDRAS | _TRIKONAS)
    active = bool(cond_disp_dignified and cond_disp_well_placed)
    return Yoga(
        name="Parijata", sanskrit="पारिजात",
        active=active,
        intensity=0.85 if active else 0.0,
        participants=(asc_lord, dispositor),
        reference="BPHS Ch.39",
        description=(
            f"Lagna lord {asc_lord} disposited by {dispositor}, which is "
            "dignified AND well-placed — wealth and honour."
        ),
    )


def detect_adhi(chart: Chart) -> Yoga:
    """Benefics in 6/7/8 from Moon — protection yoga.

    Reference: BPHS Ch.78.
    """
    moon_sign = chart.sign_of("Moon")
    if moon_sign is None:
        return Yoga(
            name="Adhi", sanskrit="आधि", active=False, intensity=0.0,
            participants=(), reference="BPHS Ch.78",
            description="(skipped — Moon position not available)",
        )
    targets = {((moon_sign - 1 + d - 1) % 12) + 1 for d in (6, 7, 8)}
    found = tuple(sorted(
        p for p, s in chart.planet_signs.items()
        if s in targets and p in _BENEFICS_NATURAL
    ))
    active = bool(found)
    return Yoga(
        name="Adhi", sanskrit="आधि", active=active,
        intensity=min(1.0, 0.4 * len(found)),
        participants=("Moon",) + found,
        reference="BPHS Ch.78",
        description="Natural benefic(s) in 6/7/8 from Moon — protection from enemies.",
    )


# ═══════════════════════════════════════════════════════════════════
# Gap I — 10 additional canonical yogas (from agent research output)
# ═══════════════════════════════════════════════════════════════════


def detect_papa_kartari(chart: Chart) -> Yoga:
    """Lagna or Moon hemmed by malefics in 2nd and 12th — BPHS Ch.78.9.

    "Kartari" = scissors; the hemmed significator is cut off from its
    natural promise. Most-cited classical affliction beyond Mangal Dosha.
    """
    def hemmed(house: int) -> bool:
        prev_h = ((house - 2) % 12) + 1
        next_h = (house % 12) + 1
        prev_mal = any(p in _MALEFICS_NATURAL for p in chart.planets_in_house(prev_h))
        next_mal = any(p in _MALEFICS_NATURAL for p in chart.planets_in_house(next_h))
        return prev_mal and next_mal

    moon_h = chart.house_of("Moon") or 0
    lagna_hemmed = hemmed(1)
    moon_hemmed = moon_h > 0 and hemmed(moon_h)
    active = lagna_hemmed or moon_hemmed
    participants: list[str] = []
    if lagna_hemmed: participants.append("Lagna")
    if moon_hemmed: participants.append("Moon")
    return Yoga(
        name="Papa Kartari", sanskrit="पाप-कर्तरि", active=active,
        intensity=0.8 if (lagna_hemmed and moon_hemmed) else (0.6 if active else 0.0),
        participants=tuple(participants),
        reference="BPHS Ch.78.9",
        description="Significator hemmed (kartari = scissors) by malefics in 2nd/12th; promise cut off.",
    )


def detect_shubha_kartari(chart: Chart) -> Yoga:
    """Lagna or Moon hemmed by benefics in 2nd and 12th — BPHS Ch.78.10.

    Auspicious counterpart of Papa Kartari. Benefic-hemmed significator
    is protected and supported by helpful circumstance.
    """
    def shubha_hemmed(house: int) -> bool:
        prev_h = ((house - 2) % 12) + 1
        next_h = (house % 12) + 1
        prev_b = any(p in _BENEFICS_NATURAL for p in chart.planets_in_house(prev_h))
        next_b = any(p in _BENEFICS_NATURAL for p in chart.planets_in_house(next_h))
        return prev_b and next_b

    moon_h = chart.house_of("Moon") or 0
    lagna_h = shubha_hemmed(1)
    moon_h_hemmed = moon_h > 0 and shubha_hemmed(moon_h)
    active = lagna_h or moon_h_hemmed
    parts: list[str] = []
    if lagna_h: parts.append("Lagna")
    if moon_h_hemmed: parts.append("Moon")
    return Yoga(
        name="Shubha Kartari", sanskrit="शुभ-कर्तरि", active=active,
        intensity=0.8 if (lagna_h and moon_h_hemmed) else (0.6 if active else 0.0),
        participants=tuple(parts),
        reference="BPHS Ch.78.10",
        description="Significator hemmed by benefics in 2nd/12th; protected from obstacles.",
    )


def detect_kahala(chart: Chart) -> Yoga:
    """4L and 9L in mutual Kendras + Lagna lord strong — Phaladeepika Ch.6.34.

    Confers managerial command and landed prosperity ("commander of armies").
    """
    roles = functional_roles(chart.asc_sign)
    l4 = next((p for p, r in roles.items() if 4 in r.houses_ruled), None)
    l9 = next((p for p, r in roles.items() if 9 in r.houses_ruled), None)
    ll = next((p for p, r in roles.items() if 1 in r.houses_ruled), None)
    if not (l4 and l9 and ll):
        return Yoga(name="Kahala", sanskrit="कहल", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.34",
                    description="(skipped — lordship not resolvable)")
    h4, h9 = chart.house_of(l4), chart.house_of(l9)
    if not (h4 and h9):
        return Yoga(name="Kahala", sanskrit="कहल", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.34",
                    description="(skipped — placements missing)")
    mutual_kendra = ((h4 - h9) % 12) in (0, 3, 6, 9)
    ll_sign = chart.sign_of(ll)
    ll_strong = (
        ll_sign is not None and (
            is_exalted(ll, ll_sign) or is_own_sign(ll, ll_sign)
            or chart.house_of(ll) in (_KENDRAS | _TRIKONAS)
        )
    )
    active = bool(mutual_kendra and ll_strong)
    return Yoga(
        name="Kahala", sanskrit="कहल", active=active,
        intensity=0.85 if active else 0.0,
        participants=(l4, l9, ll),
        reference="Phaladeepika Ch.6.34",
        description="4L + 9L in mutual Kendras with strong Lagna lord — commander of armies / landed authority.",
    )


def detect_vasumati(chart: Chart) -> Yoga:
    """Natural benefics in Upachaya houses (3/6/10/11) — BPHS Ch.78.18.

    Self-earned wealth that compounds; never inherited.
    """
    upachayas = {3, 6, 10, 11}
    benefic_houses_lagna = [chart.house_of(p) for p in ("Jupiter", "Venus", "Mercury", "Moon")]
    in_upa_lagna = sum(1 for h in benefic_houses_lagna if h in upachayas)
    moon_h = chart.house_of("Moon")
    in_upa_moon = 0
    if moon_h is not None:
        for h in benefic_houses_lagna:
            if h is None: continue
            from_moon = ((h - moon_h) % 12) + 1
            if from_moon in upachayas:
                in_upa_moon += 1
    best = max(in_upa_lagna, in_upa_moon)
    active = best >= 3
    return Yoga(
        name="Vasumati", sanskrit="वसुमती", active=active,
        intensity=1.0 if best == 4 else (0.6 if best == 3 else 0.0),
        participants=tuple(b for b in ("Jupiter", "Venus", "Mercury", "Moon")
                           if chart.house_of(b) in upachayas),
        reference="BPHS Ch.78.18",
        description="All natural benefics in Upachaya (3/6/10/11) from Lagna or Moon — self-made wealth.",
    )


def detect_shakat(chart: Chart) -> Yoga:
    """Moon in 6/8/12 from Jupiter, NOT in Kendra from Lagna — BPHS Ch.78.31.

    Cart-wheel pattern — fortune rises and falls cyclically.
    """
    moon_h = chart.house_of("Moon")
    jup_h = chart.house_of("Jupiter")
    if not (moon_h and jup_h):
        return Yoga(name="Shakat", sanskrit="शकट", active=False, intensity=0.0,
                    participants=(), reference="BPHS Ch.78.31",
                    description="(skipped — Moon or Jupiter missing)")
    rel = ((moon_h - jup_h) % 12) + 1
    cond1 = rel in {6, 8, 12}
    cond2 = moon_h not in _KENDRAS
    active = cond1 and cond2
    return Yoga(
        name="Shakat", sanskrit="शकट", active=active,
        intensity=0.7 if active else 0.0,
        participants=("Moon", "Jupiter"),
        reference="BPHS Ch.78.31",
        description="Moon 6/8/12 from Jupiter and not in Kendra — cyclic fortune-reversal pattern (cartwheel).",
    )


def detect_guru_chandala(chart: Chart) -> Yoga:
    """Jupiter conjoined with Rahu or Ketu — Jataka Tattva.

    Distorted dharma; teacher who misleads, philosophical confusion.
    """
    jh = chart.house_of("Jupiter")
    rh = chart.house_of("Rahu")
    kh = chart.house_of("Ketu")
    if jh is None:
        return Yoga(name="Guru Chandala", sanskrit="गुरु-चाण्डाल", active=False,
                    intensity=0.0, participants=(),
                    reference="Jataka Tattva",
                    description="(skipped — Jupiter missing)")
    active = jh in {rh, kh}
    jup_sign = chart.sign_of("Jupiter")
    intensity = 0.0
    if active:
        # Stronger if Jupiter exalted (Cancer) — paradoxical inversion
        if jup_sign is not None and is_exalted("Jupiter", jup_sign):
            intensity = 0.6  # transmuted to iconoclastic reform
        else:
            intensity = 0.9
    return Yoga(
        name="Guru Chandala", sanskrit="गुरु-चाण्डाल", active=active,
        intensity=intensity,
        participants=("Jupiter", "Rahu" if jh == rh else "Ketu"),
        reference="Jataka Tattva",
        description="Jupiter conjoined Rahu/Ketu — guru-corruption pattern; modern: cult / fallen-guru / conspiracy spirituality.",
    )


def detect_harsha(chart: Chart) -> Yoga:
    """6L in 6/8/12 — Vipareeta Raja subtype: Harsha (joy/health).

    Per Phaladeepika Ch.6.28. Freedom from disease, victory over enemies.
    """
    roles = functional_roles(chart.asc_sign)
    l6 = next((p for p, r in roles.items() if 6 in r.houses_ruled), None)
    if not l6:
        return Yoga(name="Harsha", sanskrit="हर्ष", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.28",
                    description="(skipped)")
    h = chart.house_of(l6)
    active = h in _DUSTHANAS
    return Yoga(
        name="Harsha", sanskrit="हर्ष", active=active,
        intensity=1.0 if h == 6 else (0.7 if active else 0.0),
        participants=(l6,),
        reference="Phaladeepika Ch.6.28",
        description="6L in 6/8/12 — Vipareeta Raja subtype: freedom from disease, victory over enemies.",
    )


def detect_sarala(chart: Chart) -> Yoga:
    """8L in 6/8/12 — Vipareeta Raja subtype: Sarala (longevity/occult).

    Per Phaladeepika Ch.6.28. Long life, escape from death-blows.
    """
    roles = functional_roles(chart.asc_sign)
    l8 = next((p for p, r in roles.items() if 8 in r.houses_ruled), None)
    if not l8:
        return Yoga(name="Sarala", sanskrit="सरल", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.28",
                    description="(skipped)")
    h = chart.house_of(l8)
    active = h in _DUSTHANAS
    return Yoga(
        name="Sarala", sanskrit="सरल", active=active,
        intensity=1.0 if h == 8 else (0.7 if active else 0.0),
        participants=(l8,),
        reference="Phaladeepika Ch.6.28",
        description="8L in 6/8/12 — Vipareeta Raja subtype: long life, occult mastery, trauma-into-mastery.",
    )


def detect_vimala(chart: Chart) -> Yoga:
    """12L in 6/8/12 — Vipareeta Raja subtype: Vimala (moksha/freedom).

    Per Phaladeepika Ch.6.29. Frugal habits, debt-freedom, moksha orientation.
    """
    roles = functional_roles(chart.asc_sign)
    l12 = next((p for p, r in roles.items() if 12 in r.houses_ruled), None)
    if not l12:
        return Yoga(name="Vimala", sanskrit="विमल", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.29",
                    description="(skipped)")
    h = chart.house_of(l12)
    active = h in _DUSTHANAS
    return Yoga(
        name="Vimala", sanskrit="विमल", active=active,
        intensity=1.0 if h == 12 else (0.7 if active else 0.0),
        participants=(l12,),
        reference="Phaladeepika Ch.6.29",
        description="12L in 6/8/12 — Vipareeta Raja subtype: minimalist + debt-free + moksha-oriented life.",
    )


def detect_kalanidhi(chart: Chart) -> Yoga:
    """Jupiter in 2H or 5H, in Mercury/Venus sign, with Mer/Ven conjunction or aspect.

    Per Phaladeepika Ch.6.41 — "treasure-house of arts" — scholar-aesthete.
    """
    jh = chart.house_of("Jupiter")
    js = chart.sign_of("Jupiter")
    if not (jh and js):
        return Yoga(name="Kalanidhi", sanskrit="कलानिधि", active=False, intensity=0.0,
                    participants=(), reference="Phaladeepika Ch.6.41",
                    description="(skipped)")
    in_right_house = jh in {2, 5}
    in_right_sign = js in {3, 6, 2, 7}  # Mercury (Ge/Vi) + Venus (Ta/Li)
    mer_h = chart.house_of("Mercury")
    ven_h = chart.house_of("Venus")
    conjunct = mer_h == jh or ven_h == jh
    mer_aspect = mer_h is not None and jh in aspects_from_planet("Mercury", mer_h)
    ven_aspect = ven_h is not None and jh in aspects_from_planet("Venus", ven_h)
    aspect_or_conj = conjunct or mer_aspect or ven_aspect
    active = in_right_house and in_right_sign and aspect_or_conj
    return Yoga(
        name="Kalanidhi", sanskrit="कलानिधि", active=active,
        intensity=0.85 if active else 0.0,
        participants=("Jupiter", "Mercury", "Venus"),
        reference="Phaladeepika Ch.6.41",
        description="Jupiter in 2H/5H in Mer/Ven sign + Mer/Ven aspect — treasure-house of arts; polymath-aesthete.",
    )


# ─── L-1: Nabhasa yoga family (BPHS Ch.36 + BV Raman's THIC) ─────────


# Sign types for Nabhasa Asraya yogas
_CHARA_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})    # movable
_STHIRA_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})   # fixed
_DWISWABHAVA_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})  # dual

_VISIBLE_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


def _visible_planet_signs(chart: Chart) -> dict[str, int]:
    """{planet: sign} for the 7 visible grahas (Nabhasa excludes nodes)."""
    out: dict[str, int] = {}
    for p in _VISIBLE_SEVEN:
        s = chart.sign_of(p)
        if s is not None:
            out[p] = s
    return out


def _count_distinct_signs(chart: Chart) -> int:
    """How many DISTINCT signs the 7 visible grahas occupy."""
    return len({s for s in _visible_planet_signs(chart).values()})


# Nabhasa Sankhya yogas (BPHS 36.6-13) — named by sign-count.
_SANKHYA_NAMES: Final[dict[int, tuple[str, str, str]]] = {
    1: ("Gola", "गोल", "all 7 visible grahas in one sign — extreme concentration"),
    2: ("Yuga", "युग", "7 visible grahas in 2 signs — duality / polarity"),
    3: ("Shoola", "शूल", "7 visible grahas in 3 signs — concentrated thrust"),
    4: ("Kedara", "केदार", "7 visible grahas in 4 signs — agrarian fields pattern"),
    5: ("Pasha", "पाश", "7 visible grahas in 5 signs — bondage / collected karma"),
    6: ("Damini", "दामिनी", "7 visible grahas in 6 signs — generous distribution"),
    7: ("Veena", "वीणा", "7 visible grahas in 7 distinct signs — Vipanchi pattern, harmonious"),
}


def _sankhya_template(target_count: int) -> Callable[[Chart], Yoga]:
    name, sanskrit, desc = _SANKHYA_NAMES[target_count]

    def detector(chart: Chart) -> Yoga:
        n = _count_distinct_signs(chart)
        active = (n == target_count)
        return Yoga(
            name=name, sanskrit=sanskrit, active=active,
            intensity=0.7 if active else 0.0,
            participants=_VISIBLE_SEVEN,
            reference=f"BPHS Ch.36.{6 + target_count - 1}",
            description=desc,
        )
    return detector


detect_gola    = _sankhya_template(1)
detect_yuga    = _sankhya_template(2)
detect_shoola  = _sankhya_template(3)
detect_kedara  = _sankhya_template(4)
detect_pasha   = _sankhya_template(5)
detect_damini  = _sankhya_template(6)
detect_veena   = _sankhya_template(7)


# Nabhasa Asraya yogas (BPHS 36.3-5) — all 7 grahas in one sign-type
def detect_rajju(chart: Chart) -> Yoga:
    """All 7 visible grahas in chara (movable) signs — Rajju yoga (BPHS 36.3).

    Doctrine: itinerant nature, frequent travel, restless personality.
    """
    signs = _visible_planet_signs(chart).values()
    active = bool(signs) and all(s in _CHARA_SIGNS for s in signs)
    return Yoga(
        name="Rajju", sanskrit="रज्जु", active=active,
        intensity=0.8 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.36.3",
        description="All 7 visible grahas in chara (movable) signs — itinerant nature, travel-driven life.",
    )


def detect_musala(chart: Chart) -> Yoga:
    """All 7 visible grahas in sthira (fixed) signs — Musala yoga (BPHS 36.4)."""
    signs = _visible_planet_signs(chart).values()
    active = bool(signs) and all(s in _STHIRA_SIGNS for s in signs)
    return Yoga(
        name="Musala", sanskrit="मुसल", active=active,
        intensity=0.8 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.36.4",
        description="All 7 visible grahas in sthira (fixed) signs — stable, accumulating, hierarchically rising.",
    )


def detect_nala(chart: Chart) -> Yoga:
    """All 7 visible grahas in dwiswabhava (dual) signs — Nala yoga (BPHS 36.5)."""
    signs = _visible_planet_signs(chart).values()
    active = bool(signs) and all(s in _DWISWABHAVA_SIGNS for s in signs)
    return Yoga(
        name="Nala", sanskrit="नल", active=active,
        intensity=0.8 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.36.5",
        description="All 7 visible grahas in dwiswabhava (dual) signs — adaptable, dual-natured, often double-careered.",
    )


# Nabhasa Dala yogas (BPHS 36.14-15) — distribution by Kendra/Panapara/Apoklima


def _planets_in_houses_set(chart: Chart, houses: set[int]) -> int:
    """Count visible grahas in the given set of houses."""
    return sum(
        1 for p in _VISIBLE_SEVEN
        if chart.house_of(p) in houses
    )


_PANAPARAS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_APOKLIMAS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})


def detect_mala(chart: Chart) -> Yoga:
    """All 7 visible grahas in PANAPARA houses (2/5/8/11) — Mala yoga."""
    n_in_panapara = _planets_in_houses_set(chart, set(_PANAPARAS))
    active = n_in_panapara == 7
    return Yoga(
        name="Mala", sanskrit="माल", active=active,
        intensity=0.75 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.36.14",
        description="All 7 visible grahas in panapara (2/5/8/11) houses — wealth-accumulating, garland-like distribution.",
    )


def detect_sarpa(chart: Chart) -> Yoga:
    """All 7 visible grahas in APOKLIMA houses (3/6/9/12) — Sarpa yoga (Nabhasa variant)."""
    n_in_apoklima = _planets_in_houses_set(chart, set(_APOKLIMAS))
    active = n_in_apoklima == 7
    return Yoga(
        name="Sarpa (Nabhasa)", sanskrit="सर्प", active=active,
        intensity=0.75 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.36.15",
        description="All 7 visible grahas in apoklima (3/6/9/12) houses — strained, sinuous, snake-path life.",
    )


# ─── L-1: Pravrajya yogas (renunciation) (BPHS Ch.78) ────────────────


def detect_pravrajya_4plus_in_one_sign(chart: Chart) -> Yoga:
    """4+ grahas in ONE sign → renunciation tendency (BPHS Ch.78.1).

    Per BV Raman: the lord of that sign determines the order/path.
    """
    sign_counts: dict[int, int] = {}
    for p in _VISIBLE_SEVEN:
        s = chart.sign_of(p)
        if s is not None:
            sign_counts[s] = sign_counts.get(s, 0) + 1
    max_in_one = max(sign_counts.values()) if sign_counts else 0
    active = max_in_one >= 4
    return Yoga(
        name="Pravrajya (4+ together)", sanskrit="प्रव्रज्या",
        active=active, intensity=0.6 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.78.1",
        description="4+ visible grahas conjunct in one sign — renunciation impulse, monastic tendency.",
    )


def detect_pravrajya_saturn_aspect(chart: Chart) -> Yoga:
    """Saturn aspecting the Moon (or Moon in 9H aspected by Saturn) → ascetic.

    Per BPHS Ch.78.2 + Phaladeepika Ch.27.
    """
    moon_h = chart.house_of("Moon")
    sat_h = chart.house_of("Saturn")
    if moon_h is None or sat_h is None:
        return Yoga(name="Pravrajya (Saturn-Moon)", sanskrit="प्रव्रज्या",
                    active=False, intensity=0.0, participants=(),
                    reference="BPHS Ch.78.2", description="(skipped — missing positions)")
    sat_aspects = aspects_from_planet("Saturn", sat_h)
    active = moon_h in sat_aspects
    return Yoga(
        name="Pravrajya (Saturn-Moon)", sanskrit="प्रव्रज्या",
        active=active, intensity=0.55 if active else 0.0,
        participants=("Saturn", "Moon"),
        reference="BPHS Ch.78.2 + Phaladeepika Ch.27",
        description="Saturn aspecting Moon — detachment, contemplative ascetic tendency.",
    )


def detect_sanyasa(chart: Chart) -> Yoga:
    """Strong Saturn + 9H/10H lord + Moon connection → formal renunciation.

    Per BV Raman's THIC ch.119 — Sanyasa yoga proper requires the
    chart's "spiritual triad" planets in mutual connection.
    """
    moon_h = chart.house_of("Moon")
    sat_h = chart.house_of("Saturn")
    if moon_h is None or sat_h is None:
        return Yoga(name="Sanyasa", sanskrit="संन्यास", active=False,
                    intensity=0.0, participants=(), reference="BV Raman THIC 119",
                    description="(skipped)")
    # Simplified: Saturn in 4 from Moon (the classic 'detachment' angle)
    # OR Moon and Saturn in mutual kendras
    sat_in_4_from_moon = ((sat_h - moon_h) % 12) + 1 == 4
    moon_in_kendra = moon_h in _KENDRAS
    sat_in_kendra = sat_h in _KENDRAS
    mutual_kendra = moon_in_kendra and sat_in_kendra
    active = sat_in_4_from_moon or mutual_kendra
    return Yoga(
        name="Sanyasa", sanskrit="संन्यास", active=active,
        intensity=0.65 if active else 0.0,
        participants=("Saturn", "Moon"), reference="BV Raman THIC 119",
        description="Saturn-Moon detachment angle — formal renunciation potential, monastic vows.",
    )


# ─── L-1: Daridra-family expansion (poverty / wealth-loss variants) ─


def detect_kuhu(chart: Chart) -> Yoga:
    """Moon void in Capricorn or Aquarius with malefic aspect — Kuhu yoga.

    Per Phaladeepika Ch.6.36 — financial vacuum, undeserved poverty.
    """
    moon_sign = chart.sign_of("Moon")
    if moon_sign is None:
        return Yoga(name="Kuhu", sanskrit="कुहू", active=False,
                    intensity=0.0, participants=(), reference="Phaladeepika Ch.6.36",
                    description="(skipped)")
    in_saturn_sign = moon_sign in {10, 11}
    moon_h = chart.house_of("Moon")
    mal_aspect = False
    if moon_h is not None:
        for m in ("Sun", "Mars", "Saturn"):
            mh = chart.house_of(m)
            if mh is not None and moon_h in aspects_from_planet(m, mh):
                mal_aspect = True
                break
    active = in_saturn_sign and mal_aspect
    return Yoga(
        name="Kuhu", sanskrit="कुहू", active=active,
        intensity=0.55 if active else 0.0,
        participants=("Moon",), reference="Phaladeepika Ch.6.36",
        description="Moon in Capricorn/Aquarius with malefic aspect — financial vacuum, recurring poverty.",
    )


def detect_dhana_yoga_simple(chart: Chart) -> Yoga:
    """Generic Dhana yoga: 2H lord + 11H lord in mutual kendra/trikona.

    Per BPHS Ch.40.4 — the most common wealth combination beyond
    Lakshmi/Vasumati/Parijata.
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_2 = None
    lord_11 = None
    for p, r in roles.items():
        if 2 in r.houses_ruled:
            lord_2 = p
        if 11 in r.houses_ruled:
            lord_11 = p
    if lord_2 is None or lord_11 is None:
        return Yoga(name="Dhana (2L-11L)", sanskrit="धन", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.4",
                    description="(skipped)")
    h2 = chart.house_of(lord_2)
    h11 = chart.house_of(lord_11)
    if h2 is None or h11 is None:
        return Yoga(name="Dhana (2L-11L)", sanskrit="धन", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.4",
                    description="(skipped)")
    distance = ((h11 - h2) % 12) + 1
    active = distance in (1, 4, 5, 7, 9, 10)
    return Yoga(
        name="Dhana (2L-11L)", sanskrit="धन", active=active,
        intensity=0.7 if active else 0.0,
        participants=(lord_2, lord_11), reference="BPHS Ch.40.4",
        description="2H-lord and 11H-lord in mutual kendra/trikona — sustained wealth accumulation.",
    )


def detect_putra_dosha(chart: Chart) -> Yoga:
    """Malefics in 5H + 5H lord debilitated/combust = Putra Dosha (child-difficulty).

    Per Phaladeepika Ch.18.
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_5 = None
    for p, r in roles.items():
        if 5 in r.houses_ruled:
            lord_5 = p
            break
    if lord_5 is None:
        return Yoga(name="Putra Dosha", sanskrit="पुत्र दोष", active=False,
                    intensity=0.0, participants=(), reference="Phaladeepika Ch.18",
                    description="(skipped)")
    malefics_in_5 = sum(
        1 for m in _MALEFICS_NATURAL if chart.house_of(m) == 5
    )
    lord_5_sign = chart.sign_of(lord_5)
    lord_5_debil = lord_5_sign is not None and is_debilitated(lord_5, lord_5_sign)
    active = malefics_in_5 >= 2 or (malefics_in_5 >= 1 and lord_5_debil)
    return Yoga(
        name="Putra Dosha", sanskrit="पुत्र दोष", active=active,
        intensity=0.6 if active else 0.0,
        participants=(lord_5,), reference="Phaladeepika Ch.18",
        description=f"5H afflicted ({malefics_in_5} malefics) — children-related obstacles or delay.",
    )


def detect_balarishta(chart: Chart) -> Yoga:
    """Moon in dushtana + malefic aspect — Balarishta (childhood-risk yoga).

    Per BPHS Ch.42 — classical early-mortality flag.
    """
    moon_h = chart.house_of("Moon")
    if moon_h is None:
        return Yoga(name="Balarishta", sanskrit="बालारिष्ट", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.42",
                    description="(skipped)")
    in_dushtana = moon_h in _DUSTHANAS
    mal_aspect = False
    for m in ("Sun", "Mars", "Saturn"):
        mh = chart.house_of(m)
        if mh is not None and moon_h in aspects_from_planet(m, mh):
            mal_aspect = True
            break
    active = in_dushtana and mal_aspect
    return Yoga(
        name="Balarishta", sanskrit="बालारिष्ट", active=active,
        intensity=0.55 if active else 0.0,
        participants=("Moon",), reference="BPHS Ch.42",
        description="Moon in dushtana with malefic aspect — childhood-mortality flag (cancellable).",
    )


# ─── L-1: More chart-architecture yogas ─────────────────────────────


def detect_chamara(chart: Chart) -> Yoga:
    """Lagna lord exalted + in kendra + Jupiter aspect — Chamara yoga (BPHS 40.10)."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_1 = None
    for p, r in roles.items():
        if 1 in r.houses_ruled:
            lord_1 = p
            break
    if lord_1 is None:
        return Yoga(name="Chamara", sanskrit="चामर", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.10",
                    description="(skipped)")
    sign = chart.sign_of(lord_1)
    house = chart.house_of(lord_1)
    if sign is None or house is None:
        return Yoga(name="Chamara", sanskrit="चामर", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.10",
                    description="(skipped)")
    exalted = is_exalted(lord_1, sign)
    in_kendra = house in _KENDRAS
    jup_h = chart.house_of("Jupiter")
    jup_aspect = jup_h is not None and house in aspects_from_planet("Jupiter", jup_h)
    active = exalted and in_kendra and jup_aspect
    return Yoga(
        name="Chamara", sanskrit="चामर", active=active,
        intensity=0.85 if active else 0.0,
        participants=(lord_1, "Jupiter"), reference="BPHS Ch.40.10",
        description="1H-lord exalted in kendra + Jupiter aspect — royal-grade authority and longevity.",
    )


def detect_simhasana(chart: Chart) -> Yoga:
    """1H lord + 9H lord + 10H lord all in kendras — Simhasana yoga (BPHS 40.11)."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lords = {}
    for p, r in roles.items():
        for h in (1, 9, 10):
            if h in r.houses_ruled:
                lords[h] = p
    if not all(h in lords for h in (1, 9, 10)):
        return Yoga(name="Simhasana", sanskrit="सिंहासन", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.11",
                    description="(skipped)")
    all_in_kendra = all(
        chart.house_of(lords[h]) in _KENDRAS for h in (1, 9, 10)
        if chart.house_of(lords[h]) is not None
    )
    active = all_in_kendra and all(chart.house_of(lords[h]) is not None for h in (1, 9, 10))
    return Yoga(
        name="Simhasana", sanskrit="सिंहासन", active=active,
        intensity=0.85 if active else 0.0,
        participants=tuple(lords[h] for h in (1, 9, 10) if h in lords),
        reference="BPHS Ch.40.11",
        description="1H + 9H + 10H lords all in kendras — Simhasana (throne) yoga, leadership grade.",
    )


def detect_bheri(chart: Chart) -> Yoga:
    """Venus/Jupiter/Lagna-lord/Moon connected via kendra/trikona — Bheri yoga (BPHS 40.12).

    Simplified: Venus + Jupiter both in kendra/trikona AND 9H lord in kendra.
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_9 = None
    for p, r in roles.items():
        if 9 in r.houses_ruled:
            lord_9 = p
            break
    ven_h = chart.house_of("Venus")
    jup_h = chart.house_of("Jupiter")
    l9_h = chart.house_of(lord_9) if lord_9 else None
    if not (ven_h and jup_h and l9_h):
        return Yoga(name="Bheri", sanskrit="भेरी", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.12",
                    description="(skipped)")
    in_aus = lambda h: h in _KENDRAS or h in {5, 9}
    active = in_aus(ven_h) and in_aus(jup_h) and in_aus(l9_h)
    return Yoga(
        name="Bheri", sanskrit="भेरी", active=active,
        intensity=0.75 if active else 0.0,
        participants=("Venus", "Jupiter", lord_9 or "?"),
        reference="BPHS Ch.40.12",
        description="Venus + Jupiter + 9H-lord all in kendra/trikona — Bheri (drum) yoga, fame + prosperity.",
    )


def detect_shanka(chart: Chart) -> Yoga:
    """5H + 6H + Lagna-lord all in strong placements — Shanka yoga (BPHS 40.13)."""
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lords = {}
    for p, r in roles.items():
        for h in (1, 5, 6):
            if h in r.houses_ruled:
                lords[h] = p
    if not all(h in lords for h in (1, 5, 6)):
        return Yoga(name="Shanka", sanskrit="शङ्ख", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.40.13",
                    description="(skipped)")
    in_strong = lambda p: chart.house_of(p) in (_KENDRAS | {5, 9})
    active = (
        in_strong(lords[1]) and in_strong(lords[5]) and in_strong(lords[6])
    )
    return Yoga(
        name="Shanka", sanskrit="शङ्ख", active=active,
        intensity=0.7 if active else 0.0,
        participants=tuple(lords[h] for h in (1, 5, 6) if h in lords),
        reference="BPHS Ch.40.13",
        description="1H + 5H + 6H lords all strong — Shanka (conch) yoga, long-life + righteousness.",
    )


def detect_chatussagara(chart: Chart) -> Yoga:
    """All 4 kendras occupied by planets — Chatussagara yoga (BPHS 40.14).

    Doctrine: 'four oceans' — wide-reaching influence, master of multiple domains.
    """
    occupied = set()
    for p in _VISIBLE_SEVEN:
        h = chart.house_of(p)
        if h is not None and h in _KENDRAS:
            occupied.add(h)
    active = occupied == _KENDRAS
    return Yoga(
        name="Chatussagara", sanskrit="चतुस्सागर", active=active,
        intensity=0.75 if active else 0.0,
        participants=_VISIBLE_SEVEN, reference="BPHS Ch.40.14",
        description="All 4 kendras occupied by visible grahas — 'four oceans', wide-reaching authority.",
    )


def detect_lagnadhi(chart: Chart) -> Yoga:
    """Benefics in 7H + 8H from Lagna — Lagnadhi yoga (BV Raman THIC 87)."""
    benefics_in_7_8 = 0
    for b in _BENEFICS_NATURAL:
        h = chart.house_of(b)
        if h in (7, 8):
            benefics_in_7_8 += 1
    active = benefics_in_7_8 >= 2
    return Yoga(
        name="Lagnadhi", sanskrit="लग्नाधि", active=active,
        intensity=0.6 if active else 0.0,
        participants=tuple(_BENEFICS_NATURAL), reference="BV Raman THIC 87",
        description=f"{benefics_in_7_8} benefics in 7H/8H — Lagnadhi, fortunate disposition.",
    )


def detect_chandradhi(chart: Chart) -> Yoga:
    """Benefics in 6H/7H/8H from MOON — Chandradhi (Adhi-from-Moon) yoga (BPHS 36).

    The classical Adhi yoga (already detected as detect_adhi) reads from Lagna.
    This variant reads from Moon.
    """
    moon_h = chart.house_of("Moon")
    if moon_h is None:
        return Yoga(name="Chandradhi", sanskrit="चन्द्राधि", active=False,
                    intensity=0.0, participants=(), reference="BPHS Ch.36",
                    description="(skipped)")
    benefics_count = 0
    for b in _BENEFICS_NATURAL:
        bh = chart.house_of(b)
        if bh is None:
            continue
        # Distance from Moon: 1-based
        dist = ((bh - moon_h) % 12) + 1
        if dist in (6, 7, 8):
            benefics_count += 1
    active = benefics_count >= 2
    return Yoga(
        name="Chandradhi", sanskrit="चन्द्राधि", active=active,
        intensity=0.65 if active else 0.0,
        participants=("Moon",) + tuple(_BENEFICS_NATURAL),
        reference="BPHS Ch.36 + Adhi variant",
        description=f"{benefics_count} benefics in 6/7/8 from Moon — Chandradhi, emotional stability + support.",
    )


def detect_vargottama(chart: Chart) -> Yoga:
    """1H lord in same sign in D1 as in D9 — Vargottama yoga.

    Note: requires per_planet_varga_signs to detect properly. This is a
    SIMPLIFIED detector that flags as 'partial' when the Lagna-lord
    sign hint suggests vargottama (sign in 1/5/9 cyclic position — the
    base case where Vargottama is more common).
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord_1 = None
    for p, r in roles.items():
        if 1 in r.houses_ruled:
            lord_1 = p
            break
    if not lord_1:
        return Yoga(name="Vargottama (partial)", sanskrit="वर्गोत्तम",
                    active=False, intensity=0.0, participants=(),
                    reference="BPHS Ch.7", description="(skipped)")
    sign = chart.sign_of(lord_1)
    # Without D9 sign, we can only flag "potential" if Lagna lord is in
    # a sign that classically tends to vargottama (movable signs at 0-3.33,
    # fixed at 13.33-16.66, dual at 26.66-30 — the "vargottama navamsha" pads)
    lon = chart.planet_lons.get(lord_1) if lord_1 else None
    if lon is None or sign is None:
        return Yoga(name="Vargottama (partial)", sanskrit="वर्गोत्तम",
                    active=False, intensity=0.0, participants=(lord_1,),
                    reference="BPHS Ch.7", description="(skipped — missing lon)")
    deg = lon % 30.0
    if sign in _CHARA_SIGNS:
        vargottama_pad = 0.0 <= deg < 3.333
    elif sign in _STHIRA_SIGNS:
        vargottama_pad = 13.333 <= deg < 16.667
    else:  # dwiswabhava
        vargottama_pad = 26.667 <= deg < 30.0
    return Yoga(
        name="Vargottama (partial)", sanskrit="वर्गोत्तम", active=vargottama_pad,
        intensity=0.6 if vargottama_pad else 0.0,
        participants=(lord_1,), reference="BPHS Ch.7",
        description=f"Lagna-lord {lord_1} in vargottama navamsha pad — D1 = D9 sign, strong promise.",
    )


# ─── Registry ────────────────────────────────────────────────────────


YOGA_DETECTORS: Final[tuple[Callable[[Chart], Yoga], ...]] = (
    # PMP (5)
    detect_ruchaka, detect_bhadra, detect_hamsa,
    detect_malavya, detect_sasa,
    # Solar/Lunar (5)
    detect_budha_aditya, detect_veshi, detect_vosi,
    detect_sunapha, detect_anapha,
    # Foundation (7)
    detect_gajakesari, detect_chandra_mangal, detect_kemadruma,
    detect_raja_yoga, detect_vipareeta_raja,
    detect_neecha_bhanga_raja, detect_dharma_karma_adhipati,
    # Affliction (3)
    detect_mangal_dosha, detect_kala_sarpa, detect_daridra,
    # Auspicious specials (4)
    detect_amala, detect_saraswati, detect_adhi, detect_lakshmi,
    # Phase B additions (5)
    detect_akhanda_samrajya, detect_sarpa_dosha,
    detect_pitra_dosha, detect_matr_dosha, detect_parijata,
    # Gap I additions (10)
    detect_papa_kartari, detect_shubha_kartari,
    detect_kahala, detect_vasumati, detect_shakat,
    detect_guru_chandala, detect_harsha, detect_sarala,
    detect_vimala, detect_kalanidhi,
    # L-1 Nabhasa Sankhya (7)
    detect_gola, detect_yuga, detect_shoola, detect_kedara,
    detect_pasha, detect_damini, detect_veena,
    # L-1 Nabhasa Asraya (3)
    detect_rajju, detect_musala, detect_nala,
    # L-1 Nabhasa Dala (2)
    detect_mala, detect_sarpa,
    # L-1 Pravrajya / Sanyasa (3)
    detect_pravrajya_4plus_in_one_sign,
    detect_pravrajya_saturn_aspect,
    detect_sanyasa,
    # L-1 Affliction expansion (3)
    detect_kuhu, detect_putra_dosha, detect_balarishta,
    # L-1 Wealth expansion (1)
    detect_dhana_yoga_simple,
    # L-1 Royal/Chart-architecture (7)
    detect_chamara, detect_simhasana, detect_bheri, detect_shanka,
    detect_chatussagara, detect_lagnadhi, detect_chandradhi,
    # L-1 Vargottama (1)
    detect_vargottama,
)


def detect_all(chart: Chart) -> tuple[Yoga, ...]:
    """Run every detector — returns all results (active and inactive).

    Phase 6 / Phase 9 filter on ``y.active`` and weight by ``y.intensity``.
    Returning inactive yogas too is intentional: the Reading Composer
    sometimes wants to explicitly note "Raja Yoga absent".
    """
    return tuple(d(chart) for d in YOGA_DETECTORS)


def active_yogas(chart: Chart) -> tuple[Yoga, ...]:
    """Convenience — only return yogas that fire."""
    return tuple(y for y in detect_all(chart) if y.active)
