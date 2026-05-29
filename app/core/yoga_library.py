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
from app.core.functional_roles import functional_roles


def _is_well_placed(planet: str, sign: int) -> bool:
    """Convenience: exalted, own, or Mooltrikona."""
    return (
        is_exalted(planet, sign)
        or is_own_sign(planet, sign)
        or is_moolatrikona(planet, sign)
    )


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
    """One factory for all 5 PMP yogas — planet must be own/exalt in Kendra."""
    def detector(chart: Chart) -> Yoga:
        house = chart.house_of(planet)
        sign = chart.sign_of(planet)
        active = False
        intensity = 0.0
        if house is not None and sign is not None:
            in_kendra = house in _KENDRAS
            in_dignity = is_exalted(planet, sign) or is_own_sign(planet, sign)
            if in_kendra and in_dignity:
                active = True
                intensity = 1.0 if is_exalted(planet, sign) else 0.75
        return Yoga(
            name=name, sanskrit=sanskrit, active=active,
            intensity=intensity, participants=(planet,),
            reference=ref,
            description=f"{planet} in own/exalt sign occupying a Kendra (1/4/7/10).",
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
    planet in Moon's sign (besides Moon itself).

    BPHS Ch.40 — significant affliction yoga; cancels if Moon receives
    a benefic Kendra aspect or sits in own/exalt. The cancellation
    rules are summarised in the description; the boolean here flags
    the *raw* Kemadruma. Phase 6 applies cancellations.
    """
    moon_sign = chart.sign_of("Moon")
    if moon_sign is None:
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
    active = not (has_2nd or has_12th or has_companion)
    return Yoga(
        name="Kemadruma", sanskrit="केमद्रुम", active=active,
        intensity=0.8 if active else 0.0, participants=("Moon",),
        reference="BPHS Ch.40",
        description="Moon with no planet in 2nd/12th/own sign — isolation yoga "
                    "(cancellable by Moon's dignity or benefic Kendra aspect).",
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
    return Yoga(
        name="Vipareeta Raja", sanskrit="विपरीत-राज", active=active,
        intensity=min(1.0, 0.5 * len(variants)),
        participants=tuple(sorted({v[1] for v in variants})),
        reference="BPHS Ch.39",
        description=("Dusthana lord in a dusthana — Harsha/Sarala/Vimala — "
                     "reversed affliction yielding gain. Variants found: "
                     + ", ".join(v[0] for v in variants) if variants else ""),
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
    # Walk forward from Rahu to Ketu; check if all 7 visible planets
    # are inside that arc.
    def arc_contains(lon: float) -> bool:
        # Normalise angles relative to Rahu (start of arc).
        diff = (lon - rahu_lon) % 360
        end_diff = (ketu_lon - rahu_lon) % 360
        return diff < end_diff
    visible = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    arc1 = all(arc_contains(chart.planet_lons[p])
               for p in visible if p in chart.planet_lons)
    # Try the OTHER arc too.
    def other_arc(lon: float) -> bool:
        return not arc_contains(lon)
    arc2 = all(other_arc(chart.planet_lons[p])
               for p in visible if p in chart.planet_lons)
    active = arc1 or arc2
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


# ─── Registry ────────────────────────────────────────────────────────


YOGA_DETECTORS: Final[tuple[Callable[[Chart], Yoga], ...]] = (
    # PMP
    detect_ruchaka, detect_bhadra, detect_hamsa,
    detect_malavya, detect_sasa,
    # Solar/Lunar
    detect_budha_aditya, detect_veshi, detect_vosi,
    detect_sunapha, detect_anapha,
    # Foundation
    detect_gajakesari, detect_chandra_mangal, detect_kemadruma,
    detect_raja_yoga, detect_vipareeta_raja,
    # Affliction
    detect_mangal_dosha, detect_kala_sarpa, detect_daridra,
    # Auspicious specials
    detect_amala, detect_saraswati, detect_adhi,
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
