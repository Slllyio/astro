"""Phase 4 — the shipped engine.

Serves only what survived the full protocol, and serves a null as a first-class
result when nothing did. On the corpus acquired so far, the null is the live
path: the Gauquelin screening returned no survivor on any of eighteen tests.

Modules:
  survivors  the claim record; refuses any claim that did not beat its twin
  report     per-claim disclosure and the honest empty state
"""

from __future__ import annotations

__all__ = ["report", "survivors"]
