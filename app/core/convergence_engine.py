"""Cross-layer convergence engine — the synthesis tier (S-1).

Every master-toolkit layer produces its own verdict in isolation. A real
astrologer doesn't read them in parallel — they look for CONVERGENCE
across ≥3 of N independent layers. When the base 3-pillar reading + the
Vimshottari MD lord + the Gochara transit + the D9 confirmation + the
Translation Engine all agree, that's HIGH-CONFIDENCE. When they
contradict, the contradiction itself is the diagnosis.

This module makes that synthesis explicit. For any prediction domain
(marriage / career / wealth / health / ...) it scans 11 doctrinal layers,
collects per-layer Evidence (signal +1/-1/0 + classical citation), and
emits a ConvergenceVerdict with weighted score, confidence band, and
list of contradictions.

Doctrinal foundation (operationalised from [[feedback-astro-doctrine-is-axiomatic]]):

    PREDICTION = f(YOGA × DASHA × GOCHARA | DESH, KAAL, PARISTHITI)

    No single signature emits a prediction. Require ≥3 of N independent
    confirmations from:
      1. Parashari static (Lagna + Chandra + Surya triple read)
      2. Parashari temporal (Vimshottari MD/AD/PD)
      3. Parashari trigger (Gochara with double-transit gate)
      4. Jaimini parallel (Chara karakas + Arudhas + Chara Dasha)
      5. Divisional confirmation (D-chart relevant to domain)

The convergence engine is the explicit ≥3-of-N gate that classical
doctrine implies but the framework didn't enforce.

## What this is NOT

This is not a statistical aggregator. The doctrine is axiomatic; the
engine's job is to surface which classical signals fired, not to
"validate" them. A "contradictory" verdict means the chart contains a
real tension worth a careful astrologer's attention — not that the
doctrine failed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Mapping

from app.core.master_reading import MasterReading


# ─── Public types ───────────────────────────────────────────────────


@dataclass(frozen=True)
class Evidence:
    """One layer's verdict on one domain question."""
    layer: str               # which doctrine module the signal came from
    signal: int              # +1 supports, -1 contradicts (0 = silent, dropped)
    weight: float            # layer's authority for this domain
    what_it_says: str        # human-readable finding
    citation: str            # classical reference


@dataclass(frozen=True)
class ConvergenceVerdict:
    """Result of cross-layer convergence detection for one domain."""
    domain: str
    primary_bhava: int
    evidence: tuple[Evidence, ...]
    n_supporting: int        # count of +1 signals
    n_contradicting: int     # count of -1 signals
    weighted_score: float    # sum(signal × weight)
    confidence_band: str     # near-certain / high / moderate / low / indeterminate
    convergence_label: str   # strongly_supportive / supportive / mixed /
                             # contradictory / afflicted / strongly_afflicted /
                             # indeterminate
    contradictions: tuple[tuple[str, str], ...]  # (layer_a, layer_b) disagreement pairs
    coverage_caveat: str     # which layers could NOT be checked + why


# ─── Domain → primary bhava map ─────────────────────────────────────


DOMAIN_PRIMARY_BHAVA: Final[Mapping[str, int]] = {
    "self":            1,
    "personality":     1,
    "wealth":          2,
    "siblings":        3,
    "courage":         3,
    "mother":          4,
    "home":            4,
    "property":        4,
    "children":        5,
    "education":       5,
    "intellect":       5,
    "health":          6,
    "service":         6,
    "marriage":        7,
    "spouse":          7,
    "partnerships":    7,
    "longevity":       8,
    "occult":          8,
    "father":          9,
    "dharma":          9,
    "fortune":         9,
    "career":          10,
    "fame":            10,
    "status":          10,
    "gains":           11,
    "social-network":  11,
    "loss":            12,
    "moksha":          12,
    "travel-foreign":  12,
}


# Domain → yoga keyword families. Used to score active yogas as positive
# evidence for that domain. Lowercased substring match against yoga name.
DOMAIN_YOGA_FAMILIES: Final[Mapping[str, frozenset[str]]] = {
    "wealth":    frozenset({"dhana", "lakshmi", "vasumati", "akhanda",
                            "neecha bhanga", "parijata"}),
    "career":    frozenset({"raja", "dharma-karma", "yogakaraka",
                            "amala", "gajakesari"}),
    "fame":      frozenset({"raja", "amala", "akhanda", "kahala"}),
    "marriage":  frozenset({"sunapha", "anapha", "durudhura", "kalanidhi"}),
    "spouse":    frozenset({"sunapha", "anapha", "durudhura"}),
    "education": frozenset({"saraswati", "budha-aditya", "bhadra"}),
    "intellect": frozenset({"saraswati", "budha-aditya", "bhadra", "veshi"}),
    "children":  frozenset({"putra", "santana", "saraswati"}),
    "health":    frozenset({"harsha", "sarala", "vimala"}),  # Vipareeta Raja
    "longevity": frozenset({"harsha", "sarala", "vimala"}),
    "dharma":    frozenset({"dharma-karma", "amala", "gajakesari"}),
    "fortune":   frozenset({"lakshmi", "vasumati", "dharma-karma"}),
    "moksha":    frozenset({"pravrajya", "sanyasa"}),  # rare, may not be active
}

# Domain → affliction yoga keywords. Active afflicting yogas = -1 signal.
DOMAIN_AFFLICTING_YOGAS: Final[Mapping[str, frozenset[str]]] = {
    "wealth":    frozenset({"daridra", "kuhu", "kemadruma"}),
    "marriage":  frozenset({"mangal dosha", "mangal-dosha", "kuja dosha"}),
    "health":    frozenset({"sarpa", "papa kartari"}),
    "longevity": frozenset({"alpa-ayur", "balarishta"}),
    "career":    frozenset({"shakat", "guru chandala"}),
    "children":  frozenset({"sarpa", "putra-dosha"}),
}


# Per-bhava natural karaka (duplicated from bhavat_bhavam to avoid cycle)
_BHAVA_KARAKAS: Final[Mapping[int, tuple[str, ...]]] = {
    1:  ("Sun",),
    2:  ("Jupiter",),
    3:  ("Mars",),
    4:  ("Moon", "Mercury"),
    5:  ("Jupiter",),
    6:  ("Mars", "Saturn"),
    7:  ("Venus",),
    8:  ("Saturn",),
    9:  ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Jupiter", "Saturn"),
    11: ("Jupiter",),
    12: ("Saturn", "Ketu"),
}


# ─── Per-layer signal collectors ────────────────────────────────────


def _signal_from_base_bhava(
    mr: MasterReading, bhava: int,
) -> Evidence | None:
    """Phase 6 three-pillar verdict for the primary bhava."""
    claim = mr.base_reading.bhava_claims.get(bhava)
    if claim is None:
        return None
    if claim.verdict_label == "strong":
        signal, what = +1, f"Bhava {bhava} verdict STRONG (3-pillar)"
    elif claim.verdict_label == "afflicted":
        signal, what = -1, f"Bhava {bhava} verdict AFFLICTED (3-pillar)"
    elif claim.verdict_label == "weak":
        signal, what = -1, f"Bhava {bhava} verdict WEAK (3-pillar)"
    elif claim.verdict_label == "medium":
        return None  # neutral — drop
    else:
        return None
    return Evidence(
        layer="base_3pillar", signal=signal, weight=1.5,
        what_it_says=what,
        citation="BPHS Ch.34 — bhava judgement triple-pillar (bhava × bhava-lord × karaka)",
    )


def _signal_from_varga_confirmation(
    mr: MasterReading, bhava: int,
) -> Evidence | None:
    """Cross-check the bhava promise in its assigned varga."""
    vc = mr.varga_confirmations.get(bhava)
    if vc is None or vc.confirmation_label == "UNKNOWN":
        return None
    if vc.confirmation_label == "CONFIRMED":
        return Evidence(
            layer="varga_confirmation", signal=+1, weight=1.5,
            what_it_says=f"D1 promise confirmed in {vc.varga_name}",
            citation="BPHS Ch.7 — divisional confirmation of D1 promise",
        )
    if vc.confirmation_label == "CONSISTENT_AFFLICTION":
        return Evidence(
            layer="varga_confirmation", signal=-1, weight=1.5,
            what_it_says=f"D1 and {vc.varga_name} both negative — genuine affliction",
            citation="BPHS Ch.7 — both pillars negative; bhava truly afflicted",
        )
    if vc.confirmation_label == "PROMISE_NO_DELIVERY":
        return Evidence(
            layer="varga_confirmation", signal=-1, weight=1.0,
            what_it_says=f"D1 promises but {vc.varga_name} contradicts — outer success without inner fruit",
            citation="Phaladeepika Ch.5 — promise without delivery",
        )
    if vc.confirmation_label == "HIDDEN_PROMISE":
        return Evidence(
            layer="varga_confirmation", signal=+1, weight=0.8,
            what_it_says=f"D1 silent but {vc.varga_name} contains promise — late-bloom delivery",
            citation="Sanjay Rath — varga-trigger activation",
        )
    return None


def _signal_from_ashtakavarga(
    mr: MasterReading, bhava: int,
) -> Evidence | None:
    """SAV strength of the primary bhava."""
    sav_report = mr.ashtakavarga.sav_per_bhava.get(bhava)
    if sav_report is None:
        return None
    if sav_report.strength_label == "strong":
        return Evidence(
            layer="ashtakavarga_sav", signal=+1, weight=1.0,
            what_it_says=f"SAV {sav_report.sav_points} → STRONG for bhava {bhava}",
            citation="BPHS Ch.66-67 — Sarvashtakavarga bindu strength",
        )
    if sav_report.strength_label == "weak":
        return Evidence(
            layer="ashtakavarga_sav", signal=-1, weight=1.0,
            what_it_says=f"SAV {sav_report.sav_points} → WEAK for bhava {bhava}",
            citation="BPHS Ch.66-67 — Sarvashtakavarga bindu deficiency",
        )
    return None  # 'average' is neutral


def _signal_from_karakamsa(mr: MasterReading) -> Evidence | None:
    """Karakamsa = soul-purpose lens. Only meaningful for life-purpose domains.

    Caller decides relevance; this function just returns the soul lens.
    """
    if mr.karakamsa is None:
        return None
    return Evidence(
        layer="karakamsa", signal=+1, weight=0.8,
        what_it_says=(
            f"Karakamsa at sign {mr.karakamsa.karakamsa_sign} "
            f"(via Atmakaraka {mr.karakamsa.atmakaraka})"
        ),
        citation="Jaimini Sutras 2.1 — Karakamsa Lagna soul-purpose lens",
    )


def _signal_from_yoga_family(
    mr: MasterReading, domain: str,
) -> tuple[Evidence, ...]:
    """Active yogas matching the domain's supportive/afflicting families."""
    supportive_kws = DOMAIN_YOGA_FAMILIES.get(domain, frozenset())
    afflicting_kws = DOMAIN_AFFLICTING_YOGAS.get(domain, frozenset())
    found: list[Evidence] = []
    for y in mr.base_reading.active_yogas:
        name_lower = y.name.lower()
        if any(kw in name_lower for kw in supportive_kws):
            found.append(Evidence(
                layer=f"yoga:{y.name}", signal=+1,
                weight=1.0 * float(getattr(y, "intensity", 1.0)),
                what_it_says=f"{y.name} active — supports {domain}",
                citation=y.reference or "BPHS / Phaladeepika yoga registry",
            ))
        elif any(kw in name_lower for kw in afflicting_kws):
            found.append(Evidence(
                layer=f"yoga:{y.name}", signal=-1,
                weight=1.0 * float(getattr(y, "intensity", 1.0)),
                what_it_says=f"{y.name} active — afflicts {domain}",
                citation=y.reference or "BPHS / Phaladeepika yoga registry",
            ))
    return tuple(found)


def _signal_from_avastha_of_karaka(
    mr: MasterReading, bhava: int,
) -> tuple[Evidence, ...]:
    """Avastha multiplier of the bhava's natural karaka(s)."""
    out: list[Evidence] = []
    for karaka in _BHAVA_KARAKAS.get(bhava, ()):
        mult = mr.avastha_multipliers.get(karaka)
        if mult is None:
            continue
        if mult >= 0.75:
            out.append(Evidence(
                layer=f"avastha:{karaka}", signal=+1, weight=0.7,
                what_it_says=f"{karaka} avastha mult {mult:.2f} — strong delivery",
                citation="BPHS Ch.45 — Baladi × Deeptadi composite",
            ))
        elif mult < 0.25:
            out.append(Evidence(
                layer=f"avastha:{karaka}", signal=-1, weight=0.7,
                what_it_says=f"{karaka} avastha mult {mult:.2f} — weak delivery",
                citation="BPHS Ch.45 — Baladi × Deeptadi composite",
            ))
    return tuple(out)


def _signal_from_vimsopaka_of_karaka(
    mr: MasterReading, bhava: int,
) -> tuple[Evidence, ...]:
    """Vimsopaka strength of the bhava's natural karaka(s)."""
    out: list[Evidence] = []
    for karaka in _BHAVA_KARAKAS.get(bhava, ()):
        rep = mr.vimsopaka.get(karaka)
        if rep is None:
            continue
        # Vimsopaka rupas range 0..20; thresholds per the vimsopaka_bala module
        if rep.strength_label in ("STRONG", "GOOD"):
            out.append(Evidence(
                layer=f"vimsopaka:{karaka}", signal=+1, weight=0.7,
                what_it_says=f"{karaka} Vimsopaka {rep.composite_rupas:.1f}/20 → {rep.strength_label}",
                citation="BPHS Ch.7 — Vimsopaka Bala (varga-weighted strength)",
            ))
        elif rep.strength_label in ("WEAK", "VERY WEAK"):
            out.append(Evidence(
                layer=f"vimsopaka:{karaka}", signal=-1, weight=0.7,
                what_it_says=f"{karaka} Vimsopaka {rep.composite_rupas:.1f}/20 → {rep.strength_label}",
                citation="BPHS Ch.7 — Vimsopaka Bala (varga-weighted weakness)",
            ))
    return tuple(out)


def _signal_from_bhrigu_bindu(
    mr: MasterReading, bhava: int,
) -> Evidence | None:
    """Is Bhrigu Bindu placed in or aspecting the primary bhava?"""
    if mr.sensitive_points.bhrigu_bindu is None:
        return None
    bb_sign = mr.sensitive_points.bhrigu_bindu.sign
    asc = mr.base_reading.asc_sign
    bb_house = ((bb_sign - asc) % 12) + 1
    if bb_house == bhava:
        return Evidence(
            layer="bhrigu_bindu", signal=+1, weight=0.5,
            what_it_says=f"Bhrigu Bindu in bhava {bhava} — fate-point activation",
            citation="Bhrigu Sutra — sensitive midpoint of Moon+Rahu",
        )
    # Bhrigu Bindu in dushtana of the target bhava = afflicting
    if bb_house in ((bhava + 5) % 12 + 1, (bhava + 7) % 12 + 1, (bhava + 11) % 12 + 1):
        return Evidence(
            layer="bhrigu_bindu", signal=-1, weight=0.4,
            what_it_says=f"Bhrigu Bindu in {bb_house}H — dushtana of bhava {bhava}",
            citation="Bhrigu Sutra — fate-point affliction",
        )
    return None


def _signal_from_dasha_alignment(
    mr: MasterReading, bhava: int,
) -> tuple[Evidence, ...]:
    """Active Vimshottari MD lord + Yogini lord: are they bhava-relevant?

    Bhava-relevant = lord of the bhava OR natural karaka of the bhava
    OR in/aspecting the bhava (only first two checked here — bhava-
    occupancy requires Chart which we don't have direct access to in
    this synthesis layer).
    """
    out: list[Evidence] = []
    karakas = _BHAVA_KARAKAS.get(bhava, ())
    md_lord = mr.base_reading.vimshottari_md_at_target
    if md_lord and md_lord in karakas:
        out.append(Evidence(
            layer="vimshottari_md", signal=+1, weight=1.0,
            what_it_says=(
                f"Vimshottari MD = {md_lord} (natural karaka of bhava {bhava}) "
                f"— direct dasha activation"
            ),
            citation="BPHS Ch.46 — Vimshottari MD lord activation",
        ))
    if mr.yogini_active is not None:
        yog_lord = mr.yogini_active.presiding_planet
        if yog_lord in karakas:
            out.append(Evidence(
                layer="yogini_md", signal=+1, weight=0.8,
                what_it_says=(
                    f"Yogini active = {yog_lord} (karaka of bhava {bhava}) "
                    f"— parallel-dasha confirmation"
                ),
                citation="Brihat Yogini Dasha — parallel temporal activation",
            ))
    return tuple(out)


def _signal_from_bhavat(
    mr: MasterReading, bhava: int,
) -> Evidence | None:
    """Bhāvāt Bhāvam — recursive bhava reading.

    If a chain reaches the primary bhava AND the chain's source bhava
    is itself strong, that's supporting. (Conservative: only count one
    bhavat chain per check.)
    """
    for chain in mr.bhavat_chains:
        if chain.derived_bhava == bhava:
            base_claim = mr.base_reading.bhava_claims.get(chain.base_bhava)
            if base_claim is None:
                continue
            if base_claim.verdict_label == "strong":
                return Evidence(
                    layer="bhavat_bhavam", signal=+1, weight=0.5,
                    what_it_says=(
                        f"Bhāvāt chain {chain.base_bhava}H→{chain.distance}th→{bhava}H "
                        f"({chain.interpretation_hint}); base bhava strong"
                    ),
                    citation="Jaimini Sutras — Bhāvāt Bhāvam recursive house reading",
                )
            if base_claim.verdict_label in ("weak", "afflicted"):
                return Evidence(
                    layer="bhavat_bhavam", signal=-1, weight=0.5,
                    what_it_says=(
                        f"Bhāvāt chain {chain.base_bhava}H→{bhava}H "
                        f"but base bhava {base_claim.verdict_label}"
                    ),
                    citation="Jaimini Sutras — recursive chain weakness propagates",
                )
    return None


def _signal_from_arudha(
    mr: MasterReading, domain: str, bhava: int,
) -> Evidence | None:
    """Arudha pada of the primary bhava — manifested image of that domain.

    Marriage → Upapada Lagna specifically; other domains use the
    bhava's general Arudha placement.
    """
    if domain in ("marriage", "spouse", "partnerships"):
        upl_sign = mr.upapada_lagna.bhava
        # UPL in 12 = foreign-residence marriage; UPL in 6/8 = marriage stress
        if upl_sign in (6, 8):
            return Evidence(
                layer="upapada_lagna", signal=-1, weight=1.0,
                what_it_says=f"Upapada Lagna in sign {upl_sign} (dushtana-style placement)",
                citation="Jaimini Sutras — UPL in 6/8/12 = marriage difficulty",
            )
        if upl_sign in (1, 4, 7, 10, 5, 9):
            return Evidence(
                layer="upapada_lagna", signal=+1, weight=1.0,
                what_it_says=f"Upapada Lagna in sign {upl_sign} (kendra/trikona — auspicious for marriage)",
                citation="Jaimini Sutras — UPL kendra/trikona = strong marriage signature",
            )
    # General arudha
    arudha = mr.all_arudhas.get(bhava)
    if arudha is None:
        return None
    # Arudha = 1 or in a kendra/trikona is supportive for the bhava's manifestation
    if arudha.bhava in (1, 4, 5, 7, 9, 10):
        return Evidence(
            layer=f"arudha_b{bhava}", signal=+1, weight=0.6,
            what_it_says=f"Arudha of bhava {bhava} = sign {arudha.bhava} (kendra/trikona)",
            citation="Jaimini Sutras — Arudha pada manifested-image strength",
        )
    if arudha.bhava in (6, 8, 12):
        return Evidence(
            layer=f"arudha_b{bhava}", signal=-1, weight=0.6,
            what_it_says=f"Arudha of bhava {bhava} = sign {arudha.bhava} (dushtana — image-erosion)",
            citation="Jaimini Sutras — Arudha in dushtana = manifested-image affliction",
        )
    return None


def _signal_from_translation(
    mr: MasterReading, bhava: int,
) -> tuple[Evidence, ...]:
    """Doctrine translations attached to the primary bhava (provenance only)."""
    claim = mr.base_reading.bhava_claims.get(bhava)
    if claim is None:
        return ()
    out: list[Evidence] = []
    for t in claim.relevant_translations[:3]:  # cap at 3 to avoid noise
        first_ref = t.classical_references[0] if t.classical_references else "—"
        out.append(Evidence(
            layer=f"translation:{t.key}", signal=0, weight=0.0,
            what_it_says=t.modern_manifestation[:120],
            citation=first_ref,
        ))
    return tuple(out)


# ─── Main convergence function ──────────────────────────────────────


def convergence_verdict(
    mr: MasterReading, domain: str,
) -> ConvergenceVerdict:
    """Scan 11 doctrinal layers for convergent evidence on one domain.

    Args:
        mr: A MasterReading from compose_master_reading.
        domain: One of the keys in DOMAIN_PRIMARY_BHAVA.

    Returns:
        ConvergenceVerdict with per-layer evidence + weighted score +
        confidence band + contradictions list.

    Raises:
        ValueError: if domain is not in DOMAIN_PRIMARY_BHAVA.

    Doctrine: ≥3 of N independent layers agreeing = high-confidence
    prediction. Less than 3 supporting + at least 2 contradicting =
    contradictory verdict (read the tension as the diagnosis, not as
    "the doctrine failed"). Less than 3 total signals = indeterminate.
    """
    bhava = DOMAIN_PRIMARY_BHAVA.get(domain)
    if bhava is None:
        raise ValueError(
            f"unknown domain: {domain!r}. "
            f"Known: {sorted(DOMAIN_PRIMARY_BHAVA)}"
        )

    evidence: list[Evidence] = []
    coverage_gaps: list[str] = []

    # Per-layer collection
    if (e := _signal_from_base_bhava(mr, bhava)) is not None:
        evidence.append(e)

    if (e := _signal_from_varga_confirmation(mr, bhava)) is not None:
        evidence.append(e)
    else:
        coverage_gaps.append("varga_confirmation (UNKNOWN for this bhava)")

    if (e := _signal_from_ashtakavarga(mr, bhava)) is not None:
        evidence.append(e)

    if domain in ("dharma", "career", "fame", "self", "personality"):
        if (e := _signal_from_karakamsa(mr)) is not None:
            evidence.append(e)
        else:
            coverage_gaps.append("karakamsa (Atmakaraka not supplied)")

    evidence.extend(_signal_from_yoga_family(mr, domain))
    evidence.extend(_signal_from_avastha_of_karaka(mr, bhava))
    evidence.extend(_signal_from_vimsopaka_of_karaka(mr, bhava))

    if (e := _signal_from_bhrigu_bindu(mr, bhava)) is not None:
        evidence.append(e)

    evidence.extend(_signal_from_dasha_alignment(mr, bhava))

    if (e := _signal_from_bhavat(mr, bhava)) is not None:
        evidence.append(e)

    if (e := _signal_from_arudha(mr, domain, bhava)) is not None:
        evidence.append(e)

    # Translations are zero-signal context — included for provenance/display
    # but don't affect the score.
    evidence.extend(_signal_from_translation(mr, bhava))

    # Tally
    supporting = [e for e in evidence if e.signal > 0]
    contradicting = [e for e in evidence if e.signal < 0]
    weighted_score = sum(e.signal * e.weight for e in evidence)
    n_sig = len(supporting) + len(contradicting)

    # Confidence band (joint of magnitude + signal count)
    abs_score = abs(weighted_score)
    if n_sig >= 5 and abs_score >= 4.0:
        confidence = "near-certain"
    elif n_sig >= 4 and abs_score >= 2.5:
        confidence = "high"
    elif n_sig >= 3 and abs_score >= 1.5:
        confidence = "moderate"
    elif n_sig >= 2:
        confidence = "low"
    else:
        confidence = "indeterminate"

    # Convergence label
    if n_sig < 2:
        label = "indeterminate"
    elif len(supporting) >= 2 and len(contradicting) >= 2:
        label = "contradictory"
    elif weighted_score >= 3.0:
        label = "strongly_supportive"
    elif weighted_score >= 1.0:
        label = "supportive"
    elif weighted_score <= -3.0:
        label = "strongly_afflicted"
    elif weighted_score <= -1.0:
        label = "afflicted"
    else:
        label = "mixed"

    # Contradictions list: name pairs of supporting vs contradicting layers
    contradictions: list[tuple[str, str]] = []
    if supporting and contradicting:
        for s in supporting[:3]:
            for c in contradicting[:3]:
                contradictions.append((s.layer, c.layer))

    coverage_caveat = (
        f"{len(coverage_gaps)} layer(s) couldn't be checked: "
        + "; ".join(coverage_gaps[:3])
        if coverage_gaps
        else "all layers checked"
    )

    return ConvergenceVerdict(
        domain=domain,
        primary_bhava=bhava,
        evidence=tuple(evidence),
        n_supporting=len(supporting),
        n_contradicting=len(contradicting),
        weighted_score=round(weighted_score, 3),
        confidence_band=confidence,
        convergence_label=label,
        contradictions=tuple(contradictions[:10]),  # cap display
        coverage_caveat=coverage_caveat,
    )


def format_convergence_verdict(v: ConvergenceVerdict) -> str:
    """Render a ConvergenceVerdict as a human-readable reasoning trace."""
    lines = [
        f"=== {v.domain.upper()} (bhava {v.primary_bhava}) ===",
        f"Verdict      : {v.convergence_label}  ({v.confidence_band} confidence)",
        f"Weighted     : {v.weighted_score:+.2f}",
        f"Signals      : {v.n_supporting} support / {v.n_contradicting} contradict",
        f"Coverage     : {v.coverage_caveat}",
        "",
        "Evidence:",
    ]
    for e in v.evidence:
        sigil = "+" if e.signal > 0 else ("-" if e.signal < 0 else ".")
        lines.append(
            f"  [{sigil}] ({e.layer:<22s} w={e.weight:.1f})  {e.what_it_says}"
        )
        lines.append(f"        -> {e.citation}")
    if v.contradictions:
        lines.append("")
        lines.append("Contradictions (read the tension as diagnosis):")
        for s, c in v.contradictions[:5]:
            lines.append(f"  {s}  <->  {c}")
    return "\n".join(lines)
