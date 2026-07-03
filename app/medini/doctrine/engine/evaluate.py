"""Rule evaluation over a chart: profiles, shadow mode, static vs timeline.

Semantics locked by the plan:

* **Activation, not mutation** — conflict adjudication never edits a
  record. An *evaluation profile* maps each conflict group to exactly one
  active rule id; inactive variants still evaluate (shadow mode) so the
  fidelity harness can compare variants against Raman's worked verdicts.
* **Static vs timeline** — a rule's ``consequent.timing`` is an activation
  spec. Static evaluation reports the structural potential and ignores
  timing; timeline evaluation additionally requires the timing gate
  (dasha leaves consume ``EvalContext.dasha``).
* **Not evaluable ≠ did not fire** — MissingInput yields ``evaluable:
  False`` instead of a False verdict.
"""
from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path

from app.medini.doctrine.engine import escape_hatch
from app.medini.doctrine.engine.predicates import (
    EvalContext,
    MissingInput,
    UnknownOp,
    evaluate_predicate,
    validate_predicate,
)

CONFLICTS_PATH = Path("data/raman_doctrine/conflicts.jsonl")


@dataclasses.dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    evaluable: bool
    fired: bool           # antecedent true (False when not evaluable)
    active: bool          # active under the profile (False = shadow mode)
    shadow_of: str | None # conflict group when running in shadow
    missing: str | None   # MissingInput reason when not evaluable


def load_profile(
    profile: str = "raman_default",
    conflicts_path: Path = CONFLICTS_PATH,
) -> dict[str, str]:
    """conflict_id -> active_rule_id under the named profile."""
    if not conflicts_path.exists():
        return {}
    active: dict[str, str] = {}
    for line in conflicts_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        res = rec.get("resolution", {})
        if res.get("scope", "raman_default") == profile:
            active[rec["conflict_id"]] = res["active_rule_id"]
    return active


def _conflict_state(rule: Mapping, profile_map: Mapping[str, str],
                    conflict_groups: Mapping[str, str]) -> tuple[bool, str | None]:
    """(active, shadow_of) for a rule under the profile."""
    group = conflict_groups.get(rule["id"])
    if group is None:
        return True, None
    winner = profile_map.get(group)
    if winner is None or winner == rule["id"]:
        return True, None
    return False, group


def compile_rule(rule: Mapping) -> None:
    """Load-time check: a ``full``/``partial`` antecedent must be
    interpretable — DSL trees validate op-by-op; escape hatches must
    resolve. Raises UnknownOp/KeyError otherwise."""
    ante = rule["antecedent"]
    if ante is None:
        return
    if isinstance(ante, str):
        escape_hatch.resolve(ante)
        return
    validate_predicate(ante)


def evaluate_rule(
    rule: Mapping,
    ctx: EvalContext,
    *,
    mode: str = "static",
    profile_map: Mapping[str, str] | None = None,
    conflict_groups: Mapping[str, str] | None = None,
) -> RuleOutcome:
    """Evaluate one record. ``mode``: static | timeline."""
    if mode not in ("static", "timeline"):
        raise ValueError(f"mode must be static|timeline, got {mode!r}")
    active, shadow_of = _conflict_state(
        rule, profile_map or {}, conflict_groups or {})
    ante = rule["antecedent"]
    if ante is None:
        return RuleOutcome(rule["id"], evaluable=False, fired=False,
                           active=active, shadow_of=shadow_of,
                           missing="non-executable (manual/unfalsifiable)")
    try:
        if isinstance(ante, str):
            fired = escape_hatch.resolve(ante).fn(ctx)
        else:
            fired = evaluate_predicate(ante, ctx)
        if fired and mode == "timeline":
            timing = rule["consequent"].get("timing")
            if timing is not None:
                fired = _timing_gate(timing, ctx)
    except MissingInput as exc:
        return RuleOutcome(rule["id"], evaluable=False, fired=False,
                           active=active, shadow_of=shadow_of, missing=str(exc))
    return RuleOutcome(rule["id"], evaluable=True, fired=bool(fired),
                       active=active, shadow_of=shadow_of, missing=None)


def _timing_gate(timing: Mapping, ctx: EvalContext) -> bool:
    """Timeline activation: is the rule's temporal window open now?"""
    mode = timing.get("mode")
    if mode in ("dasha", "bhukti"):
        if ctx.dasha is None:
            raise MissingInput("timing gate needs dasha context")
        level = "md" if mode == "dasha" else "ad"
        lord = ctx.dasha.get(level)
        if lord is None:
            raise MissingInput(f"timing gate needs {level} lord")
        of = timing.get("of")
        if of is None:
            return True  # window described in prose only; gate on presence
        return _resolve_lord_ref(of, ctx) == lord
    if mode in ("transit", "age_band", "election"):
        raise MissingInput(f"timing mode {mode!r} not yet wired to a clock")
    raise UnknownOp(f"unknown timing mode {mode!r}")


def _resolve_lord_ref(ref: str, ctx: EvalContext) -> str:
    """Resolve a timing 'of' reference: a planet name or 'lord_of_<n>'."""
    if ref.startswith("lord_of_"):
        return ctx.chart.bundle.sign_lord_of_house(int(ref.rsplit("_", 1)[1]))
    return ref


def evaluate_rules(
    rules: list[Mapping],
    ctx: EvalContext,
    *,
    mode: str = "static",
    profile: str = "raman_default",
    conflicts_path: Path = CONFLICTS_PATH,
) -> list[RuleOutcome]:
    """Evaluate a rule set under a profile; shadow variants included."""
    profile_map = load_profile(profile, conflicts_path)
    conflict_groups: dict[str, str] = {}
    if conflicts_path.exists():
        for line in conflicts_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            for rid in rec.get("rule_ids", []):
                conflict_groups[rid] = rec["conflict_id"]
    return [
        evaluate_rule(rule, ctx, mode=mode, profile_map=profile_map,
                      conflict_groups=conflict_groups)
        for rule in rules
        if rule["antecedent"] is not None
    ]
