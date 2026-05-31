"""DKP modulation adapter — wrap Track-A domain verdicts as Track-B
``BhavaVerdict`` and feed them through Track-B's
``apply_dkp_modulation()``.

Track-B's DKP (Desh-Kaal-Paristhiti) modulation layer takes a 12-field
context (latitude, climate, ashrama, marital status, profession, prashna,
etc.) and adjusts the confidence of a bhava verdict accordingly. Track A
has no equivalent layer. This adapter bridges them so a Track-A reading
can be re-scored under Track-B's DKP framework.

Public surface
--------------
- ``modulate_domain(domain_reading, dkp_context=None, *, full_reading=None)``
  → ``ModulatedDomainReading``
- ``modulate_all_domains(reading_dict, dkp_context=None)``
  → ``DkpModulatedReading``
- ``build_dkp_context_from_reading(reading_dict, **overrides)``
  → ``DKPContext``

Methodology
-----------
Adapter consists of four transforms:

1. **Domain → bhava** static map: ``career=10, marriage=7, children=5,
   wealth=2, health=6, education=4``. This is a doctrinal pick (Track A
   does not carry a bhava integer on ``DomainReading``).
2. **direction → label** mapping: positive→strong, negative→afflicted,
   neutral→medium, mixed→weak. Lossy — Track A's "mixed" has no exact
   counterpart in Track B's four-bucket label set.
3. **confidence.score + direction → composite_score** rescale:
   ``composite = (score * 2) - 1``, sign-flipped to negative when
   ``direction == "negative"``.
4. **confidence.votes → 3 PillarScores**: Track A's
   ``votes['house'|'lord'|'karaka']`` boolean trio is converted into
   three ``PillarScore`` entries with score=+1 if vote=True else -0.0.
   Reasonings synthesised from ``DomainReading.promise/afflictions/cross_checks``.

Known lossiness — preserved on the wrapper so consumers can recover:

- ``DomainReading.timing_windows`` / ``remedies`` / ``triggers`` have no
  ``BhavaVerdict`` slot. The wrapper preserves the original
  ``DomainReading`` alongside the ``ModulatedVerdict``.
- ``BhavaVerdict.confirming_yogas`` / ``afflicting_yogas`` have no
  source on ``DomainReading``. When ``full_reading`` is supplied, the
  adapter walks ``ReadingOutput.primitives`` and friends for
  ``classification == "yoga"`` findings and partitions by direction.
- If ``DKPContext`` is None or sparse, ``context_completeness`` will be
  <9 and Track B's modulator forces confidence to LOW regardless of
  Track A's confidence — this is Track B's intended behaviour.

The adapter does NOT mutate ``DomainReading`` (it's frozen with
``extra="forbid"``). A new wrapper type ``ModulatedDomainReading``
holds {original, modulated, dkp_context_used, mapping_notes}.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.bhava_judge import BhavaVerdict, PillarScore, Reasoning
from app.core.dkp_modulation import (
    DKPContext,
    ModulatedVerdict,
    apply_dkp_modulation,
    context_completeness,
)


# ---------------------------------------------------------------------------
# Static maps
# ---------------------------------------------------------------------------

# Track-A domain name → primary bhava integer. Doctrinal pick:
#   career → 10 (karma sthana)
#   marriage → 7 (kalatra sthana)
#   children → 5 (putra sthana)
#   wealth → 2 (dhana sthana)
#   health → 6 (roga sthana)
#   education → 4 (vidya sthana, classical primary education seat)
_DOMAIN_TO_BHAVA: dict[str, int] = {
    "career": 10,
    "marriage": 7,
    "children": 5,
    "wealth": 2,
    "health": 6,
    "education": 4,
}

# Track-A Finding.direction → BhavaVerdict.label.
_DIRECTION_TO_LABEL: dict[str, str] = {
    "positive": "strong",
    "negative": "afflicted",
    "neutral": "medium",
    "mixed": "weak",  # lossy collapse — preserved in notes
}


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class ModulatedVerdictView(BaseModel):
    """JSON-friendly projection of Track-B's ``ModulatedVerdict`` dataclass."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    confidence: str
    context_completeness: int
    bhava_reading_focus: str
    modulation_notes: tuple[str, ...]
    clarifying_questions: tuple[str, ...]

    @classmethod
    def from_modulated(cls, m: ModulatedVerdict) -> ModulatedVerdictView:
        return cls(
            confidence=m.confidence,
            context_completeness=m.context_completeness,
            bhava_reading_focus=m.bhava_reading_focus,
            modulation_notes=tuple(m.modulation_notes),
            clarifying_questions=tuple(m.clarifying_questions),
        )


class ModulatedDomainReading(BaseModel):
    """Wraps a Track-A ``DomainReading`` with its Track-B modulated verdict.

    The original ``DomainReading`` dict is preserved verbatim so consumers
    keep access to ``timing_windows`` / ``remedies`` / ``triggers``, which
    have no slot on ``BhavaVerdict`` and would otherwise be lost."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    bhava: int = Field(ge=1, le=12)
    original: dict[str, Any]
    modulated: ModulatedVerdictView
    mapping_notes: tuple[str, ...]


class DkpModulatedReading(BaseModel):
    """Reading-level envelope: one ``ModulatedDomainReading`` per Track-A
    domain (career, marriage, children, wealth, health, education)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.2.0"
    dkp_context_used: dict[str, Any]
    context_completeness: int
    per_domain: list[ModulatedDomainReading]


# ---------------------------------------------------------------------------
# DKPContext construction
# ---------------------------------------------------------------------------

def build_dkp_context_from_reading(
    reading: dict[str, Any], **overrides: Any
) -> DKPContext:
    """Extract whichever DKPContext fields can be read from a Track-A reading.

    Track A natively populates at most ~5 of 12 DKPContext fields:
    birth_latitude, birth_longitude, birth_date_iso, age_years (derived),
    active_dasha_lord (from current MD). The remaining 7 are user-supplied
    via ``overrides`` keyword arguments.

    Parameters
    ----------
    reading
        A Track-A ``ReadingOutput`` (dumped dict).
    **overrides
        Any ``DKPContext`` field can be overridden directly (e.g.
        ``ashrama="grihastha"``, ``profession="software_engineer"``).

    Returns
    -------
    DKPContext
        The constructed context; pass to ``modulate_*`` functions.
    """
    chart_block = reading.get("chart") or {}
    foundations = reading.get("foundations") or {}
    meta = reading.get("meta") or {}
    sequences = reading.get("sequences") or {}

    def _first_non_none(*candidates: Any) -> Any:
        for c in candidates:
            if c is not None:
                return c
        return None

    lat = _first_non_none(
        chart_block.get("latitude"),
        foundations.get("latitude"),
        meta.get("latitude"),
    )
    lon = _first_non_none(
        chart_block.get("longitude"),
        foundations.get("longitude"),
        meta.get("longitude"),
    )
    birth_date_iso = _first_non_none(
        chart_block.get("dob"),
        chart_block.get("birth_date_iso"),
        meta.get("dob"),
    )

    # Current MD lord from Vimshottari, if present.
    md_block = sequences.get("vimshottari") or sequences.get("vimshottari_md") or {}
    current_md = None
    if isinstance(md_block, dict):
        current_md = md_block.get("current_md_lord") or md_block.get("current_md_planet")

    init_kwargs: dict[str, Any] = {}
    if lat is not None:
        init_kwargs["birth_latitude"] = float(lat)
    if lon is not None:
        init_kwargs["birth_longitude"] = float(lon)
    if birth_date_iso:
        init_kwargs["birth_date_iso"] = str(birth_date_iso)
    if current_md:
        init_kwargs["active_dasha_lord"] = str(current_md)

    # Apply overrides (caller-supplied trumps anything we extracted).
    init_kwargs.update(overrides)

    return DKPContext(**init_kwargs)


# ---------------------------------------------------------------------------
# Verdict construction
# ---------------------------------------------------------------------------

def _votes_to_pillars(
    votes: dict[str, bool],
    promise_text: str,
    promise_rule: str,
    afflictions: list[dict[str, Any]],
    cross_checks: list[dict[str, Any]],
) -> tuple[tuple[PillarScore, ...], int, int]:
    """Project Track-A's ``votes['house'|'lord'|'karaka']`` booleans into
    Track-B's 3 PillarScores. Reasonings are populated from
    ``DomainReading.promise``, ``afflictions``, ``cross_checks`` so the
    pillar reasoning chain isn't empty.

    Returns ``(pillars, n_positive, n_negative)``.
    """
    pillar_specs = [
        ("bhava", votes.get("house", False), [
            Reasoning(finding=promise_text[:120], weight=1.0, reference=promise_rule),
        ]),
        ("lord", votes.get("lord", False), [
            Reasoning(
                finding=c.get("verdict", "")[:120],
                weight=0.5 if c.get("direction") == "positive" else -0.5,
                reference=c.get("rule", ""),
            )
            for c in cross_checks[:4]
        ]),
        ("karaka", votes.get("karaka", False), [
            Reasoning(
                finding=a.get("verdict", "")[:120],
                weight=-0.5,
                reference=a.get("rule", ""),
            )
            for a in afflictions[:4]
        ]),
    ]

    pillars: list[PillarScore] = []
    n_pos = 0
    n_neg = 0
    for label, vote_positive, reasonings in pillar_specs:
        score = 1.0 if vote_positive else -1.0
        if vote_positive:
            n_pos += 1
        else:
            n_neg += 1
        pillars.append(PillarScore(
            label=label,
            score=score,
            reasonings=tuple(reasonings),
        ))
    return tuple(pillars), n_pos, n_neg


def _build_bhava_verdict(
    domain_reading: dict[str, Any],
    full_reading: dict[str, Any] | None = None,
) -> tuple[BhavaVerdict, tuple[str, ...]]:
    """Build a Track-B ``BhavaVerdict`` from a Track-A ``DomainReading`` dict.

    Returns ``(verdict, mapping_notes)`` where ``mapping_notes`` records
    lossy projections so the audit trail survives.
    """
    domain = domain_reading.get("domain", "")
    bhava = _DOMAIN_TO_BHAVA.get(domain)
    if bhava is None:
        raise ValueError(
            f"Unknown domain {domain!r}; expected one of {list(_DOMAIN_TO_BHAVA)}"
        )

    overall = domain_reading.get("overall_verdict") or {}
    direction = overall.get("direction", "neutral")
    label = _DIRECTION_TO_LABEL.get(direction, "medium")

    confidence_block = domain_reading.get("confidence") or {}
    score = float(confidence_block.get("score") or 0.5)
    composite = (score * 2) - 1
    if direction == "negative":
        composite = -abs(composite)
    elif direction == "positive":
        composite = abs(composite)

    votes = confidence_block.get("votes") or {}
    promise = domain_reading.get("promise") or {}
    promise_text = promise.get("verdict", "")
    promise_rule = promise.get("rule", "")
    afflictions = domain_reading.get("afflictions") or []
    cross_checks = domain_reading.get("cross_checks") or []

    pillars, n_pos, n_neg = _votes_to_pillars(
        votes, promise_text, promise_rule, afflictions, cross_checks
    )

    # Confirming/afflicting yogas: traverse full_reading if provided.
    confirming_yogas: list[str] = []
    afflicting_yogas: list[str] = []
    if full_reading is not None:
        for node in _walk_findings(full_reading):
            if node.get("classification") == "yoga":
                yname = node.get("rule", "").rsplit(".", 1)[-1]
                d = node.get("direction", "neutral")
                if d == "positive":
                    confirming_yogas.append(yname)
                elif d == "negative":
                    afflicting_yogas.append(yname)

    notes_list: list[str] = [
        f"adapted_from=domain.{domain}.overall_verdict",
        f"direction_source={direction}",
    ]
    if direction == "mixed":
        notes_list.append("note=mixed_direction_collapsed_to_label_weak")
    if not full_reading:
        notes_list.append("note=full_reading_not_supplied_yogas_empty")

    verdict = BhavaVerdict(
        bhava=bhava,
        pillars=pillars,
        composite_score=composite,
        label=label,
        confirming_yogas=tuple(confirming_yogas),
        afflicting_yogas=tuple(afflicting_yogas),
        n_positive_pillars=n_pos,
        n_negative_pillars=n_neg,
        notes=tuple(notes_list),
    )
    return verdict, tuple(notes_list)


def _walk_findings(node: Any):
    """Yield Finding-shaped dicts. Same structural identifier as
    ``dkp_enhancer._walk_findings``: dict must have id/rule/classification/verdict."""
    if isinstance(node, dict):
        if {"id", "rule", "classification", "verdict"}.issubset(node.keys()):
            yield node
        else:
            for v in node.values():
                yield from _walk_findings(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_findings(item)


# ---------------------------------------------------------------------------
# Public entrypoints
# ---------------------------------------------------------------------------

def modulate_domain(
    domain_reading: dict[str, Any],
    dkp_context: DKPContext | None = None,
    *,
    full_reading: dict[str, Any] | None = None,
) -> ModulatedDomainReading:
    """Modulate a single Track-A ``DomainReading`` via Track-B's DKP layer.

    Parameters
    ----------
    domain_reading
        A dict matching ``app.reading.schema.DomainReading.model_dump()``.
    dkp_context
        Track-B ``DKPContext``. If None, uses empty context (completeness=0,
        confidence forced to LOW).
    full_reading
        Optional full ``ReadingOutput`` dict — supplied to extract yoga lists
        for ``BhavaVerdict.confirming_yogas`` / ``afflicting_yogas``.
    """
    ctx = dkp_context if dkp_context is not None else DKPContext()
    verdict, mapping_notes = _build_bhava_verdict(domain_reading, full_reading)
    modulated = apply_dkp_modulation(verdict, ctx)
    return ModulatedDomainReading(
        domain=domain_reading.get("domain", ""),
        bhava=verdict.bhava,
        original=domain_reading,
        modulated=ModulatedVerdictView.from_modulated(modulated),
        mapping_notes=mapping_notes,
    )


def modulate_all_domains(
    reading: dict[str, Any],
    dkp_context: DKPContext | None = None,
) -> DkpModulatedReading:
    """Modulate every Track-A domain on ``reading`` via DKP.

    Domains that are ``None`` on the reading are silently skipped.
    """
    ctx = dkp_context if dkp_context is not None else build_dkp_context_from_reading(reading)
    domains_block = reading.get("domains") or {}
    out: list[ModulatedDomainReading] = []
    for domain_name in _DOMAIN_TO_BHAVA:
        domain_reading = domains_block.get(domain_name)
        if not domain_reading:
            continue
        # Inject domain name if it's missing on the dict (schema always has it).
        if "domain" not in domain_reading:
            domain_reading = {**domain_reading, "domain": domain_name}
        out.append(modulate_domain(
            domain_reading,
            dkp_context=ctx,
            full_reading=reading,
        ))
    return DkpModulatedReading(
        dkp_context_used={
            "birth_latitude": ctx.birth_latitude,
            "birth_longitude": ctx.birth_longitude,
            "current_residence_country": ctx.current_residence_country,
            "climate_mahabhuta": ctx.climate_mahabhuta,
            "birth_date_iso": ctx.birth_date_iso,
            "age_years": ctx.age_years,
            "active_mundane_event": ctx.active_mundane_event,
            "active_dasha_lord": ctx.active_dasha_lord,
            "ashrama": ctx.ashrama,
            "marital_status": ctx.marital_status,
            "profession": ctx.profession,
            "prashna": ctx.prashna,
        },
        context_completeness=context_completeness(ctx),
        per_domain=out,
    )
