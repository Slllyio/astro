"""Master Reading composer — unified all-13-gap orchestration.

Wraps the existing 9-phase ``Reading`` (from ``reading_composer.py``)
with the 13 master-technique layers built in Gaps A-M. Output is a
``MasterReading`` dataclass with all layers populated (or None for
optional layers when their required inputs aren't provided).

## Layers wired (in evaluation order)

  Base    — compose_reading() : 9-phase Reading (Phases 1-9)
  Gap A   — ashtakavarga_predictive       (always available)
  Gap B   — varga_confirmations            (always available, D1-only fallback)
  Gap C   — yogini + ashtottari dashas    (needs moon_nakshatra + birth_jd)
  Gap D   — karakamsa + arudhas            (karakamsa needs AK + AK's D9 sign;
                                             arudhas always available)
  Gap E   — sensitive_points + upagrahas  (always; maandi needs day-of-week)
  Gap F   — baladi + deeptadi avastha     (always)
  Gap G   — vimsopaka bala                  (always; D1-only fallback)
  Gap H   — tara chakra at target          (needs moon_nakshatra + target's nakshatra)
  Gap J   — bhāvāt bhāvam common chains   (always)
  Gap K   — prashna                          (separate flow; NOT in master reading —
                                             call prashna_chart functions directly)
  Gap L   — remedies prescription            (always; per weak/afflicted planet)
  Gap M   — birth time rectification        (separate utility; NOT in master reading)

Gaps K and M are intentionally separate — Prashna is a different chart
paradigm, BTR is a search/optimisation procedure.

## Public entry point

  compose_master_reading(
      chart, context=DKPContext(),
      *, target_jd=None, birth_jd=None,
      atmakaraka=None, atmakaraka_d9_sign=None,
      moon_nakshatra_index=None, target_nakshatra_index=None,
      day_of_week=None, is_day_birth=None,
      vimshottari_md_lord=None, transit_signs=None,
      per_planet_varga_signs=None,
  ) -> MasterReading
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.core.bhava_bala import BhavaStrengthReport, compute_bhava_bala
from app.core.panchanga import BirthPanchanga, compute_birth_panchanga
from app.core.special_lagnas import (
    SpecialLagnasReport, compute_all_special_lagnas,
)
from app.core.varshaphala import VarshaphalaReport, compute_varshaphala
from app.core.ashtakavarga_predictive import (
    AshtakavargaPredictive, compute_predictive as compute_ashtakavarga_predictive,
)
from app.core.avastha_completion import (
    AvasthaReport, avastha_report, composite_avastha_multiplier,
)
from app.core.bhavat_bhavam import (
    BhavaFromBhava, common_chains, triple_lagna_view,
)
from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.karakamsa_arudha import (
    ArudhaPada, KarakamsaReading, all_arudhas, arudha_lagna,
    dara_pada, karakamsa_lagna, upapada_lagna,
)
from app.core.nakshatra_deep import TaraVerdict, tara_chakra
from app.core.reading_composer import Reading, compose_reading
from app.core.remedies import RemedyPrescription, prescribe
from app.core.sensitive_points import SensitivePointsReport, compute_all as compute_sensitive_points
from app.core.varga_confirmation import VargaConfirmation, varga_confirmation
from app.core.vimsopaka_bala import VimsopakaReport, vimsopaka_for_chart
from app.core.yogini_ashtottari_dasha import (
    AshtottariPeriod, YoginiPeriod, ashtottari_active_at,
    ashtottari_applicable, yogini_active_at,
)


@dataclass(frozen=True)
class MasterReading:
    """Unified reading with all 13 master-technique layers integrated."""

    # Base 9-phase reading (always present)
    base_reading: Reading

    # Gap A — Ashtakavarga predictive (always present)
    ashtakavarga: AshtakavargaPredictive

    # Gap B — Varga confirmation per bhava (D1-only fallback if no varga input)
    varga_confirmations: Mapping[int, VargaConfirmation]

    # Gap D — Arudha Padas (always present; Karakamsa optional)
    arudha_lagna: ArudhaPada
    upapada_lagna: ArudhaPada
    dara_pada: ArudhaPada
    all_arudhas: Mapping[int, ArudhaPada]
    karakamsa: KarakamsaReading | None

    # Gap E — Sensitive points + Upagrahas
    sensitive_points: SensitivePointsReport

    # Gap F — Avastha (Baladi + Deeptadi) for every visible planet
    avastha: AvasthaReport
    avastha_multipliers: Mapping[str, float]  # per-planet composite

    # Gap G — Vimsopaka Bala per planet
    vimsopaka: Mapping[str, VimsopakaReport]

    # Gap J — Bhāvāt Bhāvam common chains + per-bhava triple-Lagna views
    bhavat_chains: tuple[BhavaFromBhava, ...]
    triple_lagna_per_bhava: Mapping[int, Mapping[str, int]]

    # Gap C — Optional additional dashas (need moon_nakshatra + birth_jd)
    yogini_active: YoginiPeriod | None = None
    ashtottari_active: AshtottariPeriod | None = None
    ashtottari_applicable_flag: bool = False

    # Gap H — Tara Chakra at target nakshatra (need both moon_nakshatra + target_nakshatra)
    tara_at_target: TaraVerdict | None = None

    # Gap L — Prescribed remedies for weak planets
    prescribed_remedies: tuple[RemedyPrescription, ...] = ()

    # S-1 + S-5 — Cross-layer convergence verdicts per prediction domain.
    # When compose_master_reading is called with compute_convergence=True
    # (default), the engine scans 11 doctrinal layers for each of the
    # CORE_DOMAINS and attaches the ConvergenceVerdict here. UI / consumers
    # read this for the "reasoning trace" view.
    convergence_verdicts: Mapping[str, "ConvergenceVerdict"] = field(default_factory=dict)

    # S-2 part 1 — Birth Panchanga (Tithi/Yoga/Karana/Vara).
    # None if sun_lon, moon_lon, or birth_jd are absent.
    birth_panchanga: BirthPanchanga | None = None

    # S-2 part 2 — Intrinsic Bhava Bala per bhava. Always computable from chart.
    bhava_bala: Mapping[int, BhavaStrengthReport] = field(default_factory=dict)

    # S-3 — 5 special lagnas (Bhava/Hora/Ghati/Indu/Sree). IL + SL always
    # populate from chart-only; BL/HL/GL need birth_jd + birth_lon.
    special_lagnas: SpecialLagnasReport | None = None

    # S-4 — Varshaphala/Tajik progression at the snapshot age.
    # None if age_years can't be computed (need birth_jd + target_jd).
    varshaphala: VarshaphalaReport | None = None


_NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_NATURAL_MALEFICS = {"Sun", "Mars", "Saturn"}  # excluding nodes — no remedy formula

# Hard cap on prescriptions — a real astrologer never prescribes for all 7 grahas.
# Most charts get 0-2; only deeply afflicted charts reach 3.
MAX_PRESCRIPTIONS = 3

# Discrete-marker weakness threshold. A planet is prescribed for only if it
# accumulates ≥2 STRONG markers PLUS at least 1 WEAK corroboration (or all 3
# strong, the "perfect storm" of affliction). This matches Phaladeepika
# Ch.15's "tribhir adhikair vā" standard: three or more confirmations before
# committing to upaya. Score scale: STRONG marker = 0.5, WEAK marker = 0.25.
_WEAKNESS_THRESHOLD = 1.25


def _planet_weakness_score(
    vimsopaka_label: str, avastha_mult: float, in_dushtana: bool,
) -> float:
    """Discrete-tier weakness score 0..1.5. Higher = needs remedy.

    BPHS/Phaladeepika never prescribes on a single weakness signal —
    they require AT LEAST TWO independent afflictions (Phaladeepika
    Ch.15 v.7 — "ekena hi dūṣitenāpi grahena..."). This score
    operationalises that AND-gate by counting STRONG (0.5) and WEAK
    (0.25) markers across three classical axes:

      * Vimsopaka placement strength (varga-weighted)
          STRONG marker: VERY WEAK label
          WEAK marker: WEAK label
      * Avastha state-of-functioning (Baladi/Deeptadi composite)
          STRONG marker: multiplier < 0.20 (mrita/swapna)
          WEAK marker: multiplier < 0.40 (asakta/peeditadi)
      * House affliction (placed in 6/8/12)
          STRONG marker: dushtana placement (always significant)

    With _WEAKNESS_THRESHOLD = 1.0, a planet needs either two STRONG
    markers (e.g. very weak + dushtana) or one STRONG + two WEAK markers
    (e.g. dushtana + weak vims + low avastha). A single STRONG marker
    alone won't fire — which is the doctrinally correct stance.
    """
    score = 0.0
    if vimsopaka_label == "VERY WEAK":
        score += 0.5
    elif vimsopaka_label == "WEAK":
        score += 0.25
    if avastha_mult < 0.20:
        score += 0.5
    elif avastha_mult < 0.40:
        score += 0.25
    if in_dushtana:
        score += 0.5
    return score


def _diagnose_planet_condition(
    planet: str,
    vimsopaka_label: str,
    avastha_mult: float,
    is_functional_benefic: bool,
    is_functional_malefic: bool,
    in_dushtana: bool,
) -> str | None:
    """Diagnose the remedy-prescription condition for one planet.

    Returns one of: "weak_benefic" / "weak_malefic" / "strong_affliction" /
    "strong_benefic" / "lord_of_dushtana" / None.

    AND-gates weakness on BOTH Vimsopaka AND Avastha — D1-only-fallback
    runs (where every Vimsopaka label is structurally WEAK because D1
    weight=5/20) won't over-trigger.

    Dushtana alone no longer auto-fires — it goes through the rank-based
    weakness score in _build_prescriptions. A graha can be in 6/8/12
    and still be strong; classical astrology recognises Vipareeta Raja
    Yoga as the exemplar of this.
    """
    is_weak = (
        vimsopaka_label in ("WEAK", "VERY WEAK")
        and avastha_mult < 0.5
    )
    is_strong = vimsopaka_label in ("GOOD", "STRONG") and avastha_mult > 0.75

    if is_weak and planet in _NATURAL_BENEFICS:
        return "weak_benefic"
    if is_weak and planet in _NATURAL_MALEFICS:
        return "weak_malefic"
    if is_strong and is_functional_malefic:
        return "strong_affliction"
    if is_strong and is_functional_benefic:
        return "strong_benefic"
    if in_dushtana and is_weak:  # only when weakness ALSO confirmed
        return "lord_of_dushtana"
    return None


def _build_prescriptions(
    chart: Chart, vimsopaka: Mapping[str, VimsopakaReport],
    avastha_mults: Mapping[str, float],
) -> tuple[RemedyPrescription, ...]:
    """Generate remedy prescriptions for the chart's notable planets.

    Three-stage filter:
      1. Per-planet condition diagnosis (which kind of remedy, if any).
      2. Apply discrete-tier weakness score; only planets ≥_WEAKNESS_THRESHOLD
         pass. This enforces the ≥2-marker AND-gate doctrinally.
      3. Rank by weakness score, take top MAX_PRESCRIPTIONS.

    Result: most charts get 0-2 remedies; only deeply afflicted charts
    reach 3. Strong charts get 0, which is the doctrinally correct
    answer ("a balanced chart needs no upayas").
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    candidates: list[tuple[float, RemedyPrescription]] = []
    for planet in _NATURAL_BENEFICS | _NATURAL_MALEFICS:
        if planet not in vimsopaka:
            continue
        role = roles.get(planet)
        avastha_mult = avastha_mults.get(planet, 1.0)
        in_dushtana = (chart.house_of(planet) in {6, 8, 12})
        vims_label = vimsopaka[planet].strength_label
        condition = _diagnose_planet_condition(
            planet=planet,
            vimsopaka_label=vims_label,
            avastha_mult=avastha_mult,
            is_functional_benefic=role.is_functional_benefic if role else False,
            is_functional_malefic=role.is_functional_malefic if role else False,
            in_dushtana=in_dushtana,
        )
        if condition is None:
            continue
        score = _planet_weakness_score(vims_label, avastha_mult, in_dushtana)
        if score < _WEAKNESS_THRESHOLD:
            continue
        try:
            rx = prescribe(planet, condition, lagna_sign=chart.asc_sign)
        except (ValueError, KeyError):
            continue
        candidates.append((score, rx))

    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return tuple(rx for _, rx in candidates[:MAX_PRESCRIPTIONS])


def compose_master_reading(
    chart: Chart,
    context: DKPContext = DKPContext(),
    *,
    target_jd: float | None = None,
    birth_jd: float | None = None,
    atmakaraka: str | None = None,
    atmakaraka_d9_sign: int | None = None,
    moon_nakshatra_index: int | None = None,
    target_nakshatra_index: int | None = None,
    day_of_week: int | None = None,
    is_day_birth: bool | None = None,
    vimshottari_md_lord: str | None = None,
    transit_signs: Mapping[str, int] | None = None,
    per_planet_varga_signs: Mapping[str, Mapping[str, int]] | None = None,
    varga_pillar_scores: Mapping[int, float] | None = None,
    convergence_domains: tuple[str, ...] | None = None,
    birth_lon: float | None = None,
) -> MasterReading:
    """The framework's master entry point.

    Composes a 13-layer reading from a Chart + optional contextual data.
    Layers that need optional inputs degrade to None when those inputs
    are absent.

    Args:
        chart: The natal Chart.
        context: DKPContext for Phase 8 modulation.
        target_jd, birth_jd: For Phase 7 + dasha active-lookup.
        atmakaraka: AK planet name (if available from Jaimini karakas).
        atmakaraka_d9_sign: AK's D9 sign for Karakamsa Lagna.
        moon_nakshatra_index: 0..26 — needed for Yogini/Ashtottari + Tara.
        target_nakshatra_index: 0..26 — needed for Tara Chakra.
        day_of_week, is_day_birth: for Maandi computation.
        vimshottari_md_lord: passed through to base Reading.
        transit_signs: passed through to base Reading.
        per_planet_varga_signs: per-planet per-varga sign mappings for
            Vimsopaka Bala (D9, D10, etc.). If None, Vimsopaka uses
            D1-only fallback.
        varga_pillar_scores: per-bhava pre-computed varga pillar scores
            for Gap B confirmation. If None, all confirmations land
            on UNKNOWN.

    Returns:
        MasterReading with all 13 layers populated/None per available inputs.
    """
    # Base 9-phase reading
    base = compose_reading(
        chart, context,
        target_jd=target_jd, birth_jd=birth_jd,
        transit_signs=transit_signs,
        vimshottari_md_lord=vimshottari_md_lord,
    )

    # Gap A — Ashtakavarga predictive
    ashtakavarga = compute_ashtakavarga_predictive(chart)

    # Gap B — Varga confirmations per bhava
    varga_confs: dict[int, VargaConfirmation] = {}
    for b, claim in base.bhava_claims.items():
        d1_score = claim.composite_score
        varga_score = (
            varga_pillar_scores.get(b) if varga_pillar_scores else None
        )
        varga_confs[b] = varga_confirmation(b, d1_score, varga_score)

    # Gap D — Arudhas (always) + Karakamsa (optional)
    arudhas = all_arudhas(chart)
    al = arudha_lagna(chart)
    ul = upapada_lagna(chart)
    a7 = dara_pada(chart)
    karak = None
    if atmakaraka and atmakaraka_d9_sign:
        ak_d1_sign = chart.sign_of(atmakaraka)
        if ak_d1_sign:
            karak = karakamsa_lagna(atmakaraka, ak_d1_sign, atmakaraka_d9_sign)

    # Gap E — Sensitive points (Maandi optional)
    sens = compute_sensitive_points(
        chart, day_of_week=day_of_week, is_day_birth=is_day_birth,
    )

    # Gap F — Avastha
    av = avastha_report(chart)
    av_mults = {
        p: composite_avastha_multiplier(p, chart)
        for p in chart.planet_signs
        if p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    }

    # Gap G — Vimsopaka
    vims = vimsopaka_for_chart(chart, per_planet_varga_signs, scheme="saptavargaja")

    # Gap J — Bhāvāt Bhāvam
    chains = common_chains()
    triple_views = {b: triple_lagna_view(b, chart) for b in range(1, 13)}

    # Gap C — Optional dashas (need moon_nakshatra + birth_jd)
    yogini = None
    ashtot = None
    ashtot_applicable = False
    if moon_nakshatra_index is not None and birth_jd is not None and target_jd is not None:
        yogini = yogini_active_at(moon_nakshatra_index, birth_jd, target_jd)
        ashtot = ashtottari_active_at(moon_nakshatra_index, birth_jd, target_jd)
        # Check ashtottari applicability
        rahu_h = chart.house_of("Rahu")
        from app.core.functional_roles import functional_roles
        roles = functional_roles(chart.asc_sign)
        ll = next((p for p, r in roles.items() if 1 in r.houses_ruled), None)
        ll_h = chart.house_of(ll) if ll else None
        if rahu_h and ll_h:
            ashtot_applicable = ashtottari_applicable(rahu_h, ll_h)

    # Gap H — Tara at target
    tara = None
    if moon_nakshatra_index is not None and target_nakshatra_index is not None:
        tara = tara_chakra(moon_nakshatra_index, target_nakshatra_index)

    # Gap L — Prescribed remedies (synthesized from Vimsopaka + Avastha)
    prescriptions = _build_prescriptions(chart, vims, av_mults)

    mr = MasterReading(
        base_reading=base,
        ashtakavarga=ashtakavarga,
        varga_confirmations=varga_confs,
        arudha_lagna=al, upapada_lagna=ul, dara_pada=a7,
        all_arudhas=arudhas, karakamsa=karak,
        sensitive_points=sens,
        avastha=av, avastha_multipliers=av_mults,
        vimsopaka=vims,
        bhavat_chains=chains, triple_lagna_per_bhava=triple_views,
        yogini_active=yogini, ashtottari_active=ashtot,
        ashtottari_applicable_flag=ashtot_applicable,
        tara_at_target=tara,
        prescribed_remedies=prescriptions,
    )

    # S-2 part 1: Birth Panchanga (needs Sun+Moon longitudes + birth_jd).
    sun_lon = chart.planet_lons.get("Sun")
    moon_lon = chart.planet_lons.get("Moon")
    if (sun_lon is not None and moon_lon is not None
            and birth_jd is not None and moon_nakshatra_index is not None):
        try:
            panchanga = compute_birth_panchanga(
                sun_lon=float(sun_lon), moon_lon=float(moon_lon),
                birth_jd=float(birth_jd),
                moon_nakshatra_index=int(moon_nakshatra_index),
            )
        except (ValueError, TypeError):
            panchanga = None
    else:
        panchanga = None
    object.__setattr__(mr, "birth_panchanga", panchanga)

    # S-2 part 2: Bhava Bala (always computable from chart).
    try:
        bb = compute_bhava_bala(chart)
    except Exception:  # noqa: BLE001 — graceful degradation
        bb = {}
    object.__setattr__(mr, "bhava_bala", bb)

    # S-4: Varshaphala (Muntha + Sahams) at the target_jd snapshot age.
    if birth_jd is not None and target_jd is not None:
        age_years = max(0.0, (target_jd - birth_jd) / 365.2425)
        try:
            vp = compute_varshaphala(
                asc_sign=int(chart.asc_sign),
                asc_lon=float(chart.asc_lon),
                planet_lons={k: float(v) for k, v in chart.planet_lons.items()},
                age_years=age_years,
            )
            object.__setattr__(mr, "varshaphala", vp)
        except (ValueError, TypeError):
            pass

    # S-3: Special Lagnas (IL + SL always; BL/HL/GL need birth_jd + birth_lon).
    if moon_lon is not None and moon_nakshatra_index is not None:
        try:
            moon_sign = chart.planet_signs.get("Moon")
            if moon_sign is not None:
                sl_report = compute_all_special_lagnas(
                    asc_sign=int(chart.asc_sign),
                    asc_lon=float(chart.asc_lon),
                    sun_lon=float(sun_lon) if sun_lon is not None else 0.0,
                    moon_sign=int(moon_sign),
                    moon_lon=float(moon_lon),
                    moon_nakshatra_index=int(moon_nakshatra_index),
                    birth_jd=float(birth_jd) if birth_jd is not None else None,
                    birth_lon=float(birth_lon) if birth_lon is not None else None,
                )
                object.__setattr__(mr, "special_lagnas", sl_report)
        except (ValueError, TypeError):
            pass

    # S-1 + S-5: cross-layer convergence verdicts attached for the
    # caller-specified domains (defaults to CORE_DOMAINS).
    domains = convergence_domains if convergence_domains is not None else CORE_DOMAINS
    if domains:
        # Local import — convergence_engine reads from MasterReading, but
        # we attach its output back ON the MasterReading. Use object.__
        # setattr__ because MasterReading is frozen.
        from app.core.convergence_engine import convergence_verdict
        cv_map: dict[str, "ConvergenceVerdict"] = {}
        for d in domains:
            try:
                cv_map[d] = convergence_verdict(mr, d)
            except (ValueError, KeyError):
                continue
        object.__setattr__(mr, "convergence_verdicts", cv_map)
    return mr


# Default domain set for the bulk reading pipeline. Tuned to cover the
# 6 most-asked life questions in classical jyotisha consultations.
CORE_DOMAINS: tuple[str, ...] = (
    "marriage", "career", "wealth", "health", "children", "dharma",
)


def format_master_reading_text(mr: MasterReading) -> str:
    """Rich text rendering of the master reading — all 13 layers visible."""
    base = mr.base_reading
    lines: list[str] = []

    lines.append("=" * 72)
    lines.append("MASTER ASTROLOGER'S-LENS READING (13-layer integrated)")
    lines.append("=" * 72)

    # Identity
    if base.person_id:
        lines.append(f"Person: {base.person_id}")
    lines.append(f"Lagna sign: {base.asc_sign}  Lord: {base.asc_lagna_lord}")
    lines.append(f"Yogakaraka(s): {base.yogakarakas or '(none)'}")
    lines.append(f"Badhakesh: {base.badhakesh}")
    lines.append("")

    # Chart strength
    lines.append("CHART STRENGTH")
    lines.append(f"  {base.chart_strength_summary}")
    lines.append(f"  Strongest: {base.strongest_planet}   Weakest: {base.weakest_planet}")
    lines.append("")

    # Active dashas (Vimshottari + Chara + Yogini + Ashtottari)
    lines.append("ACTIVE DASHAS")
    if base.vimshottari_md_at_target:
        lines.append(f"  Vimshottari MD: {base.vimshottari_md_at_target}")
    if base.chara_md_at_target:
        lines.append(f"  Chara MD (sign): {base.chara_md_at_target}")
    if mr.yogini_active:
        lines.append(
            f"  Yogini MD: {mr.yogini_active.yogini_name} "
            f"({mr.yogini_active.presiding_planet}, {mr.yogini_active.period_years}y)"
        )
    if mr.ashtottari_applicable_flag and mr.ashtottari_active:
        lines.append(
            f"  Ashtottari MD: {mr.ashtottari_active.lord} "
            f"({mr.ashtottari_active.period_years}y) [applicable: Rahu in kendra/trine from LL]"
        )
    lines.append("")

    # Active yogas (from base)
    if base.active_yogas:
        lines.append(f"ACTIVE YOGAS ({len(base.active_yogas)})")
        for y in base.active_yogas:
            lines.append(f"  - {y.name:22s} intensity={y.intensity:.2f}  ref={y.reference}")
    lines.append("")

    # Karakamsa (soul-purpose)
    if mr.karakamsa:
        lines.append("KARAKAMSA (soul-purpose layer)")
        lines.append(f"  AK = {mr.karakamsa.atmakaraka} (D1 sign {mr.karakamsa.atmakaraka_d1_sign})")
        lines.append(f"  Karakamsa Lagna = sign {mr.karakamsa.karakamsa_sign}")
        for key_bhava in (5, 9, 10, 12):
            lines.append(f"    {key_bhava}H from K: {mr.karakamsa.bhava_readings[key_bhava]}")
    lines.append("")

    # Arudhas
    lines.append("ARUDHAS (projected image)")
    lines.append(f"  AL (1H Arudha — social mask): sign {mr.arudha_lagna.arudha_sign}")
    lines.append(f"  UL (12H Arudha — marriage indicator): sign {mr.upapada_lagna.arudha_sign}")
    lines.append(f"  A7 (7H Arudha — first spouse image): sign {mr.dara_pada.arudha_sign}")
    lines.append("")

    # Sensitive points
    sp = mr.sensitive_points
    lines.append("SENSITIVE POINTS")
    lines.append(f"  Bhrigu Bindu: sign {sp.bhrigu_bindu.sign} (h.{sp.bhrigu_bindu.natal_house})")
    lines.append(f"  Pranapada:    sign {sp.pranapada.sign} (h.{sp.pranapada.natal_house})")
    for name in ("Dhuma", "Vyatipata", "Upaketu"):
        u = sp.upagrahas[name]
        lines.append(f"  {name:11s}:  sign {u.sign} (h.{u.natal_house})")
    lines.append(f"  Beeja Sphuta:   {sp.beeja_sphuta.fertility_grade} ({sp.beeja_sphuta.dignity})")
    lines.append(f"  Kshetra Sphuta: {sp.kshetra_sphuta.fertility_grade} ({sp.kshetra_sphuta.dignity})")
    if sp.maandi:
        lines.append(f"  Maandi: sign {sp.maandi.sign} (h.{sp.maandi.natal_house})")
    lines.append("")

    # Vimsopaka + Avastha per planet
    lines.append("STRENGTH PER PLANET (Vimsopaka × Avastha)")
    lines.append(f"  {'Planet':10s} {'Vimsopaka':10s} {'Baladi':10s} {'Deeptadi':10s} {'Composite':>10s}")
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        if p not in mr.vimsopaka:
            continue
        v = mr.vimsopaka[p]
        b = mr.avastha.baladi.get(p)
        d = mr.avastha.deeptadi.get(p)
        mult = mr.avastha_multipliers.get(p, 1.0)
        lines.append(
            f"  {p:10s} {v.strength_label:10s} "
            f"{b.stage if b else '-':10s} {d.state if d else '-':10s} "
            f"{mult:>10.2f}"
        )
    lines.append("")

    # Tara at target
    if mr.tara_at_target:
        t = mr.tara_at_target
        flag = "AUSPICIOUS" if t.is_auspicious else "INAUSPICIOUS"
        lines.append(f"TARA CHAKRA at target: {t.tara_label} ({flag})")
        lines.append("")

    # Ashtakavarga predictive
    av = mr.ashtakavarga
    lines.append(f"ASHTAKAVARGA — strongest bhava: {av.strongest_bhava} "
                 f"({av.sav_per_bhava[av.strongest_bhava].sav_points} SAV pts); "
                 f"weakest: {av.weakest_bhava} ({av.sav_per_bhava[av.weakest_bhava].sav_points} pts)")
    lines.append("")

    # Per-bhava reading with varga confirmation + Bhāvāt Bhāvam triple view
    lines.append("PER-BHAVA VERDICTS")
    for b in range(1, 13):
        claim = base.bhava_claims[b]
        conf = mr.varga_confirmations.get(b)
        triple = mr.triple_lagna_per_bhava.get(b, {})
        trig = " [TRIGGERED]" if claim.gochara_triggered else ""
        lines.append(
            f"  Bhava {b:2d}  {claim.verdict_label:>10s}  "
            f"composite={claim.composite_score:+.2f}  "
            f"varga={conf.confirmation_label if conf else '-':>22s}{trig}"
        )
        lines.append(f"          focus: {claim.reading_focus}")
        lines.append(
            f"          from-Moon: {triple.get('from_moon', '?')}  "
            f"from-Sun: {triple.get('from_sun', '?')}"
        )
        if claim.confirming_yogas:
            lines.append(f"          confirming: {', '.join(claim.confirming_yogas)}")
        if claim.key_findings:
            for f in claim.key_findings[:2]:  # cap at 2 in master view
                lines.append(f"          - {f}")
    lines.append("")

    # Remedies
    if mr.prescribed_remedies:
        lines.append("PRESCRIBED REMEDIES")
        for rx in mr.prescribed_remedies:
            lines.append(
                f"  {rx.planet:10s} condition={rx.condition:20s} "
                f"→ {', '.join(rx.recommended_remedies)} (gem: {rx.gemstone_caveat})"
            )
            lines.append(f"          {rx.rationale}")
        lines.append("")

    # Open questions
    if base.open_questions:
        lines.append("OPEN CLARIFYING QUESTIONS")
        for q in base.open_questions:
            lines.append(f"  ? {q}")

    return "\n".join(lines)
