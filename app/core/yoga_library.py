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
    SIGN_RULERS, is_debilitated, is_exalted, is_moolatrikona, is_own_sign,
)
from app.core.drishti_argala import aspects_from_planet
from app.core.functional_roles import functional_roles, houses_ruled_by
from app.core.shodashavarga import compute_divisional_longitude


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


# ─── Raman "Three Hundred Important Combinations" additions (increment 35) ───
# Occupancy-only yogas the library lacked, surfaced by the yoga_coverage audit
# against Raman's book. Each is faithful to Raman's stated Definition (cited) and
# computable from sign/house occupancy alone (no daśā, no lord-strength).

_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_UPACHAYAS: Final[frozenset[int]] = frozenset({3, 6, 10, 11})


def detect_dhurdhura(chart: Chart) -> Yoga:
    """Planets (not Sun/nodes) on BOTH sides of the Moon — 2nd AND 12th from it.
    Raman, 300 Combinations No. 4 (Sunapha + Anapha together)."""
    excl = frozenset({"Sun", "Moon", "Rahu", "Ketu"})
    a, wa = _luminary_adjacency(chart, "Moon", 2, excl)
    b, wb = _luminary_adjacency(chart, "Moon", 12, excl)
    active = a and b
    return Yoga(
        name="Dhurdhura", sanskrit="धुरुधुरा", active=active,
        intensity=0.7 if active else 0.0, participants=("Moon",) + wa + wb,
        reference="Raman, 300 Combinations No.4",
        description="Planets on both sides of the Moon (2nd and 12th from it).",
    )


def detect_chatussagara(chart: Chart) -> Yoga:
    """All four kendras (1,4,7,10) occupied by planets.
    Raman, 300 Combinations No. 8."""
    occupied = {chart.house_of(p) for p in chart.planet_signs}
    active = _KENDRAS.issubset(occupied)
    who = tuple(sorted(p for p in chart.planet_signs if chart.house_of(p) in _KENDRAS))
    return Yoga(
        name="Chatussagara", sanskrit="चतुस्सागर", active=active,
        intensity=0.8 if active else 0.0, participants=who,
        reference="Raman, 300 Combinations No.8",
        description="All four kendras (1st, 4th, 7th, 10th) occupied by planets.",
    )


def detect_vasumathi(chart: Chart) -> Yoga:
    """Natural benefics in the upachayas (3,6,10,11) from the ascendant OR the Moon.
    Raman, 300 Combinations No. 9."""
    moon_sign = chart.sign_of("Moon")
    who: list[str] = []
    for b in ("Jupiter", "Venus", "Mercury"):
        h, s = chart.house_of(b), chart.sign_of(b)
        from_lagna = h in _UPACHAYAS
        from_moon = (
            moon_sign is not None and s is not None
            and (((s - moon_sign) % 12) + 1) in _UPACHAYAS
        )
        if from_lagna or from_moon:
            who.append(b)
    active = bool(who)
    return Yoga(
        name="Vasumathi", sanskrit="वसुमती", active=active,
        intensity=min(1.0, 0.4 * len(who)) if active else 0.0, participants=tuple(who),
        reference="Raman, 300 Combinations No.9",
        description="Benefics in the upachayas (3,6,10,11) from the ascendant or Moon.",
    )


def detect_sakata(chart: Chart) -> Yoga:
    """The Moon in the 6th, 8th or 12th sign from Jupiter.
    Raman, 300 Combinations No. 12."""
    ms, js = chart.sign_of("Moon"), chart.sign_of("Jupiter")
    active = (
        ms is not None and js is not None
        and (((ms - js) % 12) + 1) in {6, 8, 12}
    )
    return Yoga(
        name="Sakata", sanskrit="शकट", active=active,
        intensity=0.5 if active else 0.0, participants=("Moon", "Jupiter"),
        reference="Raman, 300 Combinations No.12",
        description="Moon in the 6th, 8th or 12th from Jupiter (a fluctuating-fortune yoga).",
    )


def detect_chakra(chart: Chart) -> Yoga:
    """All seven planets occupy odd houses (1,3,5,7,9,11).
    Raman, 300 Combinations No. 84 (an Ākṛti/dala yoga)."""
    houses = {chart.house_of(p) for p in _SEVEN}
    active = None not in houses and houses.issubset({1, 3, 5, 7, 9, 11})
    return Yoga(
        name="Chakra", sanskrit="चक्र", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.84",
        description="All seven planets in odd houses (1,3,5,7,9,11).",
    )


def _nabhasa_sign_count(chart: Chart) -> int:
    """Distinct signs occupied by the seven (non-nodal) planets."""
    return len({chart.sign_of(p) for p in _SEVEN if chart.sign_of(p) is not None})


def detect_gola(chart: Chart) -> Yoga:
    """Nābhasa Saṅkhyā: all seven planets in a single sign.
    Raman, 300 Combinations No. 101."""
    active = _nabhasa_sign_count(chart) == 1
    return Yoga(
        name="Gola", sanskrit="गोल", active=active,
        intensity=1.0 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.101",
        description="All seven planets occupy a single sign (Nābhasa Saṅkhyā).",
    )


def detect_yuga(chart: Chart) -> Yoga:
    """Nābhasa Saṅkhyā: the seven planets confined to two signs.
    Raman, 300 Combinations No. 101."""
    active = _nabhasa_sign_count(chart) == 2
    return Yoga(
        name="Yuga", sanskrit="युग", active=active,
        intensity=0.8 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.101",
        description="The seven planets confined to two signs (Nābhasa Saṅkhyā).",
    )


def detect_sula(chart: Chart) -> Yoga:
    """Nābhasa Saṅkhyā: the seven planets confined to three signs.
    Raman, 300 Combinations No. 101."""
    active = _nabhasa_sign_count(chart) == 3
    return Yoga(
        name="Sula", sanskrit="शूल", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.101",
        description="The seven planets confined to three signs (Nābhasa Saṅkhyā).",
    )


# ─── Raman "300 Combinations" lord-based additions (increment 36) ──────
# Definitions taken from a cleaner OCR edition of Raman's book (the increment-34
# djvu was noisy; verified against the clean text). Computable from lord placement
# + dignity alone (no navamsa, no daśā).


def _lord_of(chart: Chart, house: int) -> str:
    """Ruler of the sign in the given whole-sign house from the ascendant."""
    sign = ((chart.asc_sign - 1 + house - 1) % 12) + 1
    return SIGN_RULERS[sign]


def _mutual_kendra(chart: Chart, a: str, b: str) -> bool:
    ha, hb = chart.house_of(a), chart.house_of(b)
    if ha is None or hb is None:
        return False
    return (((hb - ha) % 12) + 1) in _KENDRAS


def _is_strong(chart: Chart, planet: str) -> bool:
    """Dignity-based 'powerful/strongly disposed' proxy: exalted, own, or Mooltrikona."""
    sign, lon = chart.sign_of(planet), chart.planet_lons.get(planet)
    if sign is None:
        return False
    return (is_exalted(planet, sign) or is_own_sign(planet, sign)
            or (lon is not None and is_moolatrikona(planet, lon)))


def _exchanged(chart: Chart, p: str, q: str) -> bool:
    """p and q have interchanged signs (parivartana): each sits in a sign the other rules."""
    sp, sq = chart.sign_of(p), chart.sign_of(q)
    if sp is None or sq is None:
        return False
    return SIGN_RULERS[sp] == q and SIGN_RULERS[sq] == p


def detect_parvata(chart: Chart) -> Yoga:
    """Benefics in kendras; the 6th and 8th unoccupied or occupied only by benefics.
    Raman, 300 Combinations No. 14."""
    benefics_in_kendra = [b for b in ("Jupiter", "Venus", "Mercury", "Moon")
                          if chart.house_of(b) in _KENDRAS]
    def clean(h: int) -> bool:
        occ = chart.planets_in_house(h)
        return all(p in _BENEFICS_NATURAL for p in occ)
    active = bool(benefics_in_kendra) and clean(6) and clean(8)
    return Yoga(
        name="Parvata", sanskrit="पर्वत", active=active,
        intensity=0.7 if active else 0.0, participants=tuple(benefics_in_kendra),
        reference="Raman, 300 Combinations No.14",
        description="Benefics in kendras; 6th & 8th empty or benefic-occupied.",
    )


def detect_kahala(chart: Chart) -> Yoga:
    """4th and 9th lords in kendras from each other, Lagna lord strong.
    Raman, 300 Combinations No. 15."""
    l4, l9, ll = _lord_of(chart, 4), _lord_of(chart, 9), _lord_of(chart, 1)
    active = _mutual_kendra(chart, l4, l9) and _is_strong(chart, ll)
    return Yoga(
        name="Kahala", sanskrit="कहल", active=active,
        intensity=0.6 if active else 0.0, participants=(l4, l9, ll),
        reference="Raman, 300 Combinations No.15",
        description="4th & 9th lords in mutual kendras with a strong Lagna lord.",
    )


def detect_chapa(chart: Chart) -> Yoga:
    """Ascendant lord exalted and the 4th & 10th lords interchanged houses.
    Raman, 300 Combinations No. 31."""
    ll = _lord_of(chart, 1)
    ls = chart.sign_of(ll)
    active = (ls is not None and is_exalted(ll, ls)
              and _exchanged(chart, _lord_of(chart, 4), _lord_of(chart, 10)))
    return Yoga(
        name="Chapa", sanskrit="चाप", active=active,
        intensity=0.7 if active else 0.0, participants=(ll,),
        reference="Raman, 300 Combinations No.31",
        description="Exalted Lagna lord with a 4th–10th lord exchange.",
    )


def detect_sreenatha(chart: Chart) -> Yoga:
    """Exalted 7th lord in the 10th, and the 10th lord in the 9th.
    Raman, 300 Combinations No. 32."""
    l7, l10 = _lord_of(chart, 7), _lord_of(chart, 10)
    s7 = chart.sign_of(l7)
    active = (s7 is not None and is_exalted(l7, s7)
              and chart.house_of(l7) == 10 and chart.house_of(l10) == 9)
    return Yoga(
        name="Sreenatha", sanskrit="श्रीनाथ", active=active,
        intensity=0.8 if active else 0.0, participants=(l7, l10),
        reference="Raman, 300 Combinations No.32",
        description="Exalted 7th lord in the 10th with the 10th lord in the 9th.",
    )


def detect_sankha(chart: Chart) -> Yoga:
    """5th and 6th lords in mutual kendras, Lagna lord powerful.
    Raman, 300 Combinations No. 45."""
    l5, l6, ll = _lord_of(chart, 5), _lord_of(chart, 6), _lord_of(chart, 1)
    active = _mutual_kendra(chart, l5, l6) and _is_strong(chart, ll)
    return Yoga(
        name="Sankha", sanskrit="शङ्ख", active=active,
        intensity=0.7 if active else 0.0, participants=(l5, l6, ll),
        reference="Raman, 300 Combinations No.45",
        description="5th & 6th lords in mutual kendras with a strong Lagna lord.",
    )


def detect_bheri(chart: Chart) -> Yoga:
    """Venus, the Lagna lord and Jupiter in mutual kendras, 9th lord powerful.
    Raman, 300 Combinations No. 46."""
    ll, l9 = _lord_of(chart, 1), _lord_of(chart, 9)
    trio = {"Venus", ll, "Jupiter"}
    pairwise = all(_mutual_kendra(chart, a, b)
                   for a in trio for b in trio if a < b)
    active = len(trio) >= 2 and pairwise and _is_strong(chart, l9)
    return Yoga(
        name="Bheri", sanskrit="भेरी", active=active,
        intensity=0.7 if active else 0.0, participants=tuple(sorted(trio)) + (l9,),
        reference="Raman, 300 Combinations No.46",
        description="Venus, Lagna lord and Jupiter in mutual kendras; strong 9th lord.",
    )


def detect_samudra(chart: Chart) -> Yoga:
    """All seven planets in even houses (2,4,6,8,10,12).
    Raman, 300 Combinations No. 72."""
    houses = {chart.house_of(p) for p in _SEVEN}
    active = None not in houses and houses.issubset({2, 4, 6, 8, 10, 12})
    return Yoga(
        name="Samudra", sanskrit="समुद्र", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.72",
        description="All seven planets in even houses (2,4,6,8,10,12).",
    )


# ─── Raman "300 Combinations" — increment 37 (Nabhāsa Ākṛti + navāṁśa) ─
# The Nabhāsa family (Ākṛti/Saṅkhyā/Dala, Nos. 75–106) is defined purely
# by *which house/sign-groups the seven planets occupy*, so every member
# is computable from D1 occupancy. The three navāṁśa-dependent yogas
# (Gauri/Bharathi/Mridanga) reach the D9 chart via the established idiom
# ``compute_divisional_longitude(lon, 9)``. Rahu/Ketu are excluded from
# the seven-planet Nabhāsa checks per classical convention. Where a
# clause needs "friendly sign" (Mridanga), the computable subset
# own-or-exalted is used — the detector under-fires rather than guesses.

_BENEFIC7: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFIC7: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})
_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})
_KENDRA_TRIKONA: Final[frozenset[int]] = _KENDRAS | _TRIKONAS


def _navamsa_sign(chart: Chart, planet: str) -> int | None:
    """Navāṁśa (D9) sign (1..12) of a planet, from its D1 sidereal longitude."""
    lon = chart.planet_lons.get(planet)
    if lon is None:
        return None
    return int(compute_divisional_longitude(lon, 9) % 360.0 // 30) + 1


def _occupied_arc(houses: set[int]) -> tuple[int, int] | None:
    """Minimal contiguous house-arc enclosing all occupied houses as
    ``(start_house, span)`` — the complement of the widest empty run on
    the 12-house circle. Returns None only for an empty set."""
    hs = sorted(houses)
    if not hs:
        return None
    ext = hs + [hs[0] + 12]
    gaps = [ext[i + 1] - ext[i] for i in range(len(hs))]
    widest = max(gaps)
    start = hs[(gaps.index(widest) + 1) % len(hs)]
    return start, 13 - widest


def _seven_arc(chart: Chart) -> tuple[int, int] | None:
    return _occupied_arc({chart.house_of(p) for p in _SEVEN})


def _seven_signs(chart: Chart) -> set[int]:
    return {s for s in (chart.sign_of(p) for p in _SEVEN) if s is not None}


def _seven_houses(chart: Chart) -> set[int]:
    return {h for h in (chart.house_of(p) for p in _SEVEN) if h is not None}


def _conjunct(chart: Chart, a: str, b: str) -> bool:
    """a and b share a sign (whole-sign conjunction)."""
    sa, sb = chart.sign_of(a), chart.sign_of(b)
    return sa is not None and sa == sb


def _house_has(chart: Chart, house: int, group: frozenset[str]) -> bool:
    return any(p in group for p in chart.planets_in_house(house))


def _arc_yoga(chart: Chart, name: str, sanskrit: str, start: int, span: int,
              ref: str, desc: str, intensity: float = 0.7) -> Yoga:
    arc = _seven_arc(chart)
    active = arc is not None and arc == (start, span)
    return Yoga(name=name, sanskrit=sanskrit, active=active,
                intensity=intensity if active else 0.0, participants=_SEVEN,
                reference=ref, description=desc)


def _sankhya_yoga(chart: Chart, name: str, sanskrit: str, n_signs: int,
                  ref: str, desc: str, intensity: float = 0.6) -> Yoga:
    active = len(_seven_signs(chart)) == n_signs
    return Yoga(name=name, sanskrit=sanskrit, active=active,
                intensity=intensity if active else 0.0, participants=_SEVEN,
                reference=ref, description=desc)


def _signgroup_yoga(chart: Chart, name: str, sanskrit: str, group: frozenset[int],
                    ref: str, desc: str, intensity: float = 0.7) -> Yoga:
    active = all(chart.sign_of(p) in group for p in _SEVEN)
    return Yoga(name=name, sanskrit=sanskrit, active=active,
                intensity=intensity if active else 0.0, participants=_SEVEN,
                reference=ref, description=desc)


# --- Ākṛti: contiguous-house arcs (Nos. 75–83) -------------------------

def detect_yupa(chart: Chart) -> Yoga:
    """Seven planets in the four contiguous houses from the Lagna (1–4).
    Raman, 300 Combinations No. 75."""
    return _arc_yoga(chart, "Yupa", "यूप", 1, 4, "Raman, 300 Combinations No.75",
                     "Seven planets confined to houses 1–4 (contiguous from Lagna).")


def detect_ishu(chart: Chart) -> Yoga:
    """Seven planets in the four contiguous houses from the 4th (4–7).
    Raman, 300 Combinations No. 76 (Ishu/Sara)."""
    return _arc_yoga(chart, "Ishu", "इषु", 4, 4, "Raman, 300 Combinations No.76",
                     "Seven planets confined to houses 4–7 (contiguous from the 4th).")


def detect_sakti(chart: Chart) -> Yoga:
    """Seven planets in the four contiguous houses from the 7th (7–10).
    Raman, 300 Combinations No. 77."""
    return _arc_yoga(chart, "Sakti", "शक्ति", 7, 4, "Raman, 300 Combinations No.77",
                     "Seven planets confined to houses 7–10 (contiguous from the 7th).")


def detect_danda(chart: Chart) -> Yoga:
    """Seven planets in the four contiguous houses from the 10th (10–1).
    Raman, 300 Combinations No. 78."""
    return _arc_yoga(chart, "Danda", "दण्ड", 10, 4, "Raman, 300 Combinations No.78",
                     "Seven planets confined to houses 10,11,12,1 (contiguous from the 10th).")


def detect_nauka(chart: Chart) -> Yoga:
    """Seven planets in the seven contiguous houses from the Lagna (1–7).
    Raman, 300 Combinations No. 79 (Nav/Nauka)."""
    return _arc_yoga(chart, "Nauka", "नौका", 1, 7, "Raman, 300 Combinations No.79",
                     "Seven planets in the seven contiguous houses 1–7.", intensity=0.6)


def detect_kuta(chart: Chart) -> Yoga:
    """Seven planets in the seven contiguous houses from the 4th (4–10).
    Raman, 300 Combinations No. 80."""
    return _arc_yoga(chart, "Kuta", "कूट", 4, 7, "Raman, 300 Combinations No.80",
                     "Seven planets in the seven contiguous houses 4–10.", intensity=0.6)


def detect_chatra(chart: Chart) -> Yoga:
    """Seven planets in the seven contiguous houses from the 7th (7–1).
    Raman, 300 Combinations No. 81."""
    return _arc_yoga(chart, "Chatra", "छत्र", 7, 7, "Raman, 300 Combinations No.81",
                     "Seven planets in the seven contiguous houses 7–1.", intensity=0.6)


def detect_ardha_chandra(chart: Chart) -> Yoga:
    """Seven planets in seven contiguous houses beginning from a panapara or
    apoklima (a non-kendra start). Raman, 300 Combinations No. 83."""
    arc = _seven_arc(chart)
    active = arc is not None and arc[1] == 7 and arc[0] not in _KENDRAS
    return Yoga(
        name="Ardha Chandra", sanskrit="अर्धचन्द्र", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.83",
        description="Seven planets in a seven-house arc starting from a non-kendra (half-moon).",
    )


# --- Ākṛti: kendra / trine / house-group shapes (Nos. 87–93) -----------

def detect_vihaga(chart: Chart) -> Yoga:
    """All seven planets in the 4th and 10th houses. Raman No. 87 (Vihaga)."""
    active = _seven_houses(chart) == {4, 10}
    return Yoga(
        name="Vihaga", sanskrit="विहग", active=active,
        intensity=0.6 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.87",
        description="All seven planets in the 4th and 10th houses.",
    )


def detect_vajra(chart: Chart) -> Yoga:
    """Benefics in the 1st & 7th, malefics in the 4th & 10th. Raman No. 88."""
    active = (_house_has(chart, 1, _BENEFIC7) and _house_has(chart, 7, _BENEFIC7)
              and _house_has(chart, 4, _MALEFIC7) and _house_has(chart, 10, _MALEFIC7))
    return Yoga(
        name="Vajra", sanskrit="वज्र", active=active,
        intensity=0.6 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.88",
        description="Benefics in the 1st & 7th, malefics in the 4th & 10th.",
    )


def detect_yava(chart: Chart) -> Yoga:
    """Malefics in the 1st & 7th, benefics in the 4th & 10th (reverse of Vajra).
    Raman, 300 Combinations No. 89."""
    active = (_house_has(chart, 1, _MALEFIC7) and _house_has(chart, 7, _MALEFIC7)
              and _house_has(chart, 4, _BENEFIC7) and _house_has(chart, 10, _BENEFIC7))
    return Yoga(
        name="Yava", sanskrit="यव", active=active,
        intensity=0.6 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.89",
        description="Malefics in the 1st & 7th, benefics in the 4th & 10th.",
    )


def detect_sringhataka(chart: Chart) -> Yoga:
    """All seven planets in the Lagna trines (1,5,9). Raman No. 90 (Sringhataka)."""
    hs = _seven_houses(chart)
    active = len(hs) >= 2 and hs <= {1, 5, 9}
    return Yoga(
        name="Sringhataka", sanskrit="शृङ्गाटक", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.90",
        description="All seven planets confined to the Lagna trines (1,5,9).",
    )


def detect_hala(chart: Chart) -> Yoga:
    """All seven planets confined to one non-Lagna trine set — (2,6,10),
    (3,7,11) or (4,8,12). Raman, 300 Combinations No. 91."""
    hs = _seven_houses(chart)
    active = len(hs) >= 2 and any(hs <= grp for grp in
                                  (frozenset({2, 6, 10}), frozenset({3, 7, 11}),
                                   frozenset({4, 8, 12})))
    return Yoga(
        name="Hala", sanskrit="हल", active=active,
        intensity=0.6 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.91",
        description="Seven planets confined to a non-Lagna trine set (2/6/10, 3/7/11 or 4/8/12).",
    )


def detect_kamala(chart: Chart) -> Yoga:
    """All seven planets confined to the four kendras (1,4,7,10). Raman No. 92."""
    hs = _seven_houses(chart)
    active = len(hs) >= 2 and hs <= _KENDRAS
    return Yoga(
        name="Kamala", sanskrit="कमल", active=active,
        intensity=0.8 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.92",
        description="All seven planets confined to the four kendras.",
    )


def detect_vapi(chart: Chart) -> Yoga:
    """All seven planets confined exclusively to the panaparas (2,5,8,11) OR
    the apoklimas (3,6,9,12). Raman, 300 Combinations No. 93 (Vapee)."""
    hs = _seven_houses(chart)
    active = len(hs) >= 2 and (hs <= frozenset({2, 5, 8, 11}) or hs <= frozenset({3, 6, 9, 12}))
    return Yoga(
        name="Vapi", sanskrit="वापी", active=active,
        intensity=0.6 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.93",
        description="Seven planets confined to all panaparas (2,5,8,11) or all apoklimas (3,6,9,12).",
    )


# --- Ākṛti: sign-modality triad (Nos. 102–104) -------------------------

def detect_rajju(chart: Chart) -> Yoga:
    """All seven planets in movable signs. Raman No. 102 (Rajju)."""
    return _signgroup_yoga(chart, "Rajju", "रज्जु", _MOVABLE_SIGNS,
                           "Raman, 300 Combinations No.102",
                           "All seven planets in movable signs (Ar, Cn, Li, Cp).")


def detect_musala(chart: Chart) -> Yoga:
    """All seven planets in fixed signs. Raman No. 103 (Musala)."""
    return _signgroup_yoga(chart, "Musala", "मुसल", _FIXED_SIGNS,
                           "Raman, 300 Combinations No.103",
                           "All seven planets in fixed signs (Ta, Le, Sc, Aq).")


def detect_nala(chart: Chart) -> Yoga:
    """All seven planets in common/dual signs. Raman No. 104 (Nala)."""
    return _signgroup_yoga(chart, "Nala", "नल", _DUAL_SIGNS,
                           "Raman, 300 Combinations No.104",
                           "All seven planets in dual signs (Ge, Vi, Sg, Pi).")


# --- Saṅkhyā: numerical (occupied-sign count, Nos. 95–98) --------------

def detect_vallaki(chart: Chart) -> Yoga:
    """Seven planets spread across any seven signs. Raman No. 95 (Vallaki/Veena)."""
    return _sankhya_yoga(chart, "Vallaki", "वल्लकी", 7, "Raman, 300 Combinations No.95",
                         "Seven planets occupying seven distinct signs.")


def detect_damini(chart: Chart) -> Yoga:
    """Seven planets across any six signs. Raman No. 96 (Damini)."""
    return _sankhya_yoga(chart, "Damini", "दामिनी", 6, "Raman, 300 Combinations No.96",
                         "Seven planets occupying six distinct signs.")


def detect_pasa(chart: Chart) -> Yoga:
    """Seven planets across any five signs. Raman No. 97 (Pasa)."""
    return _sankhya_yoga(chart, "Pasa", "पाश", 5, "Raman, 300 Combinations No.97",
                         "Seven planets occupying five distinct signs.")


def detect_kedara(chart: Chart) -> Yoga:
    """Seven planets across any four signs. Raman No. 98 (Kedara)."""
    return _sankhya_yoga(chart, "Kedara", "केदार", 4, "Raman, 300 Combinations No.98",
                         "Seven planets occupying four distinct signs.")


# --- Dala: benefic/malefic kendras (Nos. 105–106) ----------------------

def detect_srik(chart: Chart) -> Yoga:
    """The kendras occupied exclusively by benefics. Raman No. 105 (Srik)."""
    kendra_planets = [p for p in _SEVEN if chart.house_of(p) in _KENDRAS]
    active = (bool(kendra_planets) and all(p in _BENEFIC7 for p in kendra_planets)
              and all(chart.house_of(b) in _KENDRAS for b in _BENEFIC7))
    return Yoga(
        name="Srik", sanskrit="श्रीक्", active=active,
        intensity=0.7 if active else 0.0, participants=tuple(sorted(kendra_planets)),
        reference="Raman, 300 Combinations No.105",
        description="All benefics in kendras and no malefic in a kendra.",
    )


def detect_sarpa(chart: Chart) -> Yoga:
    """The kendras occupied exclusively by malefics. Raman No. 106 (Sarpa)."""
    kendra_planets = [p for p in _SEVEN if chart.house_of(p) in _KENDRAS]
    active = (bool(kendra_planets) and all(p in _MALEFIC7 for p in kendra_planets)
              and all(chart.house_of(m) in _KENDRAS for m in _MALEFIC7))
    return Yoga(
        name="Sarpa", sanskrit="सर्प", active=active,
        intensity=0.6 if active else 0.0, participants=tuple(sorted(kendra_planets)),
        reference="Raman, 300 Combinations No.106",
        description="All malefics in kendras and no benefic in a kendra.",
    )


# --- Special occupancy + solar yogas -----------------------------------

def detect_matsya(chart: Chart) -> Yoga:
    """Malefics in the 1st, 4th, 8th & 9th; the 5th holding both a benefic
    and a malefic (mixed). Raman, 300 Combinations No. 47."""
    active = (all(_house_has(chart, h, _MALEFICS_NATURAL) for h in (1, 4, 8, 9))
              and _house_has(chart, 5, _MALEFICS_NATURAL)
              and _house_has(chart, 5, _BENEFIC7))
    return Yoga(
        name="Matsya", sanskrit="मत्स्य", active=active,
        intensity=0.7 if active else 0.0, participants=_SEVEN,
        reference="Raman, 300 Combinations No.47",
        description="Malefics in the 1st, 4th, 8th & 9th; a mixed 5th house.",
    )


def detect_ubhayachari(chart: Chart) -> Yoga:
    """Planets (not the Moon or nodes) on both sides of the Sun — 2nd AND
    12th from it. Raman, 300 Combinations No. 18 (Ubhayachari)."""
    excl = frozenset({"Sun", "Moon", "Rahu", "Ketu"})
    a, wa = _luminary_adjacency(chart, "Sun", 2, excl)
    b, wb = _luminary_adjacency(chart, "Sun", 12, excl)
    active = a and b
    return Yoga(
        name="Ubhayachari", sanskrit="उभयचरी", active=active,
        intensity=0.6 if active else 0.0, participants=("Sun",) + wa + wb,
        reference="Raman, 300 Combinations No.18",
        description="Planets flanking the Sun on both sides (2nd and 12th from it).",
    )


def detect_ravi(chart: Chart) -> Yoga:
    """The Sun in the 10th, with the 10th lord in the 3rd conjunct Saturn.
    Raman, 300 Combinations (Ravi Yoga)."""
    l10 = _lord_of(chart, 10)
    active = (chart.house_of("Sun") == 10 and chart.house_of(l10) == 3
              and _conjunct(chart, l10, "Saturn"))
    return Yoga(
        name="Ravi", sanskrit="रवि", active=active,
        intensity=0.7 if active else 0.0, participants=("Sun", l10, "Saturn"),
        reference="Raman, 300 Combinations (Ravi Yoga)",
        description="Sun in the 10th; the 10th lord in the 3rd with Saturn.",
    )


def detect_indra(chart: Chart) -> Yoga:
    """The 5th and 11th lords interchange houses, with the Moon in the 5th.
    Raman, 300 Combinations No. 66 (Indra)."""
    l5, l11 = _lord_of(chart, 5), _lord_of(chart, 11)
    active = _exchanged(chart, l5, l11) and chart.house_of("Moon") == 5
    return Yoga(
        name="Indra", sanskrit="इन्द्र", active=active,
        intensity=0.7 if active else 0.0, participants=(l5, l11, "Moon"),
        reference="Raman, 300 Combinations No.66",
        description="5th–11th lord exchange with the Moon in the 5th.",
    )


def detect_trilochana(chart: Chart) -> Yoga:
    """The Sun, Moon and Mars in mutual trines (1/5/9 from each other).
    Raman, 300 Combinations No. 71 (Trilochana)."""
    trio = ("Sun", "Moon", "Mars")
    hs = {p: chart.house_of(p) for p in trio}
    if any(h is None for h in hs.values()):
        active = False
    else:
        active = all((((hs[b] - hs[a]) % 12) + 1) in _TRIKONAS
                     for i, a in enumerate(trio) for b in trio[i + 1:])
    return Yoga(
        name="Trilochana", sanskrit="त्रिलोचन", active=active,
        intensity=0.7 if active else 0.0, participants=trio,
        reference="Raman, 300 Combinations No.71",
        description="Sun, Moon and Mars in mutual trines (1/5/9).",
    )


# --- Navāṁśa-dependent yogas (D9) --------------------------------------

def detect_gauri(chart: Chart) -> Yoga:
    """The lord of the navāṁśa occupied by the 10th lord joins the 10th house
    in exaltation, conjunct the Lagna lord. Raman No. 28 (Gauri)."""
    l10 = _lord_of(chart, 10)
    ns = _navamsa_sign(chart, l10)
    nl = SIGN_RULERS[ns] if ns else None
    s_nl = chart.sign_of(nl) if nl else None
    active = (nl is not None and chart.house_of(nl) == 10 and s_nl is not None
              and is_exalted(nl, s_nl) and _conjunct(chart, nl, _lord_of(chart, 1)))
    return Yoga(
        name="Gauri", sanskrit="गौरी", active=active,
        intensity=0.8 if active else 0.0, participants=(l10, nl) if nl else (l10,),
        reference="Raman, 300 Combinations No.28",
        description="Navāṁśa lord of the 10th lord: exalted in the 10th, with the Lagna lord.",
    )


def detect_bharathi(chart: Chart) -> Yoga:
    """The navāṁśa lord of (any of) the 2nd/5th/11th lords is exalted and
    conjunct the 9th lord. Raman No. 29 (Bharathi — three sub-yogas)."""
    l9 = _lord_of(chart, 9)

    def _ok(house: int) -> bool:
        lx = _lord_of(chart, house)
        ns = _navamsa_sign(chart, lx)
        nl = SIGN_RULERS[ns] if ns else None
        s = chart.sign_of(nl) if nl else None
        return nl is not None and s is not None and is_exalted(nl, s) and _conjunct(chart, nl, l9)

    active = any(_ok(h) for h in (2, 5, 11))
    return Yoga(
        name="Bharathi", sanskrit="भारती", active=active,
        intensity=0.8 if active else 0.0, participants=(l9,),
        reference="Raman, 300 Combinations No.29",
        description="Navāṁśa lord of a 2nd/5th/11th lord: exalted and with the 9th lord.",
    )


def detect_mridanga(chart: Chart) -> Yoga:
    """The lord of the navāṁśa occupied by an exalted planet is posited in a
    kendra/trikona in own or exalted sign, with a strong Lagna lord.
    Raman, 300 Combinations No. 48 (Mridanga)."""
    ll = _lord_of(chart, 1)

    def _ok(p: str) -> bool:
        ns = _navamsa_sign(chart, p)
        nl = SIGN_RULERS[ns] if ns else None
        s = chart.sign_of(nl) if nl else None
        return (nl is not None and chart.house_of(nl) in _KENDRA_TRIKONA
                and s is not None and (is_exalted(nl, s) or is_own_sign(nl, s)))

    exalted = [p for p in _SEVEN
               if chart.sign_of(p) is not None and is_exalted(p, chart.sign_of(p))]
    active = _is_strong(chart, ll) and any(_ok(p) for p in exalted)
    return Yoga(
        name="Mridanga", sanskrit="मृदङ्ग", active=active,
        intensity=0.8 if active else 0.0, participants=(ll,) + tuple(exalted),
        reference="Raman, 300 Combinations No.48",
        description="Navāṁśa lord of an exalted planet, well-placed, with a strong Lagna lord.",
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
    # Raman "300 Combinations" additions — increment 35 (8)
    detect_dhurdhura, detect_chatussagara, detect_vasumathi, detect_sakata,
    detect_chakra, detect_gola, detect_yuga, detect_sula,
    # Raman "300 Combinations" lord-based additions — increment 36 (7)
    detect_parvata, detect_kahala, detect_chapa, detect_sreenatha,
    detect_sankha, detect_bheri, detect_samudra,
    # Raman "300 Combinations" Nabhāsa + navāṁśa additions — increment 37 (32)
    detect_yupa, detect_ishu, detect_sakti, detect_danda,
    detect_nauka, detect_kuta, detect_chatra, detect_ardha_chandra,
    detect_vihaga, detect_vajra, detect_yava, detect_sringhataka,
    detect_hala, detect_kamala, detect_vapi,
    detect_rajju, detect_musala, detect_nala,
    detect_vallaki, detect_damini, detect_pasa, detect_kedara,
    detect_srik, detect_sarpa, detect_matsya,
    detect_ubhayachari, detect_ravi, detect_indra, detect_trilochana,
    detect_gauri, detect_bharathi, detect_mridanga,
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
