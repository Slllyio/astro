"""``app.empirical`` — the tournament-style empirical prediction subsystem.

This package is **epistemically separate** from ``app.raman_saab``. The Raman
engine is a faithful scholarly instrument answering "what would Raman say"; its
real-outcome generalization was measured NULL on 22,177 charts and that verdict
is locked (see ``CLAUDE.md`` § MEASURED TRUTH). This subsystem therefore starts
from different ground: it asks which — if any — astrological features carry
*measured* predictive signal over a chartless demographic baseline, and it is
designed so that NULL is a first-class, shippable answer.

Structural contracts, enforced by tests:

* **One-way isolation.** ``app.raman_saab`` and ``app.core`` never import
  ``app.empirical``. The golden ratchet cannot be perturbed by anything here.
  (``tests/empirical/test_isolation.py``)
* **No global ephemeris state.** Nothing in this package calls
  ``swe.set_sid_mode``. The Western layer is tropical and needs no ayanamsa;
  mutating swisseph's global sidereal mode would silently corrupt every Vedic
  cast in the process. (``tests/empirical/test_western_tropical.py``)
* **One data path.** Every experiment loads through
  ``app.medini.ml.experiment_loader.build_experiment_matrix``; no experiment
  writes or reads its own parquet.

Sub-packages:

* ``western/`` — Phase 2 tropical toolkit (positions, houses, aspects,
  progressions, returns, transits, midpoints, harmonics). Pure computation
  over pyswisseph; no corpus dependency.
* ``acquire/`` — Phase 1 corpus growth (Gauquelin/CURA registry-timed births,
  Wikidata day-precision lives).
* ``tournament/`` — Phase 3 pre-registered feature-bank contest (prereg,
  frozen holdout, sham gates, chartless twins).
* ``engine/`` — Phase 4 shipped surface (survivor claims or the measured
  null, with framing).
* ``natal/`` — the Western natal decode: planets at birth composed into seven
  trait facets under the ``WESTERN_TRADITION`` banner; tradition disclosed as
  tradition, never as measurement.
"""

from __future__ import annotations

__all__ = ["western", "acquire", "tournament", "engine", "natal"]
