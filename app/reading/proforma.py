"""Main orchestrator for `app.reading`.

Two-function pattern per spec Section 5 (Data flow / Public-vs-private
orchestration):

- `_run_core_pipeline` — private, deterministic, Stages 1-7. No RAG. No
  recursion. Birth-time-robustness MUST import this directly (rather than
  `compute`) to avoid recursion through Tier-3 modules that re-invoke the
  engine on time perturbations.
- `compute` — public; runs the core pipeline and, when `enrich=True`,
  layers Tier-3 enrichments (citations, consensus, dispute, robustness,
  contradiction detection) via `_apply_tier3_enrichments`.

Phase 7 wiring discipline:

- Each downstream module call is wrapped in try/except. Failures are
  collected into the top-level ``warnings`` block and never propagated as
  exceptions — the engine must not crash a user. This is the
  graceful-degradation contract.
- Tier-3 lazy-import discipline: ``rag_citations``, ``consensus_scoring``,
  ``dispute_surfacing``, ``yoga_calibration``, ``contradiction_detector``,
  and ``birth_time_robustness`` are imported INSIDE
  ``_apply_tier3_enrichments`` so the ``--no-enrich`` path never loads
  ``sentence_transformers`` / ``torch``.
- ``birth_time_robustness`` re-enters the engine through
  ``_run_core_pipeline`` (the private entry-point), NOT ``compute``, to
  avoid unbounded Tier-3 recursion.
"""
from __future__ import annotations

import logging
import re as _re
import sys
from datetime import UTC, datetime
from typing import Any, Callable

from app.reading.schema import (
    ChartBlock,
    ChartInput,
    ClassicalYoga,
    Contradiction,
    DoctrineConfig,
    DomainsBlock,
    Finding,
    FoundationsBlock,
    Meta,
    PractitionerBlock,
    PrimitivesBlock,
    ReadingOutput,
    SequencesBlock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine version sourcing
# ---------------------------------------------------------------------------

_ENGINE_VERSION_FALLBACK = "0.0.0+phase7"


def _engine_version() -> str:
    """Best-effort engine version string."""
    return _ENGINE_VERSION_FALLBACK


def _swiss_ephemeris_version() -> str:
    """Swiss Ephemeris library version, or ``"unknown"`` if unavailable."""
    try:
        import swisseph as swe

        return str(swe.version)
    except Exception:  # pragma: no cover - swisseph is a hard dep in this repo
        logger.warning("swisseph version unavailable; defaulting to 'unknown'")
        return "unknown"


def _python_version() -> str:
    """Tuple-style Python version string, e.g. ``"3.12.10"``."""
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"


def _generated_at_iso() -> str:
    """Current UTC instant as ISO-8601 (timezone-aware)."""
    return datetime.now(UTC).isoformat()


_GRAHAS_9: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def _classical_yogas(
    d1_chart: dict[str, Any], asc_sign: int, lagna_longitude: float,
) -> list[ClassicalYoga]:
    """Run the core 88-detector yoga library over the D1 chart and return the
    active yogas with their classical citations, for the reading's
    classical-yogas section. Fail-soft: any error yields ``[]`` so a missing
    or partial chart never blocks a reading."""
    try:
        from app.core.chart_model import Chart
        from app.core.yoga_library import active_yogas

        signs: dict[str, int] = {}
        lons: dict[str, float] = {}
        for g in _GRAHAS_9:
            entry = d1_chart.get(g) or {}
            if entry.get("sign") is not None and entry.get("longitude") is not None:
                signs[g] = int(entry["sign"])
                lons[g] = float(entry["longitude"])
        if len(signs) < len(_GRAHAS_9):
            return []
        houses = {g: ((signs[g] - asc_sign) % 12) + 1 for g in signs}
        chart = Chart(
            planet_signs=signs, planet_houses=houses, planet_lons=lons,
            asc_sign=asc_sign, asc_lon=lagna_longitude,
        )
        return [
            ClassicalYoga(
                name=y.name, sanskrit=y.sanskrit, reference=y.reference,
                description=y.description, intensity=round(float(y.intensity), 3),
                participants=tuple(y.participants),
            )
            for y in active_yogas(chart)
        ]
    except Exception:  # noqa: BLE001 — cosmetic section; never block a reading
        return []


def _dasha_activation(d1_chart: dict[str, Any], lagna_longitude: float) -> dict[str, Any]:
    """Per-graha bhāva activation following Raman's ENCODED HTJAH influence
    doctrine — faithfully mirrors ``_influence_factors`` / ``_pair_tier`` in
    ``app/medini/doctrine/domains/house_judgment.py`` (HTJAH Vol.I ch.IV,
    pp.44-48). A planet **activates house H** by any of Raman's six factors:

      (a) owns H · (b) occupies H · (c) aspects H (graha dṛṣṭi) ·
      (d) aspects H's lord · (e) conjoins H's lord · (f) is lord of H from the Moon.

    The period's fructification tier (computed client-side from the two lords'
    influence maps) is par-excellence/predominant when BOTH the MD and AD lords
    influence H, limited when one does, dormant when neither — the doctrine's
    fully / partial / none. (The engine's ``_influence_factors`` needs a heavy
    ``RamanChart``/``ChartBundle``; this reuses the identical rule on the
    reading's D1 primitives.) Fail-soft."""
    try:
        from app.core.dignity import SIGN_RULERS
        from app.core.drishti_argala import aspects_from_planet

        lagna_sign = int(lagna_longitude % 360.0 // 30) + 1
        ph: dict[str, int] = {}      # planet -> whole-sign house from Lagna
        moon_sign: int | None = None
        for g in _GRAHAS_9:
            s = (d1_chart.get(g) or {}).get("sign")
            if s is None:
                continue
            ph[g] = ((int(s) - lagna_sign) % 12) + 1
            if g == "Moon":
                moon_sign = int(s)
        if moon_sign is None or len(ph) < len(_GRAHAS_9):
            return {}

        def lord_of(house: int) -> str:                      # sign-lord of Hth bhava
            return SIGN_RULERS[((lagna_sign - 1 + house - 1) % 12) + 1]

        def lord_from_moon(house: int) -> str:               # factor (f)
            return SIGN_RULERS[((moon_sign + house - 2) % 12) + 1]

        def factors(planet: str, house: int) -> list[str]:
            lord = lord_of(house)
            asp = aspects_from_planet(planet, ph[planet])
            facs: list[str] = []
            if planet == lord:
                facs.append("owns")
            if ph[planet] == house:
                facs.append("occupies")
            if house in asp:
                facs.append("aspects house")
            if planet != lord:
                if ph[lord] in asp:
                    facs.append("aspects lord")
                if ph[planet] == ph[lord]:
                    facs.append("conjoins lord")
            if planet == lord_from_moon(house) and "owns" not in facs:
                facs.append("lord from Moon")
            return facs

        planets: dict[str, dict[str, Any]] = {}
        for g in ph:
            infl = {str(h): f for h in range(1, 13) if (f := factors(g, h))}
            planets[g] = {"occ": ph[g],
                          "aspects": list(aspects_from_planet(g, ph[g])),
                          "influences": infl}
        return {"lagna_sign": lagna_sign, "planets": planets}
    except Exception:  # noqa: BLE001
        return {}


def _divisional_lagnas(lagna_longitude: float) -> dict[str, int]:
    """Ascendant sign (1..12) in D1/D9/D10 — lets the view mark the lagna cell in
    the divisional chart grids. Fail-soft."""
    try:
        from app.core.shodashavarga import compute_divisional_longitude

        out = {"D1": int(lagna_longitude % 360 // 30) + 1}
        for name, div in (("D9", 9), ("D10", 10), ("D7", 7), ("D12", 12)):
            out[name] = int(compute_divisional_longitude(lagna_longitude, div) % 360.0 // 30) + 1
        return out
    except Exception:  # noqa: BLE001
        return {}


# ---------------------------------------------------------------------------
# "Present tense" + real-doctrine enrichments (Phase 0 + Phase 1).
#
# These turn a birth-frozen developer report into a consultation:
#   - dasha_now:      the mahādaśā/antardaśā running TODAY (not at birth) —
#                     fixes the "Current Mahadasha: Venus 1957-1977" for a
#                     1970 native. Reuses app/integration/dasha_now.
#   - transits_now:   live gochara (Sade-Sati, Saturn-from-Moon, double
#                     transits). Reuses app/integration/transit_engine.
#   - house_doctrine: the real encoded Raman per-house verdicts from
#                     judge_all_houses_doctrine — the SAME engine validated
#                     all session — giving honest grades + the "why" factors
#                     + Rāśi/Navāṁśa agreement + the running-daśā activation
#                     tier per house.
#   - executive_summary: a deterministic lay-language restatement of the
#                     above (no invented numbers).
#
# Every block is fail-soft: any error yields an empty section, never a
# broken reading. All output lands under chart.extras.* (a free-form dict),
# so nothing here can break the ReadingOutput schema.
# ---------------------------------------------------------------------------

# Plain-language life area per whole-sign house (for the lay summary).
_HOUSE_LIFE_AREA: dict[int, str] = {
    1: "self, body & vitality",
    2: "wealth, speech & family",
    3: "courage, siblings & effort",
    4: "home, mother & inner peace",
    5: "children, creativity & intellect",
    6: "health, service & adversaries",
    7: "marriage & partnerships",
    8: "longevity, upheaval & the hidden",
    9: "fortune, dharma & the father",
    10: "career & public standing",
    11: "gains, income & aspirations",
    12: "loss, expenditure & liberation",
}


def _verdict_index(label: str) -> int | None:
    """Position of a Raman verdict on the 9-grade VERDICT_SCALE (0..8), or None.

    afflicted(0) … moderate(2) … fairly good(4) … very powerful(8).
    """
    scale = (
        "afflicted", "weak", "moderate", "moderately good", "fairly good",
        "fairly strong", "fairly powerful", "very strong", "very powerful",
    )
    try:
        return scale.index(str(label).strip().lower())
    except ValueError:
        return None


def _factor_to_dict(fv: Any) -> dict[str, Any]:
    """Serialise a FactorVerdict into a JSON-friendly dict for the view.

    Keeps the real findings (the "why"), the grade + its 0..8 index, and the
    Rāśi vs Navāṁśa sub-scores (the D1/D9 agreement)."""
    idx = _verdict_index(getattr(fv, "label", ""))
    return {
        "role": getattr(fv, "role", ""),
        "subject": getattr(fv, "subject", ""),
        "label": getattr(fv, "label", ""),
        "grade_index": idx,                       # 0..8 on VERDICT_SCALE
        "score": round(float(getattr(fv, "score", 0.0)), 3),
        "rasi_score": round(float(getattr(fv, "rasi_score", 0.0)), 3),
        "navamsa_score": round(float(getattr(fv, "navamsa_score", 0.0)), 3),
        "findings": [
            {
                "text": getattr(f, "text", ""),
                "delta": round(float(getattr(f, "delta", 0.0)), 3),
                "frame": getattr(f, "frame", ""),
                "criterion": getattr(f, "criterion", ""),
            }
            for f in getattr(fv, "findings", ()) or ()
        ],
    }


def _confidence_from_factors(lagna: Any, lord: Any, karaka: Any) -> dict[str, Any]:
    """Honest ConfidenceScore-style vote: do the 3 independent checks (house,
    lord, kāraka) concur in direction? Returns real counts, never a fabricated
    probability. A factor "votes positive" if its grade sits at or above
    "moderately good" (index 3). Agreement = size of the majority bloc."""
    votes: dict[str, str | None] = {}
    positives = 0
    graded = 0
    for name, fv in (("house", lagna), ("lord", lord), ("karaka", karaka)):
        idx = _verdict_index(getattr(fv, "label", ""))
        if idx is None:
            votes[name] = None
            continue
        graded += 1
        direction = "positive" if idx >= 3 else "guarded"
        votes[name] = direction
        if direction == "positive":
            positives += 1
    guarded = graded - positives
    majority = max(positives, guarded)
    return {
        "votes": votes,                     # {house/lord/karaka -> positive|guarded|None}
        "graded": graded,                   # how many of the 3 checks were computable
        "positive": positives,
        "guarded": guarded,
        "agreement": majority,              # N of `graded` checks that concur
        "band": (
            "strong" if graded and majority == graded and graded == 3
            else "mixed" if graded and majority < graded
            else "partial"
        ),
    }


def _d1d9_agreement(fv: Any) -> str:
    """Do Rāśi (promise) and Navāṁśa (fruition) point the same way?

    concur  — both sub-scores share sign (or one is ~0)
    diverge — opposite signs (a chart-level contradiction the reader should see)
    """
    r = float(getattr(fv, "rasi_score", 0.0))
    n = float(getattr(fv, "navamsa_score", 0.0))
    if abs(r) < 0.15 or abs(n) < 0.15:
        return "neutral"
    return "concur" if (r > 0) == (n > 0) else "diverge"


def _build_raman_chart(chart_input: ChartInput) -> Any | None:
    """Cast a RamanChart from birth data in the repo-default Lahiri frame so the
    doctrine grades explain the SAME chart the reading displays (houses/signs
    match the rendered kundali). Returns None on any failure. Built once and
    shared by the house-doctrine + planet-strength enrichments."""
    try:
        from app.medini.doctrine import raman_chart
        from app.medini.ml.raman_saab.chart_bundle import build_bundle

        year, month, day, hour, minute, tz_offset = _parse_chart_input(chart_input)
        bundle = build_bundle(
            year, month, day, hour, minute, tz_offset,
            chart_input.lat, chart_input.lon,
        )
        if bundle is None:
            return None
        return raman_chart._build(bundle, "lahiri")
    except Exception:  # noqa: BLE001
        return None


def _house_doctrine(judged: Mapping[int, Any] | None) -> dict[str, Any]:
    """Serialise the 12 REAL encoded-Raman house verdicts for the reading.

    This is the honest backbone for the executive summary, confidence
    checklist, "why" breakdowns, and house-health meter — it consumes the
    exact engine (`judge_house_doctrine`, validated across the doctrine suite)
    output, not a reinvented rollup. ``judged`` is the pre-computed
    ``{house -> HouseJudgment}`` map (from a single ``judge_chart_doctrine``
    pass so the doctrine engine runs once per reading). Fail-soft → {}."""
    if not judged:
        return {}
    try:
        from app.medini.doctrine.domains.house_judgment import VERDICT_SCALE

        houses: dict[str, Any] = {}
        for h, j in judged.items():
            timing = getattr(j, "timing", None)
            conclusion = getattr(j, "conclusion", None)
            influencers = []
            for inf in getattr(conclusion, "influencers", ()) or ():
                influencers.append({
                    "planet": getattr(inf, "planet", ""),
                    "factors": list(getattr(inf, "factors", ()) or ()),
                    "tier": getattr(inf, "tier", ""),
                    "is_benefic": bool(getattr(inf, "is_benefic", False)),
                    "nature": getattr(inf, "nature", ""),
                })
            houses[str(h)] = {
                "house": h,
                "life_area": _HOUSE_LIFE_AREA.get(h, ""),
                "verdict_label": getattr(conclusion, "label", getattr(j, "blend_label", "")),
                "verdict_index": _verdict_index(
                    getattr(conclusion, "label", "") or getattr(j, "blend_label", "")
                ),
                "blend_label": getattr(j, "blend_label", ""),
                "synthesis": getattr(conclusion, "synthesis", ""),
                "lagna": _factor_to_dict(j.lagna_verdict),
                "lord": _factor_to_dict(j.lord_verdict),
                "karaka": _factor_to_dict(j.karaka_verdict),
                "confidence": _confidence_from_factors(
                    j.lagna_verdict, j.lord_verdict, j.karaka_verdict,
                ),
                "d1d9": {
                    "house": _d1d9_agreement(j.lagna_verdict),
                    "lord": _d1d9_agreement(j.lord_verdict),
                    "karaka": _d1d9_agreement(j.karaka_verdict),
                },
                "timing": {
                    "current_md": getattr(timing, "current_md", None),
                    "current_ad": getattr(timing, "current_ad", None),
                    "current_tier": getattr(timing, "current_tier", None),
                    "current_is_activator": bool(
                        getattr(timing, "current_is_activator", False)
                    ),
                    "influencers": list(getattr(timing, "influencers", ()) or ()),
                } if timing is not None else {},
                "influencers": influencers,
            }
        return {
            "scale": list(VERDICT_SCALE),
            "ayanamsa": "lahiri",
            "houses": houses,
            "method": (
                "B. V. Raman, How to Judge a Horoscope — each house graded on its "
                "lord, occupants, aspects and kāraka (Rāśi and Navāṁśa)."
            ),
            "fidelity_note": (
                "Grades are the engine's faithful encoding of Raman's method "
                "(measured ~53–58% within one grade of Raman's own printed "
                "verdicts) — a doctrine grade, not a probability."
            ),
        }
    except Exception:  # noqa: BLE001 — never block a reading
        return {}


_KENDRAS_SET = {1, 4, 7, 10}
_DUSTHANAS_SET = {6, 8, 12}
_DUSTHANA_NAME = {6: "6th (Harsha)", 8: "8th (Sarala)", 12: "12th (Vimala)"}


def _classical_factors(chart: Any) -> dict[str, Any]:
    """Surface the advanced classical layers the engine can compute but the
    reading did not yet show (#12): functional benefic/malefic + yogakāraka,
    Maraka & Badhaka, retrogression, Graha-Yuddha (planetary war), Vipareeta
    Rāja-yoga, and Neecha-Bhaṅga. All from real chart data, fail-soft → {}."""
    if chart is None:
        return {}
    try:
        from app.core.dignity import (
            DEBILITATION, EXALTATION, SIGN_RULERS, dignity_state,
        )
        from app.core.functional_roles import (
            badhakesh_house, badhakesh_planet, functional_roles,
        )

        bundle = chart.bundle
        lagna = int(bundle.kundali.lagna_sign)
        signs = bundle.chart.planet_signs
        houses = bundle.kundali.planet_house
        lons = bundle.chart.planet_lons
        retro = getattr(bundle.chart, "planet_retrograde", {}) or {}
        moon_sign = int(signs.get("Moon", lagna))
        roles = functional_roles(lagna)

        # --- functional nature summary (per visible planet).
        functional: list[dict[str, Any]] = []
        for p, r in roles.items():
            tags = []
            if r.is_yogakaraka:
                tags.append("yogakāraka")
            if r.is_functional_benefic:
                tags.append("benefic")
            if r.is_functional_malefic:
                tags.append("malefic")
            if r.is_maraka:
                tags.append("maraka")
            if r.is_badhakesh:
                tags.append("badhaka lord")
            nature = ("benefic" if r.is_functional_benefic
                      else "malefic" if r.is_functional_malefic else "neutral")
            functional.append({
                "planet": p, "houses_ruled": list(r.houses_ruled),
                "nature": nature, "tags": tags,
                "is_yogakaraka": r.is_yogakaraka,
            })

        # --- Maraka & Badhaka.
        marakas = [p for p, r in roles.items() if r.is_maraka]
        bh = badhakesh_house(lagna)
        try:
            badhaka_planet = badhakesh_planet(lagna)
        except Exception:  # noqa: BLE001
            badhaka_planet = None

        # --- Retrogression (visible non-luminaries).
        retrograde = [p for p in _GRAHAS_9
                      if retro.get(p) and p not in ("Sun", "Moon", "Rahu", "Ketu")]

        # --- Graha-Yuddha: two tārā-grahas in the same sign within 1°.
        war_planets = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
        graha_yuddha: list[dict[str, Any]] = []
        for i, a in enumerate(war_planets):
            for b in war_planets[i + 1:]:
                if a in signs and b in signs and signs[a] == signs[b]:
                    la, lb = lons.get(a), lons.get(b)
                    if la is None or lb is None:
                        continue
                    orb = abs((la % 30.0) - (lb % 30.0))
                    if orb <= 1.0:
                        # Winner = the one with the higher longitude (further north
                        # proxy via degree-in-sign is unreliable; use lower degree =
                        # "ahead"). Report both; mark the closer-to-earlier as winner.
                        winner = a if (la % 30.0) < (lb % 30.0) else b
                        graha_yuddha.append({
                            "a": a, "b": b, "sign": int(signs[a]),
                            "orb": round(orb, 2), "winner": winner,
                        })

        # --- Vipareeta Rāja-yoga: a dusthāna lord placed in a dusthāna.
        vipareeta: list[dict[str, Any]] = []
        for p, r in roles.items():
            ruled_dusthanas = [h for h in r.houses_ruled if h in _DUSTHANAS_SET]
            ph = houses.get(p)
            if ruled_dusthanas and ph in _DUSTHANAS_SET:
                vipareeta.append({
                    "planet": p, "rules": ruled_dusthanas, "placed": int(ph),
                    "name": _DUSTHANA_NAME.get(int(ph), f"{ph}th"),
                })

        # --- Neecha-Bhaṅga: a debilitated planet whose fall is cancelled.
        neecha_bhanga: list[dict[str, Any]] = []
        for p in _GRAHAS_9:
            if p not in signs or p not in DEBILITATION:
                continue
            if DEBILITATION[p] != int(signs[p]):
                continue
            deb_sign = int(signs[p])
            dispositor = SIGN_RULERS[deb_sign]
            exalt_lord = next((g for g, s in EXALTATION.items() if s == deb_sign), None)
            reasons: list[str] = []
            for label, other in (("its dispositor", dispositor),
                                  ("the sign's exaltation-lord", exalt_lord)):
                if not other or other not in houses:
                    continue
                oh_l = houses.get(other)
                oh_m = ((int(signs.get(other, moon_sign)) - moon_sign) % 12) + 1
                if oh_l in _KENDRAS_SET or oh_m in _KENDRAS_SET:
                    reasons.append(f"{label} {other} sits in a kendra")
            if reasons:
                neecha_bhanga.append({"planet": p, "reasons": reasons})

        return {
            "functional": functional,
            "marakas": marakas,
            "badhaka": {"house": bh, "planet": badhaka_planet},
            "retrograde": retrograde,
            "graha_yuddha": graha_yuddha,
            "vipareeta": vipareeta,
            "neecha_bhanga": neecha_bhanga,
            "note": (
                "Functional nature is per your Lagna (the same planet is benefic "
                "for one ascendant, malefic for another). Vipareeta Rāja-yoga and "
                "Neecha-Bhaṅga can turn apparent weakness into strength."
            ),
        }
    except Exception:  # noqa: BLE001
        return {}


_RAMAN_BOOKS: dict[str, str] = {
    "htjah_vol1": "How to Judge a Horoscope, Vol. I",
    "htjah_vol2": "How to Judge a Horoscope, Vol. II",
    "hpa": "Hindu Predictive Astrology",
    "three_hundred": "Three Hundred Important Combinations",
    "jaimini_studies": "Studies in Jaimini Astrology",
    "manual_hindu_astrology": "A Manual of Hindu Astrology",
    "graha_bhava_balas": "Graha and Bhava Balas",
    "muhurtha": "Muhurtha (Electional Astrology)",
    "prasna_marga_1": "Prasna Marga",
    "prasna_marga_2": "Prasna Marga",
}
# Hard safety filter: the doctrine's death/longevity claims were REFUTED at
# population scale (Track B), and blunt fatalistic/harsh text must never be
# shown as a personal statement. Only favourable, benign combinations surface.
_RAMAN_UNSAFE = _re.compile(
    r"death|die|dead|mortal|maraka|balarish|arisht|mrityu|life|fatal|kill|widow|"
    r"abort|miscarr|brahminicide|suicide|assassin|blind|leper|lepro|insan|lunat|"
    r"imprison|disease|poison|drown|accident|idiot|ignor|poor|cruel|wicked|sinful|"
    r"immoral|adulter|prostitut|servil|vile|stupid|foolish|miser|debauch|quarrel|"
    r"sickly|broken|dumb|deaf|bastard|thief|beggar",
    _re.IGNORECASE,
)


def _clean_ocr(text: str) -> str:
    """Tidy OCR artefacts (soft hyphens, mid-word line breaks) for display."""
    t = text.replace("­", "").replace("¬\n", "").replace("¬", "")
    t = t.replace("-\n", "").replace("\n", " ")
    return _re.sub(r"\s+", " ", t).strip()


def _raman_doctrine(cd: Any) -> dict[str, Any]:
    """Surface the B. V. Raman knowledge base applied to THIS chart: the count of
    doctrine rules from his corpus that fire, the source books, and the
    **favourable** cited combinations his texts state for the chart's
    configurations (verbatim + citation). Consumes the pre-computed
    ``ChartDoctrine`` (single doctrine pass). Cautionary factors are
    deliberately left to the measured tensions/risks layers — blunt fatalistic/
    longevity text (refuted by Track B) is never surfaced. Fail-soft → {}."""
    if cd is None:
        return {}
    try:
        from app.medini.doctrine.domains.house_judgment import load_compendium
        books = load_compendium()
        id2rule = {r["id"]: r for rules in books.values() for r in rules}

        fired: set[str] = set()
        house_of: dict[str, int] = {}
        for h, j in cd.houses.items():
            for rid in j.fired_rule_ids:
                fired.add(rid)
                house_of.setdefault(rid, h)
        for g in cd.chart_global:
            fired.add(g.rule_id)

        safe_types = {"graha_effect", "yoga", "bhava_judgment"}
        favorable: list[dict[str, Any]] = []
        seen: set[str] = set()
        book_counts: dict[str, int] = {}
        for rid in fired:
            r = id2rule.get(rid)
            if not r:
                continue
            book_counts[r["book"]] = book_counts.get(r["book"], 0) + 1
            c = r.get("consequent") or {}
            if (r["rule_type"] not in safe_types
                    or c.get("polarity") != "favorable"):
                continue
            text = _clean_ocr(str(c.get("text", "")))
            if not text or _RAMAN_UNSAFE.search(text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            favorable.append({
                "text": text,
                "book": r["book"],
                "book_label": _RAMAN_BOOKS.get(r["book"], r["book"]),
                "house": house_of.get(rid),
            })
        favorable.sort(key=lambda n: (n["house"] is None, n["house"] or 0))
        favorable = favorable[:14]

        used_books = [
            {"id": b, "label": _RAMAN_BOOKS.get(b, b), "fired": book_counts[b]}
            for b in sorted(book_counts, key=lambda b: book_counts[b], reverse=True)
            if b in _RAMAN_BOOKS
        ]
        if not fired:
            return {}
        return {
            "total_applicable": len(fired),
            "books": used_books,
            "favorable": favorable,
            "note": (
                "The engine is B. V. Raman's own doctrine encoded rule-by-rule. "
                "Above are favourable combinations his texts state for your chart, "
                "each cited to its source. Cautionary factors are covered by the "
                "measured Chart-tensions and Risks sections rather than by blunt "
                "classical prognostications (which the population validation did "
                "not bear out)."
            ),
        }
    except Exception:  # noqa: BLE001
        return {}


def _executive_summary(reading: Mapping[str, Any]) -> list[str]:
    """Deterministic lay-language summary built ONLY from real engine output:
    strongest/weakest houses (house_doctrine), the daśā running now
    (dasha_now) and which houses it lights up (dasha_activation), and the
    standout classical yogas. No invented numbers. Fail-soft → []."""
    try:
        extras = (reading.get("chart") or {}).get("extras") or {}
        hd = (extras.get("house_doctrine") or {}).get("houses") or {}
        lines: list[str] = []

        # 1) Strongest / weakest houses by the real conclusion grade.
        graded = [
            (int(v["house"]), v.get("verdict_index"), v.get("verdict_label", ""),
             v.get("life_area", ""))
            for v in hd.values()
            if isinstance(v, dict) and v.get("verdict_index") is not None
        ]
        if graded:
            graded.sort(key=lambda t: (t[1] if t[1] is not None else -1), reverse=True)
            strong = [g for g in graded if (g[1] or 0) >= 5][:3]      # ≥ fairly strong
            weak = [g for g in reversed(graded) if (g[1] or 0) <= 1][:3]  # ≤ weak
            if strong:
                areas = "; ".join(f"the {_ordinal(h)} house ({area}, {lbl})"
                                  for h, _, lbl, area in strong)
                lines.append(f"Strongest in your chart: {areas}.")
            if weak:
                areas = "; ".join(f"the {_ordinal(h)} house ({area}, {lbl})"
                                  for h, _, lbl, area in weak)
                lines.append(f"Needing care: {areas}.")

        # 2) The daśā running NOW and which houses its lord activates.
        dn = extras.get("dasha_now") or {}
        md = dn.get("md") or {}
        ad = dn.get("ad") or {}
        if md.get("md_lord"):
            span = ""
            if md.get("start_date") and md.get("end_date"):
                span = f" ({md['start_date'][:4]}–{md['end_date'][:4]})"
            theme = ""
            act = extras.get("dasha_activation") or {}
            planets = act.get("planets") or {}
            lit = sorted({
                int(hh)
                for hh in (planets.get(md["md_lord"], {}).get("influences") or {})
            })
            if lit:
                area_bits = ", ".join(_HOUSE_LIFE_AREA.get(h, "").split(",")[0]
                                      for h in lit[:4] if _HOUSE_LIFE_AREA.get(h))
                if area_bits:
                    theme = f" — activating {area_bits}"
            ad_bit = f", {ad['ad_lord']} antardaśā" if ad.get("ad_lord") else ""
            lines.append(
                f"You are currently in {md['md_lord']} mahādaśā{span}{ad_bit}{theme}."
            )

        # 3) Standout classical yogas.
        yogas = reading.get("classical_yogas") or []
        if yogas:
            top = sorted(
                (y for y in yogas if isinstance(y, dict)),
                key=lambda y: float(y.get("intensity", 0.0)), reverse=True,
            )[:3]
            names = ", ".join(y.get("name", "") for y in top if y.get("name"))
            if names:
                lines.append(f"Notable combinations present: {names}.")

        return lines
    except Exception:  # noqa: BLE001
        return []


def _ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', … for lay-language house references."""
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


_DIGNITY_SCORE: dict[str, float] = {
    "exalted": 1.0, "moolatrikona": 0.95, "own": 0.85, "friendly": 0.68,
    "neutral": 0.5, "inimical": 0.32, "debilitated": 0.1, "enemy": 0.32,
}
_BALADI_SCORE: dict[str, float] = {
    "bala": 0.5, "kumara": 0.75, "yuva": 1.0, "vriddha": 0.35, "mrita": 0.1,
}
_JAGRAD_SCORE: dict[str, float] = {
    "jagrad": 1.0, "jagrat": 1.0, "swapna": 0.6, "sushupta": 0.3,
}


def _stars(frac: float) -> int:
    """0..1 → a 0–5 star rating."""
    return max(0, min(5, round(float(frac) * 5)))


def _planet_strength(chart: Any, avasthas: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Real per-planet strength from the cast bundle, with an honest composite
    (#13). Five real components — Dignity, Ṣaḍbala, Digbala, Vimsopaka, Avasthā
    — each rated 0–5 and averaged into a 0–100 composite. Every input is a
    measure the engine already computes; nothing is fabricated. Fail-soft."""
    if chart is None:
        return {}
    try:
        from app.core.dignity import dignity_state
        from app.core.shadbala import dig_bala

        bundle = chart.bundle
        signs = bundle.chart.planet_signs
        houses = bundle.kundali.planet_house
        av = avasthas or {}
        rows: list[dict[str, Any]] = []
        for g in _GRAHAS_9:
            if g not in signs:
                continue
            vim = bundle.strength.get(g)              # 0..1 (composite/20)
            shad = bundle.shadbala_ratio.get(g)       # total/threshold; nodes: none
            house = houses.get(g)
            try:
                dig = dignity_state(g, int(signs[g]))
            except Exception:  # noqa: BLE001
                dig = None
            # --- component fractions (0..1), each from a real measure.
            comp: dict[str, float | None] = {}
            comp["dignity"] = _DIGNITY_SCORE.get(str(dig or "").lower()) if dig else None
            comp["shadbala"] = (min(1.0, float(shad) / 1.2) if shad is not None else None)
            comp["vimsopaka"] = float(vim) if vim is not None else None
            try:
                comp["digbala"] = (min(1.0, dig_bala(g, int(house)) / 60.0)
                                   if house else None)
            except Exception:  # noqa: BLE001
                comp["digbala"] = None
            entry = av.get(g) or {}
            bal = _BALADI_SCORE.get(str(entry.get("baladi", "")).lower())
            jag = _JAGRAD_SCORE.get(str(entry.get("jagradadi", "")).lower())
            if bal is not None and jag is not None:
                comp["avastha"] = (bal + jag) / 2.0
            elif bal is not None:
                comp["avastha"] = bal
            else:
                comp["avastha"] = None
            present = [v for v in comp.values() if v is not None]
            composite = round(sum(present) / len(present) * 100) if present else None
            rows.append({
                "planet": g,
                "house": house,
                "sign": int(signs[g]),
                "navamsa_sign": bundle.navamsa_sign.get(g),
                "vimsopaka": round(vim * 20.0, 1) if vim is not None else None,
                "vimsopaka_frac": round(float(vim), 3) if vim is not None else None,
                "shadbala_ratio": round(float(shad), 2) if shad is not None else None,
                "dignity": dig,
                "combust": bool(bundle.combust.get(g, False)),
                "composite": composite,
                "stars": {k: (_stars(v) if v is not None else None)
                          for k, v in comp.items()},
            })
        if not rows:
            return {}
        return {
            "planets": rows,
            "components": ["dignity", "shadbala", "digbala", "vimsopaka", "avastha"],
            "note": (
                "Composite (0–100) averages five real measures — Dignity, Ṣaḍbala "
                "(vs the classical requirement), Digbala (directional), Vimsopaka "
                "(16-varga) and Avasthā (baladi + jāgradādi). Nodes take their "
                "dispositor's Vimsopaka."
            ),
        }
    except Exception:  # noqa: BLE001
        return {}


def _chart_tensions(reading: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Honest contradiction detector built from the REAL per-house doctrine:
    surface houses where the Rāśi (promise) and Navāṁśa (fruition) disagree, or
    where the lord and kāraka verdicts point in opposite directions. These are
    genuine chart tensions the engine already computes — not invented. → []."""
    try:
        hd = ((reading.get("chart") or {}).get("extras") or {}) \
            .get("house_doctrine") or {}
        houses = hd.get("houses") or {}
        out: list[dict[str, Any]] = []
        for h in range(1, 13):
            hv = houses.get(str(h))
            if not isinstance(hv, dict):
                continue
            area = hv.get("life_area", "")
            # D1/D9 divergence — surfaced only when BOTH frames are substantial
            # (|score| ≥ 0.5) and opposite in sign, so marginal splits stay quiet.
            best: tuple[float, str] | None = None
            for factor, key in (("house", "lagna"), ("lord", "lord"), ("karaka", "karaka")):
                fv = hv.get(key) or {}
                r = float(fv.get("rasi_score", 0.0))
                n = float(fv.get("navamsa_score", 0.0))
                if abs(r) >= 0.5 and abs(n) >= 0.5 and (r > 0) != (n > 0):
                    mag = abs(r) + abs(n)
                    if best is None or mag > best[0]:
                        rich = ("a strong Rāśi promise but a weak Navāṁśa fruition"
                                if r > 0 else
                                "a weak Rāśi promise but a strong Navāṁśa recovery")
                        best = (mag, f"its {factor} carries {rich}")
            if best is not None:
                out.append({
                    "house": h, "life_area": area, "kind": "d1d9", "weight": best[0],
                    "text": (
                        f"The {_ordinal(h)} house ({area}): {best[1]} — results may "
                        f"come, but with friction or delay."
                    ),
                })
            # Lord vs kāraka opposition — the two independent testimonies clash.
            li = (hv.get("lord") or {}).get("grade_index")
            ki = (hv.get("karaka") or {}).get("grade_index")
            if li is not None and ki is not None and abs(li - ki) >= 4:
                strong, weak = ("lord", "kāraka") if li > ki else ("kāraka", "lord")
                out.append({
                    "house": h, "life_area": area, "kind": "factor_clash",
                    "weight": float(abs(li - ki)),
                    "text": (
                        f"The {_ordinal(h)} house ({area}): the {strong} is strong "
                        f"while the {weak} is weak — a divided testimony to weigh."
                    ),
                })
        # Rank by severity and keep the most salient handful.
        out.sort(key=lambda t: t.get("weight", 0.0), reverse=True)
        return out[:6]
    except Exception:  # noqa: BLE001
        return []


# Life domains → the houses/kāraka/varga that testify to them, with a
# modern-language gloss (#11). Primary house first (double-weighted).
# References: Raman, HTJAH — house significations; classical kārakas.
_DOMAINS_SPEC: tuple[dict[str, Any], ...] = (
    {"key": "career", "label": "Career", "houses": [10, 6, 11],
     "karakas": ["Sun", "Saturn", "Mercury"], "varga": "D10_Dasamsa",
     "modern": "profession, leadership, public standing, promotion"},
    {"key": "wealth", "label": "Wealth & money", "houses": [2, 11],
     "karakas": ["Jupiter", "Venus"], "varga": "D2_Hora",
     "modern": "income, savings, assets, financial stability"},
    {"key": "marriage", "label": "Marriage & partnership", "houses": [7],
     "karakas": ["Venus", "Jupiter"], "varga": "D9_Navamsa",
     "modern": "spouse, committed relationships, business partners"},
    {"key": "health", "label": "Health & vitality", "houses": [1, 6],
     "karakas": ["Sun", "Saturn"], "varga": "D1",
     "modern": "energy, resilience, chronic-risk areas"},
    {"key": "education", "label": "Education & learning", "houses": [5, 4],
     "karakas": ["Mercury", "Jupiter"], "varga": "D24_Chaturvimsamsa",
     "modern": "study, degrees, skills, intellect"},
    {"key": "children", "label": "Children & creativity", "houses": [5],
     "karakas": ["Jupiter"], "varga": "D7_Saptamsa",
     "modern": "children, creative output, mentoring"},
    {"key": "foreign", "label": "Foreign & travel", "houses": [12, 9, 3],
     "karakas": ["Rahu", "Jupiter"], "varga": "D1",
     "modern": "relocation, travel, overseas work, immigration"},
    {"key": "spirituality", "label": "Fortune & spirituality", "houses": [9, 12],
     "karakas": ["Jupiter", "Ketu"], "varga": "D20_Vimsamsa",
     "modern": "luck, dharma, inner growth, guidance"},
)


def _potential_label(idx: float) -> str:
    """Map a mean 0–8 doctrine grade to a domain potential band."""
    if idx >= 6.0:
        return "Excellent"
    if idx >= 4.5:
        return "Strong"
    if idx >= 3.0:
        return "Good"
    if idx >= 1.5:
        return "Moderate"
    return "Challenging"


def _domain_decisions(reading: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The question-centric inference layer: for each life domain, aggregate the
    REAL evidence the engine already produced into a decision view —
    **potential** (natal doctrine), **timing** (the daśā running now), the
    **positive/negative contributors**, a **confidence** from how the
    independent signals agree, and a conflict-resolved one-line verdict.

    Every number is a transparent roll-up of engine output (house grades,
    findings, planet strength, yogas, daśā activation) — a *doctrine potential*,
    never a probability that an event will occur. Fail-soft → []."""
    try:
        extras = (reading.get("chart") or {}).get("extras") or {}
        hd = (extras.get("house_doctrine") or {}).get("houses") or {}
        if not hd:
            return []
        # planet strength lookup (for kāraka-strength confidence signal).
        pstr = {r["planet"]: r for r in
                ((extras.get("planet_strength") or {}).get("planets") or [])}

        out: list[dict[str, Any]] = []
        for spec in _DOMAINS_SPEC:
            houses = spec["houses"]
            # --- potential: weighted mean of the domain houses' doctrine grades.
            idxs: list[tuple[int, float]] = []
            for w, h in [(2.0 if i == 0 else 1.0, hh) for i, hh in enumerate(houses)]:
                gi = (hd.get(str(h)) or {}).get("verdict_index")
                if gi is not None:
                    idxs.append((w, float(gi)))
            if not idxs:
                continue
            mean_idx = sum(w * v for w, v in idxs) / sum(w for w, _ in idxs)
            score100 = round(mean_idx / 8.0 * 100)

            primary = hd.get(str(houses[0])) or {}

            # --- contributors: real findings on the primary house's factors.
            pos: list[str] = []
            neg: list[str] = []
            for factor in ("lagna", "lord", "karaka"):
                for f in (primary.get(factor) or {}).get("findings", []) or []:
                    d = float(f.get("delta", 0.0))
                    txt = f.get("text", "")
                    if not txt or d == 0:
                        continue
                    entry = f"{txt} ({'+' if d > 0 else ''}{round(d, 1)})"
                    (pos if d > 0 else neg).append(entry)
            pos = _dedup_keep(pos)[:6]
            neg = _dedup_keep(neg)[:5]

            # --- timing: the REAL MD×AD fructification tier the engine computed
            # for the running daśā, taken as the best tier across the domain's
            # houses (par excellence > predominant > limited > dormant).
            _TIER_RANK = {"par excellence": 3, "predominant": 2, "limited": 1,
                          "dormant": 0}
            best_tier, best_rank = None, -1
            for h in houses:
                t = (((hd.get(str(h)) or {}).get("timing")) or {}).get("current_tier")
                r = _TIER_RANK.get(str(t or "").lower(), -1)
                if r > best_rank:
                    best_rank, best_tier = r, t
            tier = best_tier
            is_active = best_rank >= 2                       # predominant or better
            is_mild = best_rank == 1
            activated_houses = sorted({
                str(h) for h in houses
                if _TIER_RANK.get(str(
                    (((hd.get(str(h)) or {}).get("timing")) or {}).get("current_tier")
                    or "").lower(), -1) >= 1
            })

            # --- confidence: how the independent signals agree.
            signals: list[bool] = []
            signals.append(mean_idx >= 4.0)                      # natal grade
            d1d9 = (primary.get("d1d9") or {}).get("house")
            if d1d9 in ("concur", "diverge"):
                signals.append(d1d9 == "concur")                 # D1/D9 support
            # kāraka strength
            for k in spec["karakas"][:1]:
                kr = pstr.get(k) or {}
                vim = kr.get("vimsopaka")
                if vim is not None:
                    signals.append(vim >= 10.0)                  # kāraka strong
            total = len(signals)
            natal_ok = mean_idx >= 4.0
            # Confidence = how CONSISTENTLY the independent signals point the same
            # way as the headline potential (agreement), not how good it is.
            direction = natal_ok
            agree = sum(1 for s in signals if s == direction)
            frac = agree / total if total else 0.0
            # Genuine conflict: strong natal promise but the daśā is dormant, or a
            # top-tier activation landing on weak natal support.
            timing_conflict = ((natal_ok and best_rank <= 0)
                               or (not natal_ok and best_rank >= 3))
            if timing_conflict:
                band = "Conflicting indications"
            elif total == 0:
                band = "Medium"
            elif frac >= 0.999:
                band = "Very high"
            elif frac >= 0.5:
                band = "High"
            else:
                band = "Medium"

            # --- conflict-resolved verdict line (potential vs timing).
            pot = _potential_label(mean_idx)
            timing_label = ("Active now" if is_active
                            else "Warming up" if is_mild else "Quiet")
            if natal_ok and is_active:
                line = f"{pot} potential and currently active — a favourable window."
            elif natal_ok and is_mild:
                line = (f"{pot} potential; the current daśā touches it mildly — "
                        f"steady rather than dramatic progress.")
            elif natal_ok and not is_active:
                line = (f"{pot} potential, but the current daśā is quiet here — "
                        f"results favour later periods than sudden breakthroughs.")
            elif not natal_ok and is_active:
                line = ("The period activates this area, yet natal support is "
                        "limited — effort meets friction; progress with obstacles.")
            else:
                line = f"{pot} natal support and quiet timing — a background area for now."

            # confidence as an honest percentage: the share of independent
            # signals that agree with the headline direction (internal
            # agreement, NEVER an event probability). A genuine conflict caps it.
            conf_pct = 0 if timing_conflict else (round(frac * 100) if total else 50)
            conf_reason = (
                f"{agree} of {total} independent signals agree"
                if total and not timing_conflict
                else "strong natal promise but the daśā is quiet here"
                if timing_conflict and natal_ok
                else "the period activates an area of limited natal support"
                if timing_conflict
                else "too few independent signals to judge"
            )
            out.append({
                "key": spec["key"], "label": spec["label"],
                "modern": spec["modern"], "houses": houses,
                "score": score100,
                "potential": pot,
                "potential_index": round(mean_idx, 2),
                "timing": timing_label,
                "current_tier": tier,
                "activated_houses": activated_houses,
                "confidence": band,
                "confidence_pct": conf_pct,
                "confidence_reason": conf_reason,
                "contributors_pos": pos,
                "contributors_neg": neg,
                "verdict": line,
            })
        # Present strongest-first for the dashboard.
        out.sort(key=lambda d: d["score"], reverse=True)
        return out
    except Exception:  # noqa: BLE001
        return []


def _dedup_keep(items: list[str]) -> list[str]:
    """Order-preserving de-duplication for contributor lists."""
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


# House-specific cautions when a classic risk house is weakly graded (#9).
_RISK_HOUSE_PHRASE: dict[int, str] = {
    2: "cash-flow swings and family or speech friction — keep a buffer",
    4: "domestic or property unrest and inner restlessness — protect your base",
    6: "debts, disputes or recurring health niggles — address them early",
    7: "relationship strain — patience and clear agreements with partners",
    8: "sudden disruptions, unexpected expenses or health scares — avoid speculation",
    12: "unplanned expenditure, losses and energy drain — watch the outflows",
}
# Opportunity phrasing when a domain is strongly graded (#10).
_OPP_DOMAIN_PHRASE: dict[str, str] = {
    "career": "leadership roles, promotion and public recognition",
    "wealth": "building assets and steady income growth",
    "marriage": "partnership, commitment and mutual support",
    "health": "vitality and stamina to draw on",
    "education": "study, credentials and skill-building",
    "children": "children, mentoring and creative output",
    "foreign": "travel, relocation or overseas openings",
    "spirituality": "guidance, fortune and inner growth",
}


def _risks_opportunities_narrative(
    reading: Mapping[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    """Derive (risks, opportunities, narrative) from the real decision layer —
    honest, lay-language, no invented events. Returns three lists; any may be
    empty. Fail-soft → ([], [], [])."""
    try:
        extras = (reading.get("chart") or {}).get("extras") or {}
        decisions = extras.get("domain_decisions") or []
        hd = (extras.get("house_doctrine") or {}).get("houses") or {}
        if not decisions:
            return [], [], []
        by_key = {d["key"]: d for d in decisions}

        # --- Opportunities (#10): strongly-graded domains, active ones first.
        opps: list[str] = []
        for d in decisions:
            if d["potential_index"] >= 4.0:  # ≥ fairly good
                phrase = _OPP_DOMAIN_PHRASE.get(d["key"], d["modern"].split(",")[0])
                when = (" — supported now" if d["timing"] == "Active now"
                        else " — building" if d["timing"] == "Warming up" else "")
                opps.append(f"{phrase.capitalize()}{when}.")
        opps = opps[:5]

        # --- Risks (#9): concrete house cautions first, then a few weak domains.
        house_risks: list[str] = []
        for h, phrase in _RISK_HOUSE_PHRASE.items():
            gi = (hd.get(str(h)) or {}).get("verdict_index")
            if gi is not None and gi <= 1:  # afflicted/weak
                house_risks.append(f"Watch the {_ordinal(h)} house: {phrase}.")
        domain_risks = [
            f"{d['label']} needs patience — {d['modern'].split(',')[0]} may "
            f"progress slowly; set realistic expectations."
            for d in decisions if d["potential_index"] <= 2.0
        ][:3]
        risks = _dedup_keep(house_risks + domain_risks)[:6]

        # --- Cohesive narrative (#17): potential + timing, no fabricated events.
        narrative: list[str] = []
        strongest = decisions[0] if decisions else None
        weakest = decisions[-1] if decisions else None
        dn = extras.get("dasha_now") or {}
        md = (dn.get("md") or {}).get("md_lord")
        ad = (dn.get("ad") or {}).get("ad_lord")
        active = [d for d in decisions if d["timing"] == "Active now"]
        if strongest:
            narrative.append(
                f"Your chart's clearest strength is {strongest['label'].lower()} "
                f"({strongest['potential'].lower()} potential), with "
                f"{decisions[1]['label'].lower()} also well supported."
                if len(decisions) > 1 else
                f"Your chart's clearest strength is {strongest['label'].lower()} "
                f"({strongest['potential'].lower()} potential).")
        if md:
            theme = (f", and it currently activates "
                     + ", ".join(a["label"].lower() for a in active[:2])
                     if active else "")
            narrative.append(
                f"You are running the {md} mahādaśā"
                f"{(' with ' + ad + ' antardaśā') if ad else ''}{theme}.")
        # Reconcile the headline potential vs the present timing (the anti-
        # contradiction sentence).
        if strongest:
            if strongest["timing"] == "Active now":
                narrative.append(
                    f"This is a constructive window for {strongest['label'].lower()} — "
                    f"the natal promise and the present period align.")
            else:
                narrative.append(
                    f"The pattern favours sustained progress over sudden breakthroughs: "
                    f"{strongest['label'].lower()}'s promise ripens more fully in a later "
                    f"period than the one running now.")
        if weakest and weakest["potential_index"] <= 2.0:
            narrative.append(
                f"Give extra patience to {weakest['label'].lower()}, the least "
                f"supported area, and avoid overcommitting there.")
        return risks, opps, narrative
    except Exception:  # noqa: BLE001
        return [], [], []


def _augment_present_and_doctrine(
    reading: dict[str, Any], chart_input: ChartInput,
) -> None:
    """Attach the present-tense + real-doctrine enrichments to a fully
    assembled reading dict, in place. Each block is independently fail-soft;
    all output lands under ``chart.extras.*``. Called at the very end of
    ``compute()`` so the full timeline (sequences.md_judgments) is available
    and nothing downstream can drop the new fields."""
    chart_block = reading.get("chart")
    if not isinstance(chart_block, dict):
        return
    extras = chart_block.setdefault("extras", {})
    if not isinstance(extras, dict):
        return

    # --- Phase 0a: the daśā running NOW (and the correctly-labelled birth balance).
    dasha_lords: dict[str, str] | None = None
    try:
        from app.integration import dasha_now as _dn

        block: dict[str, Any] = {}
        try:
            block["md"] = _dn.md_at_now(reading).model_dump(mode="json")
        except Exception:  # noqa: BLE001
            pass
        try:
            block["ad"] = _dn.ad_at_now(reading).model_dump(mode="json")
        except Exception:  # noqa: BLE001
            pass
        try:
            block["pd"] = _dn.pd_at_now(reading).model_dump(mode="json")
        except Exception:  # noqa: BLE001
            pass
        try:
            block["birth_balance"] = _dn.md_at_birth(reading).model_dump(mode="json")
        except Exception:  # noqa: BLE001
            pass
        if block:
            extras["dasha_now"] = block
            md_lord = (block.get("md") or {}).get("md_lord")
            ad_lord = (block.get("ad") or {}).get("ad_lord")
            if md_lord:
                dasha_lords = {"md": md_lord}
                if ad_lord:
                    dasha_lords["ad"] = ad_lord
    except Exception:  # noqa: BLE001
        pass

    # --- Phase 0b: live transits (gochara now).
    try:
        from app.integration import transit_engine as _te

        extras["transits_now"] = _te.transit_at_now(reading).model_dump(mode="json")
    except Exception:  # noqa: BLE001
        pass

    # --- Cast the RamanChart once; shared by house-doctrine + planet-strength.
    raman_chart_obj = _build_raman_chart(chart_input)

    # --- Run the encoded-Raman doctrine engine ONCE; both the per-house verdicts
    # and the fired-rule knowledge base derive from this single pass.
    chart_doctrine = None
    if raman_chart_obj is not None:
        try:
            from app.medini.doctrine.domains.house_judgment import (
                judge_chart_doctrine,
            )
            _dasha = dict(dasha_lords) if dasha_lords else None
            chart_doctrine = judge_chart_doctrine(raman_chart_obj, dasha=_dasha)
        except Exception:  # noqa: BLE001
            chart_doctrine = None

    # --- Phase 1a: the real encoded Raman per-house verdicts.
    hd = _house_doctrine(chart_doctrine.houses if chart_doctrine else None)
    if hd:
        extras["house_doctrine"] = hd

    # --- Phase 2 (#4,#13): real per-planet strength + composite (5 components).
    ps = _planet_strength(raman_chart_obj, extras.get("avasthas"))
    if ps:
        extras["planet_strength"] = ps

    # --- Phase 2 (#10): chart tensions derived from the D1/D9 + factor clashes.
    tensions = _chart_tensions(reading)
    if tensions:
        extras["tensions"] = tensions

    # --- Phase 3 (#12): advanced classical factors (functional nature, maraka/
    # badhaka, retrogression, graha-yuddha, vipareeta, neecha-bhanga).
    cf = _classical_factors(raman_chart_obj)
    if cf:
        extras["classical_factors"] = cf

    # --- B. V. Raman knowledge base: cited favourable combinations + provenance.
    rd = _raman_doctrine(chart_doctrine)
    if rd:
        extras["raman_doctrine"] = rd

    # --- Phase 3 (#1,2,3,6,8,11,14): the question-centric domain decision layer.
    decisions = _domain_decisions(reading)
    if decisions:
        extras["domain_decisions"] = decisions

    # --- Conflict-resolution / weighted-synthesis engine: one reconciled
    # verdict per domain from weighted positive-vs-negative evidence.
    try:
        from app.reading.judgement import build_judgements
        judgements = build_judgements(extras)
        if judgements:
            extras["judgements"] = judgements
    except Exception:  # noqa: BLE001
        pass

    # --- Phase 3 (#9,#10,#17): risks, opportunities, cohesive narrative.
    risks, opps, narrative = _risks_opportunities_narrative(reading)
    if risks:
        extras["risks"] = risks
    if opps:
        extras["opportunities"] = opps
    if narrative:
        extras["narrative"] = narrative

    # --- Phase 1b: the deterministic executive summary (reads the blocks above).
    summary = _executive_summary(reading)
    if summary:
        extras["executive_summary"] = summary

    # --- Classical judicial narrative in the manner of B. V. Raman — a
    # continuous, measured reading following his hierarchy (Ascendant → lord →
    # Moon → Sun → planets → house lords → yogas → synthesis → timing). Reasons
    # from the SAME real engine output the dashboard shows. Fail-soft.
    if raman_chart_obj is not None:
        try:
            from app.reading.classical_narrative import build_classical_narrative
            narrative_chapters = build_classical_narrative(
                reading, raman_chart_obj.bundle,
            )
            if narrative_chapters:
                extras["classical_narrative"] = narrative_chapters
        except Exception:  # noqa: BLE001
            pass

    # --- Native profile ("Who you are"): eight behavioural styles reasoned from
    # the real planet-strength table + an honest internal-clarity figure.
    try:
        from app.reading.native_profile import build_native_profile
        native = build_native_profile(reading, extras)
        if native:
            extras["native_profile"] = native
    except Exception:  # noqa: BLE001
        pass

    # --- Master Synthesis Layer (the spine): reduce ALL the blocks above into
    # ONE governing judgement — dominant planet / yoga / challenge, core
    # strengths & weaknesses, life theme, current phase, and the ≤10 decisive
    # factors the report leads with (anti-rule-dumping). Runs LAST so every
    # input exists; every field is real engine output, never a probability.
    try:
        from app.reading.master_synthesis import build_master
        master = build_master(reading, extras)
        if master:
            extras["master"] = master
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Input parsing helpers
# ---------------------------------------------------------------------------


def _parse_chart_input(
    chart_input: ChartInput,
) -> tuple[int, int, int, int, int, float]:
    """Decompose a ChartInput into ephemeris-engine arguments.

    Returns ``(year, month, day, hour, minute, tz_offset_hours)``.
    """
    dt = datetime.fromisoformat(f"{chart_input.dob} {chart_input.time}:00")
    tz_sign = 1
    tz_str = chart_input.tz
    if tz_str.startswith("-"):
        tz_sign = -1
        tz_str = tz_str[1:]
    elif tz_str.startswith("+"):
        tz_str = tz_str[1:]
    tz_hh, tz_mm = tz_str.split(":")
    tz_offset = tz_sign * (int(tz_hh) + int(tz_mm) / 60.0)
    return dt.year, dt.month, dt.day, dt.hour, dt.minute, tz_offset


def _safe_call(
    warnings: list[str],
    module_label: str,
    fn: Callable[..., Any],
    *args: Any,
    default: Any = None,
    **kwargs: Any,
) -> Any:
    """Invoke ``fn(*args, **kwargs)`` catching every exception.

    On failure: append a warning string to ``warnings`` and return ``default``.
    The graceful-degradation contract: the engine MUST never crash a user.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        msg = f"{module_label} failed: {type(exc).__name__}: {exc}"
        logger.warning(msg)
        warnings.append(msg)
        return default


def _flatten_findings(value: Any) -> list[Finding]:
    """Normalise a Tier-0/1/2 module return into a flat ``list[Finding]``.

    Modules variously return ``list[Finding]``, ``dict[str, Finding]``,
    ``dict[int, Finding]``, or a single ``Finding``. We unify them here.
    """
    if value is None:
        return []
    if isinstance(value, Finding):
        return [value]
    if isinstance(value, list):
        return [f for f in value if isinstance(f, Finding)]
    if isinstance(value, dict):
        out: list[Finding] = []
        for v in value.values():
            if isinstance(v, Finding):
                out.append(v)
        return out
    return []


def _add_findings(
    block_findings: list[Finding],
    by_module: dict[str, list[Finding]],
    module_name: str,
    value: Any,
) -> None:
    """Record a module's findings into both the flat list and the by-module map."""
    flat = _flatten_findings(value)
    if not flat:
        return
    block_findings.extend(flat)
    by_module[module_name] = flat


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_core_pipeline(chart_input: ChartInput) -> dict[str, Any]:
    """Run Stages 1-7 of the kundli pipeline.

    Private. Deterministic. No RAG. No recursion. Birth-time-robustness
    calls this directly to evaluate flip-rates over time perturbations
    without triggering Tier-3 enrichment on each call.
    """
    logger.info(
        "Running core pipeline for dob=%s time=%s tz=%s lat=%s lon=%s",
        chart_input.dob,
        chart_input.time,
        chart_input.tz,
        chart_input.lat,
        chart_input.lon,
    )

    warnings: list[str] = []

    # -----------------------------------------------------------------------
    # Stage 1: Natal chart compute
    # -----------------------------------------------------------------------
    chart: dict[str, Any] = {}
    try:
        year, month, day, hour, minute, tz_offset = _parse_chart_input(chart_input)
        from app.core.ephemeris_engine import calculate_all_charts

        chart = calculate_all_charts(
            year, month, day, hour, minute, tz_offset,
            latitude=chart_input.lat, longitude=chart_input.lon,
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"stage1.ephemeris_engine.calculate_all_charts failed: {type(exc).__name__}: {exc}"
        logger.warning(msg)
        warnings.append(msg)

    d1_chart = chart.get("d1") or {}
    d9_chart = chart.get("d9") or {}
    d10_chart = chart.get("d10") or {}
    divisional_charts = chart.get("divisional_charts") or {}
    ascendant = chart.get("ascendant") or {}
    asc_sign = int(ascendant.get("sign", 1)) if ascendant else 1
    lagna_longitude = float(ascendant.get("longitude", 0.0)) if ascendant else 0.0
    birth_jd = float(chart.get("birth_jd", chart.get("jd", 0.0)))
    ayanamsa = chart.get("ayanamsa")

    moon_entry = d1_chart.get("Moon") or {}
    moon_sign = int(moon_entry.get("sign", 1)) if moon_entry else 1
    moon_lon = float(moon_entry.get("longitude", 0.0)) if moon_entry else 0.0
    sun_entry = d1_chart.get("Sun") or {}
    sun_lon = float(sun_entry.get("longitude", 0.0)) if sun_entry else 0.0

    weekday = int(birth_jd + 1.5) % 7 if birth_jd else 0

    # Determine is_daytime + sunrise_jd via sunrise/sunset; fail soft.
    is_daytime = True
    sunrise_jd = birth_jd
    try:
        import swisseph as swe
        geopos = (chart_input.lon, chart_input.lat, 0.0)
        status, tret = swe.rise_trans(
            birth_jd - 1.0, swe.SUN, swe.CALC_RISE, geopos, 0.0, 0.0, swe.FLG_SWIEPH,
        )
        if status >= 0 and tret:
            sunrise_jd = float(tret[0])
        status, tret = swe.rise_trans(
            sunrise_jd, swe.SUN, swe.CALC_SET, geopos, 0.0, 0.0, swe.FLG_SWIEPH,
        )
        if status >= 0 and tret:
            sunset_jd = float(tret[0])
            is_daytime = sunrise_jd <= birth_jd < sunset_jd
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"stage1.sunrise_sunset failed: {type(exc).__name__}: {exc}"
        )

    # Build the public ChartBlock payload.
    chart_block_payload: dict[str, Any] = {
        "lagna_longitude": lagna_longitude if ascendant else None,
        "ayanamsa": ayanamsa,
        "planets": d1_chart,
        "cusps": ascendant if ascendant else {},
        "extras": {
            "birth_jd": birth_jd,
            "is_daytime": is_daytime,
            "sunrise_jd": sunrise_jd,
            "weekday": weekday,
            "current_mahadasha": chart.get("current_mahadasha"),
            "divisional_charts": divisional_charts,
            "divisional_lagnas": _divisional_lagnas(lagna_longitude),
            "dasha_activation": _dasha_activation(d1_chart, lagna_longitude),
            "panchanga": chart.get("panchanga"),
            "ashtakavarga": chart.get("ashtakavarga"),
            "avasthas": chart.get("avasthas"),
        },
    }

    # -----------------------------------------------------------------------
    # Stage 2: Tier-0 primitives
    # -----------------------------------------------------------------------
    prim_findings: list[Finding] = []
    prim_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            arudha_upapada,
            avasthas as avasthas_mod,
            gandanta,
            gulika as gulika_mod,
            ishta_phal,
            karakamsha,
            karakas,
            panchanga_reader,
            planet_retrograde,
            residential_strength,
            vimsopaka,
        )

        _add_findings(
            prim_findings, prim_by_module, "planet_retrograde",
            _safe_call(warnings, "planet_retrograde",
                       planet_retrograde.detect_retrograde, d1_chart),
        )
        _add_findings(
            prim_findings, prim_by_module, "gandanta",
            _safe_call(warnings, "gandanta",
                       gandanta.detect_gandanta, d1_chart),
        )
        if birth_jd:
            _add_findings(
                prim_findings, prim_by_module, "panchanga_reader",
                _safe_call(warnings, "panchanga_reader",
                           panchanga_reader.read_panchanga,
                           birth_jd, moon_lon, sun_lon, weekday),
            )
        karaka_findings = _safe_call(
            warnings, "karakas", karakas.compute_karakas, d1_chart,
        )
        _add_findings(prim_findings, prim_by_module, "karakas", karaka_findings)
        lagna_deg_in_sign = lagna_longitude % 30.0
        _add_findings(
            prim_findings, prim_by_module, "residential_strength",
            _safe_call(warnings, "residential_strength",
                       residential_strength.compute_residential_strength,
                       d1_chart, lagna_deg_in_sign),
        )
        if birth_jd:
            _add_findings(
                prim_findings, prim_by_module, "gulika",
                _safe_call(warnings, "gulika",
                           gulika_mod.compute_gulika_and_mandi,
                           birth_jd, chart_input.lat, chart_input.lon,
                           is_daytime, weekday),
            )
        _add_findings(
            prim_findings, prim_by_module, "avasthas",
            _safe_call(warnings, "avasthas",
                       avasthas_mod.compute_deeptadi_avasthas, d1_chart),
        )

        arudha_padas: dict[str, Finding] = _safe_call(
            warnings, "arudha_upapada",
            arudha_upapada.compute_arudha_padas, d1_chart, asc_sign,
            default={},
        ) or {}
        _add_findings(
            prim_findings, prim_by_module, "arudha_upapada", arudha_padas,
        )

        if d9_chart:
            _add_findings(
                prim_findings, prim_by_module, "karakamsha",
                _safe_call(warnings, "karakamsha",
                           karakamsha.compute_karakamsha, d1_chart, d9_chart),
            )
        if divisional_charts:
            # vimsopaka expects ``{divisor:int -> per-varga chart dict}``,
            # but `compute_divisional_charts` keys by name (e.g. "D9_Navamsa").
            # Translate via SHODASHAVARGA_NAMES.
            divisor_keyed: dict[int, dict[str, Any]] = {1: d1_chart}
            try:
                from app.core.shodashavarga import SHODASHAVARGA_NAMES
                for divisor, name in SHODASHAVARGA_NAMES.items():
                    if name in divisional_charts:
                        divisor_keyed[divisor] = divisional_charts[name]
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"vimsopaka_inputs failed: {type(exc).__name__}: {exc}"
                )
            _add_findings(
                prim_findings, prim_by_module, "vimsopaka",
                _safe_call(warnings, "vimsopaka",
                           vimsopaka.compute_vimsopaka,
                           d1_chart, divisor_keyed),
            )

        # Build shadbala components (cheshta + uchcha) for ishta_phal.
        shadbala_components: dict[str, dict[str, float]] = {}
        try:
            from app.core.shadbala import cheshta_bala, uchcha_bala
            for p, entry in d1_chart.items():
                if p == "Ketu":
                    continue
                lon = float(entry.get("longitude", 0.0))
                is_retro = bool(entry.get("is_retrograde", False))
                shadbala_components[p] = {
                    "cheshta": cheshta_bala(p, is_retro),
                    "uchcha": uchcha_bala(p, lon),
                }
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"shadbala_components_build failed: {type(exc).__name__}: {exc}"
            )

        if shadbala_components:
            _add_findings(
                prim_findings, prim_by_module, "ishta_phal",
                _safe_call(warnings, "ishta_phal",
                           ishta_phal.compute_ishta_phal,
                           d1_chart, shadbala_components),
            )
    else:
        arudha_padas = {}

    # -----------------------------------------------------------------------
    # Stage 3: Tier-1 foundations
    # -----------------------------------------------------------------------
    found_findings: list[Finding] = []
    found_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            argala,
            ashtakavarga_reader,
            bhava_bala,
            bhava_chalit,
            functional_nature,
            jaimini_drishti,
            karaka_triangulation,
            shadbala_phase1,
        )

        _add_findings(
            found_findings, found_by_module, "functional_nature",
            _safe_call(warnings, "functional_nature",
                       functional_nature.compute_functional_nature, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "bhava_chalit",
            _safe_call(warnings, "bhava_chalit",
                       bhava_chalit.compute_bhava_chalit,
                       d1_chart, lagna_longitude, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "bhava_bala",
            _safe_call(warnings, "bhava_bala",
                       bhava_bala.compute_bhava_bala, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "shadbala_phase1",
            _safe_call(warnings, "shadbala_phase1",
                       shadbala_phase1.compute_shadbala_phase1,
                       d1_chart, asc_sign, is_daytime),
        )
        _add_findings(
            found_findings, found_by_module, "ashtakavarga_reader",
            _safe_call(warnings, "ashtakavarga_reader",
                       ashtakavarga_reader.read_ashtakavarga, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "jaimini_drishti",
            _safe_call(warnings, "jaimini_drishti",
                       jaimini_drishti.compute_jaimini_drishti,
                       d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "argala",
            _safe_call(warnings, "argala",
                       argala.compute_argala, d1_chart, asc_sign),
        )
        _add_findings(
            found_findings, found_by_module, "karaka_triangulation",
            _safe_call(warnings, "karaka_triangulation",
                       karaka_triangulation.compute_karaka_triangulation,
                       d1_chart, asc_sign, moon_sign),
        )

    # -----------------------------------------------------------------------
    # Stage 4: Tier-2 practitioner
    # -----------------------------------------------------------------------
    prac_findings: list[Finding] = []
    prac_by_module: dict[str, list[Finding]] = {}

    if d1_chart:
        from app.reading.computations import (
            eclipse_natal_activation,
            graha_yuddha,
            marana_karaka_sthana,
            sade_sati_severity,
            special_lagnas,
            trika_doctrine,
        )

        _add_findings(
            prac_findings, prac_by_module, "marana_karaka_sthana",
            _safe_call(warnings, "marana_karaka_sthana",
                       marana_karaka_sthana.detect_mks, d1_chart, asc_sign),
        )
        _add_findings(
            prac_findings, prac_by_module, "trika_doctrine",
            _safe_call(warnings, "trika_doctrine",
                       trika_doctrine.detect_trika_exchanges, d1_chart, asc_sign),
        )
        _add_findings(
            prac_findings, prac_by_module, "graha_yuddha",
            _safe_call(warnings, "graha_yuddha",
                       graha_yuddha.detect_graha_yuddha, d1_chart),
        )
        if birth_jd and sunrise_jd:
            _add_findings(
                prac_findings, prac_by_module, "special_lagnas",
                _safe_call(warnings, "special_lagnas",
                           special_lagnas.compute_special_lagnas,
                           birth_jd, sunrise_jd, asc_sign),
            )
        # eclipse activation needs an `eclipses` sequence — skip when not available.
        eclipses = chart.get("eclipses") or []
        if eclipses:
            _add_findings(
                prac_findings, prac_by_module, "eclipse_natal_activation",
                _safe_call(warnings, "eclipse_natal_activation",
                           eclipse_natal_activation.detect_eclipse_activation,
                           d1_chart, asc_sign, eclipses),
            )

        # Sade Sati needs transit_saturn_sign — skip when not natal-only.
        transit_saturn_sign = chart.get("transit_saturn_sign")
        if transit_saturn_sign:
            _add_findings(
                prac_findings, prac_by_module, "sade_sati_severity",
                _safe_call(warnings, "sade_sati_severity",
                           sade_sati_severity.compute_sade_sati_severity,
                           d1_chart, asc_sign, int(transit_saturn_sign)),
            )

        # Yogas (unified entry).
        from app.reading.computations.yogas_extended import detect_yogas
        yoga_findings_list = _safe_call(
            warnings, "yogas_extended",
            detect_yogas, d1_chart, asc_sign, moon_sign,
            default=[],
        ) or []
        _add_findings(
            prac_findings, prac_by_module, "yogas_extended", yoga_findings_list,
        )

        # Divisional readings.
        from app.reading.computations.divisional_readings import (
            d2_hora, d3_drekkana, d7_saptamsa, d9_navamsha,
            d10_dashamsha, d12_dwadasamsa, d24_chaturvimsamsa, d60_shashtiamsa,
        )

        def _div(key: str) -> dict[str, Any]:
            return divisional_charts.get(key) or {}

        d2 = _div("D2_Hora")
        d3 = _div("D3_Drekkana")
        d7 = _div("D7_Saptamsa")
        d12 = _div("D12_Dwadasamsa")
        d24 = _div("D24_Chaturvimsamsa")
        d60 = _div("D60_Shastiamsa")

        if d2:
            _add_findings(
                prac_findings, prac_by_module, "d2_hora",
                _safe_call(warnings, "d2_hora",
                           d2_hora.read_d2_hora, d2, asc_sign),
            )
        if d3:
            _add_findings(
                prac_findings, prac_by_module, "d3_drekkana",
                _safe_call(warnings, "d3_drekkana",
                           d3_drekkana.read_d3_drekkana, d3, asc_sign),
            )
        if d7:
            _add_findings(
                prac_findings, prac_by_module, "d7_saptamsa",
                _safe_call(warnings, "d7_saptamsa",
                           d7_saptamsa.read_d7_saptamsa, d7, asc_sign),
            )
        if d9_chart:
            _add_findings(
                prac_findings, prac_by_module, "d9_navamsha",
                _safe_call(warnings, "d9_navamsha",
                           d9_navamsha.read_d9_navamsha,
                           d1_chart, d9_chart, asc_sign),
            )

        # D10 needs amatya_karaka — pull from karakas Findings.
        amatya = None
        for f in prim_by_module.get("karakas", []):
            if f.rule == "amatya_karaka" or "amatya" in f.id.lower():
                for ev in f.evidence:
                    if ev.startswith("planet="):
                        amatya = ev.split("=", 1)[1]
                        break
                if not amatya and f.verdict:
                    # parse first word of verdict as planet name fallback
                    words = f.verdict.split()
                    if words:
                        amatya = words[0]
                break
        if d10_chart and amatya:
            _add_findings(
                prac_findings, prac_by_module, "d10_dashamsha",
                _safe_call(warnings, "d10_dashamsha",
                           d10_dashamsha.read_d10_dashamsha,
                           d1_chart, d10_chart, asc_sign, amatya),
            )
        if d12:
            _add_findings(
                prac_findings, prac_by_module, "d12_dwadasamsa",
                _safe_call(warnings, "d12_dwadasamsa",
                           d12_dwadasamsa.read_d12_dwadasamsa, d12, asc_sign),
            )
        if d24:
            _add_findings(
                prac_findings, prac_by_module, "d24_chaturvimsamsa",
                _safe_call(warnings, "d24_chaturvimsamsa",
                           d24_chaturvimsamsa.read_d24_chaturvimsamsa,
                           d24, asc_sign),
            )
        # D60 needs atmakaraka.
        atmakaraka = None
        for f in prim_by_module.get("karakas", []):
            if f.rule == "atmakaraka" or "atma" in f.id.lower():
                for ev in f.evidence:
                    if ev.startswith("planet="):
                        atmakaraka = ev.split("=", 1)[1]
                        break
                if not atmakaraka and f.verdict:
                    words = f.verdict.split()
                    if words:
                        atmakaraka = words[0]
                break
        if d60 and atmakaraka:
            _add_findings(
                prac_findings, prac_by_module, "d60_shashtiamsa",
                _safe_call(warnings, "d60_shashtiamsa",
                           d60_shashtiamsa.read_d60_shashtiamsa,
                           d60, asc_sign, atmakaraka),
            )

    # -----------------------------------------------------------------------
    # Stage 5: Sequences
    # -----------------------------------------------------------------------
    seq_block_payload: dict[str, Any] = {
        "amsha_bala_krama": None,
        "career_executive": None,
        "md_judgments": [],
        "ad_judgments": [],
        "chara_dasha": None,   # V1.5 D-17 — populated below if d1 present
        "yogini_dasha": None,  # V1.5 D-18 — populated below if d1 present
    }

    current_md = chart.get("current_mahadasha") or {}
    current_md_lord = current_md.get("mahadasha_lord") or ""
    current_ad_lord = current_md_lord  # natal-only fallback

    if d1_chart and current_md_lord:
        from app.reading.sequences import (
            amsha_bala_krama, career_executive,
            vimshottari_ad, vimshottari_md,
        )

        md_result = _safe_call(
            warnings, "sequences.vimshottari_md",
            vimshottari_md.run_sequence, chart, asc_sign, moon_sign,
        )
        if md_result is not None:
            try:
                seq_block_payload["md_judgments"] = list(md_result.timeline)
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"sequences.vimshottari_md.timeline_unpack failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # Antardasha — need current MD start/end JDs.
        current_md_start_jd: float | None = None
        current_md_end_jd: float | None = None
        if md_result is not None:
            try:
                cmd = md_result.current_md_judgment
                current_md_start_jd = float(cmd.start_jd)
                current_md_end_jd = float(cmd.end_jd)
                # Also use the current MD lord from the MD result for consistency.
                current_md_lord = cmd.md_lord
            except Exception:  # noqa: BLE001
                pass
        if current_md_start_jd is not None and current_md_end_jd is not None:
            ad_result = _safe_call(
                warnings, "sequences.vimshottari_ad",
                vimshottari_ad.run_sequence,
                chart, asc_sign, moon_sign, current_md_lord,
                current_md_start_jd, current_md_end_jd,
            )
            if ad_result is not None:
                try:
                    seq_block_payload["ad_judgments"] = list(
                        ad_result.current_md_ads
                    ) + list(ad_result.next_md_first_3_ads)
                    # Pick the leading AD as current_ad_lord for downstream
                    # marriage_trigger (best-effort, falls back to MD lord).
                    if ad_result.current_md_ads:
                        current_ad_lord = ad_result.current_md_ads[0].ad_lord
                except Exception as exc:  # noqa: BLE001
                    warnings.append(
                        f"sequences.vimshottari_ad.unpack failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

        amsha_result = _safe_call(
            warnings, "sequences.amsha_bala_krama",
            amsha_bala_krama.run_sequence,
            chart, asc_sign, moon_sign,
            current_md_lord, current_ad_lord,
        )
        if amsha_result is not None:
            seq_block_payload["amsha_bala_krama"] = amsha_result

        career_result = _safe_call(
            warnings, "sequences.career_executive",
            career_executive.run_sequence,
            chart, asc_sign, moon_sign, current_md_lord,
            birth_jd, chart_input.lat, chart_input.lon, is_daytime, weekday,
        )
        if career_result is not None:
            seq_block_payload["career_executive"] = career_result

    # V1.5 — Chara Dasha (D-17 Jaimini sign-frame).
    # Wired into the deterministic pipeline (runs in --no-enrich too).
    # Pass-through model_dump so SequencesBlock can carry it as dict[str, Any]
    # (importing CharaDashaResult into schema.py would create a circular import).
    if d1_chart:
        try:
            from app.reading.sequences import chara_dasha
            chara_result = _safe_call(
                warnings, "sequences.chara_dasha",
                chara_dasha.run_sequence, chart, asc_sign, moon_sign,
            )
            if chara_result is not None:
                seq_block_payload["chara_dasha"] = chara_result.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"sequences.chara_dasha.import failed: {type(exc).__name__}: {exc}"
            )

    # V1.5 — Yogini Dasha (D-18 36-year specialty dasha).
    # Yogini takes moon_nakshatra (1..27), not moon_sign — derive from moon_lon.
    if d1_chart and moon_lon:
        try:
            from app.core.nakshatra import nakshatra_for_longitude
            from app.reading.sequences import yogini_dasha
            moon_nak_info = nakshatra_for_longitude(moon_lon)
            moon_nakshatra_1based = int(moon_nak_info["index"]) + 1
            yogini_result = _safe_call(
                warnings, "sequences.yogini_dasha",
                yogini_dasha.run_sequence,
                chart, asc_sign, moon_nakshatra_1based,
            )
            if yogini_result is not None:
                seq_block_payload["yogini_dasha"] = yogini_result.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"sequences.yogini_dasha.import failed: {type(exc).__name__}: {exc}"
            )

    # marriage_trigger — Tier-2, but needs current_ad_lord which we just got.
    if d1_chart and current_md_lord and arudha_padas:
        transit_jupiter_sign = chart.get("transit_jupiter_sign")
        transit_saturn_sign = chart.get("transit_saturn_sign")
        if transit_jupiter_sign and transit_saturn_sign and d9_chart:
            from app.reading.computations import marriage_trigger
            mt_finding = _safe_call(
                warnings, "marriage_trigger",
                marriage_trigger.compute_marriage_trigger,
                d1_chart, d9_chart, asc_sign, moon_sign,
                arudha_padas, current_md_lord, current_ad_lord,
                int(transit_jupiter_sign), int(transit_saturn_sign),
            )
            if isinstance(mt_finding, Finding):
                prac_findings.append(mt_finding)
                prac_by_module["marriage_trigger"] = [mt_finding]

    # -----------------------------------------------------------------------
    # Stage 6: Domain synthesis
    # -----------------------------------------------------------------------
    dom_block_payload: dict[str, Any] = {
        "career": None, "marriage": None, "children": None,
        "wealth": None, "health": None, "education": None,
    }

    if d1_chart:
        from app.reading.domains import (
            career as career_dom,
            children as children_dom,
            education as edu_dom,
            health as health_dom,
            marriage as marriage_dom,
            wealth as wealth_dom,
        )

        primitives_view = {
            "findings": list(prim_findings),
            "by_module": dict(prim_by_module),
        }
        foundations_view = {
            "findings": list(found_findings),
            "by_module": dict(found_by_module),
        }
        sequences_view: dict[str, Any] = {
            "amsha_bala_krama": seq_block_payload["amsha_bala_krama"],
            "career_executive": seq_block_payload["career_executive"],
            "md_judgments": seq_block_payload["md_judgments"],
            "ad_judgments": seq_block_payload["ad_judgments"],
        }

        for key, fn, label in (
            ("career", career_dom.synthesize_career, "domains.career"),
            ("marriage", marriage_dom.synthesize_marriage, "domains.marriage"),
            ("children", children_dom.synthesize_children, "domains.children"),
            ("wealth", wealth_dom.synthesize_wealth, "domains.wealth"),
            ("health", health_dom.synthesize_health, "domains.health"),
            ("education", edu_dom.synthesize_education, "domains.education"),
        ):
            result = _safe_call(
                warnings, label, fn,
                chart, asc_sign, moon_sign,
                sequences_view, primitives_view, foundations_view,
            )
            if result is not None:
                dom_block_payload[key] = result

    # -----------------------------------------------------------------------
    # rookie_guards — runs over the assembled reading to flag invariants.
    # -----------------------------------------------------------------------
    pre_reading: dict[str, Any] = {
        "primitives": {
            "findings": prim_findings, "by_module": prim_by_module,
        },
        "foundations": {
            "findings": found_findings, "by_module": found_by_module,
        },
        "practitioner": {
            "findings": prac_findings, "by_module": prac_by_module,
        },
        "sequences": seq_block_payload,
        "domains": dom_block_payload,
    }
    try:
        from app.reading.computations import rookie_guards
        rookie_findings = _safe_call(
            warnings, "rookie_guards",
            rookie_guards.check_rookie_invariants, pre_reading, default=[],
        ) or []
        if rookie_findings:
            prac_findings.extend(rookie_findings)
            prac_by_module["rookie_guards"] = rookie_findings
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"rookie_guards.import failed: {type(exc).__name__}: {exc}")

    # -----------------------------------------------------------------------
    # Classical yogas — the core 88-detector library, surfaced with citations.
    # (The practitioner `yogas_extended` module is a 9-detector graded subset;
    # this is the wider named-yoga catalog. Cosmetic, fail-soft.)
    # -----------------------------------------------------------------------
    classical_yogas_payload = _classical_yogas(d1_chart, asc_sign, lagna_longitude)

    # -----------------------------------------------------------------------
    # Stage 7: Assembly
    # -----------------------------------------------------------------------
    meta = Meta(
        engine_version=_engine_version(),
        swiss_ephemeris_version=_swiss_ephemeris_version(),
        python_version=_python_version(),
        generated_at=_generated_at_iso(),
        chart_input=chart_input,
        doctrines_used=[],
        doctrine_config=DoctrineConfig(),
        enrichment_enabled=False,
        robustness_enabled=False,
        stage_timings_ms={},
    )

    try:
        output = ReadingOutput(
            meta=meta,
            chart=ChartBlock(**chart_block_payload),
            primitives=PrimitivesBlock(
                findings=prim_findings, by_module=prim_by_module,
            ),
            foundations=FoundationsBlock(
                findings=found_findings, by_module=found_by_module,
            ),
            practitioner=PractitionerBlock(
                findings=prac_findings, by_module=prac_by_module,
            ),
            sequences=SequencesBlock(**seq_block_payload),
            domains=DomainsBlock(**dom_block_payload),
            contradictions=[],
            warnings=warnings,
            classical_yogas=classical_yogas_payload,
        )
    except Exception as exc:  # noqa: BLE001
        # Last-resort fallback: emit an empty-blocks reading with the
        # assembly error logged, so the CLI's schema check still passes.
        logger.warning(
            "ReadingOutput assembly failed; emitting empty fallback: %s", exc
        )
        warnings.append(
            f"stage7.assembly failed: {type(exc).__name__}: {exc}"
        )
        output = ReadingOutput(
            meta=meta,
            chart=ChartBlock(),
            primitives=PrimitivesBlock(),
            foundations=FoundationsBlock(),
            practitioner=PractitionerBlock(),
            sequences=SequencesBlock(),
            domains=DomainsBlock(),
            contradictions=[],
            warnings=warnings,
        )

    # -----------------------------------------------------------------------
    # V1.5 — modern-life enrichment.
    # Appends classification="primitive" Findings to each domain's
    # cross_checks list. Runs in --no-enrich path (deterministic, no LLM/RAG).
    # We pass the assembled ReadingOutput in object mode; the synthesizer
    # rebuilds the frozen DomainReading instances with augmented cross_checks
    # and returns a new ReadingOutput.
    # -----------------------------------------------------------------------
    if d1_chart:
        try:
            from app.reading.modern_life.synthesizer import enrich_with_modern_signals
            output = enrich_with_modern_signals(output, chart, asc_sign)
        except Exception as exc:  # noqa: BLE001
            msg = f"stage6.modern_life_enrichment failed: {type(exc).__name__}: {exc}"
            logger.warning(msg)
            # output.warnings is frozen — propagate by re-assembling Pydantic-ly
            warnings.append(msg)
            try:
                output = output.model_copy(update={"warnings": list(warnings)})
            except Exception:  # noqa: BLE001
                pass

    return output.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Tier-3 enrichment afterpass
# ---------------------------------------------------------------------------


def _findings_from_dicts(finding_dicts: list[dict[str, Any]]) -> list[Finding]:
    """Best-effort rebuild Finding objects from dicts. Skip on failure."""
    out: list[Finding] = []
    for d in finding_dicts:
        try:
            out.append(Finding.model_validate(d))
        except Exception:  # noqa: BLE001
            continue
    return out


def _apply_finding_enrichments_to_block(
    block: dict[str, Any], enriched_by_id: dict[str, Finding]
) -> None:
    """Replace dict-findings in ``block`` with enriched versions in-place.

    Walks ``findings`` list AND ``by_module`` map, swapping each by id.
    """
    if not isinstance(block, dict):
        return
    findings = block.get("findings")
    if isinstance(findings, list):
        for i, f in enumerate(findings):
            if isinstance(f, dict):
                enriched = enriched_by_id.get(f.get("id", ""))
                if enriched is not None:
                    findings[i] = enriched.model_dump(mode="json")
    by_module = block.get("by_module")
    if isinstance(by_module, dict):
        for mod_name, mod_findings in list(by_module.items()):
            if isinstance(mod_findings, list):
                for i, f in enumerate(mod_findings):
                    if isinstance(f, dict):
                        enriched = enriched_by_id.get(f.get("id", ""))
                        if enriched is not None:
                            mod_findings[i] = enriched.model_dump(mode="json")


def _apply_tier3_enrichments(
    base: dict[str, Any], chart_input: ChartInput
) -> dict[str, Any]:
    """Layer Tier-3 enrichments on top of the core pipeline output.

    Tier-3 chain: citations -> consensus -> dispute -> yoga calibration
    -> contradiction detection -> robustness. Each subsystem reads the
    bare ReadingOutput payload and returns enriched Findings.

    Lazy imports — these heavy modules (sentence_transformers, torch via
    rag_citations) are imported here so the ``--no-enrich`` path never
    pulls them. Per spec Section 9 perf discipline.
    """
    logger.debug(
        "Tier-3 enrichment invoked for dob=%s", chart_input.dob
    )
    warnings: list[str] = list(base.get("warnings") or [])

    # Lazy imports — see module docstring for rationale.
    from app.reading.computations import (
        consensus_scoring,
        contradiction_detector,
        dispute_surfacing,
        rag_citations,
        yoga_calibration,
    )

    # Collect every flat findings list from the 3 stage blocks.
    blocks_to_walk = ("primitives", "foundations", "practitioner")
    flat_dicts: list[dict[str, Any]] = []
    for key in blocks_to_walk:
        block = base.get(key) or {}
        for f in block.get("findings") or []:
            if isinstance(f, dict):
                flat_dicts.append(f)
    findings_list = _findings_from_dicts(flat_dicts)

    primitives_view = base.get("primitives") or {"findings": [], "by_module": {}}

    # Step 1: citations.
    try:
        findings_list = rag_citations.attach_citations(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.rag_citations failed: {type(exc).__name__}: {exc}"
        )
        logger.warning("rag_citations failed: %s", exc)

    # Step 2: consensus (depends on citations).
    try:
        findings_list = consensus_scoring.score_consensus(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.consensus_scoring failed: {type(exc).__name__}: {exc}"
        )

    # Step 3: dispute surfacing.
    try:
        findings_list = dispute_surfacing.surface_disputes(findings_list)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.dispute_surfacing failed: {type(exc).__name__}: {exc}"
        )

    # Step 4: yoga calibration.
    try:
        findings_list = yoga_calibration.calibrate_yogas(
            findings_list, primitives_view,
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.yoga_calibration failed: {type(exc).__name__}: {exc}"
        )

    # Apply enriched findings back into the base dict.
    enriched_by_id = {f.id: f for f in findings_list}
    for key in blocks_to_walk:
        _apply_finding_enrichments_to_block(base.get(key) or {}, enriched_by_id)

    # Step 5: contradiction detection (top-level, reads the assembled output).
    try:
        contradictions = contradiction_detector.detect_contradictions(base)
        base["contradictions"] = [c.model_dump(mode="json") for c in contradictions]
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.contradiction_detector failed: {type(exc).__name__}: {exc}"
        )

    # Step 6: robustness — uses the PRIVATE _run_core_pipeline.
    try:
        from app.reading.computations import birth_time_robustness
        robustness_findings = birth_time_robustness.score_robustness(
            chart_input, base,
        )
        rob_by_id = {f.id: f for f in robustness_findings}
        # Merge robustness back into the per-stage findings.
        for key in blocks_to_walk:
            _apply_finding_enrichments_to_block(base.get(key) or {}, rob_by_id)
        base["meta"]["robustness_enabled"] = True
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"tier3.birth_time_robustness failed: {type(exc).__name__}: {exc}"
        )

    base["meta"]["enrichment_enabled"] = True
    base["warnings"] = warnings
    return base


def compute(chart_input: ChartInput, enrich: bool = True) -> dict[str, Any]:
    """Run the full kundli pipeline and return a `ReadingOutput`-shaped dict.

    This is the public engine entry point. CLI, API routes, and downstream
    callers (LLM narrators, frontend, RAG layers) should call this rather
    than `_run_core_pipeline`. The only exception is birth-time-robustness,
    which calls `_run_core_pipeline` directly to avoid recursion.

    Args:
        chart_input: Validated user-supplied birth-data envelope.
        enrich: If True (default), layer Tier-3 enrichments after the core
            pipeline completes. If False, return the bare deterministic
            output.

    Returns:
        A dict matching the `ReadingOutput` Pydantic schema.
    """
    base = _run_core_pipeline(chart_input)
    result = base if not enrich else _apply_tier3_enrichments(base, chart_input)
    # Present-tense + real-doctrine enrichments (daśā-now, live transits, the
    # encoded Raman per-house verdicts, executive summary). Fail-soft, additive,
    # under chart.extras — runs last so the full timeline is available.
    _augment_present_and_doctrine(result, chart_input)
    return result
