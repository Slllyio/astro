"""Escape-hatch registry for rules the DSL cannot express.

A compendium record may set ``antecedent: "impl:python:<id>"`` instead of
a predicate tree. The id resolves here. Guardrails (enforced by
``tests/doctrine/test_engine.py::TestEscapeHatch``):

* every impl is registered with a **citation** (book + page/chapter) —
  same discipline as the raman_method_v2 verbatim-table style;
* an impl's signature is exactly ``(ctx: EvalContext) -> bool`` — it may
  consume ONLY the public RamanChart/EvalContext API, never raw ephemeris
  or the frozen run-5 internals (the registry check inspects closures);
* target share: <20% of ``full`` rules (audited in COVERAGE reporting).
"""
from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable

from app.medini.doctrine.engine.predicates import EvalContext, MissingInput


@dataclasses.dataclass(frozen=True)
class EscapeImpl:
    impl_id: str                       # "hpa.balarishta_full" -> impl:python:hpa.balarishta_full
    citation: str                      # book + page/chapter provenance
    fn: Callable[[EvalContext], bool]


_REGISTRY: dict[str, EscapeImpl] = {}


def register(impl_id: str, citation: str):
    """Decorator: register an escape-hatch antecedent implementation."""
    def wrap(fn: Callable[[EvalContext], bool]):
        if impl_id in _REGISTRY:
            raise ValueError(f"escape hatch {impl_id!r} already registered")
        params = list(inspect.signature(fn).parameters)
        if params != ["ctx"]:
            raise TypeError(
                f"{impl_id}: escape hatch signature must be (ctx), got {params}")
        if not citation.strip():
            raise ValueError(f"{impl_id}: citation required")
        _REGISTRY[impl_id] = EscapeImpl(impl_id, citation, fn)
        return fn
    return wrap


def resolve(antecedent: str) -> EscapeImpl:
    """Resolve an ``impl:python:<id>`` antecedent; KeyError if unknown
    (load-time contract: unresolvable escape hatches fail the load)."""
    prefix = "impl:python:"
    if not antecedent.startswith(prefix):
        raise KeyError(f"not an escape-hatch antecedent: {antecedent!r}")
    impl_id = antecedent[len(prefix):]
    if impl_id not in _REGISTRY:
        raise KeyError(f"escape hatch {impl_id!r} not registered")
    return _REGISTRY[impl_id]


def registered() -> dict[str, EscapeImpl]:
    return dict(_REGISTRY)


# ----------------------------------------------------------------- impls

@register("hpa.balarishta_screen",
          "HPA Ch. XIV 'Ayurdaya or Longevity', pp. 112-116 — combinations "
          "1/2/3/5 with bhanga antidotes 1/2/3/7 weighed together per p. 116")
def _balarishta_screen(ctx: EvalContext) -> bool:
    """Net Balarishta: any arishta present AND no bhanga counteracting."""
    from app.core.arishta_yogas import evaluate_arishta

    chart = ctx.chart.bundle.chart
    arishtas, bhangas = evaluate_arishta(
        chart.planet_lons,
        ctx.chart.bundle.kundali.planet_house,
        ctx.chart.bundle.lagna_lord,
        ctx.chart.bundle.strength,
        ctx.chart.bundle.moon_waxing,
    )
    return any(f.present for f in arishtas) and not any(f.present for f in bhangas)
